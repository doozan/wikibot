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

import os
import re
import sys
import pywikibot
from pywikibot import xmlreader
from autodooz.sort_sections import ALL_POS
from autodooz.wikilog import WikiLogger, BaseHandler
from autodooz.wikilog_language import WikiByLanguage, FileByLanguage
from collections import defaultdict
from enwiktionary_parser.languages.all_ids import languages as lang_ids
ALL_LANGS = {v:k for k,v in lang_ids.items()}

from collections import namedtuple

class Logger(WikiLogger):
    _paramtype = namedtuple("params", [ "error", "page", "language", "section", "line", "highlight" ])

logger = Logger()

def log(error, page, language, section, line, highlight=None):
    if error in ["error"]:
        print(error, page, language, section, line)

    if error == "lang-mismatch":
        error = f"Language id mismatch (id is not '{ALL_LANGS[language]}')"
    logger.add(error, page, language, section, line, highlight)

# pass if the string appears in thea headword template name
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
    "proper noun": ["-prop", "ro-name", "-noun", "-plural proper noun", "-prpn"],
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

# Templates that act like {{head}} and will contain keywords paramaters to define the POS
HEAD_TEMPLATES = [
    "head",
    "head-lite",
    "az-head",
    "grk-ita-head",
    "mh-head",
    "za-head",

    "brx-pos",
    "ha-pos",
    "hi-pos",
    "ig-pos",
    "ja-pos",
    "kok-pos",
    "ko-pos",
    "oj-pos",
    "pa-pos",
    "ru-pos",
    "ru-pos-alt-ё",
    "ryu-pos",
    "tt-pos",
    "ur-pos",
    "vi-pos",
    "yo-pos",
    "et-nom"
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
IGNORE_TEMPLATES = [
    'anchor', 'attention', 'attn', 'audio', 'cardinalbox', 'cln', 'colorbox', 'commons',
    'commonscat', 'elements', 'enum', 'examples', 'fa-regional', 'ja-kanjitab', 'ko-hanja',
    'ko-hanjatab', 'ko-regional', 'ko-yin form of', 'ko-yang form of', 'ku-regional', 'mul-number',
    'multiple images', 'no entry', 'number box', 'ordinalbox', 'phrasebook', 'picdic', 'place', 'rfc',
    'rfd', 'rfdef', 'rfi', 'rfm', 'rfm', 'rfq', 'rfquote', 'rfref', 'rfv', 'root',
    'seecites', 'slim-wikipedia', 'stroke order', 'swp', 'taxlink', 'taxon', 'taxoninfl',
    'tea room', 'vi-readings', 'wiki', 'wikibooks', 'wikipedia', 'wikiquote', 'wikisource',
    'wikispecies', 'wikiversity', 'wikiversity lecture', 'wikivoyage', 'wp', 'zodiac'
]

# Ignore lines that match [[LINK:*]]]
IGNORE_LINKS = [
    "file", "image", "category"
]

# If the first template is in this list, it's a sign that the entry is missing a template
NOT_HEADLINES = [
    "lb", "i", "q", "l", "l/ja", "der-top", "ux", "alternative form of"
]

# Ignore LANGUAGE, POS (accepts * as a wildcard for either LANGUAGE or POS)
IGNORE_SECTIONS = [
        ("Translingual", "*"),
        ("Esperanto", "*"),
        ("Ido", "*"),
        ("*", "Abbreviations"),
        ("*", "Han character"),
        ("*", "Hanja"),
        ("*", "Kanji"),
        ("*", "Symbol")
]

def ignore_lang(lang):
    return lang not in ALL_LANGS or any(l for l in IGNORE_SECTIONS if l[0] == lang)

def ignore_section(lang, section):
    return any(l for l in IGNORE_SECTIONS if l[0] in ["*", lang] and l[1] in ["*", section])

# template language names that are permitted within non-matching language sections
LANGUAGE_ALTS = {
   "Mandarin": "Chinese",
   "Western Highland Chatino": "San Juan Quiahije Chatino"
}

def language_matches(lang_id, lang_name):
    if lang_id not in lang_ids:
        return True

    id_name = lang_ids[lang_id]
    if id_name == lang_name:
        return True

    if LANGUAGE_ALTS.get(id_name) == lang_name:
        return True

# Fairly gross and sloppy, but good enough for headword lines
# will erroneosly accept {{ template } blah }
# doesn't treat {{ as a single brace (to enable {| |} table matching)
def first_template_is_closed(line):
    depth = 0

    for c in line:
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return True

def check_page(title, page_text):

    lang = None
    section_title = None
    in_pos_header = False
    open_template = None

    for line in page_text.splitlines():

        line = line.strip()
        if not line:
            continue

        # If the first template after a headword line is not closed, merge each line together until it is closed
        if open_template:
            line = open_template + line
            open_template = None
        else:
            # Skip wiki stuff that might be in the way of a template
            line = line.lstrip(" *#:")

        # Check for section headers
        if line.startswith("=="):
            res = re.match("(==+)\s*(.*?)\s*==+", line)
            if res:
                section_title = res.group(2)
                if len(res.group(1)) == 2:
                    # TODO: this doesn't work??
                    lang = section_title if not ignore_lang(section_title) else None
                elif lang:
                    in_pos_header = section_title in ALL_POS and not ignore_section(lang, section_title)
                    if in_pos_header:
                        pos_templates = POS_TEMPLATES.get(section_title.lower(), [section_title.lower()])
                        pos_line_matches = POS_LINE_MATCHES.get(section_title.lower(), [])
                        pos_headwords = POS_HEADWORDS.get(section_title.lower(), [section_title.lower()])
            continue

        # Ignore everything that's not in a POS section
        if not in_pos_header:
            continue

        # skip single line comments
        if line.startswith("<!--") and line.endswith("-->"):
            continue

        # Skip links
        if line.startswith("[[") and line[2:].split(":")[0].strip().lower() in IGNORE_LINKS:
            continue

        # Find the first template
        if line.startswith("{{") or line.startswith("{|"):
            # Ensure the first template is closed so we can properly parse it or skip it completely
            if not first_template_is_closed(line):
                open_template = line
                continue

            # Skip tables
            if line.startswith("{|"):
                continue

            # We only need to match the template name, the parameters are unimportant
            res = re.match(r"{{\s*(.*?)\s*[|}]", line)
            if res:
                template = res.group(1).lower()

                # Templates that may preceed the headline
                if template in IGNORE_TEMPLATES:
                    continue

            # We've finally reached a template that's not in the ignore list,
            # so we don't need to look at any future lines in this section
            in_pos_header = False

            # Unparsable template
            if not res:
                log("error", title, lang, section_title, line)
                continue

            if template in NOT_HEADLINES:
                log("Missing headline", title, lang, section_title, line)
                continue

            # Search templates for language codes
            template_lang_id = None
            if "-" in template:
                splits = template.split("-")

                # Check for hyphenated language codes first
                if len(splits) > 2:
                    template_lang_id = "-".join(splits[0:2])

                # Fallback to unhyphenated language code
                if template_lang_id not in lang_ids:
                    template_lang_id = splits[0]

            # The first paramater of the {{head}} template is the language code
            elif template == "head":
                res = re.match(r"{{\s*head\s*\|\s*(.*?)\s*\|", line)
                if res:
                    template_lang_id = res.group(1)

            # if template has a language prefix, check that it matches the parent language
            if template_lang_id and not language_matches(template_lang_id, lang):
                log("lang-mismatch", title, lang, section_title, line)
                continue

            # if this is head-like tempalte, check that a matching word appears on the headword line
            if template in HEAD_TEMPLATES:
                if any(pos for pos in pos_headwords if pos in line):
                    continue
                if any(alt for alt in GLOBAL_HEADWORDS if alt in line):
                    continue

            # Verify that template matches the allowed pos templates
            elif any(pos for pos in pos_templates if pos in template):
                continue

            if any(match in line for match in pos_line_matches):
                continue

            log("Mismatched templates", title, lang, section_title, line)

        else: # line doesn't start with a template
            in_pos_header = False
            log("Unexpected text (probably missing headline)", title, lang, section_title, line)

def main():

    import argparse
    argparser = argparse.ArgumentParser(description="Detect possibly mismatched POS headers from enwiktionary dump.\nBy default, scans all languages.")
    argparser.add_argument("--xml", help="XML file to load", required=True)
    argparser.add_argument("--limit", type=int, help="Limit processing to first N articles")
    argparser.add_argument("--progress", help="Display progress", action='store_true')
    argparser.add_argument("--date", help="Date of the database dump (used to generate page messages)")
    argparser.add_argument("--save", help="Save to wiktionary with specified commit message")
    args = argparser.parse_args()

    if not os.path.isfile(args.xml):
        raise FileNotFoundError(f"Cannot open: {args.xml}")

    dump = xmlreader.XmlDump(args.xml)
    parser = dump.parse()
    count = 0
    for page in parser:
        if ":" in page.title or "/" in page.title:
            continue

        if not count % 1000 and args.progress:
            print(count, end = '\r', file=sys.stderr)

        if args.limit and count >= args.limit:
            break
        count += 1

        check_page(page.title, page.text)

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
