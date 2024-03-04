import ahocorasick
import csv
import enwiktionary_sectionparser as sectionparser
import re
import multiprocessing
import os
import sys
import mwparserfromhell as mwparser
import json
import urllib

from collections import namedtuple
_taxlink = namedtuple("_taxlink", [ "label", "i", "no_auto" ])

def make_taxlink(text, taxlink_data):
    template = ["taxfmt", text, taxlink_data.label]
    if taxlink_data.i and taxlink_data.label not in ["genus", "subgenus", "section", "subsection", "species", "subspecies", "subspecies", "form", "variety"]:
        template.append("i=1")
    return "{{" + "|".join(template) + "}}"

def cleanup_taxfmt(text):
    print("cleanup: ", text)

    template_list = r"((\{\{\s*(taxfmt|taxlink)\s*[|][^{}]*?\}\}[,; ]*)*)"
    bold_ital_start = r"(?<!')(?:'{5})"
    bold_ital_end  = "(:?'{5})(?!')"
    ital_start = r"(?<!')(?:'{2})"
    ital_end  = "(:?'{2})(?!')"

    # convert '''''{{taxfmt}}''''' to '''{{taxfmt}'''
    pat = bold_ital_start + template_list + bold_ital_end
    text = re.sub(pat, r"'''\1'''", text)

    # convert ''{{taxfmt}}'' to {{taxfmt}}
    pat = ital_start + template_list + ital_end
    text = re.sub(pat, r"\1", text)

    # convert '''''({{taxlink}})''''' to '''({{taxlink}})'''
    pat = bold_ital_start + r"\(" + template_list + r"\)" + bold_ital_end
    text = re.sub(pat, r"'''(\1)'''", text)

    # convert ''({{taxlink}})'' to ({{taxlink}})
    pat = ital_start + r"\(" + template_list + r"\)" + ital_end
    text = re.sub(pat, r"(\1)", text)

    return text


ALLOWED_TEMPLATES = ["col-auto", "col2", "col3", "col4", "col4", "der2", "der3", "der4", "der5", "quote-journal", "quote-book", "trans-top", "ja-r/multi", "ja-r/args", "gl", "gloss", "coi", "syn", "ngd", "cog", "q", "syn of", "synonym of", "qual", "qualifier", "trans-see", "obs form", "obsolete form of", "l"]
#ALLOWED_TEMPLATES = []
MATCH_LINKS=True

def safe_replace(old, new, text):
    """ returns new_text, replacement_count """

    assert "⏶" not in text
    assert "⏶" not in new
    new_text = sectionparser.utils.wiki_replace(old, "⏶" + new, text, match_templates=ALLOWED_TEMPLATES, match_links=MATCH_LINKS)
    count = new_text.count("⏶")
    new_text = new_text.replace("⏶", "")
    return new_text, count



class MissingTaxlinkFixer():

    def __init__(self, taxons):
        self._summary = None
        self._log = []

        with open(taxons) as infile:
            self.taxons = {x[0]:_taxlink(x[1],x[2],x[3]) for x in csv.reader(infile, delimiter="\t")}

        print("Loaded", len(self.taxons), "taxons")
        self._trans = str.maketrans({"'": " ", "[": " ", "]": " " })

        self.auto = ahocorasick.Automaton()
        for substr in self.taxons.keys():
            self.auto.add_word(substr, substr)
        self.auto.make_automaton()

#        pattern = r"\b(" + "|".join(sorted(self.taxons.keys())) + r")\b"
#        pattern = pattern.lower()
#        print(pattern)
#        self._regex = re.compile(pattern)

    def fix(self, code, page, details):
        #print("FIX", code, page, details)

        # report mode
        if self._summary is None:
            self._log.append(("autofix_" + code, page, details))

        # fix-mode
        else:
            msg = details
            if msg not in self._summary:
                self._summary.append(msg)

    def warn(self, code, page, details=None):
        #print(code, page, details)
        if self._summary is not None:
            return

        self._log.append((code, page, details))

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

#        if "==English==" not in page_text and "==Translingual==" not in page_text:
#            return [] if summary is None else page_text

        clean = page_text.translate(self._trans) #.lower()
        clean = re.sub(r"\s\s+", " ", clean)

        substring_matches = sorted(set(found for end_ind, found in self.auto.iter(clean) if found != page), key=lambda x: (len(x)*-1, x))

        # hacky method to remove subsets - removed because the careful matching of balanced [[ and '' obviates the need, but
        # ( Capra aegagrus, Capra aegagrus hircus, Capra hircus ) => ( Capra aegagrus hircus, Capra hircus )
        # if that's removed in the future, this should be re-enabled to avoid bad matches
#        matches = [m for m in all_matches if all(not p.startswith(m) or p == m for p in all_matches)]

        if not substring_matches:
            return [] if summary is None else page_text

        wikt = sectionparser.parse(page_text, page)

        fixes = []
        changes = False

        print("substring matches", substring_matches)

#        # substring matches will match "Panda" in "RedPandaBear"
#        # Convert substring matches to full-string matches
        string_matches = []
        for target in substring_matches:
            pattern = r"(?:\b|(?<=[']))" + r"[ '\]\[]+".join(target.split(" ")) + r"(?:\b|(?=[']))"
            string_matches += re.findall(pattern, page_text)

        string_matches = sorted(set(string_matches), key=lambda x: (len(x)*-1, x))
        print("string matches", string_matches)

        for string_match in string_matches:

            target = re.sub(r"['\[\]]", "", string_match)
            taxlink_data = self.taxons[target]

            #pattern = fr"""(?x)
            #     ('''''|'''|''|\[\[)*    # match formatting or opening double brackets
            #     {target}
            #     ('''''|'''|''|\]\])*    # match formatting or closing double brackets
            #     """
            pattern = r"('''''|'''|''|\[\[)*" + re.escape(string_match) + r"('''''|'''|''|\]\])*"

            clean_fixes = []   # Fixes that can be applied anywhere with str.replace()
            careful_fixes = [] # Fixes that can only be applied carefully with wiki_replace()
            unmatchable_fixes = [] # Fixes that exist in the page that appear inside forbidden parts of the text (inside template names, comments, etc)

            # matches may overlap, eg [[cat]] and ''[[cat]]''. Sort matches longest-shortest as an imperfect workaround
            for match in sorted([m.group(0).strip() for m in re.finditer(pattern, page_text)], key=lambda x: (len(x)*-1, x)):

                print([string_match, match])

                match_count = page_text.count(match)
                #print("MATCHA", match, "[" not in match, "]]" in match, [match.partition("]")[2].strip("']")])
                if "'" not in match and "[" not in match:
                    clean_matches = sorted(set(m.group(0) for m in re.finditer(r"\{\{(l|ll|m)[|][^|{}]*[|]" + re.escape(string_match) + r"\}\}", page_text)))
                    clean_match = "[[" + string_match + "]]"
                    if clean_match in page_text:
                        clean_matches.append(clean_match)

                    if clean_matches:
                        clean_fixes += clean_matches
                        print("USING CLEAN FIXES", clean_fixes)
                        if sum(page_text.count(m) for m in clean_matches) == match_count:
                            continue

                    continue

                # ''Haliaeetus albicilla'']] as full paramater of [[Haliaeetus albicilla|''Haliaeetus albicilla'']]
                if "[" not in match and "]]" in match and match.partition("]")[2].strip("']") == "":
                    param, _, split = match.partition("]")
                    if split.strip("']") == "":

                        clean_matches = [m for m in [
                            "[[" + target + "|" + param + "]]",
                            "[[" + target + "#Translingual|" + param + "]]",
                            ] if m in page_text]

                        # Allow a replacement only when it matches the entire parameter
                        clean_match = "|" + param + "]]"
                        if clean_match in page_text:
                            clean_matches.append(param)

                        if clean_matches:
                            clean_fixes += clean_matches
                            print("USING CLEAN FIXES", clean_fixes)
                            if sum(page_text.count(m) for m in clean_matches) == match_count:
                                continue

                if match.startswith("''[[") and match.endswith("]]") and match.count("''") == 1:
                    match = match.lstrip("'")

                if match.startswith("[[") and match.endswith("]]''") and match.count("''") == 1:
                    match = match.rstrip("'")

                # [[Rallus aquaticus]]'']]
                if match.startswith("[[") and match.endswith("]]'']]") and match.count("[[") == 1:
                    match = match[:-4]

                # [[Rallus aquaticus]]]]
                if match.startswith("[[") and match.endswith("]]]]") and match.count("[[") == 1:
                    match = match[:-2]


                # '''[[Rallus aquaticus]]]]'''
                if match.startswith("'''") and match.endswith("'''") and match.count("'") == 6:
                    match = match[3:-3]

                # '''''[[Rallus aquaticus]]]]'''''
                if match.startswith("'''''") and match.endswith("'''''") and match.count("'") == 10:
                    match = match[3:-3]

                print("trimmed match: ", match)

                # Check that the match will actually be applied before warning about unbalanced items
                _, has_matches = safe_replace(match, "XXX", page_text)
                if not has_matches:
                    print("no matches")
                    unmatchable_fixes.append(match)
                    continue

                # If it starts with "[", it must start with exactly 2 [
                # [ and ] count must be balanaced
                if match.count("[") != match.count("]") or match.count("[") % 2:
                    if not taxlink_data.no_auto:
                        self.warn("unbalanced_brackets", page, match)
                    continue

                start_count = len(re.match(r"^\[*", match).group(0))
                end_count = len(re.search(r"\]*$", match).group(0))
                if start_count != end_count or start_count not in [0,2]:
                    if not taxlink_data.no_auto:
                        self.warn("unbalanced_brackets", page, match)
                    continue

                start_count = len(re.match("^'*", match).group(0))
                end_count = len(re.search("'*$", match).group(0))
                if start_count != end_count or match.count("'") % 2:
                    if "]" not in match:
                        clean_matches = [m for m in [
                            "{{l|mul|" + target + "|" + match + "}}",
                            "{{ll|mul|" + target + "|" + match + "}}",
                            "{{m|mul|" + target + "|" + match + "}}"]
                            if m in page_text]
                        if clean_matches:
                            clean_fixes += clean_matches
                            continue

                    if not taxlink_data.no_auto:
                        self.warn("unbalanced_quotes", page, match)
                    continue

                # Allow bold in full matches
                if match.count("'''"):
                    if "]" not in match:
                        clean_matches = [m for m in [
                            "{{l|mul|" + target + "|" + match + "}}",
                            "{{ll|mul|" + target + "|" + match + "}}",
                            "{{m|mul|" + target + "|" + match + "}}"]
                            if m in page_text]
                        if clean_matches:
                            clean_fixes += clean_matches
                            continue

                    if not taxlink_data.no_auto:
                        self.warn("has_bold", page, match)
                    continue

                careful_fixes.append(match)


            if not careful_fixes and not clean_fixes:
                continue

            print("CLEAN", clean_fixes)
            print("CAREFUL", careful_fixes)

            for section in wikt.ifilter_sections():

                # Don't match hyper/hyponyms yet, may be better with another template
                #if section.title.endswith("nyms"):
                #    continue

                # Taxlinks flagged no_auto contain text like "Paris" or "Argentina" and should only
                # replace matches inside Translingual, and not inside Translingual:Etymology
                if taxlink_data.no_auto:
                    if "Translingual" not in section.path:
                        continue
                    if section.title == "Etymology":
                        continue

                new = make_taxlink(target, taxlink_data)
                for old in clean_fixes:
                    fix = (old, new)

                    print("fixing", fix)

                    for idx, wikiline in enumerate(section.content_wikilines):
                        new_wikiline = wikiline.replace(old, new)
                        if new_wikiline == wikiline:
                            continue

                        new_wikiline = cleanup_taxfmt(new_wikiline)
                        section.content_wikilines[idx] = new_wikiline
                        changed = True
                        if fix not in fixes:
                            fixes.append(fix)

                for old in careful_fixes + unmatchable_fixes:
                    fix = (old, new)

                    for idx, wikiline in enumerate(section.content_wikilines):
                        assert "⏶" not in wikiline

                        match_count = re.sub(re.escape(old), "⏶", wikiline).count("⏶")
                        if not match_count:
                            continue

                        new_wikiline, change_count = safe_replace(match, new, wikiline)
                        if change_count != match_count:
                            bad = re.sub("(" + re.escape(old) + ")", r"<BAD>\1</BAD>", new_wikiline)
                            self.warn("unsafe_match", page, bad)

                            assert bad.count("<BAD>") == match_count-change_count

                        if change_count:
                            new_wikiline = cleanup_taxfmt(new_wikiline)
                            section.content_wikilines[idx] = new_wikiline
                            changed = True
                            if fix not in fixes:
                                fixes.append(fix)


        if fixes:
            for fix in fixes:
                old, new = fix
                #self.fix("match", page, f"replaced {old} with {new}")
                self.fix("match", page, "Applied {{taxfmt}} to taxon name")

#            details = "<pre>" + "\n".join(f"{old} => {new}" for old, new in fixes) + "</pre>"
#            self.fix("match", page, details)
#            print("FIX", page, details)

        if summary is None:
            return self._log

        if not summary:
            return page_text

        return str(wikt)
