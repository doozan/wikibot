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
List translations
"""

import os
import re
import sys
import pywikibot
from pywikibot import xmlreader
from autodooz.wikilog import WikiLogger
from enwiktionary_wordlist.wordlist import Wordlist
from enwiktionary_wordlist.utils import wiki_to_text
from autodooz.sectionparser import SectionParser
from enwiktionary_parser.utils import template_aware_split
from enwiktionary_parser.sections.pos import ALL_POS
from enwiktionary_parser.languages.all_ids import languages as lang_ids
ALL_LANGS = {v:k for k,v in lang_ids.items()}

class Logger(WikiLogger):
    def save_page(self, page, page_text, commit_message):
        if commit_message:
            print("saving wiki page")
            super().save_page(page, page_text, commit_message)

        # Save pages locally if no commit message provided
        else:
            page = page.lstrip("/").replace("/", "_")
            with open(page, "w") as outfile:
                outfile.write(page_text)
                print("saved", page)

    def sort_items(self, items):
        return sorted(items)

    LANGUAGE = 2
    def page_name(self, items, prev):
        return f"translation_problems"

    def make_entry(self, base_url, page_name, items, pages):
        res = [f"Translation sections with problems: {len(items)} items"]

        prev_error = None
        for item in items:
            error, page, section, line = item
            if prev_error != error:
                print(f"==={error}===")
                prev_error = error
            data = f": [[{page}#Translations|{page}:{section}"
            if line:
                data += f" <nowiki>{line}</nowiki>"
            res.append(data)
        return res

logger = Logger()

def log(error, page, section, line=None):
    if error != "unknown lang":
        print(f"{page}:{section} {error}{': ' + line if line else ''}", file=sys.stderr)
    logger.add(error, page, section, line)

def add_translation(page, pos, gloss, translations):
    print(f"{page}:{pos}:{gloss}:: {translations}")

unknown_langs = set()
def add_translations(word, pos, gloss, language, translations, section, line):

    lang_id = ALL_LANGS.get(language)
    if not lang_id:
        if "{{ttbc" in language:
            return
        path = ":".join(reversed(list(section.lineage)[:-1]))
        if language not in unknown_langs:
            unknown_langs.add(language)
            print(f"unknown lang '{language}': {line}", file=sys.stderr)
#        log("unknown lang", word, path, line)

    if language != "Spanish":
        return
    add_translation(word, pos, gloss, translations)
# t, t+, tt, tt+
# t-check
# t-needed
#    data = mwparserfromhell.parse(translations):

def process_page(title, page_text):

    if "===Translations===" not in page_text:
        return

    entry = SectionParser(page_text, title)
    for section in entry.ifilter_sections(matches=lambda x: x.title == "Translations"):

        if section.parent.title not in ALL_POS:
            path = ":".join(reversed(list(section.lineage)[:-1]))
            log("outside_pos", title, path)
            continue

        pos = section.parent.title

        gloss = None
        for line in section._lines:
            match = re.match(r"{{trans-top\|\s*([^|}]*)", line)
            if match:
                gloss = match.group(1)

            # Assumes each language is on it's own line that looks like
            # * Language: {{t|here}}, {{tt|another}}
            # see WT:TRANS for more

            # TODO: This doesn't match indented messes
            # * Chinese:
            # *: Mandarin: {{t+|cmn|基里巴斯|tr=Jīlǐbāsī|sc=Hani}}
            # * Serbo-Croatian:
            # *: Cyrillic: {{t|sh|Кирибати|m}}
            # *: Roman: {{t+|sh|Kiribati|m}}

            # Check for "* Language:"
            match = re.match(r"\s*\*\s+(.+?):\s(.*)", line)
            if match:
                language = match.group(1)
                translations = match.group(2)
                if translations:
                    add_translations(title, pos, gloss, language, translations, section, line)

# TODO: handle nested language (see Sunday#Translations and five#Translations)

#            else:
#                match = re.match(r"\s*:\*\s*(.+):\s(.*)", line)
#                if match:
#                    sub_language = match.group(1)
#                    sub_translations = match.group(2)
#                    add_translations(title, pos, gloss, f"{language}:{sub_language}", sub_translations)

            #if new_line:
            #    if line in replacements and replacements[line] != new_line:
            #        raise ValueError("duplicate fixes", line, [replacements[line], new_line])
            #    replacements[line] = new_line

def main():

    import argparse
    argparser = argparse.ArgumentParser(description="Find lemmas with only 'form of' senses")
    argparser.add_argument("--xml", help="xml dump to read", required=True)
    #argparser.add_argument("--wordlist", help="wordlist to load", required=True)
    argparser.add_argument("--limit", type=int, help="Limit processing to first N articles")
    argparser.add_argument("--progress", help="Display progress", action='store_true')
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

        process_page(page.title, page.text)

    base_url = "User:JeffDoozan/lists" if args.save else ""
    logger.save(base_url, args.save)

if __name__ == "__main__":
    main()
