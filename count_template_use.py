#!/usr/bin/python3

import argparse
import csv
import multiprocessing
import os
import re
import sys

from collections import defaultdict
from autodooz.utils import iter_xml, iter_wxt

def main():
    parser = argparse.ArgumentParser(description="Dump L2 entries containing {{taxon}}")
#    parser.add_argument("fixable_templates", help="fixable templates")
    parser.add_argument("--xml", help="XML file to load")
    parser.add_argument("--wxt", help="Wiktionary extract file to load")
    parser.add_argument("--redirects", help="TSV with redirect data", required=True)

    parser.add_argument("--debug", help="dump individual template count for single page")
    parser.add_argument("--include", help="Only count templates listed in the given tsv", action='append')
    parser.add_argument("--exclude", help="Don't count templates listed in the given tsv", action='append')

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

    if args.j > 1:
        pool = multiprocessing.Pool(args.j)
        iter_items = pool.imap_unordered(process, iter_entries, 10000)
    else:
        iter_items = map(process, iter_entries)

    with open(args.redirects) as infile:
        redirects = {x[0].removeprefix("Template:"):x[1].removeprefix("Template:") for x in csv.reader(infile, delimiter="\t") if x[0].startswith("Template:")}

    include = set()
    if args.include:
        for filename in args.include:
            with open(filename) as infile:
                include |= {x[0] for x in csv.reader(infile, delimiter="\t")}

    exclude = set()
    if args.exclude:
        for filename in args.exclude:
            with open(filename) as infile:
                exclude |= {x[0] for x in csv.reader(infile, delimiter="\t")}

    page_mode = include or exclude

    template_total = defaultdict(int)
    template_pages = defaultdict(int)

    for results in iter_items:
        if not results:
            continue

        entry_title, template_count = results

        page_count = 0
        for template, count in template_count.items():

            template = redirects.get(template, template)

            if include and template not in include:
                continue

            if exclude and template in exclude:
                continue

            template_pages[template] += 1
            template_total[template] += count
            page_count += count

            if args.debug and entry_title == args.debug:
                print(f"{template}\t{count}", file=sys.stderr)

        if page_mode:
            print(f"{entry_title}\t{page_count}")


    if not page_mode:
        for template, count in sorted(template_total.items(), key=lambda x: (x[1], x[0])):
            page_count = template_pages[template]
            print(f"{template}\t{count}\t{page_count}")

def process(args):

    entry_text, entry_title = args

    if entry_title.startswith("Module:"):
        return

#    if entry_title == "Ixora":
#        print(len(entry_text), file=sys.stderr)
    #entry_text = re.sub("<!--.*?-->", "", entry_text, flags=re.DOTALL)
#    if entry_title == "Ixora":
#        print(len(entry_text), file=sys.stderr)

    # Strip {{{vars}}} and {{#commands: from templates
    if entry_title.startswith("Template:"):
        prev_text = None
        while prev_text != entry_text:
            prev_text = entry_text
            entry_text = re.sub(r"\{\{\{[^{}]*", "", entry_text)
        entry_text = re.sub("{{\s*#[^{}]*", "", entry_text)

    template_count = defaultdict(int)
    for m in re.finditer("{{(.*?)(?=[#{<}|])", entry_text, re.DOTALL):
        if not m.group(1):
            continue
        template_name = re.sub("<!--.*?-->", "", m.group(1)).strip()
        if template_name and "\n" not in template_name:
            template_count[template_name] += 1

    return entry_title, template_count

if __name__ == "__main__":
    main()
