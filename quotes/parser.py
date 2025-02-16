import mwparserfromhell as mwparser
import sys

from autodooz.sections import ALL_LANGS
from collections import namedtuple
from autodooz.quotes.name_labeler import NameLabeler
from autodooz.quotes.names import *
from autodooz.utils import nest_aware_split, nest_aware_resplit


NESTS = (("[", "]"), ("{{", "}}"))
Parsed = namedtuple("Parsed", ["type", "values", "orig"])
LINK = namedtuple("LINK", [ "target", "text", "orig" ])

class QuoteParser():

    ignore_unhandled = {
            '"', "", "(", ")", ',', ":", "'s", "*",
            "in", "as", "in the", "on", "for", "and", "of", #"to",
            "from",
            "published in", "article in", "for the author", "rev", "the",
            #"entry in", # - this should be handled explicitly and transform "chapter" into "entry"
            # "by", "article in", "magazine", "p", "pp", "page",
    }

    def make_pre_regex(prefixes):
        # Sort "bigger" before "big"
        prefixes = sorted(prefixes, key=lambda x: x+'🂲')
        return "((" + "|".join(prefixes) + r")\s+)*".lower()

    def make_post_regex(postfixes):
        # Sort "bigger" before "big"
        postfixes = sorted(postfixes, key=lambda x: x+'🂲')
        return "([&., ]+(" + "|".join(postfixes) +")[.]?)*".lower()

    journal_prefix_regex = make_pre_regex(journal_prefixes|common_prefixes|ignorable_affixes)
    journal_postfix_regex = make_post_regex(journal_postfixes|common_postfixes|ignorable_affixes)

    publisher_prefix_regex = make_pre_regex(publisher_prefixes|common_prefixes|ignorable_affixes)
    publisher_postfix_regex = make_post_regex(publisher_postfixes|common_postfixes|ignorable_affixes)


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

    #_separator_regex = r"([/#:;\-.–,— ]*)(.*)$"
    _separator_regex = r"([/:;\-.–,— ]*)(.*)$"
    def _split_leading_separators(self, text):
        return re.match(self._separator_regex, text).groups()

    _leading_year_template_pattern = r"""(?x)
            (?P<years>
                (\s|'''|\(|\[)*           # ''' or ( or [
                (?P<template>
                    {{\s*
                      (c\.|circa|circa2|a\.|ante|post)                   # date templates
                    \s*\|?[^{}]*
                    }}
                )
                (\s|(:)?'''|\)|\])*           # ''' or ) or ]
            )
            (?P<post>.*)$         # trailing text
    """

    _leading_year_pattern = r"""(?x)
            (?P<q1>circa|ca[.]?|c[.]?|ante|a[.]?|post|p[.]?)?\s*       # optional date qualifier
            (year\s*)?
            (?P<years>
            (\s|'''|\(|\[)*           # ''' or ( or [
            \s*
            (?P<q2>circa|ca[.]?|c[.]?|ante|a[.]?|post|p[.]?)?\s*       # optional date qualifier
            (?P<year1>(1\d|20)\d{2})
            (
              (\s*(?P<separator>or|,|&|and|-|–|to|{{ndash}})+\s*)
              (?P<year2>(1\d|20)\d{2})
            )?
            \s*({{\s*(CE|C\.E\.)[^}]*}}|CE[:, ])?\s*
            (\s|(:)?'''|\)|\])*           # ''' or ) or ]
            )
            \s*({{\s*(CE|C\.E\.)[^}]*}}|CE[:, ])?\s*
            (?!-) # Not followed by - (avoids matching YYYY-MM-DD)
            (?P<post>.*)$         # trailing text
        """
    _leading_year_regex = re.compile(_leading_year_pattern, re.IGNORECASE)
    _leading_year_template_regex = re.compile(_leading_year_template_pattern, re.IGNORECASE)
    def get_leading_year(self, text):

        m_template = re.match(self._leading_year_template_regex, text)
        m = m_template if m_template else re.match(self._leading_year_regex, text)
        if not m:
            return

        group = m.group('years').strip()
        post_text = m.group('post')

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

        if group[0] in "'[(" or group[-1] in "'])":
            return


        # Parse templates
        if m_template:
            t = next(mwparser.parse(group).ifilter_templates())
            qualifier = t.name.rstrip()[0]
            if not t.has(1) or any(p.name not in ["1", "2", "short"] for p in t.params):
                return

            year1 = str(t.get(1).value).strip(" '")
            year2 = str(t.get(2).value).strip(" '") if t.has(2) else None
            separator = "-" if year2 else None
        else:

            # Don't match 1234 in 12345
            if group[-1].isnumeric and post_text and post_text[0].isnumeric():
                return

            # Double qualifiers should never happen
            if m.group("q1") and m.group("q2"):
                return

            qualifier = m.group("q1") if m.group("q1") else m.group("q2")
            year1 = m.group('year1')
            year2 = m.group('year2')
            separator = m.group('separator')


        if qualifier:
            qualifier = qualifier[0].lower()
            year1 = qualifier + ". " + year1

        # Strip {{CE}} after year
        post_text = self._strip_leading_separators(post_text)
        post_text = re.sub(r"^({{(CE|C\.E\.)[^}]*}}|CE[:,])\s*", "", post_text)

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


    classifiers = { "magazine", "song", "tv series", "transcript" }
    classifiers_pattern = "|".join(classifiers)
    connector_words_pattern = r"(the|a|an|on|in|to)\b"
    _leading_classifier_pattern = fr"""(?x)
         (?P<open>
             [(\[]*     # opening ( or [
         )
         (?P<classifier>
             (\s*({connector_words_pattern})*\s)*
             ({classifiers_pattern})+
             (\s*({connector_words_pattern}))*
         )+
         (?P<close>
             [)\]]*     # closing ( or [
         )
         (?P<post>.*)
    """
    _leading_classifier_regex = re.compile(_leading_classifier_pattern)

    # Detect text that classifies the quote (magazine, song, tv series)
    def get_leading_classifier(self, text):
        m = re.match(self._leading_classifier_regex, text)
        if not m:
            return

        match = m.group('classifier')
        for c in ["magazine", "song", "tv series"]:
            if c in match.lower():
                return {c: match}, m.group("post")

    # TODO allow-list of templates
    _leading_section_pattern = fr"""(?x)^
        (?P<classifer>
            \{{\{{gbooks.*\}}\}}               # Take gbooks without validating the parameters
            |\{{\{{.*?[|}}]                    # Other templates allowed, but parameters must pass validation
            |\[\[.*?[|\]]                      # Links allowed, but parameters must pass validation
            |\[http.*?[ \]]                    # [http.* until space or closing bracket
            |http[^ ]*                         # http.* until space
            |{number_pattern}\b
            |{number_words_pattern}\b
            |{section_labels_pattern}\b
            |(the|a|an|on|in|to|ad)\b
            |\W
        )+
    """
    _leading_section_regex = re.compile(_leading_section_pattern, re.IGNORECASE)

#    text = "issue [http://www.spiegel.de/spiegel/print/index-2010-49.html 49/2010], page 80:"

#    text = '[http://books.google.co.uk/books?id=erS-2XR-kPUC&pg=PA112&dq=crescendi&ei=58nkSeaJIYyykASju4yfDQ page 112] ([http://store.doverpublications.com/0486212661.html DoverPublications.com]; {{ISBN|0486212661}}'
#    text = '([http://store.doverpublications.com/0486212661.html DoverPublications.com]; {{ISBN|0486212661}}'
#    prev_text = None
#    print(text)
#    while text and prev_text != text:
#        prev_text = text
#        text = re.sub(_leading_section_regex, "", text, 1)
#        print(text)
#
#    exit()

    def get_leading_section(self, text):
        # Section here refers to the section= parameter of the quote templates, which is used
        # instead of a combination labeled numbers like page= volume= column= to describe
        # where the text is located. This allows for freeform entries like "Act XI (footnote)"

        # If ALL of the remaining text consists of text locations and numbers, slurp it up
        m = re.match(self._leading_section_regex, text)
        if not m or m.group(0) != text:
            return

        section = m.group(0).strip(",.:;- ")
        return section, ""


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

        if re.search(", Usenet[,.]*$", text) or ("{{monospace" in text and "Usenet" in text):
            text = self._strip_leading_separators(text)
            m = re.match("""(.*?), ("|“|'')""", text)
            if not m:
                return
            username = m.group(1)
            new_text = text[len(username):]

            username = re.sub(r"([,. ]*\(?username\)?)", "", username)

            if username.startswith('"') and username.endswith('"') and '"' not in username[1:-1]:
                username = username.strip('" ')
            return username, new_text

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
            new_text = re.sub(r"^(ed\. by|ed\.|eds\.|edited by)\s*", "", text, flags=re.IGNORECASE)
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
        return self.get_leading_start_stop('“', '”', text)

    def get_leading_fancy_quote(self, text):
        return self.get_leading_start_stop("‘", "’", text)

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

#        # handle bare link in parenthesis (http://foo.bar)
#        if text.startswith("(http://") or text.startswith("(https://"):
#            link, _, post = text[1:].partition(")")
#            link = link.rstrip(".,:;- ")
#            if " " in link:
#                return
#            link_text = ""
#            return link_text, LINK(link, link_text, link), post

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
            )
            (?:edition|ed\.)
            (?P<post>.*)$            # trailing text
        """

        m = re.match(pattern, text, re.IGNORECASE)
        if not m:
            return

        return m.group('edition').strip(), m.group('post')


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
    def _extract_link_format_sub(m):

        for start, end in  ( ('[[', ']]'), ("{{", "}}"), ("[", "]") ):
            if m.group("link_start").startswith(start):
                if not m.group("link_end").endswith(end):
                    return m.group(0)
                break

        for start, end in  ( ('"', '"'), ("''", "''"), ('“', '”'), ("‘", "’") ):
            if m.group("format_start") == start:
                if m.group("format_end") != end:
                    return m.group(0)
                if start in m.group("link_text"):
                    return m.group(0)
                if start != end and end in m.group("link_text"):
                    return m.group(0)
                break

        return m.group("format_start") + m.group("link_start") + m.group("link_text") + m.group("link_end") + m.group("format_end")


    @classmethod
    def extract_link_format(cls, text):
        pattern = r"""(?x)
            (?P<link_start>
                {{(w|lang)\|[^}|]*\|   # {{w|xx| or {{lang|xx|
                |
                \[\[[^|\]]+\|          # [[foo_until_pipe|
                |
                \[[^ \]]+\s             # [url_until_space
            )
            \s*
            (?P<format_start>''|"|“|‘)
            (?P<link_text>[^\]]+)
            (?P<format_end>''|"|”|’)
            (?P<link_end>}}|\]\]|\])  # }}, ]] or ]
        """
        return re.sub(pattern, cls._extract_link_format_sub, text)

    # TODO: Support [[:w:blah "foo"]] style links and maybe {{w|blah|''foo''}} too


    @staticmethod
    def _normalize_et_al_sub(m):
        if len(m.group('start')) == len(m.group('end')):
            return ", et al"
        return m.group(0)

    @classmethod
    def normalize_et_al(cls, text):
        pattern = r"""(?x)
                ,*
                \s+
                (?P<start>['(\[]*)
                (et|&)[.]?             # et or et.
                \s+
                al(ii|ia|ios)?      # al, al., alii, alia, alios
                \b
                \.?
                (?P<end>['\])]*)
                """
        return re.sub(pattern, cls._normalize_et_al_sub, text)

    @classmethod
    def cleanup_text(cls, text):
        # Normalize whitespace
        text = re.sub(r"\s+", " ", text)

        text = text.replace("[[w:Usenet|Usenet]]", "Usenet")

        # Remove templates that just wrap other text
        text = cls.strip_wrapper_templates(text, ["nowrap", "nobr"])

        html_tags = ["sup", "span", "small"]
        text = re.sub(r"<\s*/?\s*(" + "|".join(html_tags) + r")\b.*?>", "", text)
        text = text.replace('{{,}}', ",")
        text = text.replace('&nbsp;', " ")
        text = text.replace('{{nbsp}}', " ")
        text = text.replace('&thinsp;', " ")

        # Convert [link ''blah''] to ''[link blah]''
        text = cls.extract_link_format(text)

        # Normalize dashes
        text = text.replace("–", "-")
        text = text.replace("—", "-")
        text = text.replace('&mdash;', "-")
        text = text.replace('&ndash;', "-")
        text = text.replace('{{ndash}}', "-")
        text = text.replace('{{mdash}}', "-")

        text = re.sub(r"(''La Santa Biblia \(antigua versión de Casiodoro de Reina\)''), rev., ''(.*?)''", r"''\2'', \1", text)

        #text = re.sub(r'\[\[w:Stephanus pagination\|(.*?)\]\]', r'page \1', text)
        #text = re.sub(r"(\{\{w\|(Y Beibl cyssegr-lan|New King James Version|Bishops' Bible|Douay–Rheims Bible)\}\}),", r"''\1'',", text)
        #text = re.sub(r"(Luther Bible|King James Translators|King James Bible|Wycliffe Bible),", r"''\1'',", text)
        #text = text.replace("L. Spence Encyc. Occult", "L. Spence, ''Encyc. Occult''")
        #text = text.replace("Gibson Complete Illust. Bk Div. & Prophecy", "''Gibson Complete Illust. Bk Div. & Prophecy''")

        text = cls.normalize_et_al(text)

         # page [http://books.google.com/books?id=SYdaAAAAMAAJ&q=%22pick+up+some+McDonald%27s%22 36]
        text = re.sub(r"(?:page|pages|pp.|p.|pp|p)\s*\[(http[^ ]*)\s+(\d+)\]", r"[\1 page \2]", text)


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

#        text = re.sub("\(transcript\):$", "", text)

        return text



    def add_parsed(self, parsed, key, values, orig=None):

        counter = ""
        if not any(key.endswith(x) for x in ["separator", "unhandled"]):
            for p in reversed(parsed):
                if p.type.startswith(key):
                    prev_key, _, _ = p.type.partition("::")

                    if prev_key == key:
                        key = key + "2"
                    elif prev_key[-1].isnumeric():
                        counter = int(prev_key[-1]) + 1
                        key = key + str(counter)

                    # 'pages' starts with 'page' but they should be numbered separately
                    else:
                        continue
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

    def parsed_to_text(self, parsed):
        print(parsed[-1])
        print([p.orig for p in parsed])

        return "".join([p.orig for p in parsed if "url::" not in p.type and "link::" not in p.type])

    def parse(self, parsed, name, function, text):
        res = self.run_function(function, text)
        if not res:
            return text
        res, new_text = res

        orig = text[:len(text)-len(new_text)]

        self.add_parsed(parsed, name, res, orig)
        return new_text


    @staticmethod
    def should_pop(item):
        always_pop = ("italics", "double_quotes", "fancy_double_quotes", "isbn", "oclc", "issn" "chapter")
        return item.type.startswith(always_pop) or item.type.endswith(always_pop)

    def parse_section(self, parsed, name, function, text):

        res = self.run_function(function, text)
        if not res:
            return text
        res, new_text = res
        section_text = res[0]
        assert new_text == ""
        orig = text

        sub_items = self.parse_text(section_text, parse_names=False, parse_unlabeled_names=False, parse_sections=False)

        print("SUBITEMS", [p.type for p in sub_items])

        # read through the subdata and pop anything that's not an override countable
        # (eg, italics should never be in the section value unless it's preceeded by 
        # something that can only be handled as section data: act 2, ''introduction''
        popped = False
        while sub_items:
            # TODO: Figure out the full list of things that can be popped
            if self.should_pop(sub_items[0]):
                sub_item = sub_items.pop(0)
                self.add_parsed(parsed, sub_item.type, sub_item.values, sub_item.orig)
                popped = True
                print("POPPED", sub_item)
            else:
                break

        if not sub_items:
            return new_text

        trailing_items = []
        # If there is a single bare url at the end, split it out to link no matter what
        if sub_items and sub_items[-1].type == "url":
            print("POPPED", sub_items[-1])
            trailing_items.append(sub_items.pop())

        print("STILL SUBITEMS", [p.type for p in sub_items])
        if sub_items:
            # If none of the text was unhandled, don't use "section"
            if not any(p.type.endswith("unhandled") for p in sub_items):
                print("ALL SUBDATA IS GOOD", sub_items)
                for item in sub_items:
                    self.add_parsed(parsed, item.type, item.values, item.orig)
            else:

                # If any items have been removed from the section,
                # re-generate and re-parse the section text
                if popped or trailing_items:
                    orig = self.parsed_to_text(sub_items)
                    section_text = orig.strip(",.:;- ")

                self.add_parsed(parsed, name, [section_text], orig)


        for item in trailing_items:
            self.add_parsed(parsed, item.type, item.values, item.orig)

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
        print("LABEL", label)
        print("ORIG:", [orig])
        print("RES", res)

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

        sub_items = self.parse_text(sub_text, parse_names=True, parse_unlabeled_names=False, parse_sections=False)
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
                self.add_parsed(parsed, label, [sub_text], orig)

        else:
#            if label in ["paren", "bracket"]:
#                for sub_item in sub_items:
#                    #sub_label, sub_values = sub_item
#                    self.add_parsed(parsed, f"{sub_item.type}", sub_item.values, sub_item.orig)
#            else:
                for sub_item in sub_items:
                    #sub_label, sub_values = sub_item
                    self.add_parsed(parsed, f"{label}::{sub_item.type}", sub_item.values, sub_item.orig)

        return new_text

    mergeable_sections = tuple(set(countable_labels) | {x+"s" for x in countable_labels})
    def merge_countable_into_section(self, parsed):
        # Returns True if successful, even if no changes

        if not parsed:
            return True

        if not parsed[-1].type.endswith("section"):
            return True
#        if not parsed and parsed[-1][0] == "section":
#            return

        print("Checking for countables", parsed)

        countable_start = None
        for idx, item in enumerate(parsed):
            if item.type.endswith(self.mergeable_sections) or item.type.endswith("section"):
                if countable_start is None:
                    countable_start = idx
            elif countable_start is not None and item.type not in ["separator", "section", "url", "link"]:
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
        parts = parsed[countable_start].type.split("::")
        if any(x in parts for x in ["url", "link"]):
            print("FOUND CHILD, looking for parent", parts)
            countable_start -= 1
            if not parsed[countable_start].type.endswith(("url", "link")):
                print("MERGE FAILED: preceeding parsed item is not root url/link", parsed[countable_start].type)
                return
            parts = parsed[countable_start].type.split("::")

        if countable_start>0 and len(parts)>1:
            print("FOUND CHILD, checking if it's the first child", parts)
            countable_start -= 1
            if parsed[countable_start].type.startswith(parts[0]):
                print("MERGE FAILED: preceeding parsed item looks like a part of the countable", parsed[countable_start].type)
                return

        orig_text = self.parsed_to_text(parsed[countable_start:])

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

#            res = self.merge_countable_into_section(parsed)
#            if not res:
#                return

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


    def parse_text(self, text, parse_names=True, parse_unlabeled_names=True, _recursive=False, source_before_author=True, parse_sections=True, skip_countable=False):

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

                # Process edition before year, to capture "1995 revised edition"
                ("edition", self.get_leading_edition, self.parse, lambda: parse_names and source_before_author),
                ("year", self.get_leading_year, self.parse, True),   # process "year" before "bold"
                ("month_day", self.get_leading_month_day, self.parse, True),
                ("month", self.get_leading_month, self.parse, True),
                ("season", self.get_leading_season, self.parse, True),

                # Scan for 'section' early, as it may contain formatting
                ("section", self.get_leading_section, self.parse_section, lambda: parse_sections),

                # IF "source_before_author" is set, check for journal and publisher before author names
                ("journal", self.get_leading_journal, self.parse, lambda: parse_names and source_before_author),
                # Get leading edition before publisher to catch "First edition" without matching "First" as a publisher
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

                ("date_retrieved", self.get_leading_date_retrieved, self.parse, True),
                ("isbn", self.get_leading_isbn, self.parse, True),
                ("oclc", self.get_leading_oclc, self.parse, True),
                ("issn", self.get_leading_issn, self.parse, True),

                # Get leading edition before publisher to catch "First edition" without matching "First" as a publisher
                ("edition", self.get_leading_edition, self.parse, lambda: parse_names and not source_before_author),
                ("journal", self.get_leading_journal, self.parse, lambda: parse_names and not source_before_author),
                ("publisher", self.get_leading_publisher, self.parse, lambda: parse_names and not source_before_author),

                ("location", self.get_leading_location, self.parse, True), #, lambda: parse_names),

                # Get links late, since Publishers, Journals, and sections may contain links
                #("link", self.get_leading_link, self.parse_with_subdata, True),
                ("url", self.get_leading_url, self.parse_with_subdata, True),

                ("", self.get_leading_countable, self.parse_number, lambda: not skip_countable),

                # Classifier may be enclosed in brackets or parenthesis
                ("classifier", self.get_leading_classifier, self.parse, True),
                ("paren", self.get_leading_paren, self.parse_with_subdata, True),
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
        # TODO: Remove this after section parsing is re-done
#        if "section" in all_types and any(x in all_types or x+"s" in all_types for x in countable_labels):
#            print("RESCANNING, section and countable")
#            parsed = self.parse_text(clean_text, source_before_author=source_before_author, skip_countable=True)

        return parsed
