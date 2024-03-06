#!/usr/bin/python3

import argparse
import multiprocessing
import os
import re
import sys

from autodooz.fix_list_to_col import ListToColFixer
from autodooz.utils import iter_wxt
from autodooz.wikilog import WikiLogger, BaseHandler
from collections import defaultdict, namedtuple

class WikiSaver(BaseHandler):

    def sort_items(self, items):
        count = defaultdict(int)
        for item in items:
            count[(item.lang_id, item.error)] += 1

        # sort autofix sections first so they can be split into other pages
        # everything else sorted by count of section entries (smallest to largest)
        return sorted(items, key=lambda x: (x.lang_id, "autofix" not in x.error, count[(x.lang_id, x.error)], x.error, x.page))

    def is_new_section(self, item, prev_item):
        return prev_item and prev_item.error != item.error

    def is_new_page(self, page_sections, section_entries):
        # Page break between languages
        if page_sections and (page_sections[-1][-1].lang_id != section_entries[0].lang_id):
            return True
        # Page break fixes/errors
        return page_sections and (page_sections[-1][-1].error.startswith("autofix") != section_entries[0].error.startswith("autofix"))

    def page_name(self, page_sections, prev):
        item = page_sections[0][0]
        if "autofix" in item.error:
            return f"{item.lang_id}/der_rel_terms/fixes"
        else:
            return f"{item.lang_id}/der_rel_terms/errors"

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

class FileSaver(WikiSaver):

    def save_page(self, dest, page_text):
        dest = dest.lstrip("/").replace("/", "_")
        with open(dest, "w") as outfile:
            outfile.write(page_text)
            print("saved", dest)

    def save(self, *args, **nargs):
        super().save(*args, **nargs, commit_message=None)

class Logger(WikiLogger):
    _paramtype = namedtuple("params", [ "error", "page", "lang_id", "details" ])

logger = Logger()
def log(error, page, lang_id, details=None):
    logger.add(error, page, lang_id, details)

fixer = None
def process(args):
    # Needed to unpack args until Pool.istarprocess exists
    text, title, options = args
    return fixer.process(text, title, options=options)

def main():
    global fixer
    parser = argparse.ArgumentParser(description="Find Spanish nouns with manually specified forms")
    parser.add_argument("wxt", help="Wiktionary extract file")
    parser.add_argument("--limit", type=int, help="Limit processing to first N articles")
    parser.add_argument("--progress", help="Display progress", action='store_true')
    parser.add_argument("--save", help="Save to wiktionary with specified commit message")
    parser.add_argument("--lang", help="Operate on selected language (can be used multiple times)", action='append', required=True)
    parser.add_argument("--section", help="Operate on selected section (can be used multiple times)", action='append', required=True)

    parser.add_argument("-j", help="run N jobs in parallel (default = # CPUs - 1", type=int)
    args = parser.parse_args()

    fixer = ListToColFixer()

    if not args.j:
        args.j = multiprocessing.cpu_count()-1

    options = { "lang_ids": args.lang, "sections": args.section }
    iter_entries = iter_wxt(args.wxt, args.limit, args.progress, options)

    if args.j > 1:
        pool = multiprocessing.Pool(args.j)
        iter_items = pool.imap_unordered(process, iter_entries, 10)
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
