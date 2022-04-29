#import locale

# this reads the environment and inits the right locale
#locale.setlocale(locale.LC_ALL, "")

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

def get_language_key(title):

    if title == "Translingual":
        return " A" + title

    elif title == "English":
        return " B" + title

    return title
    #return locale.strxfrm(title)

def sort_languages(parsed):
    sorted_sections = sorted(parsed._children, key=lambda x: get_language_key(x.title))
    if sorted_sections == parsed._children:
        return False

    parsed._children = sorted_sections
    return True

def sort_pos(parsed):

    for section in parsed._children:

        # Anything with a section number is sortable, otherwise just sort the top sections
        # TODO: instead of checking x.count, check if title is in COUNTABLE_SECTIONS (in fix_section_headers)
        sortable = list(section.ifilter_sections(lambda x: x.count))
        if not sortable:
            sortable = [ section ]

        for sort_section in sortable:
            # Special case sorting for "Alternative forms" or "Alternative scripts"
            # per WT:ETE, "Alternative forms" must be the first item IFF it appears before a POS item
            # Otherwise, it can be sorted below the POS according to the normal sort order
            alt_first = False
            for i,c in enumerate(sort_section._children):
                if c.title in ["Alterative forms", "Alternative scripts"]:
                    alt_first = True
                    break
                elif c.title in ALL_POS:
                    break

            sort_section._children = sorted(sort_section._children, key=lambda x: get_l3_sort_key(x.title, alt_first=alt_first))



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
top_sort = [
        #"Alternative forms",
        "Description",
        "Glyph origin",
        "Etymology",
        "Pronunciation",
        "Production",
    ]

#NONSTANDARD_OTHER = {
#    "Transliteration",
#    "Compounds",
#    "Readings",
#    "Cuneiform sign",
#}


# Sections that will be at the very bottom, ranked as they appear here
bottom_sort = [
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
    ]

sort_prefix = {k:" "+chr(64+i) for i,k in enumerate(top_sort)}
sort_prefix.update({k:"~"+chr(64+i) for i,k in enumerate(bottom_sort)})

sort_prefix_alt_first = dict(sort_prefix)
sort_prefix_alt_first["Alternative forms"] = " 0"
sort_prefix_alt_first["Alternative scripts"] = " 0"

def get_l3_sort_key(title, alt_first=False):

    if alt_first:
        return sort_prefix_alt_first.get(title)

    if title in sort_prefix:
        return sort_prefix.get(title) + title

    if title not in ALL_POS:
        self.error("Unexpected section:", title)

    return title
