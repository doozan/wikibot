#!/usr/bin/python3

import argparse
import os
import sys

from spanish_tools.freq import NgramPosProbability
from enwiktionary_wordlist.wordlist import Wordlist

from autodooz.wikilog import WikiLogger, BaseHandler
from collections import namedtuple

class WikiSaver(BaseHandler):

    def sort_items(self, items):
        return sorted(items)

    def page_name(self, page_sections, prev):
        return f"split_verbs"

    def page_header(self, base_path, page_name, page_sections, pages):
        return [f"Verbs with data in both -r and -rse entries"]

    def make_rows(self, entries):
        for x in entries:
            yield f"[[{x.verb1}]]", f"[[{x.verb2}]]"

    def make_section(self, base_path, page_name, section_entries, prev_section_entries, pages):
        head_rows = [["Verb", "Verb+se"]]
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
    _paramtype = namedtuple("params", ["verb1", "verb2"])

logger = Logger()

def log(verb1, verb2):
    logger.add(verb1, verb2)

def main():
    parser = argparse.ArgumentParser(description="Find verbs with split data")
    parser.add_argument("--dictionary", help="Dictionary file name", required=True)
    parser.add_argument("--save", help="Save to wiktionary with specified commit message")
    parser.add_argument("--lang", help="Select language")
    args = parser.parse_args()

    ending = {"es": "se", "pt": "-se"}[args.lang]

    wordlist = Wordlist.from_file(args.dictionary)

    for word in wordlist.iter_all_words():
        if not word.pos == "v" or " " in word.word or not word.word.endswith("r"):
            continue

        if wordlist.has_word(word.word + ending, "v"):
            log(word.word, word.word+ending)

    if args.save:
        base_url = f"User:JeffDoozan/lists/{args.lang}"
        logger.save(base_url, WikiSaver, commit_message=args.save)
    else:
        dest = ""
        logger.save(dest, FileSaver)

if __name__ == "__main__":
    main()

