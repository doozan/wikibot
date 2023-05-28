import re

# leading * indicates that the match must be case-sensitive
_countable_labels = {
    "chapter": [
        "chapters",
        "chapter",
        "ch.",
        "ch",  # had space
        "cap.",
        "kapital",
        "kapitel",
        ],
    "page": [
        "page",
        "pg.",
        "pg",
        "*p,",  # had space
        "*p.",
        "*p",  # had space
        "pages",
        "pp.",
        "*pp",  # had space
        ],
    "volume": [
        "volume",
        "vol.",
        "vol",
        "volumes",
        "vols",
        "vols.",
        "*v.",
        "*v",  # had space
        ],
    "number": [
        "number",
        "num",
        "num.",
        "no.",
        "no ",  # had space
        "*n.",
        "*n ",  # had space
        "№",
        ],
    "issue": [ "issue", "issues", "iss.", ],
    "series": [ "series", "*s.", "*s ", ],
    "episode": [ "episode", "ep.", "*ep", ],
    "season": ["season"],
    "act": [ "act" ],
    "scene": [ "scene" ],
    "stanza": [ "stanza" ],
    "verse": [ "verse", "verses" ],
    "line": [ "line", "lines" ],
    "appendix": [ "appendix" ],
    "section": [ "section", "sections" ],
    "book": [ "book", "books", "bk." ],
    "part": [ "part", "parts", "pt." ],
    "booklet": [ "booklet" ],
    "letter": [ "letter", "letters" ],
    "lecture": [ "lecture", "lectures" ],
    "column": [ "column", "lectures" ],
    "devotion": [ "devotion" ],
    "meditation": [ "meditation" ],
    "ballad": [ "ballad" ],
    "band": [ "band" ],
    "canción": [ "canción" ],
    "canto": [ "canto" ],
    "song": [ "song" ],
    "sonnet": [ "sonnet" ],
    "sermon": [ "sermon" ],
    "discourse": [ "discourse", "diſcourse", "diſcourſe" ],
    "essay": [ "essay" ],
    "epigraf": [ "epigraf" ],
    "epigram": [ "epigram", "epig ", "epig." ],

    # Manually include the long s variations because
    # re.match("discourse", "Diſcourse", re.IGNORECASE) == True
    # but "Diſcourse".lower() == 'diſcourse'
}
label_to_countable_type = {label.lstrip("*"):countable for countable, labels in _countable_labels.items() for label in labels}

_case_countable_labels = [label.lstrip("*") for labels in _countable_labels.values() for label in labels if label.startswith("*")]
_nocase_countable_labels = [label for labels in _countable_labels.values() for label in labels if not label.startswith("*")]
# Order longest to shortest to match longer strings before possible substrings
_case_countable_labels.sort(key=lambda x: (len(x)*-1, x))
_nocase_countable_labels.sort(key=lambda x: (len(x)*-1, x))

_nocase_pattern =  "|".join(map(re.escape, _nocase_countable_labels))
_case_pattern = "|".join(map(re.escape, _case_countable_labels))
_countable_label_pattern = fr"((?i:{_nocase_pattern})|({_case_pattern}))"


          #\s*(?P<separator>\b(or|and|to)\b|[\-&–]|{{ndash}})\s*

countable_pattern = fr"""(?x)
    \b
    (?P<label>{_countable_label_pattern})
    (?P<label_sep>[ #]*)
    (
        # match arabic and roman numerals
        (?P<num1>(
            [a-zA-Z]?\d+(,\d\d\d)*[a-zA-Z]?
            |[ivxlcdm]+
            |[IVXLCDM]+
        ))
        (
          (?P<num_sep>\s*(\b(or|and|to)\b|[\-&–])\s*)
          [#]?                                         # number sign
          (?P<num2>(
            [a-zA-Z]?\d+(,\d\d\d)*[a-zA-Z]?
            |[ivxlcdm]+
            |[IVXLCDM]+
          ))
        )?
        |
        # Or, match spelled numbers
        (?i:(?P<spelled>   # case-insensitive
           \b
           (?P<teen>eleven|twelve|((thir|four|fif|six|seven|eigh|nine)(teen)))?
           (?P<tens>ten|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety)?
           [- ]*
           (?P<digit>one|two|three|four|five|six|seven|eight|nine)?
        ))
    )
    \b
"""


ignorable_affixes = {"the", "of", "and"}
common_prefixes = set()
common_postfixes = { "inc", "incorporated", "llc", "ltd", "limited", "intl", "inter", "international", "gmbh",
    "co", "company", "corp", "corporation", "media", "group", "institute" }

publisher_prefixes = { "university", "univ.", "department", "editorial", "institute", "office", "press",
        "american", "international", "national", "us", "united states", "royal" }
publisher_postfixes = { "press", "print", "publisher", "publishers", "publishing", "et al",
        "brothers", "bros", "son", "sons", "associates", "associate" }

journal_affixes = {
        "bulletin", "journal", "review", "proceedings", "report", "reports", "illustrated", "chronicle", "herald",
        "quarterly", "daily", "monthly", "weekly", "sunday"
        }
journal_prefixes = {
        "american", "international", "national", "us", "united states", "royal"
        } | journal_affixes
journal_postfixes = {
        "magazine", "monitor", "news", "digest", "gazette", "post", "times", "media",
        } | journal_affixes


# Named parts of a text
text_locations = {
    'preface', 'prologue', 'postscript', 'foreword', 'forward', 'chapter', 'index', 'postscript', 'headline',
    "introduction", "footnote", "entry", "conclusion", "appendix", "epilogue", "glossary", "conclusion", "caption",
    "caption on an image", "contents", "dialogue", "figure caption", "first column", "column", "glossary",
    "glosario", "picture caption", "title", "editor's forward", "editors forward", "editorial", "book subtitle",
    "subtitle", "book title", "page title", "chapter title", "closing paragraph", "cover", "cover page",
    "main title", "margin note"
} | { k.strip() for k in label_to_countable_type.keys() }


# caption on an image
#
text_types = {
    "letter", "speech", "song", "poem", "editorial"
#A General Postscript
#dedicatory epistle
#dedicatory letter
#Epistle Dedicatory
#Introductory
#Introductory Essay
#Introductory Exposition
#Letter to the reader
#Translator’s Note
#pdf dissertation
}

countables = {
        # ode
        # unit
        #objection
        # aphorism
#phase
#sermon
# sonnet
#Conversation
#Canto X
#Class X
#Devotion 8
#Dialogue 21
#Aphorism 15
#Quest. VIII
#Reflection 7
}

number_words = {
    "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
    'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen', 'sixteen', 'seventeen', 'eighteen', 'nineteen',
    "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety", "hundred",

    "first", "second", "third", "fourth", "fifth", "sixth", "seveth", "eighth", "ninth", "tenth",
    "eleventh", "twelfth", "thirteenth", "fourteenth", "fifteenth", "sixteenth", "seventeenth", "eighteenth", "nineteenth",
    "twentieth", "thirtieth", "fortieth", "fiftieth", "sixtieth", "seventieth", "eightieth", "ninetieth", "hundredth",
    }

# Words that can't appear in locations or names
disallowed_words_common = {
    'academy', 'association', 'clinic', 'clinics', 'hospital', 'library', 'school', 'society',

    'archaeological', 'art', 'health', 'medicine', 'science', 'sciences',
    'australian', 'christian', 'greek', 'jewish',
    'author',
    'digital', 'diverse',
    'museumregister', 'net',
    'search',

    'edition', 'guide', 'guides', 'diary', 'publication', 'publications',
    'part', 'issue', 'transcript', 'translation', 'script',

    "day", "week", "month", "year",
    "spring", "summer", "fall", "winter", "autumn",

    "and", "in", "of", "by", "to", "et", "for", "on", "a", "the",
    }

disallowed_publisher_words = { 'edition' } | text_locations
disallowed_publisher_words -= { 'book', 'books' }
disallowed_journal_words = { "ad" } | text_locations | text_types
disallowed_location_words = {
    "junior", "senior", "sr", "dr", "mr", "college", "university"
    } | disallowed_words_common | text_locations

# Valid names, unless listed in _allowed_names above can never contain these words
disallowed_name_words = {
    'uk', 'united', 'world', 'new',
    } | number_words | disallowed_words_common | text_locations | common_prefixes | common_postfixes \
      | publisher_prefixes | publisher_postfixes | journal_prefixes | journal_postfixes
disallowed_name_words -= { "ed", "a", "art", "christian", "p", "pp", "p.", "v.", "v", "n.", "n", "pp", "ch", "s.", "s", "e", "e.", "pt." }

allowed_short_name_words = ["ed", "jr", "md", "jd", "ii", "iv", "vi", "ms", "sr", "mr", "dr", "st"] + \
        ["ad", "de", "da", "al", "ae", "aj", "al", "le", "ah", "ya", "ab", "do", "la", "mo", "lo", "wu", "jo", "di", "du", "le", "bo"]
#            [ "phd", "msw", "iii", "mrs" ] +
#            [ "one", "two" ] + \
#            [ "doe", "ed", "eli", "jan", "san", "rob", "odd", "van", "paz"]

allowed_lowercase_names = ["a", "y", "i", "de", "von", "van", "den", "del", "vom", "vander", "bin", "der", "ten", "las", "la", "ter", "le", "du"]
allowed_lowercase_prefix = ["d'", "d’", "al-", "de", "da", "l’"]
