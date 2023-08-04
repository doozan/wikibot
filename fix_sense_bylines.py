import enwiktionary_sectionparser as sectionparser
import re
import multiprocessing
import os
import sys

from autodooz.sections import ALL_POS, COUNTABLE_SECTIONS, ALL_LANGS
from .list_mismatched_headlines import HEAD_TEMPLATES, POS_TEMPLATES

POS_TEMPLATE_LIST = [ "[a-z]+" + t if t.startswith("-") else t for templates in POS_TEMPLATES.values() for t in templates if not "=" in t ]
HEADLINE_PATTERN = "^\s*{{\s*(" + "|".join(POS_TEMPLATE_LIST + HEAD_TEMPLATES) + ")\s*[|}]"
RE_HEADLINE = re.compile(HEADLINE_PATTERN)

def is_headline(text):
    return bool(re.match(RE_HEADLINE, text))

class BylineFixer():

    SORTABLE = [k for k in sectionparser.PosParser.TYPE_TO_TEMPLATES.keys() if k not in ["sense"]]

    TYPE_TO_STYLE = { k: ":" for k in SORTABLE } | {
        "bare_ux": ":",
        "quote": "*",
        "rfquote": ":",
        "bare_quote": "*",
        "sense": "#",
        "unknown": "#",
    }


    def __init__(self):
        self._summary = None
        self._log = []

    def fix(self, code, section, location="", details=None):
        # When running tests, section will be empty
        if not section:
            print("FIX:", code, section.path, location, details)
            return

        if self._summary is not None:
            self._summary.append(f"/*{section.path}*/ {location} {details}")

        self._log.append(("autofix_" + code, section.page, section.path, location, details))

    def condense_summary(self, summary):
        prev_prefix = None
        for idx, entry in enumerate(summary):
            prefix, _, message = entry.partition("*/ ")
            if not message:
                continue

            if prefix == prev_prefix:
                summary[idx] = message

            prev_prefix = prefix

    def warn(self, code, section, location="", details=None):
        self._log.append((code, section.page, section.path, location, details))

    def process(self, page_text, page, summary=None, options=None):
        # This function runs in two modes: fix and report
        #
        # When summary is None, this function runs in 'report' mode and
        # returns [(code, page, details)] for each fix or warning
        #
        # When run using wikifix, summary is not null and the function
        # runs in 'fix' mode.
        # summary will be appended with a description of any changes made
        # and the function will return the modified page text

        self._summary = summary
        self._log = []

        entry = None
        entry_changed = False

        # Skip this particular disaster
        if page in ["уж"]:
            return [] if summary is None else page_text

        entry = sectionparser.parse(page_text, page)
        if not entry:
            return [] if summary is None else page_text

        for section in entry.ifilter_sections(matches=lambda x: x.title != "Idiom" and x.title in ALL_POS \
                and x.parent and (x.parent.title in COUNTABLE_SECTIONS or x.parent.title in ALL_LANGS)):
        #for section in entry.ifilter_sections(matches=lambda x: x.title in ALL_POS):

            # Navajo entries are a mess
            if section._topmost.title == "Navajo":
                continue

            pos = sectionparser.parse_pos(section)
            if not pos:
                continue

            old_pos_text = str(pos)

            if not pos.senses:
                first_sense = None
                headline_after_sense = False
                for idx, line in enumerate(pos.headlines):
                    if first_sense is None:
                        if any(line.startswith(c) for c in "#*:"):
                            first_sense = idx
                    elif is_headline(line):
                        headline_after_sense = True
                        break

                if first_sense is None:
                    self.warn("no_senses", section)
                elif headline_after_sense:
                    if section._children:
                        self.warn("headline_after_senses", section)
                    else:
                        self.warn("headline_after_senses_no_children", section)
                else:
                    text = "\n".join(pos.headlines[first_sense:])
                    if len(text) > 512:
                        text = text[:500] + "\n..."
                    self.warn("unparsable_sense_list", section, "", text)
                continue

            failed = self.fix_sense_list_levels(pos.senses, section)
            if failed:
                continue

            failed = self.fix_sense_list_prefix(pos.senses, section)
            if failed:
                continue

            # Run again to fix promoted children
            failed = self.fix_sense_list_prefix(pos.senses, section)
            if failed:
                continue

            failed = self.fix_sense_list_order(pos.senses, section)
            if failed:
                continue

            new_pos_text = str(pos)
            if old_pos_text != new_pos_text:
                if pos.changelog:
                    self.fix("posparser", section, "", pos.changelog)

                section.content_wikilines = [new_pos_text]
                entry_changed = True

        if summary is None:
            return self._log

        self.condense_summary(summary)

        if entry_changed:
            return str(entry)

        return page_text

    def fix_sense_list_order(self, sense_list, section):
        """ Returns None on success, non-zero on error """

        is_valid = self.validate_sense_list(sense_list, section)

        if is_valid:
            for idx, sense in enumerate(sense_list, 1):
                if sense._children:
                    orig_children = list(sense._children)
                    sense._children.sort(key=lambda x: self.SORTABLE.index(x._type))

                    if orig_children != sense._children:
                        self.fix("byline_order", section, f"sense{idx}", "sorted bylines")

    def fix_sense_list_prefix(self, sense_list, section):
        """ Returns None on success, non-zero on error """

        style = sense_list[0].style
        if not all(s.style == style for s in sense_list):
            self.warn("mixed_sense_styles", section, "", "")
            return True

        for idx, sense in enumerate(sense_list, 1):
            if sense._type not in ["unknown", "sense"]:
                self.warn("unhandled_sense_item", section, f"sense{idx}", f"({sense._type}) {sense.prefix} {sense.data}")
                return True

            if sense.prefix != "#":

                if sense._type == "sense":
                    sense.level = 1
                    sense.style = "#"
                    sense.prefix = "#"
                    self.fix("sense_prefix", section, f"sense{idx}", "fixed sense prefix")
                else:
                    self.warn("unexpected_l1_item", section, f"sense{idx}", f"{sense.prefix} {sense.data}")
                    return True


            # TODO: If all children are ["unknown", "sense"], treat them as subsenses and parse grandchildren as bylines
            # TODO: Only cleanup children for senses that should have children
            for child in sense._children:
                self.cleanup_sense_item(child, section)


    ALL_LABELED_BYLINES = ["syn", "ant", "hyper", "hypo", "holo", "merq", "tropo", "comero", "cot", "parasyn", "perfect", "imperfect", "active", "midvoice", "alti", "co", "cot" ]
    TYPE_DISALLOWED_CHILDREN = {
            k: ["syn", "ant", "hyper", "hypo", "holo", "merq", "tropo", "comero", "cot", "parasyn", "perfect", "imperfect", "active", "midvoice", "alti", "co", "cot", "quote", "ux" ]
            for k in ALL_LABELED_BYLINES }
    TYPE_DISALLOWED_CHILDREN |= {
        "quote": ALL_LABELED_BYLINES,
        "ux": ALL_LABELED_BYLINES + ["quote", "ux"],
    }

    def promote_bad_children(self, item_list, item_idx, section):

        item = item_list[item_idx]
        disallowed_children = self.TYPE_DISALLOWED_CHILDREN.get(item._type)

        bad_children = []
        for idx, child in enumerate(item._children):
            if disallowed_children and child._type in disallowed_children:
                bad_children.append(idx)

        for bad_child_idx in reversed(bad_children):
            new_sibling = item._children.pop(bad_child_idx)

            new_sibling.parent = item.parent
            new_sibling.level = item.level
            new_sibling.prefix = item.prefix[:-1] + new_sibling.style

            item_list.insert(item_idx+1, new_sibling)

            self.fix("bad_child", section, new_sibling.name, "promoted 1 level")

        idx = 0
        while idx < len(item._children):
            self.promote_bad_children(item._children, idx, section)
            idx += 1


    def fix_sense_list_levels(self, sense_list, section):
        """ Returns None on success, non-zero on error """

        # First, promote any bad child items
        idx = 0
        while idx < len(sense_list):
            self.promote_bad_children(sense_list, idx, section)
            idx += 1

    def cleanup_sense_item(self, item, section, update_style=True):

        old_prefix = item.prefix

        # Warn if encountering an "unknown" byline in most circumstances
        if item._type in ["unknown", "sense"]:


            # Don't warn about children of unhandled lines
            if item.parent and item.parent._type == "unknown":
                pass

            # Don't warn on subsenses of senses
            elif item._type == "sense" and (not item.parent or item.parent._type == "sense"):
                pass

            # Don't warn on sublines of bare_quotes and bare_ux, they're probably passages or translations
            elif item.parent and item.parent._type in ["bare_quote", "bare_ux"]:
                pass

            # old RQ: templates that can't handle passage= may have child lines
            elif item.parent and item.parent._type == "quote" and "RQ:" in item.parent.data and "passage=" not in item.parent.data:
                pass
#            # Don't warn about deeply nested bylines
#            elif item.level > 2:
#                pass

            else:
                self.warn("unhandled_byline", section, item.name, f"{item.prefix} {item.data}")


        elif update_style:
            expected_style = self.TYPE_TO_STYLE[item._type]
            if item.style != expected_style:
                self.fix("byline_style", section, item.name, f"fixed {item._type} style")
                item.style = expected_style
                item.prefix = item.parent.prefix + item.style

        if item.level != item.parent.level + 1:
            self.fix("byline_depth", section, item.name, "fixed list item depth")
            item.level = item.parent.level + 1
            item.prefix = item.parent.prefix + item.style

        if item.prefix != item.parent.prefix + item.style:
            self.fix("byline_prefix", section, item.name, "fixed list item prefix")
            item.prefix = item.parent.prefix + item.style

        for child in item._children:
            self.cleanup_sense_item(child, section, update_style=False)



    def validate_sense_list(self, sense_list, section):

        for idx, sense in enumerate(sense_list, 1):
            if sense.prefix != "#":
                self.warn("invalid_l1_sense_prefix", section, f"sense{idx}", sense.prefix)
                return False

            if sense._type not in ["unknown", "sense"]:
                self.warn("l1_sense_item_not_sense", section, f"sense{idx}", sense.prefix)
                return False

            if sense.level != 1:
                self.warn("top_sense_level_not_l1", section, f"sense{idx}", sense.level)
                return False

            seen = set()
            # only handle one level of children
            for child in sense._children:

                if child._type in [ "bare_ux", "bare_quote" ]:
                    # No need to warn, handled by fix_bare_ux and fix_bare_quotes
                    return False

                # Detect items with templates that would classify them by type, but labelled unknown
                # indicates that the line is not a single template wrapper
                if child._type == "unknown":
                    m = re.search(sectionparser.PosParser.re_templates, child.data)
                    if m:
                        template_type = sectionparser.PosParser.template_to_type[m.group('t')]
                        self.warn(f"complex_{template_type}", section, "sense" + child.name[1:], str(child))
                        return False

                # don't warn on subsenses
                if child._type in ["sense", "unknown"]:
                    # TODO: Don't warn here until senses with nested senses are handled
                    self.warn("unhandled_byline_type", section, f"sense{idx}", f"{child.prefix} {child.data}")
                    return False

                # non-sortable items shouldn't be children of senses
                if child._type not in self.SORTABLE:
                    self.warn("unhandled_byline_type", section, f"sense{idx}", f"{child.prefix} {child.data}")
                    return False

                if child.level != sense.level + 1:
                    self.warn("bad_byline_depth", section, "sense" + child.name[1:])
                    is_valid = False

                if self.TYPE_TO_STYLE[child._type] != child.style:
                    self.warn("bad_byline_style", section, "sense" + child.name[1:])
                    is_valid = False

                if child._children and child._type not in ["quote", "ux"]:
                    self.warn("byline_has_children", section, "sense" + child.name[1:], str(child))
                    return False

                if child._type in seen and child._type not in ["quote", "ux", "co", "rfquote"]:
                    self.warn("duplicate_byline_type", section, f"sense{idx} has multiple {child._type}", str(sense))
                    return False

                seen.add(child._type)

        return True
