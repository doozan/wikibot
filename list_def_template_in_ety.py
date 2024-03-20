#!/usr/bin/python3
#
# Copyright (c) 2022 Jeff Doozan
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
List "definition only" templates found in Etymology sections
"""

import csv
import enwiktionary_sectionparser as sectionparser
import multiprocessing
import os
import re
import sys

from autodooz.utils import iter_wxt
from autodooz.wikilog import WikiLogger, BaseHandler
from collections import namedtuple, defaultdict

re_templates = None
REDIRECTS = None

class WikiSaver(BaseHandler):

    def sort_items(self, items):
        count = defaultdict(int)
        for item in items:
            count[item.error] += 1

        # sorted by count of section entries (smallest to largest)
        return sorted(items, key=lambda x: (count[x.error], x.error, x.page))

    def is_new_section(self, item, prev_item):
        return prev_item and prev_item.error != item.error

    def page_name(self, page_sections, prev):
        return "def_template_in_ety"

    def page_header(self, base_path, page_name, page_sections, pages):
        return [f"{sum(map(len, page_sections))} items"]

    def format_entry(self, entry, prev_entry):
        return [f": [[{entry.page}]] {entry.path}"]

    def get_section_header(self, base_path, page_name, section_entries, prev_section_entries, pages):
        res = []

        item = section_entries[0]
        count = len(section_entries)

        if prev_section_entries:
            res.append("")
        res.append(f"==={item.error}===")
        res.append(f"; {count} item{'s' if count>1 else ''}")
        return res


class FileSaver(WikiSaver):

    def save_page(self, dest, page_text):
        dest = dest.lstrip("/").replace("/", "_")
        with open(dest, "w") as outfile:
            outfile.write(page_text)
            print("saved", dest)

    def save(self, *args, **nargs):
        super().save(*args, **nargs, commit_message=None)

def main():

    import argparse
    argparser = argparse.ArgumentParser(description="Find definition only templates inside Etymology sections")
    argparser.add_argument("wxt", help="Extract file to read")
    argparser.add_argument("--redirects", help="redirects.tsv", required=True)
    argparser.add_argument("--templates", help="def_templates.tsv", required=True)
    argparser.add_argument("--save", help="Save to wiktionary with specified commit message")
    argparser.add_argument("--limit", type=int, help="Limit processing to first N articles")
    argparser.add_argument("--progress", help="Display progress", action='store_true')
    argparser.add_argument("-j", help="run N jobs in parallel (default = # CPUs - 1", type=int)
    args = argparser.parse_args()


    with open(args.templates) as infile:
        DEF_TEMPLATES = [x[0] for x in csv.reader(infile, delimiter="\t")]

    global REDIRECTS
    with open(args.redirects) as infile:
        REDIRECTS = {x[0]:x[1] for x in csv.reader(infile, delimiter="\t") if x[1] in DEF_TEMPLATES}

    ALL_TEMPLATES = [k.removeprefix("Template:") for k in list(REDIRECTS.keys()) + DEF_TEMPLATES]

    global re_templates
    re_templates = re.compile(r"{{\s*(?P<template>" + "|".join(map(re.escape, sorted(ALL_TEMPLATES))) + ")\s*[|}]")

    if not args.j:
        args.j = multiprocessing.cpu_count()-1

    iter_entries = iter_wxt(args.wxt, args.limit, args.progress, title_matches=lambda x: ":" not in x and "/" not in x, text_matches=lambda x: "===Etymology" in x)
    if args.j > 1:
        pool = multiprocessing.Pool(args.j)
        iter_items = pool.imap_unordered(process, iter_entries, 100)
    else:
        iter_items = map(process, iter_entries)

    class Logger(WikiLogger):
        _paramtype = namedtuple("params", [ "error", "page", "path", "template" ])

    logger = Logger()

    for results in iter_items:
        if not results:
            continue
        for result in results:
            error, section, template = result
            logger.add(error, section.page, section.path, template)

    if args.save:
        base_url = "User:JeffDoozan/lists"
        logger.save(base_url, WikiSaver, commit_message=args.save)
    else:
        dest = ""
        logger.save(dest, FileSaver)

def process(args):

    entry_text, entry_title = args

    wikt = sectionparser.parse(entry_text, entry_title)
    if not wikt:
        return

    results = []
    for section in wikt.ifilter_sections(matches="Etymology"):
        section_text = section.content_text
        m = re.search(re_templates, section_text)
        if not m:
            continue
        template = m.group('template')
        template = REDIRECTS.get(template, template)
        results.append((template, section, m.group("template")))

    return results

if __name__ == "__main__":
    main()
