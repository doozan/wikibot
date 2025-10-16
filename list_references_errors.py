#!/usr/bin/python3

import pywikibot
import multiprocessing
import re
import sys

from autodooz.fix_references import ReferenceFixer
from autodooz.utils import iter_wxt
from autodooz.wikilog import WikiLogger, BaseHandler
from collections import namedtuple, defaultdict

ALL_TITLES = {
    'autofix_misnamed_references': "Section contains only references tag but is not named References",
    'autofix_missing_ref_section': "L2 uses references but has no References section",
    'autofix_missing_ref_target': "Missing <nowiki><references/></nowiki> tag",
}

FIX_PATH = "references"

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


    def get_section_header(self, base_path, page_name, section_entries, prev_section_entries, pages):
        res = []
        item = section_entries[0]
        prev_item = prev_section_entries[-1] if prev_section_entries else None
        if not prev_item or prev_item.error != item.error:
            title = ALL_TITLES[item.error] if item.error in ALL_TITLES else item.error
            res.append(f"==={title}===")
            count = sum(map(len, [x for x in pages[page_name] if x[0].error == item.error]))
            res.append(f"{count} item{'s' if count>1 else ''}<br>")

        return res

    def format_entry(self, entry, prev_entry):
        page = entry.page
        section = entry.section if entry.section else ""
        if entry.error.startswith("autofix_"):
            return [f": [[{page}]]"]

        if entry.details:
            return [f": [[{page}]] {section} {entry.details}"]
        else:
            return [f": [[{page}]] {section}"]

    _paramtype = namedtuple("params", [ "error", "page", "section", "details" ])

class FileSaver(WikiSaver):

    def save_page(self, dest, page_text):
        dest = dest.lstrip("/").replace("/", "_")
        with open(dest, "w") as outfile:
            outfile.write(page_text)
            print("saved", dest)

    def save(self, *args, **nargs):
        super().save(*args, **nargs, commit_message=None)

class Logger(WikiLogger):
    _paramtype = namedtuple("params", [ "error", "page", "section", "details" ])

fixer = None
def process(args):
    # Needed to unpack args until Pool.istarprocess exists
    return fixer.process(*args)
#        fixer.process(page.text, page.title, None, {"remove_empty": True})

def main():
    global fixer

    import argparse

    parser = argparse.ArgumentParser(description="Find fixable entries")
    parser.add_argument("wxt", help="Wiktionary extract file")
    parser.add_argument("--save", help="Save to wiktionary with specified commit message")
    parser.add_argument("--limit", type=int, help="Limit processing to first N articles")
    parser.add_argument("--progress", help="Display progress", action='store_true')
    parser.add_argument("-j", help="run N jobs in parallel (default = # CPUs - 1", type=int)
    args = parser.parse_args()

    if not args.j:
        args.j = multiprocessing.cpu_count()-1

    fixer = ReferenceFixer()
    iter_entries = iter_wxt(args.wxt, args.limit, args.progress)

    iter_entries = iter_wxt(args.wxt, args.limit, args.progress)

    if args.j > 1:
        pool = multiprocessing.Pool(args.j)
        iter_items = pool.imap_unordered(process, iter_entries, 100)
    else:
        iter_items = map(process, iter_entries)

    logger = Logger()
    for res in iter_items:
        if not res:
            continue
        for error, page, section, details in res:
            logger.add(error, page, section, details)

    if args.save:
        base_url = f"User:JeffDoozan/lists"
        logger.save(base_url, WikiSaver, commit_message=args.save)
    else:
        dest = ""
        logger.save(dest, FileSaver)


if __name__ == "__main__":
    main()
