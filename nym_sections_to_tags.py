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
from wtparser.sections import WiktionarySection
from wtparser.sections.language import LanguageSection
from wtparser.sections.pos import PosSection
from wtparser.sections.nymsection import NymSection
from wtparser.wtnodes.nymline import NymLine
from wtparser.wtnodes.word import Word

class NymSectionToTag:
    def __init__(self, lang_name, lang_id, debug=()):
        self.LANG_SECTION = lang_name
        self.LANG_ID = lang_id
        self._problems = {}
        self._stats = {}
        self._debug_fix = set(debug)
        self.fixes = set()

        #self.log = logging.getLogger("wikibot")
        #self.log.setLevel(logging.DEBUG)
        #ch = logging.StreamHandler()
        #formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        #ch.setFormatter(formatter)
        #self.log.addHandler(ch)

    def flag_problem(self, problem, *data, from_child=False):
        """ Add *problem* to the internal list of problems

        Return value is a Bool whether the problem is unhandled (True) or handled (False)
        """

        #self.log.info(problem, json.dumps(data))
        #if name in self._debug_fix:
        #    print(f"{self._page} needs {name}: {params}")
        print(f"{self._page} needs {problem}: {data}")
        self._problems[problem] = self._problems.get(problem, []) + [data]

        if "all" in self.fixes:
            return False

        return problem not in self.fixes

    def clear_problems(self):
        self._problems = {}

    def can_handle(self, problems):
        if "all" in self.fixes:
            return True

        if isinstance(problems, dict):
            res = len(set(problems.keys()).difference(self.fixes)) == 0
        else:
            res = problems in self.fixes

        return res

    def get_language_entry(self, text):
        """
        Return the body text of the language entry
        """

        start = fr"(^|\n)=={self.LANG_SECTION}==\n"
        re_endings = [ r"\[\[\s*Category\s*:", r"==[^=]+==", r"----" ]
        template_endings = [ "c", "C", "top", "topics", "categorize", "catlangname", "catlangcode", "cln", "DEFAULTSORT" ]
        re_endings += [ r"\{\{\s*"+item+r"\s*\|" for item in template_endings ]
        endings = "|".join(re_endings)
        newlines = r"(\n\s*){1,2}"
        pattern = fr"{start}.*?(?={newlines}({endings})|$)"

        res = re.search(pattern, text, re.DOTALL)
        if res:
            return res.group(0)

    def replace_nym_section_with_tag(self, language_text, nym_title, page=None):

        # Make sure there's a nym section at L3 or deeper
        header_level = 3
        header_tag = "=" * header_level
        if f"{header_tag}{nym_title}{header_tag}" not in language_text:
            return

        language = wtparser.parse_language(language_text, skip_style_tags=True, parent=self) #, name="wikibot.language")

        all_pos = language.filter_pos()
        if not len(all_pos):
            self.flag_problem("no_pos")
            return

        all_nyms = language.filter_nyms(matches=lambda x: x.name == nym_title)
        for nym in all_nyms:
            unhandled_problems = False
            pos = nym.get_ancestor(PosSection)
            if not pos:
                pos = all_pos[0]
                if len(all_pos) == 1:
                    nym.flag_problem("automatch_nymsection_outside_pos")
                else:
                    nym.flag_problem("nymsection_matches_multiple_pos")

            all_words = pos.filter_words()
            if len(all_words) > 1:
                nym.flag_problem("pos_has_multiple_words")

            all_defs = pos.filter_defs()

            if not len(all_defs):
                nym.flag_problem("pos_has_no_defs", pos.name)
                continue

            senses = nym.filter_senses()
            for nymsense in senses:
                defs = pos.filter_defs(matches=lambda d: d.has_sense(nymsense.sense))

                if not len(defs):
                    defs = all_defs
                    if nymsense.sense != "":
                        nymsense.flag_problem("nymsense_matches_no_defs", nymsense.sense)

                elif nymsense.sense != "":
                    nymsense.flag_problem("automatch_sense")

                no_merge=False
                d = defs[0]
                if len(defs) > 1:
                    nymsense.flag_problem("nymsense_matches_multiple_defs")
                    # If this isn't a perfect match, don't merge it into existing nymsense
                    # This makes it easy to manually review and move to the correct location
                    no_merge=True

                if self.can_handle(nym.local_problems) \
                   and self.can_handle(d.problems) \
                   and self.can_handle(nymsense.problems) \
                   and self.add_nymsense_to_def(nymsense, d, no_merge=no_merge):
                       nymsense._parent.remove_child(nymsense)
                else:
                    unhandled_problems = True

            # IF the nym has subsections, move them to the nym's parent object
            if len(nym.filter_sections(recursive=False)):
                if not self.flag_problem("autofix_nymsection_has_subsections"):
                    if not unhandled_problems and self.can_handle(nym.local_problems):
                        nym.raise_subsections()
                        nym._parent.remove_child(nym)

            elif not unhandled_problems and self.can_handle(nym.local_problems):
                nym._parent.remove_child(nym)

#        if str(language) == language_text:
#            self.flag_problem("no_change")

        return str(language)


    def add_nymsense_to_def(self, nymsense, definition, no_merge=False):
        # TODO: Ensure nymsense has items
        #

        nymline = definition.get_nym(nymsense._type)
        if not no_merge and nymline and "FIXME" not in nymline:
            self.flag_problem("both_nym_line_and_section")
            if self.can_handle("both_nym_line_and_section"):
                self.add_nymsense_to_nymline(nymsense, nymline)
                return True
        else:
            nymline = NymLine.from_nymsense(nymsense, name="1", parent=definition)
            if len(str(nymline)) > 200:
                nymline.flag_problem("long_nymline")
            if self.can_handle(nymline.problems):
                line = str(nymline)
                if no_merge:
                    line = re.sub("\n", f" <!-- FIXME, MATCH SENSE: '{nymsense.sense}' -->\n", line)
                definition.add_nymline(line, smart_position=True, no_merge=no_merge)
                return True

    def add_nymsense_to_nymline(self, nymsense, nymline):
        items = [wordlink.item for wordlink in nymsense.filter_wordlinks()]
        if items:
            nymline.add(items)

    def run_fix(self, text, fixes=[], page_title="", sections=["Synonyms", "Antonyms"]):
        """
        *page_title* is only used for error messages, and only available when run directly
        Only return fixes that can be fixed with the list of *fixes* provided
        """
        self.clear_problems()
        self._page = page_title

        self.fixes = set(fixes)

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

        if not len(self._problems.keys()):
            self.flag_problem("autofix")
            if "autofix" not in self.fixes and "all" not in self.fixes:
                print(f'{page_title} needs autofix')
                return text

        for x in self._problems.keys():
            self._stats[x] = self._stats.get(x, 0) + 1

        if "only" in self.fixes:
            if self.fixes.difference(set(self._problems.keys())) == {"only"} and \
               set(self._problems.keys()).difference(self.fixes) == set():
                   return new_text
            return text

        missing_fixes = set(self._problems.keys()).difference(self.fixes)
        if missing_fixes:
            self.flag_problem("partial_fix")
            missing_fixes = set(self._problems.keys()).difference(self.fixes)

        if missing_fixes and not len(self._debug_fix) and "all" not in self.fixes:
            print(f'{page_title} needs {", ".join(sorted(x for x in missing_fixes if not x.startswith("_")))}')

        if "partial_fix" in missing_fixes and "all" not in self.fixes:
            return text
        else:
            return new_text.rstrip()


def main():

    import argparse

    parser = argparse.ArgumentParser(description="Convert *nym sections to tags.")
    parser.add_argument("--xml", help="XML file to load", required=True)
    parser.add_argument("--lang-id", help="Language id", required=True)
    parser.add_argument("--lang-section", help="Language name", required=True)
    parser.add_argument("--ignore", help="List of articles to ignore")
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

    ignore = set()
    if args.ignore:
        with open(args.ignore) as infile:
            ignore = set(infile.read().splitlines())

    for entry in parser:
        if args.article_limit and count > args.article_limit:
            break
        count += 1

        if ":" in entry.title:
            continue

        if entry.title in ignore:
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
