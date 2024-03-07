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

FIX_PATH = "local_taxons"
class WikiSaver(BaseHandler):

    def sort_items(self, items):
        count = defaultdict(int)
        for item in items:
            count[item.error] += 1

        # sort autofix sections first so they can be split
        return sorted(items, key=lambda x: ("autofix" not in x.error, count[x.error], x.page))

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
            return [f"; [[{entry.page}]]: {entry.details}"]

        return [f": [[{entry.page}]]\n{entry.details}"]

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

def process(args):

    entry_text, entry_title = args

    # Taxon export is filename:section[~] where ~ indicates that it is NOT the only L2 section on the page
    entry_title, _, entry_section = entry_title.partition(":")
    no_auto = entry_section.endswith("~")

    if "taxon" not in entry_text:
        return

    wikt = sectionparser.parse(entry_text, entry_title)
    if not wikt:
        return

    taxlinks = []
    log = []
    for section in wikt.ifilter_sections(recursive=False):
        section_str = str(section)
        if "taxon" not in section_str:
            continue

        if not section.path in ["English", "Translingual"]:
            log.append(("unexpected_taxon", entry_title, ""))
            continue

        wiki = mwparser.parse(section_str)
        # allow recursive, some templates don't match even though they're not actually inside other templates
        taxons = wiki.filter_templates(matches=lambda x: x.name.strip() == "taxon")
        if not taxons:
#            for t in wiki.ifilter_templates(recursive=False):
#                print(t, t.name.strip(), t.name.strip() == "taxon")

            log.append(("no_taxon", entry_title, ""))
            continue

        if len(taxons) > 1:
            desc = "<pre>" + "\n".join(map(str, taxons)) + "</pre>"
            log.append(("multi_taxon", entry_title, desc))
            continue

        for taxon in taxons:
            text = entry_title
            label = taxon.get(1).strip()
            has_i = taxon.has("i") and taxon.get("i").strip not in ["", "0"]

            taxlinks.append((entry_title, label, has_i, no_auto))

#            template_data = ["taxfmt", entry_title, label]
#            if has_i:
#                template_data.append("i=1")

#            template = "{{" + "|".join(template_data) + "}}"
#            if no_auto:
#                log.append(("unsafe_taxlink", entry_title, "<pre>" + template + "</pre>"))
#            else:
#                log.append(("autofix_taxlink", entry_title, "<pre>" + template + "</pre>"))

    return taxlinks, log



def log_results(results):
    for log_values in results:
        log(*log_values)

def print_entries(results):
    prev_path = None
    for entry_title, section_path, data in results:
        path = f"{entry_title}:{section_path}"
        if path != prev_path:
            print(f"_____{path}_____")
            prev_path = path
        print(data)

all_taxlinks = []
def store_taxlinks(args):

    seen = set()
    dups = {}
    bad = {}

    taxlinks, logitems = args
    log_results(logitems)

    global all_taxlinks
    all_taxlinks += [t for t in taxlinks if t[0] not in dups and t[0] not in bad]

def print_taxlinks():
    unique_taxlinks = {(name, rank, has_i, no_auto) for name, rank, has_i, no_auto in all_taxlinks}
    for name, rank, has_i, no_auto in sorted(unique_taxlinks):
        assert "\n" not in name and "\t" not in name

        has_i = "1" if has_i else ""
        no_auto = "1" if no_auto else ""

        values = [name, rank, has_i, no_auto]
        print("\t".join(values))

def main():
    global fixer
    parser = argparse.ArgumentParser(description="Find errors in sense lists")
    parser.add_argument("--xml", help="XML file to load")
    parser.add_argument("--wxt", help="Wiktionary extract file to load")
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

    if args.j > 1:
        pool = multiprocessing.Pool(args.j)
        iter_items = pool.imap_unordered(process, iter_entries, 100)
    else:
        iter_items = map(process, iter_entries)

    for res in iter_items:
        if not res:
            continue
        store_taxlinks(res)

    print_taxlinks()

    if args.save:
        base_url = f"User:JeffDoozan/lists"
        logger.save(base_url, WikiSaver, commit_message=args.save)
    else:
        dest = ""
        logger.save(dest, FileSaver)

if __name__ == "__main__":
    main()
