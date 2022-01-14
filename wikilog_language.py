from collections import namedtuple
from autodooz.wikilog import BaseHandler

""" Logger class, expects log entries to have the following attributes:
    error,     - The error id
    page,      - The page contaning the error
    language,  - The language section containing the error
    section,   - Section containing the error
    line,      - The line causing the error (Optional)
    highlight, - Additional information or the part of the line causing the error (Optional)
                 If it matches exactly on substring of the line, it will be highligted
                 Otherwise it will be displayed alongside the line
"""

class WikiByLanguage(BaseHandler):

    _indextype = namedtuple("index_items", [ "link", "errors" ])

    def format_entry(self, entry, prev_entry):
        e = entry
        line = f": [[{e.page}#{e.language}|{e.page}:{e.section}]]"

        if e.line:
            if e.highlight:
                if e.line.count(e.highlight) >= 1:
                    temp = e.line.replace(e.highlight, f"</nowiki>'''<nowiki>{e.highlight}</nowiki>'''<nowiki>")
                    temp = f"<nowiki>{temp}</nowiki>"
                    temp = " " + temp.replace("<nowiki></nowiki>", "")
                else:
                    temp = f" <nowiki>{e.line}</nowiki> ('''<nowiki>{e.highlight})</nowiki>''')"
                line += temp
            else:
               line += f" <nowiki>{e.line}</nowiki>"
        elif e.highlight:
            line += f" <nowiki>{e.highlight}</nowiki>"

        return [line]

    def sort_items(self, items):
        return sorted([x for x in items if x.language], key=lambda x: (x.language, x.error, x.page, x.section))

    def sort_page_sections(self, items):
        # Sort by language, # of entries, error code
        return sorted(items, key= lambda x: (x[0].language, len(x), x[0].error))

    def is_new_section(self, item, prev_item):
        # Split by language and by error
        return not prev_item or prev_item.language != item.language or prev_item.error != item.error

    def get_section_header(self, base_path, page_name, section_entries, prev_section_entries, pages):
        res = []
        item = section_entries[0]
        prev_item = prev_section_entries[-1] if prev_section_entries else None
        if not prev_item or prev_item.language != item.language:
            res.append(f"=={item.language}==")

        count = sum(map(len, [x for x in pages[page_name] if x[0].language == item.language]))
        res.append(f"'''{item.error}''': {len(section_entries)} item{'s' if len(section_entries)>1 else ''}")

        return res

    def get_section_index(self, base_path, page_name, section_entries, prev_section_entries, pages):

        # this is called for every section, but not every section should be indexed
        # only create an index for the start of a new language

        item = section_entries[0]
        if prev_section_entries:
            prev_item = prev_section_entries[-1]
            if prev_item.language == item.language:
                return []

        return self.format_section_index(base_path, page_name, section_entries, prev_section_entries, pages)

    def format_section_index(self, base_path, page_name, section_entries, prev_section_entries, pages):
        item = section_entries[0]

        # NOTE: When changing the link format, ensure that index_sort() isn't affected
        link = f"[[{base_path}/{page_name}#{item.language}|{item.language}]]"

        errors = sum(map(len, [x for x in pages[page_name] if x[0].language == item.language]))
        return [self._indextype(link, errors)]

    def index_header(self, index_items):
        return [("Language", "#")]

    def index_sort(self, items):
        # Sort by total (descending), then language name split from [[mismatched/G#German Low German|German Low German]]
        return sorted(items, key=lambda x: (x.errors*-1, x.link.split("#")[1].split("|")[0]))

    def index_footer(self, index_items):
        return [("Total", sum(x.errors for x in index_items))]

    def is_new_page(self, page_sections, section_entries):
        # Paginate on first letter of language name
        if not page_sections:
            return False

        item = section_entries[0]
        prev = page_sections[-1][-1]
        if prev.language[0] != item.language[0]:
            return True

        # Don't paginate between two sections of the same language
        if prev.language == item.language:
            return False

        # Limit pages to 1000 items
        # pages consisting of a single entry may exceed this limit
        page_limit = getattr(self.args, "page_limit", 0)
        if page_limit and sum(map(len, page_sections)) + len(section_entries) > page_limit:
            return True

    def page_name(self, page_sections, prev_name):
        section_entries = page_sections[0]
        item = section_entries[0]

        res = item.language[0] if (not prev_name or item.language[0] != prev_name[0]) \
            else f"{prev_name[0]}{int(prev_name[1:])+1}" if len(prev_name) > 1 else f"{prev_name[0]}2"
        return res

    def page_header(self, base_path, page_name, items, pages):
        # Make a list of quicklinks to other pages
        return [" | ".join(f"[[{base_path}/{x}|{x}]]" if x != page_name else x for x in pages.keys())]





class OldByLanguageHandler(): #autodooz.wikilog.BaseHandler):

    _indextype = namedtuple("index_items", [ "link", "count" ])

    def __init__(self, page_limit=1000):
        super().__init__()
        self.PAGE_LIMIT = page_limit

    def make_section(self, base_path, page_name, section_entries, prev_section_entries, pages):
        lines = [f"=={section_entries[0].language}=="]

        def add_section(items):
            error = items[0].error
            yield f"'''{error}''': {len(items)} item{'s' if len(items)>1 else ''}"
            for i in items:

                res = f": [[{i.page}#{i.language}|{i.page}:{i.section}]]"

                if i.line:
                    temp = f":: <nowiki>{i.line}</nowiki>"
                    if i.highlight:
                        if i.line != i.highlight:
                            if temp.count(i.highlight) == 1:
                                temp = temp.replace(i.highlight, f"</nowiki>'''<nowiki>{i.highlight}</nowiki>'''<nowiki>")
                                temp = temp.replace("<nowiki></nowiki>", "")
                            else:
                                temp += f" (<nowiki>{i.highlight}</nowiki>)"
                    res += temp
                elif i.highlight:
                    res += f":: <nowiki>{i.highlight}</nowiki>"

                yield res

        section_start = 0
        prev = None
        sections = []
        for i,item in enumerate(section_entries):
            if prev and prev.error != item.error:
                sections.append((section_start, i))
                section_start = i
            prev = item
        sections.append((section_start, i+1))

        # Sort sections with most entries first
        for section_start, section_end in sorted(sections, key=lambda x: x[1]-x[0], reverse=True):
            lines += add_section(section_entries[section_start:section_end])
        return lines

    def index_header(self, index_items):
        return [("Language", "#")]

    def get_section_index(self, base_path, page_name, section_entries, prev_section_entries, pages):
        i = section_entries[0]

        # NOTE: When changing the link format, ensure that index_sort() isn't affected
        link = f"[[{base_path}/{page_name}#{i.language}|{i.language}]]"
        count = len(section_entries)
        return [self._indextype(link, count)]

    def index_sort(self, items):
        # Sort by total (descending), then language name split from [[mismatched/G#German Low German|German Low German]]
        return sorted(items, key=lambda x: (x.count*-1, x.link.split("#")[1].split("|")[0]))

    def index_footer(self, index_items):
        return [("Total", sum(count for link, count in index_items))]

    def is_new_page(self, page_sections, section_entries):
        # Paginate on first letter of language name
        if not page_sections:
            return False

        if page_sections[-1][-1].language[0] != section_entries[0].language[0]:
            return True

        # Limit pages to 1000 items
        # pages consisting of a single entry may exceed this limit
        if self.PAGE_LIMIT and sum(map(len, page_sections)) + len(section_entries) > self.PAGE_LIMIT:
            return True

    def page_name(self, page_sections, prev):
        section_entries = page_sections[0]
        item = section_entries[0]

        res = item.language[0] if (not prev or item.language[0] != prev[0]) \
            else f"{prev[0]}{int(prev[1:])+1}" if len(prev) > 1 else f"{prev[0]}2"
        print("page name", res)
        return res

    def page_header(self, base_path, page_name, items, pages):
        return [" | ".join(f"[[{base_path}/{x}|{x}]]" if x != page_name else x for x in pages.keys())]

    def sort_items(self, items):
        return sorted(items, key=lambda x: (x.language, x.error, x.page, x.section))

    def is_new_entry(self, item, prev_item):
        # Split and index by language
        return prev_item and prev_item.language != item.language

""" Log to a local file instead of a wiki page """
class FileByLanguage(WikiByLanguage):

    def save_page(self, dest, page_text):
        dest = dest.lstrip("/").replace("/", "_")
        with open(dest, "w") as outfile:
            outfile.write(page_text)
            print("saved", dest)

    def save(self, *args, **nargs):
        super().save(*args, **nargs, commit_message=None)

