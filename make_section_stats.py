#!/usr/bin/python3

import pywikibot
import re
import sys
import multiprocessing
import os

from collections import defaultdict
import enwiktionary_sectionparser as sectionparser
from autodooz.sections import WT_POS, WT_ELE, ALL_LANGS, COUNTABLE_SECTIONS

PATTERN_SIMPLE_REFS = r"(?i)(<\s*references\s*/>|{{reflist}})"

def log(errors, error, section, notes=None):
    if isinstance(section, str):
        path = section
    elif hasattr(section, "lineage"):
        path = ":".join(reversed(list(section.lineage)))
    else:
        path = section.title + ":"

    #print(path, error, notes)
    errors[error].append((path, notes))


error_header = {
    # Errors generated by sectionparser
    "comment_on_title": "Pages with a comment on the section header line",
    "text_on_title": "Pages with text on the section header line",

    # Errors generated here
    "enclosed_section_header": "Pages with a section header inside an html comment, ref tag, nowiki tag, or template",

    "trailing_open_html_comment": "Pages with an unclosed HTML comment",
    "trailing_open_template": "Pages with an unclosed template",
    "trailing_open_nowiki_tag": "Pages with an unclosed  <nowiki><nowiki></nowiki> tag",
    "trailing_open_ref_tag": "Pages with an unclosed  <nowiki><ref></nowiki> tag",

    "first_section_not_l2": "First section on the page is not L2",
    "duplicate_l2": "Duplicate L2 sections",

    "unexpected_counter": "Section title has a number but is not a countable section",
    "empty_section": "Pages with an empty section that needs manual review",

    "reference_tag_outside_references": "Pages where <nowiki><references/></nowiki> appears outside of a section named References",
    "ref_tag_without_references": "Pages with a <nowiki><ref></nowiki> tag (or equivalent) but no <nowiki><references/></nowiki> tag",
}

def format_error(error, items):

    if error in error_header:
        yield error_header[error]
        yield "\n"

    yield f"{len(items)} entries"
    yield "\n"

    for path, notes in sorted(items):
        page, extra = path.split(":", 1)
        line = []
        if len(extra) > 1:
            line.append(f": [[{page}|{path}]]")
        else:
            line.append(f": [[{page}]]")
        if notes:
            if "{{" in notes or "<" in notes:
                line.append(f" (<nowiki>{notes}</nowiki>)")
            else:
                line.append(f" ({notes})")

        yield "".join(line)

def export_error(prefix, error, items, summary):
    page = prefix + "/" + error
    save_page(page, "\n".join(format_error(error, items)), summary)

def export_errors(prefix, summary, errors):
    for error, items in errors.items():
        export_error(prefix, error, items, summary)

    # Update pages that no longer have any entries
    for error in error_header.keys()-errors.keys():
        export_error(prefix, error, [], summary)

def validate_entry(entry, errors):

    for section in entry.ifilter_sections():
        for line in section.content_wikilines:
            m = re.match("(^|^.*?\n)==[^=]+==", line, re.DOTALL)
            if m:
                log(errors, "enclosed_section_header", section, m.group(0).replace("\n", "\\n"))

    if entry._state:

        last_node = entry
        while last_node._children:
            last_node = last_node._children[-1]
        last_wikiline = last_node.content_wikilines[-1]
        bad_line = last_wikiline.splitlines()[0]

        if entry._state & 0xFF:
            log(errors, "trailing_open_template", entry, bad_line)

        if entry._state & 0x100:
            log(errors, "trailing_open_ref_tag", entry, bad_line)

        if entry._state & 0x200:
            log(errors, "trailing_open_nowiki_tag", entry, bad_line)

        if entry._state & 0x400:
            log(errors, "trailing_open_html_comment", entry, bad_line)

    if not entry._children:
        log(errors, "empty_page", entry)
        return

    if entry._children[0].level != 2:
        log(errors, "first_section_not_l2", entry._children[0])

    l2_titles = [e.title for e in entry._children]
    if len(l2_titles) != len(set(l2_titles)):
        duplicates = [title for title in l2_titles if l2_titles.count(title) > 1]
        log(errors, "duplicate_l2", entry, ", ".join(duplicates))

    for section in entry.ifilter_sections():

        if section.count and not section.title in COUNTABLE_SECTIONS:
            log(errors, "unexpected_counter", section)

        if not section.content_wikilines and not section._children:
            log(errors, "empty_section", section)

        if any(re.search(PATTERN_SIMPLE_REFS, wl) for wl in section.content_wikilines):
            if "References" not in section.lineage:
                if len(section.content_wikilines) == 1:
                    log(errors, "misnamed_references_section", section)
                else:
                    log(errors, "reference_tag_outside_references", section)

def upload_samples(base_url, samples, summary):

    sections = defaultdict(lambda: defaultdict(dict))

    for item, samples in sorted(samples.items()):
        if not samples:
            continue

        title, level = item
        section = title[0] if title[0].isalnum() else "Other"
        sections[section][title][level] = samples

    for section, titles in sections.items():
        data = []
        data.append("; Sections with <100 uses at a given level")
        data.append(" | ".join(f"[[{base_url}/{x}|{x}]]" if x != section else x for x in sorted(sections.keys(), key=lambda x: x if x == "Others" else "a"+x)))

        for title, levels in sorted(titles.items()):
            if all(x.isalnum() or x.isspace() for x in title):
                data.append(f"==={title}===")
            else:
                data.append(f"===<nowiki>{title}</nowiki>===")
            for level, samples in levels.items():
                data.append(f"; L{level}: " + ", ".join(f"[[{x}#{title}|{x}]]" for x in sorted(samples)))

        page = base_url + f"/{section}"
        page_text = "\n".join(data)
#        print(page_text)
#        return
#
        save_page(page, page_text, summary)

site = None
def save_page(page, page_text, summary):

    # no summary signals that the pages should be saved locally
    if not summary:
        dest = page.lstrip("/").replace("/", "_").replace(":", "_")
        with open(dest, "w") as outfile:
            outfile.write(page_text)
            print("saved", dest)
        return

    global site
    if not site:
        site = pywikibot.Site()
    wiki_page = pywikibot.Page(site, page)
    if wiki_page.text == page_text:
        print(f"{page} has no changes")
        return
    wiki_page.text = page_text
    print(f"saving {page}")
    wiki_page.save(summary)

def upload_stats(base_url, stats, summary):

    title_stats = defaultdict(dict)
    table_types = {}
    max_level = defaultdict(int)

    for item, count in sorted(stats.items()):
        title, level = item
        title_stats[title][level] = count

        if title not in table_types:
            if title in ALL_LANGS:
                table_type = "Languages"
            elif title in WT_POS:
                table_type = "WT:POS"
            elif title in WT_ELE:
                table_type = "WT:ELE"
            else:
                table_type = "Nonstandard"
            table_types[title] = table_type
        else:
            table_type = table_types[title]

        if level > max_level[table_type]:
            max_level[table_type] = level

    tables = defaultdict(list)
    for table_type in ["Languages", "WT:POS", "WT:ELE", "Nonstandard"]:
        tables[table_type] = []
        header = ["Section"]
        for level in range(2,max_level[table_type]+1):
            header.append(f"L{level}")
        header.append("Total")
        tables[table_type].append(header)

    for title in sorted(title_stats):
        table_type = table_types[title]
        table = tables[table_type]
        row = []
        row.append(f"{title}")
        total = 0
        for level in range(2,max_level[table_type]+1):
            count = title_stats[title].get(level, "")
            if count:
                total += count
            row.append(count)
        row.append(total)
        table.append(row)


    res = []
    for table_type in ["Languages", "WT:POS", "WT:ELE", "Nonstandard"]:
        table = tables[table_type]
        totals = [0] * (max_level[table_type])
        for row in table[1:]:
            for i,count in enumerate(row[1:]):
                if count:
                    totals[i] += count
                    # make the title linkable if there's a category with < 100
                    if count < 100 and not row[0].startswith("[["):
                        title = row[0]
                        section = title[0] if title[0].isalnum() else "Other"
                        if all(x.isalnum() or x.isspace() for x in title):
                            row[0] = f"[[{base_url}/{section}#{title}|{title}]]"
                        else:
                            row[0] = f"[[{base_url}/{section}#{title}|<nowiki>{title}</nowiki>]]"

        summary = ["Total"] + totals
        table.append(summary)

        title = f"{table_type} sections"
        res.append(f"""<div class="NavFrame">
<div class="NavHead" style="text-align: left;">{title}</div>
<div class="NavContent derivedterms" style="text-align: left;">""")

        res.append(make_wiki_table(table, extra_class="sortable", num_headers=1, num_footers=1))
        res.append("</div></div>")

    page_text = "\n".join(res)
#    print(page_text)
#    return

    page = base_url
    save_page(page, page_text, summary)


def make_wiki_table(rows, caption=None, extra_class=None, num_headers=0, num_footers=0):
    cls = f"wikitable {extra_class}" if extra_class else "wikitable"
    lines = ['{| class="' + cls + '"' ]
    if caption:
        lines.append(f'|+ class="nowrap" | {caption}')
    for i, row in enumerate(rows):
        lines.append("|-")
        divider = "!" if i<num_footers or i>len(rows)-1-num_footers else "|"
        lines.append(divider + (divider*2).join(map(str,row)))

    lines.append("|}")

    return "\n".join(lines)



def iter_wxt(datafile, options, limit=None, show_progress=False):

    if not os.path.isfile(datafile):
        raise FileNotFoundError(f"Cannot open: {datafile}")

    from enwiktionary_wordlist.wikiextract import WikiExtractWithRev
    parser = WikiExtractWithRev.iter_articles_from_bz2(datafile)

    count = 0
    for entry in parser:

        if ":" in entry.title or "/" in entry.title:
            continue

        if not count % 1000 and show_progress:
            print(count, end = '\r', file=sys.stderr)

        if limit and count >= limit:
            break
        count += 1

        yield entry.text, entry.title, options

def process(args):

    text, title, _ = args

    errors = defaultdict(list)

    section_errors = []
    entry = sectionparser.parse(text, title, section_errors)

    for error, section, details in section_errors:
        log(errors, error, section, details)

    validate_entry(entry, errors)

    sections = [ (section.title, section.level) if section.title else ("(no section title)", section.level)
            for section in entry.ifilter_sections() ]

    return title, errors, sections

def main():

    import argparse

    parser = argparse.ArgumentParser(description="Find fixable entries")
    parser.add_argument("wxt", help="Wiktionary extract file")
    parser.add_argument("--save", help="Save to wiktionary with specified commit message")
    parser.add_argument("--limit", type=int, help="Limit processing to first N articles")
    parser.add_argument("--progress", help="Display progress", action='store_true')
    parser.add_argument("-j", help="run N jobs in parallel (default = # CPUs - 1", type=int)
    args = parser.parse_args()

    from enwiktionary_wordlist.wikiextract import WikiExtractWithRev
    parser = WikiExtractWithRev.iter_articles_from_bz2(args.wxt)

    stats = defaultdict(int)
    samples = defaultdict(set)
    errors = defaultdict(list)

    if not args.j:
        args.j = multiprocessing.cpu_count()-1

    iter_entries = iter_wxt(args.wxt, None, args.limit, args.progress)

    if args.j > 1:
        pool = multiprocessing.Pool(args.j)
        iter_items = pool.imap_unordered(process, iter_entries, 100)
    else:
        iter_items = map(process, iter_entries)

    for page, page_errors, title_levels in iter_items:
        for item in title_levels:
            stats[item] += 1

            if samples[item] is not None:
                samples[item].add(page)
                if len(samples[item]) > 100:
                    del samples[item]
                    samples[item] = None

        # merge errors
        for error, items in page_errors.items():
            errors[error] += items

    export_errors("User:JeffDoozan/lists", args.save, errors)
    if args.save:
        base_url = "User:JeffDoozan/stats/sections/latest"
        upload_stats(base_url, stats, args.save)
        upload_samples(base_url, samples, args.save)


if __name__ == "__main__":
    main()
