#!/usr/bin/python3

import argparse
import multiprocessing
import os
import re
import sys

from autodooz.fix_bare_quotes import QuoteFixer
from autodooz.utils import iter_wxt
from autodooz.wikilog import WikiLogger, BaseHandler
from collections import defaultdict, namedtuple
from enwiktionary_wordlist.wordlist import Wordlist

class WikiSaver(BaseHandler):

    def sort_items(self, items):
        count = defaultdict(int)
        for item in items:
            count[item.error] += 1

        # sort autofix sections first so they can be split into other pages
        # everything else sorted by count of section entries (smallest to largest)
        return sorted(items, key=lambda x: ("autofix" not in x.error, count[x.error], x.error, x.page))

    def is_new_section(self, item, prev_item):
        return prev_item and prev_item.error != item.error

    def is_new_page(self, page_sections, section_entries):
        return page_sections and (page_sections[-1][-1].error.startswith("autofix") != section_entries[0].error.startswith("autofix"))

    def page_name(self, page_sections, prev):
        if "autofix" in page_sections[0][0].error:
            return "bare_quotes/fixes"
        else:
            return "bare_quotes/errors"

    def format_entry(self, entry, prev_entry):
        if entry.details:
            return [f": [[{entry.page}]] <nowiki>{entry.details}</nowiki>"]
        return [f": [[{entry.page}]]"]

    def get_section_header(self, base_path, page_name, section_entries, prev_section_entries, pages):
        res = []

        item = section_entries[0]
        count = len(section_entries)

        if prev_section_entries:
            res.append("")
        res.append(f"==={item.error}===")
        res.append(f"; {count} item{'s' if count>1 else ''}")
        return res

    # Error page exceeds the 2M limit on wiktionary, so skip it
    def save_page(self, dest, page_text):
        if "error" in dest:
            return
        super().save(dest, page_text)


class FileSaver(WikiSaver):

    def save_page(self, dest, page_text):
        dest = dest.lstrip("/").replace("/", "_")
        with open(dest, "w") as outfile:
            outfile.write(page_text)
            print("saved", dest)

    def save(self, *args, **nargs):
        super().save(*args, **nargs, commit_message=None)

class Logger(WikiLogger):
    _paramtype = namedtuple("params", [ "error", "page", "details" ])

logger = Logger()
def log(error, page, details=None):
    logger.add(error, page, details)

fixer = None
def process(args):
    # Needed to unpack args until Pool.istarprocess exists
    return fixer.process(*args)

from enwiktionary_sectionparser.posparser import BARE_QUOTE_LINE_RX
def dump_targets(args):
    text, title = args
    for prefix, quote in re.findall(BARE_QUOTE_LINE_RX, text):
        print(quote)

def main():
    global fixer
    parser = argparse.ArgumentParser(description="Find Spanish nouns with manually specified forms")
    parser.add_argument("wxt", help="Wiktionary extract file")
    parser.add_argument("--limit", type=int, help="Limit processing to first N articles")
    parser.add_argument("--progress", help="Display progress", action='store_true')
    parser.add_argument("--dump-targets", help="Dump all lines that might be bare quotes", action='store_true')
    parser.add_argument("--save", help="Save to wiktionary with specified commit message")
    parser.add_argument("-j", help="run N jobs in parallel (default = # CPUs - 1", type=int)
    args = parser.parse_args()

    fixer = QuoteFixer()

    if not args.j:
        args.j = multiprocessing.cpu_count()-1

    iter_entries = iter_wxt(args.wxt, args.limit, args.progress)

    if args.dump_targets:
        pool = multiprocessing.Pool(args.j)
        for item in pool.imap_unordered(dump_targets, iter_entries, 1000):
            pass
        exit()

    if args.j > 1:
        pool = multiprocessing.Pool(args.j)
        iter_items = pool.imap_unordered(process, iter_entries, 1000)
    else:
        iter_items = map(process, iter_entries)

    for results in iter_items:
        for log_values in results:
            log(*log_values)

    if args.save:
        base_url = f"User:JeffDoozan/lists"
        logger.save(base_url, WikiSaver, commit_message=args.save)
    else:
        dest = ""
        logger.save(dest, FileSaver)

if __name__ == "__main__":
    main()
