#!/usr/bin/python3

import csv
import sys
import urllib.parse

from autodooz.fix_es_drae import DraeFixer
from collections import defaultdict
from enwiktionary_wordlist.all_forms import AllForms
from enwiktionary_wordlist.wordlist import Wordlist
from spanish_tools.freq import NgramPosProbability


from drae.drae_utils import get_forms, load_forced_forms


def has_real_entry(wordlist, title):
    for word in wordlist.get_words(title):
        for sense in word.senses:
            if not sense.gloss.startswith("used in"):
                return True
    return False

def get_preferred_case(filename):
    preferred_case = {}
    seen = set()
    with open(filename) as infile:
        for line in infile:
            word, count = line.strip().split('\t')
            word_lc = word.lower()
            if word_lc in seen:
                continue
            seen.add(word_lc)
            if word_lc not in preferred_case:
                preferred_case[word_lc] = word

    return preferred_case

def get_counts(filename, drae_links):
    counts = defaultdict(int)
    with open(filename) as infile:
        rows = csv.reader(infile)

        for x, row in enumerate(rows):
            if x == 0:
                continue
            count = row[0]
            word = row[1]

            # resolve phrase forms to phrase lemmas
            lemmas = drae_links.get(word, [word])
            for lemma in set(lemmas):
                counts[lemma] += int(count)

    return counts


def main():

    import argparse

    parser = argparse.ArgumentParser(description="Generate list of missing forms")
    parser.add_argument("--wikt", help="wiktionary allforms list", required=True)
    parser.add_argument("--drae-links", help="drae links database", required=True)
    parser.add_argument("--forced-forms", help="forced line patterns", required=True)
    parser.add_argument("--freq", help="drae frequency list", required=True)
    parser.add_argument("--counts", help="word count data file", required=True)
    parser.add_argument("--wordlist", help="drae.data", required=True)
    parser.add_argument("--ignore", help="lines to ignore")
    parser.add_argument("--min-len", type=int, default=0)
    parser.add_argument("--min-use", type=int, default=0)
    args = parser.parse_args()

    wikt_forms = AllForms.from_file(args.wikt)

    wordlist = Wordlist.from_file(args.wordlist)

    forced_forms = load_forced_forms(args.forced_forms)

    preferred_case = get_preferred_case(args.counts)

    drae_links, must_link_by_id = DraeFixer.load_links(args.drae_links)

    counts = get_counts(args.freq, drae_links)

    res = []
    res.append("<!--IGNORE (any items inside this comment block will be excluded from the report when this page is refreshed)")
    ignore_lines = set()
    if args.ignore:
        with open(args.ignore) as infile:
            for line in infile:
                line = line.rstrip()
                res.append(line)
                if line.startswith(":"):
                    ignore_lines.add(line)
    res.append("-->\n")

    results = []
    for lemma in wordlist.all_entries.keys():
        clean_lemma = lemma.replace("[", "").replace("]", "")

        count = int(counts.get(clean_lemma, 0))
        if args.min_use and count < args.min_use:
            continue

        forms = get_forms(lemma, forced_forms)

        if any(wikt_forms.has_lemma(f) for f in forms):
            continue

        form = forms[0]
        if len(forms) == 1 and form.endswith("r") and wikt_forms.has_form(form, "v") and wikt_forms.has_lemma(form + "se", "v"):
            continue

        if len(forms) == 1 and form.endswith("rse") and wikt_forms.has_form(form, "v") and wikt_forms.has_lemma(form[:-2], "v"):
            continue

        if args.min_len and all(len(f.split()) < args.min_len for f in forms):
            continue

        if not has_real_entry(wordlist, lemma):
            print("Skipping placeholder", lemma, file=sys.stderr)
            continue

        clean_lemma = lemma.replace("[", "").replace("]", "")
        targets = drae_links.get(clean_lemma)
        if not targets:
            print("No link", lemma, file=sys.stderr)
        else:
            results.append((count, lemma, forms, targets))

    results.sort(key=lambda x: (x[0]*-1, x[1]))

    total = 0
    for count, lemma, forms, targets in results:

        if " " not in lemma:
            alt_case = preferred_case.get(lemma, lemma)
            if alt_case != lemma:
                print("Skipping alt-case", lemma, alt_case, file=sys.stderr)
                continue

        links = []
        for target in sorted(set(targets)):

            link_id = must_link_by_id.get(target)
            if link_id:
                url_target = f"https://dle.rae.es/{link_id}"
                links.append(f"[{url_target} {target}]")
            else:
                url_target = "https://dle.rae.es/" + urllib.parse.quote(target)
                links.append(f"[{url_target} {target}]")

        wiki_links = []
        for f in forms:
            if f.startswith("¿") and f.endswith("?"):
                wiki_links.append("¿[[" + f[1:-1] + "]]?")
            else:
                wiki_links.append(f"[[{f}]]")

        drae = ', '.join(links)
        wiki = ', '.join(wiki_links)

        line = f": {wiki}: {drae}"
        if line not in ignore_lines:
            res.append(line)

        total += 1

    res.insert(0,f"({total} entries); used at least {args.min_use} times in Google Ngram corpus 2012-2019, sorted by frequency of use")
    for line in res:
        print(line)

if __name__ == "__main__":
    main()
