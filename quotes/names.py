import re

# leading * indicates that the match must be case-sensitive
# countable things that map to distinct template parameters
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
    "issue": [ "issue", "issues", "iss.", ],
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
    "line": [ "line", "lines" ],
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
    "column": [ "column", "col" ],
}
countable_labels = _countable_labels.keys()


# labels that don't map to template parameters
# and must be combined into generic "section" parameter
_section_labels = {
    "series",
    "s.",
    "s",
    "episode",
    "ep.",
    "ep",
    "season",
    "act",
    "scene",
    "stanza",
    "verse",
    "verses",
    "appendix",
    "section",
    "book",
    "books",
    "bk",
    "lib",
    "part",
    "parts",
    "pt",
    "booklet",
    "letter",
    "letters",
    "lecture",
    "lectures",
    "devotion",
    "meditation",
    "ballad",
    "band",
    "canción",
    "canto",
    "song",
    "sonnet",
    "sermon",
    "discourse",
    "essay",
    "epigraf",
    "epigram",
    "epig",
    "caption",
    "image",
    "letter",
    "speech",
    "song",
    "poem",
    "editorial",
    "general postscript",
    "dedicatory",
    "epistle",
    "introductory",
    "introduction",
    "exposition",
    "letter",
    "reader",
    "article",
    "art",
    "ode",
    "unit",
    "objection",
    "aphorism",
    "phrase",
    "sermon",
    "sonnet",
    "conversation",
    "canto",
    "class",
    "cancion",
    "class",
    "devotion",
    "aphorism",
    "quest",
    "reflection",
    "note",
    "f",
    "paper",
    "night",

    "author's",
    "translator's",
    "editor's",
    "publisher's",

    "authors",
    "translators",
    "editors",
    "publishers",

    'preface','prologue', 'postscript', 'foreword', 'forward', 'index', 'postscript', 'headline',
    "footnote", "entry", "conclusion", "appendix", "epilogue", "glossary",
    "contents", "dialogue", "figure", "diagram", "illustration", "picture", "glossary",
    "glosario", "title", "editorial", "subtitle",
    "closing", "opening", "paragraph", "cover",
    "main", "margin", "abstract",

    "link",

    # books of the bible
    "acts", "actus", "adiae", "adias", "aggaei", "aggaeus", "amos", "apocalypse", "apocalypsis",
    "baruch", "canticle of canticles", "canticum canticorum", "chronicles", "clementine vulgate",
    "colossenses", "colossians", "corinthians", "corinthios", "daniel", "danielis", "deuteronomium",
    "deuteronomy", "douay rheims", "ecclesiastes", "ecclesiasticus", "ephesians", "ephesios",
    "esdrae", "esdras", "esther", "exodus", "ezechiel", "ezechielis", "ezekiel", "ezra", "galatas",
    "galatians", "genesis", "habacuc", "habakkuk", "haggai", "hebraeos", "hebrews", "hosea", "ioannem",
    "ioannis", "isaiae", "isaiah", "isaias", "jacobi", "james", "jeremiae", "jeremiah", "jeremias",
    "jeremy", "job", "joel", "john", "jonae", "jonah", "jonas", "joshua", "josue", "judae", "jude",
    "judges", "judices", "judith", "kings", "lamentationes", "lamentations", "leviticus", "lucam",
    "luke", "maccabees", "machabaeorum", "machabees", "malachi", "malachiae", "malachias", "marcum",
    "mark", "matthaeum", "matthew", "micah", "michaeae", "michaeas", "nahum", "nehemiae", "nehemiah",
    "numbers", "numeri", "obadiah", "osee", "paralipomenon", "peter", "petri", "philemon", "philemonem",
    "philippenses", "philippians", "proverbia", "proverbs", "psalmi", "psalms", "regum", "revelation",
    "romanos", "romans", "ruth", "samuel", "samuelis", "sapientiae", "sentences", "song of solomon",
    "sophoniae", "sophonias", "thessalonians", "thessalonicenses", "timotheum", "timothy", "titum",
    "titus", "tobiae", "tobias", "tobit", "wisdom", "zachariae", "zacharias", "zechariah", "zephaniah",
    "psalm", "letany"


} | {l.lstrip("*").strip() for labels in _countable_labels.values() for l in labels}
section_labels_pattern = "(" + "|".join(map(re.escape, sorted(_section_labels, key=lambda x: x+"🂲"))) + ")"

# Named parts of a text
label_to_countable_type = {label.lstrip("*"):countable for countable, labels in _countable_labels.items() for label in labels}
text_locations = _section_labels | { k.strip() for k in label_to_countable_type.keys() }


_case_countable_labels = [label.lstrip("*") for labels in _countable_labels.values() for label in labels if label.startswith("*")]
_nocase_countable_labels = [label for labels in _countable_labels.values() for label in labels if not label.startswith("*")]
# Order longest to shortest to match longer strings before possible substrings
_case_countable_labels.sort(key=lambda x: (len(x)*-1, x))
_nocase_countable_labels.sort(key=lambda x: (len(x)*-1, x))

_nocase_pattern =  "|".join(map(re.escape, _nocase_countable_labels))
_case_pattern = "|".join(map(re.escape, _case_countable_labels))
_countable_label_pattern = fr"((?i:{_nocase_pattern})|({_case_pattern}))"


          #\s*(?P<separator>\b(or|and|to)\b|[\-&–]|{{ndash}})\s*

number_pattern = r"([a-zA-Z]?\d+(,\d\d\d)*[a-zA-Z]?|[ivxlcdm]+|[IVXLCDM]+)"
spelled_number_pattern = \
   "(" \
   r"\b" \
   "(?P<teen>eleven|twelve|((thir|four|fif|six|seven|eigh|nine)(teen)))?" \
   "(?P<tens>ten|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety)?" \
   "[- ]*" \
   "(?P<digit>one|two|three|four|five|six|seven|eight|nine)?" \
   ")"

countable_pattern = fr"""(?x)
    \b
    (?P<label>{_countable_label_pattern})
    (?P<label_sep>[ #]*)
    (
        # match arabic and roman numerals
        (?P<num1>{number_pattern})
        (
          (?P<num_sep>\s*(\b(or|and|to)\b|[\-&–])\s*)
          [#]?                                         # number sign
          (?P<num2>{number_pattern})
        )?
        |
        # Or, match spelled numbers
        (?i:(?P<spelled>{spelled_number_pattern}))   # case-insensitive
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


number_words = {
    "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
    'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen', 'sixteen', 'seventeen', 'eighteen', 'nineteen',
    "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety", "hundred",

    "first", "second", "third", "fourth", "fifth", "sixth", "seveth", "eighth", "ninth", "tenth",
    "eleventh", "twelfth", "thirteenth", "fourteenth", "fifteenth", "sixteenth", "seventeenth", "eighteenth", "nineteenth",
    "twentieth", "thirtieth", "fortieth", "fiftieth", "sixtieth", "seventieth", "eightieth", "ninetieth", "hundredth",
    }
number_words_pattern = "(" + "|".join(number_words) + ")"

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

# bible books that are also commonly names
biblical_names = {"amos", "daniel", "ezra", "isaiah", "james", "jeremiah", "joshua", "jeremy", "joel", "john", "jonah", "jonas", "jude", "luke", "mark", "matthew", "micah", "peter", "samuel","timothy", "tobias"}

disallowed_publisher_words = { 'edition' } | text_locations
disallowed_publisher_words -= { 'book', 'books', 'art' }
disallowed_publisher_words -= biblical_names
disallowed_journal_words = { "ad" } | text_locations
disallowed_journal_words -= biblical_names
disallowed_journal_words -= { 'book', 'books', 'art' }
disallowed_location_words = {
    "junior", "senior", "sr", "dr", "mr", "college", "university"
    } | disallowed_words_common | text_locations

# Valid names, unless listed in _allowed_names above can never contain these words
disallowed_name_words = {
    'uk', 'united', 'world', 'new',
    } | number_words | disallowed_words_common | text_locations | common_prefixes | common_postfixes \
      | publisher_prefixes | publisher_postfixes | journal_prefixes | journal_postfixes
disallowed_name_words -= { "ed", "a", "art", "christian", "p", "pp", "p.", "v.", "v", "n.", "n", "pp", "ch", "s.", "s", "e", "e.", "pt." } | biblical_names

allowed_short_name_words = ["ed", "jr", "md", "jd", "ii", "iv", "vi", "ms", "sr", "mr", "dr", "st"] + \
        ["ad", "de", "da", "al", "ae", "aj", "al", "le", "ah", "ya", "ab", "do", "la", "mo", "lo", "wu", "jo", "di", "du", "le", "bo"]
#            [ "phd", "msw", "iii", "mrs" ] +
#            [ "one", "two" ] + \
#            [ "doe", "ed", "eli", "jan", "san", "rob", "odd", "van", "paz"]

allowed_lowercase_names = ["a", "y", "i", "de", "von", "van", "den", "del", "vom", "vander", "bin", "der", "ten", "las", "la", "ter", "le", "du"]
allowed_lowercase_prefix = ["d'", "d’", "al-", "de", "da", "l’"]
