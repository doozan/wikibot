import enwiktionary_sectionparser as sectionparser

from autodooz.sections import ALL_POS, ALL_L3, ALL_LANGS, COUNTABLE_SECTIONS
from collections import defaultdict

# L3 Sections that should never contain a child section with a title in ALL_L3
# Allowed to have children with unknown titles like "Other conjugations" or "More references"
CHILDLESS_SECTIONS = [

    "Alternative forms",

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

ALWAYS_ADOPTABLE_COUNTABLE_CHILDREN = ALL_POS.keys() | {
    "Pronunciation",
    "Alternative forms",
    "Alternative scripts",
    "Alternative reconstructions",
    } # | set(COUNTABLE_SECTIONS)
ADOPTABLE_COUNTABLE_CHILDREN = ALWAYS_ADOPTABLE_COUNTABLE_CHILDREN | {
    "See also",
    "References",
    "Further reading",
}

ALWAYS_ADOPTABLE_POS_CHILDREN = {
    "Definitions",
    "Inflection",
    "Declension",
    "Conjugation",
    "Translations",
}

# Sections that will be adopted only when there is no ambiguity:
# when there is only 1 POS section or when the given potential child
# section also appears as a child section of an earlier sibling
ADOPTABLE_POS_CHILDREN = ALWAYS_ADOPTABLE_POS_CHILDREN | {
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
    "Statistics", # Not in WT:ELE, but used in 20k pages
#    "Trivia",
    #"See also",
#    "References",
#    "Further reading",
    }


class SectionLevelFixer():

    def promote_embedded_peers(countable, lang, summary, page_title):

        sections = lang.filter_sections(recursive=False, matches=countable)

        new_peers = False
        for section in sections:
            # Countable sections may not have descendents of the same type
            peers = section.filter_sections(matches=countable)

            target_idx = lang._children.index(section) + 1
            for peer in peers:
                print("promoting embedded peer")
                peer.reparent(lang, target_idx)
                new_peers = True

    def cleanup_counter(self, sections):
        # Unnumbered countables should have no counter
        if len(sections) == 1:
            section = sections[0]
            if section.count:
                self.fix("autofix_unneeded_counter", section, "removed counter")
                section.count = None

        elif len(sections) > 1:

            # Verify that all section counters are simple integers (avoid breaking stuff like Etymology 1.2)
            for section in sections:
                if section.count and not section.count.isdigit():
                    self.warn("complex_counter", section.path)
                    return

            for count, section in enumerate(sections, 1):
                count = str(count)
                if section.count != count:
                    self.fix("autofix_wrong_counter", section, f"renamed to {section.title} {count}")
                    section.count = count

    def fix_numbering(self, entry):
        for l2 in entry.filter_sections(recursive=False):

            for countable_title in COUNTABLE_SECTIONS:
                sections = l2.filter_sections(recursive=False, matches=countable_title)

                if not sections:
                    continue

                self.cleanup_counter(sections)

                # Check for nested countable
                for section in sections:
                    for countable_title in COUNTABLE_SECTIONS:
                        if countable_title == section.title:
                            continue
                        child_sections = section.filter_sections(recursive=False, matches=countable_title)
                        if child_sections:
                            self.cleanup_counter(child_sections)

    def cleanup_countable(self, countable_title, parent):

        sections = parent.filter_sections(recursive=False, matches=countable_title)

        # Single countable sections should have no children
        if len(sections) == 1:
            section = sections[0]

            # Exception: Pronunciation sections are allowed to have nested Usage notes
            if section.title == "Pronunciation" and section.filter_sections(matches="Usage notes"):
                return

            self.promote_children(section)

    def promote_children(self, section):
        if not section._children:
            return

        self.fix("autofix_unwanted_children", section, "promoted all child sections to siblings")

        new_parent = section.parent
        index = section.parent._children.index(section)
        while section._children:
            child = section._children.pop()
            new_parent._children.insert(index+1, child)
            child.parent = new_parent
            child.adjust_level(new_parent.level + 1)

    def promote_child_in_place(self, old_parent, child):
        new_parent = old_parent.parent

        # Adopt all following sections as children of the child section
        idx = old_parent._children.index(child)
        child._children += old_parent._children[idx+1:]
        old_parent._children = old_parent._children[:idx+1]

        idx = new_parent._children.index(old_parent) + 1
        child.reparent(new_parent, idx)


    def move_single_pronunciation(self, lang):
        ps = lang.filter_sections(matches="Pronunciation")

        etys = lang.filter_sections(recursive=False, matches="Etymology")
        if not len(etys) > 1:
            return

        # If multiple etymologies,
        # and only one Pronunciation section,
        # and the Pronunciation section is between the first and second Etymologies
        # move the Pronunciation before the Etys
        ps = lang.filter_sections(matches="Pronunciation")
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
                        self.promote_children(section)
                    elif any(s.title != "Usage notes" for s in section._children):
                        # Don't move Pronunciation sections with both Usage notes and other children
                        # TODO: manually review these, or just promote everything that's not "Usage notes"
                        self.warn("embedded_pronunciation_has_children", f"{section.path} has Usage notes plus other child sections, ignoring")
                        return

                    section.reparent(lang, first_ety_idx)
                    self.fix("autofix_misplaced_pronunciation", lang, "moved single Pronuncation before multiple Etymologies")


    def cleanup_nested_countable(self, lang):

        # Handle nested countables, ex:
        #  ==Etymology 1==
        #  ===Pronunciation 1===
        #  ===Pronunciation 2===
        #  ==Etymology 2==
        #  ===Pronunciation===

        for countable_title in COUNTABLE_SECTIONS:
            for section in lang.filter_sections(recursive=False, matches=countable_title):
                for nested_title in COUNTABLE_SECTIONS:
                    if countable_title == nested_title:
                        continue
                    self.cleanup_countable(nested_title, section)

    def has_non_l2_language_section(self, entry):
        res = False
        for section in entry.filter_sections(matches=lambda x: x.title in ALL_LANGS):
            if section.level != 2:
                self.warn("non_l2_language", section.path)
                res = True

        return res

    def promote_languages_to_l2(self, entry):
        # Manual review only, not safe for automation

        changed = False
        for section in entry.filter_sections(matches=lambda x: x.title in ALL_LANGS):
            if section.level != 2: # and section._children:
                self.fix("autofix_misplaced_language", section, "moved non-l2 language to L2")
                section.reparent(entry)
                changed = True

    def promote_children_of_childless_sections(self, entry):
        # Promote children of childless sections
        for section in entry.filter_sections(matches=lambda x: x.title in CHILDLESS_SECTIONS):
            if self.has_only_expected_children(section, ALL_L3):
                self.promote_children(section)

    def fix_unexpected_lineage(self, entry):
        reparent = []

        for section in entry.ifilter_sections():
            ancestors = list(section.ancestors)
            if len(ancestors) <= 2:
                continue
            lineage = ancestors[1:-1] # drop the page name and the section name

            # POS sections should never be children of other POS sections
            if section.title in ALL_POS and section.parent.title in ALL_POS:
                reparent.append((section.parent, section))

            # Sections should never be descendents of themselves
            elif any(x.title == section.title for x in lineage):
                self.warn("circular_child", section.path)

            # Childless sections should have no children
            elif any(x.title in CHILDLESS_SECTIONS for x in lineage):
                self.warn("child_of_childless", section.path)

            # POS sections should only ever be found within L2 or L3 sections
            elif section.title in ALL_POS:
                if not all(x.title in ALL_LANGS or (x.title in COUNTABLE_SECTIONS and x.count) for x in lineage):
                    self.warn("pos_bad_lineage", section.path)

            # countables should only ever be found within L2 sections
            elif section.title in COUNTABLE_SECTIONS:
                if not all(x.title in ALL_LANGS or (x.title in COUNTABLE_SECTIONS and x.count) for x in lineage):
                    self.warn("countable_bad_lineage", section.path)

        for section, child in reversed(reparent):
            self.fix("autofix_pos_inside_pos", child, f"promoted in place")
            self.promote_child_in_place(section, child)


    def has_only_expected_children(self, parent, allowed_children):
        # Returns True if all child sections are known L3 sections
        valid = True
        for section in parent.filter_sections(recursive=False):
            if section.title not in allowed_children:
                self.warn("unexpected_child", section.path)
                valid = False
        return valid

    def fix_anagrams(self, entry):
        anagrams = entry.filter_sections(matches="Anagrams")
        for section in anagrams:
            if section.level > 3:
                new_parent = section.parent
                while new_parent.level > 2:
                    new_parent = new_parent.parent
            elif section.parent._children.index(section) < len(section.parent._children)-len(anagrams):
                new_parent = section.parent
            else:
                continue

            self.promote_children(section)
            self.fix("autofix_misplaced_anagrams", section, f"moved to end of {new_parent.path}")
            section.reparent(new_parent)


    def pos_adopt_stray_children(self, grandparent):
        all_parents = grandparent.filter_sections(recursive=False, matches=lambda x: x.title in ALL_POS)
        stray_children = self.find_stray_children(grandparent, ALL_POS, ADOPTABLE_POS_CHILDREN)
        self.adopt_stray_children(all_parents, stray_children, ADOPTABLE_POS_CHILDREN, ALWAYS_ADOPTABLE_POS_CHILDREN)

    def countable_adopt_stray_children(self, grandparent, countable_title):
        # Single countables shouldn't have child sections
        all_parents = grandparent.filter_sections(recursive=False, matches=countable_title)
        if len(all_parents) < 2:
            return
        stray_children = self.find_stray_children(grandparent, [countable_title], ADOPTABLE_COUNTABLE_CHILDREN)
        self.adopt_stray_children(all_parents, stray_children, ADOPTABLE_COUNTABLE_CHILDREN, ALWAYS_ADOPTABLE_COUNTABLE_CHILDREN)

    def find_stray_children(self, grandparent, parents, all_grandchildren):

        # Given a grandparent section, scans all children
        # When it encounters a child listed in [parents], that node will
        # adopt all following sections if they are in [all_grandchildren] until it encounters
        # a section listed in [parents]

        prev_parent = None
        stray_children = defaultdict(list)
        unhandled = []

        for section in grandparent.filter_sections(recursive=False):
            if section.title in parents:
                prev_parent = section

            elif prev_parent:
                if section.title in all_grandchildren:
                    stray_children[prev_parent].append(section)
                else:
                    unhandled.append((prev_parent, section))

        # Ignore any unhandled sections after the last parent
        unhandled = [x for x in unhandled if x[0] != prev_parent]
        if unhandled:
            for parent, section in unhandled:
                language = list(section.ancestors)[-2].title
                self.warn("unexpected_mixed_section", (language, section.title, parent.path))
            return

        return stray_children

    def adopt_stray_children(self, all_parents, stray_children, all_adoptable, always_adoptable):
        if not all_parents:
            return
        last_multi_parent = all_parents[-1] if len(all_parents) > 1 else None

        if not stray_children:
            return

        for new_parent, children in stray_children.items():

            # The final parent in a multi-parent group should inherit all sections in [always_adoptable]
            # plus any sections in [all_adoptable] that already exist in an earlier sibling
            # unless it already has a similarly named section
            if new_parent == last_multi_parent:
                all_cousins = set(cousin.title for uncle in all_parents[:-1] for cousin in uncle._children)
                existing_children = set(child.title for child in new_parent._children)
                new_children = []
                for child in children:
                    if child.title in always_adoptable:
                        new_children.append(child)
                    elif child.title in existing_children:
                        self.warn("adoptable_duplicate", f"{new_parent.path} already contains {child.title}")
                        break
                    elif child.title in all_adoptable and child.title in all_cousins:
                        new_children.append(child)
                    else:
                        break
                children = new_children
                if not children:
                    break

            adoptions = [child.path for child in children]
            self.fix("autofix_stray_child", new_parent, f"adopted {', '.join(adoptions)}")

            for child in children:
                old_path = child.path
                child.reparent(new_parent)


    def move_misplaced_translations(self, entry):
        changes = []
        target = None
        found = False
        for section in entry.ifilter_sections():
            if section.title in ALL_POS:
                target = section

            elif section.title == "Translations" and section.parent.title not in ALL_POS:
                if not target:
                    self.warn("translation_before_pos", f"{section.path} found before first POS")
                    continue
                changes.append((target, section))

        for new_parent, section in changes:
            # Translations shouldn't have any children, promote them to siblings before moving the translation
            self.promote_children(section)

            self.fix("autofix_misplaced_translation", section, f"moved to {new_parent.path}")
            section.reparent(new_parent)


    def fix(self, reason, section, details):
        if self._summary is not None:
            self._summary.append(details)

        self._log.append((reason, self.page_title, section.path, details))

    def warn(self, reason, details):
        self._log.append((reason, self.page_title, None, details))

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

        entry = sectionparser.parse(page_text, page_title)
        if not entry:
            return page_text if summary is not None else self._log

        if not self.has_only_expected_children(entry, ALL_LANGS):
            return page_text if summary is not None else self._log

        if self.has_non_l2_language_section(entry):
            return page_text if summary is not None else self._log

        for lang in entry.filter_sections(recursive=False):

            if not self.has_only_expected_children(lang, ALL_L3):
                continue

            self.promote_children_of_childless_sections(lang)

            self.move_single_pronunciation(lang)

            all_countable_titles = []
            for countable in lang.filter_sections(recursive=False, matches=lambda x: x.title in COUNTABLE_SECTIONS):
                if countable.title not in all_countable_titles:
                    all_countable_titles.append(countable.title)

            for countable_title in all_countable_titles:

                self.cleanup_countable(countable_title, lang)
                self.countable_adopt_stray_children(lang, countable_title)

                all_countable = lang.filter_sections(recursive=False, matches=countable_title)
                if not all_countable:
                    continue

                # Fail if there is an empty countable
                if len(all_countable) > 1:
                    for s in all_countable:
                        if not s._children:
                            if not s.content_text:
                                self.warn("empty_countable", f"{s.path}")
                            else:
                                if "{{zh-see" in s.content_text or "{{ja-see" in s.content_text:
                                    self.warn("childless_countable", f"{s.path}")
                            return page_text if summary is not None else self._log

                elif len(all_countable) < 2:
                    continue

                if not self.has_only_expected_children(lang, ALL_L3):
                    continue

                for parent in all_countable:
                    self.pos_adopt_stray_children(parent)

            self.pos_adopt_stray_children(lang)
            self.cleanup_nested_countable(lang)

        self.fix_numbering(entry)

        self.fix_anagrams(entry)
        self.move_misplaced_translations(entry)

        self.fix_unexpected_lineage(entry)

        return str(entry) if summary is not None else self._log
