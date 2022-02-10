#!/usr/bin/python3

import argparse
from collections import defaultdict, namedtuple
import csv
import io
import pywikibot
import re
import sys
from enwiktionary_wordlist.wordlist import Wordlist
from enwiktionary_wordlist.all_forms import AllForms
from form_fixer import FormFixer
from autodooz.wikilog import WikiLogger, BaseHandler

class Logger(WikiLogger):
    _paramtype = namedtuple("params", [ "error", "form", "item" ])

class WikiSaver(BaseHandler):
    error_header = {
        "form_errors": "Errors while processing forms",
        "should_be_lemma": "Forms that should probably be lemmas (manual review needed)",
#        "missing_page": "Redlinks",
        "missing_entry": "Missing Spanish section (bot job)",
        "missing_pos": "Missing POS entry (bot job)",
        "missing_pos_multi_ety": "Missing POS entry, entry has multiple etymologies (manual review needed)",
        "missing_sense": "Entry exists, but is missing a 'form of' declaration",
        "wrong_form": "Entry has existing 'form of' that doesn't match the expected 'form of'",
        "unexpected_form": "Entry claims to be a 'form of' lemma but is not declared by the lemma",
        "missing_lemma": "Entry claims to be a 'form of' non-existent lemma",
    }

    def sort_items(self, items):
        return sorted(items, key=lambda x:(x.error,  x.form))

    def is_new_page(self, page_sections, section_entries):
        # each error is a new page
        return page_sections and page_sections[-1][-1].error != section_entries[0].error

    def is_new_section(self, item, prev_item):
        # Split by error
        return prev_item and prev_item.error != item.error

    def page_name(self, page_sections, prev):
        # named by error code
        return page_sections[0][0].error

    # Add empty pages if they generated no errors
    def make_pages(self, *args, **nargs):
        pages = super().make_pages(*args, **nargs)
        for error in self.error_header.keys():
            if error not in pages:
                pages[error] = []
        return pages

    def page_header(self, base_path, page_name, page_sections, pages):
        count = sum(map(len, page_sections))
        header = self.error_header.get(page_name, page_name)
        return [f"{header}: {count} item{'' if count==1 else 's'}"]

    def format_entry(self, entry, prev_entry):

        pos, formtype, lemma, *_ = entry.item

        if entry.error in [ "missing_sense", "missing_pos_multi_ety", "missing_pos" ]:
            try:
                data = f"{pos} <nowiki>" + fixer.get_form_gloss(entry.form, entry.item) + "</nowiki>"
            except ValueError:
                data = f"{pos} ({formtype} of [[{lemma}#Spanish|{lemma}]])"

        elif entry.error == "should_be_lemma":
            data = f"{pos} declared by [[{lemma}#Spanish|{lemma}]]:{pos}"
        elif entry.error == "missing_page":
            data = f" ({formtype} of [[{lemma}#Spanish|{lemma}]]:{pos})"
        elif entry.error == "missing_entry":
            data = f" ({formtype} of [[{lemma}#Spanish|{lemma}]]:{pos})"
        elif entry.error == "unexpected_form":
            data = f"{pos} is not declared a {formtype} of [[{lemma}#Spanish|{lemma}]]:{pos}"
        elif entry.error == "missing_lemma":
            data = f"{pos} claims to be {formtype} of non-existent lemma [[{lemma}#Spanish|{lemma}]]:{pos}"
        else:
            #"missing_pos": " does not have POS {pos} ({formtype} of {lemma}:{pos})",
            #"missing_pos_multiple_ety": " does not have POS {pos} ({formtype} of {lemma}:{pos})",
            #"missing_sense": "{pos} <nowiki>{fixer2.get_form_gloss(item)}</nowiki>",
            #"wrong_form": "{pos} ({formtype} of [[{lemma}#Spanish|{lemma}]])",
            data = entry.item

        return [f": [[{entry.form}#Spanish|{entry.form}]]:" + data]

class FileSaver(WikiSaver):

    def save_page(self, dest, page_text):
        dest = dest.lstrip("/").replace("/", "_")
        with open(dest, "w") as outfile:
            outfile.write(page_text)
            print("saved", dest)

    def save(self, *args, **nargs):
        super().save(*args, **nargs, commit_message=None)

logger = Logger()

def error(error_id, form, item):
    logger.add(error_id, form, item)


fixer = None

def get_existing_forms(form, wordlist):
    words = wordlist.get_words(form)
    return get_word_forms(words)

def get_word_forms(words):
    existing_forms = set()

    for word in words:

        #if word.pos == "n" and word.genders and ("f" in word.genders or "m" in word.genders):
        #if word.pos in ["n", "adj"] and word.genders == "f":
        #if word.genders in ["m", "f"]:

        # masculines are almost always the preferred lemma form so only look at the feminine
        # when considering headword declarations to be a "form of" another lemma
        #if word.genders in ["m", "f"]:
        if word.genders == "f":
            gender = "f"# if "f" in word.genders else "m"
            mate =  "m"# if gender == "f" else "f"

            if mate in word.forms:
                for mate_lemma in word.forms[mate]:
                    existing_forms.add((word.pos, gender, mate_lemma))

        for sense in word.senses:
            # Limit to the formtypes we can handle, forms like "misspelling of" aren't our concern
            if sense.formtype and FormFixer.can_handle_formtype(sense.formtype):
                existing_forms.add((word.pos, sense.formtype, sense.lemma))

    return existing_forms

def get_masculines_from_fpl(word):
    return [lemma for lemma, forms in word.form_of.items() if "fpl" in forms]

def main(wordlist_file, allforms_file, allpages_file, limit=0, progress=False):

    global fixer

    wordlist = Wordlist.from_file(wordlist_file)
    allforms = AllForms.from_file(allforms_file)
    fixer = FormFixer(wordlist)

    with open(allpages_file) as infile:
        allpages = { x.strip() for x in infile }

#    form = "achaparrándolo"
#    declared_forms = fixer.get_declared_forms(form, wordlist, allforms)
#    existing_forms = get_existing_forms(form, wordlist)
#    missing_forms, unexpected_forms = fixer.compare_forms(declared_forms, existing_forms)
#    print("declared", declared_forms)
#    print("existing", existing_forms)
#    print("missing", missing_forms)
#    print("unexpected", unexpected_forms)
#    exit()


    count = 0
    for form in allforms.all_forms:

        # Fix for conversion from <sup>x</sup> -> ^x
        if "^" in form:
            continue

        try:
            declared_forms = fixer.get_declared_forms(form, wordlist, allforms)
        except ValueError as e:
            print(e)
#            error("form_errors", form, str(e))
            continue

        if not count % 1000 and progress:
            print(count, end = '\r', file=sys.stderr)

        if args.limit and count >= limit:
            break
        count += 1

        existing_forms = get_existing_forms(form, wordlist)

        missing_forms, unexpected_forms = fixer.compare_forms(declared_forms, existing_forms)

        missing_pos = {f[0] for f in missing_forms}
        unexpected_pos = {f[0] for f in unexpected_forms}
        wrong_forms = missing_pos & unexpected_pos

        if wrong_forms:
            for pos in wrong_forms:
                error("wrong_form", form, pos)

            unexpected_forms = [f for f in unexpected_forms if f[0] not in wrong_forms]
            missing_forms = [f for f in missing_forms if f[0] not in wrong_forms]

        for item in missing_forms:
            pos, formtype, lemma, lemma_genders = item

            if not FormFixer.can_handle_formtype(formtype):
                continue

            # TODO: for now skip multi word verbs
            if pos == "v" and " " in lemma:
                continue

            if pos == "n" and formtype == "m":
                error("should_be_lemma", form, item)
                continue

            words = list(wordlist.get_words(form, pos))
            if not words:
                matches = list(wordlist.get_words(form))
                if matches:
                    ety = {w.etymology for w in matches}
                    if len(ety) > 1:
                        error("missing_pos_multi_ety", form, item)
                    else:
                        error("missing_pos", form, item)
                else:
                    if form in allpages:
                         error("missing_entry", form, item)

# ignore redlinks
#                    else:
#                         error("missing_page", form, item)
                continue

#            if pos == "n" and formtype == "pl" and unexpected_forms:
#                masculines = get_masculines_from_fpl(words[0])
#                masculine_links = [m for m in masculines if (pos, "fpl", m) in unexpected_forms]
#                if masculine_links:
#                    for m in masculine_links:
#                        unexpected_forms.remove((pos, "fpl", m))
#                    print(f"{form}:{pos} links to masculine {masculine_links} instead of feminine $is_doublet")
#                    continue

            error("missing_sense", form, item)

        for item in unexpected_forms:
            pos, formtype, lemma = item
            words = list(wordlist.get_words(lemma, pos))
            if words:
                error("unexpected_form", form, item)
            else:
                error("missing_lemma", form, item)


    if args.save:
        base_url = "User:JeffDoozan/lists/es/forms"
        logger.save(base_url, WikiSaver, commit_message=args.save)
    else:
        logger.save("", FileSaver)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate list of missing forms")
    parser.add_argument("wordlist", help="wordlist")
    parser.add_argument("--allforms", required=True, help="all_forms file")
    parser.add_argument("--allpages", required=True, help="wiki.allpages")
    parser.add_argument("--save", help="wiktionary commit message")
    parser.add_argument("--limit", type=int, help="Limit processing to first N articles")
    parser.add_argument("--progress", help="Display progress", action='store_true')
    args = parser.parse_args()

    global SAVE_NOTE
    SAVE_NOTE = args.save

    main(args.wordlist, args.allforms, args.allpages, args.limit, args.progress)
