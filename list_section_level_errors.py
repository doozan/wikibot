#!/usr/bin/python3

import pywikibot
import multiprocessing
import re
import sys

from autodooz.fix_section_levels import SectionLevelFixer
from autodooz.utils import iter_wxt
from autodooz.wikilog import WikiLogger, BaseHandler
from collections import namedtuple, defaultdict

ALL_FIXES = {
    "autofix_misplaced_anagrams": "Misplaced Anagrams section",
    "autofix_misplaced_language": "Misplaced Language section",
    "autofix_misplaced_pronunciation": "Misplaced Pronunciation section",
    "autofix_misplaced_translation": "Misplaced Translation section",
    "autofix_pos_inside_pos": "Misplaced POS sections",
    "autofix_stray_child": "Adoptable stray children",
    "autofix_unneeded_counter": "Unneeded counter",
    "autofix_unwanted_children": "Sections that should have no child sections",
    "autofix_wrong_counter": "Section counter is wrong",
}

ALL_ERRORS = {
    "child_of_childless": "Section found inside a section that shouldn't contain other sections",
    "childless_countable": "Childless countable section",
    "circular_child": "Sections with an ancestor of the same name",
    "embedded_pronunciation_has_children": "Pronunciation with child sections",
    "empty_countable": "Empty countable section",
    "missing_pos": "L2 without POS",
    "non_l2_language": "Language section is not L2",
    "pos_bad_lineage": "POS Section found outside its expected lineage",
    "countable_bad_lineage": "Countable section found outside its expected lineage",
    "translation_before_pos": "Translation before first POS section",
    "unexpected_child": "Unexpected child",
    "unexpected_mixed_section": "Unexpected section between known sections",
    "unfinished_state": "Unclosed HTML comment or template",
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

    # Override display for unexpected_mixed_section
    def make_section(self, base_path, page_name, section_entries, prev_section_entries, pages):
        if section_entries and section_entries[0].error == "unexpected_mixed_section":
            return self.custom_format(section_entries)
        else:
            return super().make_section(base_path, page_name, section_entries, prev_section_entries, pages)

    def custom_format(self, section_entries):
        item = section_entries[0]
        count = len(section_entries)
        title = ALL_TITLES[item.error] if item.error in ALL_TITLES else item.error
        res = [f"{title}, {count} item{'s' if count>1 else ''}"]

        data = defaultdict(lambda: defaultdict(list))
        for entry in section_entries:
            lang, section, parent = entry.details
            data[lang][section].append((entry.page, parent))

        for lang, sections in sorted(data.items()):
            res.append(f"==={lang}===")
            count = sum(len(v) for v in sections.values())
            res.append(f"{count} item{'s' if count>1 else ''}")
            for section, entries in sorted(sections.items(), key=lambda x: (len(x[1]), x[0])):
                for page, parent in sorted(entries, key=lambda x: x[0]):
                    res.append(f": [[{page}]] {section} found after {parent}")
        return res

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


fixer = None
def process(args):
    # Needed to unpack args until Pool.istarprocess exists
    return fixer.process(*args)

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

    fixer = SectionLevelFixer()

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
        base_url = "User:JeffDoozan/lists/section_levels"
        logger.save(base_url, WikiSaver, commit_message=args.save)
    else:
        dest = "section_levels"
        logger.save(dest, FileSaver)


if __name__ == "__main__":
    main()
