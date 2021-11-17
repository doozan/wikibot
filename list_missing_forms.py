#!/usr/bin/python3

import argparse
import csv
import io
import sys
from enwiktionary_wordlist.wordlist import Wordlist
from enwiktionary_wordlist.all_forms import AllForms
from form_fixer import FormFixer

def get_existing_forms(form, wordlist):
    existing_forms = set()
    for word in wordlist.get_words(form):
        for sense in word.senses:
            # Limit to the formtypes we can handle, forms like "misspelling of" aren't our concern
            if sense.formtype and sense.formtype in FormFixer.all_formtypes:
                existing_forms.add((word.pos, sense.formtype, sense.lemma))

    return existing_forms

def get_masculines_from_fpl(word):
    return [lemma for lemma, forms in word.form_of.items() if "fpl" in forms]

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(description="Generate forms-to-lemmas data from wordlist")
    parser.add_argument("wordlist", help="wordlist")
    parser.add_argument("--allforms", help="all_forms file")
    args = parser.parse_args()

    wordlist = Wordlist.from_file(args.wordlist)
    allforms = AllForms.from_file(args.allforms)
    fixer = FormFixer(wordlist)

#    form = "abisinia"
#    existing_forms = get_existing_forms(form, wordlist)
#    declared_forms = fixer.get_declared_forms(form, wordlist, allforms)

#    print("existing:", existing_forms)
#    print("declared:", declared_forms)
#    missing_forms, unexpected_forms = fixer.compare_forms(declared_forms, existing_forms)
#    print("missing:", missing_forms)
#    print("unexpected:", unexpected_forms)
#    exit()


    for form in allforms.all_forms:
        # Fix for conversion from <sup>x</sup> -> ^x
        if "^" in form:
            continue

        try:
            declared_forms = fixer.get_declared_forms(form, wordlist, allforms)
        except ValueError as e:
            print(f"{form} - error, {e}")
            continue

        existing_forms = get_existing_forms(form, wordlist)

        missing_forms, unexpected_forms = fixer.compare_forms(declared_forms, existing_forms)

        is_doublet = ""
        if missing_forms and unexpected_forms:
            print(f"{form}: has missing and unexpected forms")
            is_doublet = " * has both missing/unexpected"

        for pos, formtype, lemma, lemma_genders in missing_forms:
            if pos == "v":
                continue

            if pos == "n" and formtype == "m":
                print(f"{form}:{pos} declared by {lemma}, but should probably be a lemma $is_doublet")
                continue

            words = list(wordlist.get_words(form, pos))
            if not words:
                print(f"{form}:{pos} missing pos {formtype} of {lemma} $is_doublet")
                continue

#            if pos == "n" and formtype == "pl" and unexpected_forms:
#                masculines = get_masculines_from_fpl(words[0])
#                masculine_links = [m for m in masculines if (pos, "fpl", m) in unexpected_forms]
#                if masculine_links:
#                    for m in masculine_links:
#                        unexpected_forms.remove((pos, "fpl", m))
#                    print(f"{form}:{pos} links to masculine {masculine_links} instead of feminine $is_doublet")
#                    continue

            print(f"{form}:{pos} missing sense {formtype} of {lemma} $is_doublet", sorted(declared_forms), sorted(existing_forms))

        for pos, formtype, lemma in unexpected_forms:
            if pos == "v":
                continue
            words = list(wordlist.get_words(lemma, pos))
            if words:
                print(f"{form}:{pos} unexpected form, claims to be {formtype} of {lemma}, but not reciprocated $is_doublet")
            else:
                print(f"{form}:{pos} unexpected form, claims to be {formtype} of nonexistent {lemma} $is_doublet")
