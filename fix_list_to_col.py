#!/usr/bin/python3

import enwiktionary_sectionparser as sectionparser
import mwparserfromhell
import re

from autodooz.sections import ALL_LANGS, ALL_LANG_IDS

""" Converts bulleted lists of {{l}} items into {{col-auto}} lists """

class ListToColFixer():

    def __init__(self):
        self._summary = None
        self._log = []

    def fix(self, code, section, details):
        # When running tests, section will be empty
        if not section:
            print("FIX:", code, details)
            return

        if self._summary is not None:
            self._summary.append(f"/*{section.path}*/ {details}")

        page = list(section.lineage)[-1]
        self._log.append(("autofix_" + code, page))

    def warn(self, code, section, details=None):
        # When running tests, section will be empty
        if not section:
            print("WARN:", code, details)
            return

        page = list(section.lineage)[-1]
        self._log.append((code, page, details))

    def cleanup_section(self, section, title):
        """ Returns True if the section was modified """

        lang_id = ALL_LANGS[list(section.lineage)[-2]]
        new_lines = self.cleanup_lines(lang_id, section._lines, section, title)
        if new_lines:
            section._lines = new_lines
            return True

    def cleanup_lines(self, lang_id, lines, section=None, title=None):
        if not lines:
            return

        # Allow "* See " lines to preceed lists
        pre = []
        x = 0
        while len(lines)>x and (lines[x].startswith("* See ")):
            x+=1
        if x:
            pre = lines[:x]
            lines = lines[x:]

        # Ignore sections that are just "See" links
        if not lines:
            return

        # Ignore sections that have already been converted
        if lines[0].startswith("{{col-auto|"):
            return

        # If there are existing list templates, convert them to {{col-auto}}
        new_lines = self.convert_list_templates(lang_id, lines, section, title)

        if not new_lines:
            if lines[0].startswith("* {{q"):
                new_lines = self.titled_lists_to_templates(lang_id, lines, title, section)
            else:
                new_lines = self.lines_to_template(lang_id, lines, title, section)

        if new_lines:
            return pre + new_lines

    def convert_list_templates(self, lang_id, lines, section=None, title=None):
        """
        Converts {{derX}} {{relX}} and {{colX}} templates to {{col-auto}}
        returns None if no templates were converted
        """

        # If the section is using an older template, just replace the template with {{col-auto}}
        new_lines = []
        converted = False
        for line in lines:
            new_line = re.sub(r"\{\{(\s*(rel|col|der)[2345]\s*)", "{{col-auto", line)
            if new_line != line:
                converted = True
            new_lines.append(new_line)
        if converted:
            return new_lines


    def lines_to_template(self, lang_id, lines, title=None, section=None):
        """ Converts a list of bulleted {{l}} items to {{col-auto}}:
        * {{l|es|one}}
        * {{l|es|two}} {{g|m}}
        * {{l|es|three}}
        ==
        {{col-auto|es|one|{{l|es|two|g=m}}|three}}
        """

        pre = []
        items = []
        use_expanded_template = False
        for line in lines:
            if not line.strip():
                continue

            if not re.match(r"\*\s*{{", line):
                self.warn("unhandled_line", section, line)
                return

            no_templates = line.lstrip("* ")
            no_templates = self.strip_templates(no_templates)
            if no_templates.strip(" ,;"):
                self.warn("text_outside_template", section, line)
                return

            wikicode = mwparserfromhell.parse(line)
            item = None
            item_gender = None
            for template in wikicode.filter_templates():

                if template.name.strip() == "l":
                    if len(template.params) != 2:
                        if len(template.params) == 3 and template.has("g"):
                            item_gender = template.get("g").value.strip()
                        else:
                            self.warn("l_has_extra_params", section, line)
                            return

                    if item:
                        self.warn("multiple_l_templates", section, line)
                        return

                    item = template.get(2).strip()

                elif template.name.strip() == "g":
                    if len(template.params) != 1:
                        self.warn("g_has_multiple_params", section, line)
                        return
                    gender = template.get(1).value.strip()
                    if item_gender and item_gender != gender:
                        self.warn("item_has_multiple_genders", section, line)
                        return
                    item_gender = gender

                else:
                    self.warn("unexpected_template", section, line)
                    return

            if item and item_gender:
                item = "{{l|" + lang_id + "|" + item + "|g=" + item_gender + "}}"
                use_expanded_template = True
            if item not in items:
                items.append(item)

        if not items:
            self.warn("no_items", section, line)
            return

        br = "\n" if use_expanded_template else ""
        return pre + ["{{col-auto|" + lang_id + br + "|" + f"{br}|".join(items) + br + "}}"]


    def titled_lists_to_templates(self, lang_id, lines, title=None, section=None):
        """
        Converts single-line, bulleted, titled, lists into {{col-auto}}
        * {{q|adjectives}} {{l|pl|a1}}, {{l|pl|a2}}, {{l|pl|a3}}
        * {{q|nouns}} {{l|pl|n1}}, {{l|pl|n2}}, {{l|pl|n3}}
        ==
        {{col-auto|pl|title=adjectives|a1|a2|a3}}
        {{col-auto|pl|title=nouns|n1|n2|n3}}
        """

        new_lines = []
        for line in lines:

            new_line = self.line_to_template(lang_id, line, title, section)
            if new_line is None:
                return

            if new_line != line:
                changed = True

            new_lines.append(new_line)

        if changed:
            return new_lines

    @staticmethod
    def strip_templates(text):
        old_text = None
        while text != old_text:
            old_text = text
            text = re.sub(r"\{\{[^}]*?\}\}", "", old_text)

        return text

    def line_to_template(self, lang_id, line, title=None, section=None):
        """
        Converts a single-line, bulleted, titled, list into {{col-auto}}
        * {{q|adjectives}} {{l|pl|a1}}, {{l|pl|a2}}, {{l|pl|a3}}
        ==
        {{col-auto|pl|title=adjectives|a1|a2|a3}}

        Returns None if a line does not match expected input
        """

        new_lines = []

        if not line.strip():
            return line

        if not re.match(r"\*\s*{{", line):
            self.warn("unhandled_line", section, line)
            return

        no_templates = self.strip_templates(line[2:])
        if no_templates.strip(" ,;"):
            self.warn("text_outside_template", section, line)
            return

        wikicode = mwparserfromhell.parse(line)
        label = None
        items = []
        for template in wikicode.filter_templates():
            if template.name.strip() in ["q", "qualifier", "i", "qual"]:
                if label:
                    self.warn("multi_labels", section, line)
                    return
                if items:
                    self.warn("label_after_item", section, line)
                    return
                if len(template.params) != 1:
                    self.warn("q_has_extra_params", section, line)
                    return

                label = template.get(1)

            elif template.name.strip() == "l":
                if len(template.params) != 2:
                    self.warn("l_has_extra_params", section, line)
                    return
                item = template.get(2).strip()
                if item not in items:
                    items.append(item)

            else:
                self.warn("unexpected_template", section, line)
                return

        if not label:
            self.warn("no_label", section, line)
            return

        if not items:
            self.warn("no_items", section, line)
            return

        return "{{col-auto|" + lang_id + "|" + f"title={label}|" + "|".join(items) + "}}"

    def process(self, text, title, summary=None, options=None):
        # This function runs in two modes: fix and report
        #
        # When summary is None, this function runs in 'report' mode and
        # returns [(code, page, details)] for each fix or warning
        #
        # When run using wikifix, summary is not null and the function
        # runs in 'fix' mode.
        # summary will be appended with a description of any changes made
        # and the function will return the modified page text

        self._summary = summary
        self._log = []

        entry = sectionparser.parse(text, title)
        if not entry:
            return [] if summary is None else text

        # Skip prefixes, suffixes, and afixes
        if title.startswith("-") or title.endswith("-"):
            return [] if summary is None else text

        entry_changed = False
        lang_names = [ALL_LANG_IDS[lang_id] for lang_id in options["lang_ids"]]
        l2_entries = entry.filter_sections(matches=lambda x: x.title in lang_names, recursive=False)
        if not len(l2_entries) == 1:
            return [] if summary is None else text

        l2 = l2_entries[0]
        for section in l2.ifilter_sections(matches=lambda x: x.title in options["sections"]):
            if self.cleanup_section(section, title):
                self.fix("list_to_col", section, "converted to {{col-auto}}")
                entry_changed = True

        if summary is None:
            return self._log

        if entry_changed:
            return str(entry)

        return text
