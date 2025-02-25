import enwiktionary_sectionparser as sectionparser
import mwparserfromhell as mwparser
import re
import sys

from autodooz.sections import ALL_LANGS
from collections import namedtuple
from enwiktionary_sectionparser.utils import wiki_contains
from autodooz.quotes.parser import QuoteParser, LINK
from .quotes.name_labeler import NameLabeler
from .quotes.names import *
from enwiktionary_sectionparser.posparser import BARE_QUOTE_LINE_RX

# Templates that can appear inside a passage
ALLOWED_PASSAGE_TEMPLATES = {"...", "sic", "smallcaps", "w", "l", "lang"}

# Templates that should never appear in a passage
DISALLOWED_PASSAGE_TEMPLATES = {"audio"}

# UX templates that can contain passages and translations
ALLOWED_UX_TEMPLATES = [ "usex", "ux", "uxi", "quote", "quotei", "lang" ]

# TODO: allow ko-usex, but 1= is passage not langid

# Templates that can't be merged but shouldn't generate a warning
UNHANDLED_UX_TEMPLATES = ["ja-usex", "zh-usex", "ja-x", "th-x", "zh-x", "zh-q"]

ALLOWED_UX_PARAMS = {
    "1": None,

    "2": "passage",
    "text": "passage",
    "passage": "passage",

    "3": "translation",
    "t": "translation",
    "translation": "translation",

    "4": "transliteration",
    "tr": "transliteration",
    "translit": "transliteration",
    "transliteration": "transliteration",

    "lit": "lit",

    "inline": None,

    "sc": "sc",
    "subst": "subst",
    "norm": "norm",
    "footer": "footer",
}

def wikilines_to_quote_params(wikilines, prefix, warn, handle_ux_templates=False):
    passage_wikilines = []
    translation_wikilines = []

    offset = 0
    while offset < len(wikilines) and wikilines[offset].startswith(prefix + ":"):

        if re.match(re.escape(prefix) + r":[^#:*]", wikilines[offset]):
            if translation_wikilines and passage_wikilines:
                warn("multi_passage", "\n".join(wikilines[:offset]))
                return
            passage_wikilines.append(wikilines[offset])

        elif re.match(re.escape(prefix) + r"::[^#:*]", wikilines[offset]):
            if not passage_wikilines:
                warn("translation_before_passage", "\n".join(wikilines[:offset]))
                return
            translation_wikilines.append(wikilines[offset])

        else:
            warn("unhandled_following_line", "\n".join(wikilines[:offset]))
            return

        offset += 1

    if not offset:
        # Check for quote headlines followed (incorrectly) by an unindented {{quote}} or {{quotei}}
        if offset < len(wikilines) and re.match(re.escape(prefix) + r"\s*\{\{\s*(quote|quotei)\s*\|", wikilines[offset]):
            passage_wikilines.append(wikilines[offset])
            offset +=1
        else:
            return

    res = get_passage_params(passage_wikilines, translation_wikilines, warn, handle_ux_templates)
    if not res:
        return

    return offset, res


def get_passage_params(passage_wikilines, translation_wikilines, warn, handle_ux_templates):

    """ Returns dictionary that may contain values for
    passage, translation, transliteration, footer """

    res = get_passage(passage_wikilines, warn, handle_ux_templates)
    if not res:
        return

    if "passage" not in res:
        warn("no passage", "\n".join(passage_wikilines))
        return

    if translation_wikilines:
        if "translation" in res:
            warn("multi_translations", "\n".join(passage_wikilines + translation_wikilines))
            return
        translation = get_translation(translation_wikilines)
        if not translation:
            warn("no_translation", "\n".join(translation_wikilines))
            return
        res["translation"] = translation

    if wiki_contains("|", res["passage"]):
        warn("pipe_in_passage", res["passage"])
        return

    if wiki_contains("|", res.get("translation", "")):
        warn("pipe_in_translation", res["translation"])
        return

    if wiki_contains("|", res.get("transliteration", "")):
        warn("pipe_in_translit", res["transliteration"])
        return

    return res

def get_passage(passage_wikilines, warn, handle_ux_templates):
    converted_template = False

    passage = "<br>".join(l.lstrip("#*:").strip() for l in passage_wikilines)

    if "<math>" in passage:
        warn("math_tag_in_passage", passage)
        return

    if "|" not in passage:
        return {"passage": passage}

    # Get all template names (without recursion)
    wiki = mwparser.parse(passage)
    templates = [t.name.strip() for t in wiki.ifilter_templates(recursive=False)]

    # If all templates are allowed, no further processing needed
    if not set(templates) - ALLOWED_PASSAGE_TEMPLATES:
        return {"passage": passage}

    # Fail if not handling UX templates
    if not handle_ux_templates:
        return

    if set(templates) & DISALLOWED_PASSAGE_TEMPLATES:
        return

    # verify that there is no text outside the template
    t = next(wiki.ifilter_templates(recursive=False))
    if str(t) != passage.strip():
        warn("text_outside_ux_template_in_passage", passage)
        return

    # don't handle and don't log ja-usex as an error (quote- templates don't handle japanese)
    if templates[0] in UNHANDLED_UX_TEMPLATES:
        return

    # if it's an expected UX template
    if templates[0] not in ALLOWED_UX_TEMPLATES:
        warn("unhandled_template_in_passage", passage)
        return

    # extract values from ux template
    if any(p.name.strip() not in ALLOWED_UX_PARAMS for p in t.params):
        warn("unhandled_ux_template_param_in_passage", passage)
        return

    res = {}
    for p, k in ALLOWED_UX_PARAMS.items():
        # Ignore params that don't map to a value
        if not k:
            continue
        if t.has(p):
            if p in res:
                warn(f"multiple_{k}_values", str(t))
                return
            res[k] = t.get(p).value.strip()

    return res

def get_translation(translation_wikilines):
    translation = "<br>".join(l.lstrip("#*: ") for l in translation_wikilines)

    wiki = mwparser.parse(translation)
    templates = [t.name.strip() for t in wiki.ifilter_templates(recursive=False)]

    if set(templates) & DISALLOWED_PASSAGE_TEMPLATES:
        return

    return translation

class QuoteFixer():

    def dprint(self, *args, **kwargs):
        if self.debug:
            print(args, kwargs, file=sys.stderr)

    def fix(self, code, section, details):
        if self._summary is not None:
            self._summary.append(f"/*{section.path}*/ {details}")

        page = list(section.lineage)[-1]
        self._log.append(("autofix_" + code, page))

    def warn(self, code, section, details=None):
        page = list(section.lineage)[-1]
        self._log.append((code, page, details))

    def __init__(self, debug=False, all_locations=None, all_journals=None, all_publishers=None, aggressive=False):
        self._summary = None

        self._log = []
        self.debug=debug
        self.parser = QuoteParser(debug, all_locations, all_journals, all_publishers)

        # Proposed changes will be manually, verified, be aggressive
        self.aggressive=aggressive

    def get_quote_params(self, text):

        print("___")
        print(text)
        print("PARSING")

        # Fail if comments
        if "<!--" in text or "-->" in text:
            #self.warn("html_comment")
            return

        parsed = self.parser.get_parsed(text)
        return self.convert_parsed_to_params(parsed)

    def convert_parsed_to_params(self, parsed):

        fingerprint = self.get_fingerprint(parsed)

        transformer = self.get_transformer(fingerprint)
        if not transformer:
            print("1UNHANDLED:", fingerprint)
            if any(p.type.endswith("unhandled") for p in parsed):
                fingerprint = self.get_fingerprint(parsed, condense_unhandled=True)
                transformer = self.get_transformer(fingerprint)

            if not transformer:
                print("2UNHANDLED:", fingerprint)
                return

        handler = transformer["_handler"]

        print("FINGERPRINT:", fingerprint)
        self.apply_transformation(parsed, transformer)

        params = handler(self, parsed)
        if params:
            print("PARAMS:", params)
        else:
            print("NOPARAMS", parsed)

        self.cleanup_params(params)

        return params

    def get_fingerprint(self, parsed, condense_unhandled=False):
        fingerprint = []
        for p in parsed:

            if p.type.endswith("unhandled"):
                if condense_unhandled:
                    fingerprint.append(f"{p.type}<*>")
                else:
                    fingerprint.append(f"{p.type}<{p.values[0]}>")

            elif p.type.endswith("separator"):
                continue
            else:
                fingerprint.append(p.type)

        return tuple(fingerprint)

    def get_transformer(self, fingerprint):
        fp_keys = {k for k in fingerprint}
        transformers = [ h[4] for h in self._all_handlers if self.can_handle(h, fingerprint, fp_keys) ]
        if not transformers:
            return

        if not all(t == transformers[0] for t in transformers):
            pass
            #print("Multi matches", fingerprint, transformers)
            #raise ValueError("Multi matches", fingerprint, transformers)
        return transformers[-1]


    # TODO: Handle unhandled<text> - match "unhandled" and "text"
    def can_handle(self, handler, fingerprint, fingerprint_keys):
        must_contain, match_list, may_contain, cannot_contain, transformer = handler

        # If must_contain is a list of sets, use the first set
        # that the fingerprint passes
        if must_contain and isinstance(must_contain, list):
            found = None
            for k in must_contain:
                if not k-fingerprint_keys:
                    found = k
                    break
            if not found:
                return False
            must_contain = found

        if must_contain and must_contain-fingerprint_keys:
            return False

        fp_list = []
        for f in fingerprint:
            if f in match_list:
                fp_list.append(f)
            elif f not in may_contain and f not in must_contain:
                return False
            elif f in cannot_contain:
                return False

        return match_list == fp_list

    def get_passage(self, passage_wikilines, section=None):
        lines = []
        converted_template = False
        for line in passage_wikilines:

            passage = line.lstrip("#*: ")
            if "|" in passage:

                m = re.match(r"^{{(?:quote|ux)\|[^|]*\|(.*)}}\s*$", passage, re.DOTALL)
                if m:
                    passage = m.group(1)
                    if passage.count("|") == 1 and "|t=" not in passage and "|translation=" not in passage:
                        passage = passage.replace("|", "|t=")

                    passage = passage.replace("|translation=", "|t=")

                    if converted_template:
                        if section:
                            self.warn("passage_has_multi_templates", section)
                        return
                    converted_template = True

            lines.append(passage)

        passage = "<br>".join(lines)

        passage, _, translation = passage.partition("|t=")

        if wiki_contains("|", passage):
            if section:
                self.warn("pipe_in_passage", section, passage)
            return

        if "<math>" in passage:
            self.warn("math_tag_in_passage", section, passage)
            return

        return passage, translation


    def get_translation(self, translation_wikilines):
        return "<br>".join(l.lstrip("#*: ") for l in translation_wikilines)



    def convert_quotes(self, section, title):

        lang_id = ALL_LANGS.get(section._topmost.title)
        if not lang_id:
            return

        changed = False
        to_remove = []

        for idx, wikiline in enumerate(section.content_wikilines):
            m = re.match(BARE_QUOTE_LINE_RX, wikiline)
            if not m:
                continue

            prefix = m.group('prefix')

            params = self.get_quote_params(m.group('quote'))

            warn = lambda e, d: self.warn(e, section, d)
            res = wikilines_to_quote_params(section.content_wikilines[idx+1:], prefix, warn, bool(params))
            if not res:
                continue
            offset, passage_params = res

            if not params:
                self.warn("unparsable_line", section, wikiline)
                if passage_params:
                    template_line = self.get_quote_template(prefix, section, passage_params)
                    # Only convert bare passages to {{quote}} for languages that benefit from having translations
                    if not template_line or "|mul|" in template_line or "|en|" in template_line:
                        continue
                    new_wikiline = wikiline + "\n" + template_line
                else:
                    continue
            else:
                new_wikiline = self.get_new_wikiline(prefix, section, params, passage_params)

            if not new_wikiline:
                continue

            section.content_wikilines[idx] = new_wikiline

            for to_remove_idx in range(idx+1, idx+offset+1):
                to_remove.append(to_remove_idx)

            changed = True

        for idx in reversed(to_remove):
            del section.content_wikilines[idx]

        return changed

    def get_quote_template(self, prefix, section, passage_params):
        lang_id = ALL_LANGS.get(section._topmost.title)
        new_wikiline = [ prefix + ":" + " {{quote|" + lang_id ]

        if lang_id == "en" and passage_params.get("translation"):
            self.warn("english_has_translation", section, passage_params)
            return

        ORDERED_PARAMS = ["passage", "transliteration", "translation"]
        for k in ORDERED_PARAMS:
            if passage_params.get(k):
                if k == "passage":
                    new_wikiline.append(f"|{passage_params[k]}")
                else:
                    new_wikiline.append(f"\n|{k}={passage_params[k]}")
        for k,v in sorted(passage_params.items()):
            if k in ORDERED_PARAMS:
                continue
            new_wikiline.append(f"|{k}={passage_params[k]}")

        new_wikiline[-1] += "}}"
        return "".join(new_wikiline)


    def get_new_wikiline(self, prefix, section, params, passage_params, template_override=None):

        lang_id = ALL_LANGS.get(section._topmost.title)

        if template_override:
            template = template_override
        else:
            template_type = "cite" if section.title in ["References", "Further reading", "Etymology"] else "quote"
            source = params.pop("_source")
            template = template_type + "-" + source

            if not self.is_valid_template(template, params):
                print("BAD TEMPLATE", template, params)
                return

        new_wikiline = [ prefix + " {{" + template + "|" + lang_id + "|" + "|".join([f"{k}={v}" for k,v in params.items()]) ]

        if lang_id == "en" and passage_params.get("translation"):
            self.warn("english_has_translation", section, passage_params)
            return

        ORDERED_PARAMS = ["passage", "transliteration", "translation"]
        for k in ORDERED_PARAMS:
            if passage_params.get(k):
                new_wikiline.append(f"|{k}={passage_params[k]}")
        for k,v in sorted(passage_params.items()):
            if k in ORDERED_PARAMS:
                continue
            new_wikiline.append(f"|{k}={passage_params[k]}")

        new_wikiline[-1] += "}}"
        return "\n".join(new_wikiline)


    # Parameters that are ignored if "section" is provided
    _section_override_params = countable_labels - {"chapter"}
    def is_valid_template(self, template, params):

        # the section paramater will override individual paramaters
        # TODO: enable this
        #if "section" in params and any(x in params or x+"s" in params for x in _section_override_params):
        #    return False

        for k,v in params.items():
            if wiki_contains("|", v):
                # TODO: self.warn()
                self.dprint("pipe_in_value", k, v, params)
                return False

        if template in ["quote-newsgroup", "cite-newsgroup"]:
            if all(x in params for x in ["author", "newsgroup"]):
                return True

            # Sanity check for usernames
            username = params["author"]
            if "|" in username or "=" in username:
                return False

            title = params["title"]
            if "|" in title or "=" in title:
                return False

            self.dprint("incomplete newsgroup entry")


        title = params.get("title")
        if title and not self.is_valid_title(title):
            print("BAD TITLE", title)
            return False

        if template in ["quote-book", "cite-book"]:
            if all(x in params for x in ["year", "title"]):
                return True

        elif template in ["quote-text", "cite-text"]:
            if sum(1 for x in ["year", "date"] if x in params) == 1 \
                    and sum(1 for x in ["author", "title"] if x in params):
                return True

        elif template in ["quote-journal", "cite-journal"]:
            print("CHECKING JOURNAL")
            if all(x in params for x in ["journal"]) and sum(1 for x in ["year", "date"] if x in params)==1:
                return True
            self.dprint("incomplete journal entry")


        elif template in ["quote-web", "cite-web"]:
            if all(x in params for x in ["site", "url"]):
                return True
            self.dprint("incomplete web entry")

        elif template == "quote-song":
            if all(x in params for x in ["author", "title"]):
                return True
            self.dprint("incomplete song entry")

        print("INVALID TEMPLATE", template, params)

        #raise ValueError("invalid template", template, params)
        return False

    @staticmethod
    def is_valid_title(title):

        if not title:
            return False

        if title == "Usenet":
            return False

        if title.startswith("Re:") or title.startswith("Fwd:") or title.startswith("FW:"):
            return False

        if title.startswith("{{") and title.endswith("}}"):
            return True

        if title.startswith("[") and title.endswith("]"):
            return True

        # Must start with uppercase letter
        if title[0] not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            return

        return not re.search("([()]|thesis|published|submitted|printed)", title)
        #return not re.search("(thesis|published|submitted|printed)", title)


    def process(self, text, title, summary=None, options=None):
        # This function runs in two modes: fix and report
        #
        # When summary is None, this function runs in 'report' mode and
        # returns [(code, page, details)] for each fix or warning
        #
        # When run using wikifix, summary is not null and the function
        # runs in 'fix' mode.
        # summary will be appended with a description of any changes made
        # and the function will return the modified page text

        self._log = []
        self._summary = summary

        # skip edits on pages with lua memory errors
        ignore_pages = [ "is", "I", "a", "de" ]
        if title in ignore_pages:
            return [] if summary is None else text

        entry = sectionparser.parse(text, title)
        if not entry:
            return [] if summary is None else text

        for section in entry.ifilter_sections():
            if self.convert_quotes(section, title):
                self.fix("bare_quote", section, "converted bare quote to template")

        return self._log if summary is None else str(entry)



    def cleanup_params(self, params):
        if not params:
            return

        for k in ["title", "chapter", "journal", "publisher"]:
            if k in params:
                params[k] = params[k].strip(", ")

        if params.get('year_published', -1) == params.get('year', 0):
            del params['year_published']

    def add_date(self, details, date):
        year, month, day = date

        # rename year to date to preserve dictionary order
        if year == details.get("year"):
            details = {"date" if k == "year" else k:v for k,v in details.items()}

        if not year:
            if not "year" in details:
                self.dprint("ERROR: date has no year and quote has no year, WTF?")
                return

            year = details["year"]
        elif "year" in details and int(year) != int(details["year"]):
            # TODO: currently a secondary date with a month is used to indicate
            # that it's a journal, but there's no way to included published_date in journals
            # This only happens in a handful of cases
            self.dprint("ERROR: published year doesn't match citation year")
            return

        if day:
            if day < 0:
                date = f"{day*-1} {month} {year}"
            else:
                date = f"{month} {day} {year}"

            # rename year to date to preserve dictionary order
            if "year" in details:
                details = {"date" if k == "year" else k:v for k,v in details.items()}
            details["date"] = date

        else:
            details["month"] = month

        return details


    def journal_handler(self, parsed):
        allowed_params = {"year", "journal", "author", "volume", "issue", "page", "pages", "url", "title", "titleurl", "month", "publisher", "pageurl", "year_published", "issues", "location", "section", "number", "issn"}
        return self.generic_handler(parsed, "journal", allowed_params)

    def web_handler(self, parsed):
        details = { "_source": "web" }
        allowed_params = {"year", "site", "url"}
        for p in parsed:
            if p.type == "separator":
                continue

            elif p.type == "author":
                assert len(p.values) == 1
                for idx, value in enumerate(p.values, 1):
                    key = f"author{idx}" if idx>1 else "author"
                    details[key] = value

            else:
                if p.type not in allowed_params:
                    raise ValueError("unhandled type", p)

                if len(p.values) != 1:
                    print("web unhandled multi-values", p)
                    return
                    raise ValueError("web unhandled multi-values", p)
                details[p.type] = p.values[0]
        return details



    def newsgroup_handler(self, parsed):
        details = { "_source": "newsgroup" }
        allowed_params = {"date", "author", "year", "title", "newsgroup", "url", "titleurl"}
        return self.generic_handler(parsed, "newsgroup", allowed_params)


    def song_handler(self, parsed):
        allowed_params = {"year", "author", "title"}
        return self.generic_handler(parsed, "song", allowed_params)

    def text_handler(self, parsed):
        allowed_params = {"page", "pages", "title", "year", "location", "publisher", "chapter", "pageurl", "year_published", "series", "url", "volume", "issn", "oclc", "month", "section", "sectionurl", "edition", "chapterurl"}
        allowed_params -= {"titleurl"} # quote-text doesn't handle titleurl, subtracting it here in case it gets added accidentally
        details = self.generic_handler(parsed, "text", allowed_params)
        if not details:
            return

        # Links to google books can be classified as books
        url = details.get("url", "")
        if re.search("google.[^/]*/books/", url):
            details["_source"] = "book"

#        if re.search("google.[^/]*/news/", url):
#            details["_source"] = "journal"

#        else:
#            return

        return details


    def generic_handler(self, parsed, source, allowed_params):
        details = { "_source": source }

        print("Parsed", parsed)

        def save(k,v):
            if k in details:
                print("dup value", k, v, parsed)
                details["__failed_dup_value"] = True
            details[k] = v

        for p in parsed:

            if p.type == "classifier":
                classifier_type = list(p.values[0].keys())
                if classifier_type != [source]:
                    print("MISMATCH classifier/source", classifier_type, source)
                    return
                continue

            if p.type.startswith("_maybe_"):
                print("MAYBE", p)
                if self.aggressive:
                    p = p._replace(type=p.type[len("_maybe_"):])
                else:
                    return

            if p.type == "date":
                details = self.add_date(details, p.values)
                if not details:
                    return
                continue

            if p.type == "accessdate":
                year, month, day = p.values
                save("accessdate", f"{abs(day)} {month} {year}")
                continue

            if p.type == "url":
                save("url", p.values.target)
                continue

            if p.type == "url::page":
                assert len(p.values) == 1
                save("page", p.values[0])

                # rename url to pageurl
                details = {"pageurl" if k in ["url", "chapterurl"] else k:v for k,v in details.items()}
                continue

            if p.type == "url::pages":
                assert len(p.values) == 1
                save("pages", p.values[0])

                # rename url to pageurl
                details = {"pageurl" if k in ["url", "chapterurl"] else k:v for k,v in details.items()}
                continue

            if p.type == "url::chapter":
                assert len(p.values) == 1
                save("chapter", p.values[0])

                # rename url to chapter
                details = {"chapterurl" if k == "url" else k:v for k,v in details.items()}
                continue

            if p.type.endswith("separator"):
                continue

            elif p.type in ["isbn"]:
                save(p.type, "; ".join(p.values[0]))

#            elif p.type == "_maybe_bare_page_link":
#                assert len(p.values) == 1
#                if "url" in details and "page" not in details and p.values[0].isnumeric():
#                    details = {"pageurl" if k == "url" else k:v for k,v in details.items()}
#                    save("page", p.values[0])
#                else:
#                    return

            elif p.type == "author":
                assert len(p.values)
                save(p.type, "; ".join(p.values))

#            elif p.type == "publisher2":
#                assert len(p.values) == 1
#                # assign directly to modify existing value
#                details["publisher"] += f" ({p.values[0]})"

            elif p.type in ["editor", "translator"]:
                assert len(p.values)
                if len(p.values) == 1:
                    save(p.type, p.values[0])
                else:
                    save(p.type + "s", "; ".join(p.values))

            elif p.type == "manual_review":
                print(parsed)
                print("MANUAL_REVIEW:", p.values[0])
                details["__failed_needs_manual_review"] = True

            else:
                if p.type not in allowed_params:
                    raise ValueError("unhandled type", p.type, p.values, parsed)

                if len(p.values) != 1:
                    if isinstance(p.values, LINK):
                        if "url" in p.type:
                            save(p.type, p.values.target)
                        else:
                            save(p.type, p.values.orig)
                    else:
                        print("generic unhandled multi-values", p)
                        return
                        raise ValueError("generic unhandled multi-values", p)
                else:
                    save(p.type, p.values[0])

        if any(k.startswith("__failed") for k in details.keys()):
            return

        return details


    def book_handler(self, parsed):
        allowed_params = {"page", "pages", "title", "year", "location", "publisher", "chapter", "pageurl", "year_published", "series", "url", "volume", "issn", "oclc", "month", "section", "sectionurl", "chapterurl", "edition" }
        return self.generic_handler(parsed, "book", allowed_params)


    def apply_transformation(self, parsed, transformer):
        for idx, item in enumerate(parsed):
            new_label = transformer.get(item.type)
            if new_label:
                parsed[idx] = item._replace(type=new_label)

#    _book = {"*page": "page"}
    _year2_published = {"year2": "year_published" }

    # only used in old handlers, plus there's a special handler for "url::page" to convert the link to urllink

    _url_page_page = {} #{ "url::page": "page", "_page_is_urlpage" }
    #_urlpage = {"url": "pageurl", "url::page": "page"}
    _paren_italics_series = {"paren::italics": "series"}
    _year2_year_published = {"year2": "year_published"}
    _fancy_dq_chapter = {"fancy_double_quotes": "chapter"}

    _paren_newsgroup_newsgroup = {"paren::newsgroup": "newsgroup"}

    _dq2_title = {"double_quotes2": "title"}
    _dq_author = {"double_quotes": "author"}
    _skip_italics = {"italics": "separator"}
    _skip_italics2 = {"italics2": "separator"}
    _italics_title = {"italics": "title"}
    _italics2_title = {"italics2": "title"}
    _dq_title = {"double_quotes": "title"}
    _fancy_dq_title = {"fancy_double_quotes": "title"}

    _dq_url_url = {"double_quotes::url": "url"}
    _dq_url_titleurl = {"double_quotes::url": "titleurl"}
    _dq_url_chapterurl = {"double_quotes::url": "chapterurl"}

    _dq_url_text_title = {"double_quotes::url::text": "title"}
    _dq_url_text_chapter = {"double_quotes::url::text": "chapter"}

    _fq_url_url = {"fancy_quote::url": "url"}
    _fq_url_titleurl = {"fancy_quote::url": "titleurl"}
    _fq_url_chapterurl = {"fancy_quote::url": "chapterurl"}

    _fq_url_text_title = {"fancy_quote::url::text": "title"}
    _fq_url_text_chapter = {"fancy_quote::url::text": "chapter"}

    _fancy_dq_url_url = {"fancy_double_quotes::url": "url"}
    _fancy_dq_url_titleurl = {"fancy_double_quotes::url": "titleurl"}
    _fancy_dq_url_chapterurl = {"fancy_double_quotes::url": "chapterurl"}

    _fancy_dq_url_text_title = {"fancy_double_quotes::url::text": "title"}
    _fancy_dq_url_text_chapter = {"fancy_double_quotes::url::text": "chapter"}


    _skip_paren_unhandled = { "paren::unhandled": "separator" }
    _skip_unhandled = { "unhandled": "separator" }
    _review_unhandled = { "unhandled": "manual_review" }

    _web = {"_handler": web_handler, }
    _url_unhandled_publisher = { "url::unhandled": "publisher" }
    _unhandled_publisher = { "unhandled": "publisher" }


    _paren_volumes = { "paren::volumes": "volume" }
    _paren_volume = { "paren::volume": "volume" }
    _paren_issue = { "paren::issue": "issue" }
    _paren_issues = { "paren::issues": "issue" }
    _paren_page = { "paren::page": "page" }
    _paren_date = { "paren::date": "date" }
    _url_dq_title = { "url::double_quotes": "title"}
    _url_is_titleurl = { "url": "titleurl" }
    _paren_publisher = {"paren": "_maybe_publisher"}

    _paren_italics_maybe_journal = { "paren::italics": "_maybe_journal" }
    _italics_maybe_journal = { "italics": "_maybe_journal" }
    _dq_maybe_journal = { "double_quotes": "_maybe_journal" }

    _song = {"_handler": song_handler, }

    _text = {"_handler": text_handler, }
    _url_text_title = {"url::text": "title"}
    _fq_title = {"fancy_quote": "title"}

    _paren_pub2 = {"paren": "publisher2"}
    #_url_page_page = {"url::page": "page"}
    _url_italics_title = {"url::italics": "title"}
    _italics_url_text_title = {"italics::url::text": "title"}

    _italics_link_title = {"italics::link": "title"}
    _url_date_date = {"url::date": "date"}

    _dq_chapter = {"double_quotes": "chapter"}
    _fq_chapter = {"fancy_quote": "chapter"}

    _link_title = {"link": "title"}
    _link_journal = {"link": "journal"}
    _link_publisher = {"link": "publisher"}
    _italics_chapter = {"italics": "chapter"}

    _url_titleurl = {"url": "titleurl"}

    _paren_volumes_volume = {"paren::volumes": "volume"}

#    _italics_chapter = {"italics": "chapter"}
#    _unhandled_location_or_publisher = {"unhandled": "_location_or_publisher"}



    def make_anywhere(normal, plurals, alt_keys):
        prefixes = ["link", "url", "paren", "brackets", "italics", "double_quotes", "fancy_quote", "fancy_double_quotes"]

        _anywhere = set()
        _anywhere_tr = {}
        for x in normal:
            _anywhere.add(x)
            for p in prefixes:
                _anywhere.add(f"{p}::{x}")
                _anywhere_tr[f"{p}::{x}"] = x

        # plurals
        for v in plurals:
            for k in [v, v+"s"]:
                _anywhere.add(k)
                _anywhere_tr[k] = v
                for p in prefixes:
                    _anywhere.add(f"{p}::{k}")
                    _anywhere_tr[f"{p}::{k}"] = v

        for k,v in alt_keys.items():
            _anywhere.add(k)
            _anywhere_tr[k] = v
            for p in prefixes:
                _anywhere.add(f"{p}::{k}")
                _anywhere_tr[f"{p}::{k}"] = v

        return _anywhere, _anywhere_tr

#    _book_optionals = { "_match_anywhere_optional": ('translator', 'translators', 'location', 'editor', 'publisher', 'year2', 'chapter', 'page', 'pages', 'url', 'url::page') } | _year2_published | _urlpage

    _book = {"_handler": book_handler, "italics": "title"}
    _book_anywhere, _book_anywhere_tr = make_anywhere(
        [ 'year', 'month', 'author', 'translator', 'edition', 'location', 'editor', 'publisher', 'isbn', 'issn', 'oclc', 'book_classifier'],
        [ "volume", "chapter", "page" ],
        # alternate keys
        {
#            "issues": "issues",
            "pages": "pages",
            "year2": "year_published",
            "date_retrieved": "accessdate"
        }
    )
    _book_anywhere |= {'url', 'section'}
    _book_anywhere_tr |= {
        "url::page": "url::page", # instead of just 'page', to trigger 'url' -> 'urlpage'
        "url::pages": "url::pages",
        "url::chapter": "url::chapter",
    }
#    print(_book_anywhere)
#    print(_book_anywhere_tr)
#    exit()




    #_book_anywhere = { 'translator', 'location', 'editor', 'publisher', 'year2', 'chapter', 'chapters', 'page', 'pages', 'url', 'url::chapter', 'url::page', 'isbn', 'issn', 'oclc', 'paren::isbn', 'paren::issn', 'paren::oclc', "date_retrieved", "paren::date_retrieved"}
    #_book_anywhere_tr = {'year2': "year_published", 'paren::isbn': 'isbn', 'paren::issn': 'issn', 'paren::oclc': 'oclc', "date_retrieved": "accessdate", "paren::date_retrieved": "accessdate", "volumes": "volume"}
    _book_exclude = { 'newsgroup', 'paren::newsgroup', 'journal', 'italics::journal' }

    book_must_include = [
        {"author", "chapter"},
        {"author", "url::chapter"},
        {"author", "paren::chapter"},

        {"author", "page"},
        {"author", "url::page"},
        {"author", "paren::page"},

        {"editor", "chapter"},
        {"editor", "url::chapter"},
        {"editor", "paren::chapter"},

        {"editor", "page"},
        {"editor", "url::page"},
        {"editor", "paren::page"},

        {"isbn", "editor"},
        {"isbn", "location"},
        {"isbn", "publisher"},

        {"paren::isbn", "editor"},
        {"paren::isbn", "location"},
        {"paren::isbn", "publisher"},

        {"author", "location"},
        {"location", "publisher"},
    ]

    maybe_journal_must_include = [
        {'date'},
        {'url::date'},
        {'paren::date'},

        {'year'},
        {'year', 'month'},
        {'year', 'url::month'},
        {'year', 'paren::month'},

        {'issue'},
        {'paren::issue'},

        {'issues'},
        {'paren::issues'},
    ]
    journal_must_include = [
        { 'journal' },
        { 'italics::journal' },
        { 'double_quotes::journal' },
        { 'paren::italics::journal' },
    ]
    _journal = {"_handler": journal_handler, "italics::journal": "journal", "paren::italics::journal": "journal", "volumes": "volume"}
        #(journal_must_include, ['italics', 'paren::volumes', 'paren::page']


    _journal_anywhere, _journal_anywhere_tr = make_anywhere(
        ['journal', 'date', 'year', 'month', 'author', 'translator', 'location', 'editor', 'publisher', 'isbn', 'issn', 'oclc', 'journal_classifier', 'section'],
        [ "issue", "number", "page", "volume" ], # not chapter
        # alternate keys
        {
            #"issues": "issues",
            "pages": "pages",
            "year2": "year_published",
            "date_retrieved": "accessdate"
        }
    )
    _journal_anywhere |= {'url', 'classifier'}
    _journal_anywhere_tr |= {
        "url::page": "url::page", # instead of just 'page', to trigger 'url' -> 'urlpage'
        "classifier": "separator",
    }
#    print(_journal_anywhere)
#    exit()

#    print(_journal_anywhere_tr)
#    _orig = { 'date', 'year', 'month', 'author', 'translator', 'location', 'editor', 'publisher', 'year2', 'issue', 'issues', 'volumes', 'page', 'pages', 'url', 'url::chapter', 'url::page', 'isbn', 'issn', 'oclc', 'url::date', 'paren::volume', 'paren::volumes', 'paren::page', 'paren::issues', 'paren::issue', 'paren::date', 'date_retrieved', 'paren::date_retrieved'}
#    print(_journal_anywhere)
#    print(_orig-_journal_anywhere)
#    raise ValueError()

    # Alternate terms
#`    _journal_anywhere_tr = {'year2': "year_published", 'issues': 'issue', 'volumes': 'volume', 'url::date': 'date', 'paren::date': 'date', 'paren::month': 'month', 'url::month': 'month', 'paren::volumes': 'volume', 'paren::volume': 'volume', 'paren::page': 'page', 'paren::issues': 'issue', 'paren::issue': 'issue', "date_retrieved": "accessdate", "paren::date_retrieved": "accessdate"}


    #_journal_anywhere = { 'date', 'year', 'month', 'author', 'translator', 'location', 'editor', 'publisher', 'year2', 'issue', 'issues', 'volumes', 'page', 'pages', 'url', 'url::chapter', 'url::page', 'isbn', 'issn', 'oclc', 'url::date', 'paren::volume', 'paren::volumes', 'paren::page', 'paren::issues', 'paren::issue', 'paren::date', 'date_retrieved', 'paren::date_retrieved'}
    #_journal_anywhere_tr = {'year2': "year_published", 'issues': 'issue', 'volumes': 'volume', 'url::date': 'date', 'paren::date': 'date', 'paren::month': 'month', 'url::month': 'month', 'paren::volumes': 'volume', 'paren::volume': 'volume', 'paren::page': 'page', 'paren::issues': 'issue', 'paren::issue': 'issue', "date_retrieved": "accessdate", "paren::date_retrieved": "accessdate"}
    _journal_exclude = { 'newsgroup', 'paren::newsgroup' }
    _maybe_journal_exclude = { 'journal', 'newsgroup', 'paren::newsgroup' }

    newsgroup_must_contain = [
        {'newsgroup', 'date'},
        {'newsgroup', 'year'},
        {'paren::newsgroup', 'date'},
        {'paren::newsgroup', 'year'},
    ]
    _newsgroup = {"_handler": newsgroup_handler, 'paren::newsgroup': 'newsgroup'}

    _newsgroup_anywhere = {"date_retrieved", "paren::date_retrieved"}
    _newsgroup_anywhere_tr = {"date_retrieved": "accessdate", "paren::date_retrieved": "accessdate"}
    _newsgroup_exclude = {}

    _italics_url_text_title = {"italics::url::text": "title"}
    _italics_url_titleurl = {"italics::url": "titleurl"}
    _skip_italics_link_text = {"italics::link::text": "separator"}

    _url_text_issue = {"url::text": "issue"}
    _link_url = {"link": "url"}

    _link_chapter = {"link": "chapter"}
    _skip_link_chapter = {"link::chapter": "separator"}

    _link_page = {"link": "page"}
    _skip_link_page = {"link::page": "separator"}

    _italics_link_journal = {"italics::link": "journal"}
    _skip_italics_link_journal = {"italics::link::journal": "separator"}
    _link_italics_journal = {"link::italics": "journal"}
    _skip_link_italics_journal = {"link::italics::journal": "separator"}

    _url_text_title = {"url::text": "title"}
    _unhandled_title = {"unhandled": "title"}
    _italics_url_url = {"italics::url": "url"}

    _unhandled_maybe_author = {"unhandled": "_maybe_author"}
    _unhandled_maybe_publisher = { "unhandled": "_maybe_publisher" }
    _unhandled_maybe_location = { "unhandled": "location" }
    _publisher_author = {"publisher": "author"}
    _author_publisher = {"author": "publisher"}

    _url_sectionurl = {"url": "sectionurl"}
    _url_text_section = {"url::text": "section"}

    #not_book_must_contain = [{"date", "author", "section"}, { "year", "author", "section" }]
    not_book_must_contain = [{"date"}, {"year"}]

    ###HANDLERS
    _all_handlers = [
        # Text handlers

#        ({}, ['year', 'author'], {}, {}, _text),

#        ({}, ['year', 'url', 'url::text'], {'author', 'page', 'section'}, {}, _text|_url_text_title),
#        ({}, ['year', 'italics', 'italics2'], {'author', 'page', 'section'}, {}, _text|_italics_chapter|_italics2_title),
#        ({}, ['year', 'italics'], {'author', 'page', 'section'}, {}, _text|_italics_title),
#        ({}, ['year', 'italics::url', 'italics::url::text'], {'author', 'page', 'section'}, {}, _text|_italics_url_url|_italics_url_text_title),
#        ({}, ['year', 'double_quotes'], {'author', 'page', 'section'}, {}, _text|_dq_title),
#        ({}, ['year', 'double_quotes::url', 'double_quotes::url::text'], {'author', 'page', 'section'}, {}, _text|_dq_url_url|_dq_url_text_title),
#        ({}, ['year', 'fancy_double_quotes'], {'author', 'page', 'section'}, {}, _text|_fancy_dq_title),
#        ({}, ['year', 'fancy_double_quotes::url', 'fancy_double_quotes::url::text'], {'author', 'page', 'section'}, {}, _text|_fancy_dq_url_url|_fancy_dq_url_text_title),
#        ({}, ['year', 'fancy_quote'], {'author', 'page', 'section'}, {}, _text|_fq_title),
#        ({}, ['year', 'fancy_quote::url', 'fancy_quote::url::text'], {'author', 'page', 'section'}, {}, _text|_fq_url_url|_fq_url_text_title),

#        ({}, ['year', 'author', 'italics', 'url', 'url::text'], {}, {}, _text|_italics_title|_url_sectionurl|_url_text_section),
#        ({}, ['year', 'italics', 'paren::volumes', 'paren::page'], {}, {}, _text|_paren_volumes_volume|_paren_page),

#        ({}, ['year', 'italics', 'publisher'], {}, {}, _text|_italics_title|_publisher_author),
#        ({}, ['year', 'publisher', 'italics'], {}, {}, _text|_italics_title|_publisher_author),

#        ({}, ['year', 'italics'], _book_anywhere, _book_exclude, _text|_book_anywhere_tr|_italics_title),
#        ({}, ['date', 'italics'], _book_anywhere, _book_exclude, _text|_book_anywhere_tr|_italics_title),

#        ([{'date'},{'year'}], ['italics', 'fancy_double_quotes'], _book_anywhere, _book_exclude, _text|_book_anywhere_tr|_italics_title|_fancy_dq_chapter),


#        ({}, ['year', 'url', 'url::text'], {'author', 'page', 'section'}, {}, _text|_url_text_title),

        (not_book_must_contain, ['url', 'url::text'], _book_anywhere, _book_exclude, _text|_url_text_title|_book_anywhere_tr),

        (not_book_must_contain, ['italics'], _book_anywhere, _book_exclude, _text|_italics_title|_book_anywhere_tr),
        (not_book_must_contain, ['italics::url', 'italics::url::text'], _book_anywhere, _book_exclude, _text|_book_anywhere_tr|_italics_url_text_title|_italics_url_url),

        (not_book_must_contain, ['double_quotes'], _book_anywhere, _book_exclude, _text|_dq_title|_book_anywhere_tr),
        (not_book_must_contain, ['double_quotes::url', 'double_quotes::url::text'], _book_anywhere, _book_exclude, _text|_book_anywhere_tr|_dq_url_text_title|_dq_url_url),

        (not_book_must_contain, ['fancy_quote'], _book_anywhere, _book_exclude, _text|_fq_title|_book_anywhere_tr),
        (not_book_must_contain, ['fancy_quote::url', 'fancy_double_quotes::url::text'], _book_anywhere, _book_exclude, _text|_book_anywhere_tr|_fq_url_text_title|_fq_url_url),

        (not_book_must_contain, ['fancy_double_quotes'], _book_anywhere, _book_exclude, _text|_fancy_dq_title|_book_anywhere_tr),
        (not_book_must_contain, ['fancy_double_quotes::url', 'fancy_double_quotes::url::text'], _book_anywhere, _book_exclude, _text|_book_anywhere_tr|_fancy_dq_url_text_title|_fancy_dq_url_url),

        (not_book_must_contain, ['italics::link'], _book_anywhere, _book_exclude, _text|_book_anywhere_tr|_italics_link_title),
        (not_book_must_contain, ['italics::link', 'italics::link::text'], _book_anywhere, _book_exclude, _text|_book_anywhere_tr|_italics_link_title|_skip_italics_link_text),

        (not_book_must_contain, ['double_quotes', 'italics'], _book_anywhere, _book_exclude, _text|_italics_title|_book_anywhere_tr|_dq_chapter),
        (not_book_must_contain, ['double_quotes::url', 'double_quotes::url::text', 'italics'], _book_anywhere, _book_exclude, _text|_italics_title|_book_anywhere_tr|_dq_url_chapterurl|_dq_url_text_chapter),

        (not_book_must_contain, ['fancy_quote', 'italics'], _book_anywhere, _book_exclude, _text|_italics_title|_book_anywhere_tr|_fq_chapter),
        (not_book_must_contain, ['fancy_quote::url', 'fancy_quote::url::text', 'italics'], _book_anywhere, _book_exclude, _text|_italics_title|_book_anywhere_tr|_fq_url_chapterurl|_fq_url_text_chapter),

        (not_book_must_contain, ['fancy_double_quotes', 'italics'], _book_anywhere, _book_exclude, _text|_italics_title|_book_anywhere_tr|_fancy_dq_chapter),
        (not_book_must_contain, ['fancy_double_quotes::url', 'fancy_double_quotes::url::text', 'italics'], _book_anywhere, _book_exclude, _text|_italics_title|_book_anywhere_tr|_fancy_dq_url_chapterurl|_fancy_dq_url_text_chapter),

        (not_book_must_contain, ['italics', 'italics2'], _book_anywhere, _book_exclude, _text|_book_anywhere_tr|_italics_chapter|_italics2_title),

        (not_book_must_contain, ['italics', 'double_quotes'], _book_anywhere, _book_exclude, _text|_italics_title|_book_anywhere_tr|_dq_chapter),
        (not_book_must_contain, ['italics', 'double_quotes::url', 'double_quotes::url::text'], _book_anywhere, _book_exclude, _text|_italics_title|_book_anywhere_tr|_dq_url_chapterurl|_dq_url_text_chapter),

        (not_book_must_contain, ['italics', 'fancy_quote'], _book_anywhere, _book_exclude, _text|_italics_title|_book_anywhere_tr|_fq_chapter),
        (not_book_must_contain, ['italics', 'fancy_quote::url', 'fancy_quote::url::text'], _book_anywhere, _book_exclude, _text|_italics_title|_book_anywhere_tr|_fq_url_chapterurl|_fq_url_text_chapter),

        (not_book_must_contain, ['italics', 'fancy_double_quotes'], _book_anywhere, _book_exclude, _text|_italics_title|_book_anywhere_tr|_fancy_dq_chapter),
        (not_book_must_contain, ['italics', 'fancy_double_quotes::url', 'fancy_double_quotes::url::text'], _book_anywhere, _book_exclude, _text|_italics_title|_book_anywhere_tr|_fancy_dq_url_chapterurl|_fancy_dq_url_text_chapter),

#        (not_book_must_contain, ['italics', 'publisher', 'year2', 'paren::italics'], _book_anywhere, _book_exclude, _text|_italics_title|_book_anywhere_tr|_paren_italics_series),



        #({}, ['year', 'italics', 'location', 'author'], _book_anywhere, _book_exclude, _text|_book_anywhere_tr|_italics_title|_author_publisher),
        #({}, ['year', 'author', 'unhandled<*>'], {}, {}, _text|_unhandled_title),
        #({}, ['year', 'unhandled<*>', 'italics'], {}, {}, _text|_italics_title|_unhandled_maybe_author),
        #({}, ['date', 'unhandled<*>', 'italics'], {}, {}, _text|_italics_title|_unhandled_maybe_author),


        # Song handler
        ({}, ['year', 'author', 'italics', 'classifier'], {}, {}, _song|_italics_title),


        # Web handlers
        ({}, ['year', 'url', 'url::unhandled<VOA Learning English>', 'paren::unhandled<public domain>'], {}, {},
            _web|_url_unhandled_publisher|_skip_paren_unhandled),

        # Book handlers
        (book_must_include, ['year', 'italics'], _book_anywhere, _book_exclude, _book|_book_anywhere_tr),
        (book_must_include, ['year', 'italics::url', 'italics::url::text'], _book_anywhere, _book_exclude, _book|_book_anywhere_tr|_italics_url_text_title|_italics_url_url),

        (book_must_include, ['year', 'italics::link'], _book_anywhere, _book_exclude, _book|_book_anywhere_tr|_italics_link_title),
        (book_must_include, ['year', 'italics::link', 'italics::link::text'], _book_anywhere, _book_exclude, _book|_book_anywhere_tr|_italics_link_title|_skip_italics_link_text),

        (book_must_include, ['double_quotes'], _book_anywhere, _book_exclude, _book|_dq_title|_book_anywhere_tr),
        (book_must_include, ['double_quotes::url', 'double_quotes::url::text'], _book_anywhere, _book_exclude, _book|_book_anywhere_tr|_dq_url_text_title|_dq_url_url),

        (book_must_include, ['fancy_quote'], _book_anywhere, _book_exclude,_book|_fq_title|_book_anywhere_tr),
        (book_must_include, ['fancy_quote::url', 'fancy_double_quotes::url::text'], _book_anywhere, _book_exclude,_book|_book_anywhere_tr|_fq_url_text_title|_fq_url_url),

        (book_must_include, ['fancy_double_quotes'], _book_anywhere, _book_exclude,_book|_fancy_dq_title|_book_anywhere_tr),
        (book_must_include, ['fancy_double_quotes::url', 'fancy_double_quotes::url::text'], _book_anywhere, _book_exclude,_book|_book_anywhere_tr|_fancy_dq_url_text_title|_fancy_dq_url_url),

        (book_must_include, ['italics::link'], _book_anywhere, _book_exclude,_book|_book_anywhere_tr|_italics_link_title),
        (book_must_include, ['italics::link', 'italics::link::text'], _book_anywhere, _book_exclude,_book|_book_anywhere_tr|_italics_link_title|_skip_italics_link_text),

        (book_must_include, ['double_quotes', 'italics'], _book_anywhere, _book_exclude,_book|_italics_title|_book_anywhere_tr|_dq_chapter),
        (book_must_include, ['double_quotes::url', 'double_quotes::url::text', 'italics'], _book_anywhere, _book_exclude,_book|_italics_title|_book_anywhere_tr|_dq_url_chapterurl|_dq_url_text_chapter),


        (book_must_include, ['year', 'double_quotes', 'italics'], _book_anywhere, _book_exclude, _book|_book_anywhere_tr|_dq_chapter),
        (book_must_include, ['year', 'double_quotes::url', 'double_quotes::url::text', 'italics'], _book_anywhere, _book_exclude, _book|_book_anywhere_tr|_dq_url_chapterurl|_dq_url_text_chapter),

        (book_must_include, ['year', 'fancy_quote', 'italics'], _book_anywhere, _book_exclude, _book|_book_anywhere_tr|_fq_chapter),
        (book_must_include, ['year', 'fancy_quote::url', 'fancy_quote::url::text', 'italics'], _book_anywhere, _book_exclude, _book|_book_anywhere_tr|_fq_url_chapterurl|_fq_url_text_chapter),

        (book_must_include, ['year', 'fancy_double_quotes', 'italics'], _book_anywhere, _book_exclude, _book|_book_anywhere_tr|_fancy_dq_chapter),
        (book_must_include, ['year', 'fancy_double_quotes::url', 'fancy_double_quotes::url::text', 'italics'], _book_anywhere, _book_exclude, _book|_book_anywhere_tr|_fancy_dq_url_chapterurl|_fancy_dq_url_text_chapter),

        (book_must_include, ['year', 'italics', 'italics2'], _book_anywhere, _book_exclude, _book|_book_anywhere_tr|_italics_chapter|_italics2_title),

        (book_must_include, ['year', 'italics', 'double_quotes'], _book_anywhere, _book_exclude, _book|_book_anywhere_tr|_dq_chapter),
        (book_must_include, ['year', 'italics', 'double_quotes::url', 'double_quotes::url::text'], _book_anywhere, _book_exclude, _book|_book_anywhere_tr|_dq_url_chapterurl|_dq_url_text_chapter),

        (book_must_include, ['year', 'italics', 'fancy_quote'], _book_anywhere, _book_exclude, _book|_book_anywhere_tr|_fq_chapter),
        (book_must_include, ['year', 'italics', 'fancy_quote::url', 'fancy_quote::url::text'], _book_anywhere, _book_exclude, _book|_book_anywhere_tr|_fq_url_chapterurl|_fq_url_text_chapter),

        (book_must_include, ['year', 'italics', 'fancy_double_quotes'], _book_anywhere, _book_exclude, _book|_book_anywhere_tr|_fancy_dq_chapter),
        (book_must_include, ['year', 'italics', 'fancy_double_quotes::url', 'fancy_double_quotes::url::text'], _book_anywhere, _book_exclude, _book|_book_anywhere_tr|_fancy_dq_url_chapterurl|_fancy_dq_url_text_chapter),


        (book_must_include, ['year', 'italics', 'publisher', 'year2', 'paren::italics'], _book_anywhere, _book_exclude, _book|_book_anywhere_tr|_paren_italics_series),

        ({}, ['year', 'author', 'italics', 'publisher'], {}, {}, _book),

        ({}, ['year', 'author', 'unhandled<{{w|Poly-Olbion}}>', 'section', 'url'], {}, {}, _book|_unhandled_title|_url_sectionurl),
        ({}, ['year', 'unhandled<[[:s:EB1|Encyclopaedia Britannica, 1st ed.]]>', 'volume', 'page'], {}, {}, _book|_unhandled_title),

        # scan for unhandled authors
        #({}, ['unhandled<*>', 'italics'], _book_anywhere, _book_exclude|{'author'}, _book|_book_anywhere_tr|_unhandled_maybe_author),
        #(book_must_include, ['year', 'unhandled<*>', 'italics'], _book_anywhere, _book_exclude|{'author'}, _book|_book_anywhere_tr|_unhandled_maybe_author),

        # scan for unhandled publishers
        #({}, ['italics', 'unhandled<*>'], _book_anywhere, _book_exclude|{'publisher'}, _book|_book_anywhere_tr|_unhandled_maybe_publisher),
        #({}, ['italics', 'location', 'unhandled<*>'], _book_anywhere, _book_exclude|{'publisher'}, _book|_book_anywhere_tr|_unhandled_maybe_publisher),
#        ('year', 'author', 'italics', 'location', 'unhandled<*>', 'section', 'url')

        #(book_must_include, ['year', 'italics', 'unhandled<*>'], _book_anywhere, _book_exclude|{'publisher'}, _book|_book_anywhere_tr|_unhandled_maybe_publisher),

        # unhandled location
        #({}, ['italics', 'unhandled<*>', 'publisher'], _book_anywhere, _book_exclude|{'location'}, _book|_book_anywhere_tr|_unhandled_maybe_location),


        # EXPERIMENTAL
        #({}, ['year', 'author', 'italics', 'location', 'publisher', 'unhandled<*>'], _book_anywhere, _book_exclude, _book|_book_anywhere_tr|_review_unhandled),

        # TODO: ignore link::chapter, link is chapter
        #({}, ['year', 'author', 'italics', 'link', 'link::chapter'], {}, {}, _book|_book_anywhere_tr|_link_chapter|_skip_link_chapter),




        # TODO: book_maybe ? or just allow it explicitly


        # text is not title
        #(book_must_include, ['year', 'italics', 'url', 'url::text'], {}, {}, _book|_italics_chapter|_url_text_title),


        #(book_must_include, ['year', 'italics', 'unhandled:], _book_anywhere, _book_exclude, _book|_book_anywhere_tr),
            # TODO: Check for unhandled<"page"> followed by url, url::unhandled<number>

# Mostly translated titles
#        ({'author', 'page'}, 'year, italics, paren::italics', _book_anywhere, _book|_book_anywhere_tr|_paren_italics_series),
#            (('year', 'author', 'italics', 'url', 'url::text'), _book| {"url::text": "_maybe_bare_page_link"}),


        # Journal handlers
            #('year', 'journal', 'month', 'year2'),
        (journal_must_include, [], _journal_anywhere, _journal_exclude, _journal|_journal_anywhere_tr),
        (journal_must_include, ['italics'], _journal_anywhere, _journal_exclude, _journal|_journal_anywhere_tr|_italics_title),
        (journal_must_include, ['italics', 'link', 'link::page'], _journal_anywhere, _journal_exclude, _journal|_journal_anywhere_tr|_italics_title|_link_page|_skip_link_page),
        (journal_must_include, ['italics::url', 'italics::url::text'], _journal_anywhere, _journal_exclude, _journal|_journal_anywhere_tr|_italics_url_text_title|_italics_url_titleurl),
        #(journal_must_include, ['url::double_quotes'], _journal_anywhere, _journal_exclude, _journal|_journal_anywhere_tr|_url_dq_title|_url_titleurl),
        (journal_must_include, ['double_quotes', 'link::italics::journal'], _journal_anywhere, _journal_exclude, _journal|_journal_anywhere_tr|_dq_title),

        (journal_must_include, ['fancy_quote', 'italics::journal'], _journal_anywhere, _journal_exclude, _journal|_journal_anywhere_tr|_fq_title),
        (journal_must_include, ['fancy_quote::url', 'fancy_quote::url::text', 'italics::journal'], _journal_anywhere, _journal_exclude, _journal|_journal_anywhere_tr|_fq_url_titleurl|_fq_url_text_title),
        (journal_must_include, ['fancy_double_quotes', 'italics::journal'], _journal_anywhere, _journal_exclude, _journal|_journal_anywhere_tr|_fancy_dq_title),
        (journal_must_include, ['fancy_double_quotes::url', 'fancy_double_quotes::url::text', 'italics::journal'], _journal_anywhere, _journal_exclude, _journal|_journal_anywhere_tr|_fancy_dq_url_titleurl|_fancy_dq_url_text_title),
        (journal_must_include, ['double_quotes', 'italics::journal'], _journal_anywhere, _journal_exclude, _journal|_journal_anywhere_tr|_dq_title),
        (journal_must_include, ['double_quotes::url', 'double_quotes::url::text', 'italics::journal'], _journal_anywhere, _journal_exclude, _journal|_journal_anywhere_tr|_dq_url_titleurl|_dq_url_text_title),


        ([{'date'}, {'year'}], ['double_quotes', 'link', 'link::italics::journal'], _journal_anywhere, _journal_exclude, _journal|_journal_anywhere_tr|_dq_title|_link_journal|_skip_link_italics_journal),
#('year', 'author', 'double_quotes', 'italics::journal', 'section')


        (journal_must_include, ['double_quotes::url', 'double_quotes::url::text'], _journal_anywhere, _journal_exclude, _journal|_journal_anywhere_tr|_dq_url_text_title|_dq_url_titleurl),
        ([], ['year', 'italics::journal', 'unhandled<issue>', 'url', 'url::text', 'page'], [], [], _journal|_journal_anywhere_tr|_url_text_issue|_skip_unhandled),
        ([], ['year', 'italics::link', 'italics::link::journal', 'unhandled<issue>', 'url', 'url::text', 'page'], [], [], _journal|_journal_anywhere_tr|_italics_link_journal|_skip_italics_link_journal|_url_text_issue|_skip_unhandled),


# Enable this, grep "maybe_journal" in the output, then add valid journals to the allow list
# grep maybe_journal fixes.all | sort | uniq >> allowed_journals
#            ('date', 'author', 'double_quotes::url', 'double_quotes::url::text', 'journal'),

        #(maybe_journal_must_include, ['italics::url', 'italics::url::text', 'double_quotes'], _journal_anywhere, _journal_exclude, _journal|_journal_anywhere_tr|_italics_url_text_title|_italics_url_titleurl|_dq_maybe_journal),

#         (maybe_journal_must_include, ['double_quotes', 'italics'], _journal_anywhere, _maybe_journal_exclude, _journal|_journal_anywhere_tr|_dq_title|_italics_maybe_journal),
#         (maybe_journal_must_include, ['double_quotes::url', 'double_quotes::url::text', 'italics'], _journal_anywhere, _maybe_journal_exclude, _journal|_journal_anywhere_tr|_dq_url_titleurl|_dq_url_text_title|_italics_maybe_journal),
#         (maybe_journal_must_include, ['fancy_double_quotes', 'italics'], _journal_anywhere, _maybe_journal_exclude, _journal|_journal_anywhere_tr|_fancy_dq_title|_italics_maybe_journal),
#         (maybe_journal_must_include, ['fancy_double_quotes::url', 'fancy_double_quotes::url::text', 'italics'], _journal_anywhere, _maybe_journal_exclude, _journal|_journal_anywhere_tr|_fancy_dq_url_titleurl|_fancy_dq_url_text_title|_italics_maybe_journal),
#         (maybe_journal_must_include, ['fancy_quote', 'italics'], _journal_anywhere, _maybe_journal_exclude, _journal|_journal_anywhere_tr|_fq_title|_italics_maybe_journal),
#         (maybe_journal_must_include, ['fancy_quote::url', 'fancy_quote::url::text', 'italics'], _journal_anywhere, _maybe_journal_exclude, _journal|_journal_anywhere_tr|_fq_url_titleurl|_fq_url_text_title|_italics_maybe_journal),

#        ({}, ['year', 'italics', 'volumes', 'page'], {}, {}, _journal|_italics_maybe_journal),
#        ({}, ['year', 'italics', 'paren::volumes', 'paren::page'], {}, {}, _journal|_paren_volumes_volume|_paren_page|_italics_maybe_journal),
#        (maybe_journal_must_include, ['italics'], _journal_anywhere, _journal_exclude, _journal|_journal_anywhere_tr|_italics_maybe_journal),
#        (maybe_journal_must_include, ['url::double_quotes', 'italics'], _journal_anywhere, _journal_exclude, _journal|_journal_anywhere_tr|_url_dq_title|_italics_maybe_journal),
#        (maybe_journal_must_include, ['italics', 'paren::italics'], _journal_anywhere, _journal_exclude, _journal|_journal_anywhere_tr|_paren_italics_maybe_journal),
        #({},  'italics', 'url', 'url::date'), _journal_exclude, _journal|_italics_journal|_url_date_date),


#        ('date', 'author', 'double_quotes::url', 'double_quotes::url::text', 'newsgroup')


#('date', 'author', 'double_quotes::url', 'double_quotes::url::text', 'newsgroup')

        #newsgroup_handler
        (newsgroup_must_contain, ['author', 'newsgroup', 'url'], {}, _newsgroup_exclude, _newsgroup),
        (newsgroup_must_contain, ['author', 'italics::url', 'italics::url::text'], {}, _newsgroup_exclude, _newsgroup|_italics_url_text_title|_italics_url_titleurl),
        (newsgroup_must_contain, ['author', 'italics'], {'url'}, _newsgroup_exclude, _newsgroup|_italics_title),
        (newsgroup_must_contain, ['author', 'double_quotes'], {'url'}, _newsgroup_exclude, _newsgroup|_dq_title),
        (newsgroup_must_contain, ['author', 'double_quotes::url', 'double_quotes::url::text'], [], _newsgroup_exclude, _newsgroup|_dq_url_url|_dq_url_text_title),
        (newsgroup_must_contain, ['author', 'fancy_double_quotes'], {'url'}, _newsgroup_exclude, _newsgroup|_fancy_dq_title),

        (newsgroup_must_contain, ['double_quotes', 'italics'], {'url'}, _newsgroup_exclude, _newsgroup|_dq_author|_italics_title),

#('year', 'double_quotes', 'italics', 'paren::newsgroup')


    ]
