from enwiktionary_parser.languages.all_ids import ALL_LANG_IDS, ALL_LANGS, ALT_LANGS

# Sections that must be numbered when they appear more than once at the same level
#
# These sections may stack or nest within each other, eg:
# ===Etymology===
# ===Pronunciation 1===
# ===Pronunciation 2===
#
# ===Pronunciation 1===
# ===Etymology 1===
# ===Etymology 2===
#
# or
# ===Pronunciation 1===
# ====Etymology 1====
# ====Etymology 2====
# ===Pronunciation 2===
#
COUNTABLE_SECTIONS = [
    "Etymology",
    "Pronunciation",
    #"Glyph origin",
    #"Glyph"
]

# All Parts of Speech defined by WT:ELE
WT_POS = {
    "Adjective": "adj",
    "Adverb": "adv",
    "Ambiposition": "ambip",
    "Article": "art",
    "Circumposition": "circump",
    "Classifier": "classifier",
    "Clitic": "clitic",
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

    "Romanization": "rom",
    "Logogram": "logo",
    "Determinative": "dtv",
}

# Not in WT:POS, but allowed
EXTRA_POS = {
    "Adjectival noun": "adj",
    "Adnominal": "adnominal",
    "Affix": "affix",
    "Enclitic": "enclitic",
    "Medial": "medial",
    "Idiom": "idiom",
    "Ordinal number": "onum",
    "Preverb": "preverb",
    "Prenoun": "prenoun",
    "Transliteration": "translit",
    "Verbal noun": "verbalnoun",

    "Final": "final",
    "Stem": "stem",
    "Initial": "initial",
}

ALL_POS = WT_POS | EXTRA_POS

# All sections defined by WT:ELE
WT_ELE = {
    "Description",
    "Glyph origin",
    "Etymology",
    "Pronunciation",
    "Production",

    "Usage notes",
    "Reconstruction notes",
    "Inflection",
    "Declension",
    "Conjugation",
    "Mutation",
    "Quotations",
    "Alternative forms",
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
    "Related terms",
    "Collocations",
    "Descendants",
    "Translations",
    "Trivia",
    "See also",
    "References",
    "Further reading",
    "Anagrams",
}

EXTRA_L3 = {
    "Alternative scripts",
    "Cuneiform sign", # Not in WT:ELE
    "Statistics", # Not in WT:ELE, but used in 20k pages

    "Definitions", # Used in Chinese and Japanese entries

    # Han characters and language-specific varieties
    "Han character",
    "Hanzi",
    "Kanji",
    "Hanja",

    "Mutation", # Should always be L3
    "Compounds",

    "Sign values", # Not in WT:ELE, used in Akkadian
}

ALL_L3 = set(COUNTABLE_SECTIONS) | ALL_POS.keys() | WT_ELE | EXTRA_L3

# Sections that can appear inside a Part of Speech section,
# order enforced by WT:ELE
ALL_POS_CHILDREN = [
    "Readings",
    "Definitions",

    "Usage notes",
    "Reconstruction notes",
    "Inflection",
    "Declension",
    "Conjugation",
    #"Mutation", # Defined in WT:ELE, but should always be L3
    "Quotations",
    "Alternative forms",
    "Alternative reconstructions",
    "Abbreviations", # not in WT:ELE

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
    "Compounds", # not in WT:ELE
    "Related terms",
    "Related characters", # not in WT:ELE
    "Collocations",
    "Descendants",
    "Translations",
    "Statistics", # not in WT:ELE
    "Trivia",
    "See also",
    "References",
    "Further reading",
]
