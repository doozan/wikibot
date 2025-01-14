#!/usr/bin/python3
#
# Copyright (c) 2021 Jeff Doozan
#
# This is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Find possible mismatches between a POS section header and the headline
"""

import multiprocessing
import pywikibot
import os
import re
import sys

from pywikibot import xmlreader
from autodooz.utils import iter_wxt
from autodooz.sections import ALL_POS, ALL_LANGS, ALL_LANG_IDS
from autodooz.wikilog import WikiLogger, BaseHandler
from autodooz.wikilog_language import WikiByLanguage, FileByLanguage
from collections import defaultdict

from collections import namedtuple

import enwiktionary_sectionparser as sectionparser


class Logger(WikiLogger):
    _paramtype = namedtuple("params", [ "error", "page", "language", "section", "line", "highlight" ])

logger = Logger()

def log(error, page, language, section, line, highlight=None):
    line = line.replace("\n", "")
    if error in ["error"]:
        print(error, page, language, section, line)

    if error == "lang-mismatch":
        error = f"Language id mismatch (id is not '{ALL_LANGS[language]}')"
    logger.add(error, page, language, section, line, highlight)

# pass if the string appears in the headword template name
POS_TEMPLATES = {
    "adjectival noun": ['-adj'],
    "adjective": ["-adj", "ar-nisba", "-apf"],
    "adverb": ["-adv"],
    "affix": ['-affix', 'en-suffix'],
    "article": ["-art"],
    "classifier": ["-classifier", "-cls"],
    "combining form": ["-combining form", "-cform"],
    "conjunction": ["-con"],
    "contraction": ["-cont"],
    "determiner": ["-det"],
    "diacritical mark": ["diacritic"],
    "interjection": ["-int"],
    "noun": ["-noun", "-plural noun", "-npf", "-verbal noun"],
    "number": ['-number', '-numeral'],
    "numeral": ["-num", "-card"],
    "ordinal number": ["-ordinal"],
    "participle": ["-part", "-pp", '-presp', "-past", "-active participle"],
    "particle": ["-part"],
    "postposition": ["-post"],
    "prefix": ["-pref"],
    "preposition": ["-prep"],
    "prepositional phrase": ["-pp", "-prep phrase", "-prepositional phrase"],
    "pronoun": ["-pron", "-prpr", "-ppron", "-personal pronoun"],
    "proper noun": ["-prop", "ro-name", "-noun", "-plural proper noun", "-prpn", "-proper noun", "-given name", "taxoninfl"],
    "proverb": ["-proverb", "-phrase", "-prov"],
    "romanization": ["-rom", "cmn-pinyin", "yue-jyut", "-tr"],
    "transliteration": ["-tr"],
    "suffix": ["-suff", "-ending", "suff="],
    "verb": ["-verb", "-pp", "-past", "-aux", "-inf", "en-phrasal verb", "-mutverb", "-present", "-part"],
}

# pass if the string appears anywhere in the headword line
POS_LINE_MATCHES = {
    "suffix": ["suff="],
}

# pass if the string appears in the headword template params
POS_HEADWORDS = {
    "adjective": ["adj"],
    "adverb": ["adv"],
    "affix": ["affix"],
    "article": ["art"],
    "conjunction": ["con"],
    "contraction": ["cont"],
    "determiner": ["det"],
    "interjection": ["int"],
    "noun": ["noun", "kok-pos|n", "singulative", "mk|verb form"],
    "number": ["number", "numeral"],
    "numeral": ["num"],
    "ordinal number": ["numeral"],
    "participle": ["part"],
    "particle": ["part"],
    "postposition": ["postp"],
    "prefix": ["pref"],
    "preposition": ["prep"],
    "pronoun": ["pron"],
    "proper noun": ["proper noun", "prop", "noun", "kok-pos|pn"],
    "romanization": ["pinyin", "romanization"],
    "suffix": ["suff"],
    "verb": ["verb", "past participle", "gerund", "present participle", "infinitive", "participle form", "passive participles", "kok-pos|v", "participle"],
}

# Templates that act like {{head}} and will contain keywords parameters to define the POS
HEAD_TEMPLATES = [
    "head",
    "head-lite",

    "az-head",
    "bcl-head",
    "grk-ita-head",
    "mh-head",
    "za-head",
    "tl-head",
    "ryu-head",
    "xug-head",

    "brx-pos",
    "ha-pos",
    "hi-pos",
    "ig-pos",
    "it-pos",
    "ja-pos",
    "kok-pos",
    "ko-pos",
    "nsk-pos",
    "nup-pos",
    "oj-pos",
    "pa-pos",
    "ru-pos",
    "pa-pos",
    "ru-pos",
    "ru-adj-alt-ё",
    "ru-noun-alt-ё",
    "ru-pos-alt-ё",
    "ru-verb-alt-ё",
    "ru-proper noun-alt-ё",
    "ryu-pos",
    "tt-pos",
    "ur-pos",
    "vi-pos",
    "yo-pos",
    "et-nom"

    "crk-cans",
    "crk-form",

]

# Words that can appear in {{head}} to make a valid headline for any POS
GLOBAL_HEADWORDS = [
    "misspelling",
    "nonstandard form",
    "superseded",
]

# The headword line template should be the first template immediately after a POS section header
# Alas, this is not always the case, so it's necessary to sort through some other templates
# to get to the actual headword template (list items must be lowercase)
IGNORE_TEMPLATES = {
    'anchor', 'attention', 'attn', 'audio', 'cardinalbox', 'cln', 'colorbox', 'commons',
    'commonscat', 'elements', 'enum', 'examples', 'fa-regional', 'ja-kanjitab', 'ko-hanja',
    'ko-hanjatab', 'ko-regional', 'ko-yin form of', 'ko-yang form of', 'ku-regional', 'mul-number',
    'multiple images', 'no entry', 'number box', 'ordinalbox', 'phrasebook', 'picdic', 'place', 'rfc',
    'rfd', 'rfdef', 'rfi', 'rfm', 'rfm', 'rfq', 'rfquote', 'rfref', 'rfv', 'root',
    'seecites', 'slim-wikipedia', 'stroke order', 'swp', 'taxlink', 'taxon',
    'tea room', 'vi-readings', 'wiki', 'wikibooks', 'wikipedia', 'wikiquote', 'wikisource',
    'wikispecies', 'wikiversity', 'wikiversity lecture', 'wikivoyage', 'wp', 'zodiac'
}

# Ignore lines that match [[LINK:*]]]
IGNORE_LINKS = [
    "file", "image", "category"
]

IGNORE_LANGS = [ "Translingual", "Esperanto", "Ido" ]
IGNORE_POS = [ "Abbreviations", "Han character", "Hanja", "Kanji", "Symbol", "Suffix" ]

# template language names that are permitted within non-matching language sections
LANGUAGE_ALTS = {
   "Mandarin": "Chinese",
   "Western Highland Chatino": "San Juan Quiahije Chatino"
}

def language_matches(lang_id, lang_name):
    if lang_id not in ALL_LANG_IDS:
        return True

    id_name = ALL_LANG_IDS[lang_id]
    if id_name == lang_name:
        return True

    if LANGUAGE_ALTS.get(id_name) == lang_name:
        return True

def get_template_name(text):
    res = re.match(r"\s*{{\s*(.*?)\s*[|}]", text)
    return res.group(1) if res else None

def is_pre_header(line):

    line = line.strip()

    # skip empty lines
    if not line:
        return True

    # skip single line comments
    if line.startswith("<!--") and line.endswith("-->"):
        return True

    # skip [[file:]] and other links
    if line.startswith("[[") and line[2:].split(":")[0].strip().lower() in IGNORE_LINKS:
        return True

    # Skip tables
    if line.startswith("{|"):
        return True

    if line.startswith("{{"):
        template = get_template_name(line)
        if template and template.lower() in IGNORE_TEMPLATES:
            return True

def is_header(line):

    template = get_template_name(line)
    if not template:
        return False

    if template in { "head", "head-lite", "diacritic", "taxoninfl" }:
        return True

    template = template.lower()
    # Anything that starts with "LANG-" is considered a valid header
    if "-" in template:
        splits = template.split("-")

        # Check for hyphenated language codes first
        if len(splits) > 2 and "-".join(splits[:2]) in ALL_LANG_IDS:
            return True

        if splits[0] in ALL_LANG_IDS:
            return True

        # "inc-pra" uses "pra-" as a prefix; "gmq-pro" uses "gmq-"
        if splits[0] in { "pra", "gmq" }:
            return True

    return False

def header_matches(line, section):
    pos_templates = POS_TEMPLATES.get(section.title.lower(), [section.title.lower()])
    pos_line_matches = POS_LINE_MATCHES.get(section.title.lower(), [])
    pos_headwords = POS_HEADWORDS.get(section.title.lower(), [section.title.lower()])

    # We only need to match the template name, the parameters are unimportant
    template = get_template_name(line).lower()

    # if this is a head-like template, check that a matching word appears on the headword line
    if template in HEAD_TEMPLATES:
        if any(pos for pos in pos_headwords if pos in line):
            return True
        if any(alt for alt in GLOBAL_HEADWORDS if alt in line):
            return True

    # Verify that template matches the allowed pos templates
    elif any(pos in template for pos in pos_templates):
        return True

    if any(match in line for match in pos_line_matches):
        return True



def get_template_lang_id(line):

    template = get_template_name(line).lower()

    # Search templates for language codes
    template_lang_id = None
    if "-" in template:
        splits = template.split("-")

        # Check for hyphenated language codes first
        if len(splits) > 2 and "-".join(splits[:2]) in ALL_LANG_IDS:
            return "-".join(splits[:2])

        # Fallback to unhyphenated language code
        if splits[0] in ALL_LANG_IDS:
            return splits[0]

    # The first paramater of HEAD-like template is the language code
    elif template in [ "head", "head-lite", "diacritic" ] :
        res = re.match(r"{{\s*" + template + r"\s*\|\s*(.*?)\s*\|", line)
        if res:
            return res.group(1)


def process(args):

    # Needed to unpack args until Pool.istarprocess exists
    page_text, title = args

    res = []

    entry = sectionparser.parse(page_text, title)
    if not entry:
        return res

    for lang in entry.ifilter_sections(recursive=False, matches=lambda x: x.title in ALL_LANGS and x.title not in IGNORE_LANGS):
        lang_id = ALL_LANGS.get(lang._topmost.title)

        for section in lang.ifilter_sections(matches=lambda x: x.title in ALL_POS and x.title not in IGNORE_POS):

            for line in section.content_wikilines:
                # Skip wiki stuff that might be in the way of a template
                line = line.lstrip(" *#:")

                # Skip lines that are allowed to appear before the headline
                if is_pre_header(line):
                    continue

                # Find the first template
                if line.startswith("{{"):
                    if not is_header(line):
                        res.append(("Missing headline", title, lang.title, section.title, line))
                        break

                    template_lang_id = get_template_lang_id(line)

                    # if template has a language prefix, check that it matches the parent language
                    if template_lang_id and not language_matches(template_lang_id, lang.title):
                        res.append(("lang-mismatch", title, lang.title, section.title, line))
                        break

                    if header_matches(line, section):
                        break

                    res.append(("Mismatched templates", title, lang.title, section.title, line))
                    break

                else: # line doesn't start with a template
                    res.append(("Unexpected text (probably missing headline)", title, lang.title, section.title, line))
                    break
    return res


def main():

    import argparse
    argparser = argparse.ArgumentParser(description="Detect possibly mismatched POS headers from enwiktionary dump.\nBy default, scans all languages.")
    argparser.add_argument("wxt", help="Wiktionary extract file")
    argparser.add_argument("--limit", type=int, help="Limit processing to first N articles")
    argparser.add_argument("--progress", help="Display progress", action='store_true')
    argparser.add_argument("--date", help="Date of the database dump (used to generate page messages)")
    argparser.add_argument("--save", help="Save to wiktionary with specified commit message")
    argparser.add_argument("-j", help="run N jobs in parallel (default = # CPUs - 1", type=int)
    args = argparser.parse_args()

    if not args.j:
        args.j = multiprocessing.cpu_count()-1

    iter_entries = iter_wxt(args.wxt, args.limit, args.progress)

    if args.j > 1:
        pool = multiprocessing.Pool(args.j)
        iter_items = pool.imap_unordered(process, iter_entries, 1000)
    else:
        iter_items = map(process, iter_entries)

    for results in iter_items:
        for log_values in results:
            log(*log_values)

    if args.save:
        base_url = "User:JeffDoozan/lists/mismatched pos"
        logger.save(base_url, WikiByLanguage, commit_message=args.save, page_limit=1000, data_date=args.date)
    else:
        dest = "mismatched"
        logger.save(dest, FileByLanguage, page_limit=1000, data_date=args.date)

#    base_url = "User:JeffDoozan/lists/mismatched pos" if args.save else "mismatched"
#    index_url = base_url if args.save else base_url + "/index"
#    logger.save(base_url, args.save, index_url=index_url)

if __name__ == "__main__":
    main()
