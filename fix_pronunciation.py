import enwiktionary_sectionparser as sectionparser
import re
import multiprocessing
import os
import sys
import mwparserfromhell as mwparser
from autodooz.utils import template_aware_resplit, template_aware_contains

from enwiktionary_templates.utils import get_template_params

from autodooz.sections import ALL_POS, COUNTABLE_SECTIONS, ALL_LANGS
from .list_mismatched_headlines import is_header
EXTENDED_POS = ALL_POS.keys() | { "Abbreviations", "Han character", "Hanja", "Hanzi", "Kanji", "Symbol", "Cuneiform sign", "Sign values", "Suffix", "Definitions", "Idioms", "Predicative", "Relative" }

# lowercase
KNOWN_ACCENTS = { "test_accent", "us", "uk" }
KNOWN_QUALIFIERS = { "test_qualifier", "colloquial", "obsolete", "adverb", "adjective", "noun", "verb", "singular", "plural", "dated", "rare", "singular and plural", "proscribed" }
assert KNOWN_ACCENTS & KNOWN_QUALIFIERS == set()

def multi(generator):
    count = 0
    for _ in generator:
        count += 1
        if count == 2:
            return True
    return False

def get_leading_template(text):
    if not text.startswith("{{"):
        return
    m = re.match(r"{{([^{}|]+)", text)
    if m:
        t = m.group(1).strip()
        return m.group(1).strip()

def extract_refs(text):
    refs = []
    remaining_text = text
    for ref_text, param_data, _, ref in re.findall(r"(<\s*ref\s*(.*?)\s*(/\s*>|>\s*(.*?)\s*<\s*/\s*ref\s*>))", text, flags=re.DOTALL):
        params = {}
        if param_data:
            params = {m.group('k'):m.group('v') for m in re.finditer(r'''(?P<k>[^ ]+)\s*=\s*(['"])(?P<v>.+?)\2''', param_data)}
            if not params or params.keys() - {'name', 'group'}:
                # Handle unquoted name=value
                m = re.match(r"^(name)\s*=\s*([a-zA-Z0-9'-]+)$", param_data)
                if m:
                    params = {m.group(1):m.group(2)}
                else:
                    return None
        refs.append(ref + "".join(f'<<{k}:{v}>>' for k,v in params.items()))
        remaining_text = remaining_text.replace(ref_text, "")
    return remaining_text, refs

ERR_MISMATCHED_DELIM = -1
ERR_NO_IPA = -2
ERR_UNHANDLED_TEMPLATE = -3
ERR_MULTI_IPA = -4
ERR_DUP_Q = -5
ERR_DUP_QQ = -6
ERR_COMPLEX_QUALIFIER = -7
ERR_Q_COLLISION = -8
ERR_QQ_COLLISION = -9
ERR_UNHANDLED_TEXT = -10
ERR_LANG_MISMATCH = -11
ERR_SPLIT_MULTI_IPA = -11  # multiple IPA templates, at least one of which has multiple pronunciations
ERR_LANG_MISMATCH = -12


INLINE_IPA_PARAMS = ["a", "q", "aa", "qq", "ref"]

def parse_ipa(text):

    res = extract_refs(text)
    if not res:
        return "unparsable_refs"
    remaining_text, refs = res

    m = re.match(r"(.*?)((\s*<!--.*?-->)+)\s*$", remaining_text, flags=re.DOTALL)
    trailing_comments = None
    if m:
        remaining_text = m.group(1)
        trailing_comments = m.group(2)

    wiki = mwparser.parse(remaining_text)
    #if len(splits) == 1 and not any(str(t.name).strip() == "IPA" for t in wiki.ifilter_templates(recursive=False)):
    #    return "not_ipa_list"

    ipa = None
    to_merge = { "ref": " !!! ".join(refs) } if refs else {}

    unhandled_templates = []
    unhandled_qualifiers = []

    for t in wiki.ifilter_templates(recursive=False):
        if str(t.name).strip() in ["IPA"]:
            if ipa:
                return "multi_ipa"
            ipa = t
        elif str(t.name).strip() in ["i", "lb", "q", "qual", "qualifier"]:
            if not len(t.params) == 1:
                return "complex_qualifier"

            v = str(t.get(1)).strip()
            k = None
            if v.lower() in KNOWN_ACCENTS:
                k = 'a'
            elif v.lower() in KNOWN_QUALIFIERS:
                k = 'q'
            else:
                unhandled_qualifiers.append(v)

            if k:
                k = k if not ipa else f"{k}{k}"
                if k in to_merge:
                    return f"dup_{k}"
                to_merge[k] = str(t.get(1)).strip()
        else:
            unhandled_templates.append(t)

        remaining_text = remaining_text.replace(str(t), "")

    if remaining_text.strip().strip(",.;:()}* ").strip():
        return "unhandled_text"

    if unhandled_templates:
        if all(str(t.name).strip() in ["sense", "enPR"] for t in unhandled_templates):
            return "unhandled_common_template"
        else:
            return "unhandled_template"

    params = get_template_params(ipa)
    # this is probably not safe to run automatically
    for k,v in to_merge.items():
        if any(re.match(f"^{k}[1-9]?$", str(p)) for p in params.keys()):
            return f"{k}_collision"
        if template_aware_contains("=", v):
            return f"{k}_value_contains_equal_sign"
        params[k] = v

#    for q in unhandled_qualifiers:
#        print("UQ:", q)

    if unhandled_qualifiers:
        return "unhandled_qualifier"

    params["_trailing_comments"] = trailing_comments
    return params


def parse_ipa_list(text):
    # returns a string on error
    # otherwise, returns list of dicts with ipa params

    #print(":: ", text)
    splits = list(template_aware_resplit(r"\s*(?:''|''')?(?:,\s*or\b|,|;|\band\b|\bor\b)+(?:''|''')?\s*", text))
    #print(splits)
    ipas = []
    prev_delim = None

    remaining_text = text


    for split_text, delim in splits:
        clean_delim = delim.strip()
        if prev_delim is None:
            prev_delim = clean_delim
        elif clean_delim and clean_delim != prev_delim:
            return "mismatched_delim"

        if len(splits) > 1 and "{{IPA|" not in split_text:
            return "no_ipa"

        res = parse_ipa(split_text)
        if isinstance(res, str):
            return res

        if len(splits) > 1 and 3 in res:
            return "split_multi_ipa"

        ipas.append(res)


#        if len(ipas) > 1:
#        for p in INLINE_IPA_PARAMS:
#        if any(isinstance(p, str) and p.startswith('a') for p in params):
#            return "has_a"

    return ipas

# iterate individual ipa + modifying params from {{IPA}} template params
def get_ipa_mods(ipa_params):

    idx = 2
    merged = {1}
    while idx in ipa_params:
        merged.add(idx)
        ipa = ipa_params[idx]
        mods = {}
        suffixes = ["", str(idx-1)] if idx == 2 else [str(idx-1)]
        for p in INLINE_IPA_PARAMS:
            for s in suffixes:
                if f"{p}{s}" in ipa_params:
                    mods[p] = ipa_params[f"{p}{s}"]
                    merged.add(f"{p}{s}")

        if ipa or mods:
            yield ipa, mods
        idx += 1

    if not ipa_params.keys() == merged:
        raise ValueError("KEY MISMATCH, probably non-specific param in {{IPA}}", ipa_params.keys(), merged)

def make_ipa_template(ipas):
    params = []

    lang = None
    qualifiers = None
    comments = []
    nocount = []
    for ipa_params in ipas:
        if lang is None:
            lang = ipa_params[1]
        if lang != ipa_params[1]:
            print("LANG_MISMATCH")
            return

        comment = ipa_params.pop("_trailing_comments", None)
        if comment:
            comments.append(comment)
        nocount.append(ipa_params.pop("nocount", None))

        for ipa, mods in get_ipa_mods(ipa_params):

            if qualifiers is None:
                qualifiers = mods.keys()
            else:
                if mods.keys() != qualifiers:
                    return #"ambig_merged_param"

            param = ipa
            for k,v in mods.items():
                param += f"<{k}:{v}>"
            params.append(param)

    if all(n for n in nocount):
        params.append("nocount=1")
    elif any(n for n in nocount):
        raise ValueError("mismatched nocount")

    return "{{IPA|" + lang + "|" + "|".join(params) + "}}" + "".join(comments)


class PronunciationFixer():

    def __init__(self):
        self._summary = None
        self._log = []

    def fix(self, code, section, location="", details=None):
        # When running tests, section will be empty
        if not section:
            return

        if isinstance(section, sectionparser.SectionParser):
            page = section.page
            path = ""
            target = page
        else:
            page = section.page
            path = section.path

        if self._summary is not None:
            if path:
                self._summary.append(f"/*{path}*/ {location} {details}")
            else:
                self._summary.append(f"{location} {details}")

        self._log.append(("autofix_" + code, page, path, location, details))

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
        if code == "unhandled_byline_template":
            print(code, section.page, section.path, location)
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
        if page.partition("#")[0] in ["уж", "だはんで", "-et", "-ttaa"]:
            return [] if summary is None else page_text

        entry = sectionparser.parse(page_text, page)
        if not entry:
            return [] if summary is None else page_text

        move_to_pos = []
        move_from = None

        for section in entry.ifilter_sections():

            if section.title == "Pronunciation":
                pop_lines = []
                for i, line in enumerate(section.content_wikilines):
                    l = line.strip()
                    # Comment
                    if re.match(r"^<!--.*?-->$", l, flags=re.DOTALL):
                        continue

                    prefix = re.match("^([:*#]*)", l).group(0)
                    l = l[len(prefix):].strip()

                    if "[[Image:" in l:
                        pop_lines.append(i)
                        continue

                    if "[[File:" in l:
                        m = re.match(r"\[\[File:(.+?)[\|\]]", l)
                        if m:
                            filename = m.group(1)
                            _, ext = os.path.splitext(filename)
                            ext = ext.strip(".")
                            if ext.lower() in ["oga", "ogg", "mp3", "flac", "wav"]:
                                self.warn("missing_audio_template", section, "", line)
                                continue

                            elif ext.lower() in ["jpg", "jpeg", "png", "gif", "svg", "tiff", "webm"]:
                                pop_lines.append(i)
                                continue
                            else:
                                self.warn("unhandled_file_extension", section, "", line)
                                continue
                        else:
                            self.warn("unparsable_file_link", section, "", line)
                            continue

                    wiki = mwparser.parse(l)
                    first_template = next(wiki.ifilter_templates(recursive=False), None)
                    if not first_template:
                        if "{{" not in l or "}}" not in l:
                            self.warn("text", section, "", line)
                        continue

                    if len(list(t for t in wiki.filter_templates(recursive=False) if str(t.name).strip() == "IPA")) > 1:
                        ipas = parse_ipa_list(l)
                        if isinstance(ipas, str):
                            if ipas == "not_ipa_list":
                                continue
                            self.warn("multi_ipa_" + ipas, section, "", line)
                            continue

                        try:
                            ipa_template = make_ipa_template(ipas)
                        except Exception as e:
                            print("MISMATCH", section.page, section.path, e)
                            continue

                        if not ipa_template:
                            self.warn("unmergable_multi_ipa", section, "", line)
                            continue

                        if not prefix:
                            prefix = "*"
                        section.content_wikilines[i] = prefix + " " + ipa_template
                        self.fix("multi_ipa", section, "", f"merged multiple IPA templates")
                        entry_changed = True
                        continue

                    remaining_text = l.replace(str(first_template), "", 1)
                    remaining_text = remaining_text.strip().strip(",.;:()}* ").strip()
                    remaining_text = re.sub(r"(\s*<!--.*?-->)+\s*$", "", remaining_text, flags=re.DOTALL)
                    is_single_template = remaining_text == ""

                    # entire line is a single template, no cleanup needed
                    if is_single_template:

                        if first_template is None:
                            print("=="*40, section.page, section.path)
                            print(section)
                            print("XXX", [l])
                            raise ValueError("bad stuff")

                        t = str(first_template.name).strip()
                        if not prefix and t in ["IPA", "rhyme", "rhymes", "homophones", "hmp", "homophone", "hyphenation", "hyph", "audio"]:
                            prefix = "*"
                            section.content_wikilines[i] = "* " + line
                            self.fix("unformatted", section, "", f"Added leading * to {first_template.name}")
                            entry_changed = True

                        if t in ["wikipedia", "wikiquote", "swp", "slim-wikipedia", "wp", "multiple-images"]:
                            pop_lines.append(i)
                            continue

                        elif t in ["IPA", "rhyme", "rhymes", "homophones", "hmp", "homophone", "hyphenation", "hyph", "audio"] \
                                or t in ["q", "qual", "qualifier", "i", "lb"] \
                                or t in ["rfp", "rfap", "rfref", "bg-hyph", "ka-hyphen", "enPR", "ja-ojad", "ko-tone", "ko-regional"] \
                                or any(t.endswith(x) for x in ["-pronunciation", "-p", "-pr", "-pron", "-IPA", "-ipa", "-ipa-rows", "-IPA-E", "-IPA-R"]):
                            continue

                        else:
                            self.warn("unhandled_single_template", section, t, line)
                            continue

                    if any(str(t.name).strip() == "IPA" for t in wiki.ifilter_templates(recursive=False)):

                        res = parse_ipa(l)
                        if isinstance(res, str):
                            self.warn("single_ipa_" + res, section, "", line)
                            continue

#                        if not l.startswith("{{IPA|"):
#                            self.warn("ipa_with_leading_text", section, "", line)
#                            continue
#
#                        if not l.endswith("/ref>"):
#                            self.warn("ipa_with_trailing_text", section, "", line)
#                            continue

#                        m = re.match(r"^({{IPA\|[^}]+)}}([,;: ]*(<\s*ref.*?/\s*ref>|<\s*ref[^>]+/\s*>))+$", l, flags=re.DOTALL)
#                        if not m:
#                            self.warn("ipa_with_mixed_ref", section, "", line)
#                            continue
#
#                        if m.group(0) not in line:
#                            self.warn("unmergable_reference", section, "", line)
#                            continue

#                        template = next(wiki.ifilter_templates(recursive=False))
#                        assert str(template.name).strip() == "IPA"
#                        if any(p.name.startswith("ref") for p in template.params):
#                            self.warn("unmergable_multi_ref", section, "", line)
#                            continue

#                        if len([p for p in template.params if str(p.name.strip()).isdigit()]) > 2:
#                            self.warn("multi_ipa_with_ref", section, "", line)
#                            continue

#                        refs = get_refs(l)
#                        if not refs:
#                            self.warn("unparsable_refs", section, "", line)
#                            continue

                        #params = [f"|ref{i if i > 1 else ''}={r}" for i,r in enumerate(refs, 1)]
#                        if len(params) > 1:
#                            self.warn("ipa_with_multi_ref", section, "", line)
#                        else:

                        try:
                            ipa_template = make_ipa_template([res])
                        except Exception as e:
                            print("MISMATCH", section.page, section.path, e)
                            continue

                        if not ipa_template:
                            self.warn("unmergable_single_ipa", section, "", line)
                            continue

                        section.content_wikilines[i] = prefix + " " + ipa_template
                        #line.replace(m.group(0), m.group(1) + "|ref=" + " !!! ".join(refs) + "}}")
                        self.fix("merged_templates", section, "", f"merged data into IPA template")
                        entry_changed = True
                        continue

                    if not l.startswith("{{"):
                        self.warn("leading_text", section, "", line)
                        continue

                    if not l.endswith("}}"):
                        self.warn("trailing_text", section, "", line)
                        continue

                    if len(wiki.filter_templates(recursive=False)) > 1:
                        self.warn("multi_templates", section, "", line)
                        continue


                if pop_lines:
                    move_to_pos = []
                    for pi in reversed(pop_lines):
                        pl = section.content_wikilines[pi]
                        # don't move lines that might be related to pronunciation
                        if "MapOf" in pl or "pronunciation" in pl.lower() or "location" in pl.lower():
                            continue
                        move_to_pos.insert(0, section.content_wikilines.pop(pi))
                        move_from = section

                    # trim trailing empty lines
                    while section.content_wikilines and section.content_wikilines[-1].strip() == "":
                        section.content_wikilines.pop()
                continue

            elif section.title in EXTENDED_POS and move_to_pos:

                pos = sectionparser.parse_pos(section)
                if not pos or not pos.senses:
                    self.warn("wikipedia_before_unparsable_pos", section, "", "")
                    continue

                self.warn("misplaced_lines", section, "", "")
                continue

                pos.headlines = move_to_pos + pos.headlines
                move_to_pos = []

                new_pos_text = str(pos)
                section.content_wikilines = [new_pos_text]
                entry_changed = True

                self.fix("misplaced_lines", section, "", "moved floating elements from Pronunciation to POS")

        if move_to_pos:
            self.warn("misplaced_lines_without_pos", move_from, "", "\n".join(move_to_pos))
            entry_changed = False

        if summary is None:
            return self._log

        self.condense_summary(summary)

        if entry_changed:
            return str(entry)

        return page_text
