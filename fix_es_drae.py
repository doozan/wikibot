import enwiktionary_sectionparser as sectionparser
import mwparserfromhell
import re
import sys

from collections import defaultdict

class DraeFixer():

    def __init__(self, link_filename, logger=None):
        drae_links, must_link_by_id = self.load_links(link_filename)
        self.drae_links = drae_links
        self.must_link_by_id = must_link_by_id
        self.logger = logger

    def log(self, *args, **kwargs):
        if self.logger:
            self.logger.add(*args, **kwargs)

    @staticmethod
    def load_links(filename):
        drae_links = defaultdict(list)
        must_link_by_id = {}
        with open(filename) as infile:
            for line in infile:
                items = line.strip().split("\t")
                if len(items) == 3:
                    form, link_id, link = items
                elif len(items) == 2:
                    form, link_id = items
                    link = form
                else:
                    raise ValueError("unhandled line", line, filename)

                # forms with question marks must use direct link id
                if "?" in link:
                    must_link_by_id[link] = link_id

                drae_links[form].append(link)
        return drae_links, must_link_by_id

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


    def fix_missing_drae(self, text, title, summary=None):

        text = text.replace("{{R:DRAE", "{{R:es:DRAE")

        # Skip single letters
        if len(title) == 1:
            return text

        entry = sectionparser.parse(text, title)
        if not entry:
            return text

        spanish = next(entry.ifilter_sections(matches="Spanish", recursive=False), None)
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

        drae_line = "* " + self.make_drae_template(title, target)


        # Remove DRAE line if it appears in References or See also
        remove_section = []
        for section in spanish.ifilter_sections(matches=lambda x: x.title in ["Further reading", "See also", "References"]):
            for line in section._lines:
                section._lines = [l for l in section._lines if l != drae_line]
            # IF the section is now empty, remove it
            if not section._lines:
                remove_section.append(section)
        for section in remove_section:
            idx = section.parent._children.index(section)
            section.parent._children.pop(idx)

        section = next(spanish.ifilter_sections(matches="Further reading"), None)

        if section:
            if drae_line in str(section):
                return text
        else:
            section = sectionparser.Section(spanish, 3, "Further reading")

            # New section goes before the first Anagrams section, if it exists
            pos = [x for x,e in enumerate(spanish._children) if e.title == "Anagrams"]
            if pos:
                spanish._children.insert(pos[0], section)

            # Otherwise, at the end
            else:
                spanish._children.append(section)

        section._lines.insert(0, drae_line)

        if summary is not None:
            summary.append("/*Spanish*/ added missing DRAE link")

        return str(entry).rstrip()

    def fix_wrong_drae(self, text, title, summary=None):

        text = text.replace("{{R:DRAE", "{{R:es:DRAE")

        entry = sectionparser.parse(text, title)
        if not entry:
            return text

        spanish = next(entry.ifilter_sections(matches="Spanish", recursive=False))
        section = next(spanish.ifilter_sections(matches="Further reading"))

        new_section = str(section)
        templates = list(re.finditer("{{R:es:DRAE(.*?)}}", new_section))

        fixes = []

        # Validate existing links
        targets = self.get_targets(text, title)
        for template in templates:
            target = self.get_template_target(template, title)
            if not target and title in targets:
                continue

            if not target in targets or target == title:
                if targets:
                    if target != title:
                        if " " in title and target and " " not in target:
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

        if summary is not None:
            summary.append("/*Spanish*/ adjusted DRAE link")

        return str(entry)

    @staticmethod
    def get_template_target(template, title):
        if template.group(1) == "":
            return

        params = template.group(1).split("|")
        for param in params[1:]:
            if "=" not in param:
                target = param.strip()
                break
            elif "entry=" in param:
                target = params[1].split("=")[1].strip()
                break
        else:
            return

        return target.strip()

    @staticmethod
    def make_drae_template(title, target):
        if target == title:
            target = ""
        elif "#" in target:
            page, _id = target.split("#")
            target = "|" + page + "|id=" + _id
        else:
            target = "|" + target

        return "{{R:es:DRAE" + target + "}}"
