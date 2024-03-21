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
from autodooz.utils import iter_xml, iter_wxt

namespaces = {
    "Talk": ["talk"],
    "User": ["user"],
    "User talk": ["user talk"],
    "Wiktionary": ["wt", "wiktionary"],
    "Wiktionary talk": ["wiktionary talk"],
    "File": ["file", "image"],
    "File talk": ["file talk", "image talk"],
    "Mediawiki": ["mediawiki"],
    "Template": ["t", "template"],
    "Template talk": ["template talk"],
    "Help": ["help"],
    "Help talk": ["help talk"],
    "Category": ["cat", "c", "category"],
    "Category talk": ["category talk"],
    "Thread": ["thread"],
    "Thread talk": ["thread talk"],
    "Summary": ["summary"],
    "Summary talk": ["summary talk"],
    "Appendix": ["ap", "appendix"],
    "Appendix talk": ["appendix talk"],
    "Rhymes": ["rhymes"],
    "Rhymes talk": ["rhymes talk"],
    "Transwiki": ["transwiki"],
    "Transwiki talk": ["transwiki talk"],
    "Thesaurus": ["ws", "thesaurus", "wikisaurus"],
    "Thesaurus talk": ["thesaurus talk", "wikisaurus talk"],
    "Citations": ["citations"],
    "Citations talk": ["citations talk"],
    "Sign gloss": ["sign gloss"],
    "Sign gloss talk": ["sign gloss talk"],
    "Reconstruction": ["rc", "reconstruction"],
    "Reconstruction talk": ["reconstruction talk"],
    "Module": ["mod", "module"],
    "Module talk": ["module talk"],
}
ns_aliases = [alias for aliases in namespaces.values() for alias in aliases]

def process(args):
    entry_text, entry_title = args

    m = re.match(r"^\s*(?:#REDIRECT|return\s+require)[:]?\s*\[\[\s*(.+?)\s*\]\]", entry_text, re.IGNORECASE)
    if not m:
        print("BAD REDIRECT:", [entry_title, entry_text], file=sys.stderr)
        return

    target = m.group(1)
    if ":" in target:
        m = re.match("([:]?(" + "|".join(ns_aliases) + ")):", target, re.IGNORECASE)
        if m:
            old = m.group(1)
            alias = old.lstrip(":").lower()
            new = [k for k,v in namespaces.items() if alias in v]
            assert len(new) == 1
            new = new[0]
            target = new + target.removeprefix(old)

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
