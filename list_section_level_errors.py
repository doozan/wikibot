#!/usr/bin/python3

import pywikibot
import re
import sys

from autodooz.sectionparser import SectionParser
from autodooz.fix_section_levels import SectionLevelFixer
from autodooz.wikilog import WikiLogger, BaseHandler
from collections import namedtuple

class WikiSaver(BaseHandler):

    def sort_items(self, items):
        return sorted(items, key=lambda x: (x.error, x.page))

    def is_new_section(self, item, prev_item):
        return prev_item and prev_item.error != item.error

    def is_new_page(self, page_sections, section_entries):
        return True

    def page_name(self, page_sections, prev):
        return page_sections[0][0].error

    def page_header(self, base_path, page_name, page_sections, pages):
        return [f"{sum(map(len, page_sections))} items"]

    def format_entry(self, entry, prev_entry):
        page = entry.page
        section = entry.section if entry.section else ""
        return [f": [[{page}]] {section} {entry.details}"]

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
    if error == "autofix_stray_child":
        return

    #print(error, page, section, details)
    logger.add(error, page, section, details)

def main():

    import argparse
    from pywikibot import xmlreader

    parser = argparse.ArgumentParser(description="Find fixable entries")
    parser.add_argument("xmlfile", help="Wiktionary dump")
    parser.add_argument("--save", help="Save to wiktionary with specified commit message")
    parser.add_argument("--limit", type=int, help="Limit processing to first N articles")
    parser.add_argument("--progress", help="Display progress", action='store_true')
    args = parser.parse_args()

    dump = xmlreader.XmlDump(args.xmlfile)
    parser = dump.parse()

    fixer = SectionLevelFixer()
    fixer.log = log

    count = 0
    for page in parser:
        if ":" in page.title  or "/" in page.title or page.isredirect:
            continue

        count += 1
        if count % 1000 == 0 and args.progress:
            print(count, file=sys.stderr, end="\r")
        if args.limit and count > args.limit:
            break

        fixer.process(page.text, page.title)

    if args.save:
        base_url = "User:JeffDoozan/lists/section_levels"
        logger.save(base_url, WikiSaver, commit_message=args.save)
    else:
        dest = "section_levels"
        logger.save(dest, FileSaver)


if __name__ == "__main__":
    main()
