import enwiktionary_sectionparser as sectionparser
import re
import multiprocessing
import os
import sys
import mwparserfromhell as mwparser

from autodooz.sections import ALL_POS, COUNTABLE_SECTIONS, ALL_LANGS
from .list_mismatched_headlines import is_header

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
        if page.partition("#")[0] in ["уж"]:
            return [] if summary is None else page_text

        entry = sectionparser.parse(page_text, page)
        if not entry:
            return [] if summary is None else page_text

        for section in entry.ifilter_sections(matches=lambda x: x.title != "Idiom" and x.title in ALL_POS \
                and x.parent and (x.parent.title in COUNTABLE_SECTIONS or x.parent.title in ALL_LANGS)):

            # Navajo entries are a mess
            if section._topmost.title == "Navajo":
                continue

            pos = sectionparser.parse_pos(section)
            if not pos:
                continue

            if any(re.search(r"(?<!{){\|", str(sense)) for sense in pos.senses):
                self.warn("sense_has_wikitable", section)
                continue

            old_pos_text = str(pos)

            if not pos.senses:
                headline_idx = []
                sense_idx = []
                unhandled_idx = []

                for idx, line in enumerate(pos.headlines):
                    if not line:
                        continue
                    if is_header(section, line):
                        headline_idx.append(idx)
                    elif line and line[0] in "#*:":
                        sense_idx.append(idx)
                    else:
                        unhandled_idx.append(idx)

                #print("NO SENSES", sense_idx, headline_idx)
                if not sense_idx and len(headline_idx) == 1 and headline_idx[-1] == len(pos.headlines)-1:
                    assert len(section.content_wikilines) == len(pos.headlines)

                    #self.warn("empty_sense_list", section)

                    # Special handling for garbage templates
                    if ("ru-" in pos.headlines[-1] and "-alt" in pos.headlines[-1]) or \
                       ("ar-" in pos.headlines[-1] and ("-inf-" in pos.headlines[-1] or "-coll-" in pos.headlines[-1])) or \
                       any(x in pos.headlines[-1] for x in ["ar-root", "ja-see", "zh-see", "ar-verb form"]):
                            continue

                    lang_id = ALL_LANGS.get(section._topmost.title)
                    section.content_wikilines.append("")
                    section.content_wikilines.append("# {{rfdef|" + lang_id + "}}")
                    pos = sectionparser.parse_pos(section)
                    self.fix("missing_rfdef", section, "", "added rfdef to empty POS")

#                elif not sense_idx and len(headline_idx) and len(unhandled_idx):
#                        # Headline followed by lines that are missing #
#                        self.warn("no_senses", section)
#                        continue

                        # Special headling for headlines followed by lines that are missing # (needs manual verification)
#                        print("FIXING SENSES", headline_idx, len(pos.headlines), pos.headlines)
#                        for idx, line in enumerate(section.content_wikilines[headline_idx[-1]+1:], headline_idx[-1]+1):
#                            print(idx, line)
#                            if line:
#                                section.content_wikilines[idx] = "# " + line
#                        pos = sectionparser.parse_pos(section)
#                        self.fix("missing_prefix", section, "", "added missing prefix (manually reviewed)")

                else:

                    if not sense_idx:
                        self.warn("no_senses", section)

                    elif not(headline_idx):
                        self.warn("missing_headline", section)

                    # Warn on non-consecutive headlines
                    elif not unhandled_idx and headline_idx and any(headline_idx[x] != headline_idx[x]+1 for x in range(len(headline_idx)-1)):
                        continue
                        if section._children:
                            self.warn("multi_headlines", section)
                        else:
                            self.warn("multi_headlines_no_children", section)

                    # Warn on senses before the first headline
                    elif sense_idx[0] < headline_idx[0]:
                        if section._children:
                            self.warn("headline_after_senses", section)
                        else:
                            self.warn("headline_after_senses_no_children", section)

                    elif unhandled_idx and all(pos.headlines[x].startswith("<!--") and pos.headlines[x].endswith("-->") for x in unhandled_idx):
                        #print("___", section.page, section.path, [pos.headlines[x] for x in unhandled_idx])
                        #all(pos.headlines[x].startswith("<!--") and pos.headlines[x].endswith("-->") for x in unhandled_idx):
                        self.warn("comment_in_sense_list", section)

                    else:

                        text = "\n".join(pos.headlines[sense_idx[0]:])
                        if len(text) > 512 and unhandled_idx:
                            text = "\n".join(pos.headlines[x] for x in unhandled_idx)

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

#            if len(sense_list) > 1 and sense_list[-1]._type not in ["unknown", "sense"]:
#                parent = sense_list[0]
#                child = sense_list.pop()
#                child.parent = parent
#                child.level = parent.level +1
#                child.prefix = parent.prefix + ":"
#                child.style = self.TYPE_TO_STYLE[child._type]
#
#                parent._children.append(child)
#                self.fix("stray_" + child._type, section, parent.name, "adopted stray " + child._type)
#            else:
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
                    # THIS REQUIERES MANUAL VERIFICATION
                    #sense.level = 1
                    #sense.style = "#"
                    #sense.prefix = "#"
                    #self.fix("sense_prefix", section, f"sense{idx}", "fixed sense prefix  (manually verified)")

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
            # Only fix the style tags of for senses and sub-senses
            # This allows #* bare quote to be followed by #*: {{quote}}
            parent_is_sense = item._type == "sense" and item.style == "#"
            self.cleanup_sense_item(child, section, update_style=parent_is_sense)


    def fix_complex_byline(self, byline, section=None):

        m = re.search(sectionparser.PosParser.re_templates, byline.data)
        if not m:
            return

        template_type = sectionparser.PosParser.template_to_type[m.group('t')]

        if template_type in sectionparser.PosParser.ALL_NYMS:
            return self.fix_nym_byline(template_type, byline, section)
        else:

# manual cleanup
#            if template_type == "ux":
#                text = byline.data
#                text = text.rstrip(".")
#
#                if text != byline.data:
#                    byline._type = "ux"
#                    byline.data = text
#                    self.fix(f"{template_type}_cleanup", section, byline.name, f"removed . after ux template")
#                    return True

#                return self.fix_nym_byline(template_type, byline, section)
            if section:
                self.warn(f"complex_{template_type}", section, "sense" + byline.name[1:], str(byline))
            return

    def fix_nym_byline(self, template_type, byline, section):

        prev = None
        extra = byline.data
        while prev != extra:
            prev = extra
            extra = re.sub(r"\s*(<!--.*?-->|{{[^{}]*}})", "", prev)

        replacements = []
        extra_qualifiers = []
        extra_nyms = []

        full_extra = extra
#        extra = extra.replace("'&nbsp;", " ")
#        extra = extra.replace("'&ndash;", "-")
        extra = extra.strip("\",;. ")
        if extra:

            m = re.match(r"^('')?\(('')?(?P<q>[^()]*?)('')?\)('')?$", extra, flags=re.DOTALL)
            if m:
                extra_qualifiers.append(m.group('q'))
                replacements.append((full_extra, ""))

            else:
                self.warn(f"complex_{template_type}_unhandled_text", section, "sense" + byline.name[1:], str(byline))
                return

#            m = re.match(r"^('')?\(('')?(?P<q>[^()]*?)('')?\)('')?$", extra, flags=re.DOTALL)
#            else:

        wiki = mwparser.parse(byline.data)
        templates = wiki.filter_templates(recursive=False)
        if not templates:
            if section:
                self.warn(f"complex_{template_type}_no_templates", section, "sense" + byline.name[1:], str(byline))
            return

        template = templates.pop(0)

        # Only add qualifiers to single syn templates
        if extra_qualifiers and templates:
            if section:
                self.warn(f"complex_{template_type}_bare_quote_and_other_templates", section, "sense" + byline.name[1:], str(byline))
            return

        if templates:
            # Handle extra qualifier templates
            if len(templates) == 1 and templates[0].name.strip() in ["i", "q", "qual", "qualifier", "gloss", "lb"]:

                q_template = templates[0]

                first_param = 2 if q_template.name.strip() in ["lb"] else 1

                if not q_template.has(first_param):
                    print("no 1= param in qualifier", section.page, byline.data)
                    return

                if extra_qualifiers:
                    if section:
                        self.warn(f"complex_{template_type}_dup_qualifiers", section, "sense" + byline.name[1:], str(byline))
                    return

                if len(q_template.params) > first_param:
                    print("multiple qualifiers", section.page, byline.data)
                    qualifier = "; ".join(str(x.value) for x in q_template.params[first_param-1:])
                else:
                    qualifier = q_template.get(first_param)
                    if qualifier.startswith("''") and qualifier.endswith("''"):
                        qualifier = qualifier.strip("'")

                extra_qualifiers.append(qualifier)
                replacements.append((str(q_template), ""))
                #replacements.append((full_extra, ""))

            else:
                lang_id = template.get(1).strip()
                mergeable_templates = sectionparser.PosParser.TYPE_TO_TEMPLATES[template_type] + ["l", "l-line"]
                if all(t.name.strip() in mergeable_templates and t.get(1).strip() == lang_id for t in templates):
                    for t in templates:
                        if len(t.params) != 2:
                            return
                        extra_nyms.append(t.get(2).strip())
                        replacements.append((str(t), ""))
                    #replacements.append((full_extra, ""))

                else:
                    if section:
                        self.warn(f"complex_{template_type}_unhandled_template", section, "sense" + byline.name[1:], str(byline))
                    return

#        if template_type == "ux" and len(extra_qualifiers) == 1:
#            old = str(template) # + extra_data
#            template.add("q", extra_qualifiers[0])
#            new = str(template)
#            replacements.append((old, new))
#            if section:
#                self.fix(f"{template_type}_bare_qualifier", section, byline.name, f"merged bare {template_type} qualifier into template")


        if extra_qualifiers:
            if len(template.params) != 2 or not template.has(2):
                if section:
                    self.warn(f"complex_{template_type}_multi_values_with_qualifier", section, "sense" + byline.name[1:], str(byline))
                return

            old = str(template)
            if "<q" in template.get(2):
                if section:
                    self.warn(f"complex_{template_type}_multi_qualifiers", section, "sense" + byline.name[1:], str(byline))
                return

            for qualifier in extra_qualifiers:
                template.add(2, template.get(2).rstrip() + f"<qq:{qualifier}>")

            new = str(template)
            replacements.append((old, new))
            if section:
                self.fix(f"{template_type}_bare_qualifier", section, byline.name, f"merged bare {template_type} qualifier into template")

        if extra_nyms:
            max_param = max(int(p.name.strip()) for p in template.params if p.name.strip().isdigit())
            old = str(template)
            for idx, extra_nym in enumerate(extra_nyms, 1):
                template.add(max_param+idx, extra_nym)

            new = str(template)
            replacements.append((old, new))
            if section:
                self.fix(f"{template_type}_bare_extra", section, byline.name, f"merged bare {template_type} items into template")

        text = byline.data
        for old, new in replacements:
            new_text = text.replace(old, new)
            if new_text == text:
                return
                raise ValueError("ERROR replacing text", text, replacements)
            text = new_text

        text = text.rstrip(",; ")

        byline._type = template_type
        byline.data = text

        return True



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
                    fixed = self.fix_complex_byline(child, section)
                    if not fixed:
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
