#!/usr/bin/python3

import argparse
import enwiktionary_templates as templates
import os
import re
import sys

from autodooz.sectionparser import SectionParser
from collections import namedtuple, defaultdict
from enwiktionary_wordlist.word import Word

# Removes unnecessary form overrides from es-noun templates
# The template can usually generate the correct plural or opposite-geneder
# form. This removes specified plurals or opposite-gender form
# when they match what the template would generate by default

class OverrideFixer():

    def __init__(self, logger=None):
        self._logger = logger
        self._changes = []

    def fix(self, error, page, current, default, details):
        if self._logger:
            self._logger("autofix_" + error, page, current, default)
        else:
            self._summary.append(f"/*{section.path}*/ {details}")

    def warn(self, error, page, current, default):
        if self._logger:
            self._logger(error, page, current, default)

    def get_default_forms(self, word, gender):

        mate = "m" if gender == "f" else "f"

        forms = defaultdict(list)

        for template in templates.iter_templates("{{es-noun|" + gender + "|" + mate + "=+}}"):
            data = templates.expand_template(template, word)

        for formtype, form in Word.parse_list(data):
            forms[formtype].append(form)

        return forms

    def is_simple_female_equivalent(self, custom, default, section):
        masculines = custom if custom and custom not in [ ["1"], ["+"] ] else default
        masculine = masculines[0]
        return not section._children and section._lines[1:] == ['', "# {{female equivalent of|es|" + masculine + "}}"]

    def cleanup_overrides(self, title, template, section):

        if "+" in title:
            return

        gender = str(template.get(1))
        default_forms = self.get_default_forms(title, gender)

        current_forms = defaultdict(list)
        def add_form(k, param):
            val = str(param.value).strip()
            if val:
                current_forms[k].append(val)

        for param in sorted(template.params, key=lambda x:str(x.name)):
            if str(param.name) == "2":
                add_form("pl", param)

            for p in ["m", "f", "mpl", "fpl", "pl"]:
                if re.match(p + r"\d*$", str(param.name)):
                    add_form(p, param)

        for p in ["m", "f"]:
            if p in current_forms:
                current = current_forms[p]
                default = default_forms[p]

                if p == "m" and self.is_simple_female_equivalent(current, default, section):
                    for rp in ["m", "mpl"]:
                        if template.has(p):
                            template.remove(p)
                            self.fix(f"removed_{p}", title, current, default, f"removed '{p}={current[0]}' from female equivalent of")
                    continue

                if len(current) == 1 and current == default and template.has(p):
                    template.add(p, "+")
                    self.fix(f"replaced_{p}", title, current, default, f"replaced '{p}={current[0]}' with '{p}=+'")
                else:
                    if current != ["+"] and current != ["1"]:
                        self.warn(f"custom_{p}", title, current, default)

        for p in ["mpl", "fpl"]:
            if p in current_forms:
                current = current_forms[p]
                default = default_forms[p]
                if len(current_forms[p]) == 1 and current_forms[p] == default_forms[p] and template.has(p):
                    template.remove(p)
                    self.fix(f"removed_{p}", title, current, default, f"removed '{p}={current[0]}'")
                else:
                    self.warn(f"custom_{p}", title, current, default)

        p = "pl"
        if p in current_forms:
            current = current_forms[p]
            default = default_forms[p]
            if len(current_forms[p]) == 1 and current_forms[p] == default_forms[p]:
                template.remove(2)
                self.fix(f"removed_{p}", title, current, default, "removed unneeded plural override")
            else:
                self.warn(f"custom_{p}", title, current, default)


    def cleanup_line(self, line, title, section):

        for template in templates.iter_templates(line):
            if template.name != "es-noun":
                continue

            old_template = str(template)
            self.cleanup_overrides(title, template, section)
            new_template = str(template)

            if new_template != old_template:
                line = line.replace(old_template, new_template)

        return line


    def process(self, text, title, summary=None):

        self._summary = []

        entry = SectionParser(text, title)

        entry_changed = False
        for spanish in entry.ifilter_sections(matches="Spanish", recursive=False):
            for section in spanish.ifilter_sections(matches="Noun"):
                for idx, line in enumerate(section._lines):
                    if "{{es-noun" not in line:
                        continue

                    new_line = self.cleanup_line(line, title, section)
                    if new_line != line:
                        entry_changed = True
                        section._lines[idx] = new_line

        if not entry_changed:
            return text

        if summary is not None:
            summary += self._summary
        return str(entry)
