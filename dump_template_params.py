#!/usr/bin/python3

import argparse
import json
import multiprocessing
import os
import re
import sys

from autodooz.fix_rq_template import RqTemplateFixer
from collections import defaultdict
from pywikibot import xmlreader


# https://www.mediawiki.org/wiki/Help:Magic_words
MAGIC_WORDS = [ "FULLPAGENAME", "PAGENAME", "BASEPAGENAME", "NAMESPACE", "!" ]




def iter_xml(datafile, limit=None, show_progress=False):
    dump = xmlreader.XmlDump(datafile)
    parser = dump.parse()

    count = 0
    for entry in parser:
        if not count % 1000 and show_progress:
            print(count, end = '\r', file=sys.stderr)

        if limit and count >= limit:
            break
        count += 1

        if not entry.title.startswith("Template:"):
            continue

        yield entry.text, entry.title

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

#        if not entry.title in ["Template:syc-decl-noun"]:
#            continue

        if not entry.title.startswith("Template:"):
            continue

        yield entry.text, entry.title

def main():
    parser = argparse.ArgumentParser(description="Find errors in sense lists")
    parser.add_argument("target", help="target filename")
    parser.add_argument("--xml", help="XML file to load")
    parser.add_argument("--wxt", help="Wiktionary extract file to load")
    parser.add_argument("--limit", type=int, help="Limit processing to first N articles")
    parser.add_argument("--progress", help="Display progress", action='store_true')
    parser.add_argument("-j", help="run N jobs in parallel (default = # CPUs - 1", type=int)
    args = parser.parse_args()

    if (not args.xml and not args.wxt) or (args.xml and args.wxt):
        print("use either --xml or --wxt")
        exit(1)

    if not args.j:
        args.j = multiprocessing.cpu_count()-1

    if args.wxt:
        iter_entries = iter_wxt(args.wxt, args.limit, args.progress)
    else:
        iter_entries = iter_xml(args.xml, args.limit, args.progress)

    dump_template_args(iter_entries, args.target)


def get_included_text(text):
    text = re.sub("<!--.*?-->", "", text, flags=re.DOTALL)
    text = re.sub("<\s*noinclude\s*[/]\s*>", "", text, flags=re.DOTALL)
    text = re.sub("<\s*noinclude\s*>.*?<\s*/\s*noinclude\s*>", "", text, flags=re.DOTALL)
    text = re.sub(r"<\s*[/]?\s*includeonly\s*[/]?\s*>", "", text)
    return text


invoke_count = defaultdict(int)

fixer = None
def get_allowed_params(args):

    entry_text, entry_title = args
    entry_title = entry_title.removeprefix("Template:")
    entry_text = get_included_text(entry_text)

    m = re.match(r"^\s*#REDIRECT[:]?\s*\[\[\s*([:]?T(?:emplate)?:(.*?))\s*\]\]", entry_text, re.IGNORECASE)
    if m:
        return entry_title, {"|REDIR|": m.group(2).strip()}

    ALLOWED_INVOKE = [ "string", "ugly hacks" ]
    invokes = [m.group(1).strip() for m in re.finditer("#invoke:(.*?)[|}]", entry_text, re.DOTALL)]
    for i in invokes:
        invoke_count[i] += 1
    if not all(i in ALLOWED_INVOKE for i in invokes):
        return entry_title, None

    entry_title = entry_title.removeprefix("Template:")
    #used_params = list({m.group(1):1 for m in re.finditer(r"\{\{\{\s*([a-zA-Z0-9. +/_-]+?)[|}]", entry_text)}.keys())
    used_params = list({m.group(1).strip():1 for m in re.finditer(r"\{\{\{\s*([^=|{}<>]+?)[|}]", entry_text)}.keys())

    # filter out PAGENAME, etc
    used_params = [p for p in used_params if p not in MAGIC_WORDS]

    return entry_title, used_params



def dump_template_args(iter_entries, filename):
    global fixer
    fixer = RqTemplateFixer(None)
    iter_items = map(get_allowed_params, iter_entries)

    templates = {}
    unparsable = set()
    redirects = {}
    for res in iter_items:
        entry_title, allowed_params = res
        if allowed_params is None:
            unparsable.add(entry_title)
        elif "|REDIR|" in allowed_params:
            target = allowed_params["|REDIR|"]
            redirects[entry_title] = target
        else:
            templates[entry_title] = allowed_params

    with open(filename, 'w', encoding='utf-8') as outfile:
        json.dump({
            "templates": {k:v for k,v in sorted(templates.items())},
            "unparsable": sorted(unparsable),
            "redirects": {k:v for k,v in sorted(redirects.items())},
            }, outfile, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()
#    for k,v in sorted(invoke_count.items(), key=lambda x: (x[1], x[0])):
#        print(v, k)
