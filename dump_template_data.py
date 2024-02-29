#!/usr/bin/python3

import argparse
import json
import multiprocessing
import os
import re
import sys

from autodooz.fix_rq_template import RqTemplateFixer
from collections import defaultdict
from pywikibot import xmlreader


# https://www.mediawiki.org/wiki/Help:Magic_words
MAGIC_WORDS = [ "FULLPAGENAME", "PAGENAME", "BASEPAGENAME", "NAMESPACE", "!", "SUBPAGENAME", "SUBJECTSPACE", "TALKPAGENAME"  ]
MW_COMMANDS = MAGIC_WORDS + ["subst", "safesubst", "uc", "lc", "padleft", "padright", "ns", "urlencode", "fullurl", "localurl", "ucfirst"]


def iter_xml(datafile, limit=None, show_progress=False):
    dump = xmlreader.XmlDump(datafile)
    parser = dump.parse()

    count = 0
    for entry in parser:
        if not count % 1000 and show_progress:
            print(count, end = '\r', file=sys.stderr)

        if limit and count >= limit:
            break
        count += 1

        if not entry.title.startswith("Template:"):
            continue

        yield entry.text, entry.title

def iter_wxt(datafile, limit=None, show_progress=False):

    if not os.path.isfile(datafile):
        raise FileNotFoundError(f"Cannot open: {datafile}")

    from enwiktionary_wordlist.wikiextract import WikiExtractWithRev
    parser = WikiExtractWithRev.iter_articles_from_bz2(datafile)

    count = 0
    for entry in parser:
        if not count % 1000 and show_progress:
            print(count, end = '\r', file=sys.stderr)

        if limit and count >= limit:
            break
        count += 1

#        if not entry.title in ["Template:syc-decl-noun"]:
#            continue

        if not entry.title.startswith("Template:"):
            continue

        yield entry.text, entry.title

def main():
    parser = argparse.ArgumentParser(description="Find errors in sense lists")
    parser.add_argument("target", help="target filename")
    parser.add_argument("--xml", help="XML file to load")
    parser.add_argument("--wxt", help="Wiktionary extract file to load")
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
        iter_entries = iter_wxt(args.wxt, args.limit, args.progress)
    else:
        iter_entries = iter_xml(args.xml, args.limit, args.progress)

    dump_template_args(iter_entries, args.target)


def get_included_text(text):
    text = re.sub("<!--.*?-->", "", text, flags=re.DOTALL)
    text = re.sub("<\s*noinclude\s*[/]\s*>", "", text, flags=re.DOTALL)
    text = re.sub("<\s*noinclude\s*>.*?<\s*/\s*noinclude\s*>", "", text, flags=re.DOTALL)
    text = re.sub(r"<\s*[/]?\s*includeonly\s*[/]?\s*>", "", text)

    if "onlyinclude" in text:
        text = "".join(re.findall("<\s*onlyinclude\s*>(.*?)<\s*/\s*onlyinclude\s*>", text, flags=re.DOTALL))

    return text


fixer = None
def get_template_stats(args):

    entry_text, entry_title = args
    entry_title = entry_title.removeprefix("Template:")
    entry_text = get_included_text(entry_text)

    entry_text = re.sub("{{\s*(" + "|".join(MW_COMMANDS) + ")\s*:", "", entry_text, flags=re.IGNORECASE)

    m = re.match(r"^\s*#REDIRECT[:]?\s*\[\[\s*([:]?T(?:emplate)?:(.*?))\s*\]\]", entry_text, re.IGNORECASE)
    if m:
        return entry_title, "redirect", m.group(2).strip()

    used_modules = sorted(set(m.group(1).strip() for m in re.finditer("#invoke:(.*?)[|}]", entry_text, re.DOTALL)))

    # if a module uses invoke, check if it's a pure Lua implementation or mixed
    if used_modules:
        if len(used_modules) > 1:
            template_type = "mixed"
        else:
            if re.search("{{#(^invoke)|{{{[^{}]*?}}}", entry_text):
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
        stripped = re.sub("{{\s*#[^{}]*", "", stripped)

        used_templates = []
        for m in re.finditer("{{(.*?)[{<}|]", stripped, re.DOTALL):
            if not m.group(1):
                continue
            template_name = re.sub("<!--.*?-->", "", m.group(1)).strip()
            if not template_name or "\n" in template_name:
                continue
            if template_name not in used_templates and template_name not in MAGIC_WORDS:
                used_templates.append(template_name)

    return entry_title, template_type, used_modules, used_templates, used_params


def dump_template_args(iter_entries, filename):
    global fixer
    fixer = RqTemplateFixer(None)
    iter_items = map(get_template_stats, iter_entries)

    templates = {}
    unparsable = set()
    redirects = {}
    for res in iter_items:
        template, template_type, *extra = res
        if template_type == "redirect":
            redirects[template] = extra[0]
            continue

        used_modules, used_templates, used_params = extra
        templates[template] = {k:v for k,v in [
            ("params", used_params),
            ("templates", used_templates),
            ("modules", used_modules),
        ] if v}

    with open(filename, 'w', encoding='utf-8') as outfile:
        json.dump({
            "templates": {k:v for k,v in sorted(templates.items())},
            "redirects": {k:v for k,v in sorted(redirects.items())},
            }, outfile, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()
