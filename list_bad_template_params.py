#!/usr/bin/python3

import argparse
import mwparserfromhell as mwparser
import multiprocessing
import os
import re
import sys
import json

from autodooz.fix_bad_template_params import ParamFixer
from autodooz.wikilog import WikiLogger, BaseHandler
from collections import defaultdict, namedtuple

FIX_PATH = "template_params"
TOTAL_TEMPLATES = 0
TOTAL_COUNT = 0
TOTAL_TEMPLATE_WITH_ERRORS = None

class WikiSaver(BaseHandler):

    def sort_items(self, items):

        # Filter bad pos params
        items = [i for i in items if i.error != "bad_pos_param"]

        print("SORTING", len(items))
        fix_count = defaultdict(int)
        count = defaultdict(int)
        for item in items:
            if "autofix" in item.error:
                fix_count[item.error] += 1
            else:
                count[item.template_name] += 1

        def sort_items(x):

            # fixes are sorted above everything, by error code
            if "autofix" in x.error:
                return 0, fix_count[x.error]*-1, x.error, x.page, x.template_name, x.key

            # errors are sorted by template name
            return 1, count[x.template_name]*-1, x.template_name, x.key, x.page

        # sort autofix sections first so they can be split into other pages
        # everything else sorted by count of section entries (smallest to largest)
        return sorted(items, key=sort_items)

    def is_new_section(self, item, prev_item):
        if prev_item and prev_item.error.startswith("autofix"):
            return prev_item and prev_item.error != item.error

        return prev_item and prev_item.template_name != item.template_name

    def is_new_page(self, page_sections, section_entries):
        res = page_sections and (page_sections[-1][-1].error.startswith("autofix") != section_entries[0].error.startswith("autofix"))
        if res:
            print("NEW PAGE")
        return page_sections and (page_sections[-1][-1].error.startswith("autofix") != section_entries[0].error.startswith("autofix"))

    def page_name(self, page_sections, prev):
        if "autofix" in page_sections[0][0].error:
            return FIX_PATH + "/fixes"
        else:
            return FIX_PATH + "/errors"

    def format_entry(self, entry, prev_entry):

        # if it's a fix, just print the pagename
        if "autofix" in entry.error:
            return [f": [[{entry.page}]] {entry.details}"]


        data = entry.bad_data.replace("<BAD>", '<span style="color:red">').replace("</BAD>", '</span>')
        data = data.replace("\n", "<br>")
        data = data.replace("|", "&vert;").replace("{", "&lbrace;").replace("[", "&lbrack;").replace("://", "<nowiki/>://")

        details = entry.details if entry.details else f"bad param '{entry.key}'"

        if "misnamed" in entry.error:
            return [f"{details} on [[{entry.page}]]"]
        else:
            return [f"{details} on [[{entry.page}]]", f": {data}"]

    def page_header(self, base_path, page_name, page_sections, pages):
        if not page_name.endswith("/errors"):
            return []

        total_items = sum(map(len, page_sections))
        res = [ f"; {total_items:,} template calls using invalid parameters",
                f"; {TOTAL_TEMPLATES_WITH_ERRORS:,} templates called with invalid parameters",
                f"; {TOTAL_TEMPLATES:,} unique templates validated",
                f"; {TOTAL_COUNT:,} total template calls checked",
                ]

        param_count = defaultdict(int)
        for section_entries in page_sections:
            for i in section_entries:
                for k in i.key.split(", "):
                    if k.isdigit():
                        continue
                    param_count[k] += 1

        summary = ", ".join(f"'{k}':{v}" for k,v in sorted(param_count.items(), key=lambda x: (x[1]*-1, x[0])) if v>1)
        #summary = summary.replace("|", "&vert;").replace("{", "&lbrace;").replace("[", "&lbrack;").replace("://", "<nowiki/>://")
        summary = "<nowiki>" + summary + "</nowiki>"
        res += ["===Unhandled param names used more than once===", summary]

        summary = ", ".join(k for k,v in sorted(param_count.items()) if v==1)
        #summary = summary.replace("|", "&vert;").replace("{", "&lbrace;").replace("[", "&lbrack;").replace("://", "<nowiki/>://")
        summary = "<nowiki>" + summary + "</nowiki>"
        res += ["===Unhandled param names used once===", summary]
        return res


    def get_section_header(self, base_path, page_name, section_entries, prev_section_entries, pages):
        res = []

        item = section_entries[0]
        count = len(section_entries)

        if page_name.endswith("/fixes"):
            res.append(f"==={item.error}===")
            res.append(f"; {count} page{'s' if count>1 else ''}")
            return res

        if prev_section_entries and len(prev_section_entries) >= 2 and len(section_entries) < 2:
            res.append("")
            res.append("===Other templates===")
            return res

        if len(section_entries) < 2:
            return res


        param_count = defaultdict(int)
        for i in section_entries:
            if not i.key:
                continue
            for k in i.key.split(", "):
                param_count[k] += 1

        if prev_section_entries:
            res.append("")
        res.append(f"===[[Template:{item.template_name}|{item.template_name}]]===")

        if not page_name.endswith("/errors"):
            res.append(f"; {count} page{'s' if count>1 else ''}")
            return res

        summary = ""

        SUMMARY_CUTOFF=20
        SUMMARY_LEN=10

        # Don't truncate some templates
        if item.template_name in ["taxlink"]:
            SUMMARY_CUTOFF = count + 1

        if count > SUMMARY_CUTOFF:
            summary = "(unhandled params: " + ", ".join(f"'{k}':{v}" for k,v in sorted(param_count.items(), key=lambda x: (x[1]*-1, x[0]))) + ")"
            del section_entries[SUMMARY_LEN:]

        res.append(f"'''{count} uses with bad parameter{'s' if count>1 else ''}''' {summary} {f'(showing first {SUMMARY_LEN})' if count>SUMMARY_CUTOFF else ''}<br>")

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
    _paramtype = namedtuple("params", [ "error", "page", "template_name", "key", "details", "bad_data" ])

logger = Logger()
bad_templates = set()
def log(code, page, template_name, key, details, bad_data=None):
    logger.add(code, page, template_name, key, details, bad_data)
    if "autofix" not in code:
        bad_templates.add(template_name)

def iter_wxt(datafile, limit=None, show_progress=False):

    if not os.path.isfile(datafile):
        raise FileNotFoundError(f"Cannot open: {datafile}")

    from enwiktionary_wordlist.wikiextract import WikiExtractWithRev
    parser = WikiExtractWithRev.iter_articles_from_bz2(datafile)

    count = 0
    for entry in parser:

        if not count % 1000 and show_progress:
            print(count, end = '\r', file=sys.stderr)

        if limit and count >= limit:
            break
        count += 1

        #if ":" in entry.title or "/" in entry.title:
        #    continue

        yield entry.text, entry.title


fixer = None
def process(args):
    # Needed to unpack args until Pool.istarprocess exists
    return fixer.process(*args)

def main():
    global fixer, TOTAL_TEMPLATES, TOTAL_COUNT, TOTAL_TEMPLATES_WITH_ERRORS
    parser = argparse.ArgumentParser(description="Find errors in sense lists")
    parser.add_argument("wxt", help="Wiktionary extract file")
    parser.add_argument("--json", help="JSON file with template data", required=True)
    parser.add_argument("--limit", type=int, help="Limit processing to first N articles")
    parser.add_argument("--progress", help="Display progress", action='store_true')
    parser.add_argument("--save", help="Save to wiktionary with specified commit message")
    parser.add_argument("-j", help="run N jobs in parallel (default = # CPUs - 1", type=int)
    args = parser.parse_args()

    if not args.j:
        args.j = multiprocessing.cpu_count()-1

    fixer = ParamFixer(args.json)
    TOTAL_TEMPLATES = len(fixer._templates)

    iter_entries = iter_wxt(args.wxt, args.limit, args.progress)

    if args.j > 1:
        pool = multiprocessing.Pool(args.j)
        iter_items = pool.imap_unordered(process, iter_entries, 100)
    else:
        iter_items = map(process, iter_entries)

    templates_with_errors = set()
    for count, results in iter_items:

        TOTAL_COUNT += count
        for log_values in results:
            code, page, template_name, *_ = log_values
            templates_with_errors.add(template_name)

            log(*log_values)

    TOTAL_TEMPLATES_WITH_ERRORS = len(templates_with_errors)

    templates_with_errors = defaultdict(int)
    for i in logger._items:
        if "autofix" not in i.error:
            templates_with_errors[i.template_name] += 1

    with open("templates_with_bad_params.tsv", "w") as outfile:
        for template, count in sorted(templates_with_errors.items(), key=lambda x: (x[1]*-1, x[0])):
            print(f"{template}\t{count}", file=outfile)

    if args.save:
        base_url = f"User:JeffDoozan/lists"
        logger.save(base_url, WikiSaver, commit_message=args.save)
    else:
        dest = ""
        logger.save(dest, FileSaver)

if __name__ == "__main__":
    main()
