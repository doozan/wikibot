import enwiktionary_sectionparser as sectionparser
import re
import sys

from autodooz.sections import ALL_POS, COUNTABLE_SECTIONS, ALL_LANGS
from autodooz.list_mismatched_headlines import is_header as _is_header, header_matches

def headline_matches(headline, prev_headlines, lang_name):
    """ Returns True if the first template in the given headline
    matches the first template of any of the headlines in prev_headlines
    """
    assert is_headline(headline, lang_name)
    m1 = re.search(r"{{\s*(.*?)\s*[|}]", headline)
    assert m1
    for line in prev_headlines:
        if is_headline(line, lang_name):
            m2 = re.search(r"{{\s*(.*?)\s*[|}]", line)
            assert m2
            if m1.group(1) == m2.group(1):
                return True

    return False

def is_headline(line, lang_name):
    if line.startswith("†{{taxoninfl"):
        return True
    if not _is_header(line, lang_name):
        return False
    if any(x in line for x in ["tr-def-suffix form","tr-suffix-forms", "-decl-"]):
       return False

    return True

class HeaderFixer():

    def __init__(self):
        self._summary = None
        self._log = []

    def fix(self, code, section, location="", details=None):
        # When running tests, section will be empty
        if not section:
            print("FIX:", code, section.page, section.path, location, details, file=sys.stderr)
            return

        if self._summary is not None:
            self._summary.append(f"/*{section.path}*/ {location} {details}")

        self._log.append(("autofix_" + code, section.page, section.path, location, details))

    def warn(self, code, section, location="", details=None):
        if not section:
            print("WARN:", code, section.page, section.path, location, details, file=sys.stderr)
        self._log.append((code, section.page, section.path, location, details))

    def process(self, page_text, page, summary=None, options=None):
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

        entry = None
        entry_changed = False

        entry = sectionparser.parse(page_text, page)
        if not entry:
            return [] if summary is None else page_text

        for section in entry.ifilter_sections(matches=lambda x: x.title != "Idiom" and x.title in ALL_POS \
                and x.parent and (x.parent.title in COUNTABLE_SECTIONS or x.parent.title in ALL_LANGS)):

            # Navajo entries are a mess
            lang_name = section._topmost.title
            if lang_name == "Navajo":
                continue

            old_text = str(section)
            translation_lines = None

            fixes = []
            headlines = []
            before_first_sense = True
            for i, line in enumerate(section.content_wikilines):
                if before_first_sense:
                    if is_headline(line, lang_name):
                        headlines.append(line)

                    elif line.startswith("#"):
                        if headlines:
                            before_first_sense = False
                        else:
                            self.warn("no_headlines", section, "", "\n".join(section.content_wikilines[:i]))
                            fixes = []
                            break

                elif is_headline(line, lang_name):
                    if section._children:
                        self.warn("stray_headline_child_sections", section, "", "\n".join(section.content_wikilines[i:]))

                    elif len(list(h for h in headlines if is_headline(h, lang_name))) > 1:
                        self.warn("stray_headline_multi_header_templates", section, "", "\n".join(headlines + ["", line]))

                    elif header_matches(line, section):
                        if headline_matches(line, headlines, lang_name):
                            self.fix("stray_headline", section, "", f"added missing {section.title} header")
                            new_header = "="*section.level + section.title + "="*section.level
                            if section.content_wikilines[i-1] != "":
                                new_header = "\n" + new_header
                            fixes.append((new_header, i))
                        else:
                            self.warn("stray_headline_mismatched_templates", section, "", "\n".join(headlines + ["", line]))
                    else:
                        self.warn("stray_headline", section, "", "\n".join(section.content_wikilines[i:]))

                    before_first_sense = True
                    headers = [line]

                elif line.lstrip().startswith("{{trans-top"):
                    if section.content_wikilines[-1].strip() == "{{trans-bottom}}":
                        translation_lines = section.content_wikilines[i:]
                        del section.content_wikilines[i:]
                        while section.content_wikilines[-1] == "":
                            del section.content_wikilines[-1]
                        break
                    else:
                        self.warn("unfixable_translation", section, "", "\n".join(section.content_wikilines[i:]))

                    if translation_lines:
                        section.add_child("Translations", translation_lines, 0)
                        self.fix("missing_header", section, "", "added missing Translations section header")
                        entry_changed = True
                        break

            for new_header, pos in reversed(fixes):
                section.content_wikilines.insert(pos, new_header)
                entry_changed = True

        if summary is None:
            return self._log

        if entry_changed:
            return str(entry)

        return page_text
