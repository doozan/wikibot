#!/usr/bin/python3

import argparse
from collections import defaultdict
from enwiktionary_wordlist.all_forms import AllForms
from autodooz.wikilog import WikiLogger, BaseHandler
from spanish_tools.freq import NgramPosProbability
from collections import namedtuple
import smart_open
import multiprocessing as mp

class WikiSaver(BaseHandler):

    def sort_items(self, items):
        return sorted(items, key=lambda x: (x.percent*-1, x.form))

    def page_name(self, page_sections, prev):
        return f"es/coordinate_terms"

    def page_header(self, base_path, page_name, page_sections, pages):
        return [f"Words that may be coordinate terms, still buggy"]

    def make_rows(self, entries):
        for x in entries:
            yield f"[[{x.form}]]", x.coord, x.form_count, x.coord_count, x.percent

    def make_section(self, base_path, page_name, section_entries, prev_section_entries, pages):
        head_rows = [["Form", "Coordinate", "Form count", "Coordinate count", "%"]]
        rows = self.make_rows(section_entries)
        return self.make_wiki_table(rows, extra_class="sortable", headers=head_rows)

class FileSaver(WikiSaver):

    def save_page(self, dest, page_text):
        dest = dest.lstrip("/").replace("/", "_")
        with open(dest, "w") as outfile:
            outfile.write(page_text)
            print("saved", dest)

    def save(self, *args, **nargs):
        super().save(*args, **nargs, commit_message=None)

class Logger(WikiLogger):
    _paramtype = namedtuple("params", [ "form", "coord", "form_count", "coord_count", "percent" ])

logger = Logger()

def log(form, coord, form_count, coord_count, percent):
    logger.add(form, coord, form_count, coord_count, percent)
    #print([form, coord, form_count, coord_count, percent])

_cache = {}
def get_form_lemma(ngprobs, allforms, form):
    global _cache

    cached = _cache.get(form)
    if cached:
        return cached

    form_pos = ngprobs.get_preferred_pos(form)

    if form in ["me", "te", "os", "nos", "les"]:
        lemma = "se"
    elif form in ["mi", "tu", "nuestro", "nuestra", "vuestro", "vuestra"]:
        lemma = "su"
    else:
        # TODO: handle m/f adj separately?
        lemmas = allforms.get_lemmas(form, form_pos)
        # ngprobs doesn't always have the correct pos (reharás detected as n instead of v)
        if not lemmas:
            lemmas = allforms.get_lemmas(form)
        lemma = lemmas[0].split("|")[1] if lemmas else form

        if " " in lemma:
            lemma = form

    _cache[form] = lemma

    return lemma

def get_coord_lemma(ngprobs, allforms, words):
    return " ".join(get_form_lemma(ngprobs, allforms, x) for x in words)

def get_lemma_count(ngprobs, lemma_forms, lemma, pos):
    #return sum(ngprobs.get_usage_count(form, pos) for form in lemma_forms.get((lemma, pos), []))
    return sum(ngprobs.get_usage_count(form) for form in lemma_forms.get((lemma, pos), []))

def find_coords(allforms, all_forms, ngprobs, alt_case, filename, ignore=None):
    # returns dict { (coord_lemma, form): count }
    coord_lemmas = defaultdict(int)
    seen  = set()
    with open(filename) as infile:
        for line in infile:
            line = line.strip()
            if not line:
                continue
            form, coord, form_count, coord_count = line.split("\t")
            form_count = int(form_count)
            coord_count = int(coord_count)

            words = coord.split(" ")
            if ignore and any(word in ignore for word in words):
                continue

            # ignore anything with a form not included in allforms
            if not all(word in all_forms for word in words):
                continue

            # Skip dupes
            if coord in seen:
                continue
            seen.add(coord)

            # Get link existing terms
            existing = coord if coord in all_forms else coord.lower() if coord.lower() in all_forms else alt_case.get(coord.lower())

            form_pos = ngprobs.get_preferred_pos(form)
            form_lemma = get_form_lemma(ngprobs, allforms, form)

            if existing:
                lemmas = allforms.get_lemmas(existing)
                if len(lemmas) > 1:
                    print("ambig lemmas", lemmas, existing)
                coord_lemma = lemmas[0].split("|")[1]
            else:
                coord_lemma = get_coord_lemma(ngprobs, allforms, words)

            #if coord_lemma == "mirar fijamente":
#            if coord_lemma == "muy poco":
#                print(line)
            coord_lemmas[(coord_lemma, form_lemma, form_pos)] += coord_count

    return coord_lemmas


def main():
    global args
    global ngprobs

    parser = argparse.ArgumentParser(description="Summarize ngram usage")
    parser.add_argument("--allforms", help="Exclude coordinate terms that have standalone entries")
    parser.add_argument("--min-count", help="Ignore forms with less than N uses", type=int)
    parser.add_argument("--min-percent", help="Ignore coordinate terms used less than N percent of the form's uses", type=int)
    parser.add_argument("--save", help="Save to wiktionary with specified commit message")
    parser.add_argument("--ignore2", help="Ignore coords containing the specified word (can be used more than once)", action='append')
    parser.add_argument("--ngprobs", help="Ngram probability data file")
    parser.add_argument("--coord2", help="File containing 2 word coordinate terms to check")
    parser.add_argument("--coord3", help="File containing 3 word coordinate terms to check")
    parser.add_argument("--coord4", help="File containing 4 word coordinate terms to check")
    args = parser.parse_args()

    allforms = AllForms.from_file(args.allforms)
    all_forms = set(allforms.all_forms)
    print("all_forms")
    lemma_forms = defaultdict(list)
    for form, pos, lemma in allforms.all:
        lemma_forms[(lemma, pos)].append(form)
    print("lemma_forms")

    alt_case = {form.lower():form for form in all_forms if form != form.lower()}

    ngprobs = NgramPosProbability(args.ngprobs)

    if False:
        coord = "reharás tu vida"
        words = coord.split(" ")
        print([coord, get_coord_lemma(ngprobs, allforms, words)])
        exit()

        form = "fijamente"
        form_pos = ngprobs.get_preferred_pos(form)
        form_lemma = get_form_lemma(ngprobs, allforms, form)
        count = get_lemma_count(ngprobs, lemma_forms, form_lemma, form_pos)
        print([form, form_pos, form_lemma, count])
        exit()


    all_coords = {}
    if args.coord2:
        all_coords |= find_coords(allforms, all_forms, ngprobs, alt_case, args.coord2, args.ignore2)
    if args.coord3:
        all_coords |= find_coords(allforms, all_forms, ngprobs, alt_case, args.coord3)
    if args.coord4:
        all_coords |= find_coords(allforms, all_forms, ngprobs, alt_case, args.coord4)

#    seen2 = set()
#    all_coords = {}
#    if args.coord3:
#        coord_lemmas = find_coords(allforms, all_forms, ngprobs, alt_case, args.coord3)
#        for k in coord_lemmas.keys():
#            coord_lemma, form, form_pos = k
#            words = coord_lemma.split(" ")
#            seen2.add(words[0:2])
#            seen2.add(words[1:3])
#        all_coords |= coord_lemmas
#
#    if args.coord2:
#        coord_lemmas = find_coords(allforms, all_forms, ngprobs, alt_case, args.coord2, args.ignore2)
#        for k,count in coord_lemmas.items():
#            coord_lemma, form, form_pos = k
#            if coord_lemma in seen2 and coord_lemma not in all_forms:
#                continue
#            all_coords[k] = count

    for k,coord_count in all_coords.items():
        coord_lemma, form_lemma, form_pos = k
        form_count = get_lemma_count(ngprobs, lemma_forms, form_lemma, form_pos)

        # Skip uncommon forms
        if form_count < args.min_count:
            continue

        # Min ratio
        percent = int(coord_count/form_count*100)
        if percent < args.min_percent:
            continue

        existing = coord_lemma if coord_lemma in all_forms else coord_lemma.lower() if coord_lemma.lower() in all_forms else None
        if existing:
            coord_lemma = f"[[{existing}]]"

        log(form_lemma, coord_lemma, form_count, coord_count, percent)

    if args.save:
        base_url = "User:JeffDoozan/lists"
        logger.save(base_url, WikiSaver, commit_message=args.save)
    else:
        dest = ""
        logger.save(dest, FileSaver)

if __name__ == "__main__":
    main()
