#!/usr/bin/python3

import argparse
import enwiktionary_sectionparser as sectionparser
import mwparserfromhell as mwparser
import multiprocessing
import sys

from autodooz.utils import iter_wxt
from autodooz.wikilog import WikiLogger, BaseHandler
from collections import defaultdict, namedtuple

MIN_COUNT = 10

class WikiSaver(BaseHandler):

    def sort_items(self, items):
        return sorted(items, key=lambda x: (x.count*-1, x.page))

    def page_name(self, page_sections, prev):
        return "missing_audio"

    def format_entry(self, entry, prev_entry):
        return [f": [[{entry.page}]]: {entry.count}"]

    def get_section_header(self, base_path, page_name, section_entries, prev_section_entries, pages):
        res = []

        item = section_entries[0]
        count = len(section_entries)

        if prev_section_entries:
            res.append("")
        res.append(f"English terms missing audio, sorted by number of derived terms")
        res.append(f"; {count} item{'s' if count>1 else ''} with at least {MIN_COUNT} derived terms")
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
    _paramtype = namedtuple("params", [ "page", "count" ])

logger = Logger()
def log(page, count):
    logger.add(page, count)


def has_audio(text):
    return "{{audio|en" in text

def count_derived_terms(text, title):
    wikt = sectionparser.parse(text, title)
    if not wikt:
        print("UNPARSABLE", title)
        return

    count = 0
    for section in wikt.ifilter_sections(matches="Derived terms"):
        section_str = str(section)
        if "{{col" not in section_str and "{{der" not in section_str:
            continue

        wiki = mwparser.parse(section_str)
        for template in wiki.filter_templates(recursive=False, matches = lambda x: x.name.startswith("col") or x.name.startswith("der")):
            param_count = len(list(p for p in template.params if str(p.name).isnumeric() and str(p.value).strip()))
            #print(template)
            #print(param_count, len(template.params), template.params)
            count += len(template.params)-1

        for template in wiki.filter_templates(recursive=False, matches = lambda x: x.name in ["l", "m"]):
            count += 1

    return count


fixer = None
def process(args):

    text, title = args

    if has_audio(text):
        return

    return (title, count_derived_terms(text, title))

def main():
    global fixer
    parser = argparse.ArgumentParser(description="English entries without audio")
    parser.add_argument("wxt", help="Wiktionary extract file")
    parser.add_argument("--limit", type=int, help="Limit processing to first N articles")
    parser.add_argument("--progress", help="Display progress", action='store_true')
    parser.add_argument("--save", help="Save to wiktionary with specified commit message")
    parser.add_argument("-j", help="run N jobs in parallel (default = # CPUs - 1", type=int)
    args = parser.parse_args()

    if not args.j:
        args.j = multiprocessing.cpu_count()-1

    iter_entries = iter_wxt(args.wxt, args.limit, args.progress)

    if args.j > 1:
        pool = multiprocessing.Pool(args.j)
        iter_items = pool.imap_unordered(process, iter_entries, 1000)
    else:
        iter_items = map(process, iter_entries)

    for res in iter_items:
        if not res:
            continue
        title, count = res
        if count is None or count < MIN_COUNT:
            continue
        log(title, count)

    if args.save:
        base_url = f"User:JeffDoozan/lists"
        logger.save(base_url, WikiSaver, commit_message=args.save)
    else:
        dest = ""
        logger.save(dest, FileSaver)

if __name__ == "__main__":
    main()
