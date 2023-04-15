#!/usr/bin/python3

import argparse
import os
import sys

from enwiktionary_wordlist.wordlist import Wordlist

from autodooz.wikilog import WikiLogger, BaseHandler
from collections import namedtuple
from ngram.ngramdb import NgramDB

class WikiSaver(BaseHandler):

    def sort_items(self, items):
        return sorted(items)

    def page_name(self, page_sections, prev):
        return f"drae_gender_mismatch"

    def page_header(self, base_path, page_name, page_sections, pages):
        count = sum(len(s) for s in page_sections)
        return [
            "Spanish Nouns that don't match any the genders of the corresponding DRAE entry, with usage counts from Google Ngram corpus 1950-2019",
            f"; {count} item{'s' if count>1 else ''}",
            ]

    def make_rows(self, entries):
        for x in entries:
            max_count = max([x.m, x.f, x.mp, x.fp])
            counts = [f"'''{c}'''" if c == max_count else c for c in [x.m, x.f, x.mp, x.fp]]
            yield f"[[{x.page}#Spanish|{x.page}]]", x.drae_genders, x.wiki_genders, *counts

    def make_section(self, base_path, page_name, section_entries, prev_section_entries, pages):
        head_rows = [["Page", "gender", "DRAE genders", "el ''word''", "la ''word''", "los ''word''", "las ''word''"]]
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
    _paramtype = namedtuple("params", ["page", "drae_genders", "wiki_genders", "m", "f", "mp", "fp"])

logger = Logger()

def log(page, drae_genders, wiki_genders, m, f, mp, fp):
    logger.add(page, drae_genders, wiki_genders, m, f, mp, fp)

def main():
    parser = argparse.ArgumentParser(description="Find verbs with split data")
    parser.add_argument("--wikt", help="Dictionary file name", required=True)
    parser.add_argument("--drae", help="Dictionary file name", required=True)
    parser.add_argument("--ngramdb", help="Ngram database", required=True)
    parser.add_argument("--save", help="Save to wiktionary with specified commit message")
    args = parser.parse_args()

    drae = Wordlist.from_file(args.drae)
    wikt = Wordlist.from_file(args.wikt)
    ngramdb = NgramDB(args.ngramdb)

    all_drae_genders = set()

    for word in wikt.iter_all_words():
        if not word.pos == "n":
            continue

        drae_words = drae.get_words(word.word, word.pos)
        if not drae_words:
            continue

        drae_genders = set()
        for w in drae_words:
            if w.genders:
                for gender in w.genders.split("; "):
                    drae_genders.add(gender)
                    all_drae_genders.add(gender)


        wikt_genders = word.genders if word.genders else ""
        for wikt_gender in wikt_genders.split("; "):
            if wikt_gender == "mfbysense":
                wikt_gender = "mf"
            if wikt_gender not in drae_genders:

                m = ngramdb.get_count(f"el {word.word}")
                f = ngramdb.get_count(f"la {word.word}")
                mp = ngramdb.get_count(f"los {word.word}")
                fp = ngramdb.get_count(f"las {word.word}")

                log(word.word, wikt_gender, "; ".join(sorted(drae_genders)), m, f, mp, fp)

    print(all_drae_genders)

    if args.save:
        base_url = f"User:JeffDoozan/lists/es"
        logger.save(base_url, WikiSaver, commit_message=args.save)
    else:
        dest = ""
        logger.save(dest, FileSaver)

if __name__ == "__main__":
    main()

