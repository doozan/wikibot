#!/usr/bin/python3

import argparse
import multiprocessing
import os
import re
import sys

from autodooz.fix_bare_quotes import QuoteFixer
from autodooz.quotes.make_data import load_filters, is_filtered, get_condensed_values
from autodooz.quotes.name_labeler import NameLabeler
from collections import defaultdict

def get_unparsable(fixer, filename):

    all_items = []
    with open(filename) as infile:
        start = False
        for idx, line in enumerate(infile):
            #if idx > 2000:
            #    break

            line = line.strip()
            if not line:
                continue

            if not start:

                if line == "===pipe_in_translation===":
                #if line == "===pipe_in_passage===":
                #if line == "===unparsable_line===":
                    start=True
                continue

            m = re.match(r": \[\[(.*?)]] <nowiki>(.*)</nowiki>", line)
            if not m:
                continue
            page = m.group(1)
            text = m.group(2)

            text = text.lstrip("#:* ").strip()
            all_items.append((page, text))

    total = len(all_items)
    count = 0
    for page, text in all_items:
        if not count % 100:
            print(f"{count}/{total}", end = '\r', file=sys.stderr)
        count += 1

        yield fixer, page, text


def process(args):
    fixer, page, text = args
    # Needed to unpack args until Pool.istarprocess exists
    res = fixer.get_params(text)
    if res:
        return (page, res, text)
    return


def iter_wxt(datafile, limit=None, show_progress=False):

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

        yield entry.text, entry.title


def main():

    parser = argparse.ArgumentParser(description="Find Spanish nouns with manually specified forms")
    parser.add_argument("--src", help="errors file", default="errors")
    parser.add_argument("--datadir", required=True)
    args = parser.parse_args()

    cpus = multiprocessing.cpu_count()-1
    pool = multiprocessing.Pool(cpus)

    labeler = NameLabeler(os.path.join(args.datadir, "author.allowed"))

    valid = 0
    invalid = 0

    all_filters = load_filters(args.datadir)

    pages = set()
    all_params = defaultdict(dict)
    fixer = QuoteFixer(aggressive=True)


    allowed = {}
    for p in ("author", "journal", "location", "publisher"):
        with open(os.path.join(args.datadir, f"{p}.allowed")) as infile:
            p_short = p[0]
            allowed[p_short] = {line.strip() for line in infile if line.strip()}

    new = defaultdict(list)
    for res in pool.imap_unordered(process, get_unparsable(fixer, args.src), 100):
        if res:
            page, params, line = res
            for k, v in params.items():

                if not k.startswith("author") and k not in ["publisher", "location", "journal"]:
                    continue

                p = k[0]
                v = v.lower()
                for val in get_condensed_values(v, p):

                    # Skip items that are explicitly allowed
                    if val in allowed[p]:
                        continue

                    # Skip items that are explictly disallowed
                    if v in all_filters[p]:
                        continue

                    # no need to manually verify names that looks like valid names
                    if p == "a" and labeler.is_valid_name(v, skip_case_checks=True):
                        continue

                    new[p].append((val, v, line))

            pages.add(page)
            valid += 1
        else:
            invalid += 1

    print("                ", file=sys.stderr)
    print("Valid", valid, file=sys.stderr)
    print("Invalid", invalid, file=sys.stderr)

    if not valid:
        return

    with open(os.path.join(args.datadir, "fixed.pages"), "w") as outfile:
        outfile.write("\n".join(sorted(pages)))

    for p, value_lines in new.items():
        with open(os.path.join(args.datadir, f"{p}.new"), "w") as outfile:
            seen = set()
            for condensed, value, line in sorted(value_lines):
                if condensed in seen:
                    continue
                seen.add(condensed)
                print(f"\t{condensed}\t{value}\t{line}", file=outfile)

if __name__ == "__main__":
    main()
