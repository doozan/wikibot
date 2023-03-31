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

    def cleanup_section(self, section, page):
        """ Returns True if the section was modified """

        lang_id = ALL_LANGS[list(section.lineage)[-2]]
        new_lines = self.cleanup_lines(lang_id, section._lines, section, page)
        if new_lines and new_lines != section._lines:
            section._lines = new_lines
            return True

    def cleanup_lines(self, lang_id, lines, section=None, page=None):
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
        new_lines = self.convert_list_templates(lang_id, lines, section, page)
        if new_lines:
            return pre + new_lines

        # Convert any exist {{top}}, {{rel-N}} or {{der-N}} lists
        new_lines = self.convert_top_templates(lang_id, lines, section, page)
        if new_lines:
            return pre + new_lines

        # titled, single lines lists to templates
        new_lines = self.convert_titled_lists_to_templates(lang_id, lines, section, page)
        if new_lines:
            return pre + new_lines

        # Single line of comma separated items
        if len(lines) == 1 and "}}, " in lines[0]:
            new_line = self.line_to_template(lang_id, lines[0], section, page)
            if new_line:
                return pre + [new_line]

        # Convert a simple bulleted list of items
        new_lines = self.convert_lines_to_template(lang_id, lines, section, page)
        if new_lines:
            return pre + new_lines

    def convert_list_templates(self, lang_id, lines, section, page):
        """
        Converts {{derX}} {{relX}} and {{colX}} templates to {{col-auto}}
        returns None if no templates were converted
        """

        # If the section is using an older template, just replace the template with {{col-auto}}
        new_lines = []
        for line in lines:
            new_line = re.sub(r"\{\{(\s*(rel|col|der)[2345]\s*)", "{{col-auto", line)
            new_lines.append(new_line)
        if new_lines and new_lines != lines:
            return new_lines

    def cleanup_line(self, lang_id, line, section, page):
        """ Strips leading "* " and converts [[link]] to {{l|lang_id|link}} """

        # Convert [[link]] to {{l|XX|link}}
        line = re.sub(r"\[\[([^\[\]\|]*)\]\]", "{{l|" + lang_id + "|" + r"\1" + "}}", line)

        if not re.match(r"\*\s*{{", line):
            self.warn("unhandled_line", section, line)
            return

        # Strip leading bullet
        line = re.sub(r"\*\s*", "", line)

        no_templates = self.strip_templates(line)
        if no_templates.strip(" ,;"):
            self.warn("text_outside_template", section, line)
            return

        return line.strip()

    def convert_lines_to_template(self, lang_id, lines, section, page):
        """
        converts a list of bulleted {{l}} items to {{col-auto}}:
        * {{l|es|one}}
        * {{l|es|two}} {{g|m}}
        * {{l|es|three}}
        ==
        {{col-auto|es|one|{{l|es|two|g=m}}|three}}
        """

        items = []
        for line in lines:
            if not line.strip():
                continue

            line = self.cleanup_line(lang_id, line, section, page)
            if not line:
                return

            item = self.get_item(lang_id, line, section, page)
            if not item:
                return

            if item not in items:
                items.append(item)

        if not items:
            self.warn("no_items", section, line)
            return

        return [self.generate_template(lang_id, items)]

    @staticmethod
    def generate_template(lang_id, items, table_title=None):
        use_expanded_template = len(items) > 4 or sum(len(i) for i in items) > 60 or any("{{" in item for item in items)
        br = "\n" if use_expanded_template else ""

        title_param = f"|title={table_title}" if table_title else ""

        return "{{col-auto|" + lang_id + title_param + br + "|" + f"{br}|".join(items) + br + "}}"

    def convert_top_templates(self, lang_id, lines, section, page):
        """
        Converts multi-line lists between {{*-top}} and {{*-bottom}} tags:
        returns None if no templates were converted

        {{rel-top}}
        * [[r1]]
        * [[r2]]
        * [[r3]]
        {{rel-bottom}}
        {{der3-top}}
        * [[d1]]
        * [[d2]]
        * [[d3]]
        {{der-bottom}}
        ==
        {{col-auto|pl|r1|r2|r3}}
        {{col-auto|pl|d1|d2|d3}}
        """

        if not re.match(r"{{\s*(rel-|der-)?top[1-5]{0,1}\s*[|}][^{]*}$", lines[0]):
            return

        new_lines = []
        items = []
        in_multi_line = False
        changed = False
        for line in lines:
            if not line.strip():
                continue

            if in_multi_line:
                if re.match(r"{{\s*(rel-|der-)?bottom\s*}}$", line):
                    in_multi_line = False
                    if not items:
                       self.warn("no_items", section, line)
                       return
                    new_lines.append(self.generate_template(lang_id, items))
                    items = []
                else:
                    item = self.get_item(lang_id, line, section, page)
                    if not item:
                        return
                    if item not in items:
                        items.append(item)
                continue

            # Line contains only a single rel-topX der-topX or top template
            if re.match(r"{{\s*(rel-|der-)?top[1-5]{0,1}\s*[|}][^{]*}$", line) and self.strip_templates(line) == "":
                in_multi_line = True
                continue

            # Not a multi-item list
            self.warn("unexpected_line", section, line)
            return

        if in_multi_line:
            self.warn("unclosed_list", section, line)
            return

        if new_lines and new_lines != lines:
            return new_lines


    def convert_titled_lists_to_templates(self, lang_id, lines, section, page):
        """
        Converts single-line, bulleted, titled, lists into {{col-auto}}
        * {{q|adjectives}} {{l|pl|a1}}, {{l|pl|a2}}, {{l|pl|a3}}
        * {{q|nouns}} {{l|pl|n1}}, {{l|pl|n2}}, {{l|pl|n3}}
        ==
        {{col-auto|pl|title=adjectives|a1|a2|a3}}
        {{col-auto|pl|title=nouns|n1|n2|n3}}
        """

        if not re.match(r"\*\s*{{(q|qualifier|i|qual|sense|s)\s*\|([^{]*?)}}", lines[0]):
            return

        new_lines = []
        for line in lines:
            if not line.strip():
                continue

            new_line = self.line_to_template(lang_id, line, section, page, label_required=True)
            if new_line is None:
                return

            new_lines.append(new_line)

        if new_lines and new_lines != lines:
            return new_lines

    @staticmethod
    def strip_templates(text):
        old_text = None
        while text != old_text:
            old_text = text
            text = re.sub(r"\{\{[^{}]*?\}\}", "", old_text)

        return text

    def split_label(self, text, section, page):
        """ If text starts with a label template, strip it and return
        label, following_text

        split_label("{{q|test}} foo bar") == ("test", " foo bar")
        """

        # if first template is a label, process and strip it
        label = None
        match = re.match(r"{{(q|qualifier|i|qual|sense|s)\s*\|([^{]*?)}}", text)
        if match:
            label = match.group(2).strip()
            if "|" in label or "=" in label:
                self.warn("label_has_extra_param", section, text)
                return None, None
            text = text[len(match.group(0)):]

        return label, text

    def line_to_template(self, lang_id, line, section, page, label_required=False):
        """
        Converts a single-line, bulleted, titled, list into {{col-auto}}
        * {{q|adjectives}} {{l|pl|a1}}, {{l|pl|a2}}, {{l|pl|a3}}
        ==
        {{col-auto|pl|title=adjectives|a1|a2|a3}}

        Returns None if a line does not match expected input
        """

        line = self.cleanup_line(lang_id, line, section, page)
        if not line:
            return

        label, text = self.split_label(line, section, page)
        if text is None:
            return
        if not label and label_required:
            self.warn("no_label", section, line)
            return

        items = self.get_items(lang_id, text, section, page)
        if not items:
            return

        return self.generate_template(lang_id, items, label)

    def get_items(self, lang_id, line, section, page):
        """ Returns None if all items could not be parsed """

        # TODO: only split on commas outside templates
        split_text = line.split(", ")
        items = []
        for text in split_text:
             item = self.get_item(lang_id, text, section, page)
             if not item:
                 return
             if item not in items:
                 items.append(item)

        return items

    def get_item(self, lang_id, line, section, page):
        wikicode = mwparserfromhell.parse(line)
        item = None
        item_gender = None
        item_qualifier = ""
        for template in wikicode.filter_templates():

            if template.name.strip() == "l":
                if item:
                    self.warn("multiple_l_templates", section, line)
                    return

                if len(template.params) != 2:
                    item = template
                else:
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

            elif template.name.strip() in ["q", "qualifier", "i", "qual"]:
                if item_qualifier:
                    self.warn("item_has_multiple_qualifiers", section, line)
                    return
                item_qualifier = f" {template}"

            else:
                self.warn("unexpected_template", section, line)
                return

        if not item:
            self.warn("no_item", section, line)
            return

        if isinstance(item, mwparserfromhell.nodes.template.Template):
            if item_gender:
                if item.has("g") and item.get("g") != item_gender:
                    self.warn("item_has_multiple_genders", section, line)
                    return
                item["g"] = item_gender
            return f"{item}{item_qualifier}"

        if item and item_gender:
            return "{{l|" + lang_id + "|" + item + "|g=" + item_gender + "}}" + item_qualifier

        if item_qualifier:
            return "{{l|" + lang_id + "|" + item + "}}" + item_qualifier

        return item


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
