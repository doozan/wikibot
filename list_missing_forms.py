#!/usr/bin/python3

import argparse
from collections import defaultdict, namedtuple
import csv
import io
import gc
import pywikibot
import re
import sys
from enwiktionary_wordlist.wordlist import Wordlist
from enwiktionary_wordlist.all_forms import AllForms
from enwiktionary_wordlist.wikiextract import WikiExtractWithRev
from form_fixer import FormFixer, FixRunner, ExistingForm
from autodooz.wikilog import WikiLogger, BaseHandler

class Logger(WikiLogger):
    _paramtype = namedtuple("params", [ "error", "form", "item", "text" ])

class WikiSaver(BaseHandler):
    error_header = {
        "form_errors": "Errors while processing forms",
        "should_be_lemma": "Forms that should probably be lemmas",
#        "missing_page": "Redlinks",
        "missing_entry": "Missing Spanish section",
        "missing_pos": "Missing POS entry",
        #"missing_pos_multi_ety": "Missing POS entry, entry has multiple etymologies (manual review needed)",
        "missing_sense": "Entry exists, but is missing a 'form of' declaration",
        #"wrong_form": "Entry has existing 'form of' that doesn't match the expected 'form of'",
        "unexpected_form": "Entry claims to be a 'form of' lemma but is not declared by the lemma",
        "missing_lemma": "Entry claims to be a 'form of' non-existent lemma",
    }

    def save_page(self, page, page_text):
        super().save_page(page, page_text)

    def sort_items(self, items):
        return sorted(filter_items(items), key=lambda x:(x.error,  x.form))

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
        error = page_name[:-len("_autofix")] if page_name.endswith("_autofix") else page_name
        header = self.error_header.get(page_name, page_name)
        return [f"{header}: {count} item{'' if count==1 else 's'}"]

    def format_entry(self, entry, prev_entry):

        autofix = entry.error.endswith("_autofix")
        error = entry.error[:-len("_autofix")] if autofix else entry.error
        f = entry.item

        lemmalink = f.lemma if autofix else f"[[{f.lemma}#Spanish|{f.lemma}]]"

        #if entry.error in [ "missing_sense", "missing_pos_multi_ety", "missing_pos" ]:
        if error == "missing_sense":
            try:
                data = f"{f.pos} ({f.formtype}) <nowiki>" + fixer.get_form_gloss(entry.item) + "</nowiki>"
            except ValueError:
                data = f"{f.pos} ({f.formtype} of {lemmalink})"

        elif error == "should_be_lemma":
            data = f"{f.pos} declared by {lemmalink}:{f.pos}"

        elif error == "missing_page":
            data = f" ({f.formtype} of {lemmalink}:{f.pos})"

        elif error == "missing_entry":
            data = f" ({f.formtype} of {lemmalink}:{f.pos})"

        elif error in ["unexpected_form"]:
            data = f"{f.pos} is not declared a {f.formtype} of {lemmalink}:{f.pos}"

#        elif error in ["wrong_form"]:
#            pos = entry.item
#            data = f"{entry} is not declared by {lemmalink}"

        # handled in make_section
        #elif error == "missing_lemma":

        elif error == "missing_pos":
            data = f"{f.pos}\n<pre>{entry.text}</pre>"

        else:
            #"missing_pos": " does not have POS {pos} ({formtype} of {lemma}:{pos})",
            #"missing_sense": "{pos} <nowiki>{fixer2.get_form_gloss(item)}</nowiki>",
            #"wrong_form": "{pos} ({formtype} of [[{lemma}#Spanish|{lemma}]])",
            data = entry.item

        return [f": [[{entry.form}#Spanish|{entry.form}]]:" + data]

    # override for missing lemma, which needs to be re-sorted by lemma and not by form
    def make_section(self, base_path, page_name, section_entries, prev_section_entries, pages):

        if not section_entries or section_entries[0].error != "missing_lemma":
            return super().make_section(base_path, page_name, section_entries, prev_section_entries, pages)

        res = self.get_section_header(base_path, page_name, section_entries, prev_section_entries, pages)

        prev_entry = None
        for entry in sorted(section_entries, key=lambda x: (x.item.pos, x.item.lemma)):
            if not prev_entry or prev_entry.item.pos != entry.item.pos:
                res.append(f"==={entry.item.pos}===")
            if not prev_entry or prev_entry.item.lemma != entry.item.lemma:
                res.append(f"; [[{entry.item.lemma}#Spanish|{entry.item.lemma}]]:")
            res.append(f"[[{entry.item.form}#Spanish|{entry.item.form}]] ({entry.item.formtype}),")
            prev_entry = entry
        return res

class FileSaver(WikiSaver):

    def save_page(self, dest, page_text):
        dest = dest.lstrip("/").replace("/", "_")
        with open(dest, "w") as outfile:
            outfile.write(page_text)
            print("saved", dest)

    def save(self, *args, **nargs):
        super().save(*args, **nargs, commit_message=None)

logger = Logger()

def error(error_id, form, item, text=None):
    logger.add(error_id, form, item, text)


fixer = None
fixrunner = None

def get_existing_forms(form, wordlist):
    return get_word_forms(wordlist.get_iwords(form))

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
                    existing_forms.add(ExistingForm(word.word, word.pos, gender, mate_lemma))

        for sense in word.senses:
            # Limit to the formtypes we can handle, forms like "misspelling of" aren't our concern
            if sense.formtype and FormFixer.can_handle_formtype(sense.formtype):
                existing_forms.add(ExistingForm(word.word, word.pos, sense.formtype, sense.lemma))

    return existing_forms

def get_masculines_from_fpl(word):
    return [lemma for lemma, forms in word.form_of.items() if "fpl" in forms]


ARTICLE_FILE = None
#def filter_fixes(extract, errors):
def filter_items(errors):

    # eww
    if not ARTICLE_FILE:
        raise ValueError("global variable ARTICLE_FILE has not been initialized")

    # NOTE: if an error occurs in a page not included in the language_file,
    # it will be lost in this filter, which ONLY returns items that do exist
    # In most cases this won't matter as the problem should only have been
    # found in a search of pages in the language file, but still, just a heads-up

    search_titles = defaultdict(list)
    for e in errors:
        search_titles[e.form].append(e)

    for article in WikiExtractWithRev.iter_articles_from_bz2(ARTICLE_FILE):
        title = article.title
        entry = article.text
        if title not in search_titles:
            continue

        page_errors = search_titles[title]
        for error in page_errors:
            try:
                autofix = can_autofix(entry, title, error)
            except ValueError:
                autofix = False

            yield error._replace(error=error.error+"_autofix") if autofix else error

def can_autofix(page_text, title, error):

#    if error.error == "wrong_form":
#        pos = error.item
#        if fixrunner._replace_pos(page_text, title, pos) != page_text:
#            return True
#        if fixrunner._remove_forms(page_text, title, pos) != page_text \
#                and fixrunner._add_forms(page_text, title, pos) != page_text:
#            return True

    if error.error == "unexpected_form":
        if not hasattr(error.item, "pos"):
            raise ValueError("tuple", error, error.item, title)
        if fixrunner.replace_pos(page_text, title, error.item.pos) != page_text:
            return True
#        if fixrunner._remove_forms(page_text, title, error.item.pos) != page_text:
#            return True

    elif error.error in ["missing_entry", "missing_pos"]:
        if fixrunner.add_forms(page_text, title, error.item.pos) != page_text:
            return True

    elif error.error == "missing_sense":
        if fixrunner.replace_pos(page_text, title, error.item.pos) != page_text:
            return True
        if fixrunner.add_forms(page_text, title, error.item.pos) != page_text:
            return True


def main():

    global fixer
    global fixrunner

    import argparse

    parser = argparse.ArgumentParser(description="Generate list of missing forms")
    parser.add_argument("wordlist", help="wordlist")
    parser.add_argument("--allforms", required=True, help="all_forms file")
    parser.add_argument("--allpages", required=True, help="wiki.allpages")
    parser.add_argument("--articles", required=True, help="Language extract with raw articles, used for checking autofixes")
    parser.add_argument("--save", help="wiktionary commit message")
    parser.add_argument("--limit", type=int, help="Limit processing to first N articles")
    parser.add_argument("--progress", help="Display progress", action='store_true')
    args = parser.parse_args()

    global ARTICLE_FILE
    ARTICLE_FILE = args.articles

    wordlist = Wordlist.from_file(args.wordlist)

    allforms = AllForms.from_file(args.allforms)
    fixer = FormFixer(wordlist)
    fixrunner = FixRunner("es", wordlist, allforms)

    with open(args.allpages) as infile:
        # Loading the entire contents of allpages takes 600M
        # To conserve memory, temporarily load allforms into a set
        # and then create a set of entries in allpages that are also in allforms

        allforms_set = set(allforms.all_forms)
        allpages = { x.strip() for x in infile if x in allforms_set }
        del allforms_set

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
            print("ERROR", e)
            #error("form_errors", form, str(e))
            continue

        if not count % 1000 and args.progress:
            print(count, end = '\r', file=sys.stderr)

        if args.limit and count >= args.limit:
            break
        count += 1

        existing_forms = get_existing_forms(form, wordlist)

        missing_forms, unexpected_forms = fixer.compare_forms(declared_forms, existing_forms)

        missing_pos = []
        for item in missing_forms:

            if item.form != form:
                raise ValueError(form, item)

            if not FormFixer.can_handle_formtype(item.formtype):
                continue

            # TODO: for now skip multi word verbs
            if item.pos == "v" and " " in item.lemma:
                continue

            if item.pos == "n" and item.formtype == "m":
                error("should_be_lemma", item.form, item)
                continue

            words = list(wordlist.get_words(item.form, item.pos))
            if not words:
                matches = list(wordlist.get_words(item.form))
                if matches:
                    if item.pos in missing_pos:
                        continue
                    ety = {w.etymology for w in matches}
                    level = 4 if len(ety) > 1 else 3
#                    error("missing_pos_multi_ety", form, item)
                    items = [i for i in missing_forms if i.pos == item.pos]

                    if fixer.can_handle(item):
                        pos_text = str(fixer.full_pos(level, items))
                    else:
                        pos_text = ""
                    error("missing_pos", form, item, pos_text)
                    missing_pos.append(item.pos)
                else:
                    if item.form in allpages:
                         error("missing_entry", form, item)

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

        for item in sorted(unexpected_forms):
            words = list(wordlist.get_words(item.lemma, item.pos))
            if words:
                error("unexpected_form", form, item)
            else:
                error("missing_lemma", form, item)

    if args.save:
        base_url = "User:JeffDoozan/lists/es/forms"
        logger.save(base_url, WikiSaver, commit_message=args.save)
    else:
        logger.save("forms", FileSaver)

if __name__ == "__main__":
    main()
