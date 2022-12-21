#!/usr/bin/python3

import argparse
import re
import sys

from autodooz.fix_es_form_overrides import OverrideFixer
from autodooz.wikilog import WikiLogger, BaseHandler
from collections import defaultdict, namedtuple
from enwiktionary_wordlist.wordlist import Wordlist
from pywikibot import xmlreader

class WikiSaver(BaseHandler):

    error_to_text = {
        "autofix_removed_mpl": "Remove mpl override",
        "autofix_removed_fpl": "Remove fpl override",
        "autofix_removed_pl": "Remove pl override",
        "autofix_replaced_m": "Replace m=override with m=+",
        "autofix_replaced_f": "Replace f=override with f=+",
        "custom_mpl": "Custom mpl= value",
        "custom_fpl": "Custom fpl=value",
        "custom_m": "Custom m= value",
        "custom_f": "Custom f= value",
        "custom_pl": "Custom plural value",
        }

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
            return "autofix_form_overrides"
        return "form_overrides"

    def get_section_header(self, base_path, page_name, section_entries, prev_section_entries, pages):
        res = []

        item = section_entries[0]
        error = self.error_to_text.get(item.error, item.error)
        count = len(section_entries)

        if prev_section_entries:
            res.append("")
        res.append(f"==={error}===")
        res.append(f"; {count} item{'s' if count>1 else ''}")
        return res

    def make_rows(self, entries):
        for x in entries:
            yield f"[[{x.page}]]", x.current, x.default

    def make_section(self, base_path, page_name, section_entries, prev_section_entries, pages):
        headers = self.get_section_header(base_path, page_name, section_entries, prev_section_entries, pages)
        head_rows = [["Noun", "Current Value", "Default Value"]]
        rows = self.make_rows(section_entries)
        return headers + self.make_wiki_table(rows, extra_class="sortable", headers=head_rows)

    # Add empty pages if they generated no errors
    def make_pages(self, *args, **nargs):
        pages = super().make_pages(*args, **nargs)
        for page_name in ["autofix_form_overrides", "form_overrides"]:
            if page_name not in pages:
                pages[page_name] = []
        return pages


class FileSaver(WikiSaver):

    def save_page(self, dest, page_text):
        dest = dest.lstrip("/").replace("/", "_")
        with open(dest, "w") as outfile:
            outfile.write(page_text)
            print("saved", dest)

    def save(self, *args, **nargs):
        super().save(*args, **nargs, commit_message=None)

class Logger(WikiLogger):
    _paramtype = namedtuple("params", [ "error", "page", "current", "default" ])

logger = Logger()
def log(error, page, current, default, *args):
    logger.add(error, page, "; ".join(current), "; ".join(default))

def main():
    parser = argparse.ArgumentParser(description="Find Spanish nouns with manually specified forms")
    parser.add_argument("--save", help="Save to wiktionary with specified commit message")
    parser.add_argument("--dictionary", help="Dictionary file name")
    parser.add_argument("--extract", help="Extract file name")
    args = parser.parse_args()

    fixer = OverrideFixer(log)

    if args.extract:
        for article in WikiExtractWithRev.iter_articles_from_bz2(args.extract):
            fixer.process(article.text, article.title)

    elif args.dictionary:
        wordlist = Wordlist.from_file(args.dictionary)
        for word in wordlist.iter_all_words():
            if not word.pos == "n":
                continue

            if not word.meta:
                continue

            fixer._section = word.word
            fixer.cleanup_line(word.meta, word.word)
    else:
        print("must use --extract or --dictionary")
        exit(1)

    if args.save:
        base_url = f"User:JeffDoozan/lists/es"
        logger.save(base_url, WikiSaver, commit_message=args.save)
    else:
        dest = ""
        logger.save(dest, FileSaver)

if __name__ == "__main__":
    main()
