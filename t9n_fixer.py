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
fix translation tables
"""

import os
import re
import sys
from copy import deepcopy
from autodooz.t9nparser import TranslationTable, TranslationLine, UNKNOWN_LANGS, LANG_PARENTS
from enwiktionary_wordlist.all_forms import AllForms
from autodooz.sectionparser import SectionParser

class T9nFixer():
    def __init__(self, allforms=None):
        self.allforms = allforms

    def cleanup_table(self, table):

        # TODO: warn if multiple senses and no gloss (requires en.data)

        self.fix_bottom_footer(table)

        for item in table.items:
            if not isinstance(item, TranslationLine):
                continue

            # TODO:
            # detect duplicate languages
            # fix indentation?
            # validate language code?

            if item.lang_id == "es":
                res = self.cleanup_list(item)


    def cleanup_list(self, tlist):

        if not self.allforms:
            return

        if not tlist.entries:
            return

        if tlist.has_errors:
            return

        # For now, spanish only
        if tlist.lang_id != "es":
            return

        # Adjectives only, nouns may need different logic
        if tlist.parent.pos != "Adjective":
            return
        pos = "adj"

        seen_genders = { g for item in tlist.entries for g in item.genders }

        if len(seen_genders) and ("m" not in seen_genders and "f" not in seen_genders and "mf" not in seen_genders):
            tlist.log("target_is_form", str(sorted(seen_genders)))
            return

        lemma_entries = {}
        for item in tlist.entries:

            pattern = r"""(?x)   # verbose regex
                \[\[             # double brackets
                ([^#|\]]*)       # the link target: everything before * | or ]
                .*?]]            # the link text and closing brackets
            """
            target = re.sub(pattern, r"\1", item.target)

            all_poslemmas = self.allforms.get_lemmas(target)
            if not all_poslemmas:
                if " " in item.target:
                    tlist.log("target_phrase_missing", target)
                else:
                    tlist.log("target_lemma_missing", target)
                return

            poslemmas = [p for p in all_poslemmas if p.startswith(f"{pos}|")]
            if not poslemmas:
                tlist.log("target_lemma_missing_pos", f'{item.target}:{pos}')
                return

            if len(poslemmas) > 1:
                if f"{pos}|" + target in poslemmas:
                    poslemmas = [f"{pos}|" + target]
                else:
                    tlist.log("target_lemma_ambiguous", f'{item.target} -> {poslemmas}')
                    return

            pos, lemma = poslemmas[0].split("|")
            if lemma not in lemma_entries:
                lemma_entries[lemma] = item
            else:
                # TODO: also check alt and other t params
                if item.qualifiers != lemma_entries[lemma].qualifiers:
                    tlist.log("removable_form_has_qualifier")
                    return

                if item.params and any(
                        v != lemma_entries[lemma].params.get(k) for k,v in item.params.items()
                        if not isinstance(k, int)):
                    tlist.log("removable_form_has_params")
                    return


        if len(lemma_entries) != len(tlist.entries):
            tlist.log("botfix_consolidate_forms")

            new_entries = []
            for lemma, item in lemma_entries.items():
                item.genders = []
                item.target = lemma
                new_entries.append(item)
            tlist.entries = new_entries

        elif "m" in seen_genders:
            for item in tlist.entries:
                item.genders = []

            tlist.log("botfix_remove_gendertags")



    def fix_bottom_footer(self, table):

        res = TranslationTable.parse_template_line(str(table.items[-1])) if table.items else None
        if res:
            pretext, template, params, posttext = res

        if not res or template not in TranslationTable.BOTTOM_TEMPLATES:
            if table.template in ["checktrans-top", "ttbc-top"]:
                table.items.append("{{checktrans-bottom}}")
            else:
                table.items.append("{{trans-bottom}}")
            table.log("missing_bottom_template")


class T9nFixRunner():

    """ Harness for running FormFixer from the fun_replace.py script """

    def __init__(self, allforms):
        self._fixer = None
        self._allforms = None

        # If a filename is specified, save it for lazy-loading
        if isinstance(allforms, str):
            self.allforms_file = allforms
        else:
            self._allforms = allforms

    @property
    def allforms(self):
        if not self._allforms:
            self._allforms = AllForms.from_file(self.allforms_file)
        return self._allforms

    @property
    def fixer(self):
        if not self._fixer:
            self._fixer = T9nFixer(self.allforms)
        return self._fixer

    @staticmethod
    def can_handle_page(title):

        if title is None:
            raise ValueError("This must be run through fun_replace.py, not replace.py")

        if ":" in title or "/" in title:
            return False

        return True

    def cleanup_tables(self, match, title, replacement=None):

        page_text = match.group(0)
        if not self.can_handle_page(title):
            return page_text

        if "==Translations==" not in page_text:
            return page_text

        replacements = []
        sections = SectionParser(page_text, title)
        for section in sections.ifilter_sections(matches=lambda x: x.title == "Translations"):
            pos = section.parent.title

            tables = list(TranslationTable.find_tables(str(section)))

            for table_text in tables:

                # TODO: rework TT() so it handles text instead of lines and doesn't require page, pos params
                table_lines = table_text.splitlines()
                table = TranslationTable(title, pos, table_lines, log_function=lambda *x: x)

                self.fixer.cleanup_table(table)
                new_text =  str(table)
                if new_text != table_text:
                    replacements.append((table_text, new_text))

        if replacements:
            if replacement:
                replacement._edit_summary = "Translations: cleanup formatting" #Spanish: reduced forms to common lemma"
            for item in replacements:
                old, new = item
                page_text = page_text.replace(old, new)

        return page_text
