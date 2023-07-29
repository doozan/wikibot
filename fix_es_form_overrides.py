#!/usr/bin/python3

import argparse
import enwiktionary_sectionparser as sectionparser
import enwiktionary_templates as templates
import os
import re
import sys

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

    def fix(self, error, section, current, default, details):
        if self._logger:
            page = list(section.lineage)[-1]
            self._logger("autofix_" + error, page, current, default)
        else:
            self._summary.append(f"/*{section.path}*/ {details}")

    def warn(self, error, section, current, default):
        if self._logger:
            page = list(section.lineage)[-1]
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
        return not section._children and section.content_wikilines[1:] == ['', "# {{female equivalent of|es|" + masculine + "}}"]

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
                            self.fix(f"removed_{p}", section, current, default, f"removed '{p}={current[0]}' from female equivalent of")
                    continue

                if len(current) == 1 and current == default and template.has(p):
                    template.add(p, "+")
                    self.fix(f"replaced_{p}", section, current, default, f"replaced '{p}={current[0]}' with '{p}=+'")
                else:
                    if current != ["+"] and current != ["1"]:
                        self.warn(f"custom_{p}", section, current, default)

        for p in ["mpl", "fpl"]:
            if p in current_forms:
                current = current_forms[p]
                default = default_forms[p]
                if len(current) == 1 and current == default and template.has(p):
                    template.remove(p)
                    self.fix(f"removed_{p}", section, current, default, f"removed '{p}={current[0]}'")
                else:
                    self.warn(f"custom_{p}", section, current, default)

        p = "pl"
        if p in current_forms:
            current = current_forms[p]
            default = default_forms[p]
            if len(current) == 1 and current == default:
                template.remove(2)
                self.fix(f"removed_{p}", section, current, default, "removed unneeded plural override")
            else:
                for x, item in enumerate(current, 1):
                    plural = 2 if x == 1 else f"pl{x}"
                    if item == title:
                        if template.has(plural):
                            template.add(plural, "#")
                            self.fix(f"replaced_{plural}", section, current, default, f"replaced '{plural}={title}' with '{plural}=#'")
                        else:
                            print("NOT FOUND", plural, title)
                    if len(default) == 1 and item == default[0]:
                        if template.has(plural):
                            template.add(plural, "+")
                            self.fix(f"replaced_{plural}", section, current, default, f"replaced '{plural}={title}' with '{plural}=+'")
                        else:
                            print("NOT FOUND", plural, title)

                self.warn(f"custom_{p}", section, current, default)


    def cleanup_wikiline(self, wikiline, title, section):

        for template in templates.iter_templates(wikiline):
            if template.name != "es-noun":
                continue

            old_template = str(template)
            self.cleanup_overrides(title, template, section)
            new_template = str(template)

            if new_template != old_template:
                wikiline = wikiline.replace(old_template, new_template)

        return wikiline


    def process(self, text, title, summary=None):

        self._summary = []

        entry = sectionparser.parse(text, title)
        if not entry:
            return text

        entry_changed = False
        for spanish in entry.ifilter_sections(matches="Spanish", recursive=False):
            for section in spanish.ifilter_sections(matches="Noun"):
                for idx, wikiline in enumerate(section.content_wikilines):
                    if "{{es-noun" not in wikiline:
                        continue

                    new_wikiline = self.cleanup_wikiline(wikiline, title, section)
                    if new_wikiline != wikiline:
                        entry_changed = True
                        section.content_wikilines[idx] = new_wikiline

        if not entry_changed:
            return text

        if summary is not None:
            summary += self._summary
        return str(entry)
