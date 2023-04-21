#!/usr/bin/python3

import argparse
import multiprocessing
import os
import re
import sys

from autodooz.fix_list_to_col import ListToColFixer
from autodooz.wikilog import WikiLogger, BaseHandler
from collections import defaultdict, namedtuple
import enwiktionary_sectionparser as sectionparser

class WikiSaver(BaseHandler):

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
            return "fixes"
        else:
            return "errors"

    def format_entry(self, entry, prev_entry):
        return [f": [[{entry.page}|{entry.path}]] <nowiki>{entry.details}</nowiki>"]

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

class Logger(WikiLogger):
    _paramtype = namedtuple("params", [ "error", "page", "path", "details" ])

logger = Logger()
def log(error, page, path, details=None):
    logger.add(error, page, path, details)

def iter_wxt(datafile, options, limit=None, show_progress=False):

    if not os.path.isfile(datafile):
        raise FileNotFoundError(f"Cannot open: {datafile}")

    from enwiktionary_wordlist.wikiextract import WikiExtractWithRev
    parser = WikiExtractWithRev.iter_articles_from_bz2(datafile)

    count = 0
    for entry in parser:

        if ":" in entry.title or "/" in entry.title:
            continue

        if not count % 1000 and show_progress:
            print(count, end = '\r', file=sys.stderr)

        if limit and count >= limit:
            break
        count += 1

        yield entry.text, entry.title, None, options


delims = [("{", "}"), ("[", "]")] #, ("(", ")"), ("<", ">")]

def process_page(text, title, summary=None, options=None):

    log = []

    # Strip <nowiki> and HTML comments
    text = re.sub("<\s*nowiki\s*>.*?<\s*/\s*nowiki\s*>", "", text, flags=re.DOTALL)
    text = re.sub("<!--.*?-->", "", text, flags=re.DOTALL)

    entry = sectionparser.parse(text, title)
    if not entry:
        print("no entry", title)
        return []

    for section in entry.filter_sections():
        text = "\n".join(section._lines)
        for opener, closer in delims:
            open_count = text.count(opener)
            close_count = text.count(closer)
            if open_count != close_count:
                language = list(section.lineage)[-2]
                page = title + "#" + language
                if open_count > close_count:
                    log.append((f"extra_{opener}", page, title + ":" + section.path, f"{open_count}, {close_count}"))
                else:
                    # Navajo uses {{nv-theme-header}} plus |} to build tables
                    if closer == "}" and language == "Navajo" and (close_count - open_count == text.count("{{nv-theme-header}}") == text.count("\n|}")):
                        continue
                    log.append((f"extra_{closer}", page, title + ":" + section.path, f"{close_count}, {open_count}"))

    return log

fixer = None
def process(args):
    # Needed to unpack args until Pool.istarprocess exists
    return process_page(*args)

def main():
    global fixer
    parser = argparse.ArgumentParser(description="Find Spanish nouns with manually specified forms")
    parser.add_argument("wxt", help="Wiktionary extract file")
    parser.add_argument("--limit", type=int, help="Limit processing to first N articles")
    parser.add_argument("--progress", help="Display progress", action='store_true')
    parser.add_argument("--save", help="Save to wiktionary with specified commit message")

    parser.add_argument("-j", help="run N jobs in parallel (default = # CPUs - 1", type=int)
    args = parser.parse_args()

    fixer = ListToColFixer()

    if not args.j:
        args.j = multiprocessing.cpu_count()-1

    options = {}
    iter_entries = iter_wxt(args.wxt, options, args.limit, args.progress)

    if args.j > 1:
        pool = multiprocessing.Pool(args.j)
        iter_items = pool.imap_unordered(process, iter_entries, 10)
    else:
        iter_items = map(process, iter_entries)

    for results in iter_items:
        for log_values in results:
            log(*log_values)

    if args.save:
        base_url = f"User:JeffDoozan/lists/unbalanced_delimeters"
        logger.save(base_url, WikiSaver, commit_message=args.save)
    else:
        dest = ""
        logger.save(dest, FileSaver)

if __name__ == "__main__":
    main()
