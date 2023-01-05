#!/usr/bin/python3
#
# Copyright (c) 2021 Jeff Doozan
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

"""
List translation problems
"""

from collections import defaultdict
import os
import re
import sys
from autodooz.fix_t9n import T9nFixer
from autodooz.sections import ALL_LANGS
from autodooz.wikilog import WikiLogger, BaseHandler
from autodooz.wikilog_language import WikiByLanguage as BaseWikiByLanguage
from enwiktionary_translations import TranslationTable, TranslationLine, UNKNOWN_LANGS, LANG_PARENTS
from enwiktionary_translations.language_aliases import language_aliases as LANG_ALIASES
from enwiktionary_wordlist.all_forms import AllForms
from enwiktionary_wordlist.wikiextract import WikiExtract
from collections import namedtuple
from enwiktionary_parser.sections.pos import ALL_POS

stats = {
    "total_tables": 0,
    "total_entries": 0,
    "sections_with_tables": 0,
    "pages_with_tables": 0,
    "lang_entries": defaultdict(int)
}

class Logger(WikiLogger):
    _paramtype = namedtuple("params", [ "error", "page", "section", "gloss", "language", "line", "highlight" ])

def save_to_file(self, dest, page_text):
    dest = dest.lstrip("/").replace("/", "_")
    with open(dest, "w") as outfile:
        outfile.write(page_text)
        print("saved", dest)

error_to_text = {
    "allow_missing_has_template": "Has both translation and non-translation",
    "footer_has_posttext": "Table footer has post-text",
    "footer_has_pretext": "Table footer has pre-text",
    "header_has_posttext": "Table header has post-text",
    "item_html_comment": "Entry HTML comment",
    "merged_genders": "Genders outside t-template",
    "missing_bottom_template": "Table has no bottom template",
    "missing_t": "No translation template",
    "missing_translation_target": "No translation target",
    "mixed_delimiters": "List items separated by both comma and semicolon",
    "multiple_genders_sources": "Genders in t-template and g-template",
    "multiple_qualifier_templates": "Multiple qualifiers",
    "multiple_t_templates": "Multiple t-templates",
    "nested_template": "Nested templates",
    "no_tables": "No tables",
    "outside_pos": "Table found outside a POS section",
    "t_is_l": "Uses l-template instead of t-template",
    "table_html_comment": "Table HTML comment",
    "unexpected_data": "Unexpected data",
    "unexpected_language": "Unexpected language",
    "unexpected_template": "Unexpected template",
    "wrong_language_code": "Wrong language code",
}

class WikiByLanguage(BaseWikiByLanguage):

    _indextype = namedtuple("index_items", [ "link", "entries", "errors" ])

    def format_entry(self, entry, prev_entry):
        e = entry
        lines = [f": [[{e.page}#Translations|{e.page}]] ({e.section}: {e.gloss})"]

        if e.line:
            if e.highlight:
                if e.line.count(e.highlight) >= 1:
                    temp = e.line.replace(e.highlight, f"</nowiki>'''<nowiki>{e.highlight}</nowiki>'''<nowiki>")
                    temp = f"<nowiki>{temp}</nowiki>"
                    temp = ":: " + temp.replace("<nowiki></nowiki>", "")
                else:
                    temp = f":: <nowiki>{e.line}</nowiki> ('''<nowiki>{e.highlight})</nowiki>''')"
                lines.append(temp)
            else:
               lines.append(f":: <nowiki>{e.line}</nowiki>")
        elif e.highlight:
            lines.append(f":: <nowiki>{e.highlight}</nowiki>")

        return lines

    def get_section_header(self, base_path, page_name, section_entries, prev_section_entries, pages):
        res = []
        item = section_entries[0]
        prev_item = prev_section_entries[-1] if prev_section_entries else None
        if not prev_item or prev_item.language != item.language:
            res.append(f"=={item.language}==")
            count = stats["lang_entries"][item.language]
            res.append(f"''This language has translations in {count} of {stats['total_tables']} ({(count/stats['total_tables'])*100:.2f}%) translation tables''<br>")

        count = sum(map(len, [x for x in pages[page_name] if x[0].language == item.language]))
        # To avoid cluttering the header summary, only use subheaders if the language has
        # more than 80 entries
        error = error_to_text.get(item.error, item.error)
        if count > 80:
            res.append(f"==={error}===")
            res.append(f"; {len(section_entries)} item{'s' if len(section_entries)>1 else ''}")
        else:
            res.append(f"'''{error}''': {len(section_entries)} item{'s' if len(section_entries)>1 else ''}")

        if item.error == "wrong_language_code":
            res.append(f"''Expected language code is '''{ALL_LANGS.get(LANG_ALIASES.get(item.language, item.language), '')}'''''<br>")
        return res

    def format_section_index(self, base_path, page_name, section_entries, prev_section_entries, pages):
        item = section_entries[0]

        # NOTE: When changing the link format, ensure that index_sort() isn't affected
        link = f"[[{base_path}/{page_name}#{item.language}|{item.language}]]"

        entries = stats["lang_entries"][LANG_ALIASES.get(item.language, item.language)]
        errors = sum(map(len, [x for x in pages[page_name] if x[0].language == item.language]))
        return [self._indextype(link, entries, errors)]

    def index_header(self, index_items):
        return [("Language", "Entries", "Errors")]

    @staticmethod
    def get_lang(link):
        if not link.startswith("["):
            return link

        # return language name split from [[mismatched/G#German Low German|German Low German]]
        return link.split("#")[1].split("|")[0]

    def index_sort(self, items):

        # Build a list of all languages with entries
        all_langs = stats["lang_entries"]
        langs_with_errors = { self.get_lang(item.link) for item in items }
        langs_without_errors = all_langs.keys() - langs_with_errors

        all_items = items
        for language in langs_without_errors:
            entries = stats["lang_entries"][language]
            all_items.append(self._indextype(language, entries, 0))

        return sorted(all_items, key=lambda x: (x.entries*-1, self.get_lang(x.link)))

    def index_footer(self, index_items):
        total_entries = sum(stats["lang_entries"].values())
        return [(f"Total ({len(index_items)} languages)", total_entries, sum(x.errors for x in index_items))]


class WikiByError(BaseHandler):

    _indextype = namedtuple("index_items", ["link", "count"])

    def make_page(self, *args, **nargs):
        page_lines = super().make_page(*args, **nargs)
        limit = 15000
        if len(page_lines) > limit:
            return page_lines[:limit] + [f"Page truncated to {limit} lines"]
        return page_lines

    def format_entry(self, entry, prev_entry):
        e = entry
        lines = [f": [[{e.page}#Translations|{e.page}]]:{e.section}:{e.gloss}"]

        language = f"{e.language}: " if e.language else ""
        if e.line:
            if e.highlight:
                if e.line.count(e.highlight) >= 1:
                    temp = e.line.replace(e.highlight, f"</nowiki>'''<nowiki>{e.highlight}</nowiki>'''<nowiki>")
                    temp = f"<nowiki>{temp}</nowiki>"
                    temp = f":: {language}" + temp.replace("<nowiki></nowiki>", "")
                else:
                    temp = f":: {language}<nowiki>{e.line}</nowiki> ('''<nowiki>{e.highlight})</nowiki>''')"
                lines.append(temp)
            else:
               lines.append(f":: {language}<nowiki>{e.line}</nowiki>")
        elif e.highlight:
            lines.append(f":: {language}<nowiki>{e.highlight}</nowiki>")

        return lines

    def sort_items(self, items):
        return sorted(items, key=lambda x: (x.error, x.page, x.section))

    def is_new_page(self, page_sections, section_entries):
        # each error is a new page
        return page_sections and page_sections[-1][-1].error != section_entries[0].error

    def is_new_section(self, item, prev_item):
        # Split by error
        return prev_item and prev_item.error != item.error

    def page_name(self, page_sections, prev):
        # named by error code
        return page_sections[0][0].error

    def get_section_header(self, base_path, page_name, section_entries, prev_section_entries, pages):
        error = error_to_text.get(section_entries[0].error, section_entries[0].error)
        res = [f"==={error}==="]
        res.append(f"; {len(section_entries)} items")
        return res

    def get_section_index(self, base_path, page_name, section_entries, prev_section_entries, pages):
        link = f"[[{base_path}/{page_name}|{page_name}]]"
        return [self._indextype(link, len(section_entries))]

    def index_header(self, index_items):
        return [("Error", "#")]

    def index_sort(self, items):
        return sorted(items, key=lambda x: (x.count*-1, x.link))

    def index_footer(self, index_items):
        return [("Total", sum(x.count for x in index_items))]


class FileByError(WikiByError):
    save_page = save_to_file
    def save(self, *args, **nargs):
        super().save(*args, **nargs, commit_message=None)

class FileByLanguage(WikiByLanguage):
    save_page = save_to_file
    def save(self, *args, **nargs):
        super().save(*args, **nargs, commit_message=None)

def main():

    import argparse
    argparser = argparse.ArgumentParser(description="Find lemmas with only 'form of' senses")
    argparser.add_argument("--trans", help="Extract file to read")
    argparser.add_argument("--allforms", help="Allforms for resolving forms to lemmas")
    argparser.add_argument("--save", help="Save to wiktionary with specified commit message")
    argparser.add_argument("--date", help="Date of the database dump (used to generate page messages)")
    argparser.add_argument("--limit", type=int, help="Limit processing to first N articles")
    argparser.add_argument("--progress", help="Display progress", action='store_true')
    argparser.add_argument("--dump-aliases", help="Dump likely language aliases", action='store_true')
    argparser.add_argument("--dump-parents", help="Dump likely parent languages", action='store_true')
    args = argparser.parse_args()

    allforms = AllForms.from_file(args.allforms) if args.allforms else None
    if not os.path.isfile(args.trans):
        raise FileNotFoundError(f"Cannot open: {args.trans}")

    fixer = T9nFixer(allforms)
    logger = Logger()

    def log(error, page, pos, gloss, language, line="", highlight=""):
        if error is None:
            raise ValueError("error is none"    )
        if page is None:
            raise ValueError("page is none")
        if pos is None:
            raise ValueError("pos is none")
        if gloss is None:
            gloss = ""
        if language is None:
            language = ""
        if line is None:
            line = ""
        if highlight is None:
            highlight = ""

        logger.add(error, page, pos, gloss, language, line, highlight)

#        if language:
#            langlogger.add(error, page, pos, gloss, language, line, highlight)

#        if error != "text_outside_template":
#            logger.add(error, page, pos, gloss, line, highlight)

    count = 0
    max_val = 0
    pages_with_tables = set()

    for article in WikiExtract.iter_articles_from_bz2(args.trans):
        text = article.text
        path = article.title.split(":")
        page = path[0]
        pos = path[-1]

        if pos not in ALL_POS:
            log("outside_pos", page, pos, None, None, path)

        count += 1
        if not count % 1000 and args.progress:
            print(count, end = '\r', file=sys.stderr)
        if args.limit and count > args.limit:
            break

#        if page != "pie-eyed":
#            continue

#        if pathstr != "veggie:English:Adjective":
#        if pathstr != "I love you:English:Phrase":
#            continue
#        print("\n", count)

#        val = timeit.timeit(lambda: list(TranslationTable.find_tables(text, page, pos)), number=1)
#        if val > max_val:
#            max_val = val
#            max_page = pathstr
#        continue

        tables = list(TranslationTable.find_tables(text))
        if not len(tables) and not re.search("{{\s*(trans-see|checktrans|see translation)", text):
            log("no_tables", page, pos, None, None)

#            max_page = "X"


        pages_with_tables.add(page)
        stats["sections_with_tables"] += 1
        for table_lines in tables:
            table_lines = table_lines.splitlines()
#            print(table_lines)
#            exit()
#            max_val += len(table_lines)
#            continue

            table = TranslationTable(page, pos, table_lines, log_function=log)

            stats["total_tables"] += 1
            seen = set()
            for item in table.items:
                if isinstance(item, TranslationLine) and item.lang_id not in seen:
                    stats["total_entries"] += len(item.entries)
                    stats["lang_entries"][lang_ids[item.lang_id]] += 1
                    seen.add(item.lang_id) # Don't count more than one entry per table

            if len(tables) > 1 and not table.gloss and table.template in ["tran-top", "trans-top-see", "trans-top-also"]:
                table.log("no_gloss")
            fixer.cleanup_table(table)

#            if "\n".join(map(str.strip,table_lines)) != str(table):
#                table.log("botfix_formatting")
#                print("OLD", page, pos, file=sys.stderr)
#                print("\n".join(table_lines), file=sys.stderr)
#                print("NEW", page, pos)
#                print(str(table))
                #exit()

    stats["pages_with_tables"] = len(pages_with_tables)

#    print(max_val, max_page)

#    base_url = "User:JeffDoozan/lists/translations" if args.save else "Xtranslations"
#    langlogger.save(base_url, args.save)

    if args.save:
        base_url = "User:JeffDoozan/lists/translations"
        logger.save(base_url, WikiByLanguage, commit_message=args.save, page_limit=1000, data_date=args.date)
        logger.save(base_url+"/by_error", WikiByError, commit_message=args.save, data_date=args.date)
    else:
        dest = "Xtranslations"
        logger.save(dest, FileByLanguage, page_limit=1000, data_date=args.date)
        logger.save(dest+"/by_error", FileByError, data_date=args.date)

    # Dump nested language aliases
    if args.dump_aliases:
        print("language_aliases = {")
        #for lang,codes in sorted(UNKNOWN_LANGS.items(), key=lambda x: sum(x[1].values())*-1):
        for lang,codes in sorted(UNKNOWN_LANGS.items()):
            for code, count in sorted(codes.items(), key=lambda x: x[1]*-1):
                if count > 20:
                    print(f"    '{lang}': '{lang_ids[code]}', # {code} found in {count} entries")
                break
        print("}")

    if args.dump_parents:
        print("language_parents = {")
        for lang,count in sorted(LANG_PARENTS.items()):
            if count > 20:
                print(f"    '{lang}', # used in {count} entries")
        print("}")

    colons = [x for x in lang_ids.values() if ":" in x]
    if colons:
        raise ValueError("A language exists with a colon in the name, this may cause problems for nested languages that use : as a separator")

    print(f"Total pages with tables: {stats['pages_with_tables']}")
    print(f"Total sections with tables: {stats['sections_with_tables']}")
    total_lines = sum(stats["lang_entries"].values())
    print(f"Total language lines in tables: {total_lines}")
    print(f"Total translation entries: {stats['total_entries']}")

if __name__ == "__main__":
    main()
