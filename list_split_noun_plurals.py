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
        return f"es/split_noun_plurals"

    def page_header(self, base_path, page_name, page_sections, pages):
        return [f"Nouns with data in the singular and plural entries"]

    def make_rows(self, entries):
        prev = None
        for x in entries:
            # Skip dupes, assumes list is sorted
            if prev and prev.singular == x.singular and prev.plural == x.plural:
                continue
            yield f"[[{x.singular}#Spanish|{x.singular}]]", f"[[{x.plural}#Spanish|{x.plural}]]"
            prev = x

    def make_section(self, base_path, page_name, section_entries, prev_section_entries, pages):
        head_rows = [["Singular", "Plural"]]
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
    _paramtype = namedtuple("params", [ "singular", "plural"])

logger = Logger()

def log(singular, plural):
    logger.add(singular, plural)

def main():
    parser = argparse.ArgumentParser(description="Find verbs with split data")
    parser.add_argument("--dictionary", help="Dictionary file name", required=True)
    parser.add_argument("--save", help="Save to wiktionary with specified commit message")
    args = parser.parse_args()

    wordlist = Wordlist.from_file(args.dictionary)

    for word in wordlist.iter_all_words():
        if not word.pos == "n":
            continue

        for k, v in word.forms.items():
            if "pl" not in k:
                continue
            for plural in v:
                if plural == word.word:
                    continue
                if wordlist.has_word(plural, "n"):
                    log(word.word, plural)

    if args.save:
        base_url = "User:JeffDoozan/lists"
        logger.save(base_url, WikiSaver, commit_message=args.save)
    else:
        dest = ""
        logger.save(dest, FileSaver)

if __name__ == "__main__":
    main()

