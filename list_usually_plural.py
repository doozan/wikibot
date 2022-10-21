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
        return sorted(items, key=lambda x: (x.ratio*-1, x.lemma))

    def page_name(self, page_sections, prev):
        return f"es/usually_plural"

    def page_header(self, base_path, page_name, page_sections, pages):
        return [f"Nouns that are used more in the plural than in the singular in Google Ngram data since 1950"]

    def make_rows(self, entries):
        for x in entries:
            yield f"[[{x.lemma}]]", f"[[{x.plural}]]", x.lemma_count, x.plural_count, x.ratio

    def make_section(self, base_path, page_name, section_entries, prev_section_entries, pages):
        head_rows = [["Singular", "Plural", "Singular count", "Plural count", "Ratio"]]
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
    _paramtype = namedtuple("params", [ "lemma", "plural", "lemma_count", "plural_count", "ratio"])

logger = Logger()

def log(lemma, plural, lemma_count, plural_count):
    ratio = round(plural_count/lemma_count, 2)
    logger.add(lemma, plural, lemma_count, plural_count, ratio)

def main():
    parser = argparse.ArgumentParser(description="Find usually plural nouns")
    parser.add_argument("--dictionary", help="Dictionary file name", required=True)
    parser.add_argument("--ngprobs", help="Ngram probability data file")
    parser.add_argument("--ngcase", help="Ngram case data file")
    parser.add_argument("--save", help="Save to wiktionary with specified commit message")
    args = parser.parse_args()

    probs = NgramPosProbability(args.ngprobs, args.ngcase)
    wordlist = Wordlist.from_file(args.dictionary)

    for form, data in probs.form_probs.items():
        s_total, s_form_count = probs.get_data(form)
        s_usage = 0

        # Check all words without any detected POS
        if not s_form_count:
            s_usage = s_total
        else:
            # Only check words that are primarily nouns
            if next(iter(s_form_count.keys())) != "n":
                continue

            # And only when the noun usage is at least %60 of total usage
            s_usage = s_form_count.get("n", 0)
            if s_usage / s_total < .6:
                continue
        if not s_usage:
            continue

        words = wordlist.get_words(form, "n")
        if not words:
            continue

        plurals = [pl for word in words for pl in word.forms.get("pl", [])]
        for plural in plurals:
            if plural == form:
                continue

            pl_total, pl_form_count = probs.get_data(plural)
            if not pl_total:
                continue
            pl_usage = 0
            if not pl_form_count:
                pl_usage = pl_total
            else:
                # Only allow plurals that are primarily nouns
                if next(iter(pl_form_count.keys())) != "n":
                    continue
                pl_usage = pl_form_count.get("n", 0)

                # And only when the noun usage is at least %60 of total usage
                if pl_usage / pl_total < .6:
                    continue

            if pl_usage >= s_usage:
                log(form, plural, s_usage, pl_usage)

    if args.save:
        base_url = "User:JeffDoozan/lists"
        logger.save(base_url, WikiSaver, commit_message=args.save)
    else:
        dest = ""
        logger.save(dest, FileSaver)

if __name__ == "__main__":
    main()

