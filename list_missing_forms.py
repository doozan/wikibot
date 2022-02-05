#!/usr/bin/python3

import argparse
from collections import defaultdict
import csv
import io
import pywikibot
import re
import sys
from enwiktionary_wordlist.wordlist import Wordlist
from enwiktionary_wordlist.all_forms import AllForms
from form_fixer import FormFixer

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


errors = defaultdict(list)

error_header = {
    "form_errors": "Errors while processing forms",
    "should_be_lemma": "Forms that should probably be lemmas (manual review needed)",
#    "missing_page": "Redlinks",
    "missing_entry": "Missing Spanish section (bot job)",
    "missing_pos": "Missing POS entry (bot job)",
    "missing_pos_multi_ety": "Missing POS entry, entry has multiple etymologies (manual review needed)",
    "missing_sense": "Entry exists, but is missing a 'form of' declaration (manual review needed)",
    "wrong_form": "Entry has existing 'form of' that doesn't match the expected 'form of'",
    "unexpected_form": "Entry claims to be a 'form of' lemma but is not declared by the lemma",
    "missing_lemma": "Entry claims to be a 'form of' non-existente lemma",
}


#fixer.get_form_gloss(form_obj)

error_templates = {
#    "form_errors": "{item}",
    "should_be_lemma": "{pos} declared by [[{lemma}#Spanish|{lemma}]]:{pos}",
    "missing_page": " ({formtype} of [[{lemma}#Spanish|{lemma}]]:{pos})",
    "missing_entry": " ({formtype} of [[{lemma}#Spanish|{lemma}]]:{pos})",
    #"missing_pos": " does not have POS {pos} ({formtype} of {lemma}:{pos})",
    #"missing_pos_multiple_ety": " does not have POS {pos} ({formtype} of {lemma}:{pos})",
    #"missing_sense": "{pos} <nowiki>{fixer2.get_form_gloss(item)}</nowiki>",
    #"wrong_form": "{pos} ({formtype} of [[{lemma}#Spanish|{lemma}]])",
    "unexpected_form": "{pos} is not declared a {formtype} of [[{lemma}#Spanish|{lemma}]]:{pos}",
    "missing_lemma": "{pos} claims to be {formtype} of non-existent lemma [[{lemma}#Spanish|{lemma}]]:{pos}"
}

def error(error_id, form, item):
    global errors
    errors[error_id].append((form, item))
    #print(f"{form}: {error_id}:: {item}")
    #print(format_error_line(error_id, form, item))

def format_error_line(error_id, form, item):

    line = [ f": [[{form}#Spanish|{form}]]:" ]
    template = error_templates.get(error_id)
    if not template:
        if error_id in [ "missing_sense", "missing_pos_multi_ety", "missing_pos" ]:
            pos, formtype, lemma, *_ = item
            try:
                line.append(f"{pos} <nowiki>" + fixer.get_form_gloss(form, item) + "</nowiki>")
            except ValueError:
                line.append(f"{pos} ({formtype} of [[{lemma}#Spanish|{lemma}]])")
        else:
            line.append(item)

    else:
        pos, formtype, lemma, *_ = item
        line.append(template.format(**locals()))

    return "".join(line)

def format_error(error_id, items):

    if error_id in error_header:
        yield error_header[error_id]
        yield "\n"

    yield f"{len(items)} entries"
    yield "\n"

    for form, item in sorted(items):
        yield format_error_line(error_id, form, item)

def export_error(error_id, items):
    page = "User:JeffDoozan/es_forms/" + error_id
    #print(page)
    #print("\n".join(format_error(error_id, items)))
    save_page(page, "\n".join(format_error(error_id, items)))

def export_errors():
    for error, items in errors.items():
        export_error(error, items)

    # Update pages that no longer have any entries
    for error in error_header.keys()-errors.keys():
        export_error(error, [])

site = None
def save_page(page, page_text):

    page = "forms/x2/" + re.sub("[^\w]+", "_", page)
    with open(page, "w") as outfile:
        outfile.write(page_text)
    return

    global site
    if not site:
        site = pywikibot.Site()
    wiki_page = pywikibot.Page(site, page)
    if wiki_page.text.strip() == page_text.strip():
        print(f"{page} has no changes")
        return
    wiki_page.text = page_text
    print(f"saving {page}")
    wiki_page.save(SAVE_NOTE)


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

    export_errors()

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate list of missing forms")
    parser.add_argument("wordlist", help="wordlist")
    parser.add_argument("--allforms", required=True, help="all_forms file")
    parser.add_argument("--allpages", required=True, help="wiki.allpages")
    parser.add_argument("--summary", help="wiktionary commit message")
    parser.add_argument("--limit", type=int, help="Limit processing to first N articles")
    parser.add_argument("--progress", help="Display progress", action='store_true')
    args = parser.parse_args()

    global SAVE_NOTE
    SAVE_NOTE = args.summary

    main(args.wordlist, args.allforms, args.allpages, args.limit, args.progress)
