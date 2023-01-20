#!/usr/bin/python3

import pywikibot
import re
import sys

from autodooz.fix_section_order import SectionOrderFixer
from autodooz.wikilog import WikiLogger, BaseHandler
from collections import namedtuple

ALL_FIXES = {
    "l2_sort": "Unsorted L2 sections",
    "l3_sort": "Unsorted L3 sections",
    "pos_sort": "Unsorted POS sections",
}

ALL_ERRORS = {
    "dup_sections": "Duplicate L3 sections",
    "unexpected_child": "Unexpected child section",
}

ALL_TITLES = ALL_ERRORS | ALL_FIXES

class WikiSaver(BaseHandler):

    def sort_items(self, items):
        return sorted(set(items), key=lambda x: (x.error in ALL_FIXES, x.error, x.page))

    def is_new_section(self, item, prev_item):
        return prev_item and prev_item.error != item.error

    def is_new_page(self, page_sections, section_entries):
        return page_sections[0][0].error not in ALL_FIXES

    def page_name(self, page_sections, prev):
        if page_sections[0][0].error in ALL_FIXES:
            return "fixes"
        else:
            return page_sections[0][0].error

    def get_section_header(self, base_path, page_name, section_entries, prev_section_entries, pages):
        res = []
        item = section_entries[0]
        prev_item = prev_section_entries[-1] if prev_section_entries else None
        if not prev_item or prev_item.error != item.error:
            title = ALL_TITLES[item.error] if item.error in ALL_TITLES else item.error
            res.append(f"==={title}===")
            count = sum(map(len, [x for x in pages[page_name] if x[0].error == item.error]))
            res.append(f"{count} item{'s' if count>1 else ''}<br>")

        return res

    def format_entry(self, entry, prev_entry):
        page = entry.page
        section = entry.section if entry.section else ""
        return [f": [[{page}]] {section} {entry.details}"]

    # Add empty pages if they generated no errors
    def make_pages(self, *args, **nargs):
        pages = super().make_pages(*args, **nargs)
        for error in ALL_ERRORS.keys():
            if error not in pages:
                pages[error] = []
        return pages

    def page_header(self, base_path, page_name, page_sections, pages):
        if page_sections:
            return []

        # Generate something for blank pages
        title = ALL_TITLES[page_name] if page_name in ALL_TITLES else page_name
        return [f"==={title}===", "0 items"]

    _paramtype = namedtuple("params", [ "error", "page", "section", "details" ])

class FileSaver(WikiSaver):

    def save_page(self, dest, page_text):
        dest = dest.lstrip("/").replace("/", "_")
        with open(dest, "w") as outfile:
            outfile.write(page_text)
            print("saved", dest)

    def save(self, *args, **nargs):
        super().save(*args, **nargs, commit_message=None)

class Logger(WikiLogger):
    _paramtype = namedtuple("params", [ "error", "page", "section", "details" ])

logger = Logger()
def log(error, page, section, details):
    logger.add(error, page, section, details)

def main():

    import argparse

    parser = argparse.ArgumentParser(description="Find fixable entries")
    parser.add_argument("wxt", help="Wiktionary extract file")
    parser.add_argument("--save", help="Save to wiktionary with specified commit message")
    parser.add_argument("--limit", type=int, help="Limit processing to first N articles")
    parser.add_argument("--progress", help="Display progress", action='store_true')
    args = parser.parse_args()

    from enwiktionary_wordlist.wikiextract import WikiExtractWithRev
    parser = WikiExtractWithRev.iter_articles_from_bz2(args.wxt)

    fixer = SectionOrderFixer()
    fixer._log = log

    count = 0
    for page in parser:
        count += 1
        if count % 1000 == 0 and args.progress:
            print(count, file=sys.stderr, end="\r")
        if args.limit and count > args.limit:
            break

        fixer.process(page.text, page.title)

    if args.save:
        base_url = "User:JeffDoozan/lists/section_order"
        logger.save(base_url, WikiSaver, commit_message=args.save)
    else:
        dest = "section_order"
        logger.save(dest, FileSaver)


if __name__ == "__main__":
    main()
