#!/usr/bin/python3

import argparse
import enwiktionary_sectionparser as sectionparser
import mwparserfromhell as mwparser
import multiprocessing
import os
import re
import sys
import json
import csv

from autodooz.fix_missing_taxlinks import MissingTaxlinkFixer
from autodooz.wikilog import WikiLogger, BaseHandler
from collections import defaultdict, namedtuple


TAXNAME_PAT = "[a-zA-Z0-9()×. -]+"

FIX_PATH = None
GLOBAL_DUMP = {}
class WikiSaver(BaseHandler):

    def sort_items(self, items):
        self.count = defaultdict(int)
        self.page_count = defaultdict(int)
        for item in items:
            self.count[item.error] += 1
            self.page_count[item.page] += 1

        # sort autofix sections first so they can be split
        return sorted(items, key=lambda x: ("autofix" not in x.error, self.count[x.error], self.page_count[x.page]*-1 if "autofix" in x.error else 0, x.page))

    def is_new_section(self, item, prev_item):
        return prev_item and prev_item.error != item.error

    def is_new_page(self, page_sections, section_entries):
        return page_sections and (page_sections[-1][-1].error.startswith("autofix") != section_entries[0].error.startswith("autofix"))

    def page_name(self, page_sections, prev):
        assert FIX_PATH

        if not page_sections or not page_sections[0]:
            return FIX_PATH + "/errors"

        if "autofix" in page_sections[0][0].error:
            return FIX_PATH + "/fixes"
        else:
            return FIX_PATH + "/errors"

    def format_entry(self, entry, prev_entry):

        if "autofix" in entry.error:
            if prev_entry and entry.page == prev_entry.page:
                return []
            count = self.page_count[entry.page]
            return [f": [[{entry.page}]] - {count} fix{'es' if count > 1 else ''}"]

        if entry.page is None:
            return [f": {entry.details}"]

        if len(entry.details) > 100:
            details = re.search(r".*\<BAD\>.*?\</BAD\>.*", entry.details).group(0)
        else:
            details = entry.details
        details = "<nowiki>" \
                + details.replace("<BAD>", '</nowiki><span style="color:red"><nowiki>') \
                .replace("</BAD>", '</nowiki></span><nowiki>') \
                .replace("<GOOD>", '</nowiki><span style="color:green"><nowiki>')\
                .replace("</GOOD>", '</nowiki></span><nowiki>') \
                + "</nowiki>"
        return [f"; [[{entry.page}]]:", details]

    def get_section_header(self, base_path, page_name, section_entries, prev_section_entries, pages):
        res = []
        if not section_entries:
            return res

        item = section_entries[0]
        count = len(section_entries)

        if prev_section_entries:
            res.append("")
        res.append(f"==={item.error}===")
        res.append(f"; {count} item{'s' if count>1 else ''}")
        return res


class FileSaver(WikiSaver):

    def save_page(self, dest, page_text):
        if not page_text:
            print(dest, "is empty, not saving", file=sys.stderr)
            return
        dest = dest.lstrip("/").replace("/", "_")
        with open(dest, "w") as outfile:
            outfile.write(page_text)
            print("saved", dest, file=sys.stderr)

    def save(self, *args, **nargs):
        super().save(*args, **nargs, commit_message=None)

class Logger(WikiLogger):
    _paramtype = namedtuple("params", [ "error", "page", "details" ])

logger = Logger()
def log(code, page, details):
    logger.add(code, page, details)

def iter_xml(datafile, limit=None, show_progress=False):
    from pywikibot import xmlreader
    dump = xmlreader.XmlDump(datafile)
    parser = dump.parse()

    count = 0
    for entry in parser:
        if not count % 1000 and show_progress:
            print(count, end = '\r', file=sys.stderr)

        if limit and count >= limit:
            break
        count += 1

        yield entry.text, entry.title


def iter_wxt(datafile, limit=None, show_progress=False):

    if not os.path.isfile(datafile):
        raise FileNotFoundError(f"Cannot open: {datafile}")

    from enwiktionary_wordlist.wikiextract import WikiExtractWithRev
    parser = WikiExtractWithRev.iter_articles_from_bz2(datafile)

    count = 0
    for entry in parser:

        if not count % 1000 and show_progress:
            print(count, end = '\r', file=sys.stderr)

        if limit and count >= limit:
            break
        count += 1

        yield entry.text, entry.title


fixer = None
def process(args):
    # Needed to unpack args until Pool.istarprocess exists
    return fixer.process(*args)

def process_taxons(args):

    entry_text, entry_title = args

    if ":" in entry_title or "/" in entry_title:
        return

    if "taxon" not in entry_text:
        return


    wikt = sectionparser.parse(entry_text, entry_title)
    if not wikt:
        return

    multi_l2 = any(wikt.ifilter_sections(recursive=False, matches=lambda x: x.title != "Translingual"))

    res = []
    for section in wikt.ifilter_sections(recursive=False):
        section_str = str(section)
        if "taxon" not in section_str:
            continue

        if re.search("\{\{\s*taxon\s*[|}]", section_str):
            if not section.path in ["English", "Translingual"]:
                print("unexpected taxon", entry_title, section.path, file=sys.stderr)

            flagged_path = section.path + "~" if multi_l2 else section.path
            res.append((entry_title, flagged_path, section_str))

    return res

def process_taxlinks(args):

    entry_text, entry_title = args

    # Taxon export is filename:section[~] where ~ indicates that it is NOT the only L2 section on the page
    entry_title, _, entry_section = entry_title.partition(":")
    is_manual_taxlink = entry_section.endswith("~")

    if "taxon" not in entry_text:
        return

    wikt = sectionparser.parse(entry_text, entry_title)
    if not wikt:
        return

    taxlinks = []
    log = []
    for section in wikt.ifilter_sections(recursive=False):
        section_str = str(section)
        if "taxon" not in section_str:
            continue

        if not section.path in ["English", "Translingual"]:
            log.append(("unexpected_taxon", entry_title, ""))
            continue

        wiki = mwparser.parse(section_str)
        # allow recursive, some templates don't match even though they're not actually inside other templates
        taxons = wiki.filter_templates(matches=lambda x: x.name.strip() == "taxon")
        if not taxons:
#            for t in wiki.ifilter_templates(recursive=False):
#                print(t, t.name.strip(), t.name.strip() == "taxon")

            log.append(("no_taxon", entry_title, ""))
            continue

        if len(taxons) > 1:
            desc = "<pre>" + "\n".join(map(str, taxons)) + "</pre>"
            log.append(("multi_taxon", entry_title, desc))
            continue

        for taxon in taxons:
            text = entry_title
            label = taxon.get(1).strip()
            has_i = taxon.has("i") and taxon.get("i").strip not in ["", "0"]

            taxlinks.append((entry_title, label, has_i, is_manual_taxlink, None))

            template_data = ["taxfmt", entry_title, label]
            if has_i:
                template_data.append("i=1")

            template = "{{" + "|".join(template_data) + "}}"
            if is_manual_taxlink:
                log.append(("unsafe_taxlink", entry_title, "<pre>" + template + "</pre>"))
            else:
                log.append(("autofix_taxlink", entry_title, "<pre>" + template + "</pre>"))

    return taxlinks, log


def process_missing_taxlinks(args):

    entry_text, entry_title = args

    entry_title, _, entry_section = entry_title.partition(":")
    wiki = mwparser.parse(entry_text)

    taxlinks = []
    for t in wiki.ifilter_templates(recursive=True, matches=lambda x: str(x.name).strip() == "taxlink"):
        taxon = str(t.get(1).value).strip()
        rank = str(t.get(2).value).strip()
        if not taxon or not rank:
            continue
        has_i = t.has("i") and str(t.get("i").value) not in ["", "0"]
        is_manual_taxlink = " " not in taxon

        taxlink = (taxon, rank, has_i, is_manual_taxlink, entry_title)
        taxlinks.append(taxlink)

    return taxlinks, []

def process_wanted_taxons(args):

    entry_text, entry_title = args

    if ":" in entry_title or "/" in entry_title:
        return

    wikt = sectionparser.parse(entry_text, entry_title)
    if not wikt:
        return

    names = set()
    for section in wikt.ifilter_sections(recursive=False, matches=lambda x: x.title not in ["Latin", "Germani"]):
        clean_text = re.sub("<!--.*-->", "", str(section))

        TAXNAME = "[A-Z]" + TAXNAME_PAT
        for m in re.finditer(
                r"\[\s*([Ff]ile|[Ii]mage)\s*:[^|\]]+[|][^|\]]+[|](?P<image>[^\n|\]]+)" \
                + r"|(?<!')('''''|'')(?P<ital>" + TAXNAME + r")('''''|'')(?!')" \
                + r"|\[\[\s*(?P<redlink>" + TAXNAME + r")[|\]]"
                , clean_text):
            for src in ["image", "redlink", "ital"]:
                if not m.group(src):
                    continue

                source = src
                name = m.group(src).strip()

#                if src == "ital":
#                    print(src, name, file=sys.stderr)

                if src == "image":
                    mm = re.search(r"''(" + TAXNAME + r")''", name)
                    name = mm.group(1).strip() if mm else None

            if not name:
                continue

            if re.match(r"^(A|An|I|In|The|To|Use|Used|You|On)[ ]", name):
                continue

            if name not in GLOBAL_DUMP["taxons"] and name not in GLOBAL_DUMP["bluelinks"]:
                names.add((source, name))

    return names, []


all_wanted_taxons = set()
def store_wanted_taxons(args):
    global all_wanted_taxons
    names, logitems = args
    all_wanted_taxons |= names


def print_wanted_taxons():
    prev_src = None
    for src, item in sorted(all_wanted_taxons):
        if src != prev_src:
            if prev_src:
                print("</pre>")
            print(f"==={src}===")
            print("<pre>")
            prev_src = src
        print(item)
    print("</pre>")

def log_results(results):
    for log_values in results:
        log(*log_values)

def print_entries(results):
    prev_path = None
    for entry_title, section_path, data in results:
        path = f"{entry_title}:{section_path}"
        if path != prev_path:
            print(f"_____{path}_____")
            prev_path = path
        print(data)

all_taxlinks = []
def store_taxlinks(args):

    seen = set()
    dups = {}
    bad = {}

    taxlinks, logitems = args
    log_results(logitems)

    def make_template(name, rank, has_i):
        template = "{{taxlink|" + name + "|" + rank
        if has_i:
            template += "|i=1"
        template += "}}"
        return template

    unique_taxlinks = {(name, rank, has_i) for name, rank, has_i, no_auto, page in taxlinks}

    for name, rank, has_i in unique_taxlinks:
        if name in seen:
            dups[name] = []
        else:
            seen.add(name)
            stripped = name.replace('\xa0', "").replace('\u200b', "").replace('\u200e', "")
            stripped = re.sub(TAXNAME_PAT, "", stripped)
            if stripped or name.startswith("×"):
#                print(name, [stripped])
                bad[make_template(name, rank, has_i)] = []

    for name, rank, has_i, no_auto, page in taxlinks:
        if name in dups:
            dups[name].append((rank, has_i, page))
        template = make_template(name, rank, has_i)
        if template in bad:
            bad[template].append(page)

    for name, data in dups.items():
        templates = []
        pages = []
        for rank, has_i, page in data:
            if page not in pages:
                pages.append(page)
            template = make_template(name, rank, has_i)
            if template not in templates:
                templates.append(template)

        log("taxlink_conflicts", None, "; ".join(templates) + " on [[" + "]]; [[".join(pages) + "]]" )

    for template, pages in bad.items():
        log("bad_name", None, template + " on [[" + "]]; [[".join(pages) + "]]")

    global all_taxlinks
    all_taxlinks += [t for t in taxlinks if t[0] not in dups and t[0] not in bad]

def print_taxlinks():
    unique_taxlinks = {(name, rank, has_i, no_auto) for name, rank, has_i, no_auto, page in all_taxlinks}
    for name, rank, has_i, no_auto in sorted(unique_taxlinks):
        assert "\n" not in name and "\t" not in name

        has_i = "1" if has_i else ""
        no_auto = "1" if no_auto else ""

        values = [name, rank, has_i, no_auto]
        print("\t".join(values))

def main():
    global fixer
    parser = argparse.ArgumentParser(description="Find errors in sense lists")
    parser.add_argument("--xml", help="XML file to load")
    parser.add_argument("--wxt", help="Wiktionary extract file to load")
    parser.add_argument("--limit", type=int, help="Limit processing to first N articles")
    parser.add_argument("--progress", help="Display progress", action='store_true')
    parser.add_argument("--print-taxons", help="Print all entries with taxon templates to stdout", action='store_true')
    parser.add_argument("--print-taxlinks", help="Print all valid taxlinks to stdout", action='store_true')
    parser.add_argument("--bluelinks", help="all.pages file")
    parser.add_argument("--print-missing-taxlinks", help="Print all missing taxlinks to stdout", action='store_true')
    parser.add_argument("--taxons", help="path to file generated by --print-taxlinks", action='append')
    parser.add_argument("--missing-taxons", help="path to file generated by --print-missing-taxlinks")
    parser.add_argument("--print-wanted-taxons", help="path to file generated by --print-missing-taxlinks", action='store_true')
    parser.add_argument("--save", help="Save to wiktionary with specified commit message")
    parser.add_argument("-j", help="run N jobs in parallel (default = # CPUs - 1", type=int)
    args = parser.parse_args()


    if not args.j:
        args.j = multiprocessing.cpu_count()-1

    if (not args.xml and not args.wxt) or (args.xml and args.wxt):
        print("use either --xml or --wxt")
        exit(1)

    if args.wxt:
        iter_entries = iter_wxt(args.wxt, args.limit, args.progress)
    else:
        iter_entries = iter_xml(args.xml, args.limit, args.progress)

    process_function = None
    post_process_function = None

    global FIX_PATH
    if args.print_taxons:
        FIX_PATH = "taxon-dump"
        process_function = process_taxons
        post_process_function = print_entries
        post_post_process_function = lambda: False

    elif args.print_taxlinks:
        FIX_PATH = "taxons"
        process_function = process_taxlinks
        post_process_function = store_taxlinks
        post_post_process_function = print_taxlinks

    elif args.print_missing_taxlinks:
        FIX_PATH = "missing_taxons"
        process_function = process_missing_taxlinks
        post_process_function = store_taxlinks
        post_post_process_function = print_taxlinks

    elif args.print_wanted_taxons:
        with open(args.bluelinks) as infile:
            GLOBAL_DUMP["bluelinks"] = {l.strip() for l in infile}

        GLOBAL_DUMP["taxons"] = set()
        for filename in args.taxons:
            with open(filename) as infile:
                GLOBAL_DUMP["taxons"] |= {x[0] for x in csv.reader(infile, delimiter="\t")}

        print(len(GLOBAL_DUMP["taxons"]), "known taxons...searching for additional signs of life")

        FIX_PATH = "wanted_taxons"
        process_function = process_wanted_taxons
        post_process_function = store_wanted_taxons
        post_post_process_function = print_wanted_taxons



    elif args.missing_taxons:
        fixer = MissingTaxlinkFixer("taxlink", args.missing_taxons)
        FIX_PATH = "missing_taxlinks"
        process_function = process
        post_process_function = log_results
        post_post_process_function = lambda: False

    elif args.taxons:
        fixer = MissingTaxlinkFixer("taxfmt", args.taxons[0])
        FIX_PATH = "missing_taxfmt"
        process_function = process
        post_process_function = log_results
        post_post_process_function = lambda: False

    else:
        print("no command specified")
        exit(1)



    test_iter_entries = [("""
{{also|man of war}}
==English==
{{was wotd|2022|October|7}}

===Etymology===
{{multiple images
|direction = vertical
|image1 = The Royal Sovereign a first rate man of war, carrying 100 Guns and 750 Men (PAG6958).jpg
|caption1 = Thomas Bastion and I. Cole, ''The'' Royal Sovereign'', a First Rate Man of War, Carrying 100 Guns and 750 Men'' (1715). According to the {{w|National Maritime Museum}} in [[Greenwich]], [[London]], U.K., this is a [[hand#Noun|hand]]-[[coloured#Adjective|coloured]] [[print#Noun|print]] [[depict]]ing the H.M.S. ''Royal George'', a man-of-war ''(sense 2)'' originally called the [[w:HMS Royal Charles (1673)|H.M.S. ''Royal Charles'']] when [[build#Verb|built]] in 1673.
|image3 = Magnificent Frigatebird (Fregata magnificens) female - Isla Contoy QR 2020.jpg
|caption3 = A [[magnificent frigatebird]] (''[[Fregata magnificens]]''), also called a man-of-war ''(sense 3.1.1)'', on {{w|Isla Contoy}}, [[Quintana Roo]], [[Mexico]].
|image4 = Arctic skua (Stercorarius parasiticus) on an ice floe, Svalbard.jpg
|caption4 = An [[Arctic skua]] (''[[Stercorarius parasiticus]]'') in [[Svalbard]], known as a man-of-war in the [[United States]] ''(sense 3.1.2)''.
|image5 = Portuguese Man-O-War (Physalia physalis).jpg
|caption5 = A man-of-war ''(sense 3.2)'', known more fully as a [[Portuguese man-of-war]] (''[[Physalia physalis]]'').
}}

From Late {{inh|en|enm|man of wer}}, {{m|enm|man of werre|t=fighting man, soldier}}.<ref>{{R:MED Online|subentry=man of [wer(re]|entry=wer(re|pos=n|id=MED52312}}</ref> It has been suggested that sense 2 (“powerful armed naval vessel”) derives from the fact that such vessels were manned by men-of-war (“soldiers”; sense 1).<ref>See, for example, {{cite-book|author=Eliezer Edwards|entry=Man-of-war|title=Words, Facts, and Phrases: A Dictionary of Curious, Quaint, & Out-of-the-way Matters|location=London|publisher={{w|Chatto & Windus}},{{nb...|Piccadilly}}|year=1882|page=351|pageurl=https://books.google.com/books?id=7DcCAAAAQAAJ&pg=PA351|oclc=174082463}}.</ref>
""", "test")]

    #iter_entries = test_iter_entries

    if args.j > 1:
        pool = multiprocessing.Pool(args.j)
        iter_items = pool.imap_unordered(process_function, iter_entries, 100)
    else:
        iter_items = map(process_function, iter_entries)

    for res in iter_items:
        if not res:
            continue
        post_process_function(res)

    post_post_process_function()

    if args.save:
        base_url = f"User:JeffDoozan/lists"
        logger.save(base_url, WikiSaver, commit_message=args.save)
    else:
        dest = ""
        logger.save(dest, FileSaver)

if __name__ == "__main__":
    main()
