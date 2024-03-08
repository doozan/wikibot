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

import argparse
import csv
import enwiktionary_sectionparser as sectionparser
import multiprocessing
import os
import re
import sys

from autodooz.utils import iter_xml, iter_wxt
from autodooz.wikilog import WikiLogger, BaseHandler
from collections import defaultdict, namedtuple

BLUELINKS = None
KNOWN_TAXON = None

TAXNAME_PAT = "[a-zA-Z0-9()×. -]+"
FIX_PATH = "taxons_with_redlinks"
class WikiSaver(BaseHandler):

    def sort_items(self, items):

        # sort autofix sections first so they can be split
        return sorted(items, key=lambda x: (x.error, x.page, x.details))

    def page_name(self, page_sections, prev):
        assert FIX_PATH
        return FIX_PATH

    def is_new_section(self, item, prev_item):
        return prev_item and prev_item.error != item.error

    def page_header(self, base_path, page_name, page_sections, pages):
        return [f"""All redlinks found inside L2 Translingual sections with {{tl|taxon}} on {self.args.date}"""]

    def get_section_header(self, base_path, page_name, section_entries, prev_section_entries, pages):
        res = []
        if not section_entries:
            return res

        item = section_entries[0]
        count = len(section_entries)

        if prev_section_entries:
            res.append("")
        res.append(f"==={item.error}===")
        res.append(f"; {count} item{'s' if count>1 else ''}")
        return res

    def format_entry(self, entry, prev_entry):
        return [f"; [[{entry.page}]]: {entry.details}"]

class FileSaver(WikiSaver):

    def save_page(self, dest, page_text):
        if not page_text:
            print(dest, "is empty, not saving", file=sys.stderr)
            return
        dest = dest.lstrip("/").replace("/", "_")
        with open(dest, "w") as outfile:
            outfile.write(page_text)
            print("saved", dest, file=sys.stderr)

    def save(self, *args, **nargs):
        super().save(*args, **nargs, commit_message=None)

class Logger(WikiLogger):
    _paramtype = namedtuple("params", [ "error", "page", "details" ])

logger = Logger()

def log(error, page, details):
    logger.add(error, page, details)

def process(args):

    entry_text, entry_title_section = args
    entry_title, _ = entry_title_section.split(":", 1)

    wikt = sectionparser.parse(entry_text, entry_title)
    if not wikt:
        return

    res = []

    # taxons.txt.bz2 flags Translingual sections on pages containing other L2s as "Translingual~", so use startswith()
    for section in wikt.ifilter_sections(recursive=False, matches=lambda x: x.title.startswith("Translingual")):
        section_text = str(section)
        if "taxon" not in section_text:
            continue
        for m in re.finditer(r"\[\[\s*([^|\]#]+).*?\]\]", entry_text):
            link = m.group(1).strip()
#            print([link, m.group(0)])
            if ":" in link:
                continue
            if link not in BLUELINKS:
                res.append(("translingual_l2_with_redlinks", entry_title, m.group(0)))

    return res


def main():
    parser = argparse.ArgumentParser(description="Find errors in sense lists")
    parser.add_argument("--xml", help="XML file to load")
    parser.add_argument("--wxt", help="Wiktionary extract file to load")
    parser.add_argument("--bluelinks", help="all.pages file")
    parser.add_argument("--limit", type=int, help="Limit processing to first N articles")
    parser.add_argument("--progress", help="Display progress", action='store_true')
    parser.add_argument("--date", help="Date updated", default="")
    parser.add_argument("--save", help="Save to wiktionary with specified commit message")
    parser.add_argument("-j", help="run N jobs in parallel (default = # CPUs - 1", type=int)
    args = parser.parse_args()

    if args.save and not args.date:
        print("provide --date when using --save")
        exit(1)

    if not args.j:
        args.j = multiprocessing.cpu_count()-1

    if (not args.xml and not args.wxt) or (args.xml and args.wxt):
        print("use either --xml or --wxt")
        exit(1)

    global BLUELINKS
    with open(args.bluelinks) as infile:
        print("loading bluelinks...", file=sys.stderr)
        BLUELINKS = {l.strip() for l in infile}
        print("loaded", len(BLUELINKS), "known pages", file=sys.stderr)

    if args.wxt:
        iter_entries = iter_wxt(args.wxt, args.limit, args.progress)
    else:
        iter_entries = iter_xml(args.xml, args.limit, args.progress)

    if args.j > 1:
        pool = multiprocessing.Pool(args.j)
        iter_items = pool.imap_unordered(process, iter_entries, 100)
    else:
        iter_items = map(process, iter_entries)


    for results in iter_items:
        if not results:
            continue
        for log_values in results:
            log(*log_values)

    if args.save:
        base_url = f"User:JeffDoozan/lists"
        logger.save(base_url, WikiSaver, commit_message=args.save, date=args.date)
    else:
        dest = ""
        logger.save(dest, FileSaver, date=args.date)

if __name__ == "__main__":
    main()
