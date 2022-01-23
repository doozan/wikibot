#!/usr/bin/python3
#
# Copyright (c) 2021 Jeff Doozan
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
Find possible mismatches between a POS section header and the headline
"""

import os
import re
import sys
import pywikibot
from autodooz.wikilog import WikiLogger, BaseHandler
from collections import namedtuple
from enwiktionary_wordlist.wordlist import Wordlist
from autodooz.form_fixer import POS_TO_TITLE

class WikiSaver(BaseHandler):
    def page_name(self, items, prev):
        return f"es/maybe_forms"

    def page_header(self, base_path, page_name, page_sections, pages):
        return [f"Spanish lemmas that may be forms: {sum(map(len, page_sections))} items"]

    def format_entry(self, entry, prev_entry):
        page = entry.page
        section = POS_TO_TITLE[entry.pos]
        language = "Spanish"
        return [f": [[{page}#{language}|{page}:{section}]]"]

class FileSaver(WikiSaver):

    def save_page(self, dest, page_text):
        dest = dest.lstrip("/").replace("/", "_")
        with open(dest, "w") as outfile:
            outfile.write(page_text)
            print("saved", dest)

    def save(self, *args, **nargs):
        super().save(*args, **nargs, commit_message=None)

class Logger(WikiLogger):
    _paramtype = namedtuple("params", [ "page", "pos" ])

logger = Logger()

def log(word):
    logger.add(word.word, word.pos)

def check_word(word):

    if word.meta and (" form" in word.meta or "past participle" in word.meta):
        return

    # singular nouns are always lemmas # TODO: maybe restrict this to just "feminine of" forms
    if (word.pos == "n" and word.genders in ["m", "f"]):
        return

    # If any sense is not a form-of, it's a lemma
    for sense in word.senses:
        if not sense.formtype:
            return

        if "_" not in sense.formtype \
                and sense.formtype not in ["f", "fpl", "mpl", "pl", "form", "gerund", "infinitive", "reflexive"]:
            return

    log(word)

def main():

    import argparse
    argparser = argparse.ArgumentParser(description="Find lemmas with only 'form of' senses")
    argparser.add_argument("--wordlist", help="wordlist to load", required=True)
    argparser.add_argument("--limit", type=int, help="Limit processing to first N articles")
    argparser.add_argument("--progress", help="Display progress", action='store_true')
    argparser.add_argument("--save", help="Save to wiktionary with specified commit message")
    args = argparser.parse_args()

    if not os.path.isfile(args.wordlist):
        raise FileNotFoundError(f"Cannot open: {args.wordlist}")

    wordlist = Wordlist.from_file(args.wordlist)

    count = 0
    for word in wordlist.iter_all_words():

        if not count % 1000 and args.progress:
            print(count, end = '\r', file=sys.stderr)

        if args.limit and count >= args.limit:
            break
        count += 1

        check_word(word)

    if args.save:
        base_url = "User:JeffDoozan/lists"
        logger.save(base_url, WikiSaver, commit_message=args.save)
    else:
        dest = ""
        logger.save(dest, FileSaver)

if __name__ == "__main__":
    main()
