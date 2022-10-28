import mwparserfromhell
import re
import sys

from autodooz.sectionparser import SectionParser, Section
from collections import defaultdict

class DraeFixer():

    def __init__(self, link_filename, logger=None):
        self.drae_links = self.load_drae_links(link_filename)
        self.logger = logger

    def log(self, *args, **kwargs):
        if self.logger:
            self.logger.add(*args, **kwargs)

    @staticmethod
    def load_drae_links(filename):
        drae_links = defaultdict(list)
        with open(filename) as infile:
            for line in infile:
                items = line.strip().split("\t")
                if len(items) == 3:
                    lemma, link_id, link = items
                elif len(items) == 2:
                    lemma, link_id = items
                    link = lemma
                else:
                    raise ValueError("unhandled line", line)
                drae_links[lemma].append(link)
        return drae_links

    def get_targets(self, text, title):
        links = sorted(set(self.drae_links.get(title, [])))

        # Handle cases where wiktionary uses -r for a lemma but DRAE uses -rse (and vice versa)
        # suicidar, autocensurarse
        if not links and ("{{es-verb}}" in str(text) or "{{es-verb|" in str(text)):
            if title.endswith("r"):
                links = sorted(set(self.drae_links.get(title + "se", [])))
            elif title.endswith("rse"):
                links = sorted(set(self.drae_links.get(title[:-2], [])))

        return links


    def fix_missing_drae(self, text, title, replacement=None):

        entry = SectionParser(text, title)
        spanish = next(entry.ifilter_sections(matches=lambda x: x.title == "Spanish", recursive=False), None)
        if not spanish:
            return text

        targets = self.get_targets(text, title)
        if not targets:
            # TODO: Log lemma without DRAE
            return text

        if len(targets) > 1:
            self.log("drae_link_missing", title, "('" + "', '".join(targets) +"')")

        target = targets[0]
        self.log("drae_link_missing_autofix", title, target)

        line = "* " + self.make_drae_template(title, target)
        section = next(spanish.ifilter_sections(matches=lambda x: x.title == "Further reading"), None)

        if section:
            if line in str(section):
                return text
        else:
            section = Section(spanish, 3, "Further reading")

            # New section goes before the first Anagrams section, if it exists
            pos = [x for x,e in enumerate(spanish._children) if e.title == "Anagrams"]
            if pos:
                spanish._children.insert(pos[0], section)

            # Otherwise, at the end
            else:
                spanish._children.append(section)

        section._lines.insert(0, line)

        if replacement:
            replacement._edit_summary = "Spanish: added missing DRAE link"

        return str(entry)

    def fix_wrong_drae(self, text, title, replacement=None):

        entry = SectionParser(text, title)
        spanish = next(entry.ifilter_sections(matches=lambda x: x.title == "Spanish", recursive=False))
        section = next(spanish.ifilter_sections(matches=lambda x: x.title == "Further reading"))

        new_section = str(section)
        templates = list(re.finditer("{{R:es:DRAE(.*?)}}", new_section))

        fixes = []

        # Validate existing links
        for template in templates:
            target = self.get_template_target(template, title)

            targets = self.get_targets(text, title)
            if not target in targets:
                if targets:
                    if target != title:
                        if " " in title and " " not in target:
                            if len(targets) > 1:
                                self.log("drae_link_custom_target", title, "is '{target}', should be ('" + "', '".join(targets) +"')")
                            else:
                                # If the existing link is to a single word, but the page is a phrase
                                # and there a matching phrase in drae, replace the link
                                self.log("drae_link_wrong_target_autofix", title, targets[0])
                                fixes.append((template, self.make_drae_template(title, targets[0])))
                        else:
                            self.log("drae_link_custom_target", title, "('" + "', '".join(targets) +"')")
                    else:
                        if len(targets) > 1:
                            self.log("drae_link_wrong_target", title, "('" + "', '".join(targets) +"')")
                        else:
                            self.log("drae_link_wrong_target_autofix", title, targets[0])
                            fixes.append((template, self.make_drae_template(title, targets[0])))
                else:
                    if target in self.drae_links:
                        self.log("drae_link_custom_target", title, f"('{target}')")
                    else:
                        self.log("drae_link_no_target", title, f"('{target}')")

        if not fixes:
            return text

        for old_match, new in fixes:
            old = old_match.group(0)
            new_lines = []
            for line in section._lines:
                new_lines.append(line.replace(old, new))
            section._lines = new_lines

        if replacement:
            replacement._edit_summary = "Spanish: adjusted DRAE link"

        return str(entry)

    @staticmethod
    def get_template_target(template, title):
        if template.group(1) == "":
            return title

        params = template.group(1).split("|")
        for param in params[1:]:
            if "=" not in param:
                target = param.strip()
                break
            elif "entry=" in param:
                target = params[1].split("=")[1].strip()
                break
        else:
            target = title

        return target.strip()

    @staticmethod
    def make_drae_template(title, target):
        if "#" in target:
            page, _id = target.split("#")
            target = "|" + page + "|id=" + _id
        else:
            target = "|" + target

        return "{{R:es:DRAE" + target + "}}"
