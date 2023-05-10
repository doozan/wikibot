import enwiktionary_sectionparser as sectionparser
from autodooz.sections import ALL_LANGS
import re
import sys
from enwiktionary_parser.utils import nest_aware_split, nest_aware_resplit
from .name_labeler import NameLabeler
from collections import defaultdict

class QuoteFixer():

    def dprint(self, *args, **kwargs):
        if self.debug:
            print(args, kwargs, file=sys.stderr)

    def __init__(self, debug=False):
        self._summary = None
        self._log = []
        self.debug=debug
        self.labeler = NameLabeler()

        bad=[]
        for pub in self._allowed_publishers:
            if self.get_leading_labeled_number(pub):
                bad.append(pub)
        if bad:
            print("BAD PUBLISHERS", bad)
            exit()

        self._init_fingerprints()



    def classify_names(self, text, init_command):
        return self.labeler.classify_names(text, init_command)

    def fix(self, code, section, details):
        if self._summary is not None:
            self._summary.append(f"/*{section.path}*/ {details}")

        page = list(section.lineage)[-1]
        self._log.append(("autofix_" + code, page))

    def warn(self, code, section, details=None):
        page = list(section.lineage)[-1]
        self._log.append((code, page, details))

    @staticmethod
    def strip_wrapper_templates(text, templates):
        old = ""
        while old != text:
            old = text
            # Strips simple wrappers, doesn't handle nested templates
            text = re.sub(r"{{\s*(" + "|".join(templates) + r")\s*\|([^|{{]*)}}", r"\2", text)

        return text

    def _strip_leading_separators(self, text):
        #return text.lstrip("/#:;-.–,— ")
        leading, stripped = self._split_leading_separators(text)
        return stripped

    #_separator_regex = re.escape(re.match(r"([/#:;-.–,—\s]*)(.*)", text)

    _separator_regex = r"([/#:;\-.–,— ]*)(.*)$"
    def _split_leading_separators(self, text):
        return re.match(self._separator_regex, text).groups()

    def get_leading_year(self, text):
        pattern = r"""(?x)
            (?P<years>
            (\s|'''|\(|\[)*           # ''' or ( or [
            (?P<year1>(1\d|20)\d{2})
            (
              (\s*(?P<separator>or|,|&|and|-|–|to|{{ndash}})+\s*)
              (?P<year2>(1\d|20)\d{2})
            )?
            (\s|'''|\)|\])*           # ''' or ) or ]
            )
            (?P<post>.*)$         # trailing text
        """
        m = re.match(pattern, text)
        if not m:
            return

        group = m.group('years').strip()
        post_text = m.group('post')

        # Don't match 1234 in 12345
        if group[-1].isnumeric and post_text and post_text[0].isnumeric():
            return

        # Validate that all of the opening and closing pairs match up
        old = ""
        while old != group:
            old = group
            if group.startswith("'''") and group.endswith("'''"):
                group = group[3:-3].strip()

            if group.startswith("(") and group.endswith(")"):
                group = group[1:-1].strip()

            if group.startswith("[") and group.endswith("]"):
                group = group[1:-1].strip()

        if not (group[0].isnumeric() and group[-1].isnumeric()):
            return


        # Strip {{CE}} after year
        post_text = self._strip_leading_separators(post_text)
        post_text = re.sub(r"^({{(CE|C\.E\.)[^}]*}}|CE:)\s*", "", post_text)

        year1 = m.group('year1')
        year2 = m.group('year2')
        separator = m.group('separator')

        return tuple(self.single_or_range(year1, year2, separator) + [post_text])


    def single_or_range(self, val1, val2, separator):

        if not separator:
            if val2:
                raise ValueError("val2 without separator")
            return [val1]

        if separator in ["or"]:
            separator = " or "
        elif separator in [","]:
            separator = ","
        elif separator in ["&", "and"]:
            separator = "&"
        elif separator in ["-", "–", "to", "{{ndash}}"]:
            separator = "-"
        else:
            raise ValueError("unhandled separator", [separator])

        return [val1, separator, val2]


    def get_leading_unhandled(self, text):

        # TODO: if starts with { or [, slurp until matching brace
        if text.startswith("{{"):
            end = text.find("}}")
            if end:
                return text[:end+2], text[end+2:]

        if text.startswith("]"):
            end = text.find("]")
            if end:
                return text[:end+1], text[end+1:]


        pattern = r"""(?x)
            (
              [\d\w]+          # alphanumeric
              |\s+
              |([^\d\w\s])\2*    # or, any non-alphanumeric+space character and any repetition
            )
            (?P<post>.*)$    # trailing text
        """
        m = re.match(pattern, text)
        if not m:
            return

        return m.group(1), m.group('post')


    def get_leading_newsgroup_author(self, text):

        if "{{monospace" in text and "Usenet" in text:
            text = self._strip_leading_separators(text)

            if text.startswith('"'):
                username, new_text = self.get_leading_start_stop('"', '"', text)

            else:
                m = re.match("^([^,'“]+)(.*)", text)
                if not m:
                    return
                username = m.group(1)
                new_text = m.group(2)

            username = re.sub(r"([,. ]*\(?username\)?)", "", username)
            new_text = re.sub(r"^([,. ]*\(?username\)?)", "", new_text)

            return username, new_text

            # Split link into title?
            #[http://groups.google.com/group/alt.mountain-bike/msg/88b9b6a7d4ef1e37?q=Daygo Re: Intro & Querry About Front Shocks]



    def get_leading_names_safe(self, text):
        return self.get_leading_names(text, only_labelled=True)

    def get_leading_names(self, text, only_labelled=False):

        # x TODO: make this get_leading_names and then push each identified nametype to the parsed stack
        # x do something similar with the get_leading_editors and get_leading_translators
        #
        # x maybe just make this get_leading_names and detect the ed. eds. and tr. trs. etc to adjust the default command?
        # x option to skip validation for names that are explicitly labeled?
        #
        # x validate each name while parsing and break when a non-valid name is encountered
        #
        # use this for "published by" and "(publisher)" too?
        #

        new_text = re.sub(r"^(ed\.|eds\.|edited by)\s*", "", text, flags=re.IGNORECASE)
        if new_text != text:
            return self._get_leading_classified_names(new_text, ">editor")

        new_text = re.sub(r"^(translation by|translated by|trans|tr\. by)\s+", "", text, flags=re.IGNORECASE)
        if new_text != text:
            return self._get_leading_classified_names(new_text, ">translator")

        new_text = re.sub(r"^by\s+", "", text)
        if not only_labelled:
            return self._get_leading_classified_names(new_text, "~author")

        # We're being very clever here by setting the default label to "_invalid"
        # this will label the first non-explicitly labelled name as "_invalid"
        # which will cause the VM to reject the name and everything after it
        return self._get_leading_classified_names(new_text, "~_invalid")


    def _get_leading_classified_names(self, text, init_command):

        # Names can't start with a quote mark
        if not text or text[0] in ['"', '"', '“', "‘"]:
            return

        if text[0] == "[" and not text.startswith("[["): # (text[:2] in "[[" or text[:3] in "[:s.startswith("[[") or text.startswith("[:") or text.startswith("[s:") or t
            return

        orig_text = text


        pattern = r"""(?x)
            (.*?)                    # Names
            (?P<post>
              (
                ((?<=[^A-Z])(\.[ ]))   # Break on . unless it's like J.D.
                |[ ]-                # break on " -" but not Smith-Jones
                |\b(in|as)\b         # likewise, break on "in" and "as" but not "Penguin"
                |\[http              # always break on links
                |''                  # and formatting
                |["“‘]               # And quotes
                |$
              ).*
            )
            """
        m = re.match(pattern, text)

        if not m:
            return

        if not m.group(1).strip():
            return

        name_text = self._strip_leading_separators(m.group(1)).replace("&#91;", "‘")

        for start, end in (("(", ")"), ("[", "]"), ("[[", "]]"), ("{{", "}}"), ("{", "}"), ("<", ">")):
            if name_text.count(start) != name_text.count(end):
                print("mismatched bracket count")
                return

        # Check if the remaining text starts with ''et al''
        #alt_m = re.match(r"\s*(''|[;, ]+)et al((ii|\.)''(.)?|[.,])\s*(?P<post>.*)$", m.group('post'))
        post_text = m.group('post') if m.group('post') else ""
        appended_text = ""
        if post_text:
            new_post_text = re.sub(r"^\s*(''|[\[;, ]+)et(\.)+ al((ii|ia|\.)''(\.)?|[\].,])\s*", "", post_text)
            if new_post_text != post_text:
                appended_text = ", et al."
                name_text = name_text + appended_text

        res = self.classify_names(name_text, init_command)
        if not res:
            return

        classified_names, invalid_text = res
        if not classified_names:
            return

        # Strip any appended text from the returned invalid text before concat with post_text
        if appended_text:
            print("ET AL", [invalid_text[:-len(appended_text)] + post_text])
            return classified_names, invalid_text[:-len(appended_text)] + post_text

        return classified_names, invalid_text + post_text

    def get_leading_start_stop(self, start, stop, text):
        if not text.startswith(start):
            return

        text = text[len(start):]

        nests = (("[[", "]]"), ("{{", "}}"), ("[http", "]")) #, (start, stop))
        part = next(nest_aware_split(stop, text, nests), None)
        if not part:
            return
        if part == text:
            return

        return part, text[len(part)+len(stop):]


    def get_leading_italics(self, text):
        # match exactly 2 or 5 single quotes
        q = "(?<!')(?:'{2}|'{5})(?!')"

        m = re.match(fr"({q}.+?{q})(.*)", text)
        if not m:
            return
        return m.group(1)[2:-2], m.group(2)

    def get_leading_bold(self, text):
        # match exactly 3 or 5 single quotes
        q = "(?<!')(?:'{3}|'{5})(?!')"

        m = re.match(fr"({q}.+?{q})(.*)", text)
        if not m:
            return
        return m.group(1)[3:-3], m.group(2)

    def get_leading_newsgroup(self, text):
        m = re.match(self._allowed_newsgroups_regex, text, re.IGNORECASE)
        if not m:
            return

        return m.group('usenet'), m.group('post')

    def get_leading_double_quotes(self, text):
        return self.get_leading_start_stop('"', '"', text)

    def get_leading_paren(self, text):
        return self.get_leading_start_stop('(', ')', text)

    def get_leading_brackets(self, text):
        # Don't process wikilinks
        if text.startswith("[[") or text.startswith("[http"):
            return
        return self.get_leading_start_stop(r'[', r']', text)

    def get_leading_fancy_double_quotes(self, text):
        res = self.get_leading_start_stop('“', '”', text)
        if res:
            return res
        return self.get_leading_start_stop('“', '”', text)

    def get_leading_fancy_quote(self, text):
        return self.get_leading_start_stop("‘", "’", text)

    @staticmethod
    def is_valid_title(title):

        if not title:
            return False

        if title.startswith("{{") and title.endswith("}}"):
            return True

        if title.startswith("[") and title.endswith("]"):
            return True

        # Must start with uppercase letter
        if title[0] not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            return

        return not re.search("([()]|thesis|published|submitted|printed)", title)

    @staticmethod
    def is_valid_publisher(text):

        if text.lower() in ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "sept", "oct", "nov", "dec",
                "january", "february", "march", "april", "june", "july", "august", "september", "october", "november", "december",
                "spring", "summer", "fall", "winter",
                "magazine", "appendix"]:
            return False

        if text.startswith("[") and text.endswith("]"):
            return True

        if text.startswith("{{w|") and text.endswith("}}"):
            return True

        bad_items = [r'''[:ə"“”()<>\[\]\d]''', "''",  r"\b(quoting|citing|page|by|published|reprint|edition|ed\.|p\.)\b", r"\d{4}"]
        pattern = "(" +  "|".join(bad_items) + ")"
        if re.search(pattern, text):
            return False
        return True

    def get_leading_regex(self, regex, text):
        #m = re.match(fr"^(?P<match>{regex})(?P<post>(\b|[ .,:;]).*)", text)
        m = re.match(fr"^(?P<match>{regex})(?P<post>.*)", text)
        if not m:
            return
        return m.group('match'), m.group('post')

    def get_leading_location(self, text):
        return self.get_leading_regex(self._locations_regex, text)

    def get_leading_journal(self, text):
        return self.get_leading_regex(self._journals_regex, text)

    def get_leading_publisher(self, text):
        text = re.sub(r"^(printed|published|publ\.|republished|in )(| by)?[-;:,.\s]*", "", text)
        res = self.get_leading_regex(self._allowed_publishers_regex, text)
        if not res:
            return
        return res

    def is_allowed_publisher(self, text):
        return text in self._allowed_publishers

    def get_leading_isbn(self, text):

        orig_text = text

        # Find ISBN templates
        pattern = r"""(?x)
            ({{ISBN\s*\|            # {{ISBN|
            |ISBN:)\s*              # or ISBN:
            \s*
            (?P<isbn>[0-9-X ]+)                     # numbers, -, and X
            \s*
            (}})?                    # }}
            (?P<post>.*)$            # trailing text
        """

        isbn = []
        while text:
            text = self._strip_leading_separators(text)
            m = re.match(pattern, text)
            if not m:
                break
            isbn.append(m.group('isbn').replace(" ", ""))
            text = m.group('post')

        # Find bare ISBN numbers
        pattern = r"""(?x)
            \b
            (?P<isbn>978(-)?[0-9]{10})              # ISBN
            \b
            (?P<post>.*)$            # trailing text
        """

        while text:
            text = self._strip_leading_separators(text)
            m = re.match(pattern, text)
            if not m:
                break
            isbn.append(m.group(1).replace(" ", ""))
            text = m.group('post')

        if not isbn:
            return

        print("ISBN", isbn, [orig_text, text])

        return isbn, text

    @staticmethod
    def get_leading_oclc(text):
        pattern = r"""(?x)
            \(?                             # option (
            {{OCLC\s*\|\s*                  # {{OCLC|
            (?P<oclc>[0-9-]+)               # numbers and dashes
            \s*}}                           # }}
            \)?                             # optional )
            (?P<post>.*)$            # trailing text
        """

        m = re.match(pattern, text)
        if not m:
            return

        return m.group('oclc'), m.group('post')

    @staticmethod
    def get_leading_issn(text):
        pattern = r"""(?x)
            \(?                             # option (
            {{ISSN\s*\|\s*                  # {{ISSN|
            (?P<issn>[0-9-]+)               # numbers and dashes
            \s*}}                           # }}
            \)?                             # optional )
            (?P<post>.*)$            # trailing text
        """

        m = re.match(pattern, text)
        if not m:
            return

        return m.group('issn'), m.group('post')

    @staticmethod
    def get_leading_url(text):
        pattern = r"""(?x)
            \[                              # [
            (?P<link>(//|http)[^ ]*)             # url
            \s*
            (?P<link_text>\s*.*?)?             # link text
            \]                              # ]
            (?P<post>.*)$            # trailing text
        """

        m = re.match(pattern, text)
        if not m:
            return

        link_text = m.group('link_text').strip() if m.group('link_text') else ""
        return link_text, m.group('link'), m.group('post')

    @staticmethod
    def get_leading_link(text):
        pattern = r"""(?x)
            (?P<link>\[\[:?(s|S|w|W|Special):.*?\]\])      # [[w:.*]] or [[s:.*]]
            (?P<post>.*)$            # trailing text
        """

        m = re.match(pattern, text)
        if not m:
            return

        return m.group('link'), m.group('post')

    @staticmethod
    # TODO: Convert to get_leading
    def get_gbooks(text):

        pattern = r"""(?x)
            ^(?P<pre>.*?)\s*         # leading text
            ({{gbooks.*?}})                 # gbooks template
            (?P<post>.*)$            # trailing text
        """
        m = re.match(pattern, text)
        if m:
            return m.group(2), m.group('pre') + " " + m.group('post')

        return "", text

    # leading - indicates that the match must be case-sensitive
    _number_labels = {
        "chapter": [
            "chapters",
            "chapter",
            "ch.",
            "ch ",
            ],
        "page": [
            "page",
            "pg.",
            "pg",
            "*p.",
            "*p ",
            "pages",
            "pp.",
            "*pp ",
            ],
        "issue": [
            "issue",
            "issues",
            "iss.",
            ],
        "volume": [
            "volume",
            "vol.",
            "vol",
            "volumes",
            "vols",
            "vols.",
            "*v.",
            "*v ",
            ],
        "series": [
            "series",
            "*s.",
            "*s ",
            ],
        "number": [
            "number",
            "num",
            "num.",
            "no.",
            "no ",
            "*n.",
            "*n ",
            "№",
            ],
        "episode": [
            "episode",
            "ep.",
            "ep",
            ],
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
        "song": [ "song" ],
        "epigraf": [ "epigraf" ],
        "epigram": [ "epigram", "epig ", "epig." ],
    }


    _number_aliases = {alias.lstrip("*"):label for label, aliases in _number_labels.items() for alias in aliases}

    _case_number_labels = [alias.lstrip("*") for aliases in _number_labels.values() for alias in aliases if alias.startswith("*")]
    _nocase_number_labels = [alias for aliases in _number_labels.values() for alias in aliases if not alias.startswith("*")]
    # Order longest to shortest to match longer strings before possible substrings
    _case_number_labels.sort(key=lambda x: (len(x)*-1, x))
    _nocase_number_labels.sort(key=lambda x: (len(x)*-1, x))

    _number_labels_regex = r"((?i:" + "|".join(map(re.escape, _nocase_number_labels)) \
            + ")|(" + "|".join(map(re.escape, _case_number_labels)) + "))"

    def get_leading_labeled_number(self, text):
        return self._get_leading_labeled_number(text, self._number_labels_regex)

    def _get_leading_labeled_number(self, text, label_regex):
        pattern = fr"""(?x)
            (?P<label>{label_regex})
            \s*
            [#]?                                           # number sign
            (?P<num1>[0-9ivxlcdmIVXLCDM]+)                 # numbers or roman numerals
            (
              (\s*(?P<separator>or|,|&|and|-|–|to|{{ndash}})+\s*)
              [#]?                                         # number sign
              (?P<num2>[0-9ivxlcdmIVXLCDM]+)               # numbers or roman numerals
            )?
            \b
            (?P<post>.*)
        """

        # TODO: if , is used make sure both numbers look similar

              #(\s*(?P<separator>or|,|&|and|-|–|to|{{ndash}})+\s*)


        m = re.match(pattern, text)
        if not m:

            pattern = fr"""(?x)
                (?P<label>{label_regex})
                \s*
                (?i:(?P<spelled>   # case-insensitive
                   (?P<teen>eleven|twelve|((thir|four|fif|six|seven|eigh|nine)(teen)))?
                   (?P<tens>ten|twenty|thirty|fourty|fifty|sixty|seventy|eighty|ninety)?
                   [- ]*
                   (?P<digit>one|two|three|four|five|six|seven|eight|nine)?
                ))
                \b
                (?P<post>.*)
            """
            m = re.match(pattern, text)
            if not m:
                return

            if not m.group('spelled').strip("- "):
                return

            teen = 0 if not m.group('teen') else \
                ["", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"].index(m.group('teen').lower())
            tens = 0 if not m.group('tens') else \
                ["", "ten", "twenty", "thirty", "fourty", "fifty", "sixty", "seventy", "eighty", "ninety"].index(m.group("tens").lower())
            digit = 0 if not m.group('digit') else \
                ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"].index(m.group('digit').lower())

            if teen and (tens or digit):
                print("nonsense number", m.group('spelled'))
                return
            if teen:
                number = 10 + teen
            else:
                number = tens*10+digit

            if not number:
                return

            label = self._number_aliases[m.group('label').lower()]
            return label, str(number), m.group('post')


        label = self._number_aliases[m.group('label').lower()]

        num1 = m.group('num1')
        num2 = m.group('num2')
        separator = m.group('separator')
        post_text = m.group('post')

        return tuple([label] + self.single_or_range(num1, num2, separator) + [post_text])

    @staticmethod
    def get_leading_edition(text):
        pattern = r"""(?x)
            (?P<edition>
            ((
                (1\d|20)\d{2}               # year (1000-2099)
                |travel(l)?er's
                |children's
                |illustrated
                |paperback
                |hardcover
                |softcover
                |revised
                |reprint
                |limited
                |first|second|third|((eleven|twelf|thir|four|fif|six|seven|eigh|nin(e)?|ten|eleven|twelf)(th|teen))
                |\d+(?:st|nd|rd|th)         # ordinal number
            )\s*)+
            (?:edition|ed\.)
            )
            (?P<post>.*)$            # trailing text
        """

        m = re.match(pattern, text, re.IGNORECASE)
        if not m:
            return

        return m.group('edition'), m.group('post')


    def get_leading_season(self, text):

        pattern = r"""(?x)
            \s*
            (?P<season>((Spring|Summer|Fall|Winter|Jan(uary)?|Feb(ruary)?|Mar(ch)?|Apr(il)?|May|Jun(e)?|Jul(y)?|Aug(ust)?|Sep(tember)?|Oct(ober)?|Nov(ember)?|Dec(ember)?)[—/—\- ]*)+)
            [.,]+                           # dot or comma
            (?P<post>.*)$            # trailing text
        """

        m = re.match(pattern, text)
        if not m:
            return

        return m.group('season').strip("—/—- "), m.group('post')

    def get_leading_date_retrieved(self, text):
        orig_text = text
        text = re.sub("^(retrieved|accessed)( on)?", "", text, re.IGNORECASE)
        if text == orig_text:
            return
        text = self._strip_leading_separators(text)
        return self.get_leading_date(text)

    def get_leading_month(self, text):
        pattern = r"""(?x)
            (?P<month>(Jan(uary)?|Feb(ruary)?|Mar(ch)?|Apr(il)?|May|Jun(e)?|Jul(y)?|Aug(ust)?|Sep(t)?(ember)?|Oct(ober)?|Nov(ember)?|Dec(ember)?))
            \b
            (?P<post>.*)$             # trailing text
        """

        m = re.match(pattern, text)
        if not m:
            return

        return m.group('month'), m.group('post')

    def get_leading_month_day(self, text):
        res = self._parse_leading_date(text)
        if not res:
            return

        year, month, day, post_text = res
        if year:
            return

        if month and day:
            return month, day, post_text

        return


    def get_leading_date(self, text):
        res = self._parse_leading_date(text)
        if not res:
            return

        year, month, day, post_text = res
        if not day:
            return

        return year, month, day, post_text


    def _parse_leading_date(self, text):

        # YYYY-MM-DD
        # YYYY, Month DD
        # MM-DD
        # Month DD
        pattern = r"""(?x)
            ((?P<dayname>(Sun|Mon|Tue(s)?|Thu(r?)(s)?|Fri)[.]?(day)?)\b)?   # Day name
            ([\.\-,/ ]*
                (?P<year1>
                    (\s|'''|\(|\[)*                # ''' or ( or [ (optional)
                    (1\d|20)\d{2}                  # Year
                    (\s|'''|\)|\])*                # ''' or ) or ] (optional)
                )
                ([.\-,/ ]|$)
            )?
            ([\.\-,/ ]*
                (?P<day1>3[01]|[12][0-9]|0?[1-9])    # Day 1
                (st|nd|rd|th)?
                \b
            )?
            ([.\-,/ ]*
                (?P<month>(0?[1-9]|1[012]|Jan(uary)?|Feb(ruary)?|Mar(ch)?|Apr(il)?|May|Jun(e)?|Jul(y)?|Aug(ust)?|Sep(t)?(ember)?|Oct(ober)?|Nov(ember)?|Dec(ember)?))
                \b
            )
            ([.\-,/ ]*
                (?P<day2>3[01]|[12][0-9]|0?[1-9])    # Day 2
                (st|nd|rd|th)?
                \b
            )?
            ([.\-,/ ]*
                (?P<year2>(1\d|20)\d{2})
                \b
            )? # Year2
            (?P<post>.*)$             # trailing text
        """

        m = re.match(pattern, text)

        if not m:
            return

        else:
            if not m.group('month'):
                print("NO MONTH")
                return

            if m.group('day1') and m.group('day2'):
                print("MULTI DAY")
                return

            if m.group('year1') and m.group('year2'):
                print("MULTI YEAR")
                return

            if m.group('day1'):
                day = int(m.group('day1')) * -1
            elif m.group('day2'):
                day = int(m.group('day2'))
            else:
                day = 0

            if m.group('dayname') and not day:
                print("DAYNAME without day")
                return

            year = m.group('year1') or m.group('year2')
            if year:
                if year.startswith("'") and year.endswith("'"):
                    year = year.strip("'")
                if year.startswith("[") and year.endswith("]"):
                    year = year.strip("[]")
                if year.startswith("(") and year.endswith(")"):
                    year = year.strip("()")
                if len(year) != 4:
                    print("BAD YEAR", year)
                    return

            month = m.group('month')
            if month.isnumeric():

                # Don't match 7 15 as July 15, but do match 7 15 2002
                if not year:
                    return

                # Don't handle ambiguous dates likes 02-05, 03-14 is good, 14-03, too
                if not day or abs(day) < 13:
                    print("AMBIG DAY", day, month)
                    return

                month = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][int(m.group('month'))-1]

            if month == "Feb" and abs(day) > 29:
                print("INVALID DAY", day, month)
                return

            if month in ["Apr", "Jun", "Sep", "Nov"] and abs(day)>30:
                print("INVALID DAY", day, month)
                return

            if abs(day)>31:
                return

            return year, month, day, m.group('post')


    def cleanup_text(self, text):
        # Normalize whitespace
        text = re.sub(r"\s+", " ", text)

        # Remove templates that just wrap other text
        text = self.strip_wrapper_templates(text, ["nowrap", "nobr"])

        html_tags = ["sup", "span", "small"]
        text = re.sub(r"<\s*/?\s*(" + "|".join(html_tags) + r")\b.*?>", "", text)
        text = text.replace('{{,}}', ",")
        text = text.replace('{{nbsp}}', " ")
        text = text.replace('&nbsp;', " ")
        text = text.replace("–", "-")
        text = text.replace('&mdash;', "-")
        text = text.replace('&ndash;', "-")
#
#        text = text.replace('[[et alios]]', "et al.")
#        text = text.replace('[[et al]]', "et al.")
#        text = text.replace('[[et alia]]', "et al.")
#        text = text.replace('[[et alii]]', "et al.")
#        text = text.replace('[[et al]]', "et al.")
#        text = text.replace("''et al.''", "et al.")
#        text = text.replace("et alii", "et al.")
#        text = text.replace(' et. al.', "et al.")

        return text


    def get_params(self, text):

        print("___")
        print(text)

        # Fail if comments
        if "<!--" in text or "-->" in text:
            #self.warn("html_comment")
            return

        clean_text = self.cleanup_text(text)
        parsed = self.parse_text(clean_text)

        return self.convert_parsed_to_params(parsed)


    def get_transformer(self, fingerprint):
        fp_keys = {k for k in fingerprint}
        transformers = [ h[4] for h in self._all_handlers if self.can_handle(h, fingerprint, fp_keys) ]
        if not transformers:
            return

        if not all(t == transformers[0] for t in transformers):
            raise ValueError("Multi matches", fingerprint, transformers)
        return transformers[0]

    def can_handle(self, handler, fingerprint, fingerprint_keys):
        must_contain, match_list, may_contain, cannot_contain, transformer = handler

        # If must_contain is a list of sets, use the first set
        # that the fingerprint passes
        if must_contain and isinstance(must_contain, list):
            found = None
            for k in must_contain:
                if not k-fingerprint_keys:
                    found = k
                    break
            if not found:
                return False
            must_contain = found

        if must_contain and must_contain-fingerprint_keys:
            return False

        fp_list = []
        for f in fingerprint:
            if f in match_list:
                fp_list.append(f)
            elif f not in may_contain and f not in must_contain:
                return False
            elif f in cannot_contain:
                return False

        return match_list == fp_list

    def convert_parsed_to_params(self, parsed):

        fingerprint = self.get_fingerprint(parsed)

        transformer = self.get_transformer(fingerprint)
        if not transformer:
            print("UNHANDLED:", fingerprint)
            return

        handler = transformer["_handler"]

#        transformer, handler = self._fingerprints.get(fingerprint, (None,None))
#        if not handler:
#            fingerprint = self.get_fingerprint(parsed, condense_unhandled=True)
#            transformer, handler = self._fingerprints.get(fingerprint, (None,None))

#        if not handler:
#            print("UNHANDLED:", fingerprint)
#            return

        print("FINGERPRINT:", fingerprint)
        self.apply_transformation(parsed, transformer)

        params = handler(self, parsed)
        if params:
            print("PARAMS:", params)

        self.cleanup_params(params)

        return params

    def cleanup_params(self, params):
        if not params:
            return

        for k in ["title", "chapter", "journal", "publisher"]:
            if k in params:
                params[k] = params[k].strip(", ")

        if params.get('year_published', -1) == params.get('year', 0):
            del params['year_published']

    def add_date(self, details, date):
        year, month, day = date

        # rename year to date to preserve dictionary order
        if year == details.get("year"):
            details = {"date" if k == "year" else k:v for k,v in details.items()}

        if not year:
            year = details["year"]
        elif "year" in details and int(year) != int(details["year"]):
            # TODO: currently a secondary date with a month is used to indicate
            # that it's a journal, but there's no way to included published_date in journals
            # This only happens in a handful of cases
            self.dprint("ERROR: published year doesn't match citation year")
            return

        if day:
            if day < 0:
                date = f"{day*-1} {month} {year}"
            else:
                date = f"{month} {day} {year}"

            # rename year to date to preserve dictionary order
            if "year" in details:
                details = {"date" if k == "year" else k:v for k,v in details.items()}
            details["date"] = date

        else:
            details["month"] = month

        return details


    def journal_handler(self, parsed):
        allowed_params = {"year", "journal", "author", "volume", "issue", "page", "pages", "url", "title", "titleurl", "month", "publisher", "pageurl", "year_published", "issues", "location"}
        return self.generic_handler(parsed, "journal", allowed_params)

    def web_handler(self, parsed):
        details = { "_source": "web" }
        allowed_params = {"year", "site", "url"}
        for item_type, values in parsed:
            if item_type == "separator":
                continue

            elif item_type == "author":
                assert len(values) == 1
                for idx, value in enumerate(values, 1):
                    key = f"author{idx}" if idx>1 else "author"
                    details[key] = value

            else:
                if item_type not in allowed_params:
                    raise ValueError("unhandled type", item_type, values)

                if len(values) != 1:
                    print("unhandled multi-values", item_type, values)
                    return
                    raise ValueError("unhandled multi-values", item_type, values)
                details[item_type] = values[0]
        return details



    def newsgroup_handler(self, parsed):
        details = { "_source": "newsgroup" }
        allowed_params = {"year", "title", "newsgroup", "url"}
        for item_type, values in parsed:
            if item_type.endswith("separator"):
                continue

            elif item_type == "date":
                details = self.add_date(details, values)
                if not details:
                    return

            elif item_type == "author":
                if not len(values) == 1:
                    return
                for idx, value in enumerate(values, 1):
                    key = f"author{idx}" if idx>1 else "author"
                    details[key] = value

            else:
                if item_type not in allowed_params:
                    raise ValueError("unhandled type", item_type, values)

                if len(values) != 1:
                    print("unhandled multi-values", item_type, values)
                    return
                    raise ValueError("unhandled multi-values", item_type, values)
                details[item_type] = values[0]
        return details


    def text_handler(self, parsed):
        details = { "_source": "text" }

        allowed_params = {"page", "title", "year", "location", "publisher", "chapter", "pageurl", "year_published", "series", "url", "volume"}
        for item_type, values in parsed:

            if item_type == "separator":
                continue

            elif item_type == "author":
                assert len(values)
                for idx, value in enumerate(values, 1):
                    key = f"author{idx}" if idx>1 else "author"
                    details[key] = value

            elif item_type in ["editor", "translator"]:
                assert len(values)
                if len(values) == 1:
                    details[item_type] = values[0]
                else:
                    details[item_type + "s"] = "; ".join(values)

            else:
                if item_type not in allowed_params:
                    raise ValueError("unhandled type", item_type, values)

                if len(values) != 1:
                    print("unhandled multi-values", item_type, values)
                    return
                    raise ValueError("unhandled multi-values", item_type, values)
                details[item_type] = values[0]


        # Links to google books can be classified as books
        url = details.get("url", "")
        if ".google." in details.get("url", "") or re.search("google.[^/]*/books/", url):
            details["_source"] = "book"
#        else:
#            return

        return details


    def generic_handler(self, parsed, source, allowed_params):
        details = { "_source": source }

        def save(k,v):
            if k in details:
                print("dup value", k, v, parsed)
                details["__failed_dup_value"] = True
            details[k] = v

        for item_type, values in parsed:

            if item_type == "date":
                details = self.add_date(details, values)
                if not details:
                    return
                continue

            if item_type == "accessdate":
                year, month, day = values
                save("accessdate", f"{abs(day)} {month} {year}")
                continue

            if item_type == "url::page":
                assert len(values) == 1
                save("page", values[0])

                # rename url to pageurl
                details = {"pageurl" if k in ["url", "chapterurl"] else k:v for k,v in details.items()}
                continue

            if item_type == "url::chapter":
                assert len(values) == 1
                save("chapter", values[0])

                # rename url to chapter
                details = {"chapterurl" if k == "url" else k:v for k,v in details.items()}
                continue

            if item_type.endswith("separator"):
                continue

            elif item_type in ["isbn"]:
                save(item_type, "; ".join(values[0]))

            elif item_type.startswith("maybe_"):
                print(f"{item_type}: {values}")
                return

#            elif item_type == "_maybe_publisher":
#                assert len(values) == 1
#                if "publisher" in details:
#                    return
#
#                text = values[0]
#                if "location" not in details:
#                    res = self.get_leading_location(text)
#                    if res:
#                        location, post_text = res
#                        if location and not post_text:
#                            save("location", location)
#                            continue
#
#                text = re.sub(r"^\s*in\s+", "", text)
#                print("MAYBE_PUB:", text)
#                save("publisher", text)
#                return


#            elif item_type == "_maybe_bare_page_link":
#                assert len(values) == 1
#                if "url" in details and "page" not in details and values[0].isnumeric():
#                    details = {"pageurl" if k == "url" else k:v for k,v in details.items()}
#                    save("page", values[0])
#                else:
#                    return

            elif item_type == "author":
                assert len(values)
                for idx, value in enumerate(values, 1):
                    key = f"author{idx}" if idx>1 else "author"
                    if value.endswith("'s"):
                        value = value[:-2]
                    save(key, value)

#            elif item_type == "publisher2":
#                assert len(values) == 1
#                # assign directly to modify existing value
#                details["publisher"] += f" ({values[0]})"

            #elif item_type == "_maybe_publisher":
            #    assert len(values) == 1
            #    publisher = values[0].strip(",:; ")
            #    if "," in values[0]:
            #        return
#
#                pattern = r"\b(([ivxlcdmIVXLCDM]+|[0-9]+(st|nd|rd)?|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirfour|fif)(teen)?|chapter|prayer|sermon|issue|volume|text|series|page|postscript|preface|epistle|prologue)\b"
#                if re.search(pattern, publisher, re.IGNORECASE):
#                    return
#                details["publisher"] = publisher

            elif item_type in ["editor", "translator"]:
                assert len(values)
                if len(values) == 1:
                    save(item_type, values[0])
                else:
                    save(item_type + "s", "; ".join(values))

            else:
                if item_type not in allowed_params:
                    raise ValueError("unhandled type", item_type, values, parsed)

                if len(values) != 1:
                    print("unhandled multi-values", item_type, values)
                    return
                    raise ValueError("unhandled multi-values", item_type, values)

                save(item_type, values[0])


        if "__failed_dup_value" in details:
            return

        return details


    def book_handler(self, parsed):
        allowed_params = {"page", "pages", "title", "year", "location", "publisher", "chapter", "pageurl", "year_published", "series", "url", "volume", "issn", "oclc", "month"}
        return self.generic_handler(parsed, "book", allowed_params)


    def apply_transformation(self, parsed, transformer):
        for idx, item in enumerate(parsed):
            label, values = item
            new_label = transformer.get(label)
            if new_label:
                parsed[idx] = (new_label, values)

#    _book = {"*page": "page"}
    _year2_published = {"year2": "year_published" }
    _url_page_page = {} #{ "url::page": "page", "_page_is_urlpage" }
    #_urlpage = {"url": "pageurl", "url::page": "page"}
    _paren_italics_series = {"paren::italics": "series"}
    _chapter_title = {"italics": "chapter", "italics2": "title"}
    _year2_year_published = {"year2": "year_published"}
    _fancy_dq_chapter = {"fancy_double_quotes": "chapter"}

    _paren_newsgroup_newsgroup = {"paren::newsgroup": "newsgroup"}

    _dq2_title = {"double_quotes2": "title"}
    _dq_author = {"double_quotes": "author"}
    _skip_italics = {"italics": "separator"}
    _skip_italics2 = {"italics2": "separator"}
    _italics_title = {"italics": "title"}
    _dq_title = {"double_quotes": "title"}
    _fancy_dq_title = {"fancy_double_quotes": "title"}

    _dq_url_url = {"double_quotes::url": "url"}
    _dq_url_titleurl = {"double_quotes::url": "titleurl"}
    _dq_url_text_title = {"double_quotes::url::text": "title"}

    _skip_paren_unhandled = { "paren::unhandled": "separator" }
    _skip_unhandled = { "unhandled": "separator" }

    _web = {"_handler": web_handler, }
    _url_unhandled_publisher = { "url::unhandled": "publisher" }
    _unhandled_publisher = { "unhandled": "_maybe_publisher" }

    _paren_volumes = { "paren::volumes": "volume" }
    _paren_volume = { "paren::volume": "volume" }
    _paren_issue = { "paren::issue": "issue" }
    _paren_issues = { "paren::issues": "issue" }
    _paren_page = { "paren::page": "page" }
    _paren_date = { "paren::date": "date" }
    _url_dq_title = { "url::double_quotes": "title"}
    _url_is_titleurl = { "url": "titleurl" }
    _paren_publisher = {"paren": "_maybe_publisher"}

    _paren_italics_maybe_journal = { "paren::italics": "maybe_journal" }
    _italics_maybe_journal = { "italics": "maybe_journal" }


    _text = {"_handler": text_handler, }
    _url_text_title = {"url::text": "title"}
    _fq_title = {"fancy_quote": "title"}

    _paren_pub2 = {"paren": "publisher2"}
    #_url_page_page = {"url::page": "page"}
    _url_italics_title = {"url::italics": "title"}

    _italics_link_title = {"italics::link": "title"}
    _url_date_date = {"url::date": "date"}

    _dq_chapter = {"double_quotes": "chapter"}
    _fq_chapter = {"fancy_quote": "chapter"}

    _link_title = {"link": "title"}
    _link_journal = {"link": "journal"}
    _link_publisher = {"link": "publisher"}
    _italics_chapter = {"italics": "chapter"}

    _url_titleurl = {"url": "titleurl"}

    _paren_volumes_volume = {"paren::volumes": "volume"}

#    _italics_chapter = {"italics": "chapter"}
#    _unhandled_location_or_publisher = {"unhandled": "_location_or_publisher"}



    @staticmethod
    def make_anywhere(normal, plurals, alt_keys):
        _anywhere = set()
        _anywhere_tr = {}
        for x in normal:
            _anywhere.add(x)
            _anywhere.add(f"url::{x}")
            _anywhere.add(f"paren::{x}")

            _anywhere_tr[f"url::{x}"] = x
            _anywhere_tr[f"paren::{x}"] = x

        # plurals
        for v in plurals:
            for k in [v, v+"s"]:
                _anywhere.add(k)
                _anywhere.add(f"url::{k}")
                _anywhere.add(f"paren::{k}")

                _anywhere_tr[k] = v
                _anywhere_tr[f"url::{k}"] = v
                _anywhere_tr[f"paren::{k}"] = v


        for k,v in alt_keys.items():
            _anywhere.add(k)
            _anywhere.add(f"url::{k}")
            _anywhere.add(f"paren::{k}")

            _anywhere_tr[k] = v
            _anywhere_tr[f"url::{k}"] = v
            _anywhere_tr[f"paren::{k}"] = v

        return _anywhere, _anywhere_tr




#    _book_optionals = { "_match_anywhere_optional": ('translator', 'translators', 'location', 'editor', 'publisher', 'year2', 'chapter', 'page', 'pages', 'url', 'url::page') } | _year2_published | _urlpage

    _book = {"_handler": book_handler, "italics": "title"}
    _book_anywhere, _book_anywhere_tr = make_anywhere(
        [ 'year', 'month', 'author', 'translator', 'location', 'editor', 'publisher', 'isbn', 'issn', 'oclc'],
        [ "volume", "chapter", "page" ],
        # alternate keys
        {
#            "issues": "issues",
            "pages": "pages",
            "year2": "year_published",
            "date_retrieved": "accessdate"
        }
    )
    _book_anywhere |= {'url'}
    _book_anywhere_tr |= {
        "url::page": "url::page", # instead of just 'page', to trigger 'url' -> 'urlpage'
        "url::chapter": "url::chapter",
    }



    #_book_anywhere = { 'translator', 'location', 'editor', 'publisher', 'year2', 'chapter', 'chapters', 'page', 'pages', 'url', 'url::chapter', 'url::page', 'isbn', 'issn', 'oclc', 'paren::isbn', 'paren::issn', 'paren::oclc', "date_retrieved", "paren::date_retrieved"}
    #_book_anywhere_tr = {'year2': "year_published", 'paren::isbn': 'isbn', 'paren::issn': 'issn', 'paren::oclc': 'oclc', "date_retrieved": "accessdate", "paren::date_retrieved": "accessdate", "volumes": "volume"}
    _book_exclude = { 'newsgroup', 'paren::newsgroup', 'journal', 'italics::journal' }

    book_must_include = [
        {"author", "chapter"},
        {"author", "url::chapter"},
        {"author", "page"},
        {"author", "url::page"},

        {"editor", "chapter"},
        {"editor", "url::chapter"},
        {"editor", "page"},
        {"editor", "url::page"},
    ]

    maybe_journal_must_include = [
        {'date'},
        {'url::date'},
        {'paren::date'},

        {'year', 'month'},
        {'year', 'url::month'},
        {'year', 'paren::month'},

        {'issue'},
        {'paren::issue'},

        {'issues'},
        {'paren::issues'},
    ]
    journal_must_include = [
        { 'journal' },
        { 'italics::journal' },
        { 'paren::italics::journal' },
    ]
    _journal = {"_handler": journal_handler, "italics::journal": "journal", "paren::italics::journal": "journal", "volumes": "volume"}
        #(journal_must_include, ['italics', 'paren::volumes', 'paren::page']


    _journal_anywhere, _journal_anywhere_tr = make_anywhere(
        ['date', 'year', 'month', 'author', 'translator', 'location', 'editor', 'publisher', 'isbn', 'issn', 'oclc'],
        [ "issue", "page", "volume" ], # not chapter
        # alternate keys
        {
            #"issues": "issues",
            "pages": "pages",
            "year2": "year_published",
            "date_retrieved": "accessdate"
        }
    )
    _journal_anywhere |= {'url'}
    _journal_anywhere_tr |= {
        "url::page": "url::page", # instead of just 'page', to trigger 'url' -> 'urlpage'
    }

#    print(_journal_anywhere_tr)
#    _orig = { 'date', 'year', 'month', 'author', 'translator', 'location', 'editor', 'publisher', 'year2', 'issue', 'issues', 'volumes', 'page', 'pages', 'url', 'url::chapter', 'url::page', 'isbn', 'issn', 'oclc', 'url::date', 'paren::volume', 'paren::volumes', 'paren::page', 'paren::issues', 'paren::issue', 'paren::date', 'date_retrieved', 'paren::date_retrieved'}
#    print(_journal_anywhere)
#    print(_orig-_journal_anywhere)
#    raise ValueError()

    # Alternate terms
#`    _journal_anywhere_tr = {'year2': "year_published", 'issues': 'issue', 'volumes': 'volume', 'url::date': 'date', 'paren::date': 'date', 'paren::month': 'month', 'url::month': 'month', 'paren::volumes': 'volume', 'paren::volume': 'volume', 'paren::page': 'page', 'paren::issues': 'issue', 'paren::issue': 'issue', "date_retrieved": "accessdate", "paren::date_retrieved": "accessdate"}


    #_journal_anywhere = { 'date', 'year', 'month', 'author', 'translator', 'location', 'editor', 'publisher', 'year2', 'issue', 'issues', 'volumes', 'page', 'pages', 'url', 'url::chapter', 'url::page', 'isbn', 'issn', 'oclc', 'url::date', 'paren::volume', 'paren::volumes', 'paren::page', 'paren::issues', 'paren::issue', 'paren::date', 'date_retrieved', 'paren::date_retrieved'}
    #_journal_anywhere_tr = {'year2': "year_published", 'issues': 'issue', 'volumes': 'volume', 'url::date': 'date', 'paren::date': 'date', 'paren::month': 'month', 'url::month': 'month', 'paren::volumes': 'volume', 'paren::volume': 'volume', 'paren::page': 'page', 'paren::issues': 'issue', 'paren::issue': 'issue', "date_retrieved": "accessdate", "paren::date_retrieved": "accessdate"}
    _journal_exclude = { 'newsgroup', 'paren::newsgroup' }

    newsgroup_must_contain = [
        {'newsgroup', 'date'},
        {'newsgroup', 'year'},
        {'paren::newsgroup', 'date'},
        {'paren::newsgroup', 'year'},
    ]
    _newsgroup = {"_handler": newsgroup_handler, 'paren::newsgroup': 'newsgroup'}
    _newsgroup_anywhere = {"date_retrieved", "paren::date_retrieved"}
    _newsgroup_anywhere_tr = {"date_retrieved": "accessdate", "paren::date_retrieved": "accessdate"}
    _newsgroup_exclude = {}

    ###HANDLERS
    _all_handlers = [
        # Text handlers
        ({}, ['year', 'author'], {}, {}, _text),
        ({}, ['year', 'author', 'url', 'url::text'], {}, {}, _text|_url_text_title),
        ({}, ['year', 'author', 'double_quotes'], {}, {}, _text|_dq_title),
        ({}, ['year', 'author', 'italics'], {}, {}, _text|_italics_title),
        ({}, ['year', 'author', 'fancy_quote'], {}, {}, _text|_fq_title),
        ({}, ['year', 'url', 'url::italics', 'author'], {}, {}, _text|_url_italics_title),
        ({}, ['year', 'url', 'url::text', 'page'], {}, {}, _text|_url_text_title),
        ({}, ['year', 'url', 'url::text'], {}, {}, _text|_url_text_title),
        ({}, ['year', 'italics', 'author'], {}, {}, _text|_italics_title),
        ({}, ['year', 'author', 'url', 'url::italics'], {}, {}, _text|_url_italics_title),
#        ({}, ['year', 'italics', 'paren::volumes', 'paren::page'], {}, {}, _text|_paren_volumes_volume|_paren_page),

        # Web handlers
        ({}, ['year', 'url', 'url::unhandled<VOA Learning English>', 'paren::unhandled<public domain>'], {}, {},
            _web|_url_unhandled_publisher|_skip_paren_unhandled),

        # Book handlers
        (book_must_include, ['year', 'italics'], _book_anywhere, _book_exclude, _book|_book_anywhere_tr),
        (book_must_include, ['year', 'italics::link'], _book_anywhere, _book_exclude, _book|_book_anywhere_tr|_italics_link_title),
        (book_must_include, ['year', 'fancy_quote', 'italics'], _book_anywhere, _book_exclude, _book|_book_anywhere_tr|_fq_chapter),
        (book_must_include, ['year', 'fancy_double_quotes', 'italics'], _book_anywhere, _book_exclude, _book|_book_anywhere_tr|_fancy_dq_chapter),
        (book_must_include, ['year', 'italics', 'double_quotes'], _book_anywhere, _book_exclude, _book|_book_anywhere_tr|_dq_chapter),
        (book_must_include, ['year', 'italics', 'italics2'], _book_anywhere, _book_exclude, _book|_book_anywhere_tr|_chapter_title),

        (book_must_include, ['year', 'italics', 'fancy_double_quotes'], _book_anywhere, _book_exclude, _book|_book_anywhere_tr|_fancy_dq_chapter),

        # text is not title
        #(book_must_include, ['year', 'italics', 'url', 'url::text'], {}, {}, _book|_italics_chapter|_url_text_title),


        #(book_must_include, ['year', 'italics', 'unhandled:], _book_anywhere, _book_exclude, _book|_book_anywhere_tr),
            # TODO: Check for unhandled<"page"> followed by url, url::unhandled<number>

# Mostly translated titles
#        ({'author', 'page'}, 'year, italics, paren::italics', _book_anywhere, _book|_book_anywhere_tr|_paren_italics_series),
#            (('year', 'author', 'italics', 'url', 'url::text'), _book| {"url::text": "_maybe_bare_page_link"}),


        # Journal handlers
            #('year', 'journal', 'month', 'year2'),
        (journal_must_include, [], _journal_anywhere, _journal_exclude, _journal|_journal_anywhere_tr),
        (journal_must_include, ['italics'], _journal_anywhere, _journal_exclude, _journal|_journal_anywhere_tr|_italics_title),
        (journal_must_include, ['url::double_quotes'], _journal_anywhere, _journal_exclude, _journal|_journal_anywhere_tr|_url_dq_title|_url_titleurl),

        (journal_must_include, ['double_quotes::url', 'double_quotes::url::text'], _journal_anywhere, _journal_exclude, _journal|_journal_anywhere_tr|_dq_url_text_title|_dq_url_titleurl),



# Enable this, grep "maybe_journal" in the output, then add valid journals to the allow list
# grep maybe_journal fixes.all | sort | uniq >> allowed_journals
#        ({}, ['year', 'italics', 'volumes', 'page'], {}, {}, _journal|_italics_maybe_journal),
#        ({}, ['year', 'italics', 'paren::volumes', 'paren::page'], {}, {}, _journal|_paren_volumes_volume|_paren_page|_italics_maybe_journal),
#        (maybe_journal_must_include, ['italics'], _journal_anywhere, _journal_exclude, _journal|_journal_anywhere_tr|_italics_maybe_journal),
#        (maybe_journal_must_include, ['url::double_quotes', 'italics'], _journal_anywhere, _journal_exclude, _journal|_journal_anywhere_tr|_url_dq_title|_italics_maybe_journal),
#        (maybe_journal_must_include, ['italics', 'paren::italics'], _journal_anywhere, _journal_exclude, _journal|_journal_anywhere_tr|_paren_italics_maybe_journal),
        #({},  'italics', 'url', 'url::date'), _journal_exclude, _journal|_italics_journal|_url_date_date),


#        ('date', 'author', 'double_quotes::url', 'double_quotes::url::text', 'newsgroup')


#('date', 'author', 'double_quotes::url', 'double_quotes::url::text', 'newsgroup')

        #newsgroup_handler
        (newsgroup_must_contain, ['author', 'italics'], {'url'}, _newsgroup_exclude, _newsgroup|_italics_title),
        (newsgroup_must_contain, ['author', 'double_quotes'], {'url'}, _newsgroup_exclude, _newsgroup|_dq_title),
        (newsgroup_must_contain, ['author', 'double_quotes::url', 'double_quotes::url::text'], [], _newsgroup_exclude, _newsgroup|_dq_url_url|_dq_url_text_title),
        (newsgroup_must_contain, ['author', 'fancy_double_quotes'], {'url'}, _newsgroup_exclude, _newsgroup|_fancy_dq_title),

        (newsgroup_must_contain, ['double_quotes', 'italics'], {'url'}, _newsgroup_exclude, _newsgroup|_dq_author|_italics_title),

#('year', 'double_quotes', 'italics', 'paren::newsgroup')


    ]
    _old_handlers = [
        # text_handler: [
            (('year', 'author'), _text),
            (('year', 'author', 'url', 'url::text'), _text|_url_text_title),
            (('year', 'author', 'double_quotes'), _text|_dq_title),
            (('year', 'author', 'italics'), _text|_italics_title),
            (('year', 'author', 'fancy_quote'), _text|_fq_title),
            (('year', 'url', 'url::italics', 'author'), _text|_url_italics_title),
            (('year', 'url', 'url::text', 'page'), _text|_url_text_title),
            (('year', 'url', 'url::text'), _text|_url_text_title),
            (('year', 'italics', 'author'), _text|_italics_title),
            (('year', 'author', 'url', 'url::italics'), _text|_url_italics_title),
        #],

        #book_handler: [

            (('year', 'author', 'italics', 'page'), _book),
            (('year', 'author', 'italics', 'url', 'url::page'), _book|_url_page_page),
            (('year', 'author', 'italics', 'url', 'url::text'), _book| {"url::text": "_maybe_bare_page_link"}),

#            (('year', 'author', 'fancy_quote', 'italics'), _book|_fq_chapter|_book_optionals)

            #({must_match_anywhere}, "fingerprint,as,regex", {can_match_anywhere}, _transformers),
#            ({}, "(year|date),author,fancy_quote,italics", _book_optional, _transformers, _book|_fq_chapter|_book_optional_tr),
#            (('year', 'author', 'fancy_quote', 'italics', '?location', '?editor', '?publisher', '?year2', '?chapter', '?page', '?pages', '?url', '?url::page'), _book|_fq_chapter|_year2_published|_urlpage),


            (('year', 'author', 'fancy_quote', 'italics', '?location', '?editor', '?publisher', '?year2', '?chapter', '?page', '?pages', '?url', '?url::page'), _book|_fq_chapter|_year2_published|_url_page_page),
            (('year', 'author', 'fancy_double_quotes', 'italics', '?location', '?editor', '?publisher', '?year2', '?chapter', '?page', '?pages', '?url', '?url::page'), _book|_fancy_dq_chapter|_year2_published|_url_page_page),

#            ({"publisher"}, "year,author,italics", _book_optional, _transformers, _book|_book_optional_tr),
            (('year', '?translator', 'author', 'italics', '?location', '?editor', 'publisher', '?year2', '?chapter', '?page', '?pages', '?url', '?url::page'), _book|_url_page_page|_year2_published),
#            ({"chapter"}, "year,author,italics", _book_optional, _transformers, _book|_book_optional_tr),
            (('year', 'author', 'italics', '?location', '?editor', '?publisher', '?year2', 'chapter', '?page', '?pages', '?url', '?url::page'), _book|_url_page_page|_year2_published),

            # Not necessarily a book/chapter
            #(('year', 'author', 'italics', '?location', '?editor', 'fancy_double_quotes', '?publisher', '?year2', '?chapter', '?page', '?url', '?url::page'), _book|_fancy_dq_chapter|_urlpage|_year2_published),
            (('year', 'author', 'italics', '?location', '?editor', 'double_quotes', '?publisher', '?year2', '?chapter', '?page', '?pages', '?url', '?url::page'), _book|_dq_chapter|_url_page_page|_year2_published),
            (('year', 'author', 'italics', '?location', '?editor', 'italics2', '?publisher', '?year2', '?chapter', '?page', '?pages', '?url', '?url::page'), _book|_chapter_title|_url_page_page|_year2_published),

            (('year', 'author', 'italics::link', '?location', '?editor', '?publisher', '?year2', '?chapter', '?page', '?pages', '?url', '?url::page'), _book|_italics_link_title|_url_page_page|_year2_published),

            (('year', 'editor', 'italics', 'location', 'publisher', 'page'), _book),



#            (('year', 'author', 'italics', 'location', 'publisher', 'fancy_double_quotes', 'page', 'url'), _book|_fancy_dq_chapter),
#            (('year', 'author', 'italics', 'location', 'unhandled<*>', 'fancy_double_quotes', 'page', 'url'), _book|_fancy_dq_chapter|_unhandled_publisher),

#            (('year', 'author', 'italics', 'location', 'publisher', 'page'), _book),


#            (('year', 'author', 'italics', 'location', 'publisher', 'page', 'url'), _book),
#            (('year', 'author', 'italics', 'location', 'unhandled<*>', 'page', 'url'), _book|_unhandled_publisher),

#            (('year', 'author', 'italics', 'location', 'publisher', 'volume', 'chapter', 'page', 'url'), _book|_italics_title),
#            (('year', 'author', 'italics', 'location', 'unhandled<*>', 'volume', 'chapter', 'page', 'url'), _book|_italics_title|_unhandled_publisher),

#            (('year', 'author', 'italics', 'location', 'publisher', 'year2', 'chapter', 'page', 'url'), _book|_year2_published),
#            (('year', 'author', 'italics', 'location', 'unhandled<*>', 'year2', 'chapter', 'page', 'url'), _book|_year2_published|_unhandled_publisher),

#            (('year', 'author', 'italics', 'location', 'publisher', 'year2', 'page'), _book|_year2_year_published),
#            (('year', 'author', 'italics', 'location', 'unhandled<*>', 'year2', 'page'), _book|_year2_year_published|_unhandled_publisher),

#            (('year', 'author', 'italics', 'location', 'publisher', 'url'), _book|_unhandled_publisher),
            # This is not safe to run unmonitored
            #(('year', 'author', 'italics', 'location', 'unhandled<*>', 'url'), _book|_unhandled_publisher),

            # TODO: anything in first_italics should become "title"
#            (('year', 'author', 'italics::location', 'publisher', 'year2', 'page'), _book|_year2_published),

            # Template doesn't handle "part"
            #(('year', 'author', 'italics', 'location', 'publisher', 'part', 'chapter', 'page', 'url'), _book|_italics_title),




#            (('year', 'author', 'italics', 'publisher', 'page'), _book),
            (('year', 'author', 'italics', 'publisher', 'paren', 'url', 'url::page'), _book|_paren_pub2|_url_page_page),
#            (('year', 'author', 'italics', 'publisher', 'url', 'url::page'), _book|_urlpage),
#            (('year', 'author', 'italics', 'publisher', 'year2', 'chapter'), _book|_year2_year_published),

#            (('year', 'author', 'italics', 'publisher', 'year2', 'page'), _book|_year2_year_published),
#            (('year', 'author', 'italics', 'unhandled<*>', 'year2', 'page'), _book|_year2_published|_unhandled_location_or_publisher),

#            (('year', 'author', 'italics', 'location', 'unhandled<*>', 'page'), _book|{"unhandled": "_unhandled_publisher"}),

            (('year', 'author', 'italics', 'publisher', 'year2', 'paren::italics', 'page'), _book|_paren_italics_series|_year2_published),

#            (('year', 'author', 'italics', 'translator', 'link'))


            (('year', 'author', 'italics', 'volume', 'publisher', 'page'), _book),

            (('year', 'author', 'italics::link', 'link', 'page'), _book|_italics_link_title|_link_publisher),
#            (('year', 'author', 'italics::link', 'location', 'publisher', 'year2', 'chapter', 'page', 'url'), _book|_italics_link_title|_year2_year_published),

            # Not safe to run unsupervised (paren contains junk like "thesis" or "a translation of selected notes")
            #(('year', 'author', 'italics', 'paren', 'page'), _book|_italics_title|_paren_publisher),

            (('year', 'author', 'fancy_double_quotes', 'italics', 'location', 'unhandled<*>', 'page', 'url'), _book|_fancy_dq_chapter|_unhandled_publisher),

#            (('year', 'italics', 'author', 'url', 'url::page'), _book|_urlpage|{"author":"_merge_publisher"}),

            (('year', 'editor', 'italics', 'location', 'unhandled<*>', 'page'), _book|_unhandled_publisher),


        #],

        #newsgroup_handler: [
            (('?year', '?date', 'author', 'italics', 'newsgroup', '?url'), _newsgroup|_italics_title),
            (('?year', '?date', 'author', 'double_quotes', 'newsgroup', '?url'), _newsgroup|_dq_title),
            (('?year', '?date', 'author', 'double_quotes::url', 'double_quotes::url::text', 'newsgroup'), _newsgroup|_dq_url_url|_dq_url_text_title),

            (('?year', '?date', 'double_quotes', 'italics', 'newsgroup', '?url'), _newsgroup|_dq_author|_italics_title),
            (('?year', '?date', 'double_quotes', 'italics', 'paren::newsgroup', '?url'), _newsgroup|_dq_author|_italics_title|_paren_newsgroup_newsgroup),
            (('?year', '?date', 'author', 'fancy_double_quotes', 'newsgroup', '?url'), _newsgroup|_fancy_dq_title),
            (('?year', '?date', 'double_quotes', 'paren::unhandled<username>', 'double_quotes2', 'newsgroup', '?url'), _newsgroup|_dq_author|_skip_paren_unhandled|_dq2_title),
            (('?year', '?date', 'double_quotes', 'paren::unhandled<username>', 'italics', 'newsgroup', '?url'), _newsgroup|_dq_author|_skip_paren_unhandled|_italics_title),
        #],

        #web_handler: [
            (('year', 'url', 'url::unhandled<VOA Learning English>', 'paren::unhandled<public domain>'), _web|_url_unhandled_publisher|_skip_paren_unhandled),
        #],

        #journal_handler: [
#            (('date', 'author', 'italics'), _journal|_italics_journal),
#
#            (('date', 'author', 'url', 'url::double_quotes', 'italics'), _journal|_url_is_titleurl|_url_dq_title|_italics_journal),
#            (('date', 'italics', 'page'), _journal),
#
#            #(('year', 'author', 'double_quotes', 'italics', 'paren', 'date', 'url', 'url::page'), _journal|_dq_title|_italics_journal|_paren_publisher|_urlpage),
#            (('year', 'author', 'italics', 'date'), _journal|_italics_journal),
#            (('year', 'author', 'italics', 'paren::italics', 'paren::date', 'url'), _journal|_skip_paren_unhandled|_paren_italics_journal|_paren_date),
#            (('year', 'author', 'italics', 'url', 'url::date'), _journal|_italics_journal|_url_date_date),
#
#            (('year', 'italics', 'paren::volumes', 'paren::page'), _journal|_paren_volumes|_paren_page),
#            (('year', 'italics', 'paren::volume', 'paren::issues', 'paren::page'), _journal|_paren_volume|_paren_issues|_paren_page),
#            (('year', 'italics', 'paren::issues', 'paren::page'), _journal|_paren_issues|_paren_page),
#
#            (('year', 'italics', 'date'), _journal),
#
#            (('year', 'italics', 'volumes', 'page'), _journal),
#            (('year', 'italics', 'volumes', 'url', 'url::page'), _journal|_url_page_page),
#            (('year', 'italics', 'volume', 'page'), _journal),
#
#            (('year', 'link', 'volume', 'page'), _journal|_link_journal),
#
#            (('year', 'month', 'italics', 'page'), _journal),
##        ],


    ]


    @classmethod
    def get_all_combinations(cls, pattern):

        bool_idx = None
        bool_value = None
        for idx, item in enumerate(pattern):
            if item.startswith("?"):
                bool_idx = idx
                bool_value = item[1:]
                break

        if bool_idx is None:
            yield pattern
            return

        header = list(pattern)[:bool_idx] if bool_idx else []

        if bool_idx == len(pattern)-1:
            yield header + [bool_value]
            yield header
            return

        for tail in cls.get_all_combinations(pattern[bool_idx+1:]):
            yield header + [bool_value] + tail
            yield header + tail

    def _init_fingerprints(self):
        return
        self._fingerprints = {}

        for fingerprint_pattern, transformer in self._all_handlers:
            if "_handler" not in transformer:
                print("ERROR", fingerprint_pattern)
#            handler = transformer["_handler"]
#            t_h = (transformer, handler)
            for fingerprint in self.get_all_combinations(list(fingerprint_pattern)):
                fingerprint = tuple(fingerprint)
                if fingerprint in self._fingerprints:
                    print("duplicated fingeprint", fingerprint)
                    if self._fingerprints[fingerprint] != transformer:
                        raise ValueError("Fingerprint has multiple handlers", fingerprint, fingerprint_pattern)
                self._fingerprints[fingerprint] = transformer

    def add_parsed(self, parsed, key, values):

        counter = ""
        if not any(key.endswith(x) for x in ["separator", "unhandled"]):
            for existing_key, _ in reversed(parsed):
                if existing_key.startswith(key) and (len(existing_key) == len(key) or existing_key[len(key)].isdigit()):
                    counter = str(int("0" + existing_key[len(key):])+1)
                    if counter == "1":
                        counter = "2"
                    break

        parsed.append((key+counter, values))



    def run_function(self, function, text):
        res = function(text)
        if not res:
            return

        res = list(res)

        new_text = res.pop()
        if new_text == text:
            raise ValueError("Returned value, but didn't change text", name, res, text)
            return

        return res, new_text


    def parse(self, parsed, name, function, text):
        res = self.run_function(function, text)
        if not res:
            return text
        res, new_text = res

        self.add_parsed(parsed, name, res)
        return new_text

    def parse_names(self, parsed, function, text):
        res = self.run_function(function, text)
        if not res:
            return text
        res, new_text = res

        names = res[0]
        for name, values in names.items():
            self.add_parsed(parsed, name, values)

        return new_text

    def parse_number(self, parsed, function, text):
        res = self.run_function(function, text)
        if not res:
            return text
        res, new_text = res

        number_type, *values = res
        if len(values) > 1:
            number_type = number_type + "s"
            values = ["".join(values)]

        self.add_parsed(parsed, number_type, values)

        return new_text

    def parse_with_subdata(self, parsed, label, function, text):
        res = self.run_function(function, text)
        if not res:
            return text
        res, new_text = res

        # Temporary - don't parse subdata for usenet stuff
#        if "{{monospace" in text and "Usenet" in text:
#            self.add_parsed(parsed, label, res)
#            return new_text

        sub_text, *values = res
        if values:
            if label == "url":
                self.add_parsed(parsed, label, values)
            else:
                raise ValueError("unhandled multi-value sub item")

        if not sub_text:
            return new_text

        sub_items = self.parse_text(sub_text, parse_names=False)
        print("SUB ITEMS", [label, sub_text, sub_items])
        # If everything inside the sub item is just text, ignore it
        #if re.search(r"\[(//|http)", sub_text) \

        all_types = { k for k, *vs in sub_items if k != "separator" }
        if all_types == {"unhandled"} or all_types == {"unhandled", "journal"} or \
            (len(all_types)>1 and not all_types-{"brackets", "unhandled", "separator", "italics", "parenthesis", "bold", "year", "paren"}):
            print("CONSOLIDATING", label, all_types, sub_text)
            if label == "url":
                self.add_parsed(parsed, "url::text", [sub_text])
            else:
                self.add_parsed(parsed, label, [sub_text])
            return new_text

        for sub_item in sub_items:
            sub_label, sub_values = sub_item
            self.add_parsed(parsed, f"{label}::{sub_label}", sub_values)

        return new_text


    def do_cleanup(self, parsed, text, no_recursion=False):
        if not parsed:
            return text

        # Merge any multiple "unhandled" sections
        # UN1, UN2 = UN1_UN2
        # UN1, SEP1, UN2 = UN1_SEP1_UN2
        prev_type = parsed[-1][0]
        if prev_type == "unhandled":
            if len(parsed) > 2 and parsed[-3][0] == "unhandled" and parsed[-2][0] == "separator":
                parsed[-3:] = [("unhandled", ["".join(v[0] for k,v in parsed[-3:])])]
            elif len(parsed) > 1 and parsed[-2][0] == "unhandled":
                parsed[-2:] = [("unhandled", ["".join(v[0] for k,v in parsed[-2:])])]


        # Split the separator before processing the remaining text
        separator, new_text = self._split_leading_separators(text)
        parsed2 = []

        # Cleanup to run after the year has been parsed
        if len(parsed) == 1 and prev_type in ("date", "year"):
            res = self.get_leading_newsgroup_author(new_text)
            if res:
                username, new_text = res
                self.add_parsed(parsed2, "author", [username])

        # Add the separator to the stack
        if separator:
            self.add_parsed(parsed, "separator", [separator])

        # Add any newly-parsed values to the stack
        parsed += parsed2

        # Final cleanup
        if text == "":
            replacements = []

            for idx, kv in enumerate(parsed):
                label, values = kv
                if label == "unhandled":
                    # convert unhandled<'in'> to separator
                    if values[0].lower() in ["in", "as", "in the", "on", "by", "for", "and", "of"]:
                        parsed[idx] = ("separator", values)
                    elif not no_recursion:
                        # Check if the "unhandled" text matches an allow-listed journal, publisher, etc
                        new_items = self.parse_text(values[0], parse_names=True, parse_unlabeled_names=False, _recursive=True)
                        new_good_items = [ (k,vs) for k, vs in new_items if k != "separator" ]
                        if len(new_good_items) == 1 and new_good_items[0][0] != "unhandled":
                            replacements.append((idx, new_items))

            for idx, new_values in reversed(replacements):
                parsed[idx:idx+1] = new_values


        return new_text


    def parse_text(self, text, parse_names=True, parse_unlabeled_names=True, _recursive=False):

        orig_text = text

        parsed = []

        prev_text = ""
        while text and text != prev_text:
            prev_text = text

            text = self.do_cleanup(parsed, text)

            for label, function in [
                ("date", self.get_leading_date),
                ("year", self.get_leading_year),   # process "year" before "bold"
            ]:
                text = self.parse(parsed, label, function, text)
                if text != prev_text:
                    break
            if text != prev_text:
                continue

            # Get names before months so that May Davies Martenet doesn't match as "May", "Davies Martenet"

            # TODO: get_author, similar to get_publisher that reads allow-listed author names that would otherwise be unparsable
            if parse_names and parse_unlabeled_names:
                text = self.parse_names(parsed, self.get_leading_names, text)
                if text != prev_text:
                    parse_unlabeled_names=False
                    continue


            for label, function in [
                ("month_day", self.get_leading_month_day),
                ("month", self.get_leading_month),
#                ("season", self.get_leading_season),
                ("newsgroup", self.get_leading_newsgroup),
            ]:
                text = self.parse(parsed, label, function, text)
                if text != prev_text:
                    break
            if text != prev_text:
                continue

            for label, function in [
                ("italics", self.get_leading_italics),
                ("bold", self.get_leading_bold),
                ("double_quotes", self.get_leading_double_quotes),
                ("fancy_quote", self.get_leading_fancy_quote),
                ("fancy_double_quotes", self.get_leading_fancy_double_quotes),
                ("url", self.get_leading_url),
                ("brackets", self.get_leading_brackets),
                ("paren", self.get_leading_paren),
            ]:
                text = self.parse_with_subdata(parsed, label, function, text)
                if text != prev_text:
                    # Don't look for authors after other items
                    parse_unlabeled_names=False
                    break
            if text != prev_text:
                continue

            if parse_names:
                for label, function in [
                    ("location", self.get_leading_location),
                    ("edition", self.get_leading_edition),
                    ("publisher", self.get_leading_publisher),
                ]:
                    text = self.parse(parsed, label, function, text)
                    if text != prev_text:
                        parse_unlabeled_names=False
                        break
                if text != prev_text:
                    continue

            for label, function in [
                ("journal", self.get_leading_journal),
                ("link", self.get_leading_link),
                ("date_retrieved", self.get_leading_date_retrieved),
                ("isbn", self.get_leading_isbn),
                ("oclc", self.get_leading_oclc),
                ("issn", self.get_leading_issn),
            ]:
                text = self.parse(parsed, label, function, text)
                if text != prev_text:
                    break
            if text != prev_text:
                continue

            text = self.parse_number(parsed, self.get_leading_labeled_number, text)
            if text != prev_text:
                continue

            if parse_names:
                text = self.parse_names(parsed, self.get_leading_names_safe, text)
                if text != prev_text:
                    continue

            # TODO: if the previous entry was "Location", slurp text until date or ( or { as "unverified_publisher"

            # Since the parser is about to fail, just slurp everything until the next separator into "unhandled"
            text = self.parse(parsed, "unhandled", self.get_leading_unhandled, text)

        # Run a final cleanup after everything parsed
        text = self.do_cleanup(parsed, text, _recursive)

        # TODO: "unhandled" between "location" and "date" is very likely a publisher
        # TODO: "unhandled" after "location" may be publisher

        if text:
            print(orig_text)
            print(parsed)
            raise ValueError("Unhandled text", orig_text, parsed, text)

        return parsed


    def merge_unhandled(self, parsed):

        merge_keys = []
        buffered_unhandled = []
        for idx, item in enumerate(parsed):
            datatype, data = item

            if datatype == "unhandled":
                buffered_unhandled.append(idx)
                continue

            if buffered_unhandled:
                if datatype == "separator":
                    buffered_unhandled.append(idx)
                    continue

                merge_keys.append(buffered_unhandled)
                buffered_unhandled = []

        if len(buffered_unhandled) > 1:
            merge_keys.append(buffered_unhandled)

   #     if merge_keys:
   #         print("MERGING", merge_keys, parsed)

        for keys in reversed(merge_keys):
            first = keys[0]
            last = keys[-1]
            if parsed[last][0] == "separator":
                last = last-1

            last = last + 1
            assert last > first
            unhandled_text = "".join(v[0] for k,v in parsed[first:last]).strip()
            parsed[first:last] = [("unhandled", [unhandled_text])]



    def get_fingerprint(self, parsed, condense_unhandled=False):
        fingerprint = []
        for label, data in parsed:

            if label.endswith("unhandled"):
                if condense_unhandled:
                    fingerprint.append(f"{label}<*>")
                else:
                    fingerprint.append(f"{label}<{data[0]}>")

            elif label.endswith("separator"):
                continue
            else:
                fingerprint.append(label)

        return tuple(fingerprint)


    def can_ignore_unhandled(self, unhandled_text):
        unhandled_text = unhandled_text.strip("/#:;-.–,— ")
        return not unhandled_text


    def get_passage(self, passage_lines, section=None):
        lines = []
        converted_template = False
        for line in passage_lines:

            passage = line.lstrip("#*: ")
            if "|" in passage:

                m = re.match(r"^{{(?:quote|ux)\|[^|]*\|(.*)}}\s*$", passage)
                if m:
                    passage = m.group(1)
                    if passage.count("|") == 1 and "|t=" not in passage and "|translation=" not in passage:
                        passage = passage.replace("|", "|t=")

                    passage = passage.replace("|translation=", "|t=")

                    if converted_template:
                        if section:
                            self.warn("passage_has_multi_templates", section)
                        return
                    converted_template = True

            lines.append(passage)

        passage = "<br>".join(lines)

        passage, _, translation = passage.partition("|t=")

        allowed_pipes = passage.count("{{...|") + passage.count("{{w|")
        if passage.count("|") != allowed_pipes:
            if section:
                self.warn("pipe_in_passage", section, passage)
            return

        return passage, translation


    def get_translation(self, translation_lines):
        return "<br>".join(l.lstrip("#*: ") for l in translation_lines)



    r"""

    _journal_sites = ["telegraph.co.uk", "guardian.co.uk", "washingtonpost.com", "independent.co.uk", "nytimes.com", "time.com"]
    _journal_url_regex = "[/.]" + "|".join(x.replace(".", r"\.") for x in _journal_sites) + "/"

    def get_template_source(self, params):

        if any(x in params for x in ["isbn", "oclc", "issn"]):
            return "book"

        if any(x in params for x in ["season", "episode"]):
            return "av"

        if any(x in params for x in ["issue", "number", "date", "month"]):
            if "publisher" in params:
                print("BAD JOURNAL PARAMS - has publisher", params)
                return None
            return "journal"

        urls = []
        for url_param in ["url", "chapterurl", "pageurl"]:
            url = params.get(url_param)
            if url:
                urls.append(url)

        if urls and any("books.google." in url for url in urls):
            return "book"

        if urls and any(re.search("google.[^/]*/books/", url) for url in urls):
            return "book"

        if urls and any(re.search(self._journal_url_regex, url) for url in urls):
            return "journal"

        return "text"

    _param_adjustments = {
        "journal": [
            # Old : New
            {
            "title": "journal",
#            "issue": "start_date",
            },
            {
            "chapter": "title",
            "chapterurl": "titleurl",
            "url": "titleurl",
            "number": "issue",
            }
        ]
    }
"""

    def convert_quotes(self, section, title):

        lang_id = ALL_LANGS.get(section._topmost.title)
        if not lang_id:
            return

        # Anything that starts '''YEAR''' could be a quote
        pattern = r"""([#:*]+)\s*(?P<quote>'''(1\d|20)\d{2}'''.*)$"""

        changed = False
        to_remove = []
        for idx, line in enumerate(section._lines):
            m = re.match(pattern, line)
            if not m:
                continue

            start = m.group(1)

            params = self.get_params(m.group('quote'))
            if not params:
                self.warn("unparsable_line", section, line)
                continue

            passage_lines = []
            translation_lines = []

            offset = 1
            failed = False
            while idx+offset < len(section._lines) and section._lines[idx+offset].startswith(start + ":"):

                if re.match(re.escape(start) + ":[^:]", section._lines[idx+offset]):
                    if translation_lines and passage_lines:
                        self.warn("multi_passage", section, section._lines[idx+offset])
                        failed = True
                        break
                    passage_lines.append(section._lines[idx+offset])

                elif re.match(re.escape(start) + "::[^:]", section._lines[idx+offset]):
                    if not passage_lines:
                        self.warn("translation_before_passage", section, section._lines[idx+offset])
                        failed = True
                        break
                    translation_lines.append(section._lines[idx+offset])

                else:
                    self.warn("unhandled_following_line", section, section._lines[idx+offset])
                    failed = True
                    break

                offset += 1

            if failed:
                continue

            new_lines = self.get_new_lines(start, section, params, passage_lines, translation_lines, idx)
            if not new_lines:
                continue

            for x, line in enumerate(new_lines):
                section._lines[idx+x] = line

            used = len(new_lines)
            for to_remove_idx in range(idx+used, idx+offset):
                to_remove.append(to_remove_idx)

            changed = True

        for idx in reversed(to_remove):
            del section._lines[idx]

        return changed

    def get_new_lines(self, start, section, params, passage_lines, translation_lines, idx):

        lang_id = ALL_LANGS.get(section._topmost.title)

        res = self.get_passage(passage_lines, section)
        if not res:
            return
        passage, translation1 = res

        translation2 = self.get_translation(translation_lines)
        if translation1 and translation2:
            self.warn("multi_translations", section, translation1 + " ----> " + translation2)
            return
        translation = translation1 if translation1 else translation2

        if "|" in translation:
            self.warn("pipe_in_translation", section, translation)
            return

        if translation and not passage:
            self.warn("translation_without_passage", section, section.path)
            return

        if lang_id == "en" and translation:
            self.warn("english_with_translation", section, translation)
            return

        prefix = "cite" if section.title in ["References", "Further reading", "Etymology"] else "quote"
        source = params.pop("_source")
        template = prefix + "-" + source

        page = list(section.lineage)[-1]
        print("PAGE", page)
        if not self.is_valid_template(template, params):
            return

        new_lines = [ start + " {{" + template + "|" + lang_id + "|" + "|".join([f"{k}={v}" for k,v in params.items()]) ]
        if translation2:
            new_lines.append("|passage=" + passage)
            new_lines.append("|translation=" + translation + "}}")
        elif translation1:
            new_lines.append("|passage=" + passage + "|t=" + translation + "}}")
        elif passage:
            new_lines.append("|passage=" + passage + "}}")
        else:
            new_lines[0] += "}}"

        return new_lines


    def is_valid_template(self, template, params):

        nests = (("[[", "]]"), ("{{", "}}"), ("[http", "]")) #, (start, stop))

        for k in ["url", "pageurl", "titleurl", "chapterurl", "title", "author"]:
            v = params.get(k, "").strip()

            if v.startswith("|") or v.endswith("|") \
                    or len(list(nest_aware_resplit("[|]", v, nests))) > 1:
                # TODO: self.warn()
                self.dprint("pipe_in_value", k, v, params)
                return False

        if template in ["quote-newsgroup", "cite-newsgroup"]:
            if all(x in params for x in ["author", "newsgroup"]):
                return True

            # Sanity check for usernames
            username = params["author"]
            if "|" in username or "=" in username:
                return False

            title = params["title"]
            if "|" in title or "=" in title:
                return False

            self.dprint("incomplete newsgroup entry")


        title = params.get("title")
        if title and not self.is_valid_title(title):
            return False

        if template in ["quote-book", "cite-book"]:
            if all(x in params for x in ["year", "title"]):
                return True

        if template in ["quote-text", "cite-text"]:
            if all(x in params for x in ["year"]) and sum(1 for x in ["author", "title"] if x in params):
                return True

        elif template in ["quote-journal", "cite-journal"]:
            if all(x in params for x in ["journal"]) and sum(1 for x in ["year", "date"] if x in params)==1:
                return True
            self.dprint("incomplete journal entry")


        elif template in ["quote-web", "cite-web"]:
            if all(x in params for x in ["site", "url"]):
                return True
            self.dprint("incomplete web entry")

        #raise ValueError("invalid template", template, params)
        return False


    def process(self, text, title, summary=None, options=None):
        # This function runs in two modes: fix and report
        #
        # When summary is None, this function runs in 'report' mode and
        # returns [(code, page, details)] for each fix or warning
        #
        # When run using wikifix, summary is not null and the function
        # runs in 'fix' mode.
        # summary will be appended with a description of any changes made
        # and the function will return the modified page text

        self._log = []
        self._summary = summary

        # skip edits on pages with lua memory errors
        ignore_pages = [ "is", "I", "a", "de" ]
        if title in ignore_pages:
            return [] if summary is None else text

        entry = sectionparser.parse(text, title)
        if not entry:
            return [] if summary is None else text

        for section in entry.ifilter_sections():
            if self.convert_quotes(section, title):
                self.fix("bare_quote", section, "converted bare quote to template")


        return self._log if summary is None else str(entry)



    def old_parse_details(text):
        year, text = self.get_year(text)
        if not year:
            self.dprint("no year")
            return
        save("year", year)

        month, day, text = self.get_leading_month_day(text)
        if month and day:
            del details["year"]
            save("date",f"{month} {day} {year}")
        else:
            month, text = self.get_month(text)
            if month:
                save("month", month)

        issue, text = self.get_leading_issue(text)
        if issue:
            save("issue", issue)

        names, text = self.get_leading_classified_names(text)
        add_names(names)

        chapter_title, text = self.get_leading_chapter_title(text)
        title, text = self.get_leading_title(text)
        subtitle, text = self.get_leading_title(text)
        if subtitle:
            return


        if title and subtitle:
            title = f"{title}: {subtitle}"

        # TODO: If title, strip any leading "in:" from the text
        if chapter_title:
            text = re.sub("^[-.,:; ]+in[-.,:; ]+", "", text)


        # Maybe not chapter?
        if not chapter_title:
            chapter_title, text = self.get_leading_chapter_title(text)
            if chapter_title:
                save("chapter", chapter_title.rstrip(", "))

        # TODO: read next item repeatedly, trying title, chapter_title, names until no more changes
        # then look at formats and guess values


        if not title:
            if chapter_title and "author2" not in details: # Multiple authors is a sign that the publisher or other details may be included in authors
                title = chapter_title
                chapter_title = None
            else:
                self.dprint("no title", orig_text)
                return

        if chapter_title:
            save("chapter", chapter_title.rstrip(", "))
            chapter_url, chapter_title, _ = self.get_url(chapter_title)
            if chapter_url:
                if _.strip():
                    self.dprint("chapter_url_posttext", _)
                    return
                save("chapterurl", chapter_url)
                save("chapter", chapter_title.strip(", "), True)

        save("title", title.strip(", "))
        title_url, title, _ = self.get_url(title)
        if title_url:
            if _.strip():
                self.dprint("title_url_posttext", _)
                return
            save("url", title_url)
            save("title", title.strip(", "), True)


        names, text = self.get_leading_classified_names(text)
        add_names(names)




        translator, text = self.get_translator(text)
        if translator:
            save("translator", translator)

        editor, text = self.get_editor(text)
        if editor:
            save("editor", editor)



        # url may contain the text like 'page 123' or 'chapter 3', so it needs to be extracted first
        url, _, text = self.get_url(text, True)

        gbooks, text = self.get_gbooks(text)

        # get pages before page because pp. and p. both match  pp. 12-14
        pages, text = self.get_pages(text)
        page, text = self.get_page(text)
        chapter, text = self.get_chapter(text)

        lines, text = self.get_lines(text)
        if lines:
            save("lines", lines)

        line, text = self.get_line(text)
        if line:
            save("line", line)

        volume, text = self.get_volume(text)
        if volume:
            save("volume", volume)

        issue, text = self.get_issue(text)
        if issue:
            save("issue", issue)

        number, text = self.get_number(text)
        if number:
            save("number", number)

        season, text = self.get_season(text)
        episode, text = self.get_episode(text)
        if not season and not episode:
            season, episode, text = self.get_season_episode(text)

        if season:
            save("season", season)

        if episode:
            save("episode", episode)

        edition, text = self.get_edition(text)
        if edition:
            if edition.isnumeric() and len(edition) == 4:
                save("year_published", edition)
            else:
                save("edition", edition)

        retrieved, text = self.get_date_retrieved(text)
        if retrieved:
            save("accessdate", retrieved)

        if month:
            _year, _month, _day = None, None, None
        else:
            _year, _month, _day, text = self.get_date(text)
        if _month: # Month will always be valid if get_date() returns anything
            if _year and int(_year) < int(year):
                self.dprint("ERROR: published year before citation year")
                return

            else:
                if not _year:
                    _year = year
                elif int(_year) != int(year):
                    # TODO: currently a secondary date with a month is used to indicate
                    # that it's a journal, but there's no way to included published_date in journals
                    # This only happens in a handful of cases
                    self.dprint("ERROR: published year before citation year")
                    return

                if _day:
                    if _day < 0:
                        date = f"{_day*-1} {_month} {_year}"
                    else:
                        date = f"{_month} {_day} {_year}"

                    # rename year to date to preserve dictionary order
                    if "year" in details:
                        details = {"date" if k == "year" else k:v for k,v in details.items()}
                    save("date", date, True)

                else:
                    save("month", _month)

        if gbooks:
            page = gbooks

        if url:
            if "books.google" in url or "google.com/books" in url:
                if page or pages:
                    save("pageurl", url)
                elif chapter:
                    save("chapterurl", url)
                else:
                    save("url", url)
            else:
                save("url", url)

        if sum(x in details for x in ["url", "chapterurl", "pageurl"]) > 1:
            #print("multiple_urls", orig_text)
            self.dprint("multiple_urls", text)
            return

        if chapter:
            if "chapter" in details:
                self.dprint("multiple chapter declarations", chapter, details)
                return
            save("chapter", chapter)

        if page:
            save("page", page)

        if pages:
            save("pages", pages)

        # Parse publisher after removing page, chapter, and volume info

        publisher, year_published, location, text = self.get_publisher(text)
        if publisher is None:
            return

        if location:
            save("location", location)

        if publisher:
            save("publisher", publisher)

        if year_published and year_published != year:
            save("year_published", year_published)



        isbn, text = self.get_isbn(text)
        if isbn:
            for count, isbn in enumerate(isbn, 1):
                key = f"isbn{count}" if count > 1 else "isbn"
                save(key, isbn)

        oclc, text = self.get_oclc(text)
        if oclc:
            save("oclc", oclc)

        issn, text = self.get_issn(text)
        if issn:
            save("issn", issn)

#        if not isbn and not oclc and not issn:
#            print("NO ISBN, OCLC, or ISSN FOUND")
#            print(details)
#            print(text)
#            return


        text = re.sub(r"(\(novel\)|&nbsp|Google online preview|Google [Pp]review|Google snippet view|online|preview|Google search result|unknown page|unpaged|unnumbered page(s)?|online edition|unmarked page|no page number|page n/a|Google books view|Google [Bb]ooks|Project Gutenberg transcription)", "", text)
        text = text.strip('#*:;, ()".')
        if page or pages:
            text = re.sub(r"([Pp]age(s)?|pp\.|p\.|pg\.)", "", text)


        if "_error" in details:
            for err in details["_error"]:
                self.dprint(err)
            return


        if text:
            self.dprint("unparsed text:", text, details)
            self.dprint(orig_text)
            self.dprint("")
            return

        return details

    # Order longest to shortest in order to match "New York, NY" before "New York"
    with open("allowed_publishers") as infile:
        _allowed_publishers = {line.strip() for line in infile if line.strip()}

    _allowed_publishers = sorted(_allowed_publishers, key=lambda x: (len(x)*-1, x))
    _allowed_publishers_regex = "(" + "|".join(map(re.escape, _allowed_publishers)) + r")(?=\b|$|[-.,;:])"

    with open("allowed_locations") as infile:
        _allowed_locations = {line.strip() for line in infile if line.strip()}

    # Order longest to shortest in order to match "New York, NY" before "New York"
    _allowed_locations = sorted(_allowed_locations, key=lambda x: (len(x)*-1, x))
    _locations_regex = "(" + "|".join(map(re.escape, _allowed_locations)) + r")(?=$|\s*[-.;:])"


    with open("allowed_journals") as infile:
        _allowed_journals = {line.strip() for line in infile if line.strip()}

    # Order longest to shortest in order to match "New York, NY" before "New York"
    _allowed_journals = sorted(_allowed_journals, key=lambda x: (len(x)*-1, x))
    _journals_regex = "(" + "|".join(map(re.escape, _allowed_journals)) + r""")(?=$|\s*[-.,;:'"(])"""

    # curl ftp://ftp.isc.org/pub/usenet/CONFIG/active | cut -d '.' -f 1 | uniq > allowed_newsgroups
    with open("allowed_newsgroups") as infile:
        _allowed_newsgroups = {line.strip() for line in infile if line.strip()}

    # Order longest to shortest in order to match "New York, NY" before "New York"
    _allowed_newsgroups = sorted(_allowed_newsgroups, key=lambda x: (len(x)*-1, x))

    _allowed_newsgroups_regex = r"""(?x)
            (discussion[ ])?
            (on[ ]|in[ ])?
            (Internet[ ])?
            (newsgroup[ ])?
            (''|{{monospace\|)?
            \s*
            (?P<usenet>(""" \
                + "|".join(_allowed_newsgroups) + \
            r""")\.
                ([\d\w_\-.]+)
            )
            \s*
            (}}|'')?
            ([ :,-;]*'*Usenet'*)?
            (?P<post>.*)
        """
