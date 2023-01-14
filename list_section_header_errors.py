#!/usr/bin/python3

import pywikibot
import re
import sys

from autodooz.fix_section_headers import SectionHeaderFixer
from autodooz.wikilog import WikiLogger, BaseHandler
from collections import namedtuple

ALL_FIXES = {
    'alt_lang': "Language title is in 'Other names' on [[WT:LOL]]",
    'bad_l2': "L3 section found as L2, moved to preceeding L2",
    'cap_change': "Section has wrong Capitalization",
    'defined_replacement': "Manually defined section title fixes",
    'fix_level': "Page has sections where section level is not parent_level+1",
    'fuzzy_match': "Section title is similar to allowed section title",
    'misnamed_quotations': "Section contains only seeCites but is not named Quotations",
    'misnamed_references': "Section contains only references tag but is not named References",
    'missing_ref_section': "L2 uses references but has no References section",
    'missing_ref_target': "Missing <nowiki><references/></nowiki> tag",
    'not_plural': "Section title is plural but should be singular",
    'pos_counter': "Section has counter",
}

ALL_ERRORS = {
    'l2_fuzzy_guess': "Language is not in [[WT:LOL]], possible guesses about correct spelling",
    'multi_alt_lang': "Language title matches multiple 'Other names' on [[WT:LOL]]",
    'empty_section': "Empty sections",
    'unfixable': "Unhandled Section titles",
}

ALL_TITLES = ALL_ERRORS | ALL_FIXES

class WikiSaver(BaseHandler):

    def sort_items(self, items):
        return sorted(items, key=lambda x: (x.error in ALL_FIXES, x.error, x.page))

    def is_new_section(self, item, prev_item):
        return prev_item and prev_item.error != item.error

    def is_new_page(self, page_sections, section_entries):
        return page_sections[0][0].error not in ALL_FIXES

    def page_name(self, page_sections, prev):
        if page_sections[0][0].error in ALL_FIXES:
            return "fixes"
        else:
            return page_sections[0][0].error

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
        return [f": [[{page}]] {section} {entry.details}"]

    # Add empty pages if they generated no errors
    def make_pages(self, *args, **nargs):
        pages = super().make_pages(*args, **nargs)
        for error in ALL_ERRORS.keys():
            if error not in pages:
                pages[error] = []
        return pages

    def page_header(self, base_path, page_name, page_sections, pages):
        if page_sections:
            return []

        # Generate something for blank pages
        title = ALL_TITLES[page_name] if page_name in ALL_TITLES else page_name
        return [f"==={title}===", "0 items"]

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

logger = Logger()
def log(error, page, section, details):
    logger.add(error, page, section, details)

def main():

    import argparse
    from pywikibot import xmlreader

    parser = argparse.ArgumentParser(description="Find fixable entries")
    parser.add_argument("xmlfile", help="Wiktionary dump")
    parser.add_argument("--save", help="Save to wiktionary with specified commit message")
    parser.add_argument("--limit", type=int, help="Limit processing to first N articles")
    parser.add_argument("--progress", help="Display progress", action='store_true')
    args = parser.parse_args()

    dump = xmlreader.XmlDump(args.xmlfile)
    parser = dump.parse()

    fixer = SectionHeaderFixer()
    fixer._log = log

    count = 0
    for page in parser:
        if ":" in page.title  or "/" in page.title or page.isredirect:
            continue

        count += 1
        if count % 1000 == 0 and args.progress:
            print(count, file=sys.stderr, end="\r")
        if args.limit and count > args.limit:
            break

        fixer.process(page.text, page.title, None, {"remove_empty": True})

    if args.save:
        base_url = "User:JeffDoozan/lists/section_headers"
        logger.save(base_url, WikiSaver, commit_message=args.save)
    else:
        dest = "section_headers"
        logger.save(dest, FileSaver)


if __name__ == "__main__":
    main()
