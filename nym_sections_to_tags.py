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

# The first tag listed will be used when creating nym tags
# Nyms will be inserted into definitions according to the order here
# If you don't want to process a certain nym, don't comment it out here,
# instead, change the list in run_fix()
_nyms = {
    "Synonyms": [ "syn", "synonyms"],
    "Antonyms": [ "ant", "antonyms"],
    "Hyperyms": [ "hyper", "hypernyms" ],
    "Hyponyms": [ "hypo", "hyponyms"],
    "Meronyms": [ "meronyms" ],
    "Holonyms": [ "holonyms" ],
    "Troponyms": [ "troponyms" ],
}

_tag_to_nym = { k:v for v,tags in _nyms.items() for k in tags }
_all_nym_tags = _tag_to_nym.keys()
_nym_order = list(_nyms.keys())


# Consider the presense of any non-whitespace or separator to be text
def has_text(text):
    return re.search(r"[^\s,;]", text)


def get_nest_depth(text, start_depth=0):
    """
    Returns the depth of nested templates at the end of the given line

    zero }} zero {{ one {{ two {{ three }} two }} one }} zero }} zero
    """

    if start_depth<0:
        raise ValueError("start_level cannot be negative")

    depth = start_depth

    first=True
    for t in text.split("{{"):
        if first:
            first=False
            if not depth:
                continue
        else:
            depth+=1

        depth = max(0, depth - t.count("}}"))

    return depth

def template_aware_split(text, splitter):

    results = []
    nested = []
    nested_depth = 0

    for item in text.split(splitter):
        if nested_depth:
            nested.append(item)
            nested_depth = get_nest_depth(item, nested_depth)
            if nested_depth:
                continue
            else:
                item = "".join(nested)
                nested = []

        else:
            nested_depth = get_nest_depth(item, nested_depth)
            if nested_depth:
                nested = [item]
                continue

        results.append(item)

    if nested_depth:
        results.append(item)
        raise ValueError("Open template", text)
    # TODO: warn here
#        self.needs_fix("nym_has_open_template", nested[0])


    return results


class Definition():

    def __init__(self, lang_id, line):
        self.LANG_ID = lang_id
        self._lines = []

        self.senseid = ""
        self.senses = []

        self._problems = {}

        self._nested_depth = 0
        self._open = []

        # The index of the line containing the nym declaration { NymName: idx }
        self._nymidx = {}

        self.declaration_idx = -1

        self.add(line)


    def flag_problem(self, problem, data):
        #print(problem, data)
        self._problems[problem] = self._problems.get(problem, []) + [ data ]


    def remove_problem(self, problem):
        del self._problems[problem]


    def start_open_line(self, line):
        self.flag_problem("has_open_template",line)
        self._open = [ line ]
        return


    def continue_open_line(self, line):
        self._open.append(line)
        return


    def close_open_line(self, line):
        self.remove_problem("has_open_template")
        self.process("".join(self._open))
        return


    def add(self, line):
        self._lines.append(line)

        if line == "":
            return

        if self._nested_depth:
            self._nested_depth = get_nest_depth(line, self._nested_depth)
            if not self._nested_depth:
                self.close_open_line(line)
            else:
                self.continue_open_line(line)
            return

        self._nested_depth = get_nest_depth(line, self._nested_depth)
        if self._nested_depth:
            self.start_open_line(line)
            return

        self.process(line)


    def process(self, line):

        # Don't process anything that comes before the "# [[def]]" line
        # But flag it as unhandled
        if self.declaration_idx<0:
            if line.startswith("# ") or line.startswith("#{"):
                self.parse_hash(line)
            else:
                self.flag_problem("line_before_def", line)

        # Index any existing nym tags
        elif line.startswith("#:"):
            self.parse_hashcolon(line)

        elif line.startswith("#*"):
            self.parse_hashstar(line)

        elif line.startswith("##"):
            self.parse_hashhash(line)

        else:
            print("Unexpected text in def: ", line)
            self.flag_problem("unexpected_text", line)


    def strip_to_text(self, markup):

        stripped = markup

        # Remove {{templates}}
        stripped = re.sub(r"{{[^{}]+}}", "", stripped)

        # Remove (things in parentheseis)
        stripped = re.sub(r"\([^\(\)]+\)", "", stripped)

        # [[brackets]] => brackets
        stripped = re.sub(r"\[\[([^[\]]+)\]\]", r"\1", stripped)

        return stripped.strip()


    def parse_hash(self, line):
        self.declaration_idx = len(self._lines)-1

        stripped = self.strip_to_text(line[1:])

        # assume ; is used to separate senses, we only want the first sense
        defs, *junk = stripped.partition(";")
        self.senses = [ d.strip() for d in defs.split(",") ]

        if "{{senseid" in line: # folding fix }}
            self.parse_senseid(line)


    def parse_hashcolon(self, line):
        idx = len(self._lines)-1

        res = re.match(r"#:\s*{{(" + "|".join(_all_nym_tags) + r")\|[^{}]+}}", line)
        if res:
            nym_type = _tag_to_nym[res.group(1)]
            if nym_type in self._nymidx:
                self.flag_problem("duplicate_nym_defs", line)

            self._nymidx[nym_type] = idx
            return

        self.flag_problem("hashcolon_is_not_nym", line)


    def parse_hashstar(self, line):
        return


    def parse_hashhash(self, line):
        return


    def has_nym(self, nym_name):
        assert nym_name in _nyms
        return nym_name in self._nymidx


    def get_nym_target(self, tag_name):
        """
        Return the definition text up to the point where the nym line should be inserted
        """

        target = _tag_to_nym[tag_name]
        max_order = _nym_order.index(target)

        target_idx = -1
        idx = -1
        for nym,idx in self._nymidx.items():
            if _nym_order.index(nym)>max_order:
                break
            target_idx=idx

        if target_idx<0:
            target_idx = self.declaration_idx

        return "\n".join(self._lines[:target_idx+1])


    # As of enwiki 2020-08-01 dump, senseid is only used in the Spanish section to link to wikidata sources (Q######)
    def set_senseid(self, senseid):

        if self.senseid and self.senseid != senseid:
            self.flag_problem("multi_senseid", [ self.senseid, senseid ])

        self.senseid = senseid


    def get_senseid(self):
        return self.senseid


    def has_senseid(self, senseid):
        return self.senseid == senseid


    def has_sense(self, sense):
        for sense in sense.split("|"):
            if not sense in self.senses:
                return False
        return True


    def parse_senseid(self, text):
        wiki = mwparserfromhell.parse(text,skip_style_tags=True)

        for template in wiki.filter_templates(recursive=False):
            if template.name == "senseid":
                if template.get("1") == self.LANG_ID:
                    self.set_senseid(str(template.get("2")))
                else:
                    self.flag_problem("senseid_lang_mismatch", text)


    def is_good(self):
        return self._problems == {}


    def get_problems(self):
        return self._problems.items()


class NymSectionToTag():

    def __init__(self, lang_name, lang_id, debug=()):
        self.LANG_SECTION=lang_name
        self.LANG_ID=lang_id
        self._flagged = {}
        self._stats = {}
        self._debug_fix = set(debug)


    def make_tag(self, name, items):

        params = [ name ]

        params.append(self.LANG_ID)

        idx=0
        for link,qualifier,gloss in items:

            if not link:
                self.needs_fix("missing_link")
                return None

            idx+=1

            params.append(link["2"])
            if link.get("3"):
                v = link.get("3")
                params.append( f"alt{idx}={v}" )
            if link.get("tr"):
                v = link.get("tr")
                params.append( f"tr{idx}={v}" )

            if link.get("4") or link.get("t"):
                v = link.get("4", link.get("t"))
                # TODO: Handle this as gloss?
                self.needs_fix("link_has_param4", link)

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

        tag = "{{" + "|".join(params) + "}}"

        if len(tag)>80:
            self.needs_fix("long_tag")

        return tag


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
                if current_def:
                    current_def.add("")
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
            elif line.startswith("{{"+self.LANG_ID+"-") or line.startswith("{{head"): # fix folding }}}}

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

        return [ self.parse_word(text.strip()) for text in template_aware_split(line, ",") ]

    def extract_templates_and_patterns(self, templates, patterns, text):

        response = { "templates": [], "patterns": [], "text": "" }

        wiki = mwparserfromhell.parse(text,skip_style_tags=True)

        for template in wiki.filter_templates(recursive=False):
            if template.name in templates:
                response["templates"].append(template)
                wiki.remove(template)

        text = str(wiki)
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if len(matches):
                response["patterns"].append(matches)
                text = re.sub(pattern, "", text)

        response["text"] = text
        return response

    def stripformat(self, text):

        text = text.strip()

        newtext = re.sub(r"^\[+(.*?)\]+$", r"\1", text)
        text = newtext.strip() if newtext else text

        newtext = re.sub(r"^'+(.*?)'+$", r"\1", text)
        text = newtext.strip() if newtext else text

        newtext = re.sub(r'^\"+(.*?)\"+$', r"\1", text)
        text = newtext.strip() if newtext else text

        return text.strip()

    def extract_qualifier(self, text):
        res = self.extract_templates_and_patterns( ["q","qualifier"], [r"\(([^)]*)\)"], text)
        q = []

        if len(res["templates"])>1:
            self.needs_fix("qualifier_multiple_templates")

        if len(res["patterns"])>1:
            self.needs_fix("qualifier_multiple_patterns")

        if len(res["templates"]) and len(res["patterns"]):
            self.needs_fix("qualifier_text_and_template")

        for item in res["templates"]:
            for x in item.params:
                q.append(str(x))

        q += [ self.stripformat(x) for items in res["patterns"] for item in items for x in item.split(",") ]

        if "|" in "_".join(q):
            self.needs_fix("qualifier_has_bar", text)
            q = []

        return (q, res["text"])


    def extract_gloss(self, text):
        res = self.extract_templates_and_patterns( ["g","gloss"], [], text)
        g = []
        for item in res["templates"]:
            g += map(str, item.params)

        return (g, res["text"])


    def get_link(self, text):

        links = []
        wiki = mwparserfromhell.parse(text,skip_style_tags=True)

        templates = wiki.filter_templates(recursive=False)
        for template in templates:
            if template.name in ["l", "link"]:
                if template.get("1") != self.LANG_ID:
                    self.needs_fix("link_wrong_lang")
                links.append(template)

            else:
                self.needs_fix("link_unexpected_template", text)

            wiki.remove(template)

        text_outside_templates = str(wiki)
        has_text_outside_templates = has_text(text_outside_templates)

        if len(links) == 1 and not has_text_outside_templates:
            return { p.name.strip():str(p) for p in links[0].params if p.name in ["1","2","3","4","t","tr"] }

        if len(links)>2:
            self.needs_fix("link_multiple_templates")

        wiki = mwparserfromhell.parse(text,skip_style_tags=True)
        for template in wiki.filter_templates(recursive=False):
            if template.name in ["l", "link"]:
                if template.has("3") and template.get("3") != "":
                    self.needs_fix("link_has_param_3", str(template))
                if template.has("4") and template.get("4") != "":
                    self.needs_fix("link_has_param_4", str(template))
                if template.has("t") and template.get("t") != "":
                    self.needs_fix("link_has_param_t", str(template))
                name = template.get("2")
                wiki.replace(template, name)
            else:
                wiki.remove(template)
            text == wiki

        text = re.sub(r"\s+", " ", str(wiki)).strip()

        # Replace "[[word|fancy word]]" with "word"
        orig_text = text
        remaining_text = text_outside_templates
        for match in re.findall(r"\[\[[^[\]]+\]\]", text):
            target = re.escape(match)
            replacement = match[2:].strip("]]").split("|")[0]
            text = re.sub(target, replacement, text)
            remaining_text = re.sub(target, "", remaining_text)

        has_bracketed_text = (text != orig_text)
        has_text_links = has_text(remaining_text)

        sources = []
        if len(links):
            sources.append("template")
        if has_bracketed_text:
            sources.append("brackets")
        if has_text_links:
            sources.append("text")
        if len(sources) > 1:
            self.needs_fix("link_has_" + "_and_".join(sources))

        text = " ".join([ self.stripformat(x) for x in text.split(" ") ])
        if "|" in text:
            self.needs_fix("link_has_pipe", text)
            text = text.split("|",1)[0]

        if text == "":
            return None

        return {"1": self.LANG_ID, "2": text}


    def parse_word(self, text):
        """
        Parses a word defined with [[link]] or {{l}}, {{q}} or (qualifier) and {{gloss}} tags while ignoring {{g}} tags
        Raises an error if unexpected tags or text are found or if an item is defined twice
        """

        # Special handling for "See [[Thesaurus:entry]]." items
        res = re.match(r"See \[\[(Thesaurus:[^\]]+)\]\]\.?$", text)
        if res:
            return( {"1": self.LANG_ID, "2": res.group(1)}, None, None)


        # TODO: Extract gloss from param 4/t of {{link}} template?
        gloss,text = self.extract_gloss(text)
        gloss = " ".join(gloss) if len(gloss) else None

        qualifiers,text = self.extract_qualifier(text)
        qualifiers = qualifiers if len(qualifiers) else None

        link = self.get_link(text)

        if not link or link == {}:
            self.needs_fix("missing_link", text)

        return (link, qualifiers, gloss)


    def parse_section_items(self, section):
        """
        Parses a section containing a list of words and optional qualifiers and gloss
        Returns a dict of { "sense1[|sense2|...]": [ (word, qualifier, gloss), ... ] }
        """

        all_items = {}
        sense = ""

        header_line = True
        for line in template_aware_split(section, "\n"):
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
                sense = "|".join(map(str, template.params))

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

#        if not len(sections):
#            titles = [ self.get_section_title(section) for section in all_sections ]
#            raise ValueError("No word sections", titles)

        return [ section for section in all_sections if self.get_section_title(section) in WORD_TYPES ]


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
            return
            # raise ValueError(f"WARN: Unexpected level 2 section in {self.LANG_SECTION} entry", res.group(0))

        return text


    def replace_nym_section_with_tag(self, text, nym_title, nym_tag, page=None):

        header_level = 3
        header_tag = "=" * header_level
        if not f"{header_tag}{nym_title}{header_tag}" in text:
            return

        wiki = mwparserfromhell.parse(text,skip_style_tags=True)

        replacements = []

        word_sections = self.get_word_sections(wiki, header_level)
        if not len(word_sections):
            # If words weren't found at the expected level, they're probably a level deeper inside an Entymology block
            header_level += 1
            word_sections = self.get_word_sections(wiki, header_level)

            if not len(word_sections):
                #raise ValueError(f"WARN: no word types found in {page}", text)
                return

        if len(wiki.get_sections([header_level],nym_title)):
#            print(f"FIXME: {page} {nym_title} found at level {header_level} (expected level {header_level+1})")
            self.needs_fix("has_nym_section_at_word_level")

        for section in word_sections:
            pos = self.get_section_title(section)
            if not pos:
                print(f"WARN: {page} cannot get section name")

            nym_sections = section.get_sections([header_level+1], nym_title)
            if not len(nym_sections):
                nym_sections = wiki.get_sections([header_level], nym_title)
                if not len(nym_sections):
                    continue
                self.needs_fix("use_nym_section_from_word_level")


            if len(nym_sections) > 1:
                self.needs_fix("duplicate_nym_sections")

            defs = self.get_definitions(section)
            if not len(defs):
                self.needs_fix("no_defs", pos)
                continue

            all_senseid = [d for d in defs if d.get_senseid() != ""]
            if len(all_senseid) != len(set(all_senseid)):
                self.needs_fix("duplicate_senseid")

            for nym_section in nym_sections:
                new_replacements = self.get_nyms_to_defs_replacements(nym_section, nym_title, nym_tag, defs)

                if not len(new_replacements):
                    print(f"WARN: {page} ({pos}) ({nym_section}) has no items")

                # TODO: Check defs instead of searching for tag directly
                if "{{" + nym_tag in section: # fix folding }}
                    self.needs_fix("nym_section_and_tag")

                replacements += new_replacements


        new_text = str(wiki)

        # Use an intermediary placeholder when removing entire sections so we can cleanup/condense newlines
        removed_holder = "==!!REMOVEME!!=="
        for old,new in replacements:
            if new == "":
                new = f"\n\n{removed_holder}\n\n"
            new_text = re.sub(old,new,new_text)

        return re.sub(fr"\n\s*{removed_holder}\s*(?=\n=|\n\[\[Category|\n----|$)", "\n", new_text)


    def get_nyms_to_defs_replacements(self, nym_section, nym_title, nym_tag, defs):

        replacements = []

        nyms = self.parse_section_items(nym_section)
        if not len(nyms.keys()):
            return []

        # The nym lines are appended after the matching definition
        # If multiple nym lines match the same definition, each new line will be
        # appended after the definition, above any lines that were previously appended
        # Process the nyms in reverse order to preserve their original order when appended
        nym_list = list(nyms.keys())
        nym_list.reverse()

        for nym_sense in nym_list:

            target_def = self.get_nym_target_def(nym_sense, defs)
            if target_def.has_nym(nym_title):
                self.needs_fix("has_existing_tag")

            def_target = target_def.get_nym_target(nym_tag)
            nym_line = self.make_tag(nym_tag, nyms[nym_sense])
            if not nym_line:
                self.needs_fix("make_tag_failed")
                continue

            # Use a placeholder when replacing/removing sections so we can cleanup/condense
            # any preceeding/following newline characters
            keep_pos = self.get_section_end_pos(nym_section)

            # Buffer all replacementsruntil the end so mwparser doesn't get confused
            if keep_pos:
                replacements.append([re.escape(str(nym_section)), nym_section[keep_pos:]])
            else:
                replacements.append([re.escape(str(nym_section)), ""])

            replacements.append([re.escape(def_target), fr"{def_target}\n#: {nym_line}"])

            # Do this after the section replacement, otherwise mwparser loses it on occasion
#            section.insert_after(match_line, f"\n#: {nym_line}")

        return replacements


    def get_nym_target_def(self, nym_sense, defs):
        """
        Select the best target definition from *defs* for *nym_sense*
        Returns matches definitions in the following order:
            nym_sense == def.senseid
            nym_sense == def.first_word
            nym_sense in def.words

        If none of the above match, return the first definition
        """
        if nym_sense == "":
            if len(defs) > 1:
                self.needs_fix("sense_matches_multiple_defs")
            return defs[0]

        target_def = self.get_def_matching_senseid(nym_sense, defs)
        if target_def:
            self.needs_fix("automatch_senseid")
        else:
            target_def = self.get_def_matching_sense(nym_sense, defs)
            if target_def:
                 self.needs_fix("automatch_sense")

        if not target_def:
            target_def = defs[0]
            self.needs_fix("unmatched_sense")

        return target_def


    def get_def_matching_senseid(self, nym_sense, defs):

        matches = [ d for d in defs if d.has_senseid(nym_sense) ]
        if not len(matches):
            return

        self.needs_fix("automatch_senseid")
        if len(matches) > 1:
            self.needs_fix("sense_matches_multiple_defs")

        return matches[0]


    def get_def_matching_sense(self, nym_sense, defs):

        matches = [ d for d in defs if d.has_sense(nym_sense) ]
        if not len(matches):
            return

        self.needs_fix("automatch_sense")
        if len(matches) > 1:
            self.needs_fix("sense_matches_multiple_defs")

        return matches[0]


    def needs_fix(self, name, *params):
        if name in self._debug_fix:
            print(f"{self._page} needs {name}: {params}")
        self._flagged[name] = self._flagged.get(name, []) + [params]


    def run_fix(self, text, tools=[], page_title=""):
        """
        *page_title* is only used for error messages, and only available when run directly
        Only return fixes that can be fixed with the list of *tools* provided
        """
        self._flagged = {}
        self._page = page_title

        new_text = text
        for nym_name, nym_tags in _nyms.items():
            nym_tag = nym_tags[0]
            prev_text = new_text
            new_text = self.replace_nym_section_with_tag(prev_text, nym_name, nym_tag, page_title)
            if not new_text:
                new_text = prev_text

        if new_text == text:
            return text

        if not len(self._flagged.keys()):
            self.needs_fix("autofix")

        for x in self._flagged.keys():
            self._stats[x] = self._stats.get(x,0)+1

        missing_fixes = set(self._flagged.keys()).difference(tools)
        if missing_fixes and not len(self._debug_fix):
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
    parser.add_argument('--fix-debug', action='append', help="Print debug info for issues with the specified flag (Can be specified multiple times)", default=[])
    parser.add_argument('--fix', action='append', help="Fix issues with the specified flag (Can be specified multiple times)", default=[])
    parser.add_argument('--article-limit', type=int, help="Limit processing to first N articles", default=[])
    parser.add_argument('--fix-limit', type=int, help="Limit processing to first N fixable articles", default=[])

    args = parser.parse_args()

    if not os.path.isfile(args.xml):
        raise FileNotFoundError(f"Cannot open: {args.xml}")

    dump = xmlreader.XmlDump(args.xml)
    parser = dump.parse()
    site = pywikibot.Site()

    fixer = NymSectionToTag(args.lang_section, args.lang_id, debug=args.fix_debug)

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

        lang_entry = fixer.get_language_entry(entry.text)

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

    for k,v in sorted(fixer._stats.items(), key=lambda item: item[1], reverse=True):
        print(f"{k}: {v}")

    prefile.close()
    postfile.close()


if __name__ == '__main__':
    main()
