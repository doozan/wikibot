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

import enwiktionary_sectionparser as sectionparser

def get_verb_section(entry):
    langs = entry.filter_sections(recursive=False, matches="Portuguese")
    if not len(langs) == 1:
        return
    lang = langs[0]

    verbs = lang.filter_sections(matches="Verb")
    if not len(verbs) == 1:
        return
    return verbs[0]

def merge(page_text, page_title, summary, options, src_text, src_title):
    print("X"*80)
    print("MERGE", src_title, "-->", page_title)
    entry = sectionparser.parse(page_text, page_title)
    if not entry:
        return

    dest = get_verb_section(entry)
    if not dest:
        return

    src_entry = sectionparser.parse(src_text, src_title)
    if not src_entry:
        return

    src = get_verb_section(src_entry)
    if not src:
        return

    dest.content_wikilines += [line for line in src.content_wikilines if line and "{{head" not in line]
    dest._children += [child for child in src._children if child.title not in ["Conjugation", "Quotations"]]

    summary.append(f"/*Portuguese*/ moved refleive verb data from {src_title} (manually assisted)")
    return str(entry)

def remove(page_text, page_title, summary, options, dest_title):
    entry = sectionparser.parse(page_text, page_title)
    if not entry:
        return page_text

    section = get_verb_section(entry)
    if not section:
        raise ValueError(f"No verb section found in merge source {page_title}, this should never happend")

    section._children = []
    section.content_wikilines = ["{{head|pt|verb form}}", "", "# {{reflexive of|pt|" + dest_title + "}}"]
    summary.append(f"/*Portuguese*/ moved refleive verb data to lemma {dest_title} (manually assisted)")

    return str(entry)
