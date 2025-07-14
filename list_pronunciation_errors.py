#!/usr/bin/python3

import argparse
import multiprocessing
import os
import re
import sys

from autodooz.fix_pronunciation import PronunciationFixer
from autodooz.utils import iter_wxt
from autodooz.wikilog import WikiLogger, BaseHandler
from collections import defaultdict, namedtuple

class WikiSaver(BaseHandler):

    def sort_items(self, items):
        count = defaultdict(int)

        unique = []
        seen = set()
        for item in items:
            # Skip big pages for now
            if item.error in [
                "text",
                "leading_text",
                "trailing_text",
                "multi_templates",
                "unhandled_single_template",
                "single_ipa_unhandled_template",
                "single_ipa_unhandled_common_template",
                "single_ipa_unhandled_qualifier",
                ]:
                    continue
            if item not in seen:
                seen.add(item)
                count[item.error] += 1
                unique.append(item)

        # sort autofix sections first so they can be split into other pages
        # everything else sorted by count of section entries (smallest to largest)
        return sorted(unique, key=lambda x: ("autofix" not in x.error, count[x.error], x.error, x.page))

    def is_new_section(self, item, prev_item):
        return prev_item and prev_item.error != item.error

    def is_new_page(self, page_sections, section_entries):
        # only two pages, autofixes and errors
        return page_sections[-1][-1].error.startswith("autofix") and not section_entries[0].error.startswith("autofix")
        #return page_sections and not section_entries[0].error.startswith("autofix")

    def page_name(self, page_sections, prev):
        if "autofix" in page_sections[0][0].error:
            return "pronunciation/fixes"
        else:
            return "pronunciation/errors"

    def format_entry(self, entry, prev_entry):
        if "autofix" in entry.error:
            return [f": [[{entry.page}]] {entry.section} {entry.location}"]

        if entry.details:
            return [f": [[{entry.page}#{entry.language}|{entry.page}]] {entry.section} {entry.location}\n<pre>{entry.details}</pre>"]
        else:
            return [f": [[{entry.page}#{entry.language}|{entry.page}]] {entry.section} {entry.location}"]

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
    _paramtype = namedtuple("params", [ "error", "page", "language", "section", "location", "details" ])

logger = Logger()
def log(error, page, section, location, details=None):
    lang, _, _ = section.partition(":")
    logger.add(error, page, lang, section, location, details)

fixer = None
def process(args):
    # Needed to unpack args until Pool.istarprocess exists
    return fixer.process(*args)

def main():
    global fixer
    parser = argparse.ArgumentParser(description="Find errors in sense lists")
    parser.add_argument("wxt", help="Wiktionary extract file")
    parser.add_argument("--limit", type=int, help="Limit processing to first N articles")
    parser.add_argument("--progress", help="Display progress", action='store_true')
    parser.add_argument("--save", help="Save to wiktionary with specified commit message")
    parser.add_argument("-j", help="run N jobs in parallel (default = # CPUs - 1", type=int)
    args = parser.parse_args()

    fixer = PronunciationFixer()

    if not args.j:
        args.j = multiprocessing.cpu_count()-1

    iter_entries = iter_wxt(args.wxt, args.limit, args.progress)

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
        logger.save(base_url, WikiSaver, commit_message=args.save, index_url="")
    else:
        dest = ""
        logger.save(dest, FileSaver)

if __name__ == "__main__":
    main()
