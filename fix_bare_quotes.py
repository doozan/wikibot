import enwiktionary_sectionparser as sectionparser
import re
import sys

from autodooz.sections import ALL_LANGS
from collections import namedtuple
from enwiktionary_parser.utils import nest_aware_split, nest_aware_resplit
from .quotes.name_labeler import NameLabeler
from .quotes.names import *

NESTS = (("[", "]"), ("{{", "}}"))

Parsed = namedtuple("Parsed", ["type", "values", "orig"])

LINK = namedtuple("LINK", [ "target", "text", "orig" ])

class QuoteFixer():

    ignore_unhandled = {
            '"', "", "(", ")", ',',
            "in", "as", "in the", "on", "for", "and", "of",
            "from",
            # "by", "article in", "magazine", "p", "pp", "page",
    }

    @staticmethod
    def make_pre_regex(prefixes):
        # Sort "bigger" before "big"
        prefixes = sorted(prefixes, key=lambda x: x+'🂲')
        return "((" + "|".join(prefixes) + r")\s+)*".lower()

    @staticmethod
    def make_post_regex(postfixes):
        # Sort "bigger" before "big"
        postfixes = sorted(postfixes, key=lambda x: x+'🂲')
        return "([&., ]+(" + "|".join(postfixes) +")[.]?)*".lower()

    journal_prefix_regex = make_pre_regex(journal_prefixes|common_prefixes|ignorable_affixes)
    journal_postfix_regex = make_post_regex(journal_postfixes|common_postfixes|ignorable_affixes)

    publisher_prefix_regex = make_pre_regex(publisher_prefixes|common_prefixes|ignorable_affixes)
    publisher_postfix_regex = make_post_regex(publisher_postfixes|common_postfixes|ignorable_affixes)

    def dprint(self, *args, **kwargs):
        if self.debug:
            print(args, kwargs, file=sys.stderr)

    def __init__(self, debug=False, all_locations=None, all_journals=None, all_publishers=None, aggressive=False):
        self._summary = None
        self._log = []
        self.debug=debug
        self.labeler = NameLabeler("quotes/author.allowed")

        # Proposed changes will be manually, verified, be aggressive
        self.aggressive=aggressive

#        disallowed = self.disallowed_items | pub_prefixes | journal_prefixes | self._number_aliases.keys() | pub_postfixes | journal_postfixes
        if not all_locations:
            all_locations = self.load_items("quotes/location.allowed")
#        disallowed |= all_locations
        if not all_publishers:
            all_publishers = self.load_items("quotes/publisher.allowed") #, pub_prefixes, pub_postfixes, disallowed)
            self.all_publishers = all_publishers
        if not all_journals:
            all_journals = self.load_items("quotes/journal.allowed") #, journal_prefixes, journal_postfixes, disallowed)

#        all_locations.remove('9')

#        overlap = all_publishers & all_journals
#        if overlap:
#            print("OVERLAPPING ITEMS, add to disallowed")
#            print(sorted(overlap))
#            exit()

        self._allowed_locations_regex = self.make_regex(all_locations, "", r'(?=$|\s+\d|\s*?[-.;:,])')
        #self._allowed_publishers_regex = self.make_regex(all_publishers, r"\s*(" + self.publisher_prefix_regex, self.publisher_postfix_regex + r"""(?=$|\s+\d|\s+and\s+|\s*[&-.,;:'"(]))+""")
        self._allowed_publishers_regex = self.make_regex(all_publishers, self.publisher_prefix_regex, self.publisher_postfix_regex + r"""(?=$|\s+(edition(s)?|ed\.|\d)|\s*?[-.,;:'"\[{(])""")
        self._allowed_journals_regex = self.make_regex(all_journals, self.journal_prefix_regex, self.journal_postfix_regex + r"""(?=$|\s+\d|\s*?[-.,;:'"\[{(])""")


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

    _leading_year_pattern = r"""(?x)
            (year\s*)?
            (?P<years>
            (\s|'''|\(|\[)*           # ''' or ( or [
            (?P<year1>(1\d|20)\d{2})
            (
              (\s*(?P<separator>or|,|&|and|-|–|to|{{ndash}})+\s*)
              (?P<year2>(1\d|20)\d{2})
            )?
            (\s|(:)?'''|\)|\])*           # ''' or ) or ]
            )
            (?!-) # Not followed by - (avoids matching YYYY-MM-DD)
            (?P<post>.*)$         # trailing text
        """
    _leading_year_regex = re.compile(_leading_year_pattern, re.IGNORECASE)
    def get_leading_year(self, text):
        m = re.match(self._leading_year_regex, text)
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
                if group.endswith(":"):
                    group = group[:-1]

            if group.startswith("(") and group.endswith(")"):
                group = group[1:-1].strip()

            if group.startswith("[") and group.endswith("]"):
                group = group[1:-1].strip()

        if not (group[0].isnumeric() and group[-1].isnumeric()):
            return

        # Strip {{CE}} after year
        post_text = self._strip_leading_separators(post_text)
        post_text = re.sub(r"^({{(CE|C\.E\.)[^}]*}}|CE[:,])\s*", "", post_text)

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
            separator = " & "
        elif separator in ["-", "–", "to", "{{ndash}}"]:
            separator = "-"
        else:
            raise ValueError("unhandled separator", [separator])

        return [val1, separator, val2]


    classifiers = { "magazine", "song", "tv series" }
    classifiers_pattern = "|".join(classifiers)
    connector_words_pattern = r"(the|a|an|on|in|to)\b"
    _leading_classifier_pattern = fr"""(?x)
         (?P<classifier>
             (\s*({connector_words_pattern})*\s)*
             ({classifiers_pattern})+
             (\s*({connector_words_pattern}))*
        )+
        (?P<post>.*)
    """
    _leading_classifier_regex = re.compile(_leading_classifier_pattern)

    # Detect text that classifies the quote (magazine, song, tv series)
    def get_leading_classifier(self, text):
        m = re.match(self._leading_classifier_regex, text)
        if not m:
            return

        match = m.group(1)
        for c in ["magazine", "song", "tv series"]:
            if c in match:
                return {c: match}, m.group("post")

    _leading_section_pattern = fr"""(?x)
        (?P<classifer>
            [.,:;\-()\[\]'" ]+
            |{number_pattern}\b
            |{number_words_pattern}\b
            |{section_labels_pattern}\b
            |(the|a|an|on|in|to|ad)\b
        )+
        $
    """
    _leading_section_regex = re.compile(_leading_section_pattern, re.IGNORECASE)

    def get_leading_section(self, text):
        # Section here refers to the section= parameter of the quote templates, which is used
        # instead of a combination labeled numbers like page= volume= column= to describe
        # where the text is located. This allows for freeform entries like "Act XI (footnote)"

        orig_text = text
        text = self.labeler.links_to_text(text)
        text = text.replace('{{gbooks.*?}}', " ")

        # If all of the remaining text consists of text locations and numbers, slurp it up
        if re.match(self._leading_section_regex, text):
            return orig_text.rstrip(",.:;- "), ""


    _leading_unhandled_pattern = r"""(?x)
            (?P<text>
              \s+
              |([^\d\w\s])\2*    # or, any non-alphanumeric+space character and any repetition
              |(?:(?!.*?[.]{2})[a-zA-Z0-9](?:[a-zA-Z0-9.+!%-]{1,64}|)|\"[a-zA-Z0-9.+!% -]{1,64}\")@[a-zA-Z0-9][a-zA-Z0-9.-]+(.[a-z]{2,}|.[0-9]{1,})
              |[\d\w]+          # alphanumeric
            )
            (?P<post>.*)$    # trailing text
        """
              #|[a-z0-9]+[\.'\-a-z0-9_]*[a-z0-9]+@(gmail|googlemail)\.com
              #|([-!#-'*+/-9=?A-Z^-~]+(\.[-!#-'*+/-9=?A-Z^-~]+)*|\"([]!#-[^-~ \t]|(\\[\t -~]))+\")@([-!#-'*+/-9=?A-Z^-~]+(\.[-!#-'*+/-9=?A-Z^-~]+)*|\[[\t -Z^-~]*])
              # email addresses https://stackoverflow.com/questions/5861332/pattern-matching-email-address-using-regular-expressions
              #
    _leading_unhandled_regex = re.compile(_leading_unhandled_pattern)

    def get_leading_unhandled(self, text):

        # if starts with { or [, slurp until matching brace
        if text.startswith("{{"):
            end = text.find("}}")
            if end > 0:
                print("MATCH", text, end)
                return text[:end+2], text[end+2:]

        if text.startswith("[["):
            end = text.find("]]")
            if end > 0:
                return text[:end+2], text[end+2:]

        if text.startswith("["):
            end = text.find("]")
            if end > 0:
                return text[:end+1], text[end+1:]

        m = re.match(self._leading_unhandled_regex, text)
        if not m:
            return

        return m.group('text'), m.group('post')


    def get_leading_newsgroup_author(self, text):

        if "{{monospace" in text and "Usenet" in text:
            text = self._strip_leading_separators(text)

            if text.startswith('"'):
                username, new_text = self.get_leading_start_stop('"', '"', text)

            else:
                m = re.match("^([^,'“]+)(.*)$", text)
                if not m:
                    return
                username = m.group(1)
                new_text = m.group(2)

            username = re.sub(r"([,. ]*\(?username\)?)", "", username)
            new_text = re.sub(r"^([,. ]*\(?username\)?)", "", new_text)

            return username, new_text

            # Split link into title?
            #[http://groups.google.com/group/alt.mountain-bike/msg/88b9b6a7d4ef1e37?q=Daygo Re: Intro & Querry About Front Shocks]



    def get_leading_names_safe(self, text, parsable={"author", "publisher", "translator", "editor"}):
        return self.get_leading_names(text, parsable)

    def get_leading_names(self, text, parsable={"unlabeled", "author", "publisher", "translator", "editor"}):

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

        if "editor" in parsable:
            new_text = re.sub(r"^(ed\.|eds\.|edited by)\s*", "", text, flags=re.IGNORECASE)
            if new_text != text:
                if new_text.endswith(")") and "(" not in new_text:
                    new_text = new_text.rstrip(")")
                return self._get_leading_classified_names(new_text, ">editor")

        if "translator" in parsable:
            new_text = re.sub(r"^(translation by|translated by|trans|tr\. by)\s+", "", text, flags=re.IGNORECASE)
            if new_text != text:
                return self._get_leading_classified_names(new_text, ">translator")

        if "author" in parsable:
            new_text = re.sub(r"^by\s+", "", text)
            if new_text != text:
                return self._get_leading_classified_names(new_text, ">author")

        if "unlabeled" in parsable:
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

        # NOTE: Do NOT use capturing groups here
            #r"(?<![A-Z])(?<!Dr|Ms|Mr|Sr|et)(?<!Miss)(?<!Mrs|Sra|Sgt|Pvt|etc)\.\s",   # Break on ". " unless it's like J.D. or Mr.
        split_items = [
            r"\s-",                 # break on " -" but not Smith-Jones
            r"\bin\b",              # likewise, break on "in" but not "Penguin"
            r"\bas\b",              # likewise, break on "as" but not "asthmas"
            r"\bquoted\b",          # break on "quoted"
            r"\[http",              # always break on links
            r"\[//",                # always break on links
            r"''",                  # and double quotes
            r'["“‘—•·–:]',          # And quotes and colon and dots and fancy dashes
            r"$",
        ]
        pattern = "(" + "|".join(split_items) + ")"

        nests = (("[", "]"), ("{{", "}}")) #, (start, stop))
        name_text, _ = next(nest_aware_resplit(pattern, text, nests))
        if not name_text:
            return

        name_text = name_text.rstrip(",:;([{ ")

        if name_text.endswith(".") and not name_text.endswith(("Jr.", "Dr.", "Ms.", "Mr.", "Miss.", "Sra.", "Sgt.", "Pvt.")):
            name_text = name_text.rstrip(".")

        # Strip trailing 's
        if name_text.endswith("'s"):
            name_text = name_text[:-2]

        post_text = text[len(name_text):]

        #name_text = self._strip_leading_separators(name_text) # name_text.replace("&#91;", "‘"))

        for start, end in (("(", ")"), ("[", "]"), ("[[", "]]"), ("{{", "}}"), ("{", "}"), ("<", ">")):
            if name_text.count(start) != name_text.count(end):
                print("mismatched bracket count")
                return

        # Check if the remaining text starts with ''et al''
        #alt_m = re.match(r"\s*(''|[;, ]+)et al((ii|\.)''(.)?|[.,])\s*(?P<post>.*)$", m.group('post'))
        appended_text = ""
        if post_text:
            # Match "et al", "et alia" "et alii" plus surrounding formatting
            # Handle trailing ''et al''
            pattern = r"""(?x)^
                [\[;, ]*
                ''                 # must contain ''
                [\[;, ]*
                et[.]?             # et or et.
                \s+
                al(ii|ia|ios|\.)?      # al, al., alii, alia, alios
                [\]., ]*
                ''                 # closing ''
                \]*
                """

            m = re.match(pattern, post_text) #r"[\[;, ]*''[\[;, ]*et\.? al(ii|ia)\.?[\]., ]*''", post_text)
            if m:
                et_al = m.group(0)
                post_text = post_text[len(et_al):]
                appended_text = ", et al"
                name_text = name_text + appended_text

        #print("NAME", [name_text, init_command])
        res = self.classify_names(name_text, init_command)
        if not res:
            return

        classified_names, invalid_text = res
        if not classified_names:
            return

        # FIXME
        # Temporary workaround: don't split "Blah One and Invalid Name" into "Blah One", "and Invalid Name"
        if re.match(r"\s*and\b", invalid_text):
            return

        # Strip any appended text from the returned invalid text before concat with post_text
        if appended_text:
            return classified_names, invalid_text[:-len(appended_text)] + post_text

        if invalid_text:
            return classified_names, invalid_text + post_text
        else:
            if post_text.startswith("'s"):
                post_text = post_text[2:]
            return classified_names, post_text

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

        m = re.match(fr"({q}.+?{q})(.*)$", text)
        if not m:
            return
        return m.group(1)[2:-2], m.group(2)

    def get_leading_bold(self, text):
        # match exactly 3 or 5 single quotes
        q = "(?<!')(?:'{3}|'{5})(?!')"

        m = re.match(fr"({q}.+?{q})(.*)$", text)
        if not m:
            return
        return m.group(1)[3:-3], m.group(2)

    def get_leading_newsgroup(self, text):
        m = re.match(self._allowed_newsgroups_regex, text)
        if not m:
            return

        # make sure the newsgroup isn't a domain name (news.com)
        usenet = m.group('usenet')
        if usenet.endswith(('.net', '.com', '.org')):
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

        if title.startswith("Re:") or title.startswith("Fwd:") or title.startswith("FW:"):
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
        m = re.match(regex, text)
        if not m or not m.group(0):
            return
        return m.group(0), text[len(m.group(0)):]


    location_split_regex = r"\s*([&;,—/–•·\[()]|\band\b)+\s*"

    def get_leading_location(self, text):

        parts = []
        separator = None
        while text:
            res = self.get_leading_regex(self._allowed_locations_regex, text)
            if not res:
                break

            item, text = res
            parts.append(item)

            m = re.match(self.location_split_regex, text)
            if m and m.group(0):
                separator = m.group(0)
                parts.append(separator)
                text = text[len(separator):]
            else:
                separator = None

#            print("LOC", parts, text)

        # Pop the trailing separator
        if separator:
            parts.pop()
            text = separator+text if text else separator

        if not parts:
            return

        location = "".join(parts).strip()

        # avoid "in" vs IN
        if location.islower():
            return

        return location, text

#        pattern = fr"""(?x)
#            (?P<extra>{self._loc_extra_pattern})
#            (?P<post>($|[ ,.;:]|\b).*)
#        """
#        m = re.match(pattern, text, re.IGNORECASE)
#        if m:
#            return item + m.group('extra').replace(".", ""), m.group('post')
#
#        return res

    def get_leading_journal(self, text):

        # No lowercase journals
        if text and text[0].islower():
            return

        return self.get_leading_regex_template(self._allowed_journals_regex, text)

    @staticmethod
    def cleanup_publisher(text):
        return re.sub(r"^(printed|published|publ\.|republished|in )( (in|by|for))?[-;:,.\s]*", "", text)

    def get_leading_publisher(self, text):
        text = self.cleanup_publisher(text)

        res = self.get_leading_regex_template(self._allowed_publishers_regex, text)
        if not res:
            return
        publisher, post_text = res

        # Strip trailing "edition" after "Penguin edition"
        post_text = re.sub(r"^\s+((edition(s)?\b|ed\.))", "", post_text)
        return publisher, post_text


    def get_leading_regex_template(self, regex, text):

        # lowercase starting word is usually a bad sign
        if text and text[0].islower():
            return

        template = None
        if text.startswith("[["):
            template, _ = next(nest_aware_resplit(r"((?<=]]).)", text, NESTS))
            if not template:
                return
        elif text.startswith("{{"):
            template, _ = next(nest_aware_resplit(r"((?<=}}).)", text, NESTS))
            if not template:
                return

        if template:
            template_text = self.labeler.links_to_text(template)

            res = self.get_leading_regex(regex, template_text)
            if not res:
                return
            template_match, extra = res
            # Must match the entire name
            if extra.strip():
                return

            return template, text[len(template):]


        res = self.get_leading_regex(regex, text)
        if not res:
            return

        match, text = res
        if match.endswith(" and") or match.endswith("&"):
            return

        return match, text

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

        if text.startswith("http://") or text.startswith("https://"):
            link, _, post = text.partition(" ")
            link = link.rstrip(".,:;- ")
            link_text = ""
            return link_text, LINK(link, link_text, link), text[len(link):]

        pattern = r"""(?x)
            (?P<orig_link>\[                     # [
                (?P<link>(//|http)[^ ]*)         # url
                \s*
                (?P<link_text>\s*[^\]]*?)?       # link text
            \])                                  # ]
            (?P<post>.*)$            # trailing text
        """

        m = re.match(pattern, text)
        if not m:
            return

        link_text = m.group('link_text').strip() if m.group('link_text') else ""
        return link_text, LINK(m.group('link'), link_text, m.group('orig_link')), m.group('post')

    @staticmethod
    def get_leading_link(text):
        pattern = r"""(?x)
            (?P<link>
                \[\[                         # open brackets [[
                (?P<target>
                    (:)?([sw]|special):      # w:, s:, or Special:
                    [^|\]]*?                 # target
                )
                (\|(?P<link_text>[^\]]*?))?      # Optional text
                \]\]                         # ]]
            )
            (?P<post>.*)$                    # trailing text
        """

        m = re.match(pattern, text, re.IGNORECASE)
        if not m:
            return

        link_text = m.group('link_text').strip() if m.group('link_text') else ""
        return link_text, LINK(m.group('target'), link_text, m.group('link')), m.group('post')

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

    _label_pattern = f"{countable_pattern}(?P<post>.*)$"
    _label_regex = re.compile(_label_pattern)
    def get_leading_countable(self, text):

        # TODO: Temp fix
        if text.startswith("unnumbered page"):
            return "page", "unnumbered", text[len("unnumbered page"):]

        m = re.match(self._label_regex, text)
        if not m:
            return

        if m.group('label').lower() not in label_to_countable_type:
            print("XXXXXX", [text])
#            return
            raise ValueError(text)

        countable = label_to_countable_type[m.group('label').lower()]
        if m.group('num1'):
            num1 = m.group('num1').replace(",", "")
            num2 = m.group('num2').replace(",", "") if m.group('num2') else None

            # Match p1 but not pA1 or pix
            if not num1[0].isnumeric() and not m.group("label_sep"):
                return

            if not self.is_valid_number(num1) or (num2 and not self.is_valid_number(num2)):
                return

            # check that num1 and num2 are roughly the same style, eg 12 and 123 or a2 and a3
            # sloppy, matches xvii and 991a and "page 11, 12 December 1999"
            if num2 and (num2.isnumeric() != num1.isnumeric()):
                return

            separator = m.group('num_sep')
            if separator:
                separator = separator.strip()
            post_text = m.group('post')

            return tuple([countable] + self.single_or_range(num1, num2, separator) + [post_text])
        elif m.group('spelled') and m.group('spelled').strip("- "):

            teen = 0 if not m.group('teen') else \
                ["", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"].index(m.group('teen').lower())
            tens = 0 if not m.group('tens') else \
                ["", "ten", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"].index(m.group("tens").lower())
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

            return countable, str(number), m.group('post')

        else:
            return

    @staticmethod
    def is_valid_number(text):

        if text.isnumeric():
            return True

        if not text.strip("IVXLCDM"):
            return True

        if not text.strip("ivxlcdm"):
            return True

        if len(text) > 1 and text[1:].isnumeric() or text[:-1].isnumeric():
            return True

        return False
#              (?P<num2>[0-9ivxlcdmIVXLCDM]+)               # numbers or roman numerals

        # Numbers with letters can contain at most 1 non-digit and it must be the first or the last
        # A3 and 123B are valid, A123B is not, 123A123 is not, but XXIV is
        # TODO: if , is used make sure both numbers look similar
              #(\s*(?P<separator>or|,|&|and|-|–|to|{{ndash}})+\s*)


    @staticmethod
    def get_leading_edition(text):
        pattern = r"""(?x)
            (?P<edition>
            ((
                (1\d|20)\d{2}               # year (1000-2099)
                |travel(l)?er(')?s
                |children(')?s
                |teacher(')?s
                |special
                |bicentennial
                |facsimile
                |illustrated
                |paperback
                |hardcover
                |softcover
                |revised
                |expanded
                |updated
                |u\.s\.
                |english
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
            (?P<season>((Spring|Summer|Autumn|Fall|Winter|Jan(uary)?|Feb(ruary)?|Mar(ch)?|Apr(il)?|May|Jun(e)?|Jul(y)?|Aug(ust)?|Sep(tember)?|Oct(ober)?|Nov(ember)?|Dec(ember)?)[—/—\- ]*)+)
            [.,]+                           # dot or comma
            (?P<post>.*)$            # trailing text
        """

        m = re.match(pattern, text)
        if not m:
            return

        return m.group('season').strip("—/—- "), m.group('post')

    def get_leading_date_retrieved(self, text):
        orig_text = text
        text = re.sub(r"^(retrieved|accessed)(\s+on)?[: ]*", "", text, flags=re.IGNORECASE)
        if text == orig_text:
            return
        text = self._strip_leading_separators(text)
        return self.get_leading_date(text)

    def get_leading_month(self, text):

        # Don't match May Davies Martenet, but do match January, Edward Moore
        pattern = r"""(?x)
            (?P<month>(Jan(uary)?|Feb(ruary)?|Mar(ch)?|Apr(il)?|May|Jun(e)?|Jul(y)?|Aug(ust)?|Sep(t)?(ember)?|Oct(ober)?|Nov(ember)?|Dec(ember)?))
            (?=[,.-:;'"]|\s+(1\d|20)\d{2}|$)
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

        print("date_match", (year, month, day, post_text))
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

                if not day:
                    print("NO DAY IN DATE")

                # Handle ambiguous day/month pairs (2/4)
                if abs(day) < 13:
                    # Specifically allow YYYY-MM-DD even for dates like 2020-01-02
                    alt = f"{year}-{(day*-1):02}-{month:02}"
                    if text.startswith(alt):
                        month, day = str(day*-1), int(month)
                    else:
                        print("AMBIG DAY", day, month, [alt, text])
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


    @classmethod
    def cleanup_text(cls, text):
        # Normalize whitespace
        text = re.sub(r"\s+", " ", text)

        # Remove templates that just wrap other text
        text = cls.strip_wrapper_templates(text, ["nowrap", "nobr"])

        html_tags = ["sup", "span", "small"]
        text = re.sub(r"<\s*/?\s*(" + "|".join(html_tags) + r")\b.*?>", "", text)
        text = text.replace('{{,}}', ",")
        text = text.replace('&nbsp;', " ")
        text = text.replace('{{nbsp}}', " ")
        text = text.replace('&thinsp;', " ")

        # Normalize dashes
        text = text.replace("–", "-")
        text = text.replace("—", "-")
        text = text.replace('&mdash;', "-")
        text = text.replace('&ndash;', "-")
        text = text.replace('{{ndash}}', "-")
        text = text.replace('{{mdash}}', "-")

        #text = re.sub(r'\[\[w:Stephanus pagination\|(.*?)\]\]', r'page \1', text)
        #text = re.sub(r"(\{\{w\|(Y Beibl cyssegr-lan|New King James Version|Bishops' Bible|Douay–Rheims Bible)\}\}),", r"''\1'',", text)
        #text = re.sub(r"(Luther Bible|King James Translators|King James Bible|Wycliffe Bible),", r"''\1'',", text)
        #text = text.replace("L. Spence Encyc. Occult", "L. Spence, ''Encyc. Occult''")
        #text = text.replace("Gibson Complete Illust. Bk Div. & Prophecy", "''Gibson Complete Illust. Bk Div. & Prophecy''")

#
#        text = text.replace('[[et alios]]', "et al.")
#        text = text.replace('[[et al]]', "et al.")
#        text = text.replace('[[et alia]]', "et al.")
#        text = text.replace('[[et alii]]', "et al.")
#        text = text.replace('[[et al]]', "et al.")
#        text = text.replace("''et al.''", "et al.")
#        text = text.replace("et alii", "et al.")
#        text = text.replace(' et. al.', "et al.")

        #text = text.replace("''[[w:Alonso de Molina|Alonso de Molina]]''", "[[w:Alonso de Molina|Alonso de Molina]]")
        #text = re.sub("'''1555(:)?''' ('')?(Idem|ibid)(\.)?('')?, f", "'''1555''' [[w:Alonso de Molina|Alonso de Molina]], ''Vocabulario en lengua castellana y mexicana y mexicana y castellana'', f", text, re.IGNORECASE)
        #text = re.sub("'''1571(:)?''' ('')?(Idem|ibid)(\.)?('')?, f", "'''1571''' [[w:Alonso de Molina|Alonso de Molina]], ''Vocabulario en lengua castellana y mexicana y mexicana y castellana'', f", text, re.IGNORECASE)
        #text = re.sub(r"'''1555(:)?'''(,)? ('')?(Idem|ibid)(\.)?('')?", "'''1555''' [[w:Alonso de Molina|Alonso de Molina]]", text, re.IGNORECASE)
        #text = re.sub(r"'''1571(:)?'''(,)? ('')?(Idem|ibid)(\.)?('')?", "'''1571''' [[w:Alonso de Molina|Alonso de Molina]]", text, re.IGNORECASE)

        text = text.strip()

        return text


    def get_params(self, text):

        print("___")
        print(text)
        print("PARSING")

        # Fail if comments
        if "<!--" in text or "-->" in text:
            #self.warn("html_comment")
            return

        parsed = self.get_parsed(text)
        return self.convert_parsed_to_params(parsed)

    def get_parsed(self, text):

        clean_text = self.cleanup_text(text)
        source_before_author=True
        parsed = self.parse_text(clean_text, source_before_author=source_before_author)

        all_types = { k for k, *vs in parsed if k != "separator" }
        # TODO: if parsed does not contain 'author' and does 'unhandled' and 'publisher' or 'journal' - rescan, but check for author first
        if "author" not in all_types and "unhandled" in all_types and ("journal" in all_types or "publisher" in all_types):
            print("RESCANNING, no author and unhandled")
            source_before_author=False
            parsed = self.parse_text(clean_text, source_before_author=source_before_author)

        # If section and countables, just parse section
        if "section" in all_types and any(x in all_types or x+"s" in all_types for x in countable_labels):
            print("RESCANNING, section and countable")
            parsed = self.parse_text(clean_text, source_before_author=source_before_author, skip_countable=True)

        return parsed



    def get_transformer(self, fingerprint):
        fp_keys = {k for k in fingerprint}
        transformers = [ h[4] for h in self._all_handlers if self.can_handle(h, fingerprint, fp_keys) ]
        if not transformers:
            return

        if not all(t == transformers[0] for t in transformers):
            pass
            #print("Multi matches", fingerprint, transformers)
            #raise ValueError("Multi matches", fingerprint, transformers)
        return transformers[-1]

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
            fingerprint = self.get_fingerprint(parsed, condense_unhandled=True)
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
        allowed_params = {"year", "journal", "author", "volume", "issue", "page", "pages", "url", "title", "titleurl", "month", "publisher", "pageurl", "year_published", "issues", "location", "section", "number"}
        return self.generic_handler(parsed, "journal", allowed_params)

    def web_handler(self, parsed):
        details = { "_source": "web" }
        allowed_params = {"year", "site", "url"}
        for p in parsed:
            if p.type == "separator":
                continue

            elif p.type == "author":
                assert len(p.values) == 1
                for idx, value in enumerate(p.values, 1):
                    key = f"author{idx}" if idx>1 else "author"
                    details[key] = value

            else:
                if p.type not in allowed_params:
                    raise ValueError("unhandled type", p)

                if len(p.values) != 1:
                    print("web unhandled multi-values", p)
                    return
                    raise ValueError("web unhandled multi-values", p)
                details[p.type] = p.values[0]
        return details



    def newsgroup_handler(self, parsed):
        details = { "_source": "newsgroup" }
        allowed_params = {"date", "author", "year", "title", "newsgroup", "url", "titleurl"}
        return self.generic_handler(parsed, "newsgroup", allowed_params)


    def text_handler(self, parsed):
        allowed_params = {"page", "pages", "title", "year", "location", "publisher", "chapter", "pageurl", "year_published", "series", "url", "volume", "issn", "oclc", "month", "section"}
        details = self.generic_handler(parsed, "text", allowed_params)
        if not details:
            return

        # Links to google books can be classified as books
        url = details.get("url", "")
        if re.search("google.[^/]*/books/", url):
            details["_source"] = "book"

#        if re.search("google.[^/]*/news/", url):
#            details["_source"] = "journal"

#        else:
#            return

        return details


    def generic_handler(self, parsed, source, allowed_params):
        details = { "_source": source }

        print("Parsed", parsed)

        def save(k,v):
            if k in details:
                print("dup value", k, v, parsed)
                details["__failed_dup_value"] = True
            details[k] = v

        for p in parsed:

            if p.type.startswith("_maybe_"):
                print("MAYBE", p)
                if self.aggressive:
                    p._replace(type=p.type[len("_maybe_"):])
                else:
                    return

            if p.type == "date":
                details = self.add_date(details, p.values)
                if not details:
                    return
                continue

            if p.type == "accessdate":
                year, month, day = p.values
                save("accessdate", f"{abs(day)} {month} {year}")
                continue

            if p.type == "url":
                save("url", p.values.target)
                continue

            if p.type == "url::page":
                assert len(p.values) == 1
                save("page", p.values[0])

                # rename url to pageurl
                details = {"pageurl" if k in ["url", "chapterurl"] else k:v for k,v in details.items()}
                continue

            if p.type == "url::pages":
                assert len(p.values) == 1
                save("pages", p.values[0])

                # rename url to pageurl
                details = {"pageurl" if k in ["url", "chapterurl"] else k:v for k,v in details.items()}
                continue

            if p.type == "url::chapter":
                assert len(p.values) == 1
                save("chapter", p.values[0])

                # rename url to chapter
                details = {"chapterurl" if k == "url" else k:v for k,v in details.items()}
                continue

            if p.type.endswith("separator"):
                continue

            elif p.type in ["isbn"]:
                save(p.type, "; ".join(p.values[0]))

#            elif p.type == "_maybe_bare_page_link":
#                assert len(p.values) == 1
#                if "url" in details and "page" not in details and p.values[0].isnumeric():
#                    details = {"pageurl" if k == "url" else k:v for k,v in details.items()}
#                    save("page", p.values[0])
#                else:
#                    return

            elif p.type == "author":
                assert len(p.values)
                for idx, value in enumerate(p.values, 1):
                    key = f"author{idx}" if idx>1 else "author"
                    if value.endswith("'s"):
                        value = value[:-2]
                    save(key, value)

#            elif p.type == "publisher2":
#                assert len(p.values) == 1
#                # assign directly to modify existing value
#                details["publisher"] += f" ({p.values[0]})"

            elif p.type in ["editor", "translator"]:
                assert len(p.values)
                if len(p.values) == 1:
                    save(p.type, p.values[0])
                else:
                    save(p.type + "s", "; ".join(p.values))

            elif p.type == "manual_review":
                print(parsed)
                print("MANUAL_REVIEW:", p.values[0])
                details["__failed_needs_manual_review"] = True

            else:
                if p.type not in allowed_params:
                    raise ValueError("unhandled type", p.type, p.values, parsed)

                if len(p.values) != 1:
                    if isinstance(p.values, LINK):
                        if "url" in p.type:
                            save(p.type, p.values.target)
                        else:
                            save(p.type, p.values.orig)
                    else:
                        print("generic unhandled multi-values", p)
                        return
                        raise ValueError("generic unhandled multi-values", p)
                else:
                    save(p.type, p.values[0])

        if any(k.startswith("__failed") for k in details.keys()):
            return

        return details


    def book_handler(self, parsed):
        allowed_params = {"page", "pages", "title", "year", "location", "publisher", "chapter", "pageurl", "year_published", "series", "url", "volume", "issn", "oclc", "month", "section"}
        return self.generic_handler(parsed, "book", allowed_params)


    def apply_transformation(self, parsed, transformer):
        for idx, item in enumerate(parsed):
            new_label = transformer.get(item.type)
            if new_label:
                parsed[idx] = item._replace(type=new_label)

#    _book = {"*page": "page"}
    _year2_published = {"year2": "year_published" }

    # only used in old handlers, plus there's a special handler for "url::page" to convert the link to urllink

    _url_page_page = {} #{ "url::page": "page", "_page_is_urlpage" }
    #_urlpage = {"url": "pageurl", "url::page": "page"}
    _paren_italics_series = {"paren::italics": "series"}
    _year2_year_published = {"year2": "year_published"}
    _fancy_dq_chapter = {"fancy_double_quotes": "chapter"}

    _paren_newsgroup_newsgroup = {"paren::newsgroup": "newsgroup"}

    _dq2_title = {"double_quotes2": "title"}
    _dq_author = {"double_quotes": "author"}
    _skip_italics = {"italics": "separator"}
    _skip_italics2 = {"italics2": "separator"}
    _italics_title = {"italics": "title"}
    _italics2_title = {"italics2": "title"}
    _dq_title = {"double_quotes": "title"}
    _fancy_dq_title = {"fancy_double_quotes": "title"}

    _dq_url_url = {"double_quotes::url": "url"}
    _dq_url_titleurl = {"double_quotes::url": "titleurl"}
    _dq_url_text_title = {"double_quotes::url::text": "title"}

    _skip_paren_unhandled = { "paren::unhandled": "separator" }
    _skip_unhandled = { "unhandled": "separator" }
    _review_unhandled = { "unhandled": "manual_review" }

    _web = {"_handler": web_handler, }
    _url_unhandled_publisher = { "url::unhandled": "publisher" }
    _unhandled_publisher = { "unhandled": "publisher" }


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
        prefixes = ["link", "url", "paren"]

        _anywhere = set()
        _anywhere_tr = {}
        for x in normal:
            _anywhere.add(x)
            for p in prefixes:
                _anywhere.add(f"{p}::{x}")
                _anywhere_tr[f"{p}::{x}"] = x

        # plurals
        for v in plurals:
            for k in [v, v+"s"]:
                _anywhere.add(k)
                _anywhere_tr[k] = v
                for p in prefixes:
                    _anywhere.add(f"{p}::{k}")
                    _anywhere_tr[f"{p}::{k}"] = v

        for k,v in alt_keys.items():
            _anywhere.add(k)
            _anywhere_tr[k] = v
            for p in prefixes:
                _anywhere.add(f"{p}::{k}")
                _anywhere_tr[f"{p}::{k}"] = v

        return _anywhere, _anywhere_tr

#    _book_optionals = { "_match_anywhere_optional": ('translator', 'translators', 'location', 'editor', 'publisher', 'year2', 'chapter', 'page', 'pages', 'url', 'url::page') } | _year2_published | _urlpage

    _book = {"_handler": book_handler, "italics": "title"}
    _book_anywhere, _book_anywhere_tr = make_anywhere(
        [ 'year', 'month', 'author', 'translator', 'location', 'editor', 'publisher', 'isbn', 'issn', 'oclc', 'book_classifier', 'section'],
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
        "url::pages": "url::pages",
        "url::chapter": "url::chapter",
    }
#    print(_book_anywhere)
#    print(_book_anywhere_tr)
#    exit()




    #_book_anywhere = { 'translator', 'location', 'editor', 'publisher', 'year2', 'chapter', 'chapters', 'page', 'pages', 'url', 'url::chapter', 'url::page', 'isbn', 'issn', 'oclc', 'paren::isbn', 'paren::issn', 'paren::oclc', "date_retrieved", "paren::date_retrieved"}
    #_book_anywhere_tr = {'year2': "year_published", 'paren::isbn': 'isbn', 'paren::issn': 'issn', 'paren::oclc': 'oclc', "date_retrieved": "accessdate", "paren::date_retrieved": "accessdate", "volumes": "volume"}
    _book_exclude = { 'newsgroup', 'paren::newsgroup', 'journal', 'italics::journal' }

    book_must_include = [
        {"author", "chapter"},
        {"author", "url::chapter"},
        {"author", "paren::chapter"},

        {"author", "page"},
        {"author", "url::page"},
        {"author", "paren::page"},

        {"editor", "chapter"},
        {"editor", "url::chapter"},
        {"editor", "paren::chapter"},

        {"editor", "page"},
        {"editor", "url::page"},
        {"editor", "paren::page"},

        {"isbn", "editor"},
        {"isbn", "location"},
        {"isbn", "publisher"},

        {"paren::isbn", "editor"},
        {"paren::isbn", "location"},
        {"paren::isbn", "publisher"},

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
        ['date', 'year', 'month', 'author', 'translator', 'location', 'editor', 'publisher', 'isbn', 'issn', 'oclc', 'journal_classifier', 'section'],
        [ "issue", "number", "page", "volume" ], # not chapter
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

    _italics_url_text_title = {"italics::url::text": "title"}
    _italics_url_titleurl = {"italics::url": "titleurl"}
    _skip_italics_link_text = {"italics::link::text": "separator"}

    _url_text_issue = {"url::text": "issue"}
    _link_url = {"link": "url"}

    _link_chapter = {"link": "chapter"}
    _skip_link_chapter = {"link::chapter": "separator"}

    _link_page = {"link": "page"}
    _skip_link_page = {"link::page": "separator"}

    _italics_link_journal = {"italics::link": "journal"}
    _skip_italics_link_journal = {"italics::link::journal": "separator"}
    _link_italics_journal = {"link::italics": "journal"}
    _skip_link_italics_journal = {"link::italics::journal": "separator"}

    _url_text_title = {"url::text": "title"}
    _unhandled_title = {"unhandled": "title"}
    _italics_url_url = {"italics::url": "url"}

    _unhandled_maybe_author = {"unhandled": "_maybe_author"}
    _unhandled_maybe_publisher = { "unhandled": "_maybe_publisher" }
    _unhandled_maybe_location = { "unhandled": "location" }
    _publisher_author = {"publisher": "author"}
    _author_publisher = {"author": "publisher"}


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
        ({}, ['year', 'italics', 'author', 'page'], {}, {}, _text|_italics_title),
        ({}, ['year', 'author', 'url', 'url::italics'], {}, {}, _text|_url_italics_title),
        ({}, ['year', 'italics', 'paren::volumes', 'paren::page'], {}, {}, _text|_paren_volumes_volume|_paren_page),

        ({}, ['year', 'italics', 'publisher'], {}, {}, _text|_italics_title|_publisher_author),
        ({}, ['year', 'publisher', 'italics'], {}, {}, _text|_italics_title|_publisher_author),

        ({}, ['year', 'italics'], _book_anywhere, _book_exclude, _text|_book_anywhere_tr|_italics_title),
        ({}, ['date', 'italics'], _book_anywhere, _book_exclude, _text|_book_anywhere_tr|_italics_title),

        # This a copy of the below book declarations, but with "section"
        ({"author", "section"}, ['year', 'italics'], _book_anywhere, _book_exclude, _text|_italics_title|_book_anywhere_tr),
        ({"author", "section"}, ['year', 'italics::url', 'italics::url::text'], _book_anywhere, _book_exclude, _text|_book_anywhere_tr|_italics_url_text_title|_italics_url_url),
        ({"author", "section"}, ['year', 'italics::link', 'italics::link::text'], _book_anywhere, _book_exclude, _text|_book_anywhere_tr|_italics_link_title|_skip_italics_link_text),

        ({"author", "section"}, ['year', 'italics::link'], _book_anywhere, _book_exclude, _text|_book_anywhere_tr|_italics_link_title),
        ({"author", "section"}, ['year', 'fancy_quote', 'italics'], _book_anywhere, _book_exclude, _text|_book_anywhere_tr|_fq_chapter|_italics_title),
        ({"author", "section"}, ['year', 'fancy_double_quotes', 'italics'], _book_anywhere, _book_exclude, _text|_book_anywhere_tr|_fancy_dq_chapter|_italics_title),
        ({"author", "section"}, ['year', 'italics', 'double_quotes'], _book_anywhere, _book_exclude, _text|_italics_title|_book_anywhere_tr|_dq_chapter),
        ({"author", "section"}, ['year', 'italics', 'italics2'], _book_anywhere, _book_exclude, _text|_italics_title|_book_anywhere_tr|_italics_chapter|_italics2_title),

        ({"author", "section"}, ['year', 'italics', 'fancy_double_quotes'], _book_anywhere, _book_exclude, _text|_italics_title|_book_anywhere_tr|_fancy_dq_chapter),
        ({"author", "section"}, ['year', 'italics', 'publisher', 'year2', 'paren::italics'], _book_anywhere, _book_exclude, _text|_italics_title|_book_anywhere_tr|_paren_italics_series),



        #({}, ['year', 'italics', 'location', 'author'], _book_anywhere, _book_exclude, _text|_book_anywhere_tr|_italics_title|_author_publisher),
        #({}, ['year', 'author', 'unhandled<*>'], {}, {}, _text|_unhandled_title),
        #({}, ['year', 'unhandled<*>', 'italics'], {}, {}, _text|_italics_title|_unhandled_maybe_author),
        #({}, ['date', 'unhandled<*>', 'italics'], {}, {}, _text|_italics_title|_unhandled_maybe_author),


        # Web handlers
        ({}, ['year', 'url', 'url::unhandled<VOA Learning English>', 'paren::unhandled<public domain>'], {}, {},
            _web|_url_unhandled_publisher|_skip_paren_unhandled),

        # Book handlers
        (book_must_include, ['year', 'italics'], _book_anywhere, _book_exclude, _book|_book_anywhere_tr),
        (book_must_include, ['year', 'italics::url', 'italics::url::text'], _book_anywhere, _book_exclude, _book|_book_anywhere_tr|_italics_url_text_title|_italics_url_url),
        (book_must_include, ['year', 'italics::link', 'italics::link::text'], _book_anywhere, _book_exclude, _book|_book_anywhere_tr|_italics_link_title|_skip_italics_link_text),

        (book_must_include, ['year', 'italics::link'], _book_anywhere, _book_exclude, _book|_book_anywhere_tr|_italics_link_title),
        (book_must_include, ['year', 'fancy_quote', 'italics'], _book_anywhere, _book_exclude, _book|_book_anywhere_tr|_fq_chapter),
        (book_must_include, ['year', 'fancy_double_quotes', 'italics'], _book_anywhere, _book_exclude, _book|_book_anywhere_tr|_fancy_dq_chapter),
        (book_must_include, ['year', 'italics', 'double_quotes'], _book_anywhere, _book_exclude, _book|_book_anywhere_tr|_dq_chapter),
        (book_must_include, ['year', 'italics', 'italics2'], _book_anywhere, _book_exclude, _book|_book_anywhere_tr|_italics_chapter|_italics2_title),

        (book_must_include, ['year', 'italics', 'fancy_double_quotes'], _book_anywhere, _book_exclude, _book|_book_anywhere_tr|_fancy_dq_chapter),
        (book_must_include, ['year', 'italics', 'publisher', 'year2', 'paren::italics'], _book_anywhere, _book_exclude, _book|_book_anywhere_tr|_paren_italics_series),

        ({}, ['year', 'author', 'italics', 'publisher'], {}, {}, _book),

        # scan for unhandled authors
        #({}, ['unhandled<*>', 'italics'], _book_anywhere, _book_exclude|{'author'}, _book|_book_anywhere_tr|_unhandled_maybe_author),
        #(book_must_include, ['year', 'unhandled<*>', 'italics'], _book_anywhere, _book_exclude|{'author'}, _book|_book_anywhere_tr|_unhandled_maybe_author),

        # scan for unhandled publishers
        #({}, ['italics', 'unhandled<*>'], _book_anywhere, _book_exclude|{'publisher'}, _book|_book_anywhere_tr|_unhandled_maybe_publisher),
        #({}, ['location', 'unhandled<*>'], _book_anywhere, _book_exclude|{'publisher'}, _book|_book_anywhere_tr|_unhandled_maybe_publisher),
        #(book_must_include, ['year', 'italics', 'unhandled<*>'], _book_anywhere, _book_exclude|{'publisher'}, _book|_book_anywhere_tr|_unhandled_maybe_publisher),

        # unhandled location
        #({}, ['italics', 'unhandled<*>', 'publisher'], _book_anywhere, _book_exclude|{'location'}, _book|_book_anywhere_tr|_unhandled_maybe_location),


        # EXPERIMENTAL
        #({}, ['year', 'author', 'italics', 'location', 'publisher', 'unhandled<*>'], _book_anywhere, _book_exclude, _book|_book_anywhere_tr|_review_unhandled),

        # TODO: ignore link::chapter, link is chapter
        #({}, ['year', 'author', 'italics', 'link', 'link::chapter'], {}, {}, _book|_book_anywhere_tr|_link_chapter|_skip_link_chapter),




        # TODO: book_maybe ? or just allow it explicitly


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
        (journal_must_include, ['italics', 'link', 'link::page'], _journal_anywhere, _journal_exclude, _journal|_journal_anywhere_tr|_italics_title|_link_page|_skip_link_page),
        (journal_must_include, ['italics::url', 'italics::url::text'], _journal_anywhere, _journal_exclude, _journal|_journal_anywhere_tr|_italics_url_text_title|_italics_url_titleurl),
        (journal_must_include, ['url::double_quotes'], _journal_anywhere, _journal_exclude, _journal|_journal_anywhere_tr|_url_dq_title|_url_titleurl),
        ([{'date'}, {'year'}], ['double_quotes', 'link', 'link::italics::journal'], _journal_anywhere, _journal_exclude, _journal|_journal_anywhere_tr|_dq_title|_link_journal|_skip_link_italics_journal),

        (journal_must_include, ['double_quotes::url', 'double_quotes::url::text'], _journal_anywhere, _journal_exclude, _journal|_journal_anywhere_tr|_dq_url_text_title|_dq_url_titleurl),
        ([], ['year', 'italics::journal', 'unhandled<issue>', 'url', 'url::text', 'page'], [], [], _journal|_journal_anywhere_tr|_url_text_issue|_skip_unhandled),
        ([], ['year', 'italics::link', 'italics::link::journal', 'unhandled<issue>', 'url', 'url::text', 'page'], [], [], _journal|_journal_anywhere_tr|_italics_link_journal|_skip_italics_link_journal|_url_text_issue|_skip_unhandled),


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
        (newsgroup_must_contain, ['author', 'newsgroup', 'url'], {}, _newsgroup_exclude, _newsgroup),
        (newsgroup_must_contain, ['author', 'italics::url', 'italics::url::text'], {}, _newsgroup_exclude, _newsgroup|_italics_url_text_title|_italics_url_titleurl),
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
            (('year', 'author', 'italics', '?location', '?editor', 'italics2', '?publisher', '?year2', '?chapter', '?page', '?pages', '?url', '?url::page'), _book|_italics_chapter|_italics2_title|_year2_published),

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

    def add_parsed(self, parsed, key, values, orig=None):

        counter = ""
        if not any(key.endswith(x) for x in ["separator", "unhandled"]):
            for p in reversed(parsed):
                if p.type.startswith(key):
                    if p.type == key or p.type[len(key)] == ":":
                        key = key + "2"
                    else:
                        prev_counter = int(p.type[len(key)])
                        key = key + str(prev_counter+1)
                    break

        parsed.append(Parsed(key, values, orig))



    def run_function(self, function, text):
        res = function(text)
        if not res:
            return

        *res, new_text = res
        if new_text == text:
            raise ValueError("Returned value, but didn't change text", function, res, text)
            return

        return res, new_text


    def parse(self, parsed, name, function, text):
        res = self.run_function(function, text)
        if not res:
            return text
        res, new_text = res

        orig = text[:len(text)-len(new_text)]

        self.add_parsed(parsed, name, res, orig)
        return new_text

    def parse_names(self, parsed, _, function, text):
        res = self.run_function(function, text)
        if not res:
            return text
        res, new_text = res
        #orig = text[:len(text)-len(new_text)]

        # TODO: add "names_orig"??

        names = res[0]
        for name, values in names.items():
            self.add_parsed(parsed, name, values)

        return new_text

    def parse_number(self, parsed, _, function, text):
        res = self.run_function(function, text)
        if not res:
            return text
        res, new_text = res
        orig = text[:len(text)-len(new_text)]

        number_type, *values = res
        if len(values) > 1:
            number_type = number_type + "s"
            values = ["".join(values)]

        self.add_parsed(parsed, number_type, values, orig)

        return new_text

    def parse_with_subdata(self, parsed, label, function, text):
        res = self.run_function(function, text)
        if not res:
            return text
        res, new_text = res
        orig = text[:len(text)-len(new_text)]

        # Temporary - don't parse subdata for usenet stuff
#        if "{{monospace" in text and "Usenet" in text:
#            self.add_parsed(parsed, label, res)
#            return new_text

        sub_text, *values = res
        if values:
            if label in ["url", "link"]:
                extra = values[0]
                self.add_parsed(parsed, label, extra, orig)
            else:
                raise ValueError("unhandled multi-value sub item")

        if not sub_text:
            return new_text

        sub_items = self.parse_text(sub_text, parse_names=True, parse_unlabeled_names=False, subdata=True)
        print("SUB ITEMS", [label, sub_text, sub_items])
        # If everything inside the sub item is just text, ignore it
        #if re.search(r"\[(//|http)", sub_text) \

        all_types = { k for k, *vs in sub_items if k != "separator" }
        if "unhandled" in all_types:
#        if all_types == {"unhandled"} or all_types == {"unhandled", "journal"} or \
#                (len(all_types)>1 and not all_types-{"brackets", "unhandled", "separator", "italics", "parenthesis", "bold", "year", "paren"}):
            print("CONSOLIDATING", label, all_types, sub_text)

            if label in ["url", "link"]:
                self.add_parsed(parsed, label + "::text", [sub_text])
            else:
                self.add_parsed(parsed, label, [sub_text])
            return new_text

        for sub_item in sub_items:
            #sub_label, sub_values = sub_item
            self.add_parsed(parsed, f"{label}::{sub_item.type}", sub_item.values, sub_item.orig)

        return new_text

    mergeable_sections = tuple(set(countable_labels) | {x+"s" for x in countable_labels})
    def merge_countable_into_section(self, parsed):
        # Returns True if successful, even if no changes

        if not parsed:
            return True

        if parsed[-1][0] != "section":
            return True
#        if not parsed and parsed[-1][0] == "section":
#            return

        print("Checking for countables", parsed)

        countable_start = None
        for idx, item in enumerate(parsed):
            if item[0].endswith(self.mergeable_sections):
                if countable_start is None:
                    countable_start = idx
            elif countable_start is not None and item[0] not in ["separator", "section"]:
                # Fail on countable, non-countable, section
                # TODO: handle this failure better?
                print("MERGE FAILED: found non-countable between countable and section")
                return

        if countable_start is None:
            return True

        print("Found countable", parsed[countable_start])

        # what about (italics::unhandled, italics::url::page) ?
        # or (italics::url::unhandled, italics::url::page)?
        # url::italics::page
        # Special handling for "url", "url::countable"
        parts = parsed[countable_start][0].split("::")
        if any(x in parts for x in ["url", "link"]):
            print("FOUND CHILD, looking for parent", parts)
            countable_start -= 1
            if not parsed[countable_start][0].endswith(("url", "link")):
                print("MERGE FAILED: preceeding parsed item is not root url/link", parsed[countable_start][0])
                return
            parts = parsed[countable_start][0].split("::")

        if countable_start>0 and len(parts)>1:
            print("FOUND CHILD, checking if it's first child", parts)
            countable_start -= 1
            if parsed[countable_start][0].startswith(parts[0]):
                print("MERGE FAILED: preceeding parsed item looks like a part of the countable", parsed[countable_start][0])
                return


        merge_parts = []
        for p in parsed[countable_start:]:
            print("XX", p)
            if "url::" in p.type or "link::" in p.type:
                continue
            if not p.orig:
                raise ValueError(p, parsed)
            merge_parts.append(p.orig)

        # Merge
        print("MERGE", merge_parts)
        orig_text = "".join(merge_parts)

        section = orig_text.rstrip(",.:;- ")

        parsed[countable_start:] = [Parsed("section", [section], orig_text)]

        return True


    def do_cleanup(self, parsed, text, no_recursion=False):
        if not parsed:
            return text

        # Merge any multiple "unhandled" sections
        # UN1, UN2 = UN1_UN2
        # UN1, SEP1, UN2 = UN1_SEP1_UN2
        prev_type = parsed[-1].type
        if prev_type == "unhandled":
            if len(parsed) > 2 and parsed[-3].type == "unhandled" and parsed[-2].type == "separator":
                joined = "".join(p.values[0] for p in parsed[-3:])
                parsed[-3:] = [Parsed("unhandled", [joined], joined)]
            elif len(parsed) > 1 and parsed[-2].type == "unhandled":
                joined = "".join(p.values[0] for p in parsed[-2:])
                parsed[-2:] = [Parsed("unhandled", [joined], joined)]
            #return text

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
            self.add_parsed(parsed, "separator", [separator], separator)

        # Add any newly-parsed values to the stack
        parsed += parsed2

        # Final cleanup
        # TODO: disable text scanning
        no_recursion = True
        if text == "":

            res = self.merge_countable_into_section(parsed)
            if not res:
                return

            replacements = []
            for idx, p in enumerate(parsed):
                if p.type == "unhandled":
                    # convert unhandled<'in'> to separator
                    if p.values[0].lower() in self.ignore_unhandled:
                        parsed[idx] = p._replace(type="separator")
                    elif not no_recursion:
                        print("rescanning", p)
                        # Check if the "unhandled" text matches an allow-listed journal, publisher, etc
                        new_items = self.parse_text(p.values[0], parse_names=True, parse_unlabeled_names=False, _recursive=True)
                        new_good_items = [ np for np in new_items if np.type != "separator" ]
                        if len(new_good_items) == 1 and new_good_items[0].type != "unhandled":
                            replacements.append((idx, new_items))


            for idx, new_values in reversed(replacements):
                parsed[idx:idx+1] = new_values


        return new_text


    def parse_text(self, text, parse_names=True, parse_unlabeled_names=True, _recursive=False, source_before_author=True, subdata=False, skip_countable=False):

        orig_text = text

        parsed = []

        parse_authors = True

        self.parsable_names = set()
        if parse_names:
            self.parsable_names = {"author", "editor", "translator"}
            if parse_unlabeled_names:
                self.parsable_names.add("unlabeled")

        def get_leading_names(text):
            if not self.parsable_names:
                return
            res = self.get_leading_names(text, self.parsable_names)

            # Only scan unlabeled once, even if it doesn't return anything
            self.parsable_names -= {"unlabeled"}
            if not res:
                return

            self.parsable_names -= res[0].keys()
            return res

        parse_options = [
                ("date", self.get_leading_date, self.parse, True),
                ("year", self.get_leading_year, self.parse, True),   # process "year" before "bold"
                ("month_day", self.get_leading_month_day, self.parse, True),
                ("month", self.get_leading_month, self.parse, True),
                ("season", self.get_leading_season, self.parse, True),

                # IF "source_before_author" is set, check for journal and publisher before author names
                ("journal", self.get_leading_journal, self.parse, lambda: parse_names and source_before_author),
                # Get leading edition before publisher to catch "First edition" without matching "First" as a publisher
                ("edition", self.get_leading_edition, self.parse, lambda: parse_names and source_before_author),
                ("publisher", self.get_leading_publisher, self.parse, lambda: parse_names and source_before_author),

                ("_unlabeled_names", get_leading_names, self.parse_names, True),
                ("newsgroup", self.get_leading_newsgroup, self.parse, True),

                ("italics", self.get_leading_italics, self.parse_with_subdata, True),
                #("italics", self.get_leading_italics, self.parse, True),
                ("bold", self.get_leading_bold, self.parse_with_subdata, True),
                ("double_quotes", self.get_leading_double_quotes, self.parse_with_subdata, True),
                #("double_quotes", self.get_leading_double_quotes, self.parse, True),
                ("fancy_quote", self.get_leading_fancy_quote, self.parse_with_subdata, True),
                #("fancy_quote", self.get_leading_fancy_quote, self.parse, True),
                ("fancy_double_quotes", self.get_leading_fancy_double_quotes, self.parse_with_subdata, True),
                #("fancy_double_quotes", self.get_leading_fancy_double_quotes, self.parse, True),
                ("paren", self.get_leading_paren, self.parse_with_subdata, True),

                ("date_retrieved", self.get_leading_date_retrieved, self.parse, True),
                ("isbn", self.get_leading_isbn, self.parse, True),
                ("oclc", self.get_leading_oclc, self.parse, True),
                ("issn", self.get_leading_issn, self.parse, True),

                # Get leading edition before publisher to catch "First edition" without matching "First" as a publisher
                ("edition", self.get_leading_edition, self.parse, lambda: parse_names and not source_before_author),
                ("journal", self.get_leading_journal, self.parse, lambda: parse_names and not source_before_author),
                ("publisher", self.get_leading_publisher, self.parse, lambda: parse_names and not source_before_author),

                ("location", self.get_leading_location, self.parse, True), #, lambda: parse_names),

                ("classifier", self.get_leading_classifier, self.parse, True),
                ("", self.get_leading_countable, self.parse_number, lambda: not skip_countable),
                ("section", self.get_leading_section, self.parse, lambda: not subdata),

                # Get links late, since Publishers, Journals, and sections may contain links
                ("link", self.get_leading_link, self.parse_with_subdata, True),
                ("url", self.get_leading_url, self.parse_with_subdata, True),
                ("brackets", self.get_leading_brackets, self.parse_with_subdata, True),

                # Since the parser is about to fail, just slurp everything until the next separator into "unhandled"
                ("unhandled", self.get_leading_unhandled, self.parse, True),
        ]

        prev_text = ""
        while text and text != prev_text:
            text = self.do_cleanup(parsed, text)
            if text is None:
                return
            prev_text = text

#            print("pre :", [text])
#            print("post:", [text])

            for label, function, parser, condition in parse_options:
                if condition != True and not condition():
                    continue

                text = parser(parsed, label, function, text)
                if text != prev_text:
#                    print("match", label, [prev_text, text])

                    # Don't scan for unlabeled names after the journal or the publisher
                    if label in ["journal", "publisher"]:
                        self.parsable_names -= {"unlabeled"}

                    break

        # Run a final cleanup after everything parsed
        text = self.do_cleanup(parsed, text, _recursive)

        # TODO: "unhandled" between "location" and "date" is very likely a publisher
        # TODO: "unhandled" after "location" may be publisher

        if text:
            print(orig_text)
            print(parsed)
            raise ValueError("Unhandled text", orig_text, parsed, text)

        return parsed


    def get_fingerprint(self, parsed, condense_unhandled=False):
        fingerprint = []
        for p in parsed:

            if p.type.endswith("unhandled"):
                if condense_unhandled:
                    fingerprint.append(f"{p.type}<*>")
                else:
                    fingerprint.append(f"{p.type}<{p.values[0]}>")

            elif p.type.endswith("separator"):
                continue
            else:
                fingerprint.append(p.type)

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

        # This fails on "{{a|b}} {{c|d" - where there is no closing bracket it still
        # detects the second "|" as being inside a bracket
        # As a temporary workaround, also fail if count("{{") > count("}}")
        if next(nest_aware_split("|", passage, NESTS)) != passage or \
                passage.count("{{") > passage.count("}}"):
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

        # Anything that starts '''YEAR''' or '''YEAR:''' could be a quote
        pattern = r"""([#:*]+)\s*(?P<quote>'''(1\d|20)\d{2}(:)?'''.*)$"""

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

        if next(nest_aware_split("|", translation, NESTS)) != translation or \
                translation.count("{{") > translation.count("}}"):
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

        # the section paramater will override individual paramaters
#        if "section" in params and any(x in params or x+"s" in params for x in countable_labels):
#            return False

        nests = (("[[", "]]"), ("{{", "}}"), ("[http", "]")) #, (start, stop))

        for k in ["url", "pageurl", "titleurl", "chapterurl", "title", "author"]:
            v = params.get(k, "").strip()

            if v.startswith("|") or v.endswith("|") \
                    or next(nest_aware_split("|", v, NESTS)) != v:
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

    r'''


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



    def xget_leading_location(self, text):
        searcher = self._allowed_searchers.get("location", self.init_searcher("location", "allowed_locations"))

        location = self.find_starting_item(text, *searcher)
        if not location:
            return

        if len(location) == len(text):
            return location, ""

        if text[len(location)] in "-.;:":
            return location, text[len(location):]

        return

#        if startswith(text, _loc_matches
#        return self.get_leading_regex(self._allowed_locations_regex, text)


    def xget_leading_publisher(self, text):

        text = re.sub(r"^(printed|published|publ\.|republished|in )(| by)?[-;:,.\s]*", "", text)

        searcher = self._allowed_searchers.get("publisher", self.init_searcher("publisher", "allowed_publishers"))
        item = self.find_starting_item(text, *searcher)
        if not item:
            return

        if len(item) == len(text):
            return item, ""

        if text[len(item)] in "-.,;: ":
            return item, text[len(item):]

        print("matchy but not matchy matchy", [text[len(item)]])


    def xget_leading_journal(self, text):

        searcher = self._allowed_searchers.get("journal", self.init_searcher("journal", "allowed_journals"))
        item = self.find_starting_item(text, *searcher)
        if not item:
            return

        if len(item) == len(text):
            return item, ""

        if text[len(item)] in """ -.,;:'"()[]{}""":
            return item, text[len(item):]


    def init_searcher(self, name, filename):
        with open(filename) as infile:
            prefix_len = 4
            items = set()
            for line in infile:
                line = line.strip()
                if not line:
                    continue
                if len(line) < prefix_len:
                    prefix_len = len(line)
                items.add(line)

            # Order by prefix, then longest to shortest in order to match "New York, NY" before "New York"
            items = sorted(items, key=lambda x: (x[:prefix_len], len(x)*-1, x))

        matches = self.build_matcher(items, prefix_len)

        searcher = (prefix_len, matches, items)
        self._allowed_searchers[name] = searcher
        return searcher




    def build_matcher(self, items, prefix_len):
        assert prefix_len > 1

        prev = None
        prev_start = None
        prefixes = {}
        for idx, item in enumerate(items):
#            print(idx, item)
            prefix = item[:prefix_len]
            if prefix != prev:
                if prev_start is not None:
                    prefixes[prev] = (prev_start, idx)
#                    print("new prefix", prev, prefix)
#                    if len(prefixes) > 5:
#                        exit()

                prev_start = idx
                prev = prefix

        prefixes[prev] = (prev_start, idx+1)
        return prefixes

#    _loc_matches = build_matcher(_allowed_locations, _loc_prefix_len)

    @staticmethod
    def find_starting_item(text, prefix_len, prefixes, items):
        start, stop = prefixes.get(text[:prefix_len], (0,0))
        print(text[:prefix_len], start, stop)
        for item in items[start:stop]:
            print(text, item)
            if text.startswith(item):
                return item



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


    '''


    # curl ftp://ftp.isc.org/pub/usenet/CONFIG/active | cut -d '.' -f 1 | uniq > allowed_newsgroups
    with open("quotes/newsgroup.allowed") as infile:
        _allowed_newsgroups = {line.strip() for line in infile if line.strip()}
    # sort "bigger" before "big"
    _allowed_newsgroups = sorted(_allowed_newsgroups, key=lambda x: x+"🂲")

    _allowed_newsgroups_regex = re.compile(r"""(?x)
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
            (?P<post>.*)$
        """, re.IGNORECASE)


    @staticmethod
    def make_regex(items, pre, post):
        # sort "bigger" before "big"
        sorted_items = sorted(items, key=lambda x: x+'🂲')

        return re.compile(f"{pre}(" + "|".join(map(re.escape, sorted_items)) + fr"){post}", re.IGNORECASE)

    @staticmethod
    def load_items(filename):
        items = set()
        with open(filename) as infile:
            for line in infile:
                line = line.strip()
                if line:
                    items.add(line)

        return items

    def old_load_items(self, filename, prefixes=None, postfixes=None, disallowed_items=[]):
        pre = self.make_pre_regex(prefixes) if prefixes else ""
        post = self.make_post_regex(postfixes) if postfixes else ""

        pattern = (f"^{pre}(?P<data>.*?){post}$")

        items = set()
        with open(filename) as infile:
            for line in infile:
                line = line.lower().strip()
                orig = line
                line = re.sub(pattern, r"\g<data>", line)
                line = line.strip(", ")

                # Fix for over-compressed items like "The University Press" being shortened to just "University"
                if line in disallowed_items or line.isnumeric() or len(line)<2:
                    if line == orig:
                        continue
                    line = orig

                # TODO: allow some like "Doubleday, Page"
                if line.endswith((", page", ", chapter")):
                    continue

                if len(line)<2:
                    continue

                if line in disallowed_items:
                    print("bad item - disallowed", orig)
                    continue

                if line.isnumeric():
                    print("bad item - numeric", orig)
                    continue

                if self.get_leading_countable(line):
                    print("bad item", orig)
                    continue

                if not line:
                    continue

#                print("PUB", line)
#                exit()

#                if line.startswith("nyu"):
#                    print(line, orig)
#                    exit()
                items.add(line)
        return items

    _allowed_locations = set()
    with open("quotes/location.allowed") as infile:
        for line in infile:
            line = line.strip()
            if not line:
                continue
            _allowed_locations.add(line)

    # sort "bigger" before "big"
    _allowed_locations = sorted(_allowed_locations, key=lambda x: x+'🂲')
