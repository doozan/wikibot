import enwiktionary_sectionparser as sectionparser
import re
import unicodedata

from autodooz.sections import ALL_LANGS, ALL_L3, ALL_POS, ALL_POS_CHILDREN, COUNTABLE_SECTIONS
from collections import defaultdict


#NONSTANDARD_OTHER = {
#    "Transliteration",
#    "Compounds",
#    "Readings",
#    "Cuneiform sign",
#}


# Sections that will be at the very bottom, ranked as they appear here
BOTTOM_SORT = {k:v for v,k in enumerate([
    "Definitions",

    "Usage notes",
    "Reconstruction notes",
    "Inflection",
    "Declension",
    "Conjugation",
    "Quotations",
    "Alternative forms",
    "Alternative scripts",
    "Alternative reconstructions",

    "Synonyms",
    "Antonyms",
    "Hypernyms",
    "Hyponyms",
    "Meronyms",
    "Holonyms",
    "Troponyms",
    "Coordinate terms",
    "Derived terms",
    "Derived characters", # not in WT:ELE
    "Related terms",
    "Related characters", # not in WT:ELE
    "Collocations",
    "Descendants",
    "Translations",
    "See also",
    "Mutation",
    "Statistics", # Not in WT:ELE, but used in 20k pages
    "Trivia",
    "References",
    "Further reading",
    "Anagrams",
], 1)}

# Categories that can be safely be forced all the way to the bottom
BOTTOM_SORT_SAFE = {k:v for v,k in enumerate([
    "References",
    "Further reading",
    "Anagrams",
], 1)}


# Categories that can be safely sorted to the top (above first POS)
TOP_SORT = {k:v for v,k in enumerate([
        "Description",
        "Glyph origin",
        "Kanji", # Differs from WT:ELE order, but follows common practice in Japanese
        "Hanzi", # Differs from WT:ELE order, but follows common practice in Japanese
        "Sign values", # Not in WT:ELE, used in Akkadian
        "Etymology",
        "Pronunciation",
        "Production",
        "Hanja", # Differs from WT:ELE order, but follows common practice in Korean
        "Han character", # Difers from WT:ELE order, but follows common practice in Translingual
    ], 1)}


ALL_SORTABLE = TOP_SORT.keys() | ALL_POS.keys() | BOTTOM_SORT.keys()


def is_spanish_form_header(text):
    return bool(re.match(r"\s*{{(head|head-lite)\|es\|(past participle|[^|]* form[ |}])", text, re.MULTILINE)) \
            or "{{es-past participle" in text

def is_spanish_form(section):
    wikiline = ""
    # Skip leading empty lines (shouldn't exist, but just to be safe)
    for wikiline in section.content_wikilines:
        if wikiline.strip():
            break
    return is_spanish_form_header(wikiline)

class SectionOrderFixer:

    def __init__(self):
        # Only used when calling functions directly during unit testing
        # all other uses should just call process() which will set these variables
        self._summary = None
        self._log = []
        self.page_title = "test"

    @staticmethod
    def normalize_lang(s):

        # strip diacritics
        res = ''.join(c for c in unicodedata.normalize('NFD', s)
                      if unicodedata.category(c) != 'Mn')

        # remove ' marks
        # replace hypens with spaces
        return res.replace("'", "").replace("-", " ")

    @classmethod
    def get_language_key(cls, title):

        if title == "Translingual":
            return (0, title)

        elif title == "English":
            return (1, title)

        return (2, cls.normalize_lang(title))

    def sort_l2(self, entry):

        # Only sort if all sections are L2 and match expected language titles
        if not entry._children or not all(c.level == 2 and c.title in ALL_LANGS for c in entry._children):
            return

        sorted_sections = sorted(entry._children, key=lambda x: self.get_language_key(x.title))
        if sorted_sections != entry._children:
            entry._children = sorted_sections
            self.fix("l2_sort", entry, "Sorted L2 languages per [[WT:ELE]]")

    @staticmethod
    def has_alt_before_pos(l3):
        for c in l3.ifilter_sections(recursive=False):
            if c.title in ["Alternative forms", "Alternative scripts"]:
                return True
            elif c.title in ALL_POS:
                return False
        return False


    # L3 can be either the full language entry or, if there are countable sections, each countable sections
    #
    # ===Etymology===
    # ===Noun===
    # ===References===
    # ===Usage notes===
    #
    # or
    #
    # ===Etymology 1===
    # ====Noun====
    # ====References====
    # ====Usage notes====
    #
    def sort_l3(self, language):

        if language.title not in ALL_LANGS:
            return

        if not self.has_only_expected_children(language, ALL_L3):
            return

        sortable = language.filter_sections(matches=lambda x: x.title in COUNTABLE_SECTIONS and x.count)
        if not sortable:
            sortable = [ language ]

        for l3 in sortable:

            if not self.has_only_expected_children(l3, ALL_L3):
                continue

            # Special case sorting for "Alternative forms" or "Alternative scripts"
            # per WT:ETE, "Alternative forms" must be the first item IFF it appears before a POS item
            # Otherwise, it can be sorted below the POS according to the normal sort order
            alt_first = self.has_alt_before_pos(l3)

            # Spanish can sort all of the section in one go
            if language.title == "Spanish":
                orig = list(l3._children)
                l3._children.sort(key=lambda x: self.get_l3_sort_key(x, alt_first=alt_first, lemmas_before_forms=True))
                if orig != l3._children:
                    self.fix("l3_sort", l3, "sorted sections per [[WT:ELE]] with forms before lemmas")

            # Sort other languages in two passes to generate a more verbose summary
            else:
                orig = list(l3._children)
                totals = defaultdict(int)
                pos_count = 0
                pos_is_contig = True # All of the POS sections are contiguous
                prev_pos = False
                for section in l3._children:
                    totals[section.title] += 1
                    is_pos = section.title in ALL_POS

                    if is_pos:
                        if pos_count and not prev_pos:
                            pos_is_contig = False
                        pos_count += 1

                    prev_pos = is_pos

                has_dup = False
                for title, count in totals.items():
                    if count > 1 and (title in BOTTOM_SORT_SAFE or title in TOP_SORT):
                        # Multi countables shouldn't be sorted, but don't need to produce a warning
                        if title not in COUNTABLE_SECTIONS:
                            self.warn("dup_sections", f"{l3.path} has {count} {title} sections")
                        has_dup = True
                # Don't sort sections with double items
                if has_dup:
                    continue


                # If all POS sections are contiguous (without other sections between them) and all of the sections are sortable, sort everything in one pass
                if pos_is_contig and all(title in ALL_SORTABLE for title in totals.keys()):
                    orig = list(l3._children)
                    l3._children.sort(key=lambda x: self.get_l3_sort_key(x, alt_first=alt_first))
                    if orig != l3._children:
                        self.fix("l3_sort", l3, "sorted sections per [[WT:ELE]]")

                else:
                    l3._children.sort(key=lambda x: self.get_l3_topsort_key(x, alt_first=alt_first, lemmas_before_forms=False))
                    if orig != l3._children:
                        top = []
                        for x in l3._children:
                            if x.title not in TOP_SORT and (not alt_first or x.title not in ["Alternative forms", "Alternative scripts"]):
                                break
                            top.append(x.title)
                        self.fix("l3_sort", l3, "sorted " + "/".join(top) + " to top per [[WT:ELE]]")

                    orig = list(l3._children)
                    l3._children.sort(key=lambda x: self.get_l3_sort_key_safe(x, alt_first=alt_first, lemmas_before_forms=False))
                    if orig != l3._children:
                        self.fix("l3_sort", l3, "sorted References/Further reading/Anagrams to bottom per [[WT:ELE]]")


    def sort_pos_children(self, pos):

        # Only sort if the section itself is really a POS
        if pos.title not in ALL_POS:
            raise ValueError("unexpected POS, refusing to sort", pos.title)

        can_sort = True
        for child in pos._children:
            if child.title not in ALL_POS_CHILDREN:
                self.warn("unexpected_child", f"{pos.path} has unexpected child {child.title}")
                can_sort = False

        if not can_sort:
            return

        orig = list(pos._children)
        pos._children.sort(key=lambda x: ALL_POS_CHILDREN.index(x.title))
        if orig != pos._children:
            self.fix("pos_sort", pos, "sorted child sections per [[WT:ELE]]")

    @staticmethod
    def get_l3_sort_key_safe(item, alt_first=False, lemmas_before_forms=False):
        return (0, 0, BOTTOM_SORT_SAFE.get(item.title, 0))

    @staticmethod
    def get_l3_topsort_key(item, alt_first=False, lemmas_before_forms=False):
        if alt_first and item.title in ["Alternative forms", "Alternative scripts"]:
            return (0, -1, item.title)

        return (0, 0, TOP_SORT.get(item.title, 999))

    @staticmethod
    def get_l3_sort_key(item, alt_first=False, lemmas_before_forms=False):

        if alt_first and item.title in ["Alternative forms", "Alternative scripts"]:
            return (0, -1, item.title)

        if item.title in TOP_SORT:
            sort_group = 0
            sort_class = 0
            sort_item = TOP_SORT[item.title]
        elif item.title in ALL_POS:
            sort_group = 1
            sort_class = 0
            sort_item = 0
            if lemmas_before_forms:
                if not is_spanish_form(item):
                    sort_class = 0
                    sort_item = 0  # Lemmas remain in original order
                else:
                    sort_class = 1
                    sort_item = item.title # Forms sorted a-z

        elif item.title in BOTTOM_SORT:
            sort_group = 2
            sort_class = 0
            sort_item = BOTTOM_SORT[item.title]
        else:
            raise ValueError("Unhandled section:", item.path)
            #error("Unexpected section:", item.title)

        return (sort_group, sort_class, sort_item)

    def has_only_expected_children(self, parent, allowed_children):
        # Returns True if all child sections are in allowed_children
        valid = True

        lineage = [x.title for x in list(parent.ancestors)[:-1]]
        for section in parent.filter_sections(recursive=False):
            if section.title not in allowed_children:
                self.warn("unexpected_child", section.path)
                valid = False

            if section.title in lineage:
                self.warn("bad_lineage", section.path)
                valid = False

        return valid

    def fix(self, reason, section, details):
        if isinstance(section, sectionparser.SectionParser):
            page = section.page
            path = ""
        else:
            page = section.page
            path = section.path

        if self._summary is not None:
            if path:
                self._summary.append(f"/*{path}*/ {details}")
            else:
                self._summary.append(f"{details}")

        self._log.append((reason, page, path, details))


    def warn(self, reason, details):
        self._log.append((reason, self.page_title, None, details))

    # Sorts everything
    def process(self, page_text, page_title, summary=None, options=None):

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

        self.page_title = page_title
        self._changes = []

        entry = sectionparser.parse(page_text, page_title)
        if not entry:
            return page_text if summary is not None else self._log

        self.sort_l2(entry)

        for lang in entry.filter_sections(recursive=False):

            self.sort_l3(lang)

            # Sort POS entries if the POS is a direct child of language or countable section (avoids sorting sections buried underneath something unexpected)
            all_pos = entry.filter_sections(matches=lambda x: x.title in ALL_POS and (x.parent.title in COUNTABLE_SECTIONS or x.parent.title in ALL_LANGS))
            for section in all_pos:
                self.sort_pos_children(section)

        return str(entry) if summary is not None else self._log
