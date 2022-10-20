#!/usr/bin/python3

import re
from collections import defaultdict
from enwiktionary_parser.languages import all_ids as language_constants
from Levenshtein import distance as fuzzy_distance

from autodooz.sectionparser import Section
from autodooz.sort_sections import ALL_L3_SECTIONS, ALL_POS, COUNTABLE_SECTIONS


# Tags that generate a <ref> link
ref_tags = ["<ref[ :>]", r'{{ja-pron\|[^}]*(acc_ref|accent_ref)'] #}} code folding fix
PATTERN_REF_TAGS = "(?i)(" + "|".join(ref_tags) + ")"

# Tags that generate <references/>
PATTERN_REFS = r"(?i)(<\s*references|{{reflist)"

ALL_LANGUAGE_IDS = language_constants.languages
ALL_LANGUAGE_NAMES = { v:k for k,v in ALL_LANGUAGE_IDS.items() }

# Words will be fuzzy matched for typos
# WARNING: do not use this for titles that have a similar form, EX: "Prxverb" -> ("Proverb", "Preverb")
COMMON_TYPOS = {
    "Alternative forms": 2,
    "Alternative scripts": 2,
    "Adjective": 2,
    "Declension": 2,
    "Etymology": 2,
    "Derived terms": 2,
    "Further reading": 2,
    "Pronunciation": 2,
    "References": 2,
    "Related terms": 2,
    "Synonyms": 1,
    "Noun": 1,
    "Usage notes": 2,
}

for word, max_typos in COMMON_TYPOS.items():
    similar = [x for x in ALL_L3_SECTIONS if x != word and fuzzy_distance(word, x)<=max_typos]
    if len(similar):
        raise ValueError(f"{word} is not a candidate for typo matching, because it's too similar to {similar}")

TITLE_FIXES = {
    "Alternate forms": "Alternative forms",
    "Alternate form": "Alternative forms",

    "Alternate term": "Alternative forms",
    "Alternate terms": "Alternative forms",
    "Alternative term": "Alternative forms",
    "Alternative terms": "Alternative forms",

    "Alternate script": "Alternative scripts",
    "Alternate scripts": "Alternative scripts",

    "Coordidnate terms": "Coordinate terms",
    "Coordinated terms": "Coordinate terms",

    "Decendants": "Descendants",

    "Derived words": "Derived terms",
    "Derivatived term": "Derived terms",
    "Derivative terms": "Derived terms",
    "Derived form": "Derived terms",
    "Derived forms": "Derived terms",
    "Derived words": "Derived terms",

    "Nouon": "Noun",
#    "Note": "Usage notes",
#    "Notes": "Usage notes",
#    "Usage": "Usage notes",
}

ALLOWED_VARIATIONS = {
#    "Adjectives", # Used by Arabic
#    "Nouns", # Used by Arabic
#    "Verbs", # Used by Arabic
    "Idioms", # Used by Japanese
    "Proverbs", # Used by Japanes
    "Preverb", # Used by Ojibwe
    "Prenoun", # Used by Munsee
#    "Proper nouns", # Used by Arabic
}

def fix_section_titles(entry):
    """
    Spell check section titles
    """

    changed = False
    for section in entry.ifilter_sections():
        if "=" in section.title:
            continue
        if section.level == 2:
            continue
        if section.title in ALL_L3_SECTIONS:
            continue
        if section.title in ALLOWED_VARIATIONS:
            continue


        title = section.title.capitalize()

        if title in ALL_L3_SECTIONS:
            changed = True
            section.title = title


        elif title.endswith("s") and title[:-1] in ALL_L3_SECTIONS:
            # Special handling for items like "Proverbs", "Idioms" that are allowed to appear below a POS section
            if section.level > 3 and section.parent.title not in COUNTABLE_SECTIONS:
                #print(f"{entry.title}: {section.title} should be allowed")
                pass

            else:
                changed = True
                section.title = title[:-1]
#
#        elif not title.endswith("s") and title + "s" in ALL_L3_SECTIONS:
#            changed = True
#            section.title = title + "s"

        elif title in TITLE_FIXES:
            changed = True
            section.title = TITLE_FIXES[title]

        else:
            for word, max_typos in COMMON_TYPOS.items():
                if fuzzy_distance(word, title) <= max_typos:
                    section.title = word
                    changed = True
                    break

            # Unfixable
            pass

    return changed


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
    prev = None
    reparent = []
    for i, child in enumerate(entry._children):
        if child.level != 2:
            return

        if prev and child.title in ALL_L3_SECTIONS:
            reparent.append((i, prev))
        prev = child

    # pop starting from the end so it doesn't change the index
    for idx, newparent in reversed(reparent):
        child = entry._children.pop(idx)
        newparent._children.append(child)
        child.level = 3
        adjust_level(3, child._children)

    return bool(reparent)


def fix_remove_pos_counters(entry):
    """ Ensure POS entries do not have a numeric counter """

    changed = False

    for section in entry.ifilter_sections():
        if section.count and section.title in ALL_POS:
            changed = True
            section.count = None

    return changed

def fix_counters(entry):

    # Assure that countable sections have a counter if there is more than one
    # And that they do NOT have a counter if there is less than one

    def adjust_countables(sections):
        changed = False
        countables = defaultdict(list)
        for section in sections:
            if section.title in COUNTABLE_SECTIONS:
                countables[section.title].append(section)

            if section._children:
                changed = adjust_countables(section._children) or changed

        for items in countables.values():
            total = len(items)
            for i,section in enumerate(items, 1):
                if total == 1:
                    if section.count != "":
                        section.count = ""
                        changed = True
                elif section.count != str(i):
                    section.count = str(i)
                    changed = True

        return changed

    return adjust_countables(entry._children)

def remove_empty_sections(entry):

    changed = False
    for section in reversed(list(entry.ifilter_sections())):
        if section.level == 2:
            continue

        if section.title in COUNTABLE_SECTIONS:
            continue

        if not section._lines and not section._children:
            section.parent._children.remove(section)
            changed = True

    return changed

def add_missing_references(entry):

    changed = False

    for section in entry._children:
        if re.search(PATTERN_REF_TAGS, str(section)) and not re.search(PATTERN_REFS, str(section)):
            ref_section = next(section.ifilter_sections(matches=lambda x: x.title == "References"), None)
            if ref_section:
                ref_section._lines.insert(0, "<references/>")
                changed = True
                continue

            new_section = Section(entry, 3, "References")
            new_section.add("<references/>")

            # Anagrams is always the last section, otherwise References is the last
            if section._children[-1].title == "Anagrams":
                section._children.insert(-1, new_section)
            else:
                section._children.append(new_section)

            changed = True

    return changed

def move_misnamed_references(entry):

    changed = False
    for section in entry.ifilter_sections():
        if len(section._lines) == 1 \
                and re.match(PATTERN_REFS, section._lines[0].strip()) \
                and "References" not in section.lineage \
                and section.title == "Further reading":

                    section.title = "References"
                    changed = True

                    target = section.parent
                    while target.level > 2 and target.parent.title not in COUNTABLE_SECTIONS:
                        target = target.parent
                    if target == section.parent:
                        break

                    found = False
                    for i, child in enumerate(section.parent._children, 0):
                        print("check", i)
                        if child == section:
                            print("pop", i, len(section.parent._children))
                            found = section.parent._children.pop(i)
                            break
                    if not found:
                        raise ValueError("can't find child in parent")

                    section.level = target.level + 1

                    # Anagrams is always the last section, otherwise References is the last
                    if target._children[-1].title == "Anagrams":
                        target._children.insert(-1, section)
                    else:
                        target._children.append(section)

                    break

    return changed


def move_misplaced_translations(entry):

    changes = []
    target = None
    found = False
    for section in entry.ifilter_sections():
        #print("scanning", section.level, section.title)
        if section.title in ALL_POS:
            #print("target is", section.title)
            target = section

        elif section.title == "Translations" and section.parent.title not in ALL_POS:
            print(" misplaced, flagging")
            if not target:
                print("Translation found before POS, can't move", entry.title)
                continue
            changes.append((target, section))

    for target, section in changes:

        index = section.parent._children.index(section)
        item = section.parent._children.pop(index)

        # Translations shouldn't have any children, promote them to siblings before moving the translation
        while item._children:
            newparent = item.parent
            child = item._children.pop()
            print("moving child to", newparent.title, newparent.level, item.level)
            child.parent = newparent
            child.level = newparent.level + 1 # TODO: also re-level grandchildren
            newparent._children.insert(index, child)

        print("Moving to", target.title, target.level)
        item.parent = target
        item.level = target.level + 1
        target._children.append(item)

    return bool(changes)
