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

import enwiktionary_sectionparser as sectionparser
import os
import re
import sys
import pywikibot

from enwiktionary_wordlist.wikiextract import WikiExtractWithRev
from enwiktionary_parser import parse_page
from autodooz.wikilog import WikiLogger, BaseHandler
from collections import namedtuple
from enwiktionary_wordlist.sense import Sense
from autodooz.fix_es_forms import POS_TO_TITLE, FormFixer
from enwiktionary_wordlist.utils import wiki_to_text

from autodooz.sections import ALL_POS

class WikiSaver(BaseHandler):
    def page_name(self, items, prev):
        return f"es/forms_with_data"

    def sort_items(self, items):
        return sorted(items, key=lambda x:(x.error, x.section, x.page))

    def is_new_section(self, item, prev_item):
        # Split by error and section
        return not prev_item or prev_item.error != item.error or prev_item.section != item.section

    def page_header(self, base_path, page_name, page_sections, pages):
        return [f"Spanish forms with extra data: {sum(map(len, page_sections))} items"]

    def format_entry(self, entry, prev_entry):
        e = entry
        language = "Spanish"

        res = f"; [[{e.page}#{language}|{e.page}:{e.section}]]"
        if e.line:
            res += f": <nowiki>{e.line}</nowiki>"

        return [res]

    def get_section_header(self, base_path, page_name, section_entries, prev_section_entries, pages):
        res = []
        item = section_entries[0]
        prev_item = prev_section_entries[-1] if prev_section_entries else None
        if not prev_item or prev_item.error != item.error:
            res.append(f"==={item.error}===")
            count = sum(map(len, [x for x in pages[page_name] if x[0].error == item.error]))
            res.append(f"{count} item{'s' if count>1 else ''}<br>")

        res.append(f"===={item.section}====")
        res.append(f"{len(section_entries)} item{'s' if len(section_entries)>1 else ''}<br>")

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
    _paramtype = namedtuple("params", [ "error", "page", "section", "line" ])

logger = Logger()

def check_page(title, page_text, log):

    # All forms use the head template,
    # this is a fast way of finding the pages that don't have forms
    if "{{head|es" not in page_text:
        return

    entry = sectionparser.parse(page_text, title)
    if not entry:
        return

    for spanish in entry.ifilter_sections(matches="Spanish", recursive=False):
        for section in spanish.ifilter_sections(matches=lambda x: FormFixer.is_form(x)):
            FormFixer.is_generated(section, lambda error, line=None: log(error, title, section.title, line))

def main():

    import argparse
    argparser = argparse.ArgumentParser(description="Find forms with data beyond a simple form declaration")
    argparser.add_argument("--file", help="XML file to load", required=True)
    argparser.add_argument("--limit", type=int, help="Limit processing to first N articles")
    argparser.add_argument("--progress", help="Display progress", action='store_true')
    argparser.add_argument("--save", help="Save to wiktionary with specified commit message")
    args = argparser.parse_args()

    def log(error, page, section, line=None):
        logger.add(error, page, section, line)

    count = 0
    for page in WikiExtractWithRev.iter_articles_from_bz2(args.file):
        if ":" in page.title or "/" in page.title:
            continue

        if not count % 1000 and args.progress:
            print(count, end = '\r', file=sys.stderr)

        if args.limit and count >= args.limit:
            break
        count += 1

        check_page(page.title, page.text, log)

    if args.save:
        base_url = "User:JeffDoozan/lists"
        logger.save(base_url, WikiSaver, commit_message=args.save)
    else:
        dest = ""
        logger.save(dest, FileSaver)

if __name__ == "__main__":
    main()


class MoveSubsectionsRunner():

    def move_form_subsections(self, match, title, replacement):
        """ Move any form subsections into the previous non-form """
        page_text = match.group(0)

        body = get_lean_spanish_entry(page_text)
        entry = sectionparser.parse(body, title)
        if not entry:
           return

        summary = []
        target = None
        for section in entry.ifilter_sections(recursive=True, matches=lambda x: x.title in ALL_POS):

            if not re.search(r"^\s*{{head\|es\|(past participle|[^|]* form)", section.content_text):
                target = section
                continue

            if not target:
                continue

            if not section._children:
                continue

            if target._children:
                target._children += section._children
            else:
                target._children = section._children
            section._children = []
            moved = True

            summary.append(f"moved subsections from {section.title} to {target.title}")

        if not summary:
            return page_text

        replacement._edit_summary = f"Spanish: " + "; ".join(summary)
        return page_text.replace(body, str(entry))


class MergeDataRunner():

    def __init__(self, pairfile):
        self._site = None
        self.skip_next = False
        self.iter_count = 0
        self.load_pairfile(pairfile)

    section_to_pos = {
        "Adjective": "adj",
        "Noun": "n",
        "Verb": "v",
    }

    @property
    def site(self):
        if not self._site:
            self._site = pywikibot.Site()
        return self._site

    def load_pairfile(self, filename):
        partners = {}
        with open(filename) as infile:
            for line in infile:
                line = line.strip()
                k,v = line.split("-", 1)
                k = k.strip("# []")
                v = v.strip(" []")
                partners[k] = v

        self.lemma2form = partners
        self.form2lemma = {v:k for k,v in partners.items()}
        if not len(self.lemma2form) == len(self.form2lemma):
            raise ValueError("input file has duplicate forms or lemmas", filename)


    def merge_pairs(self, match, title, replacement):
        """ This will be called twice for each pair
        On the first call, it should add data to the target page
        On the second call, it should remove data from the source page
        """

        self.iter_count += 1
        page_text = match.group(0)

        if self.skip_next:
            self.skip_next = False
            print("skipping")
            return page_text
        self.skip_next = False

        if self.iter_count % 2:
            self._lemma = title
            lemma = title
            form = self.lemma2form[lemma]

            wiki_page = pywikibot.Page(self.site, form)
            src_text = wiki_page.text

            fixes = []
            def log(*args):
                print(args)
                fixes.append(args)

            check_page(title, src_text, log)
            if not fixes:
                print("no fixes found")
                self.skip_next = True
                return page_text

            if len(fixes) != 1:
                print("too many changes, can't merge", fixes)
                self.skip_next = True
                return page_text

            error, page, item, line = fixes[0]
            if error != "has_sense_details":
                print("error is not has_sense_details", error)
                self.skip_next = True
                return page_text

            self._section = item._parent._name
            self._pos = self.section_to_pos[self._section]
            if not self._pos:
                print("can't find pos", self._section)
                self.skip_next = True
                return page_text

            self._matched = line

            body = get_lean_spanish_entry(page_text)
            if not body:
                print(page_text)
                raise ValueError("no spanish found")
            wikt = parse_page(body, title, None)
            if not wikt:
                print("no page data", title)
                print(page_text)
                return page_text

            items = wikt.filter_words(matches = lambda x: x._parent._name == self._section)

            print("checking" ,page)

            if not items:
                print("no matches", self._section)
                self.skip_next = True
                return page_text

            if len(items) > 1:
                print("too many matches", self._section)
                self.skip_next = True
                return page_text

            orig_entry = str(wikt)
            wt_section = items[0]
            if not str(wt_section).endswith("\n"):
                wt_section.add_text("\n" + line + "\n")
            else:
                wt_section.add_text(line + "\n")

            new_page_text = page_text.replace(orig_entry, str(wikt))
            if new_page_text == page_text:
                print("no changes")
                self.skip_next = True
                return page_text

            replacement._edit_summary = f"Spanish: {self._section}: moved form data from {form} (manually assisted)"
            return new_page_text

        else:
            replacement._edit_summary = f"Spanish: {self._section}: moved form data to lemma {self._lemma} (manually assisted)"
            return page_text.replace(self._matched + "\n", "").replace(self._matched, "")
