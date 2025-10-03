#!/usr/bin/python3

import argparse
import multiprocessing
import os
import re
import sys

from autodooz.utils import iter_wxt
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
        return sorted(items, key=lambda x: ("autofix" not in x.error, count[x.error], x.error, x.page))

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

        if entry.details is None:
            print("BAD", entry)
            return []

        data = entry.details.replace("__HIGHLIGHT__", '</nowiki><b><u>').replace("__/HIGHLIGHT__", '</u></b><nowiki>')

        return [f": [[{entry.page}|{entry.path}]]\n <nowiki>{data}</nowiki>"]

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

delims = [
        (
            ["{{"],
            ["}}"]
        ),
        (
            ["{", "&lbrace;", "&#x7B;", "&lcub;"],
            ["}", "&rbrace;", "&#x7D;", "&rcub;"],
        ),
        (
            ["[", "&lbrack;", "&#91;", "&lsqb;"],
            ["]", "&rbrack;", "&#93;", "&rsqb;"]
        )
    ]

def highlight_unmatched(opener, closer, text):
    depth = []
    unmatched = []
    for i, c in enumerate(text):
        if c == opener:
            depth.append(i)
        if c == closer:
            if depth:
                depth.pop(0)
            else:
                unmatched.append(i)
    unmatched += depth
    for i in reversed(sorted(unmatched)):
        text = text[:i] + "__HIGHLIGHT__" + text[i] + "__/HIGHLIGHT__" + text[i+1:]

#    print("unmatched", unmatched)
    return text


#assert (res := highlight_unmatched("{", "}", "TEST{TEST")) == "TEST__HIGHLIGHT__{__/HIGHLIGHT__TEST", res
#assert highlight_unmatched("{", "}", "TEST}TEST") == "TEST__HIGHLIGHT__}__/HIGHLIGHT__TEST"
#assert highlight_unmatched("{", "}", "T{E}ST}TEST") == "T{E}ST__HIGHLIGHT__}__/HIGHLIGHT__TEST"
#assert highlight_unmatched("{", "}", "TESTTEST{") == "TESTTEST__HIGHLIGHT__{__/HIGHLIGHT__"
#assert highlight_unmatched("{", "}", "}TESTTEST") == "__HIGHLIGHT__}__/HIGHLIGHT__TESTTEST"

def process_page(text, title, summary=None, options=None):

    # Strip <mapframe>, <math>, <score> and HTML comments
    #text = re.sub(r"<\s*nowiki\s*>.*?<\s*/\s*nowiki\s*>", "", text, flags=re.DOTALL)
    text = re.sub(r"<\s*mapframe(\s[^/>]*)?>.*?<\s*/\s*mapframe\s*>", "", text, flags=re.DOTALL)
    text = re.sub(r"<\s*math(\s[^/>]*)?>.*?<\s*/\s*math\s*>", "", text, flags=re.DOTALL)
    text = re.sub(r"<\s*score\s*?(\s[^>]*)?>.*?<\s*/\s*score\s*>", "", text, flags=re.DOTALL)
    text = re.sub("<!--.*?-->", "", text, flags=re.DOTALL)

    entry = sectionparser.parse(text, title)
    if not entry:
        print("no entry", title)
        return []

    log = []

    for section in entry.filter_sections():
        for text in section.content_wikilines:
            for openers, closers in delims:

                opener = openers[0]
                closer = closers[0]

                open_count = text.count(opener)
                close_count = text.count(closer)

                all_open_count = sum(text.count(o) for o in openers)
                all_close_count = sum(text.count(c) for c in closers)

                if open_count != close_count and all_open_count != all_close_count:

                    language = list(section.lineage)[-2]
                    page = title + "#" + language

                    unmatched = opener if open_count > close_count else closer

                    # Navajo uses {{nv-theme-header}} plus |} to build tables
                    if unmatched == "}" and language == "Navajo":# and (close_count - open_count == text.count("{{nv-theme-header}}") == text.count("\n|}")):
                        continue

                    highlighted = highlight_unmatched(opener[0], closer[0], text)

                    # ignore quote templates and quotes that start with [ (used when quoting an alt form of the lemma)
                    if unmatched == "[":
                        if "{{quote-" in highlighted or highlighted.startswith("#* [") or highlighted.startswith("#* __HIGHLIGHT__[__/HIGHLIGHT__"):
                            continue

                    # ignore quote templates and quotes that end with ] (used when quoting an alt form of the lemma)
                    if unmatched == "]":
                        if "{{quote-" in highlighted or (highlighted.startswith("#*: ") and highlighted.endswith("__HIGHLIGHT__]__/HIGHLIGHT__")):
                            continue

                    log.append((f"extra_{unmatched}", page, title + ":" + section.path, highlighted)) # f"{open_count}, {close_count}"))

    return log

def process(args):
    # Needed to unpack args until Pool.istarprocess exists
    return process_page(*args)

def main():
    parser = argparse.ArgumentParser(description="Find Spanish nouns with manually specified forms")
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
