#!/usr/bin/python3

import argparse
import mwparserfromhell
import re
import sys
from collections import defaultdict
from enwiktionary_wordlist.utils import wiki_to_text
from enwiktionary_wordlist.wikiextract import WikiExtractWithRev

def clean(text):
    text = re.sub(r"[}\|\"“”«»]", "", text).strip()
    text = re.sub(r"''+", "", text)
    return text

def get_text_trans_from_passage(t, title):

    passage = next((str(t.get(p).value) for p in ["passage", "text"] if t.has(p) and str(t.get(p).value).strip()), "")
    passage_text = clean(wiki_to_text(passage, title))

    trans = next((str(t.get(p).value) for p in ["t", "translation"] if t.has(p) and str(t.get(p).value).strip()), "")
    trans_text = clean(wiki_to_text(trans, title))

    return passage_text, trans_text

def get_text_trans_from_ux(t, title):

    passage = next((str(t.get(p).value) for p in [2] if t.has(p) and str(t.get(p).value).strip()), "")
    passage_text = clean(wiki_to_text(passage, title))

    trans = next((str(t.get(p).value) for p in [3, "t", "translation"] if t.has(p) and str(t.get(p).value).strip()), "")
    trans_text = clean(wiki_to_text(trans, title))

#    print("trans", trans_text, "@", str(t))

    return passage_text, trans_text

def load_passages(filename):
    passages = defaultdict(lambda: defaultdict(list))
#    seen_templates = defaultdict(int)
#    no_trans = defaultdict(int)

    for article in WikiExtractWithRev.iter_articles_from_bz2(filename):
        title = article.title
        data = article.text

        if not re.search("{{(ux|quote|RQ|cite)", article.text):
            continue

        wiki = mwparserfromhell.parse(data)
        for t in wiki.ifilter_templates():

            text = trans = None
            if t.has("passage") or t.has("text"):
                text, trans = get_text_trans_from_passage(t, title)
            elif t.name.strip() in ["uxi", "ux", "quote"]:
                text, trans = get_text_trans_from_ux(t, title)
            else:
                continue

            if not text:
#                print("no passage", title, str(t), file=sys.stderr)
                continue

#            seen_templates[str(t.name).strip()] += 1
#            if not trans:
#                no_trans[str(t.name).strip()] += 1

            passages[text][trans].append(title)

#    for template, count in sorted(seen_templates.items(), key=lambda x: x[1]):
#        print(count, template, no_trans.get(template, 0), file=sys.stderr)
    return passages


def main():
    parser = argparse.ArgumentParser(description="Find fixable entries")
    parser.add_argument("extract", help="language extract file")
    parser.add_argument("--list", help="list of articles to check")
    parser.add_argument("--mismatched-trans", help="Generate list of mismatched translations", action='store_true')
    parser.add_argument("--missing-trans", help="Generate list of missing translations", action='store_true')
    parser.add_argument("--dump", help="Dump all missing translations", action='store_true')
    parser.add_argument("--tag", help="Merge extra data", action='store_true')
    args = parser.parse_args()

    if args.tag:
        builder.print_tagged_data(args.sentences, args.tags[0], args.verb_rank, args.verbose)

    if args.list:
        with open(args.list) as infile:
            search_articles = set(x.strip().partition(": ")[0] for x in infile)

        if not len(search_articles):
            print("no articles to search")
            exit()

        print(f"Searching {len(search_articles)} articles", file=sys.stderr)
    else:
        search_articles = None

    passages = load_passages(args.extract)

    if args.mismatched_trans:
        mismatched_trans = [k for k,v in passages.items() if len(v) > 1]

        for passage in sorted(mismatched_trans):
            print(f"'''<nowiki>{passage}</nowiki>'''")
            for trans in passages[passage]:
                print(f": [[" + "]], [[".join(sorted(passages[passage][trans])) + f"]]: ''<nowiki>{trans}</nowiki>''")

    if args.missing_trans:
        missing_trans = [k for k,v in passages.items() if len(v) == 1 and len(v[""]) > 1]

        for passage in sorted(missing_trans, key=lambda x: (len(passages[x][""])*-1, sorted(passages[x][""]))):
            print("; [[" + "]], [[".join(sorted(passages[passage][""])) + f"]]: <nowiki>{passage}</nowiki>")

    count = 0
    for passage in passages.keys():
        if "\n" in passage:
            count += 1

    if args.dump:
        print("")
        for passage in [k for k,v in passages.items() if list(v.keys()) == [""]]:
            passage = passage.replace("\n", " \\ ")
            pages = "|".join(sorted(passages[passage][""]))
            print(f"{passage}\t{pages}")


if __name__ == "__main__":
    main()
