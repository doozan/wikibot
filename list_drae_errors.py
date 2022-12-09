#!/usr/bin/python3

import argparse
import re
import sys

from autodooz.fix_es_drae import DraeFixer
from autodooz.sectionparser import SectionParser
from autodooz.wikilog import WikiLogger, BaseHandler
from collections import defaultdict, namedtuple
from enwiktionary_wordlist.all_forms import AllForms
from enwiktionary_wordlist.wikiextract import WikiExtractWithRev
from enwiktionary_wordlist.wordlist import Wordlist

class WikiSaver(BaseHandler):

    error_to_text = {
        "drae_link_custom_target": "Template uses custom target",
        "drae_link_missing": "Page is missing DRAE link",
        "drae_link_no_target": "Template links to non-existant DRAE lemma",
        "drae_link_old_template": "Page uses old template",
        "drae_link_on_form": "Template on page without lemma",
        "drae_link_wrong_target": "Template lemma doesn't match page lemma",
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
        if page_sections and "autofix" in page_sections[-1][-1].error:
            return True

        return "autofix" in section_entries[0].error

    def page_name(self, page_sections, prev):
        # autofix errors are split into their own pages
        # everything else is consolidated into "drae_link_errors"
        if "autofix" in page_sections[0][0].error:
            return page_sections[0][0].error
        return "drae_link_errors"

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

    def format_entry(self, entry, prev_entry):
        page = entry.page
        details = entry.details
        if details:
            return [f": [[{page}#Spanish|{page}]] {details}"]
        return [f": [[{page}#Spanish|{page}]]"]

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
def log(error, page, details=None):
    logger.add(error, page, details)

def is_form(wordlist, title):
    return not any(AllForms.is_lemma(word) for word in wordlist.get_words(title))

def process(text, title, wordlist, fixer):

    if "{{R:DRAE" in text:
        log("drae_link_old_template", title)

    page_is_form = is_form(wordlist, title)
    if page_is_form and "{{R:es:DRAE" not in text:
        return

    entry = SectionParser(text, title)
    spanish = entry.filter_sections(matches=lambda x: x.title == "Spanish", recursive=False)
    if not spanish:
        return
    if len(spanish) > 1:
        print("WARN: multiple spanish entries", title, file=sys.stderr)
    spanish = spanish[0]
    sections = spanish.filter_sections(matches=lambda x: x.title == "Further reading")

    if page_is_form:
        # Fix for lemmas without senses, which are not included in the wordlist and therefor not tagged as lemmas
        if re.search("{{es-(noun|verb|adj)", str(spanish)):
            return

        if any("{{R:es:DRAE" in str(section) for section in sections):
            log("drae_link_on_form", title)
        return

    if len(sections) > 1:
        print("WARN: multiple Further reading sections", title, file=sys.stderr)
        return

    # Check for missing DRAE links
    templates = list(re.finditer("{{R:es:DRAE(.*?)}}", str(sections[0]))) if sections else []
    if templates:
        fixer.fix_wrong_drae(text, title)
    else:
        fixer.fix_missing_drae(text, title)

def main():
    parser = argparse.ArgumentParser(description="Find fixable entries")
    parser.add_argument("--wordlist", help="wiktionary allforms")
    parser.add_argument("--draelinks", help="drae links data")
    parser.add_argument("--save", help="Save to wiktionary with specified commit message")
    parser.add_argument("extract", help="language extract file")
    args = parser.parse_args()

    wordlist = Wordlist.from_file(args.wordlist)
    fixer = DraeFixer(args.draelinks, logger)

    for article in WikiExtractWithRev.iter_articles_from_bz2(args.extract):
        process(article.text, article.title, wordlist, fixer)

    if args.save:
        base_url = "User:JeffDoozan/lists/es"
        logger.save(base_url, WikiSaver, commit_message=args.save)
    else:
        dest = ""
        logger.save(dest, FileSaver)

if __name__ == "__main__":
    main()
