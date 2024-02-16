#!/usr/bin/python3

import argparse
import mwparserfromhell as mwparser
import multiprocessing
import os
import re
import sys
import json

from autodooz.fix_rq_template import RqTemplateFixer
from autodooz.fix_bad_rq_params import RqParamFixer
from autodooz.wikilog import WikiLogger, BaseHandler
from collections import defaultdict, namedtuple

FIX_PATH = "rq"

class WikiSaver(BaseHandler):

    def sort_items(self, items):
        print("SORTING", len(items))
        count = defaultdict(int)
        for item in items:
            count[item.template_name] += 1

        # sort autofix sections first so they can be split into other pages
        # everything else sorted by count of section entries (smallest to largest)
        return sorted(items, key=lambda x: ("autofix" not in x.error, count[x.template_name]*-1, x.template_name, x.key, x.page))

    def is_new_section(self, item, prev_item):
        return prev_item and prev_item.template_name != item.template_name

    def is_new_page(self, page_sections, section_entries):
        return page_sections and (page_sections[-1][-1].error.startswith("autofix") != section_entries[0].error.startswith("autofix"))

    def page_name(self, page_sections, prev):
        if "autofix" in page_sections[0][0].error:
            return FIX_PATH + "/fixes"
        else:
            return FIX_PATH + "/errors"

    def format_entry(self, entry, prev_entry):

        data = str(entry.template_data).replace(entry.bad_data, '<span style="color:red">' + entry.bad_data + '</span>', 1)
        data = data.replace("|", "&vert;").replace("{", "&lbrace;").replace("[", "&lbrack;").replace("://", "<nowiki/>://")

        details = entry.details if entry.details else f"bad param '{entry.key}'"

        if "misnamed" in entry.error:
            return [f"[[Template:{entry.template_name}]] {details} on [[{entry.page}]]"]
        else:
            return [f"[[Template:{entry.template_name}]] {details} on [[{entry.page}]]", f": {data}"]

    def get_section_header(self, base_path, page_name, section_entries, prev_section_entries, pages):
        res = []

        #if prev_section_entries and len(prev_section_entries) >= 2 and len(section_entries) < 2:
        #    res.append("")
        #    res.append("===Other templates===")
        #    return res

        #if len(section_entries) < 2:
        #    return res

        item = section_entries[0]
        count = len(section_entries)

        if prev_section_entries:
            res.append("")
        res.append(f"==={item.template_name}===")
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
    _paramtype = namedtuple("params", [ "error", "page", "template_name", "key", "details", "template_data", "bad_data" ])

logger = Logger()
bad_templates = set()
def log(code, page, template_name, key, details, template_data=None, bad_data=None):
    logger.add(code, page, template_name, key, details, template_data, bad_data)
    if "autofix" not in code:
        bad_templates.add(template_name)

def iter_wxt(datafile, limit=None, show_progress=False):

    if not os.path.isfile(datafile):
        raise FileNotFoundError(f"Cannot open: {datafile}")

    from enwiktionary_wordlist.wikiextract import WikiExtractWithRev
    parser = WikiExtractWithRev.iter_articles_from_bz2(datafile)

    count = 0
    for entry in parser:

#        if entry.title != "abound":
#            continue

#        if "RQ:Dickens Old Curiosity Shop" not in entry.text:
#            continue

        #if ":" in entry.title or "/" in entry.title:
        #    continue

        if not count % 1000 and show_progress:
            print(count, end = '\r', file=sys.stderr)

        if limit and count >= limit:
            break
        count += 1

        yield entry.text, entry.title


#def dump_template_data(templates_wxt, target_filename):
#
#    templates = {}
#    apf = AllowparamsFixer()
#
#    for entry in iter_wxt(templates_wxt):
#        entry_text, entry_title = entry
#
#        new_text = apf.process(entry_text, entry_title, [])
#
#        invoke_count = len(re.findall("^{{#invoke:", new_text, re.MULTILINE))
#        if not invoke_count == 1:
#            continue
#
#        if not "{{#invoke:quote" in new_text:
#            continue
#
#        auto_props = apf.get_auto_props(new_text)
#
#        manual_props = apf.get_params("propagateparams", new_text, entry_title)
#        if page_params is None:
#            continue
#
#        used_params = apf.get_used_params(new_text)
#        declared_params = apf.get_declared_params(new_text)
#
#        allowed_params = auto_props + manual_props + used_params + declared_params
#
#        entry_title = entry_title.removeprefix("Template:")
#
#        templates[entry_title] = allowed_params
#
#    templates = {k:v for k,v in sorted(templates.items())}
#
#    with open(target_filename, 'w', encoding='utf-8') as outfile:
#        json.dump(templates, outfile, ensure_ascii=False, indent=4)


fixer = None
def process(args):
    # Needed to unpack args until Pool.istarprocess exists
    return fixer.process(*args)

def main():
    global fixer
    parser = argparse.ArgumentParser(description="Find errors in sense lists")
    parser.add_argument("wxt", help="Wiktionary extract file")
    parser.add_argument("--templates", help="Wiktionary extract file with RQ: templates")
    parser.add_argument("--limit", type=int, help="Limit processing to first N articles")
    parser.add_argument("--progress", help="Display progress", action='store_true')
    parser.add_argument("--save", help="Save to wiktionary with specified commit message")
    parser.add_argument("-j", help="run N jobs in parallel (default = # CPUs - 1", type=int)
    args = parser.parse_args()

    if not args.j:
        args.j = multiprocessing.cpu_count()-1


    template_datafile = "templates.json"

#    if args.templates:
#        dump_template_data(args.templates, template_datafile)

    fixer = RqParamFixer(template_datafile)

    iter_entries = iter_wxt(args.wxt, args.limit, args.progress)

    if args.j > 1:
        pool = multiprocessing.Pool(args.j)
        iter_items = pool.imap_unordered(process, iter_entries, 1000)
    else:
        iter_items = map(process, iter_entries)

    for results in iter_items:
        for log_values in results:
            log(*log_values)

    with open("templates_with_bad_params.json", "w") as outfile:
        json.dump(sorted(bad_templates), outfile, ensure_ascii=False, indent=4)

    if args.save:
        base_url = f"User:JeffDoozan/lists"
        logger.save(base_url, WikiSaver, commit_message=args.save)
    else:
        dest = ""
        logger.save(dest, FileSaver)

if __name__ == "__main__":
    main()
