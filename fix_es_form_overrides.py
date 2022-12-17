#!/usr/bin/python3

import argparse
import enwiktionary_templates as templates
import os
import re
import sys

from autodooz.sectionparser import SectionParser
from collections import namedtuple, defaultdict
from enwiktionary_wordlist.wordlist import Wordlist
from enwiktionary_wordlist.word import Word

# Removes unnecessary form overrides from es-noun templates
# The template can usually generate the correct plural or opposite-geneder
# form. This removes specified plurals or opposite-gender form
# when they match what the template would generate by default

class OverrideFixer():

    def __init__(self, logger=None):
        self._logger = logger
        self._section = None
        self._changes = []

    def fix(self, code, current, default, details):
        if self._logger:
            self._logger("autofix_" + code, self._section, current, default)
        else:
            self._summary.append(f"/*{self._section.path}*/ {details}")

    def warn(self, code, current, default):
        if self._logger:
            self._logger(code, self._section, current, default)

    def get_default_forms(self, word, gender):

        mate = "m" if gender == "f" else "f"

        forms = defaultdict(list)

        for template in templates.iter_templates("{{es-noun|" + gender + "|" + mate + "=+}}"):
            data = templates.expand_template(template, word)

        for formtype, form in Word.parse_list(data):
            forms[formtype].append(form)

        return forms

    def cleanup_overrides(self, title, template):

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
                if len(current) == 1 and current == default and template.has(p):
                    template.add(p, "+")
                    self.fix(f"replaced_{p}", current, default, f"replaced '{p}={current[0]}' with '{p}=+'")
                else:
                    if current != ["+"] and current != ["1"]:
                        self.warn(f"custom_{p}", current, default)

        for p in ["mpl", "fpl"]:
            if p in current_forms:
                current = current_forms[p]
                default = default_forms[p]
                if len(current_forms[p]) == 1 and current_forms[p] == default_forms[p] and template.has(p):
                    template.remove(p)
                    self.fix(f"removed_{p}", current, default, f"removed '{p}={current[0]}'")
                else:
                    self.warn(f"custom_{p}", current, default)

        p = "pl"
        if p in current_forms:
            current = current_forms[p]
            default = default_forms[p]
            if len(current_forms[p]) == 1 and current_forms[p] == default_forms[p]:
                template.remove(2)
                self.fix(f"removed_{p}", current, default, "removed unneeded plural override")
            else:
                self.warn(f"custom_{p}", current, default)


    def cleanup_line(self, line, title):

        for template in templates.iter_templates(line):
            if template.name != "es-noun":
                continue

            old_template = str(template)
            self.cleanup_overrides(title, template)
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

                    # needed for logging to work
                    self._section = section

                    new_line = self.cleanup_line(line, title)
                    if new_line != line:
                        entry_changed = True
                        section._lines[idx] = new_line

        if not entry_changed:
            return text

        if summary:
            summary += self._summary
        return str(entry)
