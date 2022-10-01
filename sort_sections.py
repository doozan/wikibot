#import locale
import re

# this reads the environment and inits the right locale
#locale.setlocale(locale.LC_ALL, "")

COUNTABLE_SECTIONS = {
    "Etymology",
    "Pronunciation",
    "Glyph origin",
    "Glyph"
}

WT_POS = {
    # Parts of speech
    "Adjective": "adj",
    "Adverb": "adv",
    "Ambiposition": "ambip",
    "Article": "art",
    "Circumposition": "circump",
    "Classifier": "classifier",
    "Conjunction": "conj",
    "Contraction": "concentration",
    "Counter": "counter",
    "Determiner": "determiner",
    "Ideophone": "ideophone",
    "Interjection": "interj",
    "Noun": "n",
    "Numeral": "num",
    "Participle": "v",
    "Particle": "particle",
    "Postposition": "postp",
    "Preposition": "prep",
    "Pronoun": "pron",
    "Proper noun": "prop",
    "Verb": "v",

    # Morphemes
    "Circumfix": "circumfix",
    "Combining form": "affix",
    "Infix": "infix",
    "Interfix": "interfix",
    "Prefix": "prefix",
    "Root": "root",
    "Suffix": "suffix",

    # Symbols and characters
    "Diacritical mark": "diacrit",
    "Letter": "letter",
    "Ligature": "ligature",
    "Number": "num",
    "Punctuation mark": "punct",
    "Syllable": "syllable",
    "Symbol": "symbol",

    # Phrases
    "Phrase": "phrase",
    "Proverb": "proverb",
    "Prepositional phrase": "prep",

    # Han characters and language-specific varieties
    "Han character": "han",
    "Hanzi": "hanzi",
    "Kanji": "hanji",
    "Hanja": "hanja",

    "Romanization": "rom",
    "Logogram": "logo",
    "Determinative": "dtv",
}

ALL_POS = WT_POS | {
    # Not in WT:POS, but allowed
    "Transliteration": "translit",
    "Preverb": "preverb",
    "Affix": "affix",
    "Ordinal number": "onum",
    "Adjectival noun": "adj",
    "Idiom": "idiom",
    "Abbreviations": "abbrev",
}

import unicodedata
def strip_accents(s):
   return ''.join(c for c in unicodedata.normalize('NFD', s)
                  if unicodedata.category(c) != 'Mn')

def get_language_key(title):

    if title == "Translingual":
        return (0, title)

    elif title == "English":
        return (1, title)

    return (2, strip_accents(title))

def sort_languages(parsed):

    if not parsed._children or parsed._children[0].level != 2:
        return False

    sorted_sections = sorted(parsed._children, key=lambda x: get_language_key(x.title))
    if sorted_sections == parsed._children:
        return False

    parsed._children = sorted_sections
    return True

def sort_pos(language):

    # Anything with a section number is sortable, otherwise just sort the top sections
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

        if not all(x.title in top_sort or x.title in bottom_sort or x.title in ALL_POS for x in sort_section._children):
            break

        sort_section._children.sort(key=lambda x: get_l3_sort_key(x, alt_first=alt_first))



WT_ELE = {
        "Description",
        "Glyph origin",
        "Etymology",
        "Pronunciation",
        "Production",

        "Definitions",

        "Usage notes",
        "Reconstruction notes",
        "Inflection",
        "Declension",
        "Conjugation",
        "Mutation",
        "Quotations",
        "Alternative forms",
        #"Alternative scripts",
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
        #"Derived characters", # not in WT:ELE
        "Related terms",
        #"Related characters", # not in WT:ELE
        "Descendants",
        "Translations",
        #"Statistics", # Not in WT:ELE, but used in 20k pages
        "Trivia",
        "See also",
        "References",
        "Further reading",
        "Anagrams",
}

# Sections that will be a the very top, ranked as they appear here
top_sort = {k:v for v,k in enumerate([
        #"Alternative forms",
        "Description",
        "Glyph origin",
        "Etymology",
        "Pronunciation",
        "Production",
    ])}

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
        "Descendants",
        "Translations",
        "Statistics", # Not in WT:ELE, but used in 20k pages
        "Trivia",
        "See also",
        "References",
        "Further reading",
        "Anagrams",
    ])}

ALL_L3_SECTIONS = COUNTABLE_SECTIONS | WT_ELE | ALL_POS.keys() | top_sort.keys() | bottom_sort.keys()

L3_SORT_LANGUAGES = ["Spanish"]

def is_form(section):
    return bool(re.search(r"{{head\s*\|[^}]* form", str(section))) or "{{es-past participle}}" in str(section)

def get_l3_sort_key(item, alt_first=False):

    if alt_first and item.title in ["Alternative forms", "Alternative scripts"]:
        return (0, -1, item.title)

    if item.title in top_sort:
        sort_group = 0
        sort_class = 0
        sort_item = str(top_sort[item.title])
    elif item.title in ALL_POS:
        sort_group = 1
        sort_class = is_form(item.title)
        sort_item = item.title
    elif item.title in bottom_sort:
        sort_group = 2
        sort_class = 0
        sort_item = bottom_sort[item.title]
    else:
        raise ValueError("Unhandled section:", item.path)
        #error("Unexpected section:", item.title)

    return (sort_group, sort_class, sort_item)
