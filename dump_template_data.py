#!/usr/bin/python3

import argparse
import csv
import json
import multiprocessing
import os
import re
import sys

from autodooz.magic_words import MAGIC_WORDS, MAGIC_COMMANDS
from autodooz.utils import iter_wxt, iter_xml
from collections import defaultdict

def main():
    parser = argparse.ArgumentParser(description="Find errors in sense lists")
    parser.add_argument("target", help="target filename")
    parser.add_argument("--xml", help="XML file to load")
    parser.add_argument("--wxt", help="Wiktionary extract file to load")
    parser.add_argument("--redirects", help="redirects.tsv")
    parser.add_argument("--limit", type=int, help="Limit processing to first N articles")
    parser.add_argument("--progress", help="Display progress", action='store_true')
    parser.add_argument("-j", help="run N jobs in parallel (default = # CPUs - 1", type=int)
    args = parser.parse_args()

    if (not args.xml and not args.wxt) or (args.xml and args.wxt):
        print("use either --xml or --wxt")
        exit(1)

    if not args.j:
        args.j = multiprocessing.cpu_count()-1

    if args.wxt:
        iter_entries = iter_wxt(args.wxt, args.limit, args.progress, title_matches=lambda x: x.startswith("Template:"))
    else:
        iter_entries = iter_xml(args.xml, args.limit, args.progress, title_matches=lambda x: x.startswith("Template:"))

    with open(args.redirects) as infile:
        redirects = {x[0].removeprefix("Template:"):x[1].removeprefix("Template:") for x in csv.reader(infile, delimiter="\t") if x[0].startswith("Template:")}

    dump_template_args(iter_entries, redirects, args.target)


def get_included_text(text):
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    text = re.sub(r"<\s*noinclude\s*[/]\s*>", "", text, flags=re.DOTALL)
    text = re.sub(r"<\s*noinclude\s*>.*?<\s*/\s*noinclude\s*>", "", text, flags=re.DOTALL)
    text = re.sub(r"<\s*[/]?\s*includeonly\s*[/]?\s*>", "", text)

    if "onlyinclude" in text:
        text = "".join(re.findall(r"<\s*onlyinclude\s*>(.*?)<\s*/\s*onlyinclude\s*>", text, flags=re.DOTALL))

    return text


def get_template_stats(args):

    entry_text, entry_title = args
    entry_title = entry_title.removeprefix("Template:")
    entry_text = get_included_text(entry_text)

    entry_text = re.sub(r"{{\s*(" + "|".join(MAGIC_COMMANDS) + r")\s*:", "", entry_text, flags=re.IGNORECASE)

    if re.match(r"^\s*#REDIRECT", entry_text, re.IGNORECASE):
        return

    used_modules = sorted(set(m.group(1).strip() for m in re.finditer(r"#invoke:(.*?)[|}]", entry_text, re.DOTALL)))

    # if a module uses invoke, check if it's a pure Lua implementation or mixed
    if used_modules:
        if len(used_modules) > 1:
            template_type = "mixed"
        else:
            if re.search(r"{{#(^invoke)|{{{[^{}]*?}}}|{{[^#{}][^{}]*?}}", entry_text):
                template_type = "mixed"
            else:
                template_type = "lua"
    else:
        template_type = "wiki"

    #used_params = list({m.group(1):1 for m in re.finditer(r"\{\{\{\s*([a-zA-Z0-9. +/_-]+?)[|}]", entry_text)}.keys())
    used_params = list({m.group(1).strip():1 for m in re.finditer(r"\{\{\{\s*([^=|{}<>]+?)[|}]", entry_text)}.keys())

    # filter out PAGENAME, etc
    used_params = [p for p in used_params if p not in MAGIC_WORDS]

    used_templates = None
    if template_type in ["wiki", "mixed"]:

        # Strip {{{vars}}}
        prev_text = None
        stripped = entry_text
        while prev_text != stripped:
            prev_text = stripped
            stripped = re.sub(r"\{\{\{[^{}]*", "", stripped)
        # strip {{#commands
        stripped = re.sub(r"{{\s*#[^{}]*", "", stripped)

        used_templates = []
        for m in re.finditer(r"{{(.*?)[{<}|]", stripped, re.DOTALL):
            if not m.group(1):
                continue
            template_name = re.sub(r"<!--.*?-->", "", m.group(1)).strip()
            if not template_name or "\n" in template_name:
                continue
            if template_name not in used_templates and template_name not in MAGIC_WORDS:
                used_templates.append(template_name)

    return entry_title, template_type, used_modules, used_templates, used_params


def dump_template_args(iter_entries, redirects, filename):
    iter_items = map(get_template_stats, iter_entries)

    templates = {}
    unparsable = set()
    for res in iter_items:
        if not res:
            continue
        template, template_type, used_modules, used_templates, used_params = res
        templates[template] = {k:v for k,v in [
            ("params", used_params),
            ("templates", used_templates),
            ("modules", used_modules),
        ] if v}


    lua_templates = set()
    mixed_templates = set()
    wiki_templates = set()
    static_templates = set()
    maybe_mixed_templates = set()

    # First pass:
    #   add counts
    #   detect all Lua template
    #   detect all static templates
    #   detect obvious mixed templates
    #   detect obvious wiki templates
    for template, data in templates.items():
        if "params" not in data and "templates" not in data:
            mods = data.get("modules", [])
            if not mods:
                static_templates.add(template)
            elif len(data.get("modules", [])) == 1:
                lua_templates.add(template)
            else:
                mixed_templates.add(template)

        elif "templates" in data and "modules" in data:
            mixed_templates.add(template)

        elif "templates" not in data:

            if "modules" not in data:
                wiki_templates.add(template)
            else:
                mixed_templates.add(template)

        else:
            maybe_mixed_templates.add(template)

    # multiple passess, detect mixed templates that call other mixed templates
    found = True
    while found:
        found = set()
        for template in maybe_mixed_templates:
            for i in templates[template]["templates"]:
                i = redirects.get(i, i)
                if i in mixed_templates:
                    found.add(template)

        for template in found:
            mixed_templates.add(template)
            maybe_mixed_templates.remove(template)

    wiki_templates |= maybe_mixed_templates

    for flag, items in [
        ("lua", lua_templates),
        ("mixed", mixed_templates),
        ("wiki", wiki_templates),
        ("static", static_templates),
    ]:
        for template in items:
            templates[template]["type"] = flag


    with open(filename, 'w', encoding='utf-8') as outfile:
        json.dump({
            "templates": templates,
            }, outfile, ensure_ascii=False, indent=4, sort_keys=True)

if __name__ == "__main__":
    main()
