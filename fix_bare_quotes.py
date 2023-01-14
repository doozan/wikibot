import enwiktionary_sectionparser as sectionparser
from autodooz.sections import ALL_LANGS
import re
import sys

def dprint(*args, **kwargs):
    return
    print(args, kwargs, file=sys.stderr)

class QuoteFixer():

    def __init__(self):
        self._summary = None
        self._log = []

    def fix(self, code, section, details):
        if self._summary is not None:
            self._summary.append(f"/*{section.path}*/ {details}")

        page = list(section.lineage)[-1]
        self._log.append(("autofix_" + code, page))

    def warn(self, code, section, details=None):
        page = list(section.lineage)[-1]
        self._log.append((code, page, details))

    @staticmethod
    def get_year(text):
        m = re.match(r"^'''(\d{4})'''[;,:—\- ]*(.*)$", text)
        if not m:
            dprint(text)
            return

        return m.group(1), m.group(2)


    @classmethod
    def get_translator(cls, text):
        translator, text = cls.get_prefixed_translator(text)
        if translator:
            return translator, text

        return cls.get_suffixed_translator(text)

    @classmethod
    def get_prefixed_translator(cls, text):

        pattern = r"""(?x)
            ^[;:, ]*(?P<pre>.*?)\s*         # leading text
            \(?(?:tr\.|trans\.|translated)\s*(?:by)?\s*
            (.*?)
            [),]                            # must end with a ) or ,
            [;:, ]*(?P<post>.*)$            # trailing text
        """

        m = re.match(pattern, text)
        if m:
            if not cls.is_valid_name(m.group(2)):
                dprint("invalid translator:", m.group(2))
                return "", text

            return m.group(2), m.group('pre') + " " + m.group('post')
        return "", text


    @classmethod
    def get_suffixed_translator(cls, text):
        pattern = r"""(?x)
            ^(?P<pre>.*?)\s*         # leading text
            (?:^|[;:,])\s*           # beginning of line or separator
            ([^,]*?)\s*              # name
            \(translator\)
            [;:, ]*(?P<post>.*)$     # trailing text
        """

        m = re.match(pattern, text)
        if m:
            if not cls.is_valid_name(m.group(2)):
                dprint("***************** invalid translator:", m.group(2))
                return "", text

            return m.group(2), m.group('pre') + " " + m.group('post')
        return "", text


    @classmethod
    def get_editor(cls, text):

        pattern = r"""(?x)
            ^[;:, ]*(?P<pre>.*?)\s*  # leading text
            [;:,(]\s*                # separator
            (?:edited\sby|ed\.)\s+   # edited by
            (.*?)                    # name
            [);:,]\s*                # separator
            (?P<post>.*)$            # trailing text
        """

        m = re.match(pattern, text)
        if not m:

            # Search for (eds. 1, 2)
            pattern = r"""(?x)
                ^[;:, ]*(?P<pre>.*?)\s*  # leading text
                (?:\(eds.)\s+            # (eds.
                (.*?)                    # names
                [)]\s*                   # )
                (?P<post>.*)$            # trailing text
            """
            m = re.match(pattern, text)

        if not m:
            return [], text

        names = []
        for name in cls.split_names(m.group(2)):
            if not cls.is_valid_name(name):
                dprint("invalid editor:", name)
                return [], text
            names.append(name)

        return "; ".join(names), m.group('pre') + " " + m.group('post')


    @staticmethod
    def is_valid_name(text):

        if text.startswith("[") and text.endswith("]"):
            return True

        if text.startswith("{{w|") and text.endswith("}}"):
            return True

        bad_items = [r'''[:ə"“”()<>\[\]\d]''', "''",  r"\b(and|in|of|by|to|et al|Guides|Press|[Cc]hapter|Diverse)\b", r"\.com", r"\btrans" ]
        pattern = "(" +  "|".join(bad_items) + ")"
        if re.search(pattern, text):
            return False

        if len(text) < 5:
            return False

        if text.count(" ") > 3:
            return False

        if " " not in text and text not in ["Various", "Anonymous", "anonymous", "Unknown", "unknown"]:
            return False

        return True

    @staticmethod
    def split_names(text):
        s = re.search("( and| &|,|;) ", text)
        separator = s.group(1) if s else ", "

        names = []
        for name in text.split(separator):
            name = name.strip()
            if name.startswith("and "):
                name = name[4:]
            if name.startswith("& "):
                name = name[2:]
            if not name:
                continue
            if len(name) < 5:
                if name in ["Jr.", "Jr", "MD", "PhD", "MSW", "JD", "II", "III", "IV", "jr", "MS", "PHD", "Sr."]:
                    names[-1] += f", {name}"
                    continue
            names.append(name)

        return names

    @classmethod
    def get_authors(cls, text):
        authors = []

        has_et_al = False
        new_text = re.sub(r"(''|[;, ]+)et al((ii|\.)''|[.,])", "", text)
        if new_text != text:
            has_et_al = True
            text = new_text

        m = re.match("""(.+?) (("|'').*)$""", text)
        if not m:
            return [], text

        author_text = m.group(1).strip(":;, ").replace("&#91;", "").replace(" (author)", "")

        authors = []
        for author in cls.split_names(author_text):
            if not cls.is_valid_name(author):
                dprint("invalid author:", author)
                return [], text
            authors.append(author)

        if has_et_al:
            authors.append("et al")

        return authors, m.group(2)

    @staticmethod
    def get_chapter_title(text):
        # The chapter title is the first string closed in " " possibly followed by "in"
        pattern = r"""(?x)
            [;:, ]*                 # separator
            "(.+?)"                 # title enclosed in quotes
            [;:, ]*                 # separator
            (in)?                   # in (optional)
            [;:, ]*(?P<post>.*)$    # trailing text
        """

        m = re.match(pattern, text)
        if m:
            return m.group(1), m.group('post')


        # The chapter title is sometimes enclosed in '' '' instead of " ". In this case it MUST be followed by ", in ''"
        pattern = r"""(?x)
            [;:, ]*                 # separator
            ''(.+?)'',\s+in           # title enclosed in quotes
            [;:, ]*(?P<post>''.*)$    # trailing text
        """

        m = re.match(pattern, text)
        if m:
            return m.group(1), m.group('post')

        return "", text


    @classmethod
    def get_title(cls, text):
        # The title is the first string closed in '' '' possibly followed by (novel)

        # match exactly 2 or 5 single quotes
        q = "(?<!')(?:'{2}|'{5})(?!')"

        m = re.match(fr"[;:, ]*({q}.+?{q})(?:\s*\(novel\)\s*)?[;:,. ]*(.*)$", text)
        if not m:
            return "", text

        # If the title is followed by another title, the following is a subtitle
        title = m.group(1)[2:-2]
        subtitle, post_text = cls.get_title(m.group(2))
        if subtitle:
            return f"{title}: {subtitle}", post_text

        return title, m.group(2)


    @staticmethod
    def is_valid_publisher(text):

        if text.startswith("[") and text.endswith("]"):
            return True

        if text.startswith("{{w|") and text.endswith("}}"):
            return True

        bad_items = [r'''[:ə"“”()<>\[\]\d]''', "''",  r"\b(page|by|published|reprint|edition|ed\.|p\.)\b", r"\d{4}"]
        pattern = "(" +  "|".join(bad_items) + ")"
        if re.search(pattern, text):
            return False
        return True

    @classmethod
    def get_publisher(cls, text):

        # The publisher is all text after the title until the ISBN tag

        m = re.match(r"[(;:., ]*(.*?)[;:, ]*(\(?{{ISBN.*)$", text)
        if m and m.group(1):

            publisher = m.group(1).strip()
            publisher = re.sub(r"\s+([Pp]aperback\s*)?[Ee]d(ition|\.)$", "", publisher)

            pattern = r"""(?x)
               [,|\(\s]*               # optional separator
               (\d{4})                 # date
               \s*
               (?:([Rr]eprint|[Pp]aperback))?         # optionally followed by reprint
               [);,.\s]*
               """

            mp = re.match(pattern, publisher)
            if not mp:
                mp = re.search(pattern + "$", publisher)

            published_year = None
            if mp:
                published_year = mp.group(1)
                publisher = publisher.replace(mp.group(0), "").strip()

            location = None
            if ":" in publisher:
                location, _, l_publisher = publisher.partition(":")
                location = location.strip()

                if location in [ "Baltimore", "London", "Toronto", "New York", "Dublin", "Washington, DC", "Nashville", "Montréal", "[[Paris]]", "[[Lausanne]]", "New York, N.Y." ]:
                    publisher = l_publisher.strip()
                else:
                    dprint("unknown location:", location)
                    location = None

            publisher = re.sub(r"\s*\(publisher\)$", "", publisher)
            publisher = re.sub(r"^published by( the)?", "", publisher)

            if not cls.is_valid_publisher(publisher):
                dprint("bad publisher", publisher)
                return None, None, None, text

            return publisher, published_year, location, m.group(2)
        return "", None, None, text


    @staticmethod
    def get_isbn(text):

        # Find ISBN templates
        pattern = r"""(?x)
            ^[;:, ]*(?P<pre>.*?)\s*         # leading text
            \(?                             # option (
            {{ISBN\s*\|\s*                  # {{ISBN|
            ([0-9-X ]+)                     # numbers, -, and X
            \s*}}                           # }}
            \)?                             # optional )
            [;:, ]*(?P<post>.*)$            # trailing text
        """

        isbn = []
        while True:
            m = re.match(pattern, text)
            if not m:
                break
            isbn.append(m.group(2).replace(" ", ""))
            text = m.group('pre') + " " + m.group('post')


        # Find bare ISBN numbers
        pattern = r"""(?x)
            ^[;:, ]*(?P<pre>.*?)            # leading text
            [ ;:,(]\s*                      # separator
            (978(-)?[0-9]{10})              # ISBN
            [ ;:,)]\s*                      # separator
            [;:, ]*(?P<post>.*)$            # trailing text
        """

        while True:
            m = re.match(pattern, text)
            if not m:
                break
            isbn.append(m.group(2).replace(" ", ""))
            text = m.group('pre') + " " + m.group('post')


        return isbn, text

    @staticmethod
    def get_oclc(text):

        pattern = r"""(?x)
            ^[;:, ]*(?P<pre>.*?)\s*         # leading text
            \(?                             # option (
            {{OCLC\s*\|\s*                  # {{OCLC|
            ([0-9-]+)                       # numbers
            \s*}}                           # }}
            \)?                             # optional )
            [;:, ]*(?P<post>.*)$            # trailing text
        """

        m = re.match(pattern, text)
        if m:
            return m.group(2), m.group('pre') + " " + m.group('post')
        return "", text

    @staticmethod
    def get_url(text):

        pattern = r"""(?x)
            ^[;:, ]*(?P<pre>.*?)\s*         # leading text
            \[                              # [
            (http[^ ]*)                     # url
            (?P<link_text> .*?)?            # link text
            \]                              # ]
            [;:, ]*(?P<post>.*)$            # trailing text
        """
        m = re.match(pattern, text)
        if m:
            return m.group(2), m.group('pre') + m.group('link_text') + " " + m.group('post')

        return "", text

    @staticmethod
    def get_gbooks(text):

        pattern = r"""(?x)
            ^[;:, ]*(?P<pre>.*?)\s*         # leading text
            ({{gbooks.*?}})                 # gbooks template
            [;:, ]*(?P<post>.*)$            # trailing text
        """
        m = re.match(pattern, text)
        if m:
            return m.group(2), m.group('pre') + " " + m.group('post')

        return "", text

    @staticmethod
    def get_page(text):
        pattern = r"""(?x)
            ^[;:, ]*(?P<pre>.*?)\s*         # leading text
            \b                              # hard separator
            (?:[Pp]age|pg\.|p\.|p)          # page, pg, p., or p
            (?:&nbsp;|\s*)+                 # whitespace
            ([0-9ivxcdmIVXCDM]+)            # numbers or roman numerals
            [;:, ]*(?P<post>.*)$            # trailing text
        """
            #([0-9ivxcdmIVXCDM]+)            # numbers or roman numerals

        m = re.match(pattern, text)
        if m:
            return m.group(2), m.group('pre') + " " + m.group('post')
        return "", text


    @staticmethod
    def get_pages(text):

        pattern = r"""(?x)
            ^[;:, ]*(?P<pre>.*?)\s*             # leading text
            (?:[Pp]age[s]*|pp\.)                   # Pages or pp.
            (?:&nbsp;|\s*)*                     # optional whitespace
            (\d+                                # first number
            \s*(?:,|-|–|&|and|to|{{ndash}})+\s*   # mandatory separator(s)
            \d+)                                # second number
            [;:, ]*                             # trailing separator or whitespace
            (?P<post>.*)                        # trailing text
        """

        m = re.match(pattern, text)
        if m:
            return m.group(2), m.group('pre') + " " + m.group('post')
        return "", text


    @staticmethod
    def get_edition(text):
        pattern = r"""(?x)
            ^[(;:, ]*(?P<pre>.*?)\s*         # leading text
            ((
                \d{4}                       # year
                |[Tt]raveller's
                |[Ii]llustrated
                |[Pp]aperback
                |[Hh]ardcover
                |[Ss]oftcover
                |[Rr]evised
                |[Rr]eprint
                |[Ll]imited
                |\d+(?:st|nd|rd|th)         # ordinal number
            )\s*)+
            \s*
            (?:[Ee]dition|[Ee]d\.)
            [);:, ]*(?P<post>.*)$            # trailing text
        """

        m = re.match(pattern, text)
        if m:
            return m.group(2).strip(), m.group('pre') + " " + m.group('post')

        return "", text


    @staticmethod
    def get_volume(text):
        pattern = r"""(?x)
            ^[;:, ]*(?P<pre>.*?)\s*         # leading text
            (?:[Vv]olume|vol\.|vol )        # page, pg., or p. optionally followed by whitespace
            (?:&nbsp;|\s*)+                 # whitespace
            ([0-9ivxcdmIVXCDM]+)            # numbers or roman numerals
            [;:, ]*(?P<post>.*)$            # trailing text
        """

        m = re.match(pattern, text)
        if m:
            return m.group(2), m.group('pre') + " " + m.group('post')
        return "", text


    @staticmethod
    def get_chapter(text):

        pattern = r"""(?x)
            ^[;:, ]*(?P<pre>.*?)\s*         # leading text
            (?:[Cc]hapter|ch\.)             # chapter or ch. followed by whitespace
            (?:&nbsp;|\s*)+                 # whitespace
            ([0-9ivxcdmIVXCDM]+)            # numbers or roman numerals
            [;:, ]*(?P<post>.*)$            # trailing text
        """

        m = re.match(pattern, text)
        if m:
            return m.group(2), m.group('pre') + " " + m.group('post')
        return "", text


    @classmethod
    def parse_details(cls, text):

        # This assumes details are listed in the following order
        # '''YEAR''', Author 1, Author 2, ''Title of work'', Publisher (ISBN)
        # Authors and Publish are optional
        # After the fixed details, the following details are all optional and
        # may occurr in any order:
        # (OCLC) page 1, chapter 2,

        #if "quoted" in text or "comic" in text or "&quot;" in text or "<!--" in text or "-->" in text:
        if "<!--" in text or "-->" in text:
            return

        orig_text = text
        details = {}

        text = re.sub(r"<\s*/?\s*sup\s*>", "", text)
        text = text.replace('<span class="plainlinks">', "")
        text = text.replace('</span>', "")
        text = text.replace('<small>', "")
        text = text.replace('</small>', "")
        text = text.replace('{{,}}', ",")

        year, text = cls.get_year(text)
        details["year"] = year

        translator, text = cls.get_translator(text)
        if translator:
            details["translator"] = translator

        editor, text = cls.get_editor(text)
        if editor:
            details["editor"] = editor

        authors, text = cls.get_authors(text)
        for count, author in enumerate(authors, 1):
            key = f"author{count}" if count > 1 else "author"
            details[key] = author

        chapter_title, text = cls.get_chapter_title(text)
        if chapter_title:
            details["chapter"] = chapter_title

        title, text = cls.get_title(text)
        if not title:
            dprint("no title", text)
            return
        details["title"] = title

        # url may contain the text like 'page 123' or 'chapter 3', so it needs to be extracted first
        url, text = cls.get_url(text)
        gbooks, text = cls.get_gbooks(text)

        # get pages before page because pp. and p. both match  pp. 12-14
        pages, text = cls.get_pages(text)
        page, text = cls.get_page(text)
        chapter, text = cls.get_chapter(text)
        volume, text = cls.get_volume(text)
        if volume:
            details["volume"] = volume
        edition, text = cls.get_edition(text)
        if edition:
            if edition.isnumeric() and len(edition) == 4:
                details["year_published"] = edition
            else:
                details["edition"] = edition

        if gbooks:
            page = gbooks

        if url:
            if "books.google" in url:
                if page or pages:
                    details["pageurl"] = url
                elif chapter:
                    details["chapterurl"] = url
                else:
                    details["url"] = url
            else:
                details["url"] = url

        if chapter:
            details["chapter"] = chapter

        if page:
            details["page"] = page

        if pages:
            details["pages"] = pages

        # Parse publisher after removing page, chapter, and volume info

        publisher, year_published, location, text = cls.get_publisher(text)
        if publisher is None:
            return
        if publisher:
            details["publisher"] = publisher

        if year_published and year_published != year:
            details["year_published"] = year_published

        if location:
            details["location"] = location


        isbn, text = cls.get_isbn(text)
        if isbn:
            for count, isbn in enumerate(isbn, 1):
                key = f"isbn{count}" if count > 1 else "isbn"
                details[key] = isbn
        else:
            print("NO ISBN FOUND")
            print(details)
            print(text)
            return

        oclc, text = cls.get_oclc(text)
        if oclc:
            details["oclc"] = oclc

        text = re.sub(r"(\(novel\)|&nbsp|Google online preview|Google [Pp]review|Google snippet view|online|preview|Google search result|unknown page|unpaged|unnumbered page(s)?|online edition|unmarked page|no page number|page n/a|Google books view|Google [Bb]ooks)", "", text)
        text = text.strip('#*:;, ()".')
        if page:
            text = re.sub(r"([Pp]age(s)?|pp\.|p\.|pg\.)", "", text)
        if text:
            dprint("unparsed text:", text)
            dprint(orig_text)
            dprint("")
            return

        return details


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


    def convert_book_quotes(self, section, title):

        lang_id = ALL_LANGS.get(section._topmost.title)
        if not lang_id:
            return

        pattern = r"""([#:*]+)\s*(?P<details>'''\d{4}'''.*{{ISBN.*)$"""

        changed = False
        to_remove = []
        for idx, line in enumerate(section._lines):
            m = re.match(pattern, line)
            if not m:
                continue
            start = m.group(1)

            params = self.parse_details(m.group('details'))
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
                    passage_lines.append(section._lines[idx+offset])

                elif re.match(re.escape(start) + "::[^:]", section._lines[idx+offset]):
                    if not passage_lines:
                        self.warn("translation_before_passage", section, section._lines[idx+offset])
                    translation_lines.append(section._lines[idx+offset])

                else:
                    self.warn("unhandled_following_line", section, section._lines[idx+offset])
                    failed = True

                offset += 1

            if failed:
                continue

            res = self.get_passage(passage_lines, section)
            if not res:
                continue
            passage, translation1 = res

            translation2 = self.get_translation(translation_lines)
            if translation1 and translation2:
                self.warn("multi_translations", section, translation + " ----> " + translation2)
            else:
                translation = translation1 if translation1 else translation2

            if "|" in translation:
                self.warn("pipe_in_translation", section, translation)
                return


            if translation and not passage:
                self.warn("translation_without_passage", section, section.path)
                continue

            if not passage:
                # TODO: convert to cite-book instead of quote-book
                self.warn("no_following_line", section, section.path)
                continue

            if lang_id == "en" and translation:
                self.warn("english_with_translation", section, translation)
                continue

            section._lines[idx] = start + " {{quote-book|" + lang_id + "|" + "|".join([f"{k}={v}" for k,v in params.items()])
            if translation2:
                section._lines[idx+1] = "|passage=" + passage
                section._lines[idx+2] = "|translation=" + translation + "}}"
            elif translation1:
                section._lines[idx+1] = "|passage=" + passage + "|t=" + translation + "}}"
            else:
                section._lines[idx+1] = "|passage=" + passage + "}}"

            used = 3 if translation2 else 2
            for to_remove_idx in range(idx+used, idx+offset):
                to_remove.append(to_remove_idx)

            changed = True

        for idx in reversed(to_remove):
            del section._lines[idx]

        return changed


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
            if self.convert_book_quotes(section, title):
                self.fix("bare_quote", section, "converted bare quote to quote-book")

        return self._log if summary is None else str(entry)
