#!/usr/bin/python3

import argparse
import csv
import mwparserfromhell as mwparser
import multiprocessing
import os
import re
import sys
import json

from autodooz.fix_bad_template_params import ParamFixer
from autodooz.utils import iter_wxt, iter_xml
from autodooz.wikilog import WikiLogger, BaseHandler
from collections import defaultdict, namedtuple

FIX_PATH = "template_params"
TOTAL_TEMPLATES = 0
TOTAL_COUNT = 0
TOTAL_TEMPLATE_WITH_ERRORS = None

class WikiSaverBadParams(BaseHandler):

    def sort_items(self, items):

        # Filter bad pos params
        items = [i for i in items if i.error == "bad_param"]

        print("SORTING", len(items))
        fix_count = defaultdict(int)
        count = defaultdict(int)
        for item in items:
            count[item.template_name] += 1

        # sort autofix sections first so they can be split into other pages
        # everything else sorted by count of section entries (smallest to largest)
        return sorted(items, key=lambda x: (count[x.template_name]*-1, x.template_name, x.key, x.page))

    def is_new_section(self, item, prev_item):
        return prev_item and prev_item.template_name != item.template_name

    def is_new_page(self, page_sections, section_entries):
        return False

    def page_name(self, page_sections, prev):
        return FIX_PATH + "/errors"

    def format_entry(self, entry, prev_entry):

        data = entry.bad_data.replace("<BAD>", '<span style="color:red">').replace("</BAD>", '</span>')
        data = data.replace("\n", "<br>")
        data = data.replace("|", "&vert;").replace("{", "&lbrace;").replace("[", "&lbrack;").replace("://", "<nowiki/>://")

        details = f"bad param '{entry.key}'"

        if any(entry.page.startswith(prefix) for prefix in ["Template:"]):
            return [f"{details} on [[{entry.page}]]"]

        return [f"{details} on [[{entry.page}]]", f": {data}"]

    def page_header(self, base_path, page_name, page_sections, pages):

        total_items = sum(map(len, page_sections))
        res = [ f"; {total_items:,} template calls using invalid parameters",
                f"; {TOTAL_TEMPLATES_WITH_ERRORS:,} templates called with invalid parameters",
                f"; {TOTAL_TEMPLATES:,} unique templates validated",
                f"; {TOTAL_COUNT:,} total template calls checked",
                ]

        param_count = defaultdict(int)
        for section_entries in page_sections:
            for i in section_entries:
                if i.error != "bad_param":
                    continue
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

        if prev_section_entries and len(prev_section_entries) >= 2 and len(section_entries) < 2:
            res.append("")
            res.append("===Other templates===")
            return res

        if len(section_entries) < 2:
            return res


        SUMMARY_CUTOFF=30
        SUMMARY_LEN=10

        # Don't truncate some templates
        expanded_langs = [ "el" ]
        if any(item.template_name.startswith(f"{lang}-") or f":{lang}:" in item.template_name for lang in expanded_langs):
            SUMMARY_CUTOFF =  100

        excess_entries = []
        param_count = defaultdict(int)
        for i, entry in enumerate(section_entries):
            if not entry.key:
                continue
            params = entry.key.split(", ")
            for p in params:
                param_count[p] += 1

            if all(param_count[p] > SUMMARY_LEN for p in params):
                excess_entries.append(i)

        if prev_section_entries:
            res.append("")
        res.append(f"===[[Template:{item.template_name}|{item.template_name}]]===")

        summary = ""

        if count > SUMMARY_CUTOFF:
            summary = "(unhandled params: " + ", ".join(f"'{k}':{v}" for k,v in sorted(param_count.items(), key=lambda x: (x[1]*-1, x[0]))) + ")"
            for i in reversed(excess_entries):
                del section_entries[i]

        res.append(f"'''{count} uses with bad parameter{'s' if count>1 else ''}''' {summary} {f'(showing first {SUMMARY_LEN} of each bad param)' if count>SUMMARY_CUTOFF else ''}<br>")

        return res


class WikiSaver(BaseHandler):

    def sort_items(self, items):

        # Filter bad pos params
        items = [i for i in items if i.error != "bad_param" and i.error != "bad_pos_param"]

        print("SORTING", len(items))
        fix_count = defaultdict(int)
        count = defaultdict(int)
        for item in items:
            count[item.error] += 1

        # sort autofix sections first so they can be split into other pages
        # everything else sorted by count of section entries (smallest to largest)
        return sorted(items, key=lambda x: ("autofix" not in x.error, count[x.error], x.error, x.page))

    def is_new_section(self, item, prev_item):
        return prev_item and prev_item.error != item.error

    def is_new_page(self, page_sections, section_entries):
        return page_sections and (page_sections[-1][-1].error.startswith("autofix") != section_entries[0].error.startswith("autofix"))

    def page_name(self, page_sections, prev):
        assert FIX_PATH

        if not page_sections or not page_sections[0]:
            return FIX_PATH + "/noerrors"

        if "autofix" in page_sections[0][0].error:
            return FIX_PATH + "/fixes"
        else:
            return FIX_PATH + "/other_errors"

    def format_entry(self, entry, prev_entry):

        if entry.error == "unparsable":
            return [f": [[{entry.page}]]"]

        if entry.error in ["variable_template_name", "unparsable_template_name", "probably_not_template", "template_namespace"]:
            return [f"; [[{entry.page}]]: {entry.template_name}"]

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


class FileSaverBadParams(WikiSaverBadParams):

    def save_page(self, dest, page_text):
        dest = dest.lstrip("/").replace("/", "_")
        with open(dest, "w") as outfile:
            outfile.write(page_text)
            print("saved", dest)

    def save(self, *args, **nargs):
        super().save(*args, **nargs, commit_message=None)

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
def log(code, page, template_name, key, details, bad_data=None):
    logger.add(code, page, template_name, key, details, bad_data)

fixer = None
def process(args):
    # Needed to unpack args until Pool.istarprocess exists
    try:
        return fixer.process(*args)
    except Exception as e:
        page_text, page_title, *_ = args
        print("Failed processing", page_title)
        raise e

def iter_json(filename, limit=None, show_progress=False, *extra, title_matches=None, text_matches=None):
    count = 0
    with open(filename) as infile:
        data = json.load(infile)
        for template, pages in data["templates"].items():
            if template == "el-link-2":
                continue

            for page, bad_calls in pages.items():

                if not count % 1000 and show_progress:
                    print(count, end = '\r', file=sys.stderr)

                if limit and count >= limit:
                    break
                count += 1

                res = []
                unique_calls = sorted(set(b[1] for b in bad_calls))

                yield "\n".join(unique_calls), page



def main():
    global fixer, TOTAL_TEMPLATES, TOTAL_COUNT, TOTAL_TEMPLATES_WITH_ERRORS
    parser = argparse.ArgumentParser(description="Find errors in sense lists")

    parser.add_argument("--xml", help="XML file to load")
    parser.add_argument("--wxt", help="Wiktionary extract file to load")
    parser.add_argument("--json", help="JSON file with bad calls, previously created with --dump-json")
    parser.add_argument("--templates", help="JSON file with template data", required=True)
    parser.add_argument("--redirects", help="TSV file with redirects", required=True)
    parser.add_argument("--allpages", help="TXT file with allpages", default=None)
    parser.add_argument("--dump-json", help="Output json file with all bad template calls")
    parser.add_argument("--dump-bad-param-only", help="Only dump calls with bad_param to json", action='store_true')
    parser.add_argument("--limit", type=int, help="Limit processing to first N articles")
    parser.add_argument("--progress", help="Display progress", action='store_true')
    parser.add_argument("--save", help="Save to wiktionary with specified commit message")
    parser.add_argument("-j", help="run N jobs in parallel (default = # CPUs - 1", type=int)
    args = parser.parse_args()

    if not args.j:
        args.j = multiprocessing.cpu_count()-1

    if sum(1 for a in [args.xml, args.wxt, args.json] if a) != 1:
        print("use either --xml or --wxt or --json")
        exit(1)

    if args.wxt:
        iter_entries = iter_wxt(args.wxt, args.limit, args.progress)
    elif args.xml:
        iter_entries = iter_xml(args.xml, args.limit, args.progress)
    else:
        iter_entries = iter_json(args.json, args.limit, args.progress)


    test_entries = [("""
{{code|=0}}
""", "test")]
    #iter_entries = test_entries

    fixer = ParamFixer(args.templates, args.redirects, args.allpages)
    TOTAL_TEMPLATES = len(fixer._templates)

    if args.j > 1:
        pool = multiprocessing.Pool(args.j)
        iter_items = pool.imap_unordered(process, iter_entries, 100)
    else:
        iter_items = map(process, iter_entries)


    with open(args.redirects) as infile:
        redirects = {x[0]:x[1] for x in csv.reader(infile, delimiter="\t") if x[0].startswith("Template:")}

    templates_with_errors = set()
    for res in iter_items:
        if not res:
            continue

        count, results = res

        TOTAL_COUNT += count
        for log_values in results:
            code, page, template_name, *other_args = log_values

            template_target = redirects.get(template_name, template_name)
            templates_with_errors.add(template_target)

            log(code, page, template_target, *other_args)

    TOTAL_TEMPLATES_WITH_ERRORS = len(templates_with_errors)

    if args.dump_json:
        templates_with_errors = defaultdict(lambda: defaultdict(list))
        for i in logger._items:
            if args.dump_bad_param_only and i.error != "bad_param":
                continue
            templates_with_errors[i.template_name][i.page].append((i.key, i.details))

        with open(args.dump_json, "w") as outfile:
            json.dump({"templates": templates_with_errors}, outfile, ensure_ascii=False, indent=4, sort_keys=True)

#        with open("templates_with_bad_params.tsv", "w") as outfile:
#            for template, count in sorted(templates_with_errors.items(), key=lambda x: (x[1]*-1, x[0])):
#                print(f"{template}\t{count}", file=outfile)

    if args.save:
        base_url = f"User:JeffDoozan/lists"
        logger.save(base_url, WikiSaver, commit_message=args.save)
        logger.save(base_url, WikiSaverBadParams, commit_message=args.save)
    else:
        dest = ""
        logger.save(dest, FileSaver)
        logger.save(dest, FileSaverBadParams)

if __name__ == "__main__":
    main()
