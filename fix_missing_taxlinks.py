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
_taxlink = namedtuple("_taxlink", [ "name", "rank", "i", "no_auto" ])

def cleanup_taxfmt(text):
    #print("cleanup: ", [text])

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

    # convert {{q|{{taxlink}}}} to ({{taxlink}}"
    pat = r"\{\{\s*q\s*[|]\s*" + template_list + r"\s*}}"
    text = re.sub(pat, r"(\1)", text)

    return text



def get_safe_replacements(page_text, target, param=None, match_only_mul=True):

    """ Get matches that can be anywhere on the page, even inside templates, comments, etc """

    safe_fixes = []
    lang_pat = "mul" if match_only_mul else "[a-z_ -]*"

    if param:
        safe_fixes += [m for m in [
            "[[''" + target + "|" + param + "'']]",
            "[[''" + target + "#Translingual|" + param + "'']]",
            "''[[" + target + "|" + param + "]]''",
            "''[[" + target + "#Translingual|" + param + "]]''",

            # Not safe - will match inside {{head}} where we probably don't want {{taxfmt}}
            #"[[" + target + "|" + param + "]]",
            #"[[" + target + "#Translingual|" + param + "]]",
            ] if m in page_text]

        safe_fixes += sorted(set(m.group(0) for m in re.finditer(r"\{\{(l|ll|m)[|]" + lang_pat + r"[|](\[\[|'')*" + re.escape(target) + r"[|]" + re.escape(param) + r"(''|\]\])*\}\}", page_text)))

    else:
        safe_fixes += [m for m in [
            #"''[[" + target + "]]''",  # Not safe, replaces '''[[target]]''' with '[[target]]'
            "[[''" + target + "'']]",
            ] if m in page_text]
        safe_fixes += sorted(set(m.group(0) for m in re.finditer(r"\{\{(l|ll|m)[|]" + lang_pat + r"[|](\[\[|'')*" + re.escape(target) + r"(''|\]\])*\}\}", page_text)))



    #print("GET SAFE:", [target, param], safe_fixes)

    return safe_fixes



class MissingTaxlinkFixer():

    def __init__(self, template_name, taxons, aggressive=False):
        self._summary = None
        self._log = []
        self._template_name = template_name

        if aggressive:
            self.ALLOWED_TEMPLATES = ["col-auto", "col2", "col3", "col4", "col4", "der2", "der3", "der4", "der5", "ja-r/multi", "ja-r/args", "gl", "gloss", "coi", "syn", "ngd", "cog", "q", "syn of", "synonym of", "qual", "qualifier", "obs form", "obsolete form of", "suffix"]
            self.MATCH_LINKS=True
        else:
            self.ALLOWED_TEMPLATES = []
            self.MATCH_LINKS=False

        TAXNAME_PAT = "[a-zA-Z0-9()×. -]+"
        with open(taxons) as infile:
            self.taxons = {x[0]:(x[1],x[2],x[3]) for x in csv.reader(infile, delimiter="\t") if re.sub(TAXNAME_PAT, "", x[0]) == ""}

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

    def make_template(self, taxon_data):
        template = [self._template_name, taxon_data.name, taxon_data.rank]
        if taxon_data.i and taxon_data.rank not in ["genus", "subgenus", "section", "subsection", "species", "subspecies", "subspecies", "form", "variety"]:
            template.append("i=1")
        return "{{" + "|".join(template) + "}}"

    def text_replace(self, old, new, text):

        #print(":: SAFE_REPLACE", (old, new, text))
        pre_count = text.count(new)
        text = text.replace(old, new)
        post_count = text.count(new)
        count = post_count - pre_count

        #print(":: SAFE_REPLACED", (text))
        return text, count

    def careful_replace(self, old, new, text, **kwargs):
        """ returns new_text, replacement_count """

        if "match_templates" not in kwargs:
            kwargs["match_templates"] = self.ALLOWED_TEMPLATES

        if "match_links" not in kwargs:
            kwargs["match_links"] = self.MATCH_LINKS

        #if new != "⏶":
        #    print(":: SREPLACE", (old, new, text))
        pre_count = text.count(new)
        text = sectionparser.utils.wiki_replace(old, new, text, **kwargs)
        post_count = text.count(new)
        count = post_count - pre_count
        #if new != "⏶":
        #    print(":: SREPLACED", [text])
        return text, count

    def very_careful_replace(self, old, new, text):
        return self.careful_replace(old, new, text, match_templates=None, match_links=None)

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


    def get_taxon_data(self, text):
        # strip brackets and quotes
        text = re.sub(r"['\[\]]", "", text)
        # Condense whitespace
        text = re.sub(r"\s\s+", " ", text)
        return _taxlink(text, *self.taxons[text])

    def get_fixes(self, string_match, page_text):
        safe_fixes = []   # fixes that can be applied anywhere with str.replace()
        careful_fixes = [] # fixes that can only be applied carefully with wiki_replace()
        very_careful_fixes = [] # fixes that can only be applied very carefully with wiki_replace and not matching inside any templates
        unmatchable_fixes = [] # Fixes that exist in the page that appear inside forbidden parts of the text (inside template names, comments, etc)

        unbalanced_brackets = []
        unbalanced_quotes = []

        taxon_data = self.get_taxon_data(string_match)
        target = taxon_data.name

        safe_fixes = get_safe_replacements(page_text, target, match_only_mul=taxon_data.no_auto)

        pattern = r"( |'''''|'''|''|\[\[)*" + re.escape(string_match) + r"( |'''''|'''|''|\]\])*"
        # matches may overlap, eg [[cat]] and ''[[cat]]''. sort matches longest-shortest as an imperfect workaround
        for match in sorted([m.group(0).strip() for m in re.finditer(pattern, page_text)], key=lambda x: (len(x)*-1, x)):

            match_unbalanced_brackets = []
            match_unbalanced_quotes = []

            #print([string_match, match])

            match_count = page_text.count(match)

            if "'" not in match and "[" not in match:
                continue

            # trim leading and trailing '' and ''' when separated by a space
            prev = None
            while prev != match:
                prev = match
                match = re.sub("^'+ ", "", match)
                match = re.sub(" '+$", "", match)

            # ''haliaeetus albicilla'']] as full paramater of [[haliaeetus albicilla|''haliaeetus albicilla'']]
            if "[" not in match and "]]" in match and match.partition("]")[2].strip("']") == "":
                param, _, split = match.partition("]")
                if split.strip("']") == "":
                    safe_fixes += get_safe_replacements(page_text, target, match, match_only_mul=taxon_data.no_auto)

            # check for full templates using unstripped match
            if "[" not in match and "]" not in match:
                safe_matches = get_safe_replacements(page_text, target, match, match_only_mul=taxon_data.no_auto)
                if safe_matches:
                    safe_fixes += safe_matches

            if match.startswith("''[[") and match.endswith("]]") and match.count("''") == 1:
                match = match.lstrip("'")

            if match.startswith("[[") and match.endswith("]]''") and match.count("''") == 1:
                match = match.rstrip("'")

            # [[rallus aquaticus]]'']]
            if match.startswith("[[") and match.endswith("]]'']]") and match.count("[[") == 1:
                match = match[:-4]

            # [[rallus aquaticus]]]]
            if match.startswith("[[") and match.endswith("]]]]") and match.count("[[") == 1:
                match = match[:-2]

            # '''[[rallus aquaticus]]]]'''
            if match.startswith("'''") and match.endswith("'''") and match.count("'") == 6:
                match = match[3:-3]

            # '''''[[rallus aquaticus]]]]'''''
            if match.startswith("'''''") and match.endswith("'''''") and match.count("'") == 10:
                match = match[3:-3]

            if "'" not in match and "[" not in match and "]" not in match:
                continue

            # check for full templates using stripped match
            if "[" not in match and "]" not in match:
                safe_matches = get_safe_replacements(page_text, target, match, match_only_mul=taxon_data.no_auto)
                if safe_matches:
                    safe_fixes += safe_matches

            # check that the match will actually be applied before warning about unbalanced items
            _, has_matches = self.careful_replace(match, "⏶", page_text)

            if not has_matches:
                unmatchable_fixes.append(match)
                continue

            # if it starts with "[", it must start with exactly 2 [
            # [ and ] count must be balanaced
            if match.count("[") != match.count("]") or match.count("[") % 2:
                if not taxon_data.no_auto:
                    unbalanced_brackets.append(match)
                continue

            start_count = len(re.match(r"^\[*", match).group(0))
            end_count = len(re.search(r"\]*$", match).group(0))
            if start_count != end_count or start_count not in [0,2]:
                if not taxon_data.no_auto:
                    unbalanced_brackets.append(match)
                continue

            start_count = len(re.match("^'*", match).group(0))
            end_count = len(re.search("'*$", match).group(0))
            if start_count != end_count or match.count("'") % 2:
                if not taxon_data.no_auto:
                    unbalanced_quotes.append(match)
                continue

            # Allow bold in full matches
            if match.count("'''"):
                if not taxon_data.no_auto:
                    self.warn("has_bold", page, match)
                continue

            careful_fixes.append(match)


        return safe_fixes, careful_fixes, very_careful_fixes, unmatchable_fixes, unbalanced_brackets, unbalanced_quotes



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

        #print("substring matches", substring_matches)

#        # substring matches will match "Panda" in "RedPandaBear"
#        # Convert substring matches to full-string matches
        string_matches = []
        for target in substring_matches:
            pattern = r"(?:\b|(?<=[']))" + r"[ '\]\[]+".join(target.split(" ")) + r"(?:\b|(?=[']))"
            string_matches += [m for m in re.findall(pattern, page_text) if m != page]

        string_matches = sorted(set(string_matches), key=lambda x: (len(x)*-1, x))
        #print("string matches", string_matches)

        for string_match in string_matches:
            safe_fixes, careful_fixes, very_careful_fixes, unmatchable_fixes, unbalanced_brackets, unbalanced_quotes = self.get_fixes(string_match, page_text)
            if not safe_fixes and not careful_fixes and not very_careful_fixes:
                continue

            #print("SAFE", safe_fixes)
            #print("CAREFUL", careful_fixes)
            #print("VERY CAREFUL", very_careful_fixes)

            taxon_data = self.get_taxon_data(string_match)

            for section in wikt.ifilter_sections():

                # Don't match hyper/hyponyms yet, may be better with another template
                #if section.title.endswith("nyms"):
                #    continue

                # Taxlinks flagged no_auto contain text like "Paris" or "Argentina" and should only
                # replace matches inside Translingual, and not inside Translingual:Etymology
                if taxon_data.no_auto:
                    if "Translingual" not in section.path:
                        continue
                    if section.title == "Etymology":
                        continue

                new = self.make_template(taxon_data)
                fixes = []

                for old in safe_fixes:
                    fixes.append((old, new, self.text_replace))

                for old in careful_fixes + unmatchable_fixes:
                    fixes.append((old, new, self.careful_replace))

                for old in very_careful_fixes:
                    fixes.append((old, new, self.very_careful_replace))

                for old, new, fixer in fixes:

                    for idx, wikiline in enumerate(section.content_wikilines):
                        sub_line = wikiline.replace(new, "⌁")
                        match_count = sub_line.count(old)
                        if not match_count:
                            continue

                        new_wikiline, change_count = fixer(old, new, sub_line)
                        new_wikiline = new_wikiline.replace("⌁", new)

                        if change_count:
                            new_wikiline = cleanup_taxfmt(new_wikiline)
                            section.content_wikilines[idx] = new_wikiline
                            self.fix("match", page, "Applied {{" + self._template_name + "}} to taxon name")

                for idx, wikiline in enumerate(section.content_wikilines):
                    unapplied_fixes = []
                    for fix in fixes:
                        old, new, fixer = fix
                        idx = len(unapplied_fixes)
                        tag = f"<BAD:{idx}>"

                        old_wikiline = wikiline
                        wikiline = wikiline.replace(old, tag)
                        if old_wikiline != wikiline:
                            unapplied_fixes.append(fix)

                    if not unapplied_fixes:
                        continue

                    for error, matches in [
                            ("unbalanced_brackets", unbalanced_brackets),
                            ("unbalanced_quotes", unbalanced_quotes)
                            ]:
                        for match in matches:
                            if match not in wikiline:
                                continue
#                            print("BAD", (match, wikiline))

                            line = wikiline.replace(match, f"<BAD>{match}</BAD>")
                            for idx, fix in enumerate(unapplied_fixes):
                                old, new, fixer = fix
                                tag = f"<BAD:{idx}>"
                                line = line.replace(tag, f"{old}")

                            self.warn(error, page, line)

                    for idx, fix in enumerate(unapplied_fixes):
                        old, new, fixer = fix
                        tag = f"<BAD:{idx}>"
                        wikiline = wikiline.replace(tag, f"<BAD>{old}</BAD><GOOD>{new}</GOOD>")

                    self.warn("safe_match", page, wikiline)

#                            bad_count = bad.count("<BAD>")
#                            if not bad_count == match_count-change_count:
#                                print(match_count, change_count, bad.count("<BAD>"), existing_count)
#                                print(page)
#                                print((old, new, fixer))
#                                print("----")
#                                print(wikiline)
#                                print("----")
#                                print(new_wikiline)
#                                print("----")
#                                print(bad)
#                                raise ValueError("mismatch")
#                            assert bad.count("<BAD>") == match_count-change_count



        if summary is None:
            return self._log

        if not summary:
            return page_text

        return str(wikt)
