#!/usr/bin/python3

import argparse
import mwparserfromhell
import re
import sys
from collections import defaultdict
from enwiktionary_wordlist.utils import wiki_to_text
from enwiktionary_wordlist.language_extract import LanguageFile

parser = argparse.ArgumentParser(description="Find fixable entries")
parser.add_argument("extract", help="language extract file")
parser.add_argument("list", help="list of articles to check")
args = parser.parse_args()

with open(args.list) as infile:
    search_articles = set(x.strip().partition(": ")[0] for x in infile)

if not len(search_articles):
    print("no articles to search")
    exit()

print(f"Searching {len(search_articles)} articles", file=sys.stderr)

seen = defaultdict(list)
for item in LanguageFile.iter_articles(args.extract):
    title, data = item
    if title not in search_articles:
        continue

    wiki = mwparserfromhell.parse(data)
    for t in wiki.ifilter_templates():
        if not t.has("passage") and not t.has("text"):
            continue
        if t.has("t") or t.has("translation"):
            continue

        passage = str(t.get("passage").value) if t.has("passage") else str(t.get("text").value)
        passage_text = wiki_to_text(passage, "title")
        passage_text = re.sub(r"[}\|'\"“”«»]", "", passage_text)
        if not passage_text:
            continue
        seen[passage_text].append(title)

for k,v in sorted(seen.items(), key=lambda x: (len(x[1]), x[1]), reverse=True):
    if len(v) > 1:
        print("; [[" + "]], [[".join(sorted(v)) + "]]: <nowiki>" + k[len("passage="):] + "</nowiki>")
