#!/usr/bin/python3
#
# Copyright (c) 2020 Jeff Doozan
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
This will search all entries with a specified language with (Syn|Ant|*)nym categories
For all parts of speech having exactly one definition and containing a *nym category,
the category will be converted into an appropriate tag and added to the definition
"""

import os
from pywikibot import xmlreader
import re

import wtparser
from wtparser.nodes.language import LanguageSection
from wtparser.nodes.word import WordSection
from wtparser.nodes.nymsection import NymSection

class NymSectionToTag:
    def __init__(self, lang_name, lang_id, debug=()):
        self.LANG_SECTION = lang_name
        self.LANG_ID = lang_id
        self.errors = {}
        self._stats = {}
        self._debug_fix = set(debug)

        #self.log = logging.getLogger("wikibot")
        #self.log.setLevel(logging.DEBUG)
        #ch = logging.StreamHandler()
        #formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        #ch.setFormatter(formatter)
        #self.log.addHandler(ch)

    def flag_problem(self, problem, *data):
        #self.log.info(problem, json.dumps(data))
        #if name in self._debug_fix:
        #    print(f"{self._page} needs {name}: {params}")
        print(f"{self._page} needs {problem}: {data}")
        self.errors[problem] = self.errors.get(problem, []) + [data]

#    def remove_problem(self, problem):
#        del self.errors[problem]

#    def clear(self):
#        self.errors = {}

#    def is_good(self):
#        return self.errors == {}

#    def get_problems(self):
#        return self.errors.items()

    def get_language_entry(self, text):
        """
        Return the body text of the language entry
        """
        start_pattern = fr"\n=={self.LANG_SECTION}==\n"
        end_pattern = r"(?=\n==[^=]+==\s*\n|\n\[\[Category:|\n----\s*\n|$)"
        pattern = rf"({start_pattern}.*?){end_pattern}"
        res = re.search(pattern, text, re.DOTALL)
        if res:
            return res.group(1)

    def replace_nym_section_with_tag(self, language_text, nym_title, page=None):

        # Make sure there's a nym section at L3 or deeper
        header_level = 3
        header_tag = "=" * header_level
        if f"{header_tag}{nym_title}{header_tag}" not in language_text:
            return

        language = wtparser.parse_language(language_text, skip_style_tags=True, parent=self) #, name="wikibot.language")

        all_words = language.filter_words()
        if not len(all_words):
            self.flag_problem("no_words")

        for word in all_words:
            all_defs = word.filter_defs(recursive=False)
            all_nyms = word.filter_nyms(matches=nym_title)

            if len(all_nyms) == 0:
                if len(all_words) == 1:
                    all_nyms = language.filter_nyms(matches=nym_title)
                    if len(all_nyms):
                        self.flag_problem("automatch_nymsection_outside_word")
                else:
                    self.flag_problem("nym_matches_multiple_words")

            if len(all_nyms) == 0:
                self.flag_problem("cannot_find_nyms")
                continue

            if len(all_nyms) > 1:
                self.flag_problem("multiple_nym_sections")

            if len(all_nyms) and not len(all_defs):
                self.flag_problem("word_has_no_defs")
                continue

            for nym in all_nyms:

                # TODO: warn if word already has existing nym
                senses = nym.filter_senses()
                for nymsense in senses:
                    # TODO: Warn if nymsense has data that can't be converted
                    defs = word.get_defs_matching_sense(nymsense.sense)
                    if not len(defs):
                        if nymsense.sense == "":
                            defs = all_defs
                        else:
                            self.flag_problem("nym_matches_no_defs")
                            defs = [ all_defs[0] ]

                    if len(defs) > 1:
                        self.flag_problem("nym_matches_multiple_defs")
                    d = defs[0]
                    d.add_nymsense(nymsense)
                language.remove_child(nym)

        if str(language) == language_text:
            self.flag_problem("no_change")

        return str(language)


    def run_fix(self, text, tools=[], page_title="", sections=["Synonyms", "Antonyms"]):
        """
        *page_title* is only used for error messages, and only available when run directly
        Only return fixes that can be fixed with the list of *tools* provided
        """
        self.errors = {}
        self._page = page_title

        # TODO: Support fixing a single section at a time if the other section has errors
        new_text = text
        for nym_title in sections:
            prev_text = new_text
            new_text = self.replace_nym_section_with_tag(
                prev_text, nym_title, page_title
            )
            if not new_text:
                new_text = prev_text

        if new_text == text:
            return text

        if not len(self.errors.keys()):
            self.flag_problem("autofix")

        for x in self.errors.keys():
            self._stats[x] = self._stats.get(x, 0) + 1

        missing_fixes = set(self.errors.keys()).difference(tools)
        if missing_fixes and not len(self._debug_fix) and "all" not in tools:
            #print(f'{page_title} needs {", ".join(sorted(missing_fixes))}')
            return text

        return new_text


def main():

    import argparse

    parser = argparse.ArgumentParser(description="Convert *nym sections to tags.")
    parser.add_argument("--xml", help="XML file to load", required=True)
    parser.add_argument("--lang-id", help="Language id", required=True)
    parser.add_argument("--lang-section", help="Language name", required=True)
    parser.add_argument(
        "--pre-file",
        help="Destination file for unchanged articles (default: pre.txt)",
        default="pre.txt",
    )
    parser.add_argument(
        "--post-file",
        help="Destination file for changed articles (default: post.txt)",
        default="post.txt",
    )
    parser.add_argument(
        "--fix-debug",
        action="append",
        help="Print debug info for issues with the specified flag (Can be specified multiple times)",
        default=[],
    )
    parser.add_argument(
        "--section",
        action="append",
        help="Process specified nym section (Can be specified multiple times) (default: Synonyms, Antonyms)",
        default=["Synonyms", "Antonyms"],
    )
    parser.add_argument(
        "--fix",
        action="append",
        help="Fix issues with the specified flag (Can be specified multiple times)",
        default=[],
    )
    parser.add_argument(
        "--article-limit",
        type=int,
        help="Limit processing to first N articles",
        default=[],
    )
    parser.add_argument(
        "--fix-limit",
        type=int,
        help="Limit processing to first N fixable articles",
        default=[],
    )

    args = parser.parse_args()

    if not os.path.isfile(args.xml):
        raise FileNotFoundError(f"Cannot open: {args.xml}")

    dump = xmlreader.XmlDump(args.xml)
    parser = dump.parse()

    fixer = NymSectionToTag(args.lang_section, args.lang_id, debug=args.fix_debug)

    prefile = open(args.pre_file, "w")
    postfile = open(args.post_file, "w")

    count = 0
    lang_count = 0
    fixable = 0

    for entry in parser:
        if args.article_limit and count > args.article_limit:
            break
        count += 1

        if ":" in entry.title:
            continue

        lang_entry = fixer.get_language_entry(entry.text)

        if not lang_entry:
            continue

        lang_count += 1

        fixed = fixer.run_fix(lang_entry, args.fix, entry.title, args.section)
        if fixed == lang_entry:
            continue

        prefile.write(f"\nPage: {entry.title}\n")
        prefile.write(lang_entry)

        postfile.write(f"\nPage: {entry.title}\n")
        postfile.write(fixed)

        fixable += 1
        if args.fix_limit and fixable >= args.fix_limit:
            break

    print(f"Total articles: {count}")
    print(f"Total in {args.lang_section}: {lang_count}")
    print(f"Total fixable: {fixable}")

    for k, v in sorted(fixer._stats.items(), key=lambda item: item[1], reverse=True):
        print(f"{k}: {v}")

    prefile.close()
    postfile.close()


if __name__ == "__main__":
    main()
