#!/usr/bin/python3

import re
from collections import defaultdict
from Levenshtein import distance as fuzzy_distance

from autodooz.sectionparser import SectionParser, Section
from autodooz.sections import ALL_LANGS, ALL_L3, ALL_POS, ALL_POS_CHILDREN, COUNTABLE_SECTIONS
from autodooz.lang_data import ALT_LANGS

# Tags that generate a <ref> link
ref_tags = ["<ref[ :>]", r'{{ja-pron\|[^}]*(acc_ref|accent_ref)'] #}} code folding fix
PATTERN_REF_TAGS = "(?i)(" + "|".join(ref_tags) + ")"

# Tags that generate <references/>
PATTERN_REFS = r"(?i)(<\s*references|{{reflist)"

ety_templates = [
    "back-form",
    "compound", "com",
    "compoundsee",
    "affix", "af",
    "prefix", "pre",
    #"prefixsee",
    "suffix", "suf",
    #"suffixsee",
    "confix",
    "circumfix",
    "transfix",
    "infix",
    "inh",
    #"infixsee",
    #"interfixsee",
    "blend",
    "univerbation",
]
PATTERN_ETY_TEMPLATES = r"{{(" + "|".join(ety_templates) + r")\s*[|}]"

def get_fuzzy_matches(title, words, max_distance):
    #print(title, words, max_distance)
    #for x in words:
    #    print(title, x, fuzzy_distance(title, x))
    return [x for x in words if title != x and fuzzy_distance(title, x)<=max_distance]

import unicodedata
def strip_accents(s):
   return ''.join(c for c in unicodedata.normalize('NFD', s)
                  if unicodedata.category(c) != 'Mn')
L3_FUZZY_MATCHES = {
    "Adjectival noun": 3,
    "Adjective": 2,
    "Adnominal": 2,
    "Adverb": 1,
    "Affix": 0,
    "Alternative forms": 2,
    "Alternative reconstructions": 3,
    "Alternative scripts": 2,
    "Ambiposition": 1,
    "Anagrams": 2,
    "Antonyms": 1,
    "Article": 0,
    "Circumfix": 2,
    "Circumposition": 2,
    "Classifier": 3,
    "Clitic": 0,
    "Collocations": 2,
    "Combining form": 3,
    "Compounds": 2,
    "Conjugation": 0,
    "Conjunction": 0,
    "Contraction": 1,
    "Coordinate terms": 3,
    "Counter": 2,
    "Cuneiform sign": 3,
    "Declension": 1,
    "Definitions": 2,
    "Derived terms": 1,
    "Descendants": 3,
    "Description": 2,
    "Determinative": 1,
    "Determiner": 1,
    "Diacritical mark": 3,
    "Enclitic": 0,
    "Etymology": 2,
    "Final": 1,
    "Further reading": 3,
    "Glyph origin": 3,
    "Han character": 3,
    "Hanja": 0,
    "Hanzi": 0,
    "Holonyms": 0,
    "Hypernyms": 0,
    "Hyponyms": 0,
    "Ideophone": 2,
    "Idiom": 1,
    "Infix": 0,
    "Inflection": 1,
    "Initial": 2,
    "Interfix": 2,
    "Interjection": 1,
    "Kanji": 1,
    "Letter": 1,
    "Ligature": 2,
    "Logogram": 2,
    "Medial": 1,
    "Meronyms": 1,
    "Mutation": 1,
    "Noun": 1,
    "Number": 1,
    "Numeral": 1,
    "Ordinal number": 3,
    "Participle": 1,
    "Particle": 0,
    "Phrase": 1,
    "Postposition": 1,
    "Prefix": 1,
    "Preposition": 1,
    "Prepositional phrase": 3,
    "Production": 1,
    "Pronunciation": 2,
    "Proper noun": 2,
    "Punctuation mark": 3,
    "Quotations": 1,
    "Reconstruction notes": 3,
    "References": 3,
    "Related terms": 1,
    "Romanization": 2,
    "Root": 1,
    "See also": 2,
    "Sign values": 3,
    "Statistics": 3,
    "Stem": 1,
    "Suffix": 1,
    "Syllable": 2,
    "Symbol": 1,
    "Synonyms": 1,
    "Translations": 2,
    "Transliteration": 2,
    "Trivia": 1,
    "Troponyms": 1,
    "Usage notes": 3,
    "Verb": 1,
    "Verbal noun": 2
}


L2_FIXES = {
    'allowed': ALL_LANGS,
    #'allowed_no_accents': {strip_accents(x) for x in ALL_LANGS},
    # No fuzzy matches for language, too sloppy
    #'fuzzy_matches': L2_FUZZY_MATCHES,

    'replacements': {
        'Arabic': 'Arabic', # unicode char on the A
        'Assyrian neo-aramiac': 'Assyrian Neo-Aramaic',
        'Assyrian Neo-Aramic': 'Assyrian Neo-Aramaic',
        'Azerbaijan': 'Azerbaijani',
        'Guarani': 'Guaraní',
        'Hijaz Arabic': 'Hijazi Arabic',
        'Ingrain': 'Ingrian',
        'Iñupiaq': 'Inupiaq',
        'Iriga Bikolano': 'Iriga Bicolano',
        'Jjapanese': 'Japanese',
        'Kapampangn': 'Kapampangan',
        'Karachay Balkar': 'Karachay-Balkar',
        'Kashmir': 'Kashmiri',
        'Khorasani Turkic': 'Khorasani Turkish',
        'Māori': 'Maori',
        'Megrelian': 'Mingrelian',
        'Mezquital otomi': 'Mezquital Otomi',
        'Middle Mongolian': 'Middle Mongolian',
        'Norwegian (Bokmål)': 'Norwegian Bokmål',
        'Ogba': 'Ogbah',
        'Pahari-Pothwari': 'Pahari-Potwari',
        'Panjabi': 'Punjabi',
        'Prasun': 'Prasuni',
        'Queretaro Otomi': 'Querétaro Otomi',
        'Sanksrit': 'Sanskrit',
        'Serbo-croatian': 'Serbo-Croatian',
        'Shekhani': 'Sekani',
        'Siclian': 'Sicilian',
        'Slovenian': 'Slovincian',
        'Tai nue': 'Tai Nüa',
        'Tai-nüa': 'Tai Nüa',
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
        "Descendants": 3,
        "Hyponyms": 0,
        "Abbreviations": 2,
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
        if word not in fixes["allowed"]:
            raise ValueError(f"fuzzy match '{word}' is not in list of 'allowed' titles")
        for word2, max_typos2 in fixes.get("fuzzy_matches", {}).items():
            if word != word2:
                distance = fuzzy_distance(word, word2)
                if distance <= max_typos + max_typos2:
                    raise ValueError(f"{word} is not a candidate for typo matching, because it's too similar to {word2} {distance} ({max_typos}, {max_typos2})")

_validate(L2_FIXES)
_validate(L3_FIXES)
_validate(POS_CHILD_FIXES)

class SectionHeaderFixer():

    def __init__(self):
        # Only used when calling functions directly during unit testing
        # all other uses should just call process() which will set these variables
        self._changes = []
        self.page_title = "test"

    def get_fixed_title(self, section, fixes):

        allowed = fixes["allowed"]

        if section.title in allowed:
            return

        title = section.title

        cap_title = section.title.capitalize()
        if cap_title in allowed:
            self.fix("cap_change", section, f"renamed to {cap_title}")
            return cap_title

        if title.endswith("s") and title[:-1] in allowed:
            new_title = title[:-1]
            self.fix("not_plural", section, f"renamed to {new_title}")
            return new_title

        if title in fixes.get("replacements", []):
            new_title = fixes["replacements"][title]
            self.fix("defined_replacement", section, f"renamed to {new_title}")
            return new_title

        if title in ALT_LANGS:
            alt_titles = ALT_LANGS[title]
            if len(alt_titles) == 1:
                new_title = alt_titles[0]
                self.fix("alt_lang", section, f"renamed to {new_title}, per WT:LOL")
                return new_title
            else:
                self.warn("multi_alt_lang", f"{section.path} {alt_titles}")
                return

        fuzzy_matches = []
        for new_title, max_typos in fixes.get("fuzzy_matches",{}).items():
            fuzzy_matches += get_fuzzy_matches(title, [new_title], max_typos)

        if len(fuzzy_matches) > 1:
            raise ValueError("ERROR: ambiguous fuzzy matches", title, fuzzy_matches)

        elif len(fuzzy_matches) == 1:
            new_title = fuzzy_matches[0]
            self.fix("fuzzy_match", section, f"renamed to {new_title}")
            return new_title

    def fix_title(self, section, fixes):
        if "=" in section.title:
            return

        if section.title in fixes["allowed"]:
            return

        new_title = self.get_fixed_title(section, fixes)
        if new_title:
            section.title = new_title

        else:
            if section.level == 2:
                self.get_lang_guesses(section)
            self.warn("unfixable", section.path)


    def get_lang_guesses(self, section):
        title = section.title
        for limit in range(1,5):
            fuzzy_matches = []
            for new_title in ALL_LANGS:
                fuzzy_matches += get_fuzzy_matches(title, [new_title], limit)
            if fuzzy_matches:
                self.warn("l2_fuzzy_guess", f"{section.path} MAYBE (fuzzy match {limit}): {'; '.join(fuzzy_matches)}")
                if len(fuzzy_matches) > 1:
                    break

        for limit in range(1,5):
            fuzzy_matches = []
            new_matches = []
            for new_title in ALT_LANGS:
                new_matches += get_fuzzy_matches(title, [new_title], limit)
                for match in new_matches:
                    self.warn("l2_fuzzy_guess", f"{section.path} MAYBE (fuzzy match alt lang '{new_title}' {limit}): {'; '.join(ALT_LANGS[new_title])}")
                fuzzy_matches += new_matches
            if len(fuzzy_matches) > 1:
                break


    def fix_section_titles(self, entry):
        """
        Spell check section titles
        """

        changes = []

        for section in entry.ifilter_sections():

            if section.level < 2:
                continue

            if section.level == 2:
                self.fix_title(section, L2_FIXES)

            elif section.parent.title in COUNTABLE_SECTIONS or section.parent.title in ALL_LANGS:
                self.fix_title(section, L3_FIXES)

            elif section.parent.title in ALL_POS:
                self.fix_title(section, POS_CHILD_FIXES)

    #        else:
    #            self.fix_title(section, OTHER_FIXES)

        return changes


    def _adjust_level(self, level, sections):
        changed = False
        for section in sections:
            if section.level != level:
                changed = True
                section.level = level

            if section._children and self._adjust_level(level+1, section._children):
                changed = True
        return changed

    def fix_section_levels(self, entry):
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

        if self._adjust_level(2, entry._children):
            self.fix("fix_level", None, "child level should be parent level+1")


    def fix_bad_l2(self, entry):
        """ Find known non-language sections that are L2 and move them into the previous L2 entry """
        reparent = []
        prev = None
        for child in entry.filter_sections(recursive=False):
            if child.level != 2:
                return

            title = child.title.strip("=")

            if prev and title in ALL_L3:
                reparent.append((child, prev))
            prev = child

        for child, newparent in reparent:
            self.fix("bad_l2", child, f"moved errant L2 to {newparent.path}")
            child.reparent(newparent)

    def fix_remove_pos_counters(self, entry):
        """ Ensure POS entries do not have a numeric counter """

        for section in entry.ifilter_sections():
            if section.count and section.title in ALL_POS:
                self.fix("pos_counter", section, "removed counter")
                section.count = None

    def remove_empty_sections(self, entry):

        for section in reversed(entry.filter_sections()):
            if section.level == 2:
                continue

            if section.title in COUNTABLE_SECTIONS:
                continue

            if not section._lines and not section._children:
                self.fix("empty_section", section, "removed empty section")
                section.parent._children.remove(section)

    def add_missing_references(self, entry):

        for section in entry._children:
            if re.search(PATTERN_REF_TAGS, str(section)) and not re.search(PATTERN_REFS, str(section)):
                ref_section = next(section.ifilter_sections(matches="References"), None)
                if ref_section:
                    ref_section._lines.insert(0, "<references/>")
                    self.fix("missing_ref_target", ref_section, "added missing <references/>")
                    continue

                new_section = Section(entry, 3, "References")
                new_section.add("<references/>")

                # Anagrams is always the last section, otherwise References is the last
                if section._children and section._children[-1].title == "Anagrams":
                    section._children.insert(-1, new_section)
                else:
                    section._children.append(new_section)

                self.fix("missing_ref_section", section, "added References section")

    def rename_misnamed_etymology(self, entry):
        for section in entry.ifilter_sections(matches = lambda x: x.title == "Pronunciation"):
            if any(re.search(PATTERN_ETY_TEMPLATES, line) for line in section._lines):
                self.fix("misnamed_etymology", section, "renamed to Etymology (manually reviewed)")
                section.title = "Etymology"

    def rename_misnamed_pronunciation(self, entry):
        for section in entry.ifilter_sections(matches = lambda x: x.title == "Etymology"):
            print("scanning", section.path)
            if any("IPA" in line and "IPAchar" not in line and "IPAfont" not in line for line in section._lines):
                self.fix("misnamed_pronunciation", section, "renamed to Pronunciation (manually reviewed)")
                section.title = "Pronunciation"

    def rename_misnamed_further_reading(self, entry):
        for section in entry.ifilter_sections(matches = lambda x: x.title == "References"):
            if not any(re.match(PATTERN_REFS, line.strip(" #:*")) for line in section._lines):
                self.fix("misnamed_further_reading", section, "renamed to Further reading")
                section.title = "Further reading"

    def split_bulky_references(self, entry):
        """
        EXPERIMENTAL: Move everything except <references/> from the References section to Further reading
        Not safe to run generally """
        for section in entry.ifilter_sections(matches = lambda x: x.title == "References"):
            moved_idx = []
            for idx, line in enumerate(section._lines):
                if not re.match(PATTERN_REFS, line.strip(" #:*")):
                    moved_idx.append(idx)

            if not moved_idx:
                continue

            moved_lines = []
            for idx in reversed(moved_idx):
                moved_lines.insert(0, section._lines.pop(idx))

            existing_section = next(section.parent.ifilter_sections(matches = lambda x: x.title == "Further reading"), None)
            if existing_section:
                self.fix("moved_further_reading", section, "moved non-footnotes to Further reading")
                for line in moved_lines:
                    if line not in existing_section._lines:
                        existing_section._lines.append(line)

            else:
                self.fix("split_further_reading", section, "split non-footnotes to Further reading")
                new_section = Section(section.parent, section.level, "Further reading")
                new_section._lines = moved_lines
                section.parent._children.append(new_section)

    def rename_misnamed_references(self, entry):
        for section in entry.ifilter_sections(matches = lambda x: x.title == "Further reading"):
            if len(section._lines) == 1 \
                    and re.match(PATTERN_REFS, section._lines[0].strip(" #:*")) \
                    and "References" not in section.lineage:
                        self.fix("misnamed_references", section, "renamed to References")
                        section.title = "References"

    def rename_misnamed_quotations(self, entry):
        for section in entry.ifilter_sections(matches = lambda x: x.title == "Citations"):
            if len(section._lines) == 1 \
                    and re.match("{{seeCites.*?}}", section._lines[0].strip(" #:*")) \
                    and "Quotation" not in section.lineage:
                        self.fix("misnamed_quotations", section, "renamed to Quotations")
                        section.title = "Quotations"

    def fix(self, reason, section, details):
        if section:
            self._changes.append(f"/*{section.path}*/ {details}")
            self._log(reason, self.page_title, section.path, details)
        else:
            self._changes.append(details)
            self._log(reason, self.page_title, None, details)

    def warn(self, reason, details):
        self._log(reason, self.page_title, None, details)

    @staticmethod
    def _log(reason, page, section_path, details):
        print(page, reason, section_path, details)

    # called by wikifix to mass apply the above fixes
    def process(self, page_text, page_title, summary=None, custom_args=None):

        self.page_title = page_title
        self._changes = []

        if ":" in page_title or "/" in page_title:
            return page_text

        entry = SectionParser(page_text, page_title)

        self.fix_section_titles(entry)
        self.fix_remove_pos_counters(entry)
        self.fix_bad_l2(entry)
        self.rename_misnamed_references(entry)
        self.rename_misnamed_quotations(entry)
        self.add_missing_references(entry)

        # not safe to run unsupervised
        if custom_args and custom_args.get("remove_empty"):
            self.remove_empty_sections(entry)

        # not safe to run unsupervised
        if custom_args and custom_args.get("fix_misnamed_further_reading"):
            spanish = next(entry.ifilter_sections(matches="Spanish"), None)
            if spanish:
                self.rename_misnamed_further_reading(spanish)
                self.split_bulky_references(spanish)

        # not safe to run unsupervised
        if custom_args and custom_args.get("fix_misnamed_etymology"):
            self.rename_misnamed_etymology(entry)

        # not safe to run unsupervised
        if custom_args and custom_args.get("fix_misnamed_pronunciation"):
            self.rename_misnamed_pronunciation(entry)

        self.fix_section_levels(entry)

        if not self._changes:
            return page_text

        if summary is not None:
            summary += self._changes

        return str(entry)
