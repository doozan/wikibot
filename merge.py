#!/usr/bin/python3
#
# Copyright (c) 2022 Jeff Doozan
#
# This is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import pywikibot
import re

class MergeRunner():

    """ Given a list of pages, alternately calls
    funcion_merge(page1_text, page1_title, summary, options, page2_text, page2_title)
    if function_merge returns any data, the next time this is invoked it will call
    function_remove(page2_text, page2_title, summary, options, page1_title)
    if funciton_merge ruturns None, the next call will do nothing
    """

    def __init__(self, links_src, function_merge, function_remove):
        self._site = None
        self.skip_next = False
        self.iter_count = 0
        self.src2dest = {}
        self.dest2src = {}

        links = self.get_links(links_src)

        if len(links) % 2:
            raise ValueError(f"found {len(links)} links in {links_src}, expected an even number")

        iter_links = iter(links)
        for dest in iter_links:
            src = next(iter_links)
            self.src2dest[src] = dest
            self.dest2src[dest] = src

        if not len(self.src2dest) == len(self.dest2src):
            raise ValueError("page list contiains duplicate source or dest", filename)

        self._merge = function_merge
        self._remove = function_remove

    @property
    def site(self):
        if not self._site:
            self._site = pywikibot.Site()
        return self._site

    def merge_pages(self, page_text, page_title, summary, options):
        """ This will be called twice for each pair
        On the first call, it should add data to the target page
        On the second call, it should remove data from the source page
        """

        self.iter_count += 1

        if self.skip_next:
            self.skip_next = False
            print("skipping")
            return page_text

        self.skip_next = False

        if self.iter_count % 2:

            print("XXX MERGING", self.iter_count, page_title)
            dest = page_title

            if dest not in self.dest2src:
                print("!"*80)
                print(self.src2dest)
                print("X"*80)
                print(self.dest2src)
                return page_text

            src_title = self.dest2src[dest]
            wiki_page = pywikibot.Page(self.site, src_title)
            src_text = wiki_page.text

            # Move data from 'src' to 'dest'
            res = self._merge(page_text, page_title, summary, options, src_text, src_title)
            if res is None or res == page_text:
                skip_next = True
                return page_text
            return res

        else:
            print("XXX REMOVING", self.iter_count, page_title)
            # Remove data from 'src' after it has been successfully moved to 'dest'
            src = page_title

            if src not in self.src2dest:
                print("*"*80)
                print(self.src2dest)
                print("x"*80)
                print(self.dest2src)
                return page_text


            dest_title = self.src2dest[src]

            res = self._remove(page_text, page_title, summary, options, dest_title)
            if res is None:
                return page_text
            return res

    @staticmethod
    def get_links(src):
        if src.startswith("User:"):
            site = pywikibot.Site()
            return pywikibot.Page(site, src).linkedPages()
        else:
            with open(src) as infile:
                return re.findall(r"\[\[(.*?)\]\]", infile.read())
