import enwiktionary_sectionparser as sectionparser
import mwparserfromhell as mwparser
import re
import sys

from autodooz.sections import ALL_LANGS
from autodooz.fix_bare_quotes import wikilines_to_quote_params, UNHANDLED_UX_TEMPLATES
from enwiktionary_parser.utils import nest_aware_contains
NESTS = (("[[", "]]"), ("{{", "}}"))

# index of "passage" when using numbered parameters
POSITION_PARAM = {
    "quote-book": "7",
    "quote-book-ur": "7",
    "quote-mailing list": "7",
    "quote-newsgroup": "7",
    "quote-song": "7",
    "quote-text": "7",
    "quote-us-patent": "7",
    "quote-video game": "7",
    "quote-web": "7",

    "quote-av": "8",
    "quote-journal": "8",

    "quote-hansard": "9",

#    "quote-wikipedia": None,
#    "quote-lite": None,
}

from .allowed_rq_templates import ALLOWED_RQ_TEMPLATES

from autodooz.sections import ALL_POS
from collections import defaultdict

class QuoteFixer():

    def __init__(self):
        self._summary = None
        self._log = []

    def fix(self, code, section, details):
        # When running tests, section will be empty
        if not section:
            print("FIX:", code, details)
            return

        if self._summary is not None:
            item = f"/*{section.path}*/ {details}"
            if item not in self._summary:
                self._summary.append(f"/*{section.path}*/ {details}")

        self._log.append(("autofix_" + code, section.page, section.path, None))

    def warn(self, code, section, details=None):
        self._log.append((code, section.page, section.path, details))

    def process(self, text, page, summary=None, options=None):
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

        entry = sectionparser.parse(text, page)
        if not entry:
            return [] if summary is None else text

        for section in entry.ifilter_sections(matches=lambda x: x.title in ALL_POS):

            to_remove = []
            idx = 0
            for idx, wikiline in enumerate(section.content_wikilines):
                m = re.match(r"""^(?P<prefix>[#:*]+)\s*(?P<template>{{\s*(RQ:|quote-).*}})\s*$""", wikiline, re.DOTALL)
                if not m:
                    continue
                prefix = m.group('prefix')
                template_text = m.group('template')

                wiki = mwparser.parse(template_text)
                t = next(wiki.ifilter_templates())

                # Only operate on single templates without surrounding text
                if str(t) != str(wikiline).lstrip("#*:").strip():
                    continue

                # No trailing lines = nothing to scan
                if idx+1 >= len(section.content_wikilines):
                    continue

                warn = lambda e, d: self.warn(e, section, d)
                res = wikilines_to_quote_params(section.content_wikilines[idx+1:], prefix, warn, handle_ux_templates=True)
                if not res:
                    continue
                offset, passage_params = res

                # If quote already has text, no need to continue
                template_name = re.sub("(<!--.*?-->)", "", str(t.name)).strip()
                passage_param_names = ["passage", "text"]
                if POSITION_PARAM.get(template_name):
                    passage_param_names.append(POSITION_PARAM.get(template_name))
                existing_passage_param = [p for p in passage_param_names if t.has(p)]
                if existing_passage_param:
                    #existing_passage = str(t.get(existing_passage_param[0]))
                    #new_passage = existing_passage + "<br>" + passage_params["passage"]
                    #del passage_params["passage"]
                    #wikiline = wikiline.replace(existing_passage, new_passage)
                    self.warn("quote_with_child_lines", section, "\n".join(section.content_wikilines[idx:idx+offset+1]))
                    continue

                # Fragile templates can't handle newline separated paramaters
                fragile_template = False
                # Unhandled templates can't handle passage= parameter
                unhandled_template = False

                if template_name.startswith("RQ:"):
                    if template_name in ["RQ:sga-gloss", "RQ:sga:Glosses", "RQ:sga-Corm"]:
                        # skip mixed irish/latin quotes
                        continue
                    if template_name in ALLOWED_RQ_TEMPLATES:
                        fragile_template = True
                    else:
                        # Unhandled templates with an existing {{quote can be ignored
                        if "{{quote" in section.content_wikilines[idx+1]:
                            continue

                        unhandled_template = True
                        self.warn("unhandled_rq_with_bare_passage", section, "\n".join(section.content_wikilines[idx:idx+offset+1]))

                if passage_params.get("translation"):
                    if section.path.startswith("English:"):
                        self.warn("english_has_translation", section, "\n".join(section.content_wikilines[idx:idx+offset+1]))
                        continue



                if unhandled_template:
                    if "{{quote" in section.content_wikilines[idx+1]:
                        print("already a quote")
                        continue

                    if passage_params.keys() - {"passage", "translation"}:
                        self.warn("unhandled_passage_param", section, "\n".join(section.content_wikilines[idx:idx+offset+1]))

                    passage = passage_params["passage"]
                    translation = passage_params.get("translation")
                    translit = None
#                    if template_name == "RQ:Tanach":
#                        if passage.startswith("{{lang|he|") and passage.endswith("}}"):
#                            passage = passage[len("{{lang|he|"):-2]
#                        if translation and "<br>" in translation:
#                            translit, translation = translation.split("<br>")
#                        print("TEM", template_name, [translit, translation])

                    lang_id = ALL_LANGS.get(section._topmost.title)
                    if translit:
                        new_wikiline = prefix + ": {{quote|" + lang_id + "|" + passage + "|tr=" + translit + "|t=" + translation + "}}"
                    elif translation:
                        new_wikiline = prefix + ": {{quote|" + lang_id + "|" + passage + "|" + translation + "}}"
                    else:
                        new_wikiline = prefix + ": {{quote|" + lang_id + "|" + passage + "}}"
                    section.content_wikilines[idx+1] = new_wikiline

                    for to_remove_idx in range(idx+2, idx+offset+1):
                        print(to_remove_idx)
                        to_remove.append(to_remove_idx)

                    entry_changed = True
                    self.fix("quote_outside_template", section, "converted bare passage to quote")
                    #self.warn("quote_with_child_lines", section, "\n".join(section.content_wikilines[idx:idx+offset+1]))

                else:
                    new_params = []
                    # Sort passage, translation, and transliteration before other possible params
                    for k, v in sorted(passage_params.items(), key=lambda x:
                        (0, x) if x[0] in ["passage", "translation", "transliteration"] else (1, x)):
                        new_params.append(f"{k}={passage_params[k]}")

                    # Some RQ templates can't handle newlines
                    sep = "" if fragile_template else "\n"
                    if new_params:
                        wikiline = re.sub(r"}}\s*$", "", wikiline) + f"{sep}|" + f"{sep}|".join(new_params) + "}}"
                    section.content_wikilines[idx] = wikiline

                    for to_remove_idx in range(idx+1, idx+offset+1):
                        to_remove.append(to_remove_idx)

                    entry_changed = True
                    self.fix("passage_outside_template", section, "merged bare passage into existing quote template")


            for idx in reversed(to_remove):
                del section.content_wikilines[idx]


        if summary is None:
            return self._log

        if entry_changed:
            return str(entry)

        return text
