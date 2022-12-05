import re
import unicodedata

from autodooz.sectionparser import SectionParser
from autodooz.sections import ALL_LANGS, ALL_L3, ALL_POS, ALL_POS_CHILDREN, COUNTABLE_SECTIONS
from autodooz.form_fixer import FormFixer
from collections import defaultdict

def strip_accents(s):
   return ''.join(c for c in unicodedata.normalize('NFD', s)
                  if unicodedata.category(c) != 'Mn')

def get_language_key(title):

    if title == "Translingual":
        return (0, title)

    elif title == "English":
        return (1, title)

    return (2, strip_accents(title))

def sort_l2(entry):

    changes = []

    # Only sort if all sections are L2 and match expected language titles
    if not entry._children or not all(c.level == 2 and c.title in ALL_LANGS for c in entry._children):
        return changes

    sorted_sections = sorted(entry._children, key=lambda x: get_language_key(x.title))
    if sorted_sections != entry._children:
        entry._children = sorted_sections
        changes.append("Sorted L2 languages per WT:ELE")

    return changes


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
def sort_l3(language):

    changes = []

    if language.title not in ALL_LANGS:
        return changes

    if not has_only_expected_children(language, ALL_L3):
        return changes

    sortable = language.filter_sections(matches=lambda x: x.title in COUNTABLE_SECTIONS and x.count)
    if not sortable:
        sortable = [ language ]

    for l3 in sortable:

        if not has_only_expected_children(l3, ALL_L3):
            continue

        # Special case sorting for "Alternative forms" or "Alternative scripts"
        # per WT:ETE, "Alternative forms" must be the first item IFF it appears before a POS item
        # Otherwise, it can be sorted below the POS according to the normal sort order
        alt_first = has_alt_before_pos(l3)

        # Spanish can sort all of the section in one go
        if language.title == "Spanish":
            orig = list(l3._children)
            l3._children.sort(key=lambda x: get_l3_sort_key(x, alt_first=alt_first, lemmas_before_forms=True))
            if orig != l3._children:
                changes.append(f"/*{l3.path}*/ sorted sections per WT:ELE with forms before lemmas")

        # Sort other languages in two passes to generate a more verbose summary
        else:
#            orig = list(l3._children)
#            l3._children.sort(key=lambda x: get_l3_sort_key_altforms(x, alt_first=alt_first, lemmas_before_forms=False))
#            if orig != l3._children:
#                changes.append(f"/*{l3.path}*/ moved AltForms found before first POS to first section per WT:ELE")

            orig = list(l3._children)
            totals = defaultdict(int)
            for section in l3._children:
                totals[section.title] += 1

            if any(count > 1 and title in bottom_sort_safe for title, count in totals.items()):
                # Don't sort sections with double items
                # TODO: log this
                continue

            l3._children.sort(key=lambda x: get_l3_sort_key_safe(x, alt_first=alt_first, lemmas_before_forms=False))
            if orig != l3._children:
                changes.append(f"/*{l3.path}*/ sorted References/Further reading/Anagrams to bottom per WT:ELE")

    return changes


def sort_pos_children(pos):

    changes = []

    # Only sort if the section itself is really a POS
    if pos.title not in ALL_POS:
        raise ValueError("unexpected POS, refusing to sort", pos.title)

    can_sort = True
    for child in pos._children:
        if child.title not in ALL_POS_CHILDREN:
            print(pos.path, "can't sort POS, found unexpected child section", child.title)
            can_sort = False

    if not can_sort:
        return changes

    orig = list(pos._children)
    pos._children.sort(key=lambda x: ALL_POS_CHILDREN.index(x.title))
    if orig != pos._children:
        changes.append(f"/*{pos.path}*/ sorted child sections per WT:ELE")

    return changes



# Sections that will be a the very top, ranked as they appear here
top_sort = {k:v for v,k in enumerate([
        #"Alternative forms",
        "Description",
        "Glyph origin",
        "Etymology",
        "Pronunciation",
        "Production",
    ], 1)}

#NONSTANDARD_OTHER = {
#    "Transliteration",
#    "Compounds",
#    "Readings",
#    "Cuneiform sign",
#}


# Sections that will be at the very bottom, ranked as they appear here
bottom_sort = {k:v for v,k in enumerate([
        "Definitions",

        "Usage notes",
        "Reconstruction notes",
        "Inflection",
        "Declension",
        "Conjugation",
        "Mutation",
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
        "Statistics", # Not in WT:ELE, but used in 20k pages
        "Trivia",
        "See also",
        "References",
        "Further reading",
        "Anagrams",
    ], 1)}

# Categories that can be safely sorted the bottom
bottom_sort_safe = {k:v for v,k in enumerate([
        "References",
        "Further reading",
        "Anagrams",
    ], 1)}

def get_l3_sort_key_altforms(item, alt_first=False, lemmas_before_forms=False):
    if alt_first and item.title in ["Alternative forms", "Alternative scripts"]:
        return (0, -1, item.title)

    return (0,0,0)

def get_l3_sort_key_safe(item, alt_first=False, lemmas_before_forms=False):
    return (0, 0, bottom_sort_safe.get(item.title, 0))

def get_l3_sort_key(item, alt_first=False, lemmas_before_forms=False):

    if alt_first and item.title in ["Alternative forms", "Alternative scripts"]:
        return (0, -1, item.title)

    if item.title in top_sort:
        sort_group = 0
        sort_class = 0
        sort_item = 0 # str(top_sort[item.title])
    elif item.title in ALL_POS:
        sort_group = 1
        sort_class = 0
        sort_item = 0
        if lemmas_before_forms:
            if not FormFixer.is_form(item):
                sort_class = 0
                sort_item = 0  # Lemmas remain in original order
            else:
                sort_class = 1
                sort_item = item.title # Forms sorted a-z

    elif item.title in bottom_sort:
        sort_group = 2
        sort_class = 0
        sort_item = bottom_sort[item.title]
    else:
        raise ValueError("Unhandled section:", item.path)
        #error("Unexpected section:", item.title)

    return (sort_group, sort_class, sort_item)


# Called by wikifix
def export_sort_l2(text, title, summary, options):

    entry = SectionParser(text, title)

    changes = sort_l2(entry)
    if not changes:
        return text

    summary += changes

    return str(entry)

def export_sort_l3(text, title, summary, options):

    if ":" in title:
        return text

    entry = SectionParser(text, title)
    languages = entry.filter_sections(recursive=False)

    changes = []
    for language in languages:
        old = str(language)
        changes += sort_l3(language)

    if not changes:
        return text

    summary += changes

    return str(entry).rstrip()


# Sorts everything
def process(page_text, page_title, summary=[], custom_args=None):

    entry = SectionParser(page_text, page_title)
    if entry.state != 0:
        print(page_title, "unfinished state", entry.state)
        return page_text

    summary += sort_l2(entry)

    for lang in entry.filter_sections(recursive=False):

        summary += sort_l3(lang)

        # Sort POS entries if the POS is a direct child of language or countable section (avoids sorting sections buried underneath something unexpected)
        all_pos = entry.filter_sections(matches=lambda x: x.title in ALL_POS and (x.parent.title in COUNTABLE_SECTIONS or x.parent.title in ALL_LANGS))
        for section in all_pos:
            summary += sort_pos_children(section)

    if not summary:
        return page_text

    return str(entry)

def has_only_expected_children(parent, allowed_children):
    for section in parent.filter_sections(recursive=False):
        if section.title not in allowed_children:
            return False
    return True
