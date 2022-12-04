from autodooz.sectionparser import SectionParser
from autodooz.sort_sections import ALL_POS, ALL_L3_SECTIONS, ALL_LANGS, COUNTABLE_SECTIONS, sort_languages, sort_pos_children
from collections import defaultdict

DEBUG=False
def dprint(*args):
    if DEBUG:
        print(*args)

CHILDLESS_SECTIONS = [

    "Inflection",
    "Declension",
    "Conjugation",
    "Mutation",
    "Quotations",

    "Usage notes",

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
]

ETY_CHILDREN = ALL_POS.keys() | {"Pronunciation"}

ALWAYS_ADOPTABLE_POS_CHILDREN = {
    "Definitions",
    "Inflection",
    "Declension",
    "Conjugation",
    "Translations",
}

ADOPTABLE_POS_CHILDREN = {
    "Definitions",

    "Usage notes",
    "Reconstruction notes",
    "Inflection",
    "Declension",
    "Conjugation",
    #"Mutation",
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
#    "Statistics", # Not in WT:ELE, but used in 20k pages
#    "Trivia",
    #"See also",
#    "References",
#    "Further reading",
#        "Anagrams",
    }


def promote_embedded_peers(countable, lang, summary, page_title):

    sections = lang.filter_sections(recursive=False, matches=lambda x: x.title == countable)

    new_peers = False
    for section in sections:
        # Countable sections may not have descendents of the same type
        peers = section.filter_sections(matches=lambda x: x.title == countable)

        target_idx = lang._children.index(section) + 1
        for peer in peers:
            print("promoting embedded peer")
            reparent(peer, lang, target_idx)
            new_peers = True


def cleanup_countable(countable_title, parent, summary, page_title):

    sections = parent.filter_sections(recursive=False, matches=lambda x: x.title == countable_title)

    if len(sections) == 1:
        cleanup_single_countable(sections[0], summary, page_title)
    elif len(sections) > 1:
        cleanup_multi_countable(sections, summary, page_title)

#    promote_embedded_peers(countable, lang, summary, page_title)


def cleanup_single_countable(section, summary, page_title):

    # Unnumbered countables should have no counter
    if section.count:
        summary.append(f"/*{section.path}*/ removed counter")
        print(page_title, summary[-1])
        section.count = None

    # pronunciation sections are allowed to have nested Usage notes
    if section.title == "Pronunciation" and any(x.title == "Usage notes" for x in section._children):
        return

    # Unnumbered countables should have no children
    promote_children(section, summary, page_title)

def promote_children(section, summary, page_title):
    if not section._children:
        return

    summary.append(f"/*{section.path}*/ promoted all child sections to siblings")
    print(page_title, summary[-1])

    new_parent = section.parent
    index = section.parent._children.index(section)
    while section._children:
        child = section._children.pop()
        new_parent._children.insert(index+1, child)
        child.parent = new_parent
        child.adjust_level(new_parent.level + 1)

def cleanup_multi_countable(sections, summary, page_title):
    for count, section in enumerate(sections, 1):
        count = str(count)
        if section.count != count:
            old_path = section.path
            section.count = count
            summary.append(f"/*{old_path}*/ renamed to {section.title} {section.count}")
            print(page_title, summary[-1])

def move_single_pronunciation(lang, summary, page_title):

    etys = lang.filter_sections(recursive=False, matches=lambda x: x.title == "Etymology")
    if not len(etys) > 1:
        return

    # If multiple etymologies,
    # and only one Pronunciation section,
    # and the Pronunciation section is between the first and second Etymologies
    # move the Pronunciation before the Etys
    ps = lang.filter_sections(matches=lambda x: x.title == "Pronunciation")
    if len(ps) == 1:
        section = ps[0]
        if section.level == 3:
            section_idx = lang._children.index(section)
            first_ety = etys[0]
            first_ety_idx = lang._children.index(first_ety)

            second_ety = etys[1]
            second_ety_idx = lang._children.index(second_ety)

            if second_ety_idx > section_idx > first_ety_idx:

                if all(s.title != "Usage notes" for s in section._children):
                    promote_children(section, summary, page_title)
                elif any(s.title != "Usage notes" for s in section._children):
                    print(f"/*{section.path}*/ has Usage notes plus other child sections, ignoring")
                    # Don't move Pronunciation sections with both Usage notes and other children
                    # TODO: manually review these, or just promote everything that's not "Usage notes"
                    return

                reparent(section, lang, first_ety_idx)
                summary.append(f"/*{lang.path}*/ moved single Pronuncation before multiple Etymologies")
                print(page_title, summary[-1])


def cleanup_nested_countable(lang, summary, page_title):

    # Handle nested countables, ex:
    #  ==Etymology 1==
    #  ===Pronunciation 1===
    #  ===Pronunciation 2===
    #  ==Etymology 2==
    #  ===Pronunciation===

    for countable_title in COUNTABLE_SECTIONS:
        for section in lang.filter_sections(recursive=False, matches=lambda x: x.title == countable_title):
            for nested_title in COUNTABLE_SECTIONS:
                if countable_title == nested_title:
                    continue
                cleanup_countable(nested_title, section, summary, page_title)

def has_non_l2_language_section(entry, page_title, summary):
    res = False
    for section in entry.filter_sections(matches=lambda x: x.title in ALL_LANGS):
        if section.level != 2:
            # TODO: Log this
            print(page_title, "non_l2_language", section.path)
            res = True

    return res

def promote_languages_to_l2(entry, page_title, summary):
    # Manual review only, not safe for automation

    changed = False
    for section in entry.filter_sections(matches=lambda x: x.title in ALL_LANGS):
        if section.level != 2: # and section._children:
            summary.append(f"/*{section.path}*/ moved non-l2 language to L2")
            print(page_title, summary[-1])
            reparent(section, entry)
            changed = True

    if changed:
        summary += sort_languages(entry)

def promote_children_of_childless_sections(entry, page_title, summary):
    # Promote children of childless sections
    for section in entry.filter_sections(matches=lambda x: x.title in CHILDLESS_SECTIONS):
        if not all(s.title in ALL_L3_SECTIONS for s in section.filter_sections(recursive=False)):
            # TODO: log this to page for manual review
            print("unhandled child section")
        else:
            promote_children(section, summary, page_title)

def has_only_expected_children(parent, allowed_children, page_title, summary):
    # Returns True if all child sections are known L3 sections
    valid = True
    for section in parent.filter_sections(recursive=False):
        if section.title not in allowed_children:
            # TODO: log this
            print(page_title, "unknown section", section.path)
            valid = False
    return valid

def fix_anagrams(entry, page_title, summary):
    for section in entry.filter_sections(matches=lambda x: x.title == "Anagrams"):
        if section.level > 3:
            new_parent = section.parent
            while new_parent.level > 2:
                new_parent = new_parent.parent

            promote_children(section, summary, page_title)
            summary.append(f"/*{section.path}*/ moved to {new_parent.path}")
            print(summary[-1])
            reparent(section, new_parent)

def process(page_text, page_title, summary=[], custom_args=None):


#    if "==English==" not in page_text:
#        return page_text

    entry = SectionParser(page_text, page_title)
    if entry.state != 0:
        print(page_title, "unfinished state", entry.state)
        return page_text

    if not has_only_expected_children(entry, ALL_LANGS, page_title, summary):
        return page_text

    if has_non_l2_language_section(entry, page_title, summary):
        return page_text

    fix_anagrams(entry, page_title, summary)

#    langs = []
#    langs = entry.filter_sections(recursive=False)
    langs = entry.filter_sections(recursive=False, matches=lambda x: x.title not in \
            ["Chinese", "Japanese", "English", "Spanish", "Mandarin", "Cebuano"])
    if not langs:
        return page_text

    for lang in langs:

        if not has_only_expected_children(lang, ALL_L3_SECTIONS, page_title, summary):
            continue

        dprint("Scanning", lang.path)

        promote_children_of_childless_sections(lang, page_title, summary)

        move_single_pronunciation(lang, summary, page_title)

        all_countable_titles = []
        for countable in lang.filter_sections(recursive=False, matches=lambda x: x.title in COUNTABLE_SECTIONS):
            if countable.title not in all_countable_titles:
                all_countable_titles.append(countable.title)

        for countable_title in all_countable_titles:

            cleanup_countable(countable_title, lang, summary, page_title)
            countable_adopt_stray_children(lang, countable_title, summary, page_title)

            all_countable = lang.filter_sections(recursive=False, matches=lambda x: x.title == countable_title)
            if not all_countable:
                continue

            # Fail if there is an empty countable
            if len(all_countable) > 1 and any(not s._children for s in all_countable):
                # TODO: Log this
                print(page_title, f"/*{lang.path}*/ has empty {countable.title} section, failing")
                # Childless multi-sections are bad
                summary = []
                return page_text

            if len(all_countable) < 2:
                continue

            if not has_only_expected_children(lang, ALL_L3_SECTIONS, page_title, summary):
                continue

            for parent in all_countable:
                pos_adopt_stray_children(parent, summary, page_title)

        pos_adopt_stray_children(lang, summary, page_title)
        cleanup_nested_countable(lang, summary, page_title)

    if not summary:
        return page_text

    # Sort languages
    summary += sort_languages(entry)

    # Sort POS entries if the POS is a direct child of language or countable section (avoids sorting sections buried underneath something unexpected)
    all_pos = entry.filter_sections(matches=lambda x: x.title in ALL_POS and (x.parent.title in COUNTABLE_SECTIONS or x.parent.title in ALL_LANGS))
    for section in all_pos:
        summary += sort_pos_children(section)

    # If there were changes, run another pass to ensure promoted items have counters
    if not custom_args or "second_loop" not in custom_args:
        return process(str(entry), page_title, summary, custom_args={"second_loop": True})

    return str(entry)


def pos_adopt_stray_children(grandparent, summary, page_title):

    all_parents = grandparent.filter_sections(recursive=False, matches=lambda x: x.title in ALL_POS)
    if not all_parents:
        dprint("no POS parents found under", grandparent.path)
        return
    dprint("scanning", len(all_parents), "in", grandparent.path)
    last_multi_parent = all_parents[-1] if len(all_parents) > 1 else None

    stray_children = find_stray_children(grandparent, ALL_POS, ADOPTABLE_POS_CHILDREN, summary, page_title)

    if not stray_children:
        return

    for new_parent, children in stray_children.items():

        # The final parent in a multi-parent group should inherit all sections in ALWAYS_ADOPTABLE_POS_CHILDREN
        # plus any sections that already exist in an earlier sibling
        if new_parent == last_multi_parent:
            all_cousins = set(cousin.title for uncle in all_parents[:-1] for cousin in uncle._children)
            new_children = []
            for child in children:
                if child in ALWAYS_ADOPTABLE_POS_CHILDREN or child.title in all_cousins:
                    new_children.append(child)
                else:
                    break
            children = new_children
            if not children:
                break

        adoptions = [child.path for child in children]
        summary.append(f"/*{new_parent.path}*/ adopted {', '.join(adoptions)}")
        print(page_title, summary[-1])

        for child in children:
            old_path = child.path
            reparent(child, new_parent)

        summary += sort_pos_children(new_parent)


def countable_adopt_stray_children(grandparent, countable_title, summary, page_title):

    # Single countables shouldn't have child sections
    all_parents = grandparent.filter_sections(recursive=False, matches=lambda x: x.title == countable_title)
    if len(all_parents) < 2:
        return

    stray_children = find_stray_children(grandparent, [countable_title], ETY_CHILDREN, summary, page_title)

#    print("found", len(stray_children), countable_title, "with stray children in", grandparent.title)

    if not stray_children:
        return

    for new_parent, children in stray_children.items():

        adoptions = [child.path for child in children]
        summary.append(f"/*{new_parent.path}*/ adopted {', '.join(adoptions)}")
        print(page_title, summary[-1])

        for child in children:
            old_path = child.path
            reparent(child, new_parent)

def find_stray_children(grandparent, parents, grandchildren, summary, page_title):

    # Given a grandparent section, scans all children
    # When it encounters a child listed in [parents], that node will
    # adopt all following sections if they are in [grandchildren] until it encounters
    # a section listed in [parents]

#    print(f"scanning {grandparent.path} to find children that should be grandchildren")

    multi_parent = False
    prev_parent = None
    stray_children = defaultdict(list)
    unhandled_between_parents = False

    for section in grandparent.filter_sections(recursive=False):
#        print("checking", section.path, section.title, parents)
        if section.title in parents:
#            print("parent", section.title, section.count)
            if prev_parent:
                multi_parent = True
                if unhandled_sections:
                    print(page_title, f"unhandled section {unhandled_sections} between {prev_parent.path} and {section.path}")
                    unhandled_between_parents = True
            prev_parent = section
            unhandled_sections = False
        elif prev_parent:
            if section.title in grandchildren:
#                print("found stray child", section.path)
#                if section.count:
#                    print(page_title, "ignoring section with counter")
#                    return
                if unhandled_sections:
                    # TODO: Log this
                    print(page_title, f"unhandled section {unhandled_sections} between {prev_parent.path} and {section.path}")
                    return

                stray_children[prev_parent].append(section)
            else:
#                print("unhandled", section.title)
                unhandled_sections = section.path
#        else:
#            print("skipping section before first parent", section.title)

    if unhandled_between_parents:
        # TODO: Log this
        print("unhandled between parents")
        return

    return stray_children

def reparent(child, new_parent, index=None):
    child.parent._children.remove(child)
    if index is None:
        new_parent._children.append(child)
    else:
        new_parent._children.insert(index, child)

    child.parent = new_parent
    child.adjust_level(new_parent.level + 1)


def add_children_to_pos(lang):

        multi_pos = False
        prev_pos = None
        misplaced_children = defaultdict(list)
        interspersed_non_children = True

        for section in lang._children:
            if section.title in ALL_POS:
                if prev_pos:
                    multi_pos = True
                prev_pos = section
            elif prev_pos and section.title in CHILD_SECTIONS:
                misplaced_children[prev_pos].append(section)


        # TODO: misplaced_children[prev_pos] may contain sections that shouldn't be children, but instead apply to all previous POS entries,
        # for example, Usage Notes
        # For each possible section like this, check if there exists a corresponding cousin node in an earlier POS. If not, don't convert it to child

        if multi_pos and misplaced_children:
            for new_parent, children in misplaced_children.items():
                if new_parent == prev_pos:
                    break
                for child in children:
                    old_parent = child.parent
                    old_path = child.path
                    child.parent = new_parent
                    new_parent._children.append(child)
                    child.level = new_parent.level + 1
                    new_path = child.path
                    index = old_parent._children.index(child)
                    del old_parent._children[index]
                    summary.append(f"/*{old_path}*/ moved to {new_path}")
                    print(page_title, summary[-1])
                    #log(page_title, old_path, new_path)

        return str(entry)
