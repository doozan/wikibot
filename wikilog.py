from collections import namedtuple
import pywikibot
import sys

"""
Pages are composed of one or more Sections
Sections are generated calling is_new_section(item, prev_item) for each entry in the sorted log
"""

class BaseHandler():
    """ Saves a log to a wiktionary page """

    _site = None # used by pywikbot

    def save(self, items, base_path, **kwargs):
        """ Save logged items to wiki pages """

        # Stash extra params
        # This lets class overrides stash variable information that can be accessed
        # by the the overridden functions
        self.args = namedtuple('args', kwargs.keys())(*kwargs.values())

        items = self.sort_items(items)
        pages = self.make_pages(items)

        index_saved = False
        index_lines = self.make_index(base_path, pages)
        index_dest = getattr(self.args, "index_url", base_path)

        for page_name, page_sections in pages.items():
            page_lines = self.make_page(base_path, page_name, page_sections, pages)
            dest = base_path + "/" + page_name
            # save index on the first page if no index_dest specified
            if index_lines and not index_dest and not index_saved:
                index_dest = dest
            # Merge the index if it should be part of the page
            if index_lines and index_dest == dest:
                page_lines = index_lines + page_lines
                index_saved = True
            self.save_page(dest, "\n".join(page_lines))

        if not index_saved and index_lines and index_dest:
            self.save_page(index_dest, "\n".join(index_lines))
            index_saved = True

        assert bool(index_lines) == index_saved

    def make_pages(self, items):

        pages = {} # page_name: page_sections
        page_name = None
        page_sections = []

        section_start = 0
        prev_item = None
        i = 0
        for i, item in enumerate(items):
            if prev_item and self.is_new_section(item, prev_item):

                section_entries = items[section_start:i]
                if page_sections and self.is_new_page(page_sections, section_entries):
                    page_name = self.page_name(page_sections, page_name)
                    pages[page_name] = page_sections
                    page_sections = []
                page_sections.append(section_entries)
                section_start = i
            prev_item = item

        section_entries = items[section_start:i+1]
        if page_sections and self.is_new_page(page_sections, section_entries):
            page_name = self.page_name(page_sections, page_name)
            pages[page_name] = page_sections
            page_sections = []
        page_sections.append(section_entries)
        page_name = self.page_name(page_sections, page_name)
        pages[page_name] = page_sections
        page_sections = []

        return pages

    def save_page(self, page, page_text):
        if not page_text.strip():
            print(f"{page} is empty, not saving", file=sys.stderr)
            return

        if not self._site:
            self._site = pywikibot.Site()
        wiki_page = pywikibot.Page(self._site, page)
        if wiki_page.text.strip() == page_text.strip():
            print(f"{page} has no changes", file=sys.stderr)
            return
        wiki_page.text = page_text
        print(f"saving {page}", file=sys.stderr)
        wiki_page.save(self.args.commit_message)

    def index_header(self, index_items):
        """ Returns a list of table rows to be used as table headers """
        return []

    def index_sort(self, items):
        """ Sorts the index entries, if desired """
        return items

    def index_footer(self, index_items):
        """ Returns a list of rows to be used as table footers """
        return []

    def is_new_page(self, page_sections, section_entries):
        """ Returns True if section_entries should be on a new page,
        False if they should be added to the existing page """
        return False

    def page_name(self, page_sections, prev):
        """ Returns a string to be used as the page name for the given items """
        return str(int(prev)+1) if prev else "1"

    def page_header(self, base_path, page_name, page_sections, pages):
        """ Returns a list of strings to be appended to the head of the page """
        return []

    def page_footer(self, base_path, page_name, items, pages):
        """ Returns a list of strings to be concatenated to the end of the page """
        return []

    def sort_items(self, items):
        """ Sorts the logged items """
        return items

    def is_new_section(self, item, prev_item):
        """ Returns True if the current item should be added to a new section,
        False if it should be added to the current section """
        return False

    def sort_page_sections(self, items):
        """ Sorts the page sections """
        return items

    def get_section_header(self, base_path, page_name, section_entries, prev_section_entries, pages):
        return []

    def get_section_footer(self, base_path, page_name, section_entries, prev_section_entries, pages, section_lines):
        return []

    def make_section(self, base_path, page_name, section_entries, prev_section_entries, pages):
        res = self.get_section_header(base_path, page_name, section_entries, prev_section_entries, pages)

        prev_entry = None
        for entry in section_entries:
            res += self.format_entry(entry, prev_entry)
            prev_entry = entry

        res += self.get_section_footer(base_path, page_name, section_entries, prev_section_entries, pages, res)

        return res

    def format_entry(self, entry, prev_entry):
        return str(entry)

    def make_page(self, base_path, page_name, page_sections, pages):
        """ Returns a list of strings to be used as the given page
        page_sections = list of list of logged items
        """
        page_lines = self.page_header(base_path, page_name, page_sections, pages)
        prev_section_entries = None
        for section_entries in self.sort_page_sections(page_sections):
            page_lines += self.make_section(base_path, page_name, section_entries, prev_section_entries, pages)
            prev_section_entries = section_entries
        page_lines += self.page_footer(base_path, page_name, page_sections, pages)
        return page_lines

    def get_section_index(self, base_path, page_name, section_entries, prev_section_entries, pages):
        """ Returns a list of rows to be added to the index """
        return []

    def make_index(self, base_path, pages):
        """ Returns a list of strings to be used as the index page """
        index_items = self.make_index_items(base_path, pages)
        if not index_items:
            return []

        index_header = self.index_header(index_items)
        index_footer = self.index_footer(index_items)
        index_items = self.index_sort(index_items)

        return self.make_wiki_table(index_items, extra_class="sortable", headers=index_header, footers=index_footer)

    def make_index_items(self, base_path, pages):
        index_items = []
        prev_section_entries = None
        for page_name, page_sections in pages.items():
            for section_entries in page_sections:
                index_items += self.get_section_index(base_path, page_name, section_entries, prev_section_entries, pages)
                prev_section_entries = section_entries

        return index_items

    def make_wiki_table(self, rows, caption=None, extra_class=None, headers=[], footers=[]):
        """ Formats a list of rows as a wiki table """
        cls = f"wikitable {extra_class}" if extra_class else "wikitable"
        lines = ['{| class="' + cls + '"' ]
        if caption:
            lines.append(f'|+ class="nowrap" | {caption}')

        divider = "!"
        for row in headers:
            lines.append("|-")
            lines.append(divider + (divider*2).join(map(str,row)))

        divider = "|"
        for row in rows:
            lines.append("|-")
            lines.append(divider + (divider*2).join(map(str,row)))

        divider = "!"
        for row in footers:
            lines.append("|-")
            lines.append(divider + (divider*2).join(map(str,row)))

        lines.append("|}")
        return lines

class WikiLogger():

    _paramtype = tuple

    def __init__(self):
        self._items = []

    def add(self, *item):
        """ Add an item to the log """
        self._items.append(self._paramtype(*item))

    def save(self, dest, handler=BaseHandler, *args, **kwargs):
        handler().save(self._items, dest, *args, **kwargs)
