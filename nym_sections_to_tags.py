#!/usr/bin/python3
# -*- python-mode -*-

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

import json
import mwparserfromhell
import os
import pywikibot
from pywikibot import xmlreader
import re


class Definition():

    def __init__(self, lang_id, line):
        self.LANG_ID = lang_id
        self._lines = [ line ]

        self.sense_id = ""
        self._dirty = True

        self._problems = {}

    def flag_problem(self, problem, data):
        self._problems[problem] = self._problems.get(problem, []) + [ data ]

    def add(self, line):
        self._dirty = True
        self._lines.append(line)

    def get_nym_target(self, tag_name):
        """
        Return the definition text up to the point where the nym line should be inserted
        """
        # TODO: be smarter
        return self._lines[0]

    def set_sense_id(self, sense_id):
        if self.sense_id and self.sense_id != sense_id:
            self.flag_problem("multi_sense_id", [ self.sense_id, sense_id ])

    def get_sense_id(self):
        return self.sense_id

    def set_sense_id_from_line(self, line):
        wiki = mwparserfromhell.parse(text,skip_style_tags=True)

        for template in wiki.filter_templates(recursive=False):
            if template.name == "senseid":
                if template.get("1") != self.LANG_ID:
                    self.flag_problem("senseid_language_mismatch", line)
                self.set_sense_id(template.get("2"))

    def _parse(self):
        if not self._dirty:
            return

        first_line = True
        for line in self._lines:
            if first_line:
                if line.startswith("# ") or line.startswith("#{"):
                    if "{{senseid" in line:
                        self.set_sense_id(line)
                    continue
                else:
                    self._unhandled_lines = True
                first_line = False
            # TODO: Verify that lines starting with | are part of a multi line template
            elif line.startswith("#:") or line.startswith("#*") or line.startswith("##") or line.startswith("|"):
                continue
            else:
                print("Unexpected in def: ", line)
                self._unhandled_lines = True

        self._dirty = False

    def is_good(self):
        self._parse()
        return self._problems == {}

    def get_problems(self):
        return self._problems.items()


class NymSectionToTag():

    def __init__(self, lang_name, lang_id):
        self.LANG_SECTION=lang_name
        self.LANG_ID=lang_id

    def make_tag(self, name,items):

        params = [ name ]

        lang = items[0][0].get("1")
        params.append(lang)

        idx=0
        for link,qualifier,gloss in items:
            idx+=1

            params.append(link["2"])
            if link.get("3"):
                v = link.get("3")
                params.append( f"alt{idx}={v}" )
            if link.get("tr"):
                v = link.get("tr")
                params.append( f"tr{idx}={v}" )

            if qualifier:
                v = ",".join(map(str,qualifier))
                params.append( f"q{idx}={v}" )

            if gloss:
                self.needs_fix("has_gloss", gloss)
                if qualifier:
                    self.needs_fix("has_gloss_and_qualifier", gloss, qualifier)
                else:
                    params.append( f"q{idx}={gloss}" )

        if "|" in "_".join(params):
            raise ValueError("Item has | character in paramaters", items)

        return "{{" + "|".join(params) + "}}"

    def get_definitions(self, section):
        """
        Parses a section containing a section definition, one or more word headers,
        and an ordered list of definitions under each word header

        Returns a list of Definition objects
        """

        defs = []
        current_def = None
        header_line = True
        for line in section.splitlines():
            line = line.strip()
            if line == "":
                continue

            elif header_line:
                if line.startswith("="):
                    header_line = False
                    continue
                else:
                    self.needs_fix("text_before_header", line)
                    print("Expected header, got:", line)
                    continue

            # Stop if we come to the end of the section or the Category declarations
            elif line == "----" or line.startswith("[[Category:"):
                break

            # Stop searching when we come to another section
            elif line.startswith("=="):
                break

            elif line.startswith("# ") or line.startswith("#{"):
                if current_def is not None:
                    defs.append(current_def)
                current_def = Definition(self.LANG_ID, line)
                continue


            # Word declaration
            elif line.startswith("{{"+self.LANG_ID+"-") or line.startswith("{{head"): # Fix for code folding: }}}}

                # This is the word declaration for the first set of definitions
                if current_def is None and not len(defs):
                    continue

                # Some articles list multiple parts of speech or etymology without breaking them  into sections.
                # If we encounter a new declaration, flag it for manual review
                else:
                    self.needs_fix("multiple_word_declarations_in_def", line)
                    if current_def is not None:
                        defs.append(current_def)
                        current_def = None

            elif current_def is not None:
                current_def.add(line)

            else:
                self.needs_fix("unexpected_text_before_def", line)

        if current_def is not None:
            defs.append(current_def)

        for item in defs:
            for problem,data in item.get_problems():
                self.needs_fix(f"def_{problem}", data)

        return defs


    def parse_word_line(self, line):
        """
        Parses a list of words defined within wiki tags
        If a line has multiple words, they must be comma separated
        Returns a list of tuples
        [ (word, qualifier, gloss) ]
        """

        if line.startswith("*"):
            line = line[1:]
        return [ self.parse_word(text.strip()) for text in line.split(",") ]


    def strip_templates(self, text):

        wiki = mwparserfromhell.parse(text,skip_style_tags=True)

        for template in wiki.filter_templates(recursive=False):
            wiki.remove(template)

        return str(wiki)


    def parse_word(self, text):
        """
        Parses a word defined with [[link]] or {{l}}, {{q}} or (qualifier) and {{gloss}} tags while ignoring {{g}} tags
        Raises an error if unexpected tags or text are found or if an item is defined twice
        """

        # Special handling for "See [[Thesaurus:entry]]." items
        res = re.match(r"See \[\[(Thesaurus:[^\]]+)\]\]\.?$", text)
        if res:
            return( {"1": self.LANG_ID, "2": res.group(1)}, None, None)

        item = self.get_item_from_templates(text)
        item2 = self.get_item_from_text(text)

        res = []

        for a,b in zip(item, item2):
            if a and b:
                self.needs_fix("duplicate_text_and_template", item, item2)

        res = tuple( a if a else b for a,b in zip(item,item2) )

        if not res[0] or res[0] == "":
            raise ValueError("No link found", text)

        return res


    def get_item_from_text(self, text):
        """
        Parse a string containing [[Link]] and (qualifier) text
        Returns a tuple with ( {"1":"LANG_ID", "2": "Link"}, ["qualifier"], None )
        """
        clean_text = self.strip_templates(text).strip()

        link,qualifier,gloss=None,None,None

        pattern = r"\[\[([^\]]+)\]\]"
        res = re.search(pattern, clean_text)
        if res:
            link = { "1": self.LANG_ID, "2": res.group(1) }
            clean_text = re.sub(pattern, "", clean_text, 1)

        pattern = r"\(([^)]+)\)"
        res = re.search(pattern, clean_text)
        if res:
            # Strip out '', ''', '''', etc markups (does not check that they're balanced)
            no_markup = re.sub(r"''*", "", res.group(1))
            qualifier = [ x.strip() for x in no_markup.split(",") ]
            clean_text = re.sub(pattern, "", clean_text, 1)

        res = re.match(r"^\s*$", clean_text)
        if not res:
            self.needs_fix("nym_unexpected_text", clean_text)

        return(link, qualifier, gloss)


    def get_item_from_templates(self, text):

        templates = mwparserfromhell.parse(text).filter_templates(recursive=False)
        link,qualifier,gloss = None,None,None

        for template in templates:

            if template.name in [ "link", "l" ]:
                if template.params[0] != self.LANG_ID:
                    raise ValueError("Word is not in the expected language", text)
                if link:
                    # If there are two or more links, it's often the case of poorly tagged {{l|en|double}} {{l|en|word}}
                    # Join the link text with a space and then flag for manual review
                    self.needs_fix("multi_link", text)
                    link["2"] += " " + str(template.get(2).value)
                else:
                    link = { str(p.name):str(p.value) for p in template.params if str(p.name) in [ "1", "2", "3", "tr" ] }

            elif template.name in [ "qualifier", "qual", "q", "i" ]:
                if qualifier:
                    self.needs_fix("multi_qualifier", text)
                qualifier = [ p.value for p in template.params if p.can_hide_key ]

            elif template.name in [ "gloss", "gl" ]:
                if gloss:
                    self.needs_fix("multi_gloss", text)
                if len(template.params) != 1:
                    raise ValueError(f"Unexpected number of parameters for {template.name}", template.params)
                gloss = str(template.get(1))

            # Ignore {{g}} template
            elif template.name in [ "g" ]:
                continue

            else:
                self.needs_fix("unknown_template", text)



        return(link, qualifier, gloss)


    def parse_section_items(self, section):
        """
        Parses a section containing a list of words and optional qualifiers and gloss
        Returns a dict of { sense: [ (word, qualifier, gloss) ] }
        """

        all_items = {}
        sense = ""

        header_line = True
        for line in section.splitlines():
            line = line.strip()
            if line == "":
                continue

            if header_line:
                header_line=False
                continue

            if line == "----" or line.startswith("[[Category:"):
                break

            res = re.match(r"\*\s*{{s(ense)?\|[^{}]+}}\s*", line)
            if res:
                text = res.group(0)
                wiki = mwparserfromhell.parse(text,skip_style_tags=True)
                template = wiki.filter_templates(recursive=False)[0]
                sense = str(template.get("1"))

                # strip the sense tag
                remove = re.escape(res.group(0))
                line = re.sub(remove, "* ", line)


            all_items[sense] = all_items.get(sense,[]) + self.parse_word_line(line)

        return all_items


    def get_section_title(self, section):
        res = re.match(r"\s*=+([^=]+)=+", str(section))
        if not res:
            print("failed matching section title", section)
            return
        return res.group(1)

        # Alternately this might work, no idea which is more efficient
        # heading = section.filter_headings()[0]


    def get_word_sections(self, wiki, level):
        """
        Get all known part of speech sections at specified header level
        """

        WORD_TYPES = ( "Noun","Verb","Adjective","Adverb","Interjection","Article","Proper noun",
                "Preposition","Numeral","Cardinal number","Ordinal number","Number","Acronym",
                "Determiner","Phrase","Suffix","Pronoun","Conjunction","Provecb","Contradiction",
                "Prefix","Letter","Abbreviation","Initialism","Idiom","Affix","Adverbial phrase",
                "Participle")
        all_sections =  wiki.get_sections([level])

        sections = [ section for section in all_sections if self.get_section_title(section) in WORD_TYPES ]

        if not len(sections):
            titles = [ self.get_section_title(section) for section in all_sections ]
            raise ValueError("No word sections", titles)

        return sections


    def get_section_end_pos(self, text, start_pos=0):
        # Sections may be terminated by "[[Category]]" tags or a "----" separator,
        # or nothing, if it's the last section on the page
        end_str = [ "\n[[Category", "\n----\n" ]
        end_pos = None
        for ending in end_str:
            found_pos = text.find(ending, start_pos)
            if found_pos != -1:
                end_pos = found_pos
                break

        return end_pos


    def get_language_entry(self, text):
        """
        Return the body text of the language entry
        """

        start_str = f"\n=={self.LANG_SECTION}==\n"
        start_pos = text.find(start_str)
        if start_pos < 0:
            return
        start_pos +=1

        end_pos = self.get_section_end_pos(text, start_pos)

        text = text[start_pos:end_pos]

        # This shouldn't happen, but it does
        res = re.search(r"\n==[^=]+==\n", text[len(start_str):])
        if res:
            raise ValueError(f"WARN: Unexpected level 2 section in {self.LANG_SECTION} entry", res.group(0))

        return text


    def nym_section_to_tag(self, text, section_title, tag_name, page=None):

        header_level = 3
        header_tag = "=" * header_level
        if not f"{header_tag}{section_title}{header_tag}" in text:
            return

        wiki = mwparserfromhell.parse(text,skip_style_tags=True)

        try:
            word_sections = self.get_word_sections(wiki, header_level)
        except ValueError as err:
            #print(f"WARN: {page}: ", err.args)
            titles_searched = err.args[1]
            word_sections = []

        if not len(word_sections):
            # If words weren't found at level 3, they're probably at level 4 inside an Entymology block
            try:
                header_level += 1
                word_sections = self.get_word_sections(wiki, header_level)
            except ValueError as err:
                print(f"WARN: {page}: ", err.args[0], titles_searched + err.args[1])
                print(text)
                word_sections = []
                exit()

            if not len(word_sections):
                raise ValueError(f"WARN: no word types found in {page}", text)

        if len(wiki.get_sections([header_level],section_title)):
            print(f"FIXME: {page} {section_title} found at level {header_level} (expected level {header_level+1})")

        for section in word_sections:
            pos = self.get_section_title(section)
            if not pos:
                print(f"WARN: {page} cannot get section name")

            nym_sections = section.get_sections([header_level+1], section_title)

            if not len(nym_sections):
                continue
            if len(nym_sections) > 1:
                print(f"FIXME: {page} has too {len(nym_sections)} {section_title} sections (1 expected)")
                continue

            nym_section = nym_sections[0] if len(nym_sections) else None

            try:
                if "{{"+tag_name in section:
                    self.needs_fix("has_existing_tag")

                defs = self.get_definitions(section)
            except ValueError as err:
                print(f"WARN: {page} ({pos}): ", err.args)
                continue

            if not len(defs):
                print(f"WARN: {page} ({pos}) has no definitions")
                continue

            try:
                nyms = self.parse_section_items(nym_section) if nym_section else []
            except ValueError as err:
                #print(defs)
                #print(f"WARN: {page} ({pos}): ", err.args)
                continue

            if len(nyms.keys()) and "{{" + tag_name in section: # fix vim code folding: }}
                print(f"FIXME: {page} ({pos}) has '{tag_name}' template and {section_title} section")
                continue

            if not len(nyms.keys()):
                continue


            sense_def_list = [d.get_sense_id() for d in defs]
            sense_def = { d.get_sense_id():d for d in defs }
            if len(sense_def.keys()) != len(sense_def_list):
                self.needs_fix("duplicate_sense_ids")

#            if len(defs) == 1:
#                self.needs_fix("single_def")
#            else:
#                self.needs_fix("multi_def")


            for nym_sense in nyms.keys():
                def_matches = sense_def_list.count(nym_sense)
                if def_matches:
                    if def_matches>1:
                        self.needs_fix("sense_matches_multiple_defs")

                    target_def = sense_def[nym_sense]
                else:
                    # assigned unmatched senses to the first def senseless def
                    # or the first declared def if they all have senseids
                    self.needs_fix("unmatched_sense")
                    if "" in sense_def:
                        target_def = sense_def[""]
                    else:
                        target_def = sense_def[sense_def_list[0]]

                match_line = target_def.get_nym_target(tag_name)
                nym_tag = self.make_tag(tag_name, nyms[nym_sense])

                # Use a placeholder when replacing/removing sections so we can cleanup/condense
                # and preceeding/following newline characters
                placeholder = "==!!REPLACEME!!=="
                keep_pos = self.get_section_end_pos(nym_section)
                if keep_pos:
                    wiki.replace(nym_section, nym_section[keep_pos:])
                else:
                    wiki.replace(nym_section, f"\n{placeholder}\n\n")

                # Do this after the section replacement, otherwise mwparser loses it on occasion
                section.insert_after(match_line, f"\n#: {nym_tag}")

            return re.sub(fr"\n*{placeholder}\n*(?=\n\n=|$)", "", str(wiki))

    def needs_fix(self, name, *params):
        self._flagged[name] = self._flagged.get(name, []) + [params]

    def run_fix(self, text, tools=[], page_title=""):
        """
        *page_title* is only used for error messages, and only available when run directly
        Only return fixes that can be fixed with the list of *tools* provided
        """
        self._flagged = {}

        new_text = text
        for nym_name, nym_tag in [ ["Troponyms", "troponyms"], ["Holonyms", "holonyms"], ["Meronyms", "meronyms"], ["Hyponyms", "hypo"], ["Hyperyms", "hyper"], ["Antonyms", "ant"], ["Synonyms", "syn"] ]:
            prev_text = new_text
            new_text = self.nym_section_to_tag(prev_text, nym_name, nym_tag, page_title)
            if not new_text:
                new_text = prev_text

        if new_text == text:
            return text

#        for fix in [ "unknown_template" ]:
#            if fix in self._flagged:
#                print(f"{page_title}: {fix} {self._flagged[fix]}")

        missing_fixes = set(self._flagged.keys()).difference(tools)
        if missing_fixes:
            print(f'{page_title} needs {", ".join(sorted(missing_fixes))}')
            return text

        return new_text


def main():

    import argparse

    parser = argparse.ArgumentParser(description='Convert *nym sections to tags.')
    parser.add_argument('--xml', help="XML file to load", required=True)
    parser.add_argument('--lang-id', help="Language id", required=True)
    parser.add_argument('--lang-section', help="Language name", required=True)
    parser.add_argument('--pre-file', help="Destination file for unchanged articles (default: pre.txt)", default="pre.txt")
    parser.add_argument('--post-file', help="Destination file for changed articles (default: post.txt)", default="post.txt")
    parser.add_argument('--fix', action='append', help="Fix issues with the specified flag (Can be specified multiple times)", default=[])
    parser.add_argument('--article-limit', type=int, help="Limit processing to first N articles", default=[])
    parser.add_argument('--fix-limit', type=int, help="Limit processing to first N fixable articles", default=[])

    args = parser.parse_args()

    if not os.path.isfile(args.xml):
        raise FileNotFoundError(f"Cannot open: {args.xml}")

    dump = xmlreader.XmlDump(args.xml)
    parser = dump.parse()
    site = pywikibot.Site()

    fixer = NymSectionToTag(args.lang_section, args.lang_id)

    prefile = open(args.pre_file, "w")
    postfile = open(args.post_file, "w")

    all_sections = set()
    count=0
    lang_count=0
    fixable=0

    for entry in parser:
        if args.article_limit and count>args.article_limit:
            break
        count+=1

        if ":" in entry.title:
            continue

        try:
            lang_entry = fixer.get_language_entry(entry.text)
        except ValueError as err:
            #print(f"WARN: {entry.title}: ", err.args)
            continue

        if not lang_entry:
            continue

        lang_count += 1

        fixed = fixer.run_fix(lang_entry, args.fix, entry.title)
        if fixed == lang_entry:
            continue

        prefile.write(f"\nPage: {entry.title}\n")
        prefile.write(lang_entry)

        postfile.write(f"\nPage: {entry.title}\n")
        postfile.write(fixed)

        fixable += 1
        if args.fix_limit and fixable>=args.fix_limit:
            break

    print(f"Total articles: {count}")
    print(f"Total in {args.lang_section}: {lang_count}")
    print(f"Total fixable: {fixable}")

    prefile.close()
    postfile.close()


if __name__ == '__main__':
    main()
