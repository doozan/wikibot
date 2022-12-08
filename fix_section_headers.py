#!/usr/bin/python3

import re
from collections import defaultdict
from Levenshtein import distance as fuzzy_distance

from autodooz.sectionparser import SectionParser, Section
from autodooz.sections import ALL_LANGS, ALL_L3, ALL_POS, ALL_POS_CHILDREN, COUNTABLE_SECTIONS
from .lang_data import ALT_LANGS

# Tags that generate a <ref> link
ref_tags = ["<ref[ :>]", r'{{ja-pron\|[^}]*(acc_ref|accent_ref)'] #}} code folding fix
PATTERN_REF_TAGS = "(?i)(" + "|".join(ref_tags) + ")"

# Tags that generate <references/>
PATTERN_REFS = r"(?i)(<\s*references|{{reflist)"

def get_fuzzy_matches(title, words, max_distance):
    #print(title, words, max_distance)
    #for x in words:
    #    print(title, x, fuzzy_distance(title, x))
    return [x for x in words if fuzzy_distance(title, x)<=max_distance]

from section_headers_fuzzy_matches import L2_FUZZY_MATCHES, L3_FUZZY_MATCHES

import unicodedata
def strip_accents(s):
   return ''.join(c for c in unicodedata.normalize('NFD', s)
                  if unicodedata.category(c) != 'Mn')

L2_FIXES = {
    'allowed': ALL_LANGS,
    #'allowed_no_accents': {strip_accents(x) for x in ALL_LANGS},
    # No fuzzy matches for language, too sloppy
    #'fuzzy_matches': L2_FUZZY_MATCHES,

    'replacements': {
        'Arabic': 'Arabic', # unicode char on the A
        'Assyrian neo-aramiac': 'Assyrian Neo-Aramaic',
        'Guarani': 'Guaraní',
        'Hijaz Arabic': 'Hijaz Arabic',
        'Ingrain': 'Ingrian',
        'Iñupiaq': 'Inupiaq',
        'Iriga Bikolano': 'Iriga Bicolano',
        'Jjapanese': 'Japanese',
        'Kapampangn': 'Kapampangan',
        'Karachay Balkar': 'Karachay-Balkar',
        'Khorasani Turkic': 'Khorasani Turkish',
        'Māori': 'Maori',
        'Megrelian': 'Mingrelian',
        'Norwegian (Bokmål)': 'Norwegian Bokmål',
        'Ogba': 'Ogbah',
        'Panjabi': 'Punjabi',
        'Prasun': 'Prasuni',
        'Serbo-croatian': 'Serbo-Croatian',
        'Shekhani': 'Sekani',
        'Slovenian': 'Slovincian',
        'Tai-nüa': 'Tai Nüa',
        'Tai nue': 'Tai Nüa',
        'Transligual': 'Translingual',
        'Ukrainain': 'Ukrainian',
        'Yidish': 'Yiddish',
    }
}
#print(len(L2_FIXES["allowed"]), len(L2_FIXES["allowed_no_accents"]))
#assert len(L2_FIXES["allowed"]) == len(L2_FIXES["allowed_no_accents"])

L3_FIXES = {
    'allowed': ALL_L3,

    'fuzzy_matches': L3_FUZZY_MATCHES,

    'replacements': {
        "Alternate forms": "Alternative forms",
        "Alternate form": "Alternative forms",

        "Alternate term": "Alternative forms",
        "Alternate terms": "Alternative forms",
        "Alternative term": "Alternative forms",
        "Alternative terms": "Alternative forms",

        "Alternative spellings": "Alternative forms",

        "Alternate script": "Alternative scripts",
        "Alternate scripts": "Alternative scripts",

        #"Note": "Usage notes",
        #"Notes": "Usage notes",
        #"Usage": "Usage notes",
    },
}

POS_CHILD_FIXES = {
    'allowed': ALL_POS_CHILDREN + [
        "Adjectives", # Used by Arabic
        "Nouns", # Used by Arabic
        "Verbs", # Used by Arabic
        "Idioms", # Used by Japanese
        "Proverbs", # Used by Japanes
        "Preverb", # Used by Ojibwe
        "Prenoun", # Used by Munsee
        "Proper nouns", # Used by Arabic
        ],

    'fuzzy_matches': { k:1 for k in ALL_POS_CHILDREN } | {
        "Descendants": 3
    },

    'replacements' : {
        "Derived words": "Derived terms",
        "Derivatived term": "Derived terms",
        "Derivative terms": "Derived terms",
        "Derived form": "Derived terms",
        "Derived forms": "Derived terms",
        "Derived words": "Derived terms",
    }

}

def _validate(fixes):
    for word, max_typos in fixes.get("fuzzy_matches", {}).items():
        similar = get_fuzzy_matches(word, fixes["allowed"], max_typos)
        if len(similar) > 1:
            raise ValueError(f"{word} is not a candidate for typo matching, because it's too similar to {similar}")

_validate(L2_FIXES)
_validate(L3_FIXES)
_validate(POS_CHILD_FIXES)

def get_fixed_title(title, fixes):

    allowed = fixes["allowed"]

    if title in allowed:
        return

    title = title.capitalize()
    if title in allowed:
        print("cap change")
        return title

    if title.endswith("s") and title[:-1] in allowed:
        print("stripped s")
        return title[:-1]

    if title in fixes.get("replacements", []):
        print("exact replacement")
        return fixes["replacements"].get(title)

    if title in ALT_LANGS:
        alt_titles = ALT_LANGS[title]
        if len(alt_titles) == 1:
            print("alt lang")
            return alt_titles[0]
        else:
            print("ERROR: multi alt langs", title, alt_titles)
            return

    fuzzy_matches = []
    for new_title, max_typos in fixes.get("fuzzy_matches",{}).items():
        fuzzy_matches += get_fuzzy_matches(title, [new_title], max_typos)

    if len(fuzzy_matches) > 1:
        print("ERROR: ambiguous fuzzy matches", title, fuzzy_matches)
    elif len(fuzzy_matches) == 1:
        print("fuzzy match")
        return fuzzy_matches[0]

def fix_title(section, fixes):
    if "=" in section.title:
        return

    if section.title in fixes["allowed"]:
        return

    new_title = get_fixed_title(section.title, fixes)
    if new_title:
        print([section.path], "renamed to", [new_title])
        section.title = new_title

    else:
        if section.level == 2:
            get_maybe_langs(section.title)
        print("unfixable", section.title)


def get_maybe_langs(title):
    for limit in range(1,5):
        fuzzy_matches = []
        for new_title in ALL_LANGS:
            fuzzy_matches += get_fuzzy_matches(title, [new_title], limit)
        if fuzzy_matches:
            print(title, f"MAYBE (fuzzy match {limit})", fuzzy_matches)
            if len(fuzzy_matches) > 1:
                return

    for limit in range(1,5):
        fuzzy_matches = []
        for new_title in ALT_LANGS:
            fuzzy_matches += get_fuzzy_matches(title, [new_title], limit)

        if fuzzy_matches:
            for match in fuzzy_matches:
                print(title, f"MAYBE (fuzzy match {limit} alt lang name {new_title})", ALT_LANGS[new_title])
            if len(fuzzy_matches) > 1:
                return


def fix_section_titles(entry):
    """
    Spell check section titles
    """

    changes = []

    for section in entry.ifilter_sections():

        if section.level < 2:
            continue

        if section.level == 2:
            fix_title(section, L2_FIXES)

#        elif section.parent.title in COUNTABLE_SECTIONS or section.parent.title in ALL_LANGS:
#            fix_title(section, L3_FIXES)

#        elif section.parent.title in ALL_POS:
#            fix_title(section, POS_CHILD_FIXES)

#        else:
#            fix_title(section, OTHER_FIXES)

    return changes


def adjust_level(level, sections):
    changed = False
    for section in sections:
        if section.level != level:
            changed = True
            section.level = level

        if section._children and adjust_level(level+1, section._children):
            changed = True
    return changed

def fix_section_levels(entry):
    """
    Ensure each child's level matches parent level +1
    Returns True if any levels have been changed, otherwise False
    Safe to run unsupervised
    """

    if not entry._children:
        return

    if entry._children[0].level != 2:
        return
#        raise ValueError("First section is not L2")


    return adjust_level(2, entry._children)


def fix_bad_l2(entry):
    """ Find known non-language sections that are L2 and move them into the previous L2 entry """
    changes = []
    reparent = []
    prev = None
    for i, child in enumerate(entry._children):
        if child.level != 2:
            return changes

        title = child.title.strip("=")

        if prev and title in ALL_L3:
            reparent.append((i, prev))
        prev = child

    # pop starting from the end so it doesn't change the index
    for idx, newparent in reversed(reparent):
        child = entry._children.pop(idx)
        old_path = child.path
        newparent._children.append(child)
        child.parent = newparent
        child.level = 3
        child.title = child.title.strip("=")
        adjust_level(3, child._children)
        new_path = child.path
        changes.append(f"/*{old_path}*/ moved errant L2 to {new_path}")

    return changes


def fix_remove_pos_counters(entry):
    """ Ensure POS entries do not have a numeric counter """

    changes = []
    for section in entry.ifilter_sections():
        if section.count and section.title in ALL_POS:
            changes.append(f"/*{section.path}*/ removed counter from section title")
            section.count = None

    return changes

def remove_empty_sections(entry):

    changes = []
    for section in reversed(entry.filter_sections()):
        if section.level == 2:
            continue

        if section.title in COUNTABLE_SECTIONS:
            continue

        if not section._lines and not section._children:
            section.parent._children.remove(section)
            changes.append(f"/*{section.path}*/ removed empty section")

    return changes

def add_missing_references(entry):

    changes = []
    for section in entry._children:
        if re.search(PATTERN_REF_TAGS, str(section)) and not re.search(PATTERN_REFS, str(section)):
            ref_section = next(section.ifilter_sections(matches=lambda x: x.title == "References"), None)
            if ref_section:
                ref_section._lines.insert(0, "<references/>")
                changes.append(f"/*{ref_section.path}*/ added missing <references/>")
                continue

            new_section = Section(entry, 3, "References")
            new_section.add("<references/>")

            # Anagrams is always the last section, otherwise References is the last
            if section._children and section._children[-1].title == "Anagrams":
                section._children.insert(-1, new_section)
            else:
                section._children.append(new_section)

            changes.append(f"/*{section.path}*/ added References section")

    return changes

def rename_misnamed_references(entry):

    changes = []
    for section in entry.ifilter_sections():
        if len(section._lines) == 1 \
                and re.match(PATTERN_REFS, section._lines[0].strip()) \
                and "References" not in section.lineage \
                and section.title == "Further reading":

                    changes.append(f"/*{section.path}*/ renamed to References")
                    section.title = "References"

    return changes

def rename_misnamed_quotations(entry):

    changes = []
    for section in entry.ifilter_sections():
        if len(section._lines) == 1 \
                and re.match("{{seeCites.*?}}", section._lines[0].strip()) \
                and "Quotation" not in section.lineage \
                and section.title == "Quotations":
                    changes.append(f"/*{section.path}*/ renamed to Quotations")
                    section.title = "Quotations"

    return changes

# called by wikifix to mass apply the above fixes
def process(text, title, summary, custom):

    #if ":" in title or "/" in title:
    #    return text

    changes = []
    entry = SectionParser(text, title)

    changes += fix_section_titles(entry)
    changes += fix_remove_pos_counters(entry)
    changes += fix_bad_l2(entry)
    changes += rename_misnamed_references(entry)
    changes += rename_misnamed_quotations(entry)
    changes += add_missing_references(entry)

    # not safe to run unsupervised
    #changes += remove_empty_sections(entry)

    fix_section_levels(entry) and changes.append("adjusted section levels")

    if not changes:
        return text

    summary += changes

    return str(entry)
