import enwiktionary_sectionparser as sectionparser
from autodooz.sections import ALL_LANGS
import re
import sys
from enwiktionary_parser.utils import nest_aware_split


class QuoteFixer():

    def dprint(self, *args, **kwargs):
        if self.debug:
            print(args, kwargs, file=sys.stderr)

    def __init__(self, debug=False):
        self._summary = None
        self._log = []
        self.debug=debug

    def fix(self, code, section, details):
        if self._summary is not None:
            self._summary.append(f"/*{section.path}*/ {details}")

        page = list(section.lineage)[-1]
        self._log.append(("autofix_" + code, page))

    def warn(self, code, section, details=None):
        page = list(section.lineage)[-1]
        self._log.append((code, page, details))

    def get_year(self, text):
        m = re.match(r"^'''(\d{4})'''[\.;,:—\- ]*(.*)$", text)
        if not m:
            self.dprint(text)
            return 

        return m.group(1), m.group(2)


    def get_translator(self, text):
        translator, text = self.get_prefixed_translator(text)
        if translator:
            return translator, text

        return self.get_suffixed_translator(text)

    def get_prefixed_translator(self, text):

        pattern = r"""(?x)
            ^[;:, ]*(?P<pre>.*?)\s*         # leading text
            \(?(?:tr\.|trans\.|translated)\s*(?:by)?\s*
            (.*?)
            [),]                            # must end with a ) or ,
            [;:, ]*(?P<post>.*)$            # trailing text
        """

        m = re.match(pattern, text)
        if m:
            if not self.is_valid_name(m.group(2)):
                self.dprint("invalid translator:", m.group(2))
                return "", text

            return m.group(2), m.group('pre') + " " + m.group('post')
        return "", text


    def get_suffixed_translator(self, text):
        pattern = r"""(?x)
            ^(?P<pre>.*?)\s*         # leading text
            (?:^|[;:,])\s*           # beginning of line or separator
            ([^,]*?)\s*              # name
            \(translator\)
            [;:, ]*(?P<post>.*)$     # trailing text
        """

        m = re.match(pattern, text)
        if m:
            if not self.is_valid_name(m.group(2)):
                self.dprint("***************** invalid translator:", m.group(2))
                return "", text

            return m.group(2), m.group('pre') + " " + m.group('post')
        return "", text


    def get_editor(self, text):

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
                (?:\(eds[.]{0,1})\s+     # (eds.
                (.*?)                    # names
                [)]\s*                   # )
                (?P<post>.*)$            # trailing text
            """
            m = re.match(pattern, text)

        if not m:
            return [], text

        pub_names = self.split_names(m.group(2))
        if pub_names is None:
            print("BAD EDITOR NAME", text)
            return [], text

        names = []
        for name in pub_names:
            if not self.is_valid_name(name):
                self.dprint("invalid editor:", name)
                return [], text
            names.append(name)

        return "; ".join(names), m.group('pre') + " " + m.group('post')


    @staticmethod
    def is_valid_name(text):

        if not text:
            return False

        if text.startswith("[") and text.endswith("]"):
            return True

        if text.startswith("{{w|") and text.endswith("}}"):
            return True

        if text[0] in " .;:-" or text[-1] in " ;:-":
            return False

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
        s = re.search("(( and| &|,|;) )", text)
        separator = s.group(1) if s else ", "

        names = []
        for name in nest_aware_split(separator, text, [("{{","}}"), ("[[","]]")]):
            name = name.strip()
            if name.startswith("and "):
                name = name[4:]
            if name.startswith("& "):
                name = name[2:]
            if not name:
                continue

            if re.match(r"(Jr|MD|PhD|MSW|JD|II|III|IV|jr|MS|PHD|Sr)\.?\b", name, re.IGNORECASE):
                if not names:
                    return None

                names[-1] += f", {name}"
                continue

            names.append(name)

        return names

    def classify_names(self, names):
        """
        ["John Doe (author)", "Jane Doe (translator)", "Ed One", "Ed Two (eds.)"] => {"author": ["John Doe"], "translator": ["Jane Doe"], "editor": ["Ed One", "Ed Two"]}
        """

        res = {}
        buffer = []
        default = "author"
        for name in names:
            m = re.match(r"(?P<name>[^(]*?)\s+(?P<label>\(?([Aa]ut(hor)?|[Ee]d(itor)?|[Tt]r(anslator)?)s?\.?\))", name)
            if not m:
                buffer.append(name)
                continue

            label = m.group("label").lower().strip("().")

            new_name = m.group("name").strip()
            if new_name:
                buffer.append(new_name)

            # If the label isn't plural, it only applies to the last item in the buffer
            # Anything else in the buffer should be labeled with the default
            if not label.endswith("s"):
                name = buffer.pop()
                if buffer:
                    if default in res:
                        # Duplicate job label
                        return
                    res[default] = buffer
                buffer = [name]

            if label.startswith("au"):
                job_type = "author"
            elif label.startswith("ed"):
                job_type = "editor"
            elif label.startswith("tr"):
                job_type = "translator"

            # Stray label
            if not buffer:
                return

            if job_type in res:
                # Duplicate job label
                return

            res[job_type] = buffer
            buffer = []


        if buffer:
            if default in res:
                return
                # Duplicate job label
                raise ValueError(res, default, buffer)
            res[default] = buffer


        for k, names in res.items():
            valid_names = []
            has_et_al = False
            for name in names:
                new_name = re.sub(r"(''|\b)(et|&) al((ii|\.)''(.)?|[.,]|$)", "", name)
                if new_name != name:
                    has_et_al=True
                    name = new_name.strip()
                    if not name:
                        continue

                if not self.is_valid_name(name):
                    self.dprint(f"invalid {k} name:", name)
                    return

                valid_names.append(name)

            if has_et_al:
                valid_names.append("et al")

            res[k] = valid_names

        return res


    def get_classified_names(self, text):
        m = re.match("""(.+?) (?P<post>("|''|“).*)$""", text)
        if not m:
            return {}, text

        author_text = m.group(1).strip(":;, ").replace("&#91;", "")

        # Check if the remaining text starts with ''et al''
        alt_m = re.match(r"\s*(''|[;, ]+)et al((ii|\.)''(.)?|[.,])\s*(?P<post>.*)$", m.group('post'))
        if alt_m:
            author_text = author_text.rstrip(", ") + ", et al."
            m = alt_m

        names = self.split_names(author_text)
        if not names:
            return {}, text
        classified_names = self.classify_names(names)

        if classified_names:
            return classified_names, m.group('post')

        return {}, text


    def get_authors(self, text):
        authors = []

        orig_text = text

        has_et_al = False
        text = re.sub(r"(''|[;, ]+)et al((ii|\.)''(.)?|[.,])", "", text)
        if text != orig_text:
            has_et_al = True

        m = re.match("""(.+?) (("|''|“).*)$""", text)
        if not m:
            return [], orig_text

        author_text = m.group(1).strip(":;, ").replace("&#91;", "").replace(" (author)", "")

        authors = []
        author_names = self.split_names(author_text)
        if author_names is None:
            print("BAD AUTHOR NAME", text)
            return [], orig_text

        for author in author_names:
            if not self.is_valid_name(author):
                self.dprint("invalid author:", author)
                return [], orig_text
            authors.append(author)

        if not authors:
            return [], orig_text

        if has_et_al:
            authors.append("et al")

        return authors, m.group(2)

    @staticmethod
    def get_chapter_title(text):
        # The chapter title is the first string closed in " " or “” possibly followed by "in"
        pattern = r"""(?x)
            [;:, ]*                 # separator
            [“"](.+?)["”]           # title enclosed in quotes
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
            ''(.+?)''               # title enclosed in quotes
            [;:, ]+                 # separator
            in                      # in
            [;:, ]+                 # separator
            (?P<post>.*)$           # trailing text
        """

        m = re.match(pattern, text)
        if m:
            return m.group(1), m.group('post')

        return "", text


    def get_title(self, text):
        # The title is the first string closed in '' '' possibly followed by (novel)

        # match exactly 2 or 5 single quotes
        q = "(?<!')(?:'{2}|'{5})(?!')"

        m = re.match(fr"[;:, ]*({q}.+?{q})(?:\s*\(novel\)\s*)?[;:,. ]*(.*)$", text)
        if not m:
            return "", text

        # If the title is followed by another title, the following is a subtitle
        title = m.group(1)[2:-2]
        subtitle, post_text = self.get_title(m.group(2))
        if subtitle:
            return f"{title}: {subtitle}", post_text

        return title, m.group(2)

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

    def get_journal_title(self, text):
        # The title is everything until the first ; or ,

        m = re.match(r"[.;:, ]*(?P<title>[^.;,]*)[;:,. ]*(?P<post>.*)$", text)
        if m and self.is_valid_title(m.group("title")):
            return m.group('title'), m.group('post')

        return "", text

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

    def get_publisher(self, text):

#        print("get publisher", [text])

        # The publisher is all text after the title until the ISBN/OCLC/ISSN tag

        #m = re.match(r"[(;:., ]*(.*?)[;:, ]*(\(?{{(?:ISBN|OCLC|ISSN).*)$", text)
        m = re.match(r"[(;:., ]*(.*?)[;:, ]*(\(?{{(?:ISBN|OCLC|ISSN).*)?$", text)
        if m and m.group(1):

            publisher = m.group(1).strip(";:, ")
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
            locations = list(nest_aware_split(":", publisher, [("{{","}}"), ("[","]")]))
            location = locations[0].strip("()")
            if location in [ "Ourense", "A Coruña", "UK", "Canada", "Baltimore", "London", "Toronto", "New York", "Dublin", "Washington, DC", "Nashville", "Montréal", "[[Paris]]", "[[Lausanne]]", "New York, N.Y.",
                    "Santiago", "Santiago de Compostela", "Boston", "Vigo", "Madrid", "Philadelphia", "Ourense", "Edinburgh", "Garden City, NY", "Sada / A Coruña", "Coimbra", "Chicago", "Oxford", "Erich Mühsam", "Pontevedra", "San Francisco", "Oviedo", "Indianapolis", "Cambridge", "Valga", "New York and London", "Sydney", "Leipzig", "Bauzten" ]:
                publisher = ":".join(locations[1:]).strip()
            else:
                if len(locations) > 1:
                    self.dprint("unknown location:", location)
                location = None

            publisher = re.sub(r"\s*\(publisher\)$", "", publisher)
            publisher = re.sub(r"^published by( the)?", "", publisher)

            if not publisher.strip("/():;, "):
                if location in ["Oxford"]:
                    publisher = location
                    location = None
                else:
                    publisher = ""

            if not self.is_allowed_publisher(publisher) and not self.is_valid_publisher(publisher):
                self.dprint("bad publisher", publisher)
                return None, None, None, text

            # Group2 matches ISBN templates, which is a good sign the publisher data is valid
            if m.group(2):
                return publisher, published_year, location, m.group(2)

            # If there was no ISBN template, the publisher text is less reliable,
            # only pass if the publisher exactly matches an allowlist
            elif not publisher or self.is_allowed_publisher(publisher):
                return publisher, published_year, location, ""

        return "", None, None, text

    def is_allowed_publisher(self, text):
        return text in [
"I.E.O.P.F.",
"Fundación Barrié",
"UK",
"Modern Library",
"Oxford",
"John Macock",
"Pan Macmillan",
"Pocket Books",
"{{w|Ballantine Books}}",
"[[w:Bauer Media Group|Bauer Media]]",
"{{w|Bloomsbury Publishing}}",
"{{w|Chuokoron-Shinsha",
"{{w|Time Inc.}}",
"{{w|University of Texas Press}}",
"il Mulino",
"Samlaget",
"University of Michigan Press",
"Bantam",
"Indiana University Press",
"Klim",
"Modtryk",
"University of Illinois Press",
"University of Toronto Press",
"{{w|Farrar, Straus and Giroux}}",
"Ballantine Books",
"Chatto & Windus",
"Courier Corporation",
"H. John Edwards",
"[[w:Houghton Mifflin Harcourt|Houghton Mifflin Company]]",
"{{w|Lulu.com}}",
"{{w|National Institute of the Korean Language}}",
"Rex Bookstore, Inc.",
"SUNY Press",
"{{w|John Benjamins Publishing Company}}",
"Edizioni Scientifiche e Artistiche",
"Farrar, Straus and Giroux",
"Government Printing Office",
"Grosset & Dunlap",
"Johns Hopkins University Press",
"University of Hawai‘i Press",
"[[w:Farrar, Straus and Giroux|Farrar, Straus and Giroux]]",
"{{w|Indiana University Press}}",
"{{w|Rowman & Littlefield}}",
"Cornell University Press",
"SAGE",
"Salavopoulos & Kinderlis",
"U.S. Government Printing Office",
"{{w|John Wiley & Sons}}",
"Adams Media",
"Cambridge Scholars Publishing",
"Fleet",
"Kyobunkan",
"Printed by [[w:William Jaggard|Isaac Iaggard]], and [[w:Edward Blount|Ed[ward] Blount]]",
"{{w|Elsevier}}",
"Wiley",
"NYU Press",
"Puffin Books",
"Oxford University Press",
"University of Utah Press",
"Lulu Press, Inc",
"Picador",
"Vintage Books",
"{{w|Bantam Books}}",
"World Health Organization}}",
"Filipiniana Publications",
"Hachette",
"OUP Oxford",
"Uchitel Publishing House",
"W. W. Norton & Company",
"[[w:Charles Scribner's Sons|Scribner]]",
"[[w:Macmillan Publishers|Macmillan and Co.]]",
"Xlibris",
"Greenwood Press",
"Grove Press",
"McFarland & Company",
"Packt Publishing Ltd",
"[[w:St. Martin's Press|St. Martin’s Press]]",
"Granta Books",
"Greenwood Publishing Group",
"Harper",
"{{w|Ian Allan Publishing}}",
"[[w:Springer Science+Business Media|Springer-Verlag]]",
"Institut d'ethnologie",
"Lexington Books",
"{{w|Pocket Books}}",
"De La Salle University Press",
"Einaudi",
"ราชบัณฑิตยสถาน",
"Academic Press",
"Faber & Faber",
"Gummerus",
"Otava",
"Arnoldo Mondadori Editore",
"BBC",
"Langenscheidt Verlag",
"Bamavarma & Bros",
"Siglo Veintiuno Editores",
"สำนักเลขาธิการคณะรัฐมนตรี",
"Apress",
"Black Swan (2020)",
"A&C Black",
"Bantam Books",
"Editora regional da Extremadura",
"Folio Society",
"Open Road Media",
"Tammi",
"Psychology Press",
"Orbit",
"Société Internationale de Linguistique (SIL)",
"Springer Nature",
"{{w|Alfred A. Knopf}}",
"Elsevier Health Sciences",
"Penguin Books",
"Scribner",
"{{w|McFarland & Company}}",
"Harper & Brothers",
"John Benjamins Publishing Company",
"Scripts",
"BRILL",
"Linguistic Data Consortium",
"Trafford Publishing",
"{{w|Little, Brown and Company}}",
"[[w:Springer Science+Business Media|Springer]]",
"มติชน",
"Palgrave Macmillan",
"Doubleday",
"Viking",
"Motilal Banarsidass Publishing House",
"{{w|CRC Press}}",
"{{w|Harvard University Press}}",
"Foris}}",
"Partridge Publishing Singapore",
"University of Hawaii Press",
"{{w|Princeton University Press}}",
"Henry Holt and Company",
"Houghton Mifflin Harcourt",
"Springer-Verlag",
"The Gutenberg Project",
"O'Reilly Media",
"ABC-CLIO",
"MIT Press",
"Penguin UK",
"{{w|Academic Press}}",
"WSOY",
"Museum Tusculanum Press",
"Rosinante & Co",
"Harvard University Press",
"James R. Osgood, McIlvaine and Co.",
"Clarendon Press",
"Eastern Horizon Press",
"{{w|Random House}}",
"Yale University Press",
"University of Chicago Press",
"McFarland",
"Language Science Press",
"[[w:United States Government Publishing Office|U.S. Government Printing Office]]",
"{{w|iUniverse}}",
"Fourth Estate",
"LG Evergreen Foundation",
"University of California Press",
"Walter de Gruyter",
"Elsevier",
"[[w:United States Government Publishing Office|United States Government Printing Office]]",
"{{w|University of Chicago Press}}",
"Vintage",
"[[w:ja:大学書林|Daigakushorin]]",
"J. L. Cox & Son",
"University of Michigan",
"Hamish Hamilton",
"Harlequin",
"Politikens Forlag",
"Simon & Schuster",
"Gyldendal Uddannelse",
"Bloomsbury Publishing",
"Knopf",
"Taylor & Francis",
"{{w|AuthorHouse}}",
"Editorial Porrúa",
"Columbia University Press",
"Siglo Veintiuno Editores",
"{{w|Palgrave Macmillan}}",
"Little, Brown and Company",
"{{w|Simon & Schuster}}",
"[[w:United States Government Publishing Office|Government Printing Office]]",
"{{w|Penguin Books}}",
"F. A. Davis Company",
"Sdu Uitgevers",
"{{w|University of California Press}}",
"Allen and Unwin",
"Princeton University Press",
"{{w|The New York Times Company}}",
"Le Monnier",
"Atuakkiorfik",
"St. Martin's Press",
"Brill",
"Instituto Lingüístico de Verano",
"National African Language Resource Center",
"Instituto Lingüístico de Verano, A.C.",
"Rowman & Littlefield",
"Kodansha",
"American Mission Press",
"Bloomsbury",
"Art People",
"{{lj|青空文庫}}",
"สำนักงานคณะกรรมการกฤษฎีกา",
"Mondadori",
"William Heinemann",
"Pusat Pembinaan dan Pengembangan Bahasa, Departemen Pendidikan dan Kebudayaan",
"Mondial",
"{{w|Xlibris}}",
"CRC Press",
"Hachette UK",
"Profile Books",
"Macmillan",
"Xlibris Corporation",
"University of Texas Press",
"BoD – Books on Demand",
"Garzanti Libri",
"HarperCollins",
"[[w:Guardian Media Group|Guardian News & Media]]",
"Kyo-Hak Publishing",
"University of Queensland Press",
"Long",
"AuthorHouse",
"Pacific Linguistics, Research School of Pacific and Asian Studies, The Australian National University",
"Shueisha",
"Springer Science & Business Media",
"Lulu.com",
"Stanford University Press",
"Random House",
"Shogakukan",
"SIL International",
"{{w|Cambridge University Press}}",
"iUniverse",
"University of Oklahoma Press",
"Rider/Hutchinson & Co.",
"{{w|Routledge}}",
"Springer",
"{{w|Oxford University Press}}",
"John Wiley & Sons",
"Simon and Schuster",
"Electronic Arts",
"Penguin",
"Lindhardt og Ringhof",
"Gyldendal A/S",
"Oxford University Press",
"Cambridge University Press",
"{{w|Columbia University Press}}",
"Editorial Porrúa",
"Routledge"]

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
    def get_issn(text):

        pattern = r"""(?x)
            ^[;:, ]*(?P<pre>.*?)\s*         # leading text
            \(?                             # option (
            {{ISSN\s*\|\s*                  # {{ISSN|
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
    def get_url(text, keep_text=False):

        pattern = r"""(?x)
            ^[;:, ]*(?P<pre>.*?)\s*         # leading text
            \[                              # [
            (?P<link>http[^ ]*)             # url
            (?P<link_text> .*?)?            # link text
            \]                              # ]
            [;:, ]*(?P<post>.*)$            # trailing text
        """
        m = re.match(pattern, text)
        if m:
            if keep_text:
                return m.group('link'), "", m.group('pre') + " " + m.group('link_text') + " " + m.group('post')
            else:
                return m.group('link'), m.group('link_text'), m.group('pre') + " " + m.group('post')

        return "", "", text

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
            (?P<num>[0-9ivxlcdmIVXLCDM]+)   # numbers or roman numerals
            [;:, ]*(?P<post>.*)$            # trailing text
        """
            #([0-9ivxcdmIVXCDM]+)            # numbers or roman numerals

        m = re.match(pattern, text)
        if m:
            return m.group('num'), m.group('pre') + " " + m.group('post')

        new_text = re.sub(r"\s*(unknown page|unpaged|unnumbered page(s)?|unmarked page|no page number|page n/a)\s*", " ", text)
        if new_text != text:
            return "unnumbered", new_text.strip()

        return "", text


    @staticmethod
    def get_pages(text):

        pattern = r"""(?x)
            ^[;:, ]*(?P<pre>.*?)\s*             # leading text
            (?:[Pp]age[s]*|pp\.)                # Pages or pp.
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
            (?:[Vv]ol(.|ume)?)              # Volume, vol. vol
            (?:&nbsp;|\s)+                  # whitespace
            (?P<num>[0-9ivxlcdmIVXLCDM]+)   # numbers or roman numerals
            [;:, ]*(?P<post>.*)$            # trailing text
        """

        m = re.match(pattern, text)
        if m:
            return m.group('num'), m.group('pre') + " " + m.group('post')
        return "", text


    @staticmethod
    def get_issue(text):
        pattern = r"""(?x)
            ^[;:, ]*(?P<pre>.*?)\s*         # leading text
            (?:[Ii]ssue)                    # issue
            (?:&nbsp;|\s*)+                 # whitespace
            (?P<num>[0-9ivxlcdmIVXLCDM]+)   # numbers or roman numerals
            [;:, ]*(?P<post>.*)$            # trailing text
        """

        m = re.match(pattern, text)
        if m:
            return m.group('num'), m.group('pre') + " " + m.group('post')
        return "", text


    @staticmethod
    def get_number(text):
        pattern = r"""(?x)
            ^[;:, ]*(?P<pre>.*?)\s*         # leading text
            (?:[Nn](o|um(ber)?)\.?)         # Number, Num, "no."
            (?:&nbsp;|\s)+                  # whitespace
            (?P<num>[0-9ivxlcdmIVXLCDM]+)   # numbers or roman numerals
            [;:, ]*(?P<post>.*)$            # trailing text
        """

        m = re.match(pattern, text)
        if m:
            return m.group('num'), m.group('pre') + " " + m.group('post')
        return "", text


    @staticmethod
    def get_chapter(text):

        pattern = r"""(?x)
            ^[;:, ]*(?P<pre>.*?)\s*         # leading text
            (?:[Cc]hapter|ch\.)             # chapter or ch. followed by whitespace
            (?:&nbsp;|\s*)+                 # whitespace
            (?P<num>[0-9ivxlcdmIVXLCDM]+)   # numbers or roman numerals
            [;:, ]*(?P<post>.*)$            # trailing text
        """

        m = re.match(pattern, text)
        if m:
            return m.group('num'), m.group('pre') + " " + m.group('post')
        return "", text

    @staticmethod
    def get_season_episode(text):
        pattern = r"""(?x)
            ^[;:, ]*(?P<pre>.*?)\s*         # leading text
            \b                              # hard separator
            s(\d{1,3})e(\d{1,3})             # s000e000
            \b                              # hard separator
            [;:, ]*(?P<post>.*)$            # trailing text
        """

        m = re.match(pattern, text)
        if m:
            return m.group(2), m.group(3), m.group('pre') + " " + m.group('post')
        return "", "", text


    @staticmethod
    def get_month_day(text):
        pattern = r"""(?x)
            \s*
            (?P<month>Jan(uary)?|Feb(ruary)?|Mar(ch)?|Apr(il)?|May|Jun(e)?|Jul(y)?|Aug(ust)?|Sep(tember)?|Oct(ober)?|Nov(ember)?|Dec(ember)?)
            [.,]*                           # dot or comma
            (\s+(?P<day>3[01]|[12][0-9]|0?[1-9]))   # 1-31
            \b                              # hard separator
            [;:, ]*(?P<post>.*)$            # trailing text
        """

        m = re.match(pattern, text)
        if m:
            return m.group('month'), int(m.group('day')), m.group('post')
        return "", "", text


    @staticmethod
    def get_month(text):
        pattern = r"""(?x)
            \s*
            (?P<month>Jan(uary)?|Feb(ruary)?|Mar(ch)?|Apr(il)?|May|Jun(e)?|Jul(y)?|Aug(ust)?|Sep(tember)?|Oct(ober)?|Nov(ember)?|Dec(ember)?)
            [.,]+                           # dot or comma
            [;:, ]*(?P<post>.*)$            # trailing text
        """

        m = re.match(pattern, text)
        if m:
            return m.group('month'), m.group('post')
        return "", text


    @staticmethod
    def get_season(text):
        pattern = r"""(?x)
            ^[;:, ]*(?P<pre>.*?)\s*         # leading text
            (?:[Ss]eason)                   # Season
            (?:&nbsp;|\s*)+                 # whitespace
            (?P<num>[0-9ivxlcdmIVXLCDM]+)   # numbers or roman numerals
            [;:, ]*(?P<post>.*)$            # trailing text
        """

        m = re.match(pattern, text)
        if m:
            return m.group('num'), m.group('pre') + " " + m.group('post')
        return "", text


    @staticmethod
    def get_episode(text):
        pattern = r"""(?x)
            ^[;:, ]*(?P<pre>.*?)\s*         # leading text
            (?:[Ee]p(?:isode|\.))           # Ep. or Episode
            (?:&nbsp;|\s*)+                 # whitespace
            (?P<num>[0-9ivxlcdmIVXLCDM]+)   # numbers or roman numerals
            [;:, ]*(?P<post>.*)$            # trailing text
        """

        m = re.match(pattern, text)
        if m:
            return m.group('num'), m.group('pre') + " " + m.group('post')
        return "", text

    def get_date_retrieved(self, text):
        pattern = r"""(?x)
            ^[;:, ]*(?P<pre>.*?)\s*         # leading text
            \(retrieved
            \s
            (?P<date>.*?)
            \)
            [;:, ]*(?P<post>.*)$            # trailing text
            """

        m = re.match(pattern, text)
        if m:
            retrieved = m.group('date').strip()
            year, month, day, trailing = self.get_date(retrieved)
            if not trailing.strip():
                return retrieved, m.group('pre') + " " + m.group('post')
            else:
                self.dprint("bad_retrieved", retrieved)

        return "", text


    @staticmethod
    def get_date(text):
        pattern = r"""(?x)
            ^[;:, ]*(?P<pre>.*?)\s*             # leading text
            ((?P<day1>3[01]|[12][0-9]|0?[1-9])\s+)?   # 1-31
            (?P<month>Jan(uary)?|Feb(ruary)?|Mar(ch)?|Apr(il)?|May|Jun(e)?|Jul(y)?|Aug(ust)?|Sep(t)?(ember)?|Oct(ober)?|Nov(ember)?|Dec(ember)?)
            [.,]*                           # dot or comma
            (\s+(?P<day2>3[01]|[12][0-9]|0?[1-9]))?   # 1-31
            ,*                              # comma
            (?:&nbsp;|\s*)+                 # whitespace
            ,*                              # comma
            (?P<year>\d{4})                 # YYYY
            [;:, ]*(?P<post>.*)$            # trailing text
        """

        m = re.match(pattern, text)
        if m:
            if m.group('day1'):
                day = int(m.group('day1'))*-1
            elif m.group('day2'):
                day = int(m.group('day2'))
            else:
                day = 0
            return m.group('year'), m.group('month'), day, m.group('pre') + " " + m.group('post')


        pattern = r"""(?x)
            ^[;:,]*(?P<pre>.*?)\b            # leading text
            (?P<year>\d{4})                  # Year
            \-                               # -
            (?P<month>0?[1-9]|1[012])        # Month
            \-                               # -
            (?P<day>3[01]|[12][0-9]|0?[1-9]) # Day
            \b[;:, ]*(?P<post>.*)$           # trailing text
        """
        m = re.match(pattern, text)
        if m:
            month = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][int(m.group('month'))-1]
            day = int(m.group('day'))
            if not (
                    (month == "Feb" and day>29)
                    or (month in ["Apr", "Jun", "Sep", "Nov"] and day>30)
                    ):
                return m.group('year'), month, day, m.group('pre') + " " + m.group('post')

        return None, None, None, text

    def parse_details(self, text):

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
        text = text.replace('{{nbsp}}', " ")
        text = text.replace('&nbsp;', " ")
#        text = text.replace("&#91;", "[")

        year, text = self.get_year(text)
        details["year"] = year

        month, day, text = self.get_month_day(text)
        if month and day:
             del details["year"]
             details["date"] = f"{month} {day} {year}"


        month, text = self.get_month(text)
        if month:
             details["month"] = month

        # TODO: get_retrieved


        translator, text = self.get_translator(text)
        editor, text = self.get_editor(text)

        names, text = self.get_classified_names(text)
        for count, author in enumerate(names.get("author",[]), 1):
            key = f"author{count}" if count > 1 else "author"
            details[key] = author

        if "editor" in names:
            if editor:
                self.dprint("multi editor")
                return
            if len(names["editor"]) > 1:
                details["editors"] = "; ".join(names["editor"])
            else:
                editor = names["editor"][0]
        if editor:
            details["editor"] = editor

        if "translator" in names:
            if translator:
                self.dprint("multi translator")
                return
            if len(names["translator"]) > 1:
                details["translators"] = "; ".join(names["translator"])
            else:
                editor = names["translator"][0]
        if translator:
            details["translator"] = translator

        chapter_title, text = self.get_chapter_title(text)
        title, text = self.get_title(text)

        if not title:
            if chapter_title and "author2" not in details: # Multiple authors is a sign that the publisher or other details may be included in authors
                title = chapter_title
                chapter_title = None
            else:
                self.dprint("no title", text)
                return

        if chapter_title:
            details["chapter"] = chapter_title.rstrip(", ")
            chapter_url, chapter_title, _ = self.get_url(chapter_title)
            if chapter_url:
                if _.strip():
                    self.dprint("chapter_url_posttext", _)
                    return
                details["chapterurl"] = chapter_url
                details["chapter"] = chapter_title.strip(", ")

        details["title"] = title.strip(", ")
        title_url, title, _ = self.get_url(title)
        if title_url:
            if _.strip():
                self.dprint("title_url_posttext", _)
                return
            details["url"] = title_url
            details["title"] = title.strip(", ")

        # url may contain the text like 'page 123' or 'chapter 3', so it needs to be extracted first
        url, _, text = self.get_url(text, True)

        gbooks, text = self.get_gbooks(text)

        # get pages before page because pp. and p. both match  pp. 12-14
        pages, text = self.get_pages(text)
        page, text = self.get_page(text)
        chapter, text = self.get_chapter(text)
        volume, text = self.get_volume(text)
        if volume:
            details["volume"] = volume

        issue, text = self.get_issue(text)
        if issue:
            details["issue"] = issue

        number, text = self.get_number(text)
        if number:
            details["number"] = number

        season, text = self.get_season(text)
        episode, text = self.get_episode(text)
        if not season and not episode:
            season, episode, text = self.get_season_episode(text)

        if season:
            details["season"] = season

        if episode:
            details["episode"] = episode

        edition, text = self.get_edition(text)
        if edition:
            if edition.isnumeric() and len(edition) == 4:
                details["year_published"] = edition
            else:
                details["edition"] = edition

        retrieved, text = self.get_date_retrieved(text)
        if retrieved:
            details["accessdate"] = retrieved

        _year, _month, _day, text = self.get_date(text)
        if _year:
            if _year != details.get("year"):
                self.dprint("mismatch year", text)
                return

            if _day:
                del details["year"]
                if _day < 0:
                    details["date"] = f"{_day*-1} {_month} {_year}"
                else:
                    details["date"] = f"{_month} {_day} {_year}"
            else:
                details["month"] = _month

        if gbooks:
            page = gbooks

        if url:
            if "books.google" in url or "google.com/books" in url:
                if page or pages:
                    details["pageurl"] = url
                elif chapter:
                    details["chapterurl"] = url
                else:
                    details["url"] = url
            else:
                details["url"] = url

        if sum(x in details for x in ["url", "chapterurl", "pageurl"]) > 1:
            #print("multiple_urls", orig_text)
            self.dprint("multiple_urls", text)
            return

        if chapter:
            if "chapter" in details:
                self.dprint("multiple chapter declarations", chapter, details)
                return
            details["chapter"] = chapter

        if page:
            details["page"] = page

        if pages:
            details["pages"] = pages

        # Parse publisher after removing page, chapter, and volume info

        publisher, year_published, location, text = self.get_publisher(text)
        if publisher is None:
            return

        if location:
            details["location"] = location

        if publisher:
            details["publisher"] = publisher

        if year_published and year_published != year:
            details["year_published"] = year_published



        isbn, text = self.get_isbn(text)
        if isbn:
            for count, isbn in enumerate(isbn, 1):
                key = f"isbn{count}" if count > 1 else "isbn"
                details[key] = isbn

        oclc, text = self.get_oclc(text)
        if oclc:
            details["oclc"] = oclc

        issn, text = self.get_issn(text)
        if issn:
            details["issn"] = issn

#        if not isbn and not oclc and not issn:
#            print("NO ISBN, OCLC, or ISSN FOUND")
#            print(details)
#            print(text)
#            return


        text = re.sub(r"(\(novel\)|&nbsp|Google online preview|Google [Pp]review|Google snippet view|online|preview|Google search result|unknown page|unpaged|unnumbered page(s)?|online edition|unmarked page|no page number|page n/a|Google books view|Google [Bb]ooks|Project Gutenberg transcription)", "", text)
        text = text.strip('#*:;, ()".')
        if page or pages:
            text = re.sub(r"([Pp]age(s)?|pp\.|p\.|pg\.)", "", text)

        if text:
            self.dprint("unparsed text:", text, details)
            self.dprint(orig_text)
            self.dprint("")
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


    def get_template_type(self, section):
        return "cite" if section.title in ["References", "Further reading", "Etymology"] else "quote"

    _journal_sites = ["telegraph.co.uk", "guardian.co.uk", "washingtonpost.com", "independent.co.uk", "nytimes.com", "time.com"]
    _journal_url_regex = "[/.]" + "|".join(x.replace(".", r"\.") for x in _journal_sites) + "/"


    def get_template_source(self, params):


        if any(x in params for x in ["isbn", "oclc", "issn"]):
            return "book"

        if any(x in params for x in ["season", "episode"]):
            return "av"

        # {'year': '1935', 'author': '{{w|Arthur Leo Zagat}}', 'chapter': 'IV', 'title': 'Dime Mystery Magazine', 'month': 'November', 'url': 'http://gutenberg.net.au/ebooks13/1304651h.html'}

        if any(x in params for x in ["issue", "number", "date", "month"]):  # "month" is over aggressive
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
        "journal": {
            # Old : New
            "title": "journal",
            "chapter": "title",
            "chapterurl": "titleurl",
            "url": "titleurl",
            "number": "issue",
            }
    }

    def get_source_adjusted_params(self, source, params):
        # Renames paramaters in params to match those used by "source" type templates
        rename = self._param_adjustments.get(source)
        if not rename:
            return params

        return {rename.get(k, k):v for k,v in params.items()}


    def convert_quotes(self, section, title):

        lang_id = ALL_LANGS.get(section._topmost.title)
        if not lang_id:
            return

        # Non-Book quotes start with four digit year and don't include ISBN or OCLC
        pattern = r"""([#:*]+)\s*(?P<details>'''\d{4}'''.*)$"""

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

            new_lines = self.get_new_lines(start, section, params, passage_lines, translation_lines)
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

    def get_new_lines(self, start, section, params, passage_lines, translation_lines):

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

        prefix = self.get_template_type(section)
        source = self.get_template_source(params)
        template = prefix + "-" + source

        params = self.get_source_adjusted_params(source, params)

        if source == "journal" and not all(x in params for x in ["journal", "title"]):
            self.dprint("incomplete journal entry")
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
