#!/usr/bin/python3

import argparse
import csv
import json
import multiprocessing
import mwparserfromhell as mwparser
import os
import re
import sys

import enwiktionary_sectionparser as sectionparser

from autodooz.escape_template import escape, unescape
from autodooz.utils import iter_xml, iter_wxt

def clean_name(obj):
    text = re.sub(r"<!--.*?-->", "", unescape(str(obj.name)), flags=re.DOTALL)
    return text.strip()

def main():
    parser = argparse.ArgumentParser(description="Find errors in sense lists")
    parser.add_argument("--xml", help="XML file to load")
    parser.add_argument("--wxt", help="Wiktionary extract file to load")
    parser.add_argument("-t", help="template name", action='append')
    parser.add_argument("--redirects", help="TSV with redirect data")
    #parser.add_argument("-tx", help="template regex", action='append')
    parser.add_argument("--wikiline", help="Dump the entire line containing the template", action='store_true')
    parser.add_argument("--limit", type=int, help="Limit processing to first N articles")
    parser.add_argument("--progress", help="Display progress", action='store_true')
    parser.add_argument("-j", help="run N jobs in parallel (default = # CPUs - 1", type=int)
    args = parser.parse_args()

    if (not args.xml and not args.wxt) or (args.xml and args.wxt):
        print("use either --xml or --wxt")
        exit(1)

    if not args.j:
        args.j = multiprocessing.cpu_count()-1

    redirects = {}
    if args.redirects:
        with open(args.redirects) as infile:
            redirects = {x[0].removeprefix("Template:"):x[1].removeprefix("Template:") for x in csv.reader(infile, delimiter="\t") if x[1].startswith("Template:") and x[1].removeprefix("Template:") in args.t}

    template_names = sorted(args.t + list(redirects.keys()))

#    print("extracting", redirects.keys(), file=sys.stderr)
#    exit()

    if args.wxt:
        iter_entries = iter_wxt(args.wxt, args.limit, args.progress, template_names, args.wikiline)
    else:
        iter_entries = iter_xml(args.xml, args.limit, args.progress, template_names, args.wikiline)

    if args.j > 1:
        pool = multiprocessing.Pool(args.j)
        iter_items = pool.imap_unordered(process, iter_entries, 100)
    else:
        iter_items = map(process, iter_entries)



    prev_path = None
    for results in iter_items:
        if not results:
            continue

        for entry_title, section_path, template in results:
            path = f"{entry_title}#{section_path}" if section_path is not None else entry_title
            if path != prev_path:
                print(f"_____{path}_____")
                prev_path = path
            print(template)


def process(args):

    entry_text, entry_title, templates, dump_wikiline = args

    if not any(t in entry_text for t in templates):
        return

    if "{{{" in entry_text or "{{#" in entry_text:
        # Don't treat pages that already contain the 'escape' characters
        if unescape(entry_text) != entry_text:
            print(entry_title, "uses escape char", file=sys.stderr)
            return entry_text
        entry_text = escape(entry_text, escape_comments=False)

    try:
        res = []
        include_section = False
        if include_section:
            wikt = sectionparser.parse(entry_text, entry_title)
            if not wikt:
                print("unparsable", file=sys.stderr)
                return

            for section in wikt.ifilter_sections(recursive=False):

                section_str = str(section)
                if not any(t in section_str for t in templates):
                    return

                if dump_wikiline:
                    for wikiline in section.content_wikilines:
                        wiki = mwparser.parse(section_str)
                        if any(t for t in wiki.ifilter_templates(matches=lambda x: clean_name(x) in templates)):
                            res.append((entry_title, section.path, unescape(wikiline)))
                else:
                    wiki = mwparser.parse(section_str)
                    res += [(entry_title, section.path, unescape(str(t))) for t in wiki.ifilter_templates(matches=lambda x: clean_name(x) in templates)]
        else:
            wiki = mwparser.parse(entry_text)
            res += [(entry_title, None, unescape(str(t))) for t in wiki.ifilter_templates(matches=lambda x: clean_name(x) in templates)]

    except Exception as e:
        entry_text, entry_title, *_ = args
        print("Failed processing", entry_title)
        raise e

    return res

if __name__ == "__main__":
    main()
#    for k,v in sorted(invoke_count.items(), key=lambda x: (x[1], x[0])):
#        print(v, k)
