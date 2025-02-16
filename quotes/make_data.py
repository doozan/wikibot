#!/usr/bin/python3


# bzcat ../spanish_data/2023-05-01/all-en.enwikt.txt.bz2 | grep -P "{{(cite|quote)-*" > allquotes

# grep "^publisher:" allquotes_params | sort | uniq -c | sort -rn | awk '$1 > 4' | cut -d ":" -f 2- | cut -d" " -f2- > allquotes_publishers
# grep "^location:" allquotes_params | sort | uniq -c | sort -rn | awk '$1 > 2' | cut -d ":" -f 2- | cut -d" " -f2- > allquotes_locations
# grep "^author:" allquotes_params | sort | uniq -c | sort -rn | awk '$1 > 2' | cut -d ":" -f 2- | cut -d" " -f2- > allquotes_authors


import multiprocessing
import mwparserfromhell
import os
import re
import sys

from autodooz.fix_bare_quotes import QuoteFixer
from autodooz.quotes.name_labeler import NameLabeler
from autodooz.quotes.names import countable_pattern
from autodooz.quotes.parser import QuoteParser
from collections import defaultdict
from enwiktionary_parser.utils import nest_aware_split, nest_aware_resplit
from autodooz.quotes.names import disallowed_name_words, disallowed_journal_words, disallowed_publisher_words, disallowed_location_words
disallowed_words = {
    'j': disallowed_journal_words,
    'l': disallowed_location_words,
    'a': disallowed_name_words,
    'p': disallowed_publisher_words,
}


labeler = NameLabeler()

ALL_TYPES = {
        "p": ["publisher"],
        "a": ["author", "author2", "author3", "author4", "author5"],
        "l": ["location", "city"],
        "j": ["journal", "work", "magazine", "newspaper", "periodical"],
}

NESTS = (("[[", "]]"), ("{{", "}}"), ("[", "]"), ("(", ")"), ("<!--", "-->")) #, (start, stop))


def old_process(lines, all_count):
    data = "\n".join(lines)
    wikicode = mwparserfromhell.parse(data)

    for template in wikicode.filter_templates():
        name = template.name.strip()
        if not (name.startswith("quote") or name.startswith("cite")):
            continue

        if "-" not in name:
            continue

        _,_,source = name.partition("-")
        if source not in ["book", "journal"]:
            continue

        for short_param, param_names in ALL_TYPES.items():
            for param in param_names:
                if not template.has(param):
                    continue

                v = template.get(param).value.strip(" ")
                if not v:
                    continue

                all_count[short_param][v] += 1

    return all_count


def iter_wxt(datafile, limit=None, show_progress=False):

    from enwiktionary_wordlist.wikiextract import WikiExtractWithRev
    parser = WikiExtractWithRev.iter_articles_from_bz2(datafile)

    count = 0
    for entry in parser:

        if ":" in entry.title or "/" in entry.title:
            continue

        if not count % 1000 and show_progress:
            print(count, end = '\r', file=sys.stderr)

        if limit and count >= limit:
            break
        count += 1

        yield entry.text, entry.title

def extract_quote_templates(params):

    article, title = params

    if "{{quote-" not in article and "{{cite-" not in article:
        return

    wikicode = mwparserfromhell.parse(article)

    count = {} #defaultdict(lambda: defaultdict(int))

    for template in wikicode.filter_templates():
        name = template.name.strip()
        if not (name.startswith("quote") or name.startswith("cite")):
            continue

        if "-" not in name:
            continue

        _,_,source = name.partition("-")
        if source not in ["book", "journal"]:
            continue

        for short_param, param_names in ALL_TYPES.items():
            for param in param_names:
                if not template.has(param):
                    continue

                v = template.get(param).value.strip()
                if not v:
                    continue

                if short_param not in count:
                    count[short_param] = {}
                if v not in count[short_param]:
                    count[short_param][v] = 0

                count[short_param][v] += 1

    return count

def dump_params(filename, path, suffix):

    iter_entries = iter_wxt(filename, 0, True)
    pool = multiprocessing.Pool(multiprocessing.cpu_count()-1)
    iter_items = pool.imap_unordered(extract_quote_templates, iter_entries, 1000)

    all_count = defaultdict(lambda: defaultdict(int))

    for results in iter_items:
        if not results:
            continue
        for param, value_counts in results.items():
            for value, count in value_counts.items():
                all_count[param][value] += count

    for p, counts in all_count.items():
        name = ALL_TYPES[p][0]
        filename = os.path.join(path, f"{name}.{suffix}")
        with open(filename, "w") as outfile:
            for k, k_count in sorted(counts.items()):
                outfile.write(f"{k}\t{k_count}\n")


def load_params(all_params, path, suffix):
    for short_param, param_names in ALL_TYPES.items():
        name = param_names[0]

        try:
            filename = os.path.join(path, f"{name}.{suffix}")
            with open(filename) as infile:
                for line in infile:
                    line = line.strip()
                    if not line:
                        continue
                    v, _, count = line.rpartition("\t")
                    if not v:
                        v = count
                        count = "1"

                    all_params[short_param][v] += int(count)

        except (IOError, OSError):
            continue


def load_filters(path):

    all_filters = {}
    for short_param, param_names in ALL_TYPES.items():
        name = param_names[0]
        try:
            filename = os.path.join(path, f"{name}.filters")
            with open(filename) as infile:
                all_filters[short_param] =  {line.strip() for line in infile if line.strip()}
        except (IOError, OSError):
            all_filters[short_param] = {}
    return all_filters



def main():
    import argparse
    parser = argparse.ArgumentParser(description="datamine existing template paramaters")
    parser.add_argument("--wxt", help="Extract existing template paramaters from wiki extract")
    parser.add_argument("--datadir", required=True)
    parser.add_argument("--targets", required=True)
    args = parser.parse_args()

    if args.wxt:
        dump_params(args.wxt, args.datadir, "all")

    # Merge any ".new" files into ".manually.allowed" or ".filters" files
    merge_new(args.datadir)

    all_params = defaultdict(lambda: defaultdict(int))
    load_params(all_params, args.datadir, "all")
    all_params = clean_params(all_params)

    all_filters = load_filters(args.datadir)

    # Apply filters
    filtered = find_filtered(all_params, all_filters, ["p", "j"])
    if filtered:
        filename = "filtered"
        dump_filtered(filtered, args.datadir, "filtered")
        remove_filtered(all_params, filtered)
        print(f"dumped {filename} items, please review")

#    split_values(all_params)

    # Handle items that appear in multiple lists
    filename = os.path.join(args.datadir, "dupes")
    apply_resolutions(all_params, f"{filename}.resolved")
    conflicts = find_conflicts(all_params)
    if conflicts:
        dump_unresolved(conflicts, filename)
        apply_resolutions(all_params, filename)
        print(f"dumped conflicting items to '{filename}', please review and add to {filename}.resolved")
        exit()

    for k,counts in sorted(all_params.items()):
        print(k, len(counts))

    # Condense items
    # Detect any items in different groups that condense to the same form
    # Then, re-condense everything except thet over-condensed items
    condensed_params = condense_values(all_params)
    overcondensed = find_conflicts(condensed_params)
    filtered = find_filtered(condensed_params, all_filters, ["p", "j"])
    #filtered = find_filtered(condensed_params, all_filters)
    for k,vals in filtered.items():
        overcondensed[k] |= vals
    if overcondensed:
        condensed_params = condense_values(all_params, overcondensed)

    # Find anything that compresses to a filterable item and try condensing again
#    filtered = find_filtered(condensed_params, all_filters)
#    if filtered:
#        condensed_params = condense_values(condensed_params, filtered)

    # Run filter again, dump filtered
    # TODO: now that locations and authors have been split, this is where they should be filtered
    filtered = find_filtered(condensed_params, all_filters)
    if filtered:
        suffix = "condensed.filtered"
        dump_filtered(filtered, args.datadir, suffix)
        remove_filtered(condensed_params, filtered)
        print(f"dumped *.{suffix} items, please review")

    filename = os.path.join(args.datadir, "condensed.dupes")
    apply_resolutions(condensed_params, f"{filename}.resolved")
    conflicts = find_conflicts(condensed_params)
    if conflicts:
        dump_unresolved(conflicts, filename)
        apply_resolutions(condensed_params, filename)
        print(f"dumped excluded items to '{filename}', please review and add to {filename}.resolved")
        exit()


    print("----")
    for k,counts in sorted(condensed_params.items()):
        print(k, len(counts))

    # This is just a sanity-check to ensure that all
    # existing values match only one type of parameter
#    filename = "multi_matches.dupes"
#    unresolved = find_multi_matches(all_params, condensed_params)
#    if unresolved:
#        dump_unresolved(unresolved, filename)
#        #apply_resolutions(condensed_params, filename)
#        print(f"dumped excluded items to '{filename}', please review and add to {filename}.resolved")
#        exit()
#    else:
#        print("no multi-matches")

    load_params(condensed_params, args.datadir, "manually.allowed")
    # Clean the manually loaded params to convert to lowercase and apply any needed fixup
    condensed_params = clean_params(condensed_params)


    condensed_params = get_useful_params(condensed_params, args.targets)
    print("----")
    for k,counts in sorted(condensed_params.items()):
        print(k, len(counts))

    dump_allowed(condensed_params, args.datadir, "allowed")

    # later - find individual words that are highly correlated to publishers or journals and add
    # them to a disallowed_names list?

# Remove anything that doesn't match any of the text that needs to be fixes
def get_useful_params(all_params, filename):
    useful = {}
    with open(filename, 'r') as file:
        data = file.read().lower()

    x = 0
    valid = 0
    res = defaultdict(lambda: defaultdict(int))
    for p, counts in all_params.items():

        for text, count in counts.items():
            if text in data:
                res[p][text] += count
                valid += 1

            if not x % 10:
                print(f"{valid}/{x}", end = '\r', file=sys.stderr)
            x += 1

    return res

def dump_allowed(all_values, path, suffix):

    for p, counts in all_values.items():
        name = ALL_TYPES[p][0]
        filename = os.path.join(path, f"{name}.{suffix}")
        with open(filename, "w") as outfile:
            for v,count in sorted(counts.items()):
                print(v, file=outfile)

def remove_filtered(all_items, filtered):
    for v, sources in filtered.items():
        for p in sources:
            try:
                del all_items[p][v]
            except ValueError:
                pass

def dump_filtered(unresolved, path, suffix):

    filtered = defaultdict(set)

    for value, sources in sorted(unresolved.items()):
        for p in sources:
            filtered[p].add(value)

    for p,values in filtered.items():
        name = ALL_TYPES[p][0]
        filename = os.path.join(path, f"{name}.{suffix}")
        with open(filename, "w") as outfile:
            outfile.write("\n".join(sorted(values)))

def dump_unresolved(unresolved, filename):

    with open(filename, "w") as outfile:
        for value, sources in sorted(unresolved.items(), key=lambda x: (x[1], x[0])):
            src = "".join(sorted(sources))
            outfile.write(f"\t{src}\t{value}\n")

def apply_resolutions(all_values, filename):
    with open(filename) as infile:
        for line in infile:
            line = line.rstrip()
            if not line:
                continue

            try:
                allowed,locations,v = line.split("\t")
            except ValueError:
                print("failed", [line])
                exit()

            if len(allowed) > 1:
                raise ValueError("too many allowed items", line)

            for p in locations:
                if p == allowed:
                    continue
                try:
                    del all_values[p][v]
                except KeyError:
                    #print(f"{v} not found in {p}")
                    pass


def contains_disallowed_word(text, source):
    stripped = re.sub(r"[^\w\d\s]+", "", text)

    words = [w.lower() for w in nest_aware_split(" ", stripped, NESTS)]
    res = any(w in disallowed_words[source] for w in words)
    return res

def is_filtered(v, source, all_filters):

    if len(v) < 2:
        return True

    if len(v) < 3 and source != "l":
        return True

    # Skip things that look like dates
    if re.search(r"\d\d\d\d", v):
        return True

    if v.startswith("'") or v.startswith('"'):
        return True

    if "[http" in v:
        return True

    if v.count("[") != v.count("]"):
        return True

    if v.count("(") != v.count(")"):
        return True

    if v.startswith("&"):
        return True

    if v.isnumeric():
        return True

    if v in all_filters[source]:
        return True

#    if re.search(countable_pattern, v):
#        return True

    if source == "p":
        if re.search(r'("|printed|published|\b(by|for)\b)', v, re.IGNORECASE):
            return True

        if ":" in v and "w:" not in v:
            return True

    elif source == "a":

        if "university of " in v and "." not in v and "," not in v:
            return True

        # Filter valid names because they don't need to be part of the explict allow list
        return labeler.is_valid_name(v, skip_case_checks=True)
#
#        if re.search(r"(''|[<>])", v):
#            return True

#        if len(v)<5 or v.startswith("The ") or re.search(r'([<>"&]|\b(and|to|with)\b)', v):
#            return True

    elif source == "l":
        if ":" in v:
            return True

    #elif source == "j":
    # Don't filter :, to allow "Film review: special"
    #    if ":" in v:
    #        return True

    return contains_disallowed_word(v, source)

def find_filtered(all_values, all_filters, allowed_sources=[]):

    res = defaultdict(set)
    for p, counts in all_values.items():
        if allowed_sources and p not in allowed_sources:
            continue

        for v in counts:
            if is_filtered(v, p, all_filters):
                res[v].add(p)

    return res

def find_conflicts(all_values):

    unresolved = defaultdict(set)

    keys = sorted(all_values.keys())
    for idx, p in enumerate(keys):
        for p2 in keys[idx+1:]:
            overlap = all_values[p].keys() & all_values[p2].keys()
            if overlap:
                for v in overlap:
                    unresolved[v].add(p)
                    unresolved[v].add(p2)
    return unresolved


def get_multi_match(params):
    fixer, p, text = params

    # skip authors for now, could be useful later for cleaning up bad authors?
    if p == "a":
        return

    matches = []
    res = fixer.get_leading_publisher(text)
    if res and res[1].strip(". ") == "":
        matches.append("p")

    res = fixer.get_leading_journal(text)
    if res and res[1].strip(". ") == "":
        matches.append("j")

    res = fixer.get_leading_location(text)
    if res and res[1].strip(". ") == "":
        matches.append("l")

    if len(matches) > 1:
        return text, matches



#    if p != "p":
#        res = fixer.get_leading_publisher(text)
#        if res and res[1].strip(". ") == "":
#            return text, [p, "p"]
#
#    if p != "j" and fixer.get_leading_journal(text) is not None:
#        res = fixer.get_leading_publisher(text)
#        if res and res[1].strip(". ") == "":
#            return text, [p, "j"]


def find_multi_matches(all_values, condensed_values):

    fixer = QuoteFixer(all_publishers=condensed_values["p"], all_journals=condensed_values["j"], all_locations=condensed_values["l"])

    unresolved = defaultdict(set)

    cpus = multiprocessing.cpu_count()-1
    pool = multiprocessing.Pool(cpus)
    i=0
    for res in pool.imap_unordered(get_multi_match, [(fixer,p,v) for p,counts in all_values.items() for v in counts], 1000):
        i+=1
        if not i % 1000:
            print(i, end = '\r', file=sys.stderr)
        if not res:
            continue
        text, matches = res
        for p in matches:
            unresolved[text].add(p)

    return unresolved

def clean_params(all_params):
    res = defaultdict(lambda: defaultdict(int))
    for p, counts in all_params.items():
        for text, count in counts.items():
            # Don't convert the authors to lowercase yet, as some of the filtering is case-dependent
#            if p != "a":
            text = text.lower()
            QuoteParser.cleanup_text(text)

            if p == "p":
                text = QuoteParser.cleanup_publisher(text)

            if not text:
                continue
            res[p][text] += count
    return res


def split_location(text):

    split_iter = iter(re.split(QuoteParser.location_split_regex, text))
    for v in split_iter:
        sep = next(split_iter, None)
        if not v:
            continue
        yield v

# This is already done in condense()
def split_values(all_values):

    for p in ["l"]:
        splits = defaultdict(int)
        for text, count in all_values[p].items():
            for v in split_location(text):
                splits[v] += count

        all_values[p] = splits


def get_condensed_values(text, p):
    vals = condense(text, p)
    if not vals:
        return []

    if isinstance(vals, str):
        vals = [vals]

    return vals

def condense_values(all_values, excluded=[]):

#    disallowed = {}
#    for short_param, param_names in ALL_TYPES.items():
#        param_name = param_names[0]
#        filename = f"{disallowed_prefix}{param_name}"
#        try:
#            with open(filename) as infile:
#                disallowed[short_param] = {line.strip() for line in infile if line.strip()}
#        except (IOError, OSError):
#            disallowed[short_param] = {}

    res = defaultdict(lambda: defaultdict(int))
    for p, counts in all_values.items():
        for text, count in counts.items():

            for v in get_condensed_values(text, p):

#                if v.lower() in disallowed[p]:
#                    v = text
#                    if v.lower() in disallowed[p]:
#                        continue

#                if contains_disallowed_word(v, p):
#                    v = text
#                    if contains_disallowed_word(v, p):
#                        continue

                if v in excluded:
                    v = text
                res[p][v] += count

    return res



def old_load_items(self, filename, prefixes=None, postfixes=None, disallowed_items=[]):
        pre = self.make_pre_regex(prefixes) if prefixes else ""
        post = self.make_post_regex(postfixes) if postfixes else ""

        pattern = (f"^{pre}(?P<data>.*?){post}$")

        items = set()
        with open(filename) as infile:
            for line in infile:
                line = line.lower().strip()
                orig = line
                line = re.sub(pattern, r"\g<data>", line)
                line = line.strip(", ")

                # Fix for over-compressed items like "The University Press" being shortened to just "University"
                if line in disallowed_items or line.isnumeric() or len(line)<2:
                    if line == orig:
                        continue
                    line = orig

                # TODO: allow some like "Doubleday, Page"
                if line.endswith((", page", ", chapter")):
                    continue

                if len(line)<2:
                    continue

                if line in disallowed_items:
                    print("bad item - disallowed", orig)
                    continue

                if line.isnumeric():
                    print("bad item - numeric", orig)
                    continue

                if self.get_leading_labeled_number(line):
                    print("bad item", orig)
                    continue

                if not line:
                    continue

#                print("PUB", line)
#                exit()

#                if line.startswith("nyu"):
#                    print(line, orig)
#                    exit()
                items.add(line)

        return items


journal_regex = re.compile(rf"{QuoteParser.journal_prefix_regex}(?P<condensed>.*?){QuoteParser.journal_postfix_regex}$", re.IGNORECASE)
publisher_regex = re.compile(rf"{QuoteParser.publisher_prefix_regex}(?P<condensed>.*?){QuoteParser.publisher_postfix_regex}$", re.IGNORECASE)

def condense(v, p):

    v = NameLabeler.links_to_text(v)

    if p == "p": # publisher
        condensed = re.match(publisher_regex, v).group('condensed')
        if not condensed:
            return v
        return condensed

    elif p == "j": # journal
        condensed = re.match(journal_regex, v).group('condensed')
        if not condensed:
            return v
        return condensed

    elif p == "a": # author
        #res = []
#        for v, sep in labeler.split_names(v):
        if True:
            # Cleanup names extracted from template parameters

            v = v.lstrip(". )]").strip("-# ")
            if v.startswith("(") and v.endswith(")"):
                v = v.strip("()")

            if v.endswith(")") and "(" not in v:
                v = v.strip(")")

            if v.endswith("]") and "[" not in v:
                v = v.strip("]")

            if v.startswith("[") and not v.startswith("[[") and v.endswith("]"):
                v = v.strip("[]")

            pattern = r"""(?x)
                \b
                \s*
                et[.]?                 # et or et.
                \s+
                al(ii|ia|ios)?         # al, alii, alia, alios
                [. ]*
                $
            """
            v = re.sub(pattern, "", v)

            v = v.strip()
            if not v or v.isnumeric():
                return
                #continue

            if len(v) - v.count(".") - v.count(" ") < 3:
                return
                #continue

            return v
#            res.append(v)
#            continue
        #return res

    elif p == "l": # location
        return split_location(v)

    return v

def merge_new(path):

    new_items = defaultdict(set)

    files = [f for f in os.listdir(path) if f.endswith('.new')]
    for file in files:
        filename = os.path.join(path, file)

        print("processing", filename)
        with open(filename) as infile:
            for line in infile:
                if line.startswith("#"):
                   continue

                if line.startswith("!"):
                    suffix = "filters"
                    line = line[1:]
                else:
                    suffix = "manually.allowed"

                if not line[0] in "aplj":
                    continue

                p, val, *_ = line.split("\t")
                val = val.strip()
                if not val:
                    continue

                dest = { "p": "publisher", "a": "author", "j": "journal", "l": "location" }[p]

                target = os.path.join(path, f"{dest}.{suffix}")
                new_items[target].add(val)

    for target in new_items:
        try:
            with open(target) as infile:
                existing = { line.strip() for line in infile if line.strip() and not line.strip().startswith("#") }
        except FileNotFoundError:
            existing = set()

        items = new_items[target] - existing
        if not items:
            continue

        print("adding", len(items), "new lines to", target)

        with open(target, "a") as outfile:
            outfile.write("\n")
            outfile.write("\n".join(sorted(items)))

if __name__ == "__main__":
#    text = "{{w|Springer Science & Business Media}}"
#    print(condense(text, "p"))
#    exit()


    main()

