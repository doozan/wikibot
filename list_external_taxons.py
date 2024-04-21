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

TAXNAME_PAT = "[a-zA-Z0-9()×. -]+"
FIX_PATH = "external_taxons"
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
        return [f": {entry.details}"]

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

    entry_text, entry_title_section = args

    entry_title, _, entry_section = entry_title_section.partition(":")
    wiki = mwparser.parse(entry_text)

    taxlinks = []
    for t in wiki.ifilter_templates(recursive=True, matches=lambda x: str(x.name).strip() == "taxlink"):
        if not (t.has(1) and t.has(2)):
            print("missing params", entry_title_section, t, file=sys.stderr)
            continue
        taxon = str(t.get(1).value).strip()
        rank = str(t.get(2).value).strip()
        if not taxon or not rank:
            continue
        if t.has("nomul") and str(t.get("nomul").value) not in ["", "0"]:
            continue
        has_i = t.has("i") and str(t.get("i").value) not in ["", "0"]
        no_auto = " " not in taxon
        wplink = str(t.get("wplink").value) if t.has("wplink") else ""
        wslink = str(t.get("wslink").value) if t.has("wslink") else ""

        taxlink = (taxon, rank, has_i, wplink, wslink, no_auto, entry_title)
        taxlinks.append(taxlink)

    return taxlinks, []

all_taxlinks = []
def store_taxlinks(args):

    seen = set()
    dups = {}
    bad = defaultdict(list)

    taxlinks, logitems = args
    log_results(logitems)

    def make_template(name, rank, has_i, wplink, wslink):
        template = "{{tl|taxlink|" + name + "|" + rank
        if has_i:
            template += "|i=1"
        if wplink:
            template += f"|wplink={wplink}"
        if wslink:
            template += f"|wslink={wslink}"
        template += "}}"
        return template

    unique_taxlinks = {(name, rank, has_i, wplink, wslink) for name, rank, has_i, wplink, wslink, no_auto, page in taxlinks}

    for name, rank, has_i, wplink, wslink in unique_taxlinks:
        if name in seen:
            dups[name] = []
        else:
            seen.add(name)

    for name, rank, has_i, wplink, wslink, no_auto, page in taxlinks:
        stripped = re.sub(TAXNAME_PAT, "", name)
        if stripped:
            bad[make_template(name, rank, has_i, wplink, wslink)].append(page)

        if name in dups:
            dups[name].append((rank, has_i, wplink, wslink, page))

    for name, data in dups.items():
        templates = []
        pages = []
        for rank, has_i, wplink, wslink, page in data:
            if page not in pages:
                pages.append(page)
            template = make_template(name, rank, has_i, wplink, wslink)
            if template not in templates:
                templates.append(template)

        log("taxlink_conflicts", None, "; ".join(templates) + " on [[" + "]]; [[".join(pages) + "]]" )

    for template, pages in bad.items():
        log("bad_name", None, template + " on [[" + "]]; [[".join(pages) + "]]")

    global all_taxlinks
    all_taxlinks += [t for t in taxlinks if t[0] not in dups and t[0] not in bad]

def print_taxlinks():
    unique_taxlinks = {(name, rank, has_i, wplink, wslink, no_auto) for name, rank, has_i, wplink, wslink, no_auto, page in all_taxlinks}
    for name, rank, has_i, wplink, wslink, no_auto in sorted(unique_taxlinks):
        assert "\n" not in name and "\t" not in name

        has_i = "1" if has_i else ""
        no_auto = "1" if no_auto else ""

        values = [name, rank, has_i, no_auto, wplink, wslink]
        print("\t".join(values))


def log_results(results):
    for log_values in results:
        log(*log_values)


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
