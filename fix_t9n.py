#!/usr/bin/python3
#
# Copyright (c) 2021-2025 Jeff Doozan
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

import enwiktionary_sectionparser as sectionparser
import os
import re
import sys

from autodooz.sections import ALL_LANGS, ALL_LANG_IDS
from enwiktionary_translations.t9nparser import TranslationTable, TranslationLine, Translation, get_tables
from enwiktionary_wordlist.all_forms import AllForms
from autodooz.utils import nest_aware_resplit, nest_aware_split

ttbc_fixes = {}

class T9nFixer():
    def __init__(self, allforms=None):
        self.allforms = allforms

    def cleanup_table(self, table):
        # TODO: warn if multiple senses and no gloss (requires en.data)

        self.fix_bottom_footer(table)
        table.fixes = []

        fixes = []
        for i, item in enumerate(table.items):

            if isinstance(item, TranslationLine):
                res = self.cleanup_line(item)
            else:
                # Expand {{ttbc
                if "{{ttbc" in item:
                    cleaned_item = ttbc_fixes.get(item)
                    if not cleaned_item:
                        cleaned_item = self.cleanup_ttbc(item)
                    if cleaned_item:
                        fixes.append((i, cleaned_item))
                        table.fixes.append("Updated {{ttbc}} line")

                # replace "* Language" with "* Language:"
                else:
                    match = re.match("[ #*:]+(.*)", item)
                    if match:
                        if match.group(1).strip() in ALL_LANGS:
                            fixes.append((i, item.rstrip() + ":"))
                            table.fixes.append("Appended : to bare language line")

            # TODO:
            # detect duplicate languages
            # fix indentation?
            # validate language code?


        if fixes:
            for i, new_item in fixes:
                table.items[i] = new_item

    re_ttbc_line = re.compile(r"([*#: ]*){{ttbc\|([^|}]+)}}(.*)") #}} - code folding fix
    @classmethod
    def cleanup_ttbc(cls, line):

        match = re.match(cls.re_ttbc_line, line)
        if not match:
            return

        lang_id = match.group(2)
        full_lang = ALL_LANG_IDS.get(lang_id)
        if not full_lang:
            return

        new_line = match.group(1) + full_lang + match.group(3)
        if "{{t-check" in new_line or "{{t+check" in new_line:
            return new_line

        newer_line = re.sub(r"{{(t|tt|t\+|tt\+)\s*\|", lambda x: "{{t+check|" if x.group(1).endswith("+") else "{{t-check|", new_line)
        if newer_line != new_line:
            return newer_line

        res = TranslationTable.parse_lang_line(new_line)
        if not res:
            return

        # Don't aggressively check without manual approval
        return

        depth, lang, data = res

        res = depth + " " + lang + ": "
        entries = []
        for entry in nest_aware_resplit(r"[,;]\s*", data, [("(",")")]):
            new_entry = cls.make_translation(entry[0], lang_id)
            if new_entry == entry:
                return
            entries.append(new_entry)

        return res + ", ".join(entries)


    @classmethod
    def make_translation(cls, text, lang_id):


        #(?:{{l\|[^|]+\|)?       # {{l|*|
        #(?:}})?                 # }}

        PATTERN = r"""(?x)  # verbose regex
        \s*
        (?:\[\[)                # [[
        ([^#\|(){}\[\]]+?)      # single link without any symbols or whitespace, captured asgroup(1)
        (?:]])                  # ]]
        \s*
        (?:{{g\|([^}]+)}})?     # {{g|blah}} tag, "bl|ah" captured as group(2)
        \s*
        (\([\w, \-'’"]+\))?     # (words without any symbols), captured as group(3)
        \s*
        (\([0-9, \-]+\))?       # (1,2, 3), captured as group(4)
        \s*
        $
        """

        match = re.match(PATTERN, text)
        if not match:
            return text

        new_entry = "{{t|" + lang_id + "|" + match.group(1)
        if match.group(2):
            new_entry += "|" + match.group(2)
        new_entry += "}}"
        if match.group(3):
            new_entry += " " + match.group(3)
        if match.group(4):
            new_entry += " " + match.group(4)

        return new_entry

        # bareword or [[single link]]
#        match = re.match(r"(?:\[\[)?([:_\-=}\|{[\][!@#$%^&*() \",'])(?:]])$", data)
#        if match:
#            return depth + " " + lang + ": {{t-check|" + lang_id + "|" + match.group(1) + "}}"

        # bareword {{g|m}}
        # [[single link]] {{g|m}}
#        match = re.match(r"(?:\[\[)?([^\W]*)(?:]])?\s*({{g\|([^}])+}})?$", data)
#        if match:
#            return depth + " " + lang + ": {{t-check|" + lang_id + "|" + match.group(1) + "|" + match.group(2) + "}}"


#        data = data.strip("[]")
#        if data and not re.search(r"[:_\-=}\|{[\][!@#$%^&*() \",']", data):
#            return depth + lang + ": {{t-check|" + lang_id + "|" + data + "}}"


#        return str(tline)



#        entries = []
#        for entry in split_entry_list(data):

    def convert_l_to_t(self, item):

        gender_keys = []
        for k in item.params.keys():
            if isinstance(k, int):
                continue
            elif k.startswith("g"):
                gender_keys.append(k)
            elif k not in ["ts", "sc", "tr", "alt", "lit", "id"]:
                raise ValueError("complex_keys", item)

        genders = {}
        for k in gender_keys:
            v = item.params.pop(k)
            idx = k[1:]
            if idx:
                genders[int(idx)] = v
            else:
                genders[1] = v

        gender_list = []
        for k,v in sorted(genders.items(), key=lambda x: x[1]):
            if v not in gender_list:
                gender_list.append(v)

        for k,v in enumerate(gender_list, 3):
            item.params[k] = v

        if item.template == "l":
            item.template = "t"

        item.parent.parent.fixes.append("Converted {{l}} to {{t}}")


    def cleanup_line(self, tline):

        if tline.has_errors:
            entries = []
            for item in nest_aware_split(',', tline._entries, [("{{","}}"), ("(",")")]):

                # Disable the tline logger when rebuilding the Translations so that
                # it doesn't add new errors to the log
                old_log = tline.log
                tline.log = lambda *x, **y: ""
                entry = Translation(item, tline)
                tline.log == old_log

                if entry.has_errors:
                    entry.parent = tline
                    new_item = self.make_translation(item, tline.lang_id)
                    if new_item != item:
                        tline.parent.fixes.append("Converted bare link to {{t}}")
                        entry = Translation(new_item, tline)

                    # If it couldn't be parsed, give up
                    else:
                        return

                entries.append(entry)
            tline.entries = entries
            tline.has_errors = False
            return

        if not tline.entries:
            return

        if not self.allforms:
            return

        for item in tline.entries:
            if "{{l" in str(item):
                self.convert_l_to_t(item)

       # For now, spanish only
        if tline.lang_id != "es":
            return

        # Adjectives only, nouns may need different logic
        if tline.parent.pos != "Adjective":
            return
        pos = "adj"

        seen_genders = set()
        for item in tline.entries:
            # Fail if any item is t-needed
            if not item.params:
                return

            for k,g in item.params.items():
                if isinstance(k,int) and k > 2:
                    seen_genders.add(g)


        if len(seen_genders) and ("m" not in seen_genders and "f" not in seen_genders and "mf" not in seen_genders):
            tline.log("target_is_form", str(sorted(seen_genders)))
            return

        lemma_entries = {}
        for item in tline.entries:
            pattern = r"""(?x)   # verbose regex
                \[\[             # double brackets
                ([^#|\]]*)       # the link target: everything before * | or ]
                .*?]]            # the link text and closing brackets
            """
            target = item.params[2]
            clean_target = re.sub(pattern, r"\1", target)

            all_poslemmas = self.allforms.get_lemmas(clean_target)
            if not all_poslemmas:
                if " " in target:
                    tline.log("target_phrase_missing", target)
                else:
                    tline.log("target_lemma_missing", f"{target}")
                return

            poslemmas = [p for p in all_poslemmas if p.startswith(f"{pos}|")]
            if not poslemmas:
                tline.log("target_lemma_missing_pos", f'{target}:{pos}')
                return

            if len(poslemmas) > 1:
                if f"{pos}|" + clean_target in poslemmas:
                    poslemmas = [f"{pos}|" + clean_target]
                else:
                    tline.log("target_lemma_ambiguous", f'{target} -> {poslemmas}')
                    return

            pos, lemma = poslemmas[0].split("|")
            if lemma not in lemma_entries:
                lemma_entries[lemma] = item
            else:
                # TODO: also check alt and other t params
                if item.qualifier != lemma_entries[lemma].qualifier:
                    tline.log("removable_form_has_qualifier")
                    return

                if item.params and any(
                        v != lemma_entries[lemma].params.get(k) for k,v in item.params.items()
                        if not isinstance(k, int)):
                    tline.log("removable_form_has_params")
                    return


        if len(lemma_entries) != len(tline.entries):
            tline.log("botfix_consolidate_forms")
            tline.parent.fixes.append("Spanish: reduced adjective forms to common lemma")

            new_entries = []
            for lemma, item in lemma_entries.items():
                item.params[2] = lemma
                item.params = {k:v for k,v in item.params.items() if (not isinstance(k, int) or k < 3)}
                new_entries.append(item)
            tline.entries = new_entries

        elif "m" in seen_genders:
            for item in tline.entries:
                item.params = {k:v for k,v in item.params.items() if (not isinstance(k, int) or k < 3)}

            tline.log("botfix_remove_gendertags")
            tline.parent.fixes.append("Spanish: removed gender tags from adjectives")


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



    def cleanup_tables(self, page_text, title, summary=None):

        if not self.can_handle_page(title):
            return page_text

        if "==Translations==" not in page_text:
            return page_text

        replacements = []
        sections = sectionparser.parse(page_text, title)
        if not sections:
            return page_text

        for section in sections.ifilter_sections(matches="Translations"):
            pos = section.parent.title

            for table in get_tables(section.content_wikilines):

                table = TranslationTable(title, pos, table, log_function=lambda *x: x)

                old_text = str(table)
                self.fixer.cleanup_table(table)
                new_text =  str(table)

                if table.fixes and new_text != old_text:
                    replacements.append((old_text, new_text, table.fixes))

        if replacements:
            all_fixes = []
            for item in replacements:
                old, new, fixes = item
                all_fixes += fixes
                page_text = page_text.replace(old, new)

            if summary is not None:
                summary.append("Translations: " + ", ".join(sorted(set(all_fixes))))
                #replacement._edit_summary = "Translations: expanded {{ttbc}} to language, wrapped entries in {{t-check}} (manually assisted)" #Spanish: reduced forms to common lemma"
                #replacement._edit_summary = "Translations: replaced bare '* Language' with '* Language:'" #Spanish: reduced forms to common lemma"

        return page_text

r"""
ttbc_orig = []
with open("ttbc.orig") as infile:
    for line in infile:
        line = line.strip()
        if ttbc_orig and line == ttbc_orig[-1]:
            print("dup", line)
        ttbc_orig.append(line)

with open("ttbc") as infile:
    for i, line in enumerate(infile):
        line = line.strip()

        match = re.search("{{ttbc\|([^|}]*)", line)
        lang_id = match.group(1)

        for match in re.findall("{{t-check\|([^|}]*)", line):
            if match != lang_id:
                print("mismatch", [match, lang_id], line)

        if line.count("{") != line.count("}"):
            print("{ mismatch", line)

        if line.count("(") != line.count(")"):
            print("( mismatch", line)

        if line.count("[") != line.count("]"):
            print("[ mismatch", line)

        line = T9nFixer.cleanup_ttbc(line)
        ttbc_fixes[ttbc_orig[i]] = line


print("DONE")

#if len(ttbc_orig) != len(set(ttbc_orig)):
#    print("dup lines")
#else:
#    print("no dups")


"""
