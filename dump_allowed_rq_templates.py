#!/usr/bin/python3

import argparse
import multiprocessing
import os
import re
import sys
import mwparserfromhell as mwparser
from collections import defaultdict


def remove_pound_brackets(text):
    while "{{#" in text:
        depth = 0
        start = text.index("{{#")
        end = 0
        for m in re.finditer("(\{|\})", text[start:]):
            if m.group(0) == "{":
                depth += 1
            if m.group(0) == "}":
                depth -= 1
                if depth == 0:
                    end = m.end()
                    break
        if end:
            text = text[:start] + text[start+end:]
        else:
            break

    return text


#    ital = "(?<!')(?:'{2}|'{5})(?!')"
#    return re.match(fr"{ital}.*{ital}$", text) and not re.search(ital, text[2:-2])


def get_included_text(text):
    text = re.sub("<\s*noinclude\s*>.*?<\s*/\s*noinclude\s*>", "", text, flags=re.DOTALL)
    text = re.sub(r"<\s*(/)?\s*includeonly\s*>", "", text)
    return text


def rq_template_uses_invoke(text):
    text = get_included_text(text)

    if "#invoke:quote" in text:
        return True

def rq_template_uses_template(text):
    text = get_included_text(text)

    return "{{quote-" in text or "{{RQ:" in text

def rq_template_supports_params(text):
    text = get_included_text(text)

    if rq_template_uses_invoke(text):
        return True
        #return bool(re.search(r"\|\s*allowparams\s*=\s*\*", text))

    elif not rq_template_uses_template(text):
        return False

    # strip {{# items to improve mwparser parsing
    mini_text = remove_pound_brackets(text)
    #print(mini_text)
    wiki = mwparser.parse(mini_text)
    for t in wiki.ifilter_templates(matches=lambda x: x.name.startswith(("quote-", "RQ:"))):

        #print("---")
        #print(t.name)
        #for p in t.params:
        #    print("  ", p.name)
        #exit()

        if t.name.startswith("quote-") and t.has(1):
            lang_id = t.get(1).strip()
        elif t.name.startswith("RQ:"):
            lang_id = "en"
        else:
            print(t.name, "NO LANG ID", file=sys.stderr)
            return False

        has_passage = any(t.has(p) for p in ["passage", "text"]) and "{{passage" in text
        has_translation = any(t.has(p) for p in ["translation", "t"]) and "{{translation" in text
        if has_passage and (lang_id == "en" or has_translation):
            return True

#        if not has_passage and re.search("|passage\s*=", text) and "{{passage" in text:
#            print(entry_title, file=sys.stderr)

#        if lang_id != "en" and not any(t.has(p) for p in ["tr", "translit", "transliteration"]):
#            print(entry_title, "NO TRANSLITERATION", lang_id, file=sys.stderr)




import pywikibot
site = pywikibot.Site('wiktionary:en')
def iter_search(text, limit=None, show_progress=False):
    count = 0
    for item in site.search(text, total=limit):
        count += 1
        if not count % 10 and show_progress:
            print(count, end = '\r', file=sys.stderr)
        yield item


def process(entry):

    entry_title = str(entry.title)
    entry_text = str(entry.text)

    if not entry_title.startswith("Template:"):
        return

    if "/" in entry_title:
        return

    m = re.match(r"^#REDIRECT[:]?\s+\[\[\s*(Template:RQ:.*?)\s*\]\]", entry_text, re.IGNORECASE)
    if m:
        return "redir", m.group(1), entry_title

    if not entry_title.startswith("Template:RQ:"):
        return

    if rq_template_uses_invoke(entry_text) and rq_template_supports_params(entry_text):
        print(";[[" + entry_title + "]]: allowparams = " + ",".join(get_used_params(entry_text)))
        return "module", entry_title

    elif rq_template_uses_template(entry_text) and rq_template_supports_params(entry_text):
        return "template", entry_title

def main():

    parser = argparse.ArgumentParser(description="Find RQ templates that can handle passage= parameters")
    parser.add_argument("xml", help="XML file to load")
    parser.add_argument("--limit", type=int, help="Limit processing to first N articles")
    parser.add_argument("--progress", help="Display progress", action='store_true')
    parser.add_argument("-j", help="run N jobs in parallel (default = # CPUs - 1", type=int)
    args = parser.parse_args()

    if not args.j:
        args.j = multiprocessing.cpu_count()-1

    from pywikibot import xmlreader
    dump = xmlreader.XmlDump(args.xml)
    iter_entries = dump.parse()

    #search = "-intitle:/\// -insource:/#invoke/ -insource:/\{\{\{/ prefix:Template:RQ:"
    #iter_entries = iter_search(search, args.limit, args.progress)

    count = 0
    total = 0
    mod = 0
    tl = 0

    redirect_targets = defaultdict(set)
    valid_module_templates = set()
    valid_wiki_templates = set()

    if args.j > 1:
        pool = multiprocessing.Pool(args.j)
        iter_items = pool.imap_unordered(process, iter_entries, 1000)
    else:
        iter_items = map(process, iter_entries)


    count = 0
    for res in iter_items:
        count += 1
        if count % 1000 == 0 and args.progress:
            print(count, file=sys.stderr, end="\r")
        if args.limit and count > args.limit:
            break

        if not res:
            continue
        template_type, *values = res
        if template_type == "redir":
            target, template_name = values
            redirect_targets[target].add(template_name)
        elif template_type == "module":
            template_name = values[0]
            valid_module_templates.add(template_name)
        elif template_type == "template":
            template_name = values[0]
            valid_wiki_templates.add(template_name)
        else:
            raise ValueError("unhandled response", res)

    exit()

    for k in valid_module_templates & redirect_targets.keys():
        valid_module_templates |= redirect_targets[k]

    print("RQ_INVOKE_TEMPLATES = {")
    for template in sorted(valid_module_templates):
        print(f'    "{template.removeprefix("Template:")}",')
    print("}")

    for k in valid_wiki_templates & redirect_targets.keys():
        valid_wiki_templates |= redirect_targets[k]

    print("RQ_OTHER_TEMPLATES = {")
    for template in sorted(valid_wiki_templates):
        print(f'    "{template.removeprefix("Template:")}",')
    print("}")

    print("dumped", len(valid_wiki_templates)+len(valid_module_templates), file=sys.stderr)

if __name__ == "__main__":
    main()
