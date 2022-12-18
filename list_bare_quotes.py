#!/usr/bin/python3

import argparse
import re
import sys

from autodooz.fix_bare_quotes import QuoteFixer
from autodooz.wikilog import WikiLogger, BaseHandler
from collections import defaultdict, namedtuple
from enwiktionary_wordlist.wordlist import Wordlist
from pywikibot import xmlreader

class WikiSaver(BaseHandler):

    def sort_items(self, items):
        count = defaultdict(int)
        for item in items:
            count[item.error] += 1

        # sort autofix sections first so they can be split into other pages
        # everything else sorted by count of section entries (smallest to largest)
        return sorted(items, key=lambda x: ("autofix" in x.error, count[x.error], x.error, x.page))

    def is_new_section(self, item, prev_item):
        return prev_item and prev_item.error != item.error

    def is_new_page(self, page_sections, section_entries):
        return page_sections and (page_sections[-1][-1].error.startswith("autofix") != section_entries[0].error.startswith("autofix"))

    def page_name(self, page_sections, prev):
        if "autofix" in page_sections[0][0].error:
            return "fixes"
        else:
            return "errors"

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
    _paramtype = namedtuple("params", [ "error", "page", "details" ])

logger = Logger()
def log(error, section, details=None):
    page = list(section.lineage)[-1]
    logger.add(error, page, details)

def main():
    parser = argparse.ArgumentParser(description="Find Spanish nouns with manually specified forms")
    parser.add_argument("xml", help="XML file to load")
    parser.add_argument("--limit", type=int, help="Limit processing to first N articles")
    parser.add_argument("--progress", help="Display progress", action='store_true')
    parser.add_argument("--save", help="Save to wiktionary with specified commit message")
    args = parser.parse_args()

    fixer = QuoteFixer(log)

    dump = xmlreader.XmlDump(args.xml)
    parser = dump.parse()
    count = 0
    for page in parser:
        if ":" in page.title or "/" in page.title:
            continue

        if not count % 1000 and args.progress:
            print(count, end = '\r', file=sys.stderr)

        if args.limit and count >= args.limit:
            break
        count += 1

        fixer.process(page.text, page.title)

    if args.save:
        base_url = f"User:JeffDoozan/lists/bare_quotes"
        logger.save(base_url, WikiSaver, commit_message=args.save)
    else:
        dest = ""
        logger.save(dest, FileSaver)

if __name__ == "__main__":
    main()
