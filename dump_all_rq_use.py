#!/usr/bin/python3

import argparse
import multiprocessing
import os
import re
import sys
import mwparserfromhell as mwparser
from collections import defaultdict

import enwiktionary_sectionparser as sectionparser

def process(xml_entry):

    title = str(xml_entry.title)
    text = str(xml_entry.text)

#    if title != "Citations:lucre":
#        return

#    print("parsing")

#    if "{{RQ:" not in text and "{{Template:RQ:" not in text:
#        print("no text")
#        return

    matches = [line for line in sectionparser.utils.wiki_splitlines(text) if "{{RQ:" in line or "{{Template:RQ:" in line]
#    print("MATCHES", matches)

    if matches:
        return f"{xml_entry.title}:@{xml_entry.revisionid}", matches



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

    if args.j > 1:
        pool = multiprocessing.Pool(args.j)
        iter_items = pool.imap_unordered(process, iter_entries, 1000)
    else:
        iter_items = map(process, iter_entries)


    count = 0
    total = 0
    for res in iter_items:
        count += 1
        if count % 1000 == 0 and args.progress:
            print(count, total, file=sys.stderr, end="\r")
        if args.limit and count > args.limit:
            break

        if not res:
            continue

        src, matches = res
        print(f"_____{src}_____")
        for match in matches:
            total += 1
            print(match)

if __name__ == "__main__":
    main()
