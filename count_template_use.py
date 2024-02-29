#!/usr/bin/python3

import argparse
import multiprocessing
import os
import re
import sys

from collections import defaultdict

def iter_xml(datafile, limit=None, show_progress=False):
    from pywikibot import xmlreader
    dump = xmlreader.XmlDump(datafile)
    parser = dump.parse()

    count = 0
    for entry in parser:
        if not count % 100 and show_progress:
            print(count, end = '\r', file=sys.stderr)

        if limit and count >= limit:
            break
        count += 1

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

        yield entry.text, entry.title

def main():
    parser = argparse.ArgumentParser(description="Dump L2 entries containing {{taxon}}")
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

    if args.j > 1:
        pool = multiprocessing.Pool(args.j)
        iter_items = pool.imap_unordered(process, iter_entries, 10000)
    else:
        iter_items = map(process, iter_entries)

    template_count = defaultdict(int)
    for results in iter_items:
        if not results:
            continue

        for template, count in results:
            template_count[template] += 1

    for template, count in sorted(template_count.items(), key=lambda x: (x[1], x[0])):
        print(f"{template}\t{count}")

def process(args):

    entry_text, entry_title = args

    if entry_title.startswith("Module:"):
        return

    # Strip {{{vars}}} and {{#commands: from templates
    if entry_title.startswith("Template:"):
        prev_text = None
        while prev_text != entry_text:
            prev_text = entry_text
            entry_text = re.sub(r"\{\{\{[^{}]*", "", entry_text)
        entry_text = re.sub("{{\s*#[^{}]*", "", entry_text)

    template_count = defaultdict(int)
    for m in re.finditer("{{(.*?)[{<}|]", entry_text, re.DOTALL):
        if not m.group(1):
            continue
        template_name = re.sub("<!--.*?-->", "", m.group(1)).strip()
        if template_name and "\n" not in template_name:
            template_count[template_name] += 1


    return [(template, count) for template, count in template_count.items()]


if __name__ == "__main__":
    main()
