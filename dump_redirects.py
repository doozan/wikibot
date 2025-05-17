#!/usr/bin/python3

import argparse
import csv
import json
import multiprocessing
import mwparserfromhell as mwparser
import os
import re
import sys

from autodooz.utils import iter_xml, iter_wxt, split_namespace

def process(args):
    entry_text, entry_title = args

    m = re.match(r"^\s*(?:#REDIRECT|return\s+require)[:]?\s*\[\[\s*(.+?)\s*\]\]", entry_text, re.IGNORECASE)
    if not m:
        print("BAD REDIRECT:", [entry_title, entry_text], file=sys.stderr)
        return

    target = m.group(1)
    namespace, target = split_namespace(target)

    return entry_title, target

def main():
    parser = argparse.ArgumentParser(description="Find errors in sense lists")
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
        iter_items = pool.imap_unordered(process, iter_entries, 100)
    else:
        iter_items = map(process, iter_entries)

    redirects = {}
    for results in iter_items:
        if not results:
            continue

        entry_title, target = results
        redirects[entry_title] = target


    writer = csv.writer(sys.stdout, delimiter='\t', lineterminator='\n')
    for src, target in sorted(redirects.items()):
        writer.writerow([src,target])

if __name__ == "__main__":
    main()
