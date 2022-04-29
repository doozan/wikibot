#!/usr/bin/python3
#
# Copyright (c) 2022 Jeff Doozan
#
# This is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
List -ismo without -ista and vice versa
"""

from autodooz.wikilog import WikiLogger, BaseHandler
from collections import namedtuple
from enwiktionary_wordlist.all_forms import AllForms
from enwiktionary_wordlist.wikiextract import WikiExtract
import sys

class WikiSaver(BaseHandler):

    def sort_items(self, items):
        return sorted(items)

    def is_new_section(self, item, prev_item):
        return prev_item and prev_item.error != item.error

    def is_new_page(self, page_sections, section_entries):
        return True

    def page_name(self, page_sections, prev):
        return f"es/" + page_sections[0][0].error

    def page_header(self, base_path, page_name, page_sections, pages):
        return [f"{sum(map(len, page_sections))} items"]

    def format_entry(self, entry, prev_entry):
        page = entry.page
        language = "Spanish"
        return [f": [[{page}#{language}|{page}]]"]

class FileSaver(WikiSaver):

    def save_page(self, dest, page_text):
        dest = dest.lstrip("/").replace("/", "_")
        with open(dest, "w") as outfile:
            outfile.write(page_text)
            print("saved", dest)

    def save(self, *args, **nargs):
        super().save(*args, **nargs, commit_message=None)

class Logger(WikiLogger):
    _paramtype = namedtuple("params", [ "error", "page" ])

logger = Logger()

def log(error, page):
    logger.add(error, page)

def main():

    import argparse
    argparser = argparse.ArgumentParser(description="Find -ismo without -ista and vice versa")
    argparser.add_argument("file", help="Extract file to read")
    argparser.add_argument("--allforms", help="Allforms for checking lemmas")
    argparser.add_argument("--save", help="Save to wiktionary with specified commit message")
    argparser.add_argument("--date", help="Date of the database dump (used to generate page messages)")
    argparser.add_argument("--limit", type=int, help="Limit processing to first N articles")
    argparser.add_argument("--progress", help="Display progress", action='store_true')
    args = argparser.parse_args()

    count = 0

    allforms = AllForms.from_file(args.allforms) if args.allforms else None
    all_lemmas = set(allforms.all_lemmas)
    for article in WikiExtract.iter_articles_from_bz2(args.file):

        if not count % 1000 and args.progress:
            print(count, end = '\r', file=sys.stderr)

        if args.limit and count >= args.limit:
            break
        count += 1

        text = article.text
        path = article.title.split(":")
        page = path[0]
        pos = path[-1]

        if page.endswith("ismo"):
            error = "ismo_without_ista"
            search = page[:-4] + "ista"
        elif page.endswith("ista"):
            error = "ista_without_ismo"
            search = page[:-4] + "ismo"
        else:
            continue

        if page not in all_lemmas:
            continue

        if search in all_lemmas and search not in article.text:
            log(error, page)

    if args.save:
        base_url = "User:JeffDoozan/lists"
        logger.save(base_url, WikiSaver, commit_message=args.save)
    else:
        dest = ""
        logger.save(dest, FileSaver)

if __name__ == "__main__":
    main()
