#!/usr/bin/python3

import re
import argparse
from enwiktionary_wordlist.wordlist import Wordlist

def main():
    import argparse

    parser = argparse.ArgumentParser(description="List verbs missing a type label in at least one sense")
    parser.add_argument("wordlist", help="wordlist")
    args = parser.parse_args()

    wordlist = Wordlist.from_file(args.wordlist)

    missing_type = set()
    for word in wordlist.iter_all_words():
        if word.pos != "v":
            continue

        if not len(word.senses):
            continue

        if word.meta and "verb form" in word.meta:
            continue

        for s in word.senses:
            if not s.qualifier or not re.search(r"(transitive|reflexive|pronominal)", s.qualifier):
                missing_type.add(word.word)
                break

    for f in sorted(missing_type):
        print(f)

if __name__ == "__main__":

    main()

