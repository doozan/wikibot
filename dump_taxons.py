#!/usr/bin/python3

import argparse
import enwiktionary_sectionparser as sectionparser
import mwparserfromhell as mwparser
import multiprocessing
import os
import re
import sys
import json
import csv

from autodooz.fix_missing_taxlinks import MissingTaxlinkFixer
from autodooz.wikilog import WikiLogger, BaseHandler
from collections import defaultdict, namedtuple
from autodooz.utils import iter_xml, iter_wxt

def process(args):

    entry_text, entry_title = args

    wikt = sectionparser.parse(entry_text, entry_title)
    if not wikt:
        return

    multi_l2 = any(wikt.ifilter_sections(recursive=False, matches=lambda x: x.title != "Translingual"))

    res = []
    for section in wikt.ifilter_sections(recursive=False):
        section_str = str(section)
        if "taxon" not in section_str:
            continue

        if re.search("\{\{\s*taxon\s*[|}]", section_str):
            if not section.path in ["English", "Translingual"]:
                print("unexpected taxon", entry_title, section.path, file=sys.stderr)

            flagged_path = section.path + "~" if multi_l2 else section.path
            res.append((entry_title, flagged_path, section_str))

    return res

def print_entries(results):
    prev_path = None
    for entry_title, section_path, data in results:
        path = f"{entry_title}:{section_path}"
        if path != prev_path:
            print(f"_____{path}_____")
            prev_path = path
        print(data)

def main():
    global fixer
    parser = argparse.ArgumentParser(description="Find errors in sense lists")
    parser.add_argument("--xml", help="XML file to load")
    parser.add_argument("--wxt", help="Wiktionary extract file to load")
    parser.add_argument("--limit", type=int, help="Limit processing to first N articles")
    parser.add_argument("--progress", help="Display progress", action='store_true')
    parser.add_argument("-j", help="run N jobs in parallel (default = # CPUs - 1", type=int)
    args = parser.parse_args()


    if not args.j:
        args.j = multiprocessing.cpu_count()-1

    if (not args.xml and not args.wxt) or (args.xml and args.wxt):
        print("use either --xml or --wxt")
        exit(1)

    if args.wxt:
        iter_entries = iter_wxt(args.wxt, args.limit, args.progress, title_matches=lambda x: ":" not in x and "/" not in x, text_matches=lambda x: "taxon" in x)
    else:
        iter_entries = iter_xml(args.xml, args.limit, args.progress, title_matches=lambda x: ":" not in x and "/" not in x, text_matches=lambda x: "taxon" in x)

    if args.j > 1:
        pool = multiprocessing.Pool(args.j)
        iter_items = pool.imap_unordered(process, iter_entries, 100)
    else:
        iter_items = map(process, iter_entries)

    for res in iter_items:
        if not res:
            continue
        print_entries(res)

if __name__ == "__main__":
    main()
