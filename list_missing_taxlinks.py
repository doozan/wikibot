#!/usr/bin/python3

import argparse
import enwiktionary_sectionparser as sectionparser
import mwparserfromhell as mwparser
import multiprocessing
import os
import re
import sys
import json
import csv

from autodooz.fix_missing_taxlinks import MissingTaxlinkFixer
from autodooz.wikilog import WikiLogger, BaseHandler
from collections import defaultdict, namedtuple
from autodooz.utils import iter_xml, iter_wxt

FIX_PATH = "missing_taxlink"
class WikiSaver(BaseHandler):

    def sort_items(self, items):
        self.count = defaultdict(int)
        self.page_count = defaultdict(int)
        for item in items:
            self.count[item.error] += 1
            self.page_count[(item.error, item.page)] += 1

        # sort autofix sections first so they can be split
        return sorted(items, key=lambda x: ("autofix" not in x.error, self.count[x.error], self.page_count[(x.error, x.page)]*-1 if "autofix" in x.error else 0, x.page))

    def is_new_section(self, item, prev_item):
        return prev_item and prev_item.error != item.error

    def is_new_page(self, page_sections, section_entries):
        return page_sections and (page_sections[-1][-1].error.startswith("autofix") != section_entries[0].error.startswith("autofix"))

    def page_name(self, page_sections, prev):
        assert FIX_PATH

        if not page_sections or not page_sections[0]:
            return FIX_PATH + "/errors"

        if "autofix" in page_sections[0][0].error:
            return FIX_PATH + "/fixes"
        else:
            return FIX_PATH + "/errors"

    def format_entry(self, entry, prev_entry):

        if "autofix" in entry.error:
            if prev_entry and entry.page == prev_entry.page:
                return []
            count = self.page_count[(entry.error, entry.page)]
            return [f": [[{entry.page}]] - {count} fix{'es' if count > 1 else ''}"]

        if entry.page is None:
            return [f": {entry.details}"]

        if len(entry.details) > 100:
            details = re.search(r".*\<BAD\>.*?\</BAD\>.*", entry.details).group(0)
        else:
            details = entry.details
        details = "<nowiki>" \
                + details.replace("<BAD>", '</nowiki><span style="color:red"><nowiki>') \
                .replace("</BAD>", '</nowiki></span><nowiki>') \
                .replace("<GOOD>", '</nowiki><span style="color:green"><nowiki>')\
                .replace("</GOOD>", '</nowiki></span><nowiki>') \
                + "</nowiki>"
        return [f"; [[{entry.page}]]:", details]

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
def log(code, page, details):
    logger.add(code, page, details)

fixer = None
def process(args):
    # Needed to unpack args until Pool.istarprocess exists
    return fixer.process(*args)

def main():
    global fixer
    parser = argparse.ArgumentParser(description="Find errors in sense lists")
    parser.add_argument("--xml", help="XML file to load")
    parser.add_argument("--wxt", help="Wiktionary extract file to load")
    parser.add_argument("--local", help="taxons on Wiktionary", action='append', required=True)
    parser.add_argument("--external", help="taxons not on Wiktionary", action='append', required=True)
    parser.add_argument("--limit", type=int, help="Limit processing to first N articles")
    parser.add_argument("--progress", help="Display progress", action='store_true')
    parser.add_argument("--save", help="Save to wiktionary with specified commit message")
    parser.add_argument("-j", help="run N jobs in parallel (default = # CPUs - 1", type=int)
    args = parser.parse_args()

    if not args.j:
        args.j = multiprocessing.cpu_count()-1

    if (not args.xml and not args.wxt) or (args.xml and args.wxt):
        print("use either --xml or --wxt")
        exit(1)

    if args.wxt:
        iter_entries = iter_wxt(args.wxt, args.limit, args.progress)
    else:
        iter_entries = iter_xml(args.xml, args.limit, args.progress)

    debug=False
    #debug=True
    if debug:
        test_iter_entries = [("""
{{also|acarina}}
==Translingual==
[[File:Acari sp. (40153549962).jpg|thumb|[[Acari]] (syn. '''Acarina''') sp.]]

====Synonyms====
* [[Acari]]

""", "test")]
        iter_entries = test_iter_entries

    # Add the local files as negative matches for external links (to avoid creating taxlinks for things that should be taxfmt)
    args.external += [f"!{file}" for file in args.local]
    fixer = MissingTaxlinkFixer(templates={"taxlink": args.external, "taxfmt": args.local})
    if args.j > 1:
        pool = multiprocessing.Pool(args.j)
        iter_items = pool.imap_unordered(process, iter_entries, 100)
    else:
        iter_items = map(process, iter_entries)

    for res in iter_items:
        if not res:
            continue
        for log_values in res:
            log(*log_values)

    if args.save and debug:
        raise ValueError("trying to save while in debug mode")

    if args.save:
        base_url = f"User:JeffDoozan/lists"
        logger.save(base_url, WikiSaver, commit_message=args.save)
    else:
        dest = ""
        logger.save(dest, FileSaver)

if __name__ == "__main__":
    main()
