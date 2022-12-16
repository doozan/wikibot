from autodooz.sectionparser import SectionParser
from autodooz.sections import ALL_LANGS
import re

def get_year(text):
    m = re.match(r"'''(\d{4})'''[;,:—\- ]*(.*)", text)
    if not m:
        print(text)
        exit()
        return
    return m.group(1), m.group(2)


def get_translator(text):
    translator, text = get_prefixed_translator(text)
    if translator:
        return translator, text

    return get_suffixed_translator(text)

def get_prefixed_translator(text):

    pattern = r"""(?x)
        ^[;:, ]*(?P<pre>.*?)\s*         # leading text
        \(?(?:tr\.|trans\.|translated)\s*by\s*
        (.*?)
        [),]                            # must end with a ) or ,
        [;:, ]*(?P<post>.*)             # trailing text
    """

    m = re.match(pattern, text)
    if m:
        if not is_valid_name(m.group(2)):
            print("***************** invalid translator:", m.group(2))
            return "", text

        return m.group(2), m.group('pre') + " " + m.group('post')
    return "", text


def get_suffixed_translator(text):
    pattern = r"""(?x)
        ^(?P<pre>.*?)\s*         # leading text
        (?:^|[;:,])\s*           # beginning of line or separator
        ([^,]*?)\s*               # name
        \(translator\)
        [;:, ]*(?P<post>.*)      # trailing text
    """

    m = re.match(pattern, text)
    if m:
        if not is_valid_name(m.group(2)):
            print("***************** invalid translator:", m.group(2))
            return "", text

        return m.group(2), m.group('pre') + " " + m.group('post')
    return "", text


def is_valid_name(text):

    if text.startswith("[") and text.endswith("]"):
        return True

    if text.startswith("{{w|") and text.endswith("}}"):
        return True

    bad_items = [r'''[:ə"“”()<>\[\]\d]''', "''",  r"\b(in|of|by|to|et al|Guides|Press|[Cc]hapter|Diverse)\b", r"\.com", r"\btrans" ]
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


def get_authors(text):
    authors = []

    m = re.match("(.+?) (''.*)", text)
    if not m:
        return [], text

    author_text = m.group(1).strip(":;, ").replace("&#91;", "").replace(" (author)", "")

    s = re.search("( and| &|,|;) ", author_text)
    separator = s.group(1) if s else ", "

    for author in author_text.split(separator):
        author = author.strip()
        if len(author) < 5:
            if author in ["Jr.", "Jr", "MD", "PhD", "MSW", "JD", "II", "III", "IV", "jr", "MS", "PHD", "Sr."]:
                authors[-1] += f", {author}"
                continue

        new_author = re.sub(r"et al\.?$", "", author)
        has_et_al = new_author != author
        if has_et_al:
            author = new_author.strip()

        if not is_valid_name(author):
            print("invalid author:", author)
            return [], text
        authors.append(author)

        if has_et_al:
            authors.append("et al")

    return authors, m.group(2)


def get_title(text):
    # The title is the first string closed in '' ''
    m = re.match("''(.+?)''[;:,. ]*(.*)", text)
    if not m:
        return "", text
    return m.group(1), m.group(2)


def is_valid_publisher(text):

    if text.startswith("[") and text.endswith("]"):
        return True

    if text.startswith("{{w|") and text.endswith("}}"):
        return True

    bad_items = [r'''[:ə"“”()<>\[\]\d]''', "''",  " reprint", "\bpage\b", r"\d{4}", " edition", r"\bed\.", r"p\.", "\bpublished\b"]
    pattern = "(" +  "|".join(bad_items) + ")"
    if re.search(pattern, text):
        return False
    return True

def get_publisher(text):

    # The publisher is all text after the title until the ISBN tag

    m = re.match(r"[(;:., ]*(.*?)[;:, ]*(\(?{{ISBN.*)", text)
    if m and m.group(1):

        publisher = m.group(1).strip()

        pattern = r"""(?x)
           \s*(?:,|\()?\s*
           \s*(?:[Ii]llustrated)?\s*   # optionally preceeded by illustrated
           (\d{4})                 # date
           \s*(?:[Ee]dition|[Rr]eprint)?\s*   # optionally followed by edition
           \s*[),.]?\s*
           """

        mp = re.match(pattern, publisher)
        if not mp:
            mp = re.search(pattern + "$", publisher)

        published_year = None
        if mp:
            published_year = mp.group(1)
            publisher = publisher.replace(mp.group(0), "").strip()
            publisher = re.sub(r"\s+[Ee]dition$", "", publisher)

        location = None
        if ":" in publisher:
            location, _, l_publisher = publisher.partition(":")
            location = location.strip()

            print("location:", location)

            if location in [ "Baltimore", "London", "Toronto", "New York", "Dublin", "Washington, DC", "Nashville", "Montréal" ]:
                publisher = l_publisher.strip()
            else:
                location = None

#        publisher = publisher.strip("() ")

        if not is_valid_publisher(publisher):
            print("bad publisher", publisher)
            return None, None, None, text

        return publisher, published_year, location, m.group(2)
    return "", None, None, text


def get_isbn(text):
    pattern = r"""(?x)
        ^[;:, ]*(?P<pre>.*?)\s*         # leading text
        \(?                             # option (
        {{ISBN\s*\|\s*                  # {{ISBN|
        ([0-9-X ]+)                     # numbers, -, and X
        \s*}}                           # }}
        \)?                             # optional )
        [;:, ]*(?P<post>.*)             # trailing text
    """

    m = re.match(pattern, text)
    if m:
        return m.group(2).replace(" ", ""), m.group('pre') + " " + m.group('post')
    return "", text


def get_oclc(text):

    pattern = r"""(?x)
        ^[;:, ]*(?P<pre>.*?)\s*         # leading text
        \(?                             # option (
        {{OCLC\s*\|\s*                  # {{OCLC|
        ([0-9-]+)                       # numbers
        \s*}}                           # }}
        \)?                             # optional )
        [;:, ]*(?P<post>.*)             # trailing text
    """

    m = re.match(pattern, text)
    if m:
        return m.group(2), m.group('pre') + " " + m.group('post')
    return "", text


def get_url(text):

    pattern = r"""(?x)
        ^[;:, ]*(?P<pre>.*?)\s*         # leading text
        \[                              # [
        (http.*?)                       # url
        \]                              # ]
        [;:, ]*(?P<post>.*)             # trailing text
    """
    m = re.match(pattern, text)
    if m:
        url, _, link_text = m.group(2).partition(" ")
        return url, link_text, m.group('pre') + " " + m.group('post')

    return "", "", text

def get_gbooks(text):

    pattern = r"""(?x)
        ^[;:, ]*(?P<pre>.*?)\s*         # leading text
        ({{gbooks.*?}})                 # gbooks template
        [;:, ]*(?P<post>.*)             # trailing text
    """
    m = re.match(pattern, text)
    if m:
        return m.group(2), m.group('pre') + " " + m.group('post')

    return "", text

def get_page(text):
    pattern = r"""(?x)
        ^[;:, ]*(?P<pre>.*?)\s*         # leading text
        (?:[Pp]age|pg\.|p\.|p )(?:&nbsp;)?\s*            # page, pg., or p. optionally followed by whitespace
        (\d+)                           # numbers
        [;:, ]*(?P<post>.*)             # trailing text
    """

    m = re.match(pattern, text)
    if m:
        return m.group(2), m.group('pre') + " " + m.group('post')
    return "", text


def get_edition(text):
    pattern = r"""(?x)
        ^[;:, ]*(?P<pre>.*?)\s*         # leading text
        (\d+(?:st|nd|rd|th))\s+         # ordinal number
        (?:[Ee]dition)
        [;:, ]*(?P<post>.*)             # trailing text
    """

    m = re.match(pattern, text)
    if m:
        return m.group(2), m.group('pre') + " " + m.group('post')
    return "", text


def get_volume(text):
    pattern = r"""(?x)
        ^[;:, ]*(?P<pre>.*?)\s*         # leading text
        (?:[Vv]olume|vol\.|vol )(?:&nbsp;)?\s*            # page, pg., or p. optionally followed by whitespace
        (\d+)                           # numbers
        [;:, ]*(?P<post>.*)             # trailing text
    """

    m = re.match(pattern, text)
    if m:
        return m.group(2), m.group('pre') + " " + m.group('post')
    return "", text


def get_chapter(text):

    pattern = r"""(?x)
        ^[;:, ]*(?P<pre>.*?)\s*         # leading text
        (?:[Cc]hapter|ch.)\s+           # chapter or ch. followed by whitespace
        (\d+)                           # numbers
        [;:, ]*(?P<post>.*)             # trailing text
    """

    m = re.match(pattern, text)
    if m:
        return m.group(2), m.group('pre') + " " + m.group('post')
    return "", text


def parse_details(text):

    # This assumes details are listed in the following order
    # '''YEAR''', Author 1, Author 2, ''Title of work'', Publisher (ISBN)
    # Authors and Publish are optional
    # After the fixed details, the following details are all optional and
    # may occurr in any order:
    # (OCLC) page 1, chapter 2,

    if "quoted" in text or "comic" in text or "&quot;" in text:
        return

    orig_text = text
    details = {}

    text = re.sub(r"<\s*/?\s*sup\s*>", "", text)
#    text = text.replace('<span class="plainlinks">', "")
#    text = text.replace('</span>', "")

    year, text = get_year(text)
    details["year"] = year

    translator, text = get_translator(text)
    if translator:
        details["translator"] = translator

    authors, text = get_authors(text)
    for count, author in enumerate(authors, 1):
        key = f"author{count}" if count > 1 else "author"
        details[key] = author


    title, text = get_title(text)
    if not title:
        print("no title", text)
        return
    details["title"] = title


    # url may contain the text like 'page 123' or 'chapter 3', so it needs to be extracted first
    url, link_text, text = get_url(text)
    print("url", url, link_text)
    gbooks, text = get_gbooks(text)
    page, text = get_page(text)
    chapter, text = get_chapter(text)
    volume, text = get_volume(text)
    if volume:
        details["volume"] = volume
    edition, text = get_edition(text)
    if edition:
        details["edition"] = edition

    if link_text:
        link_page, link_text = get_page(link_text)
        if link_page:
            if not page:
                page = link_page
            details["pageurl"] = url
            url = ""

        link_chapter, link_text = get_chapter(link_text)
        if link_chapter:
            if not chapter:
                chapter = link_chapter
            if url:
                details["chapterurl"] = url
                url = ""

    if link_text:
        link_text = re.sub("(Google preview|Google search result|unnumbered page|online edition|unmarked page|Google [Bb]ooks)", "", link_text)
        link_text = link_text.strip(':;, ()".')
        if link_text:
            # assume three digit numbers are page numbers
            if len(link_text) == 3 and link_text.isnumeric() and not page:
                page = link_text
            else:
                print("unparsed link text:", link_text)
                return

    if gbooks:
        page = gbooks

    if url:
        details["url"] = url

    if chapter:
        details["chapter"] = chapter

    if page:
        details["page"] = page

    # Parse publisher after removing page, chapter, and volume info

    publisher, year_published, location, text = get_publisher(text)
    if publisher is None:
        return
    if publisher:
        details["publisher"] = publisher

    if year_published and year_published != year:
        details["year_published"] = year_published

    if location:
        details["location"] = location

    isbn, text = get_isbn(text)
    details["isbn"] = isbn

    oclc, text = get_oclc(text)
    if oclc:
        details["oclc"] = oclc

    

    text = text.strip('#*:;, ()".').replace("&nbsp;", "")
    if text:
        if page:
            text = re.sub(r"([Pp]age|p\.|pg\.)", "", text)

        if text.strip('#*:;, ()".'):
            print("unparsed text:", text)
            print(orig_text)
            print("")
            return

    return details


def get_details_from_pattern(text):
    pattern = r"""'''(?P<year>\d*)''', (?P<authors>[^("'\n]*?), ''(?P<title>[^'\n]*)'', (?P<publisher>[^(\n]*?)(:)? \({{ISBN\|(?P<isbn>.*)}}\), page (?P<page>\d*)(:)?"""

    m = re.match(pattern, text)

    for k,v in m.groupdict().items():
        if not v:
            continue
        if k == "authors":
            for x, author in enumerate(v.split(", "), 1):
                key = f"author{x}" if x>1 else "author"
                params[key] = author
        else:
            params[k] = v

    return params





def parse_match(m):

    passage = m.groupdict().get("passage")
    if "|" in passage:
        print("| in passage, skipping:", passage)
        return

    nextline = m.group('nextline')
#    if re.match("#[#*:]+", nextline):
#        print("nextline has data")
#        return

    details = parse_details(m.group('details'))
    if not details:
        return

    return details, passage, "\n" + nextline


def convert_book_quotes(section):

    lang_id = ALL_LANGS.get(section._topmost.title)
    if not lang_id:
        return

    pattern = r"""([#:*]+)\s*(?P<details>'''\d{4}'''.*{{ISBN.*)$"""

#    """\n\1: (?P<passage>.*$)\n(?P<nextline>.*)"""


    outfile = open("unparsed.txt", "a")

    changed = False
    for idx, line in enumerate(section._lines):
        m = re.match(pattern, line)
        if not m:
            continue
        start = m.group(1)
        if len(section._lines) <= idx+1:
            print("no following line", list(section.lineage))
            continue

        if not section._lines[idx+1].startswith(start + ":"):
            print("unexpected following line", section._lines[idx+1], list(section.lineage))
            continue

        params = parse_details(m.group('details'))
        if not params:
            outfile.write(m.group('details') + "\n")
            continue

        passage = section._lines[idx+1].lstrip("#*: ")
        if "|" in passage:
            m = re.match(r"^{{quote\|" + lang_id + r"\|(.*)}}$", passage)
            if m:
                passage = m.group(1)

            if "|" in passage:
                print("| in passage", passage)
                continue

        translation = None
        if len(section._lines) > idx+2 and section._lines[idx+2].startswith(start + ":"):
            translation = section._lines[idx+2].lstrip("#*: ")
            if "|" in translation:
                print("| in translation", translation)
                continue

        if translation and len(section._lines) > idx+3 and section._lines[idx+3].startswith(start + ":"):
            print("too many following lines", list(section.lineage))
            continue

        section._lines[idx] = start + " {{quote-book|" + lang_id + "|" + "|".join([f"{k}={v}" for k,v in params.items()])
        if translation:
            # English should never have a translation
            if lang_id == "en":
                continue

            section._lines[idx+1] = "|passage=" + passage
            section._lines[idx+2] = "|t=" + translation + "}}"
        else:
            section._lines[idx+1] = "|passage=" + passage + "}}"

        changed = True

    outfile.close()
    return changed


def fix_bare_quotes(text, title, summary, options):

    changes = []

    # skip edits on pages with lua memory errors
    ignore_pages = [ "is", "I", "Daniel", "a", "de" ]
    if title in ignore_pages:
        return text

    entry = SectionParser(text, title)

    for section in entry.ifilter_sections():
        if convert_book_quotes(section):
            changes.append(f"/*{section.path}*/ converted bare quote to template")

    if changes:
        summary += changes
        return str(entry)

    return text
