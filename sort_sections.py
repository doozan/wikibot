#import locale
import re
import unicodedata

from autodooz.sectionparser import SectionParser
from autodooz.sections import ALL_LANGS, ALL_POS, ALL_POS_CHILDREN, COUNTABLE_SECTIONS
from autodooz.form_fixer import FormFixer

def strip_accents(s):
   return ''.join(c for c in unicodedata.normalize('NFD', s)
                  if unicodedata.category(c) != 'Mn')

def get_language_key(title):

    if title == "Translingual":
        return (0, title)

    elif title == "English":
        return (1, title)

    return (2, strip_accents(title))

def sort_languages(entry):

    changes = []

    # Only sort if all sections are L2 and match expected language titles
    if not entry._children or not all(c.level == 2 and c.title in ALL_LANGS for c in entry._children):
        return changes

    sorted_sections = sorted(entry._children, key=lambda x: get_language_key(x.title))
    if sorted_sections != entry._children:
        entry._children = sorted_sections
        changes.append("Sorted L2 languages per WT:ELE")

    return changes

def sort_pos(language):

    changes = []

    assert language.title in L3_SORT_LANGUAGES
    lemmas_before_forms = language.title in L3_LEMMAS_BEFORE_FORMS

    sortable = language.filter_sections(matches=lambda x: x.title in COUNTABLE_SECTIONS and x.count)
    if not sortable:
        sortable = [ language ]

    for sort_section in sortable:
        # Special case sorting for "Alternative forms" or "Alternative scripts"
        # per WT:ETE, "Alternative forms" must be the first item IFF it appears before a POS item
        # Otherwise, it can be sorted below the POS according to the normal sort order
        alt_first = False
        for c in sort_section._children:
            if c.title in ["Alternative forms", "Alternative scripts"]:
                alt_first = True
                break
            elif c.title in ALL_POS:
                break

        unhandled = [x for x in sort_section._children if
                x.title not in top_sort
                and x.title not in bottom_sort
                and x.title not in ALL_POS]
        if unhandled:
#            for section in unhandled:
#                print("unhandled section, not sorting", section.path)
            continue


        # Spanish can sort all of the section in one go
        if language.title == "Spanish":
            orig = list(sort_section._children)
            sort_section._children.sort(key=lambda x: get_l3_sort_key(x, alt_first=alt_first, lemmas_before_forms=lemmas_before_forms))
            if orig != sort_section._children:
                changes.append(f"/*{sort_section.path}*/ sorted sections per WT:ELE with forms before lemmas")

        # Since English only sorts a few sections, do it in multiple passes to generate a more verbose summary
        else:
            orig = list(sort_section._children)
            sort_section._children.sort(key=lambda x: get_l3_sort_key_altforms(x, alt_first=alt_first, lemmas_before_forms=lemmas_before_forms))
            if orig != sort_section._children:
                changes.append(f"/*{sort_section.path}*/ moved AltForms found before first POS to first section per WT:ELE")

            orig = list(sort_section._children)
            sort_section._children.sort(key=lambda x: get_l3_sort_key_safe(x, alt_first=alt_first, lemmas_before_forms=lemmas_before_forms))
            if orig != sort_section._children:
                changes.append(f"/*{sort_section.path}*/ moved References/Further reading/Anagrams to bottom per WT:ELE")

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
def sort_l2(text, title, summary, options):

    entry = SectionParser(text, title)

    changes = sort_languages(entry)
    if not changes:
        return text

    summary += changes

    return str(entry)

L3_SORT_LANGUAGES = ["Spanish", "English"]
L3_LEMMAS_BEFORE_FORMS = ["Spanish"]

def sort_l3(text, title, summary, options):

    if ":" in title:
        return text

    entry = SectionParser(text, title)
    languages = entry.filter_sections(matches=lambda x: x.title in L3_SORT_LANGUAGES, recursive=False)

    changes = []
    for language in languages:
        old = str(language)
        changes += sort_pos(language)
#        if str(language) != old:
#        extra_options = " with lemmas before forms" if language.title in L3_LEMMAS_BEFORE_FORMS else ""
#            #changes.append(f"/*{language.title}*/ sorted L3 sections per WT:ELE{extra_options}")
#            changes.append(f"/*{language.title}*/ moved AltForms found before first POS to first section, per WT:ELE")
#            #changes.append(f"/*{language.title}*/ moved References/Further reading/Anagrams to bottom per WT:ELE")

    if not changes:
        return text

    summary += changes

    return str(entry).rstrip()
