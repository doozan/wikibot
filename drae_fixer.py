import mwparserfromhell
import re
import sys

from autodooz.sectionparser import SectionParser, Section
from collections import defaultdict
from enwiktionary_wordlist.all_forms import AllForms

class DraeFixer():

    def __init__(self, form_filename, link_filename, logger=None):
        self.drae_forms = AllForms.from_file(form_filename)
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

    @staticmethod
    def strip_brackets(string):
        return string.replace("[", "").replace("]", "")

    def get_lemmas(self, text, title, check_verbs=True, get_all=False):

        # drae.links entries do not use []
        title = self.strip_brackets(title)

        if not get_all:
            if self.drae_forms.has_lemma(title):
                return [title]
            elif " " not in title:
                return []

        lemmas = [l.split("|") for l in self.drae_forms.get_lemmas(title)]

        # Handle cases where wiktionary uses -r for a lemma but DRAE uses -rse (and vice versa)
        # suicidar, autocensurarse
        if not lemmas and check_verbs and ("{{es-verb}}" in str(text) or "{{es-verb|" in str(text)):
            if title.endswith("r"):
                lemmas = self.get_lemmas(text, title + "se", check_verbs=False)
            elif title.endswith("rse"):
                lemmas = self.get_lemmas(text, title[:-2], check_verbs=False)

        if len(lemmas) == 1:
            return [self.strip_brackets(l[1]) for l in lemmas]
        else:
            stripped = sorted(set(self.strip_brackets(l[1]) for l in lemmas if l[1] == title or l[0] not in ["v", "part"]))
            if stripped:
                return stripped
            return sorted(set(self.strip_brackets(l[1]) for l in lemmas))

    def fix_missing_drae(self, text, title, replacement=None):

        entry = SectionParser(text, title)
        spanish = next(entry.ifilter_sections(matches=lambda x: x.title == "Spanish", recursive=False))

        lemmas = self.get_lemmas(spanish, title)
        if not lemmas:
            return text

        link = None
        links = sorted(set(link for lemma in lemmas for link in self.drae_links.get(lemma, [])))
        if not links:
            return text

        if len(links) > 1:
            self.log("drae_link_missing", title, "('" + "', '".join(links) +"')")

        link = links[0]
        self.log("drae_link_missing_autofix", title, link)

        section = next(spanish.ifilter_sections(matches=lambda x: x.title == "Further reading"), None)
        if not section:
            section = Section(spanish, 3, "Further reading")

            # New section goes before the first Anagrams section, if it exists
            pos = [x for x,e in enumerate(spanish._children) if e.title == "Anagrams"]
            if pos:
                spanish._children.insert(pos[0], section)

            # Otherwise, at the end
            else:
                spanish._children.append(section)

        line = "* " + self.make_drae_template(title, link)
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

            lemmas = self.get_lemmas(spanish, title, get_all=True)
            links = sorted(set(link for lemma in lemmas for link in self.drae_links.get(lemma, [])))
            if not target in links:
                if links:
                    if target != title:
                        if " " in title and " " not in target:
                            if len(links) > 1:
                                self.log("drae_link_custom_target", title, "is '{target}', should be ('" + "', '".join(links) +"')")
                            else:
                                # If the existing link is to a single word, but the page is a phrase
                                # and there a matching phrase in drae, replace the link
                                self.log("drae_link_wrong_target_autofix", title, links[0])
                                fixes.append((template, self.make_drae_template(title, links[0])))
                        else:
                            self.log("drae_link_custom_target", title, "('" + "', '".join(links) +"')")
                    else:
                        if len(links) > 1:
                            self.log("drae_link_wrong_target", title, "('" + "', '".join(links) +"')")
                        else:
                            self.log("drae_link_wrong_target_autofix", title, links[0])
                            fixes.append((template, self.make_drae_template(title, links[0])))
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
