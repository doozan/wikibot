import enwiktionary_sectionparser as sectionparser
from autodooz.sections import ALL_LANGS
import re
import sys
from enwiktionary_parser.utils import nest_aware_split, nest_aware_resplit



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

    @staticmethod
    def strip_wrapper_templates(text, templates):
        old = ""
        while old != text:
            old = text
            # Strips simple wrappers, doesn't handle nested templates
            text = re.sub(r"{{\s*(" + "|".join(templates) + r")\s*\|([^|{{]*)}}", r"\2", text)

        return text

    def get_leading_year(self, text):
        m = re.match(r"^\s*'''(\d{4})'''[\.;,:—\- ]*(.*)$", text)
        if not m:
            self.dprint("NO YEAR", text)
            return None, None

        # Strip {{CE}} after year
        post_text = m.group(2)
        post_text = re.sub(r"^{{(CE|C\.E\.)[^}]*}}\s*", "", post_text)

        return m.group(1), post_text


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

        if text in ["María Francisca Isla y Losada",
                'Donatien Alphonse François de Sade',
'Diego Antonio Cernadas y Castro',
'United States. Congress. House. Committee on Appropriations',
'United States. Congress. House. Committee on Ways',
'Great Britain. Parliament. House of Commons',
'Homer',
'Edward Bulwer Lytton Baron Lytton',
'Canada. Parliament. House of Commons',
'Shakespeare',
]:
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

        if " " in text and "unknown" in text.lower():
            return False

        if " " not in text and text not in ["Various", "Anonymous", "anonymous", "Unknown", "unknown"]:
            return False

        return True

    @staticmethod
    def split_names(text):
        names = []
        for name, _ in nest_aware_resplit(r"(\bwith\b|\band\b|[&,;])", text, [("{{","}}"), ("[[","]]")]):
            name = name.strip()
            if not name:
                continue

            if re.match(r"(Jr|MD|PhD|MSW|JD|II|III|IV|jr|MS|PHD|Sr)\.?\b", name, re.IGNORECASE):
                if not names:
                    return None

                names[-1] += f", {name}"
                continue

            names.append(name)

        return names

    _classify_commands = {
        "(authors)": "<author",
        "(English author)": "!author",
        "(original author)": "!author",
#        "(writer)": "author",
#        "(lyrics)": "author",
        "(author)": "!author",
        "(aut.)": "!author",
        "(auth)": "!author",
        "(auth.)": "!author",
        "(translator)": "!translator",
        "(attributed translator)": "!translator",
        "(tr)": "!translator",
        "(tr.)": "!translator",
        "(trans.)": "!translator",
        "(translation)": "!translator",
        "(transl)": "!translator",
        "(transl.)": "!translator",
        "(translators)": "<translator",
        "(trs)": "<translator",
        "(trs.)": "<translator",
        "(editors)": "<editor",
        "(eds)": "<editor",
        "(eds.)": "<editor",
        "(editor)": "!editor",
        "(ed)": "!editor",
        "(Ed.)": "!editor",
        "(ed.)": "!editor",
        "(compiler)": "!editor",

        "translator": "!translator",
        "translating": "<translator",
        "translated by": ">translator",
        "tr. by": ">translator",
        "trans. by": ">translator",

    }
    _classify_regex = "(" + "|".join(map(re.escape, _classify_commands)) + ")"


    def run_command(self, command_line, stack, state):

        """
        <CMD><VALUE>

        CMD can be:
          + (push value to stack)
          < (apply value to all stack items)
          ! (apply value to top stack item and apply default to all remaining stack items
          > (apply value to next item pushed to stack)
        """

        cmd = command_line[0]
        value = command_line[1:]

        if cmd == "+":
            item = value.strip()
            label = state.get("_next")
            if label:
                state[label] = [item]
                del state["_next"]
            else:
                stack.append(item)
            return True

        if not stack:
            self.dprint("command with no stack", command, stack, state)
            return

        if cmd == "<":
            consume_items = stack.copy()

        elif cmd == "!":
            consume_items = [stack.pop()]
            if stack:
                state["author"] = stack.copy()

        elif cmd == ">":
            consume_items = None
            if stack:
                state["author"] = stack.copy()
            state["_next"] = value

        else:
            self.dprint("unhandled label command", command)
            return

        if consume_items:
            if value in state:
                self.dprint("duplicate value", command, consume_items, state)
                return
            state[value] = consume_items

        del stack[:]

        return True


    def classify_names(self, names, _debug_text=""):
        """
        ["John Doe (author)", "Jane Doe (translator)", "Ed One", "Ed Two (eds.)"] => {"author": ["John Doe"], "translator": ["Jane Doe"], "editor": ["Ed One", "Ed Two"]}

        each "Name" gets pushed to a stack
        (label) acts as a command, the () are optional
        NOTE: "translating" is an alias for "translators"
        if label is singular, apply the label to last item on the stack and then apply "author" to all stack items
        if label is plural, apply the label to all items on the stack
        """

        state = {}
        stack = []

        for name in names:

            actions = []
            name_parts = []
            for text, command in nest_aware_resplit(self._classify_regex, name, [("{{","}}"), ("[[","]]")]):
                if text:
                    text = text.strip()
                    if text:
                        self.run_command("+" + text, stack, state)

                if command:
                    cmd = self._classify_commands.get(command)
                    if cmd:
                        if not self.run_command(cmd, stack, state):
                            return

        if stack:
            if not self.run_command("<author", stack, state):
                return


        # Fixes for "translating"
        if "translator" in state and "author" in state:
            state["author"] = [a.removesuffix("'s").removesuffix(" as") for a in state["author"]]

        for k, names in state.items():
            valid_names = []
            has_et_al = False
            for name in names:
                new_name = re.sub(r"(''|\b)(et|&) al((ii|\.)''(.)?|[.,]|$)", "", name)
                if new_name != name:
                    has_et_al=True
                    name = new_name.strip()
                    if not name:
                        continue
                elif name.strip() == "al.":
                    has_et_al=True
                    continue

                if not self.is_valid_name(name):
                    m = re.search(r"\(.*?\)", name)
                    if m:
                        self.dprint("unhandled paren in name", m.group(0))
                    self.dprint(f"invalid {k} name:", name, ":::", _debug_text)
                    return

                valid_names.append(name)

            if has_et_al:
                valid_names.append("et al")

            state[k] = valid_names

        if any(k.startswith("_") for k in state.keys()):
            self.dprint(f"LIST VM BAD RETURN STATE", state)
            raise ValueError(f"LIST VM BAD RETURN STATE", state)

        return state




    def get_leading_classified_names(self, text):

        # Names can't start with a quote mark
        orig_text = text

        text = text.lstrip(";:, ")
        if not text or text[0] in ['"', '"', '“', '”']:
            return {}, text

        m = re.match(r"""^(.*?)[:;, ](?P<post>("|''|“).*)$""", text)
        if not m or not m.group(1).strip():
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
        classified_names = self.classify_names(names, author_text)

        if classified_names:
            return classified_names, m.group('post')
        elif "al." in text:
            print("INVALID", text)

        return {}, text


    @staticmethod
    def get_leading_chapter_title(text):
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
            ''([^']+?)''               # title enclosed in quotes
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

        m = re.match(fr"[;:, ]*({q}.+?{q})(.*)$", text)
        if not m:
            return "", text

        title = m.group(1)[2:-2]

        # strip (novel) from remaing text
        post_text = re.sub(r"^\s*\(novel\)\s*[;:,. ]*", "", m.group(2))

        return title, post_text

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
            location = locations[0].strip(":,(). ")
            if location in [ "Ourense", "A Coruña", "US", "USA", "UK", "Canada", "Baltimore", "London", "Toronto", "New York", "Dublin", "Washington, DC", "Nashville", "Montréal", "[[Paris]]", "[[Lausanne]]", "New York, N.Y.",
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
"Polygon",
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
    def get_line(text):
        pattern = r"""(?x)
            ^[;:, ]*(?P<pre>.*?)\s*         # leading text
            \b                              # hard separator
            (?:[Ll]ine)                     # page, pg, p., or p
            (?:&nbsp;|\s*)+                 # whitespace
            (?P<num>[0-9ivxlcdmIVXLCDM]+)   # numbers or roman numerals
            [;:, ]*(?P<post>.*)$            # trailing text
        """

        # TODO: Validate number as pure arabic or roman numerals

        m = re.match(pattern, text)
        if m:
            page = m.group('num').strip(",")
            return page, m.group('pre') + " " + m.group('post')

        return "", text


    @staticmethod
    def get_lines(text):

        pattern = r"""(?x)
            ^[;:, ]*(?P<pre>.*?)\s*             # leading text
            [Ll]ines                            # Lines
            (?:&nbsp;|\s*)*                     # optional whitespace
            ([0-9ivxlcdmIVXLCDM]+               # numbers or roman numerals
            \s*(?:,|-|–|&|and|to|{{ndash}})+\s*   # mandatory separator(s)
            [0-9ivxlcdmIVXLCDM]+)               # numbers or roman numerals
            [;:, ]*                             # trailing separator or whitespace
            (?P<post>.*)                        # trailing text
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
            (?P<num>[0-9ivxlcdmIVXLCDM,]+)  # numbers or roman numerals, comma separators
            [;:, ]*(?P<post>.*)$            # trailing text
        """

        # TODO: Validate number as pure arabic or roman numerals
        # allow values like E4 and 4A (but not after a single p without a space)?

        m = re.match(pattern, text)
        if m:
            page = m.group('num').strip(",")
            return page, m.group('pre') + " " + m.group('post')

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
            ([0-9ivxlcdmIVXLCDM]+               # numbers or roman numerals
            \s*(?:,|-|–|&|and|to|{{ndash}})+\s*   # mandatory separator(s)
            [0-9ivxlcdmIVXLCDM]+)               # numbers or roman numerals
            [;:, ]*                             # trailing separator or whitespace
            (?P<post>.*)                        # trailing text
        """

        # TODO: Validate that pages before and pages after are both roman or non-roman

        m = re.match(pattern, text)
        if m:
            pages = m.group(2)
            # Sanity check "1,234" should be "page 1234" and not "pages 1,234"
            if "," in pages:
                s = pages.split(",")
                if len(s) == 2 and len(s[0])==1 and len(s[1]) == 3:
                    return "", text


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
    def get_leading_month_day(text):
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
    def get_leading_issue(text):
        pattern = r"""(?x)
            \s*
            (?P<season>((Spring|Summer|Fall|Winter|Jan(uary)?|Feb(ruary)?|Mar(ch)?|Apr(il)?|May|Jun(e)?|Jul(y)?|Aug(ust)?|Sep(tember)?|Oct(ober)?|Nov(ember)?|Dec(ember)?)[- ]*)+)
            [.,]+                           # dot or comma
            [;:, ]*(?P<post>.*)$            # trailing text
        """

        m = re.match(pattern, text)
        if m:
            return m.group('season').strip(" -"), m.group('post')

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

        # YYYY-MM-DD
        # YYYY, Month DD
        pattern = r"""(?x)
            ^[;:,]*(?P<pre>.*?)              # leading text
            \b                               # Hard break
            (?P<year>\d{4})                  # Year
            [-, ]+                           # separator
            (?P<month>(0?[1-9]|1[012]|Jan(uary)?|Feb(ruary)?|Mar(ch)?|Apr(il)?|May|Jun(e)?|Jul(y)?|Aug(ust)?|Sep(t)?(ember)?|Oct(ober)?|Nov(ember)?|Dec(ember)?))
            [-, ]+                           # separator
            (?P<day>3[01]|[12][0-9]|0?[1-9]) # Day
            \b                               # Hard break
            [;:, ]*(?P<post>.*)$             # trailing text
        """
        m = re.match(pattern, text)
        if m:
            month = m.group('month')
            if month.isnumeric():
                month = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][int(m.group('month'))-1]

            day = int(m.group('day'))  # Always Mon DD
            if not (
                    (month == "Feb" and day>29)
                    or (month in ["Apr", "Jun", "Sep", "Nov"] and day>30)
                    ):
                return m.group('year'), month, day, m.group('pre') + " " + m.group('post')



        # YYYY DD Mon
        pattern = r"""(?x)
            ^[;:,]*(?P<pre>.*?)              # leading text
            \b                               # Hard break
            (?P<year>\d{4})                  # Year
            [-, ]+                           # separator
            (?P<day>3[01]|[12][0-9]|0?[1-9]) # Day
            [-, ]+                           # separator
            (?P<month>(Jan(uary)?|Feb(ruary)?|Mar(ch)?|Apr(il)?|May|Jun(e)?|Jul(y)?|Aug(ust)?|Sep(t)?(ember)?|Oct(ober)?|Nov(ember)?|Dec(ember)?))
            \b                               # Hard break
            [;:, ]*(?P<post>.*)$             # trailing text
        """
        m = re.match(pattern, text)
        if m:
            month = m.group('month')

            day = int(m.group('day'))*-1  # always DD Month
            if not (
                    (month == "Feb" and day>29)
                    or (month in ["Apr", "Jun", "Sep", "Nov"] and day>30)
                    ):
                return m.group('year'), month, day, m.group('pre') + " " + m.group('post')



        # DD Mon, YYYY
        # Mon DD, YYYY
        # Mon, YYYY
        pattern = r"""(?x)
            ^[;:, ]*(?P<pre>.*?)\s*             # leading text
            ((?P<dayname>(Sun|Mon|Tue(s)?|Thu(r?)(s)?|Fri)(day)?)[, ]+)?   # Day name
            ((?P<day1>3[01]|[12][0-9]|0?[1-9])\s+)?   # 1-31
            (?P<month>Jan(uary)?|Feb(ruary)?|Mar(ch)?|Apr(il)?|May|Jun(e)?|Jul(y)?|Aug(ust)?|Sep(t)?(ember)?|Oct(ober)?|Nov(ember)?|Dec(ember)?)
            [.,]*                           # dot or comma
            (\s+(?P<day2>3[01]|[12][0-9]|0?[1-9]))?   # 1-31
            ,*                              # comma
            (?:&nbsp;|\s*)+                 # whitespace
            ,*                              # comma
            (?P<year>\d{4})?                # YYYY
            \b
            [;:, ]*(?P<post>.*)$            # trailing text
        """

        m = re.match(pattern, text)
        if m:
            if m.group('day1') and m.group('day2'):
                day = int(m.group('day1'))*-1
                year = m.group('day2')
                if len(year) != 2: # Don't match single digits
                    print("bad date", text)
                    return None, None, None, text

                # Convert to four digit year, with some future proofing
                year = "20" + year if int(year)<25 else "19" + year

            else:
                if m.group('day1'):
                    day = int(m.group('day1'))*-1
                elif m.group('day2'):
                    day = int(m.group('day2'))
                else:
                    day = 0

                year = m.group('year')

            if day or year:
                return year, m.group('month'), day, m.group('pre') + " " + m.group('post')

        return None, None, None, text

    def parse_details(self, text):

        print("_____")
        print(text)

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

        def save(k, v, allow_override=False):
            if not allow_override and k in details:
                if not "_error" in details:
                    details["_error"] = []
                details["_error"].append(f"duplicate key '{k}' OLD:'{details[k]}' NEW:'{orig_text}'")
            details[k] = v

        text = re.sub(r"<\s*/?\s*sup\s*>", "", text)
        text = text.replace('<span class="plainlinks">', "")
        text = text.replace('</span>', "")
        text = text.replace('<small>', "")
        text = text.replace('</small>', "")
        text = text.replace('{{,}}', ",")
        text = text.replace('{{nbsp}}', " ")
        text = text.replace('&nbsp;', " ")
#        text = text.replace('&mdash;', " ")

        text = self.strip_wrapper_templates(text, ["nowrap", "nobr"])

        year, text = self.get_leading_year(text)
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
        for k, names in names.items():
            if k == "author":
                for count, author in enumerate(names, 1):
                    key = f"author{count}" if count > 1 else "author"
                    save(key, author)
            elif k in ["translator", "editor"]:
                if len(names) > 1:
                    save(k + "s", "; ".join(names))
                else:
                    save(k, names[0])
            else:
                self.dprint(f"unhandled key {k}")
                return

        translator, text = self.get_translator(text)
        if translator:
            save("translator", translator)

        editor, text = self.get_editor(text)
        if editor:
            save("editor", editor)

        chapter_title, text = self.get_leading_chapter_title(text)
        title, text = self.get_title(text)

        subtitle, text = self.get_title(text)
        if title and subtitle:
            title = f"{title}: {subtitle}"

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
                    print("FAILED: published year doesn't match citation year")
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

    def get_source_adjusted_params(self, source, params):
        # Renames paramaters in params to match those used by "source" type templates
        rename_stages = self._param_adjustments.get(source)
        if not rename_stages:
            return params

        res = params
        for x, rename in enumerate(rename_stages):
            for k in rename.values():
                if k in res:
                    self.dprint(f"conflicting param during rename {k}")
                    return

            res = {rename.get(k, k):v for k,v in res.items()}

        return res


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

        prefix = self.get_template_type(section)
        source = self.get_template_source(params)
        if not source:
            print("FAILED", section._lines[idx])
            #exit()
            return

        template = prefix + "-" + source

        params = self.get_source_adjusted_params(source, params)
        if not params:
            return

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
