from collections import namedtuple
import pywikibot

"""
Pages are composed of one or more Sections
Sections are generated calling is_new_section(item, prev_item) for each entry in the sorted log
"""

class BaseHandler():
    """ Saves a log to a wiktionary page """

    _site = None # used by pywikbot

    def save(self, items, base_path, **nargs):
        """ Save logged items to wiki pages """

        # Stash extra params
        # This lets class overrides stash variable information that can be accessed
        # by the the overridden functions
        self.args = namedtuple('args', nargs.keys())(*nargs.values())

        if not items:
            return

        items = self.sort_items(items)
        pages = self.make_pages(items)

        for page_name, page_sections in pages.items():
            page_lines = self.make_page(base_path, page_name, page_sections, pages)
            self.save_page(base_path+"/"+page_name, "\n".join(page_lines))

        index_lines = self.make_index(base_path, page_name, pages)
        if index_lines:
            index_url = getattr(self.args, "index_url", base_path)
            self.save_page(index_url, "\n".join(index_lines))

    def make_pages(self, items):

        pages = {} # page_name: page_sections
        page_name = None
        page_sections = []

        section_start = 0
        prev_item = None
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
        if not self._site:
            self._site = pywikibot.Site()
        wiki_page = pywikibot.Page(self._site, page)
        if wiki_page.text.strip() == page_text.strip():
            print(f"{page} has no changes")
            return
        wiki_page.text = page_text
        print(f"saving {page}")
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

    def make_section(self, base_path, page_name, section_entries, prev_section_entries, pages):
        res = self.get_section_header(base_path, page_name, section_entries, prev_section_entries, pages)

        prev_entry = None
        for entry in section_entries:
            res += self.format_entry(entry, prev_entry)
            prev_entry = entry
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

    def make_index(self, base_path, page_name, pages):
        """ Returns a list of strings to be used as the index page """
        index_items = self.make_index_items(base_path, page_name, pages)


        index_header = self.index_header(index_items)
        index_footer = self.index_footer(index_items)
        index_items = index_header + self.index_sort(index_items) + index_footer

        if not index_items:
            return []

        return self.make_wiki_table(index_items, extra_class="sortable", num_headers=len(index_header), num_footers=len(index_footer))

    def make_index_items(self, base_path, page_name, pages):
        index_items = []
        prev_section_entries = None
        for page_name, page_sections in pages.items():
            for section_entries in page_sections:
                index_items += self.get_section_index(base_path, page_name, section_entries, prev_section_entries, pages)
                prev_section_entries = section_entries

        return index_items

    def make_wiki_table(self, rows, caption=None, extra_class=None, num_headers=0, num_footers=0):
        """ Formats a list of rows as a wiki table """
        cls = f"wikitable {extra_class}" if extra_class else "wikitable"
        lines = ['{| class="' + cls + '"' ]
        if caption:
            lines.append(f'|+ class="nowrap" | {caption}')
        for i, row in enumerate(rows):
            lines.append("|-")
            divider = "!" if i<num_footers or i>len(rows)-1-num_footers else "|"
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

    def save(self, dest, handler=BaseHandler, *args, **nargs):
        handler().save(self._items, dest, *args, **nargs)
