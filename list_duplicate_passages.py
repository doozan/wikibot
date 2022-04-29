#!/usr/bin/python3

import argparse
import mwparserfromhell
import re
import sys
from collections import defaultdict
from enwiktionary_wordlist.utils import wiki_to_text
from enwiktionary_wordlist.wikiextract import WikiExtractWithRev

parser = argparse.ArgumentParser(description="Find fixable entries")
parser.add_argument("extract", help="language extract file")
parser.add_argument("--list", help="list of articles to check")
parser.add_argument("--mismatched-trans", help="Generate list of mismatched translations", action='store_true')
parser.add_argument("--missing-trans", help="Generate list of missing translations", action='store_true')
args = parser.parse_args()

if args.list:
    with open(args.list) as infile:
        search_articles = set(x.strip().partition(": ")[0] for x in infile)

    if not len(search_articles):
        print("no articles to search")
        exit()

    print(f"Searching {len(search_articles)} articles", file=sys.stderr)
else:
    search_articles = None

seen = defaultdict(lambda: defaultdict(list))

for article in WikiExtractWithRev.iter_articles_from_bz2(args.extract):
    title = article.title
    data = article.text

    if search_articles:
        if title not in search_articles:
            continue
    elif not re.search("(passage|text)=", article.text):
        continue

    wiki = mwparserfromhell.parse(data)
    for t in wiki.ifilter_templates():
        if not t.has("passage") and not t.has("text"):
            continue

        passage = next((str(t.get(p).value) for p in ["passage", "text"] if t.has(p) and str(t.get(p).value)), "")
        passage_text = wiki_to_text(passage, "title")
        passage_text = re.sub(r"[}\|'\"“”«»]", "", passage_text).strip()
        if not passage_text:
            continue

        trans = next((str(t.get(p).value) for p in ["t", "translation"] if t.has(p) and str(t.get(p).value)), "")
        trans_text = wiki_to_text(trans, "title")
        trans_text = re.sub(r"[}\|'\"“”«»]", "", trans_text).strip()

        seen[passage_text][trans_text].append(title)

if args.mismatched_trans:
    mismatched_trans = [k for k,v in seen.items() if len(v) > 1]

    for passage in sorted(mismatched_trans):
        print(f"'''<nowiki>{passage}</nowiki>'''")
        for trans in seen[passage]:
            print(f": [[" + "]], [[".join(sorted(seen[passage][trans])) + f"]]: ''<nowiki>{trans}</nowiki>''")

if args.missing_trans:
    missing_trans = [k for k,v in seen.items() if len(v) == 1 and len(v[""]) > 1]

    for passage in sorted(missing_trans, key=lambda x: (len(seen[x][""])*-1, sorted(seen[x][""]))):
        print("; [[" + "]], [[".join(sorted(seen[passage][""])) + f"]]: <nowiki>{passage}</nowiki>")
