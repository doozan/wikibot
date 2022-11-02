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

from collections import defaultdict, namedtuple
import re
import sys

from enwiktionary_parser.utils import wiki_finditer

Match = namedtuple("Match", ["path", "path_index", "match_index", "start", "end"])

class Section:
    def __init__(self, title, level, index, start, end, parent):
        self.title = title
        self.level = level
        self.index = index
        self.start = start
        self.end = end
        self.parent = parent
        self._path = None

    @property
    def path(self):
        if not self._path:
            path = [self.title]
            ancestor = self.parent
            while ancestor:
                path.insert(0, ancestor.title)
                ancestor = ancestor.parent
            #self._path = tuple(path)
            self._path = ":".join(path)

        return self._path

    def __str__(self):
        return str(self.__dict__)

_path_stack = []
_path_count = defaultdict(int)
def add_section(all_sections, line, start, no_children=False):
    global _path_count
    global _path_stack

    level = min(len(line)-len(line.lstrip("=")), len(line)-len(line.rstrip("=")))
    title = line[level:-1*level].strip() if level else line.strip()

    if ":" in title:
        raise ValueError("section titles must not contain a colon (:)", line)

    # If the sections don't include children, always set the previous section's
    # end position when starting a new section
    if no_children and _path_stack and _path_stack[-1].level != 0:
        _path_stack[-1].end = start-1

    # Remove any sections from the stack that are deeper than the current level
    while _path_stack and _path_stack[-1].level >= level:
        closed_section = _path_stack.pop()
        if not no_children:
            closed_section.end = start-1

    parent = _path_stack[-1] if _path_stack else None
    section = Section(title, level, None, start, None, parent)

    _path_stack.append(section)
    all_sections.append(section)

    path = section.path
    _path_count[path] += 1
    section.index = _path_count[path]

    return section

def find_section(sections, start, end):
    # Find the section that encompasses the entire matching range
    # Assumes that sections is ordered and that the first section is L0 (entire page)
    best_section = None
    for section in sections:
        if section.start > start:
            break
        if section.end >= end:
            if not best_section or best_section.start <= section.start:
                best_section = section
    return best_section

def is_allowed(path_filter, section):
    # returns True if a given section.path is allowed (matches the filter)
    # The filter is an allowlist, so if a given section.path matches the filter, it is allowed
    return re.match(path_filter, section.path)

def get_matches(title, full_text, re_match, re_not, match_context, no_path, dotall=False, path_filter=None, no_children=True):

    if match_context not in ["page", "L2", "section", "line", "none"]:
        raise ValueError("unhandled context", match_context)

    if dotall:
        raise ValueError("not implemented")

    page_matches = []
    all_sections = []

    # Create a L0 section with the page name
    section = add_section(all_sections, title, 0)

    needs_sections = False
    if path_filter \
            or match_context in ["L2", "section"] \
            or not no_path:
        needs_sections = True

    pattern = rf"(?P<pat>{re_match})|(?P<section>^==+.*?==+)" if needs_sections else re_match

    found_sections = []
    for m in wiki_finditer(pattern, full_text, re.MULTILINE, ignore_comments=False, ignore_nowiki=True, ignore_templates=True):

        if needs_sections and m.group("section"):
            found_sections.append((m.group(0), m.start()))
            continue

        start = m.start()
        end = m.end()

        if match_context == "line":
            start = full_text.rfind("\n", 0, start)
            if start != 0:
                start += 1
            end = full_text.find("\n", end)
        page_matches.append((start, end))

    if not page_matches:
        return []

    for line, start in found_sections:
        add_section(all_sections, line, start, no_children)

    if no_children:
        # Only the first section (full page) and last section need to have the ending set
        if _path_stack:
            _path_stack[0].end = len(full_text)
            _path_stack[-1].end = len(full_text)
    else:
        for section in _path_stack:
            section.end = len(full_text)

    # re_not will block all results on the page if the not pattern matches anywhere in the page
    if re_not and re.search(re_not, full_text):
        return []

    # detect sections with ambiguous paths and add section_max as needed
    matches = []
    matched_sections = set()
    match_count = defaultdict(list)
    idx = 0
    for match_pos in page_matches:

        start, end = match_pos
        section = find_section(all_sections, start, end)

        # If the path has been excluded, don't include the match
        if path_filter and not is_allowed(path_filter, section):
            continue

        if not section:
            raise ValueError("no section", title, match_pos, [(x.start, x.end) for x in all_sections])
        section_max = _path_count[section.path]
        section_index = (section.index, section_max) if section_max > 1 else None

        if match_context == "page":
            if matches:
                continue
            match_start = 0
            match_end = len(full_text)
        elif match_context == "L2":
            l2 = section
            while l2.level > 2 and l2.parent:
                l2 = l2.parent
            if l2.level != 2:
                raise ValueError("no l2 section", title, section.path)

            if l2 in matched_sections:
                continue

            matched_sections.add(l2)
            match_start = l2.start
            match_end = l2.end

        elif match_context == "section":
            # Limit each section to a single match
            # TODO: child sections should be ignored if their parent has already been included
            # this is difficult (impossible?) if the parent is ambiguous
            # no, can distinguish parent by line number
            if section in matched_sections:
                continue
            matched_sections.add(section)
            match_start = section.start
            match_end = section.end
        else:
            match_start = start
            match_end = end
            if match_end == match_start:
                match_end += 1

        match = Match(section.path, section_index, None, match_start, match_end)
        matches.append(match)

        match_text = full_text[match.start:match.end]

        count_item = (section.path, section_index, match_text)
        match_count[count_item].append(idx)
        idx += 1

    for dup_matches in match_count.values():
        total = len(dup_matches)
        if total > 1:
            for i, idx in enumerate(dup_matches):
                matches[idx] = matches[idx]._replace(match_index=(i, total))

    return matches


def format_matches(matches, *args, **kwargs):
    for match in matches:
        yield from format_match(match, *args, **kwargs)

def get_match_position(match, expand_matches=False):
    """ Returns a string (possibly blank) containg section and match indexes
    Returns None if the match has been consolidated into an earlier match and should not be printed
    """
    position_items = []
    if match.path_index is not None:
        idx, total = match.path_index
        position_items.append(f"{{{idx},{total}}}")

    if match.match_index is not None:
        idx, total = match.match_index
        if expand_matches:
            position_items.append(f"[{idx},{total}]")
        else:
            if idx == 1:
                position_items.append(f"[*,{total}]")
            else:
                return

    return "".join(position_items)


def format_match(match, full_text, *args, **kwargs):
    text = full_text[match.start:match.end]
    yield from format_item(match, text, *args, **kwargs)

def format_fix(match, fix, full_text, *args, **kwargs):

    if fix.type in ["section", "line"]:
        new_text = fix.new
    elif fix.type in "regex":
        title = match.path.partition(":")[0]
        new_text = get_fixed_text(match, fix, full_text, title)
    else:
        raise ValueError("unsupported fix.type: {fix.type}")

    yield from format_item(match, new_text, *args, **kwargs)


def get_fixed_text(match, fix, text, title, *args, **kwargs):
    if fix.type in ["section", "line"]:
        return fix.new

    if fix.type in ["regex", "text"]:
        if callable(fix.new):
            messages = [] # TODO: handle messages
            new = lambda match: fix.new(match, title, *args, **kwargs)
        else:
            new = fix.new if fix.type == "regex" else re.escape(fix.new)

        old = re.escape(text[match.start:match.end])
        old_text = text[match.start:match.end]
        return re.sub(old, new, old_text)

    raise ValueError("unsupported fix.type: {fix.type}")


def format_item(match, text, nopath=False, expand_matches=False, compact=True, revision=None):

    position = get_match_position(match, expand_matches)
    if position is None:
        return
        yield

    path = match.path

    if compact:
        if "\n" in text:
            raise ValueError("compact mode, but match has newline")
        yield(f'{path}:{position}: {text}')
    else:
        yield(f"_____{path}:{position}_____\n{text}")
