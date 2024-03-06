#!/usr/bin/python3

import argparse
import json
import multiprocessing
import os
import re
import sys

from autodooz.fix_rq_template import RqTemplateFixer
from autodooz.utils import iter_wxt, iter_xml
from pywikibot import xmlreader

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
        iter_entries = iter_wxt(args.wxt, args.limit, args.progress, title_matches=lambda x: x.startswith("Template:RQ")
    else:
        iter_entries = iter_xml(args.xml, args.limit, args.progress, title_matches=lambda x: x.startswith("Template:RQ")

    dump_template_args(iter_entries, args.target)

fixer = None
def get_allowed_params(args):

    entry_text, entry_title = args

    m = re.match(r"^#REDIRECT[:]?\s+\[\[\s*(Template:RQ:.*?)\s*\]\]", entry_text, re.IGNORECASE)
    if m:
        return entry_title.removeprefix("Template:"), {"redir": m.group(1).removeprefix("Template:")}

    new_text = fixer.process(entry_text, entry_title, [])
    if not new_text:
        return

    ALLOWED_INVOKE = [ "quote", "string" ]
    invokes = [m.group(1).strip() for m in re.finditer("{{#invoke:(.*?)[|}]", new_text, re.DOTALL)]
    if not all(i in ALLOWED_INVOKE for i in invokes):
        return

    if not "{{#invoke:quote" in new_text:
        #print("no quote invoke")
        return

    auto_props = fixer.get_auto_props(new_text, entry_title)
    if auto_props is None:
        print("failed extracting auto props")
        return

    manual_props = fixer.get_params("propagateparams", new_text, entry_title)
    if manual_props is None:
        print("failed parsing propagateparams")
        return

    used_params = fixer.get_used_params(new_text)
    declared_params = fixer.get_declared_params(new_text)

    #print(entry_text)
    #print("-----------")
    #print(new_text)
    #print(used_params, declared_params, auto_props, manual_props)

#    print(auto_props, manual_props, used_params, declared_params)
    allowed_params = sorted(set(auto_props + manual_props + used_params + declared_params))

    entry_title = entry_title.removeprefix("Template:")

    return entry_title, allowed_params



def dump_template_args(iter_entries, filename):
    global fixer
    fixer = RqTemplateFixer(None)
    iter_items = map(get_allowed_params, iter_entries)

    templates = {}
    for res in iter_items:
        if not res:
            continue
        entry_title, allowed_params = res
        templates[entry_title] = allowed_params

    templates = {k:v for k,v in sorted(templates.items())}

    # Resolve the redirects. If they redirect to a good template, copy data from that template
    # if they redirect to an unhandled template, delete them
    to_remove = []
    for k, v in templates.items():
        if "redir" in v:
            if v["redir"] in templates:
                templates[k] = templates[v["redir"]]
            else:
                to_remove.append(k)

    for k in to_remove:
        del templates[k]

    with open(filename, 'w', encoding='utf-8') as outfile:
        json.dump(templates, outfile, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()
