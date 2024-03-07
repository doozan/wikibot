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
FIX_PATH = "possible_taxons"
class WikiSaver(BaseHandler):

    def sort_items(self, items):

        print("SAVING", len(items))

        self.count = defaultdict(int)
        source_count = defaultdict(int)
        for item in items:
            self.count[(item.source, item.name)] += 1
            source_count[item.source] += 1

        print("UNIQUE", len(self.count))

        # sort autofix sections first so they can be split
        return sorted(items, key=lambda x: (source_count[x.source], x.source, self.count[(x.source, x.name)]*-1, x.name, x.page))

    def page_name(self, page_sections, prev):
        assert FIX_PATH
        return FIX_PATH

    def is_new_section(self, item, prev_item):
        return prev_item and prev_item.source != item.source

    def page_header(self, base_path, page_name, page_sections, pages):
        return [f"""All italacized or bolded text in file/images descriptions, redlinks, and italacized text that start with a capital letter that occur outside of "Latin" or "German" entries and don't match the name of a taxon referenced by an existing {{tl|taxlink}} and don't match the name of an existing page, as of {self.args.date}"""]

    def get_section_header(self, base_path, page_name, section_entries, prev_section_entries, pages):
        res = []
        if not section_entries:
            return res

        item = section_entries[0]
        count = len(section_entries)

        if prev_section_entries:
            res.append("")
        res.append(f"==={item.source}===")
        res.append(f"; {count} item{'s' if count>1 else ''}")
        res.append("<pre>")
        return res

    def get_section_footer(self, base_path, page_name, section_entries, prev_section_entries, pages, section_lines):
        if not section_lines:
            return []
        return ["</pre>"]

    def format_entry(self, entry, prev_entry):
        if prev_entry and prev_entry.name == entry.name:
            return []
        return [f"{self.count[(entry.source, entry.name)]}: {entry.name}"]

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
    _paramtype = namedtuple("params", [ "source", "page", "name" ])

logger = Logger()

def log(source, page, name):
    logger.add(source, page, name)

def process(args):

    entry_text, entry_title = args

    if ":" in entry_title or "/" in entry_title:
        return

    wikt = sectionparser.parse(entry_text, entry_title)
    if not wikt:
        return

    res = []
    for section in wikt.ifilter_sections(recursive=False, matches=lambda x: x.title not in ["Latin", "German"]):
        clean_text = re.sub("<!--.*-->", "", str(section))

        TAXNAME = "[A-Z]" + TAXNAME_PAT
        for m in re.finditer(
                r"\[\s*([Ff]ile|[Ii]mage)\s*:[^|\]]+[|][^|\]]+[|](?P<image>[^\n|\]]+)" \
                + r"|(?<!')('''''|'')(?P<ital>" + TAXNAME + r")('''''|'')(?!')" \
                + r"|\[\[\s*(?P<redlink>" + TAXNAME + r")[|\]]"
                , clean_text):
            for src in ["image", "redlink", "ital"]:
                if not m.group(src):
                    continue

                source = src
                name = m.group(src).strip()

#                if src == "ital":
#                    print(src, name, file=sys.stderr)

                if src == "image":
                    mm = re.search(r"''(" + TAXNAME + r")''", name)
                    name = mm.group(1).strip() if mm else None

            if not name:
                continue

            if re.match(r"^(A|An|I|In|The|To|Use|Used|You|On)[ ]", name):
                continue

            if name not in KNOWN_TAXONS and name not in BLUELINKS:
                res.append((source, entry_title, name))

    return res


def main():
    parser = argparse.ArgumentParser(description="Find errors in sense lists")
    parser.add_argument("--xml", help="XML file to load")
    parser.add_argument("--wxt", help="Wiktionary extract file to load")
    parser.add_argument("--bluelinks", help="all.pages file")
    parser.add_argument("--taxons", help="path to file generated by --print-taxlinks", action='append')
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

    global KNOWN_TAXONS
    KNOWN_TAXONS = set()
    for filename in args.taxons:
        with open(filename) as infile:
            KNOWN_TAXONS |= {x[0] for x in csv.reader(infile, delimiter="\t")}

    print(len(KNOWN_TAXONS), "known taxons...searching for additional signs of life", file=sys.stderr)

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
