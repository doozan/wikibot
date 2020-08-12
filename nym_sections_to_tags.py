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
This will search all entries with a specified language with (Syn|Ant|Homo|Hyper)nym categories
For all parts of speech having exactly one definition and containing a *nym category,
the category will be converted into an appropriate tag and added to the definition
"""

import json
import mwparserfromhell
import os
import pywikibot
from pywikibot import xmlreader
import re

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
                raise ValueError("Item has gloss, needs manual review", link, qualifier, gloss)
#                params.append( f"q{idx}={gloss}" )

        if "|" in "_".join(params):
            raise ValueError("Item has | character in paramaters", items)

        return "{{" + "|".join(params) + "}}"

    def get_definition_lines(self, section):
        """
        Returns a list of all lines beginning with "# " in a section
        Skips expected sub-lines starting with "#*" or "##"
        Raises an error if it encounters any unexpected lines
        """

        defs = []
        header_line = True
        for line in section.splitlines():
            if header_line:
                header_line = False
                declaration_line = True
                continue

            line = line.strip()
            if line == "":
                continue

            # Stop if we come to the end of the section or the Category declarations
            if line == "----" or line.startswith("[[Category:"):
                break

            if declaration_line:
                declaration_line = False
                continue

            # Stop searching when we come to another section
            if line.startswith("==="):
                break

            if line.startswith("# ") or line.startswith("#{"):
                defs.append(line)

            # Line modifiers are allowed after the first def, but fail if there's an existing syn tag
            elif len(defs):
                if line.startswith("#:") or line.startswith("#*") or line.startswith("##"): # or line.startswith("#|passage"):
                    continue
                elif line.startswith("{{es-") or line.startswith("{{head"): # Fix for code folding: }}}}
                    raise ValueError("Multiple word declarations found", line)
                else:
                    raise ValueError("Unexpected definition subline", line)

            # Fail if we encounter an unexpected item
            else:
                raise ValueError("Unexpected definition line", line)

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
                raise ValueError("Duplicated value in template and text", item, item2)

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
            raise ValueError("Unexpected text found", clean_text)

        return(link, qualifier, gloss)


    def get_item_from_templates(self, text):

        templates = mwparserfromhell.parse(text).filter_templates(recursive=False)
        link,qualifier,gloss = None,None,None

        for template in templates:

            if template.name in [ "link", "l" ]:
                if template.params[0] != self.LANG_ID:
                    raise ValueError("Word is not in the expected language", text)
                if link:
                    raise ValueError("More than one {{link}} detected", text)
                link = { str(p.name):str(p.value) for p in template.params if str(p.name) in [ "1", "2", "3", "tr" ] }

            elif template.name in [ "qualifier", "qual", "q", "i" ]:
                if qualifier:
                    raise ValueError("More than one {{qualifier}} detected", text)
                qualifier = [ p.value for p in template.params if p.can_hide_key ]

            elif template.name in [ "gloss", "gl" ]:
                if qualifier:
                    raise ValueError("More than one {{gloss}} detected", text)
                if len(template.params) != 1:
                    raise ValueError(f"Unexpected number of parameters for {template.name}", template.params)
                gloss = str(template.params[0])

            # Ignore {{g}} template
            elif template.name in [ "g" ]:
                continue

            # TODO: Manually verify that sense matches the single def
            elif template.name == "sense":
                raise ValueError(f"Sense tag unexpected with single definition", text)

            else:
                raise ValueError(f"Unexpected template", template)

        return(link, qualifier, gloss)


    def parse_section_items(self, section):
        """
        Parses a section containing a list of words and optional qualifiers and gloss
        Returns a list of tuples
        [ (word, qualifier, gloss) ]
        Returns None if an unexpected item is found
        """

        all_items = []

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

            all_items += self.parse_word_line(line)

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


    def get_language_entry(self, text):
        """
        Return the full text of the requested *language entry
        """

        start_str = f"\n=={self.LANG_SECTION}==\n"
        end_str="\n----\n"

        start_pos = text.find(start_str)
        if start_pos < 0:
            return
        start_pos +=1

        # Sections are terminated by the end_str, unless its the last section on the page
        end_pos = text.find(end_str, start_pos)
        end_pos = None if end_pos < 0 else end_pos+len(end_str)

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
            print(f"FIXME: {page} {section_title} found at level {header_level} (exepected level {header_level+1})")

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
                defs = self.get_definition_lines(section)
            except ValueError as err:
                print(f"WARN: {page} ({pos}): ", err.args)
                continue

            # We only want to handle single definition words
            if not len(defs) == 1:
                continue
            def_line = defs[0]

            try:
                nyms = self.parse_section_items(nym_section) if nym_section else []
            except ValueError as err:
                #print(defs)
                #print(f"WARN: {page} ({pos}): ", err.args)
                continue

            if len(nyms) and "{{" + tag_name in section: # fix vim code folding: }}
                print("NOTICE: Definition has '{nym}' template and {section_title} section")
                continue

            if not len(nyms):
                continue

            try:
                nym_tag = self.make_tag(tag_name, nyms) if len(nyms) else ""
            except ValueError as err:
                print(f"WARN: {page} ({pos}): ", err.args)
                continue

            if not nym_tag or nym_tag == "":
                continue

            # If the section is at the end of the page, it may contain
            # [[Category]] tags or the "----" ending, which must be preserved
            start_pos = nym_section.find("[[Category")
            if start_pos<0:
                start_pos = nym_section.find("----")
            if start_pos<0:
                wiki.remove(nym_section)
            else:
                wiki.replace(nym_section, nym_section[start_pos:])

            # For some reason, it's important do add the line after removing the sections.
            # When done in the other order, the added line may be removed
            section.insert_after(def_line, f"\n#: {nym_tag}")

            return str(wiki)


    def run_fix(self, text, title=None):

        new_text = text
        for nym_name, nym_tag in [ ["Troponyms", "troponyms"], ["Holonyms", "holonyms"], ["Meronyms", "meronyms"], ["Hyponyms", "hyper"], ["Hyperyms", "hypo"], ["Antonyms", "ant"], ["Synonyms", "syn"] ]:
            prev_text = new_text
            new_text = self.nym_section_to_tag(prev_text, nym_name, nym_tag, title)
            if not new_text:
                new_text = prev_text

#        if new_text != text:
#            print("Changes")
        return new_text


def main():

    import argparse

    parser = argparse.ArgumentParser(description='Convert *nym sections to tags.')
    parser.add_argument('--xml', help="XML file to load", required=True)
    parser.add_argument('--lang-id', help="Language id", required=True)
    parser.add_argument('--lang-section', help="Language name", required=True)
    parser.add_argument('--pre-file', help="Destination file for unchanged articles (default: pre.txt)", default="pre.txt")
    parser.add_argument('--post-file', help="Destination file for changed articles (default: post.txt)", default="post.txt")

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
    lang_fixable=0

    for entry in parser:
        if count>=10000:
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

        fixed = fixer.run_fix(lang_entry, entry.title)
        if fixed == lang_entry:
            continue

        lang_fixable += 1

        prefile.write(f"\nPage: {entry.title}\n")
        prefile.write(lang_entry)

        postfile.write(f"\nPage: {entry.title}\n")
        postfile.write(fixed)


    print(f"Total articles: {count}")
    print(f"Total in {args.lang_section}: {lang_count}")
    print(f"Total fixes: {lang_fixable}")

    prefile.close()
    postfile.close()


if __name__ == '__main__':
    main()
