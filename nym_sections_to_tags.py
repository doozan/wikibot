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
import regex
import sys
from Levenshtein import distance

import enwiktionary_parser as wtparser
from enwiktionary_parser.sections import WiktionarySection
from enwiktionary_parser.sections.language import LanguageSection
from enwiktionary_parser.sections.pos import PosSection
from enwiktionary_parser.sections.nym import NymSection
from enwiktionary_parser.wtnodes.nymline import NymLine
from enwiktionary_parser.wtnodes.word import Word

from enwiktionary_wordlist.wordlist import Wordlist
from enwiktionary_wordlist.wikiextract import WikiExtractWithRev

from enwiktionary_sectionparser import ALL_POS
from enwiktionary_templates import ALL_LANGS, ALL_LANG_IDS

class NymSectionToTag:
    def __init__(self, lang_id, wordlist=None, debug=()):
        self.LANG_SECTION = ALL_LANG_IDS[lang_id]
        self.LANG_ID = lang_id
        self._problems = {}
        self._stats = {}
        self._debug_fix = set(debug)
        self.fixes = set()

        self.wordlist = Wordlist.from_file(wordlist) if isinstance(wordlist, str) else wordlist

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
#        print(f"{self._page} needs {problem}: {data}", file=sys.stderr)
        self._problems[problem] = self._problems.get(problem, []) + [data]

        return not self.can_handle(problem)

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


    @classmethod
    def split_sense(cls, sense):
        # on any character that isn't in the unicode alphabet
        split = []
        for x in regex.split(r'[^\p{L}]+', sense):
            if len(x) <= 2 or x in ["and", "for", "the", "with"]:
                continue
            if x not in split:
                split.append(x)
        return split

    @staticmethod
    def sense_matches_target(split_sense, targets, fuzzy):
        if len(split_sense) > len(targets):
            return False
            #split_sense, targets = targets, split_sense
        for sense in split_sense:
            if fuzzy:
                if not any(distance(sense, x) < 3 for x in targets):
                    return False
            else:
                if not any(sense == x for x in targets):
                    return False
        return True


    def get_matching_pos(self, nymsense, all_pos):
        # If we have a wordlist, make sure the nymsense pos matches at least one possible pos of
        # at least one synonym
        if self.wordlist:
            pos_options = []
            for link in nymsense.ifilter_decoratedlinks():
                word = link.link.get("target")
                for word_obj in self.wordlist.get_words(word):
                    if word_obj.pos not in pos_options:
                        pos_options.append(word_obj.pos)

            return [ pos for pos in all_pos if sectionparser.ALL_POS.get(pos.name) in pos_options ]

        else:
            return all_pos

    def get_matching_senses(self, nymsense, all_pos, fuzzy=False):

        # Returns a list of wordsenses that match the provided nymsense

        valid_pos = self.get_matching_pos(nymsense, all_pos)
        all_wordsenses = [ ws for pos in valid_pos for ws in pos.ifilter_wordsenses() ]

        if not nymsense.sense:
            return all_wordsenses

        split_sense = self.split_sense(nymsense.sense.lower())
        if not split_sense:
            return all_wordsenses

        # Check sense_id
        matches = [ ws for ws in all_wordsenses if self.sense_matches_target(split_sense, ws.sense_ids, fuzzy) ]

        # Check labels/qualifiers
        if not matches:
            matches = [ ws for ws in all_wordsenses if self.sense_matches_target(split_sense, ws.sense_labels, fuzzy) ]

        # Match in the gloss
        if not matches:
            matches = [ ws for ws in all_wordsenses if self.sense_matches_target(split_sense, self.split_sense(ws.gloss.lower()), fuzzy) ]

        return matches


    # Try to pair nym senses against the wordsenses
    def get_matching_senses_by_nymsense(self, nymsense, all_pos, fuzzy=False):
        if not self.wordlist:
            return []

        valid_pos = self.get_matching_pos(nymsense, all_pos)
        all_wordsenses = [ ws for pos in valid_pos for ws in pos.ifilter_wordsenses() ]

        # Still trying to find the best match among multiple options
        # Try to match the sense against the synonym's senses
        gloss_options = []
        has_word = False
        for link in nymsense.ifilter_decoratedlinks():
            word = link.link.get("target")
            if self.wordlist.has_word(word):
                has_word = True
            for word_obj in self.wordlist.get_words(word):
                for sense in word_obj.senses:
                    nym_gloss = self.split_sense(sense.gloss.lower())
                    if nym_gloss and nym_gloss not in gloss_options:
                        gloss_options.append(nym_gloss)

        matches = []
        for ws in all_wordsenses:
            split_target = self.split_sense(ws.gloss.lower())
            if not split_target:
                continue
            matched = False
            for nym_gloss in gloss_options:
                if self.sense_matches_target(nym_gloss, split_target, fuzzy):
                    matches.append(ws)
                    mached = True
                if matched:
                    break

        return matches

    def get_search_pos(self, nym, wikt):
        """ Returns a list of POS that match the given nymsection """

        # First, see if a parent node is a POS
        pos = nym.get_ancestor(PosSection)
        if pos:
            return [pos]

        # Next, see if a parent nod is an Etymology containing a POS
        search_pos = []
        etymology = nym.get_matching_ancestor(lambda x: hasattr(x, "name") and x.name.startswith("Etymology"))
        if etymology:
            search_pos = etymology.filter_pos()

        # Finally, just match every POS on the page
        if not search_pos:
            search_pos = wikt.filter_pos()

        if len(search_pos) == 1:
            nym.flag_problem("automatch_nymsection_outside_pos")
        else:
            nym.flag_problem("nymsection_matches_multiple_pos")

        return search_pos

    def replace_nym_section_with_tag(self, language_text, nym_title, title=None):

        # Make sure there's a nym section at L3 or deeper
        header_level = 3
        header_tag = "=" * header_level
        if f"{header_tag}{nym_title}{header_tag}" not in language_text:
            return

        wikt = wtparser.parse_page(language_text, title=title, parent=self, skip_style_tags=True)

        self._stats[nym_title] = self._stats.get(nym_title, 0) + 1

        # Don't use ifilter because it gets confused when we remove the nym section
        for nym in wikt.filter_nyms(matches=lambda x: x.name == nym_title):
            unhandled_problems = False
            search_pos = self.get_search_pos(nym, wikt)

            if not any(sense for p in search_pos for sense in p.ifilter_wordsenses()):
                nym.flag_problem("pos_has_no_defs", nym_title)
                continue

            for nymsense in nym.filter_nymsenses():
                matches = self.get_matching_senses(nymsense, search_pos, fuzzy=False)

                # Try fuzzy match if we don't have an exact match
                if len(matches) != 1:
                    alt_matches = self.get_matching_senses(nymsense, search_pos, fuzzy=True)
                    if len(alt_matches) == 1:
                        nymsense.flag_problem("nymsense_fuzzy_match", nym_title)
                        matches = alt_matches

                # Still no exact match
                # Try matching the nymsense to the wordsense
                if len(matches) != 1:
                    alt_matches = self.get_matching_senses_by_nymsense(nymsense, search_pos, fuzzy=False)
                    if len(alt_matches) == 1:
                        nymsense.flag_problem("nymsense_gloss_matches_wordsense", nym_title)
                        matches = alt_matches

                    # There were no matches, try again with fuzzy matching
                    elif not alt_matches:
                        alt_matches = self.get_matching_senses_by_nymsense(nymsense, search_pos, fuzzy=True)
                        if len(alt_matches) == 1:
                            nymsense.flag_problem("nymsense_gloss_matches_wordsense_fuzzy", nym_title)
                            matches = alt_matches

                no_merge = len(matches) != 1

                if len(matches) == 1:
                    if nymsense.sense != "":
                        nymsense.flag_problem("automatch_sense", matches, nymsense.sense)

                elif not matches:
                    nymsense.flag_problem("nymsense_matches_no_defs", nymsense.sense)
                    # Default to matching the first def
                    matches = [next(sense for p in search_pos for sense in p.ifilter_wordsenses())]

                else:
                    nymsense.flag_problem("nymsense_matches_multiple_defs")
                    # If this isn't a perfect match, don't merge it into existing nymsense
                    # This makes it easy to manually review and move to the correct location

                match = matches[0]
                if self.can_handle(nym.local_problems) \
                   and self.can_handle(match.problems) \
                   and self.can_handle(nymsense.problems) \
                   and self.add_nymsense_to_def(nymsense, match, no_merge=no_merge):
                       nymsense._parent.remove_child(nymsense)
                else:
                    unhandled_problems = True

            # IF the nym has subsections, move them to the nym's parent object
            if any(nym.ifilter_sections(recursive=False)):
                if not self.flag_problem("autofix_nymsection_has_subsections"):
                    if not unhandled_problems and self.can_handle(nym.local_problems):
                        nym.raise_subsections()
                        nym._parent.remove_child(nym)

            elif not unhandled_problems and self.can_handle(nym.local_problems):
                nym._parent.remove_child(nym)


#        if str(wikt) == language_text:
#            self.flag_problem("no_change")

        return str(wikt)


    def add_nymsense_to_def(self, nymsense, definition, no_merge=False):

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
                    line = regex.sub("\n", f" <!-- FIXME, MATCH SENSE: '{nymsense.sense}' -->\n", line)
                definition.add_nymline(line, smart_position=True, no_merge=no_merge)
                return True

    def add_nymsense_to_nymline(self, nymsense, nymline):
        items = [decoratedlink.item for decoratedlink in nymsense.filter_decoratedlinks()]
        if items:
            nymline.add(items)


    def process(self, page_text, page_title, summary=None, fixes=[], sections=["Synonyms", "Antonyms"], dump_unfixable=False):

        entry = sectionparser.parse(page_text, page_title)
        if not entry:
            return page_text

        # TODO: get lang from self.LANG_ID
        lang_name = "Spanish"
        l2 = entry.filter_sections(matches=lang_name, recursive=False)
        if not l2 or not len(l2) == 1:
            return page_text

        lang = l2[0]

        old_text = str(lang)
        new_text = self.run_fix(str(lang), fixes, page_title)
        if old_text == new_text:
            return page_text

        header, children, changes = entry.parse(new_text)
        if header or len(children) != 1:
            raise ValueError("unexpected changes")
        new_lang = children[0]

        idx = entry._children.index(lang)
        entry._children[idx] = new_lang

        if summary is not None:
            summary.append(f"/*{lang_name}*/ replaced Synonym section with template")

        return str(entry)

    def run_fix(self, text, fixes=[], page_title="", sections=["Synonyms", "Antonyms"], dump_unfixable=False):
        """
        *page_title* is only used for error messages, and only available when run directly
        Only return fixes that can be fixed with the list of *fixes* provided
        """

        self.clear_problems()
        self._page = page_title

        self.fixes = set(fixes)

        new_text = text

        found = False
        for nym_title in sections:
            prev_text = new_text
            new_text = self.replace_nym_section_with_tag(
                prev_text, nym_title, page_title
            )
            if not new_text:
                new_text = prev_text
            else:
                found = True

        if not found:
            if dump_unfixable:
                return None
            else:
                return text

        if new_text == text:
            return text

        if not len(self._problems.keys()):
            self.flag_problem("autofix")
            if "autofix" not in self.fixes and "all" not in self.fixes:
                print(f'{page_title} needs autofix', file=sys.stderr)
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

#        if missing_fixes and not len(self._debug_fix) and "all" not in self.fixes:
#            print(f'XXXXXXX {page_title} needs {", ".join(sorted(x for x in missing_fixes if not x.startswith("_")))}')

        if "partial_fix" in missing_fixes and "all" not in self.fixes:
            return text

        return new_text.rstrip()


def main():

    import argparse

    parser = argparse.ArgumentParser(description="Convert *nym sections to tags.")
    #parser.add_argument("--xml", help="XML file to load", required=True)
    parser.add_argument("--langdata", help="Language extract file to load", required=True)
    parser.add_argument("--lang-id", help="Language id", required=True)
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
        help="Process specified nym section (Can be specified multiple times) (default: Synonyms)",
        default=["Synonyms"],
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
    parser.add_argument("--wordlist", help="Use reference wordlist for smarter matching")
    parser.add_argument("--dump-unfixable", help="Dump unfixable articles")

    args = parser.parse_args()

    #if not os.path.isfile(args.xml):
    #    raise FileNotFoundError(f"Cannot open: {args.xml}")
    if not os.path.isfile(args.langdata):
        raise FileNotFoundError(f"Cannot open: {args.langdata}")

#    dump = xmlreader.XmlDump(args.xml)
#    parser = dump.parse()
#    parser = LanguageParser(args.bz2)

    if args.lang_id not in ALL_LANG_IDS:
        raise ValueError(f"Unknown language id: {args.lang_id}")

    wordlist = Wordlist.from_file(args.wordlist) if args.wordlist else None

    fixer = NymSectionToTag(args.lang_id, wordlist, debug=args.fix_debug)

    prefile = open(args.pre_file, "w")
    postfile = open(args.post_file, "w")

    count = 0
    lang_count = 0
    unfixable = 0
    fixable = 0

    ignore = set()
    if args.ignore:
        with open(args.ignore) as infile:
            ignore = set(infile.read().splitlines())

    for article in WikiExtractWithRev.iter_articles_from_bz2(args.langdata):
        entry_title = article.title
        lang_entry = article.text

        if args.article_limit and count > args.article_limit:
            break
        count += 1

#        if ":" in entry_title:
#            continue

        if entry_title in ignore:
            continue

        if not lang_entry:
            continue

        lang_count += 1

#        print(f"Scanning {entry_title}")

        fixed = fixer.run_fix(lang_entry, args.fix, entry_title, args.section, args.dump_unfixable)
        if not fixed:
            continue
        if fixed == lang_entry:
            unfixable += 1
            if args.dump_unfixable:
                print(f"_____{entry_title}_____")
                print(lang_entry)
            continue

        prefile.write(f"\nPage: {entry_title}\n")
        prefile.write(lang_entry)

        postfile.write(f"\nPage: {entry_title}\n")
        postfile.write(fixed)

        fixable += 1
        if args.fix_limit and fixable >= args.fix_limit:
            break

    print("_____Stats_____")
    print(f"Total articles: {count}")
    print(f"Total in {fixer.LANG_SECTION}: {lang_count}")
    for section in args.section:
        print(f"Total with {section}: {fixer._stats[section]}")
    print(f"Total unfixable: {unfixable}")
    print(f"Total fixable: {fixable}")

    print("_____Unfixable_____")
    for k, v in sorted(fixer._stats.items(), key=lambda item: item[1], reverse=True):
        if k not in args.fix:
            print(f"{k}: {v}")

    print("_____Fixable_____")
    for k, v in sorted(fixer._stats.items(), key=lambda item: item[1], reverse=True):
        if k in args.fix:
            print(f"{k}: {v}")

    prefile.close()
    postfile.close()


if __name__ == "__main__":
    main()
