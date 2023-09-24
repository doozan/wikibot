import enwiktionary_sectionparser as sectionparser
import re
import sys

from autodooz.sections import ALL_POS, ALL_LANGS

def is_sentence(text):
    return bool(re.match(r"^\W*[A-Z].*[.?!]\W*$", text))

def is_italic(text):
    # Returns True if entire string is enclosed in '' italic wikimarkup
    ital = "(?<!')(?:'{2}|'{5})(?!')"
    return re.match(fr"{ital}.*{ital}$", text) and not re.search(ital, text[2:-2])

class BareUxFixer():

    def __init__(self):
        self._summary = None
        self._log = []

    def fix(self, code, section, location, details):
        # When running tests, section will be empty
        if not section:
            print("FIX:", code, details)
            return

        if self._summary is not None:
            item = f"/*{section.path}*/ {location} {details}"
            if item not in self._summary:
                self._summary.append(item)

        self._log.append(("autofix_" + code, section.page, section.path, location, None))

    def warn(self, code, section, location, details=None):
        if self._log is None:
            print("WARN", code, section.path, location, details)
        self._log.append((code, section.page, section.path, location, details))

    def process(self, text, page, summary=None, options=None):
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

        entry = sectionparser.parse(text, page)
        if not entry:
            return [] if summary is None else text

        ALLOWED_SIBLINGS = ["quote", "ux", "bare_ux", "syn", "ant", "hyper", "hypo", "holo", "merq", "tropo", "comero", "cot", "parasyn", "perfect", "imperfect", "active", "midvoice", "alti", "co", "cot" ]

        for section in entry.ifilter_sections(matches=lambda x: x.title in ALL_POS):

            # Only operate on non-english entries
            lang_id = ALL_LANGS.get(section._topmost.title)
            if not lang_id or lang_id == "en":
                continue

            pos = sectionparser.parse_pos(section)
            if not pos:
                continue

            all_fixable_ux = []

            for sense in pos.senses:

                fixable_items = []
                bare_ux_items = [c for c in sense._children if c._type == "bare_ux"]

#                # TODO: Manual review - if there are exactly 2 bare_ux_items and neither have children
#                # then the second item may be the translation of the first item
#                if len(bare_ux_items) == 2 and all(not i._children for i in bare_ux_items):
#                    if any(c._type in ["unknown", "sense"] for c in sense._children):
#                        continue
#                    idx_bare_ux_items = [idx for idx, c in enumerate(sense._children) if c._type == "bare_ux"]
#                    print("MULTI UX SIBLINGS", idx_bare_ux_items, str(sense))
#                    if idx_bare_ux_items[1] == idx_bare_ux_items[0]+1:
#                        self.warn("fixme_multi_ui", section, "", "")
#                        continue

                for item in bare_ux_items:
                    passage = str(item.data)

                    if lang_id == "en":
                        # English UX items must be complete sentences
                        if item._children:
                            self.warn("english_with_translation", section, item.name, str(item))
                            continue

                        if not is_sentence(passage):
                            self.warn("english_passage_not_sentence", section, item.name, passage)
                            continue

                        fixable_items.append(item)
                    else:

                        # Has translation, probably a good UX
                        if item._children:
                            assert len(item._children) == 1
                            fixable_items.append(item)

                        # No translation, make sure the passage looks like a sentence
                        else:
                            if not is_sentence(passage):
                                #self.warn("nonenglish_passage_not_sentence", section, item.name, passage)
                                continue
                            fixable_items.append(item)


                if len(fixable_items) != len(bare_ux_items):
                    if len(bare_ux_items) > 1:
                        self.warn("unfixable_multi_ux", section, item.name, str(sense))
                    continue

                if len(bare_ux_items) > 1:
                    self.warn("multi_bare_ux", section, "", str(sense))
                    continue

                if bare_ux_items and any(c._type not in ALLOWED_SIBLINGS for c in sense._children):
                    self.warn("bare_ux_with_unhandled_siblings", section, "", str(sense))
                    continue

                all_fixable_ux += fixable_items

            to_remove = []
            for item in all_fixable_ux:
                for idx, wikiline in enumerate(section.content_wikilines):
                    if str(item.data) in str(wikiline):

                        assert is_italic(item.data)
                        passage = item.data[2:-2]

                        translation = None
                        if item._children:
                            assert len(item._children) == 1
                            translation = item._children[0].data

                            if is_italic(translation.strip()):
                                translation = translation.strip()[2:-2]

                            assert translation.strip()

                            to_remove.append(idx+1)


                        if "|" in passage:
                            self.warn("pipe_in_ux_passage", section, item.name, passage)
                            continue

                        if translation and "|" in translation:
                            self.warn("pipe_in_ux_translation", section, item.name, translation)
                            continue

                        if "://" in passage:
                            self.warn("url_in_ux_passage", section, item.name, passage)
                            continue

                        if translation and "://" in translation:
                            self.warn("url_in_ux_translation", section, item.name, translation)
                            continue

                        new_wikiline = item.prefix + " {{ux|" + lang_id + "|" + passage
                        if translation:
                            if len(translation) > 80 or len(passage) > 80:
                                new_wikiline += "\n|t=" + translation
                            else:
                                new_wikiline += "|" + translation
                        new_wikiline += "}}"
                        section.content_wikilines[idx] = new_wikiline

                        self.fix("bare_ux", section, item.name, "converted bare ux to template")
                        entry_changed = True

            for idx in reversed(to_remove):
                del section.content_wikilines[idx]

        if summary is None:
            return self._log

        if entry_changed:
            return str(entry)

        return text
