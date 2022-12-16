#!/usr/bin/python3

import argparse
import os
import sys

from enwiktionary_wordlist.wordlist import Wordlist

from autodooz.wikilog import WikiLogger, BaseHandler
from collections import namedtuple

class WikiSaver(BaseHandler):

    def sort_items(self, items):
        return sorted(items)

    def page_name(self, page_sections, prev):
        return f"drae_gender_mismatch"

    def page_header(self, base_path, page_name, page_sections, pages):
        return [f"Nouns that don't match the DRAE gender"]

    def make_rows(self, entries):
        for x in entries:
            yield f"[[{x.page}]]", x.drae_genders, x.wiki_genders

    def make_section(self, base_path, page_name, section_entries, prev_section_entries, pages):
        head_rows = [["Page", "DRAE gender", "genders"]]
        rows = self.make_rows(section_entries)
        return self.make_wiki_table(rows, extra_class="sortable", headers=head_rows)

class FileSaver(WikiSaver):

    def save_page(self, dest, page_text):
        dest = dest.lstrip("/").replace("/", "_")
        with open(dest, "w") as outfile:
            outfile.write(page_text)
            print("saved", dest)

    def save(self, *args, **nargs):
        super().save(*args, **nargs, commit_message=None)

class Logger(WikiLogger):
    _paramtype = namedtuple("params", ["page", "drae_genders", "wiki_genders"])

logger = Logger()

def log(page, drae_genders, wiki_genders):
    logger.add(page, drae_genders, wiki_genders)

def main():
    parser = argparse.ArgumentParser(description="Find verbs with split data")
    parser.add_argument("--wikt", help="Dictionary file name", required=True)
    parser.add_argument("--drae", help="Dictionary file name", required=True)
    parser.add_argument("--save", help="Save to wiktionary with specified commit message")
    args = parser.parse_args()

    drae = Wordlist.from_file(args.drae)
    wikt = Wordlist.from_file(args.wikt)

    for word in drae.iter_all_words():
        if not word.pos == "n":
            continue

        wiki_words = wikt.get_words(word.word, word.pos)
        if not wiki_words:
            continue

        if any(w.genders == word.genders for w in wiki_words):
            continue

        wiki_genders = set()
        for w in wiki_words:
            if w.genders:
                wiki_genders.add(w.genders)

        log(word.word, word.genders, "; ".join(sorted(wiki_genders)))

    if args.save:
        base_url = f"User:JeffDoozan/lists/es"
        logger.save(base_url, WikiSaver, commit_message=args.save)
    else:
        dest = ""
        logger.save(dest, FileSaver)

if __name__ == "__main__":
    main()

