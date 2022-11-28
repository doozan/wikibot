import re

class SectionParser():

    def log(self, error, section, line):
        lineage = list(section.lineage) if section else [ self.title, "" ]
        page = lineage.pop
        path = ":".join(reversed(lineage))
        self._log.append((error, path, line))
        return

    error = log

    def __init__(self, text, page_title):
        self.title = page_title
        self.level = 1

        self._header = []
        self._children = []

        self._log = []

        # Parser states
        self.in_comment = False
        self.in_nowiki = False
        self.template_depth = []

        self.has_nowiki = False
        self.has_comment = False

        self._parse(text)

    def add(self, item):
        if isinstance(item, str):
            self._header.append(item)
        else:
            self._children.append(item)

    def ifilter_sections(self, recursive=True, matches=lambda x: True):
        for child in self._children:
            if matches(child):
                yield child
            if recursive:
                yield from(child.ifilter_sections(recursive, matches))

    def filter_sections(self, *args, **kwargs):
        return list(self.ifilter_sections(*args, **kwargs))

    @property
    def header(self):
        if self._header:
            return "\n".join(self._header) + "\n"
        return ""

    def __str__(self):
        return self.header + "\n----\n\n".join(list(map(str, self._children))).rstrip()

    @property
    def state(self):
        state = 0
        if self.in_comment:
            state += 1
        if self.template_depth:
            state += 2
        if self.in_nowiki:
            state += 4
        return state

    def _update_state(self, line):
        separators = ("<!--", "-->", "<nowiki>", "</nowiki>", "^{{[^|}]*", r"[^\\]{{[^|}]*", "}}")
        for item in re.findall("(" + "|".join(separators) + ")", line):
            if item == "<nowiki>":
                self.has_nowiki = True
            if item == "<!--":
                self.has_comment = True

            if self.in_comment:
                if item == "-->":
                    self.in_comment = False
                continue

            if self.in_nowiki:
                if item == "</nowiki>":
                    self.in_nowiki = False
                continue

            if item.startswith("{{") or item[1:3] == "{{":
                self.template_depth.append(line) #item)

            elif item == "}}" and self.template_depth:
                self.template_depth.pop()

            elif item == "<!--":
                self.in_comment = True

            elif item == "<nowiki>":
                self.in_nowiki = True

    def _parse(self, text):

        references = False
        section = None
        parent = None
        header_comment = None

        for line in text.splitlines():

            line_state = self.state

            # Update in_comment and template_depth
            self._update_state(line)

            m = re.match(r"^(==+)([^=]+)(==+)\s*(.*?)\s*$", line)

            if line_state:
                if not section:
                    self._header.append(line)
                else:
                    section.add(line)

                if m:
                    if line_state & 1:
                        self.log("open_html_comment", section, line)
                    if line_state & 2:
                        self.log("open_template", section, self.template_depth[-1] + " | " + line)
                    if line_state & 4:
                        self.log("open_nowiki", section, line)

                continue

            # New section start
            if m:
                level = min(len(m.group(1)), len(m.group(3)))
                lpad = (len(m.group(1))-level) * "="
                rpad = (len(m.group(3))-level) * "="

                if m.group(4):
                    if re.match(r"^\<!--.*--\>$", m.group(4)):
                        header_comment = m.group(4)
                        self.log("comment_on_title", section, line)
                    else:
                        self.error("text_on_title", section, line)

                m = re.match(r"\s*(.*?)\s*(\d*)\s*$", m.group(2))

                title = lpad + m.group(1) + rpad
                count = m.group(2)

                if not section:
                    parent = self

                elif level > section.level:
                    parent = section

                else:
                    parent = section.parent
                    while parent and level <= parent.level:
                        parent = parent.parent

                new_section = Section(parent, level, title, count)
                parent.add(new_section)

                section = new_section
                if header_comment:
                    section.add(header_comment)
                    header_comment = None

                continue

            if not section:
                self._header.append(line)
            else:
                section.add(line)


class Section():

    templates = [ "c", "C", "cat", "top", "topic", "topics", "categorize", "catlangname", "catlangcode", "cln" ]
    re_templates = r"\{\{\s*(" + "|".join(templates) + r")\s*[|}][^{}]*\}*"
    re_categories = r"\[\[\s*Category\s*:[^\]]*\]\]"
    re_match_categories = fr"({re_templates}|{re_categories})"

    def __init__(self, parent, level, title, count=None):
        self.parent = parent
        self.level = level
        self.title = title
        self.count = count

        self._lines = []
        self._trailing_empty_lines = []
        self._children = []

        # Categories are collected in the topmost Section
        target = self
        while hasattr(target.parent, "_add_category"):
            target = target.parent
        if target == self:
            self._categories = []
            self._moved_categories = False
            self._duplicate_categories = False
        self._topmost = target

    def adjust_level(self, new_level):
        if new_level != self.level:
            self.level = new_level
            for child in self._children:
                child.adjust_level(new_level + 1)

    @classmethod
    def has_category(cls, line):
        # Returns True if there is a category classifier anywhere on the line
        return bool(re.search(cls.re_match_categories, line))

    @classmethod
    def is_category(cls, line):
        # Returns True if a line contains at least one category and no text outside of the category templates or HTML comments

        # Remove HTML comments first
        line = re.sub("(<!--.*?-->)", "", line)

        line_without_cats = re.sub(cls.re_match_categories, '', line)
        if line_without_cats != line and line_without_cats.strip() == "":
            return True

        return False

    @classmethod
    def extract_categories(csl, line):
        # Returns (line_without_categories, [categories])

        # Remove HTML comments first
        line = re.sub("(<!--.*?-->)", "", line)

        line_without_cats = re.sub(cls.re_match_categories, '', line)
        if line_without_cats != line and line_without_cats.strip() == "":
            return True

    def add(self, item):
        if isinstance(item, str):
            # Ignore empty lines before first data item
            if re.match(r"^(----+)?\s*$", item):
                if not self._lines:
                    return
                # buffer empty lines until there is a data line
                self._trailing_empty_lines.append(item)

            elif self.is_category(item):
                self._add_category(item)

            else:
                if self._trailing_empty_lines:
                    self._lines += self._trailing_empty_lines
                    self._trailing_empty_lines = []

                self._lines.append(item)
                # Raise flag if there are additional lines after any category declaration
                if self._topmost._categories:
                    self._topmost._moved_categories = True

            return

        self._children.append(item)

    def _add_category(self, line):
        if hasattr(self.parent, "_add_category"):
            self.parent._add_category(line)
        else:
            if line in self._categories:
                self._duplicate_categories = True
            else:
                self._categories.append(line)

    @property
    def header(self):
        head = "\n" if self.level > 2 else ""

        name = self.title + " " + self.count if self.count else self.title
        return head + "="*self.level + name + "="*self.level + "\n"

    @property
    def categories(self):
        if not hasattr(self, "_categories") or not self._categories:
            return ""

        return "\n" + "\n".join(self._categories) + "\n"

    @property
    def lines(self):
        if not self._lines:
            return ""

        return "\n".join(self._lines) + "\n"

    @property
    def lineage(self):
        item = self
        while item:
            if getattr(item, "count", None):
                yield item.title + " " + item.count
            else:
                yield item.title
            if not hasattr(item, "parent"):
                break
            item = item.parent

    @property
    def path(self):
        lineage = list(self.lineage)
        return ":".join(reversed(lineage[:-1]))

    def ifilter_sections(self, recursive=True, matches=lambda x: True):
        for child in self._children:
            if matches(child):
                yield child
            if recursive:
                yield from(child.ifilter_sections(recursive, matches))

    def filter_sections(self, *args, **kwargs):
        return list(self.ifilter_sections(*args, **kwargs))

    def __str__(self):
        return self.header + self.lines + "".join(list(map(str, self._children))) + self.categories

