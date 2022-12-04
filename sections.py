from enwiktionary_parser.languages.all_ids import languages as ALL_LANG_IDS
ALL_LANGS = {v:k for k,v in ALL_LANG_IDS.items()}

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
    # Temporarily disabled to avoid fixing pages with Kanji sections
    #"Han character": "han",
    #"Hanzi": "hanzi",
    #"Kanji": "hanji",
    #"Hanja": "hanja",

    "Romanization": "rom",
    "Logogram": "logo",
    "Determinative": "dtv",
}

# Not in WT:POS, but allowed
EXTRA_POS = {
    "Transliteration": "translit",
    "Preverb": "preverb",
    "Affix": "affix",
    "Ordinal number": "onum",
    "Adjectival noun": "adj",
    "Idiom": "idiom",
    "Abbreviations": "abbrev",
}

ALL_POS = WT_POS | EXTRA_POS

# Sections that can appear inside a Part of Speech section,
# order enforced by WT:ELE
ALL_POS_CHILDREN = [
    "Definitions",

    "Usage notes",
    "Reconstruction notes",
    "Inflection",
    "Declension",
    "Conjugation",
    # Temporarily disabled to avoid fixing pages with Mutation sections
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
    "Statistics", # Not in WT:ELE, but used in 20k pages
    "Trivia",
    "See also",
    "References",
    "Further reading",
]


# All sections defined by WT:ELE
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
    "Collocations",
    "Descendants",
    "Translations",
    #"Statistics", # Not in WT:ELE, but used in 20k pages
    "Trivia",
    "See also",
    "References",
    "Further reading",
    "Anagrams",
}

ALL_L3 = set(COUNTABLE_SECTIONS) | ALL_POS.keys() | WT_ELE