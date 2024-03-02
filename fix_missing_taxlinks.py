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
    if taxlink_data.i:
        template.append("i=1")
    return "{{" + "|".join(template) + "}}"

class MissingTaxlinkFixer():

    def __init__(self, taxons):
        self._summary = None
        self._log = []

        with open(taxons) as infile:
            self.taxons = {x[0]:_taxlink(x[1],x[2],x[3]) for x in csv.reader(infile, delimiter="\t")}

        print("Loaded", len(self.taxons), "taxons")
        self._trans = str.maketrans({"'": None, "[": " ", "]": " " })

        self.auto = ahocorasick.Automaton()
        for substr in self.taxons.keys():
            self.auto.add_word(substr, substr)
        self.auto.make_automaton()

#        pattern = r"\b(" + "|".join(sorted(self.taxons.keys())) + r")\b"
#        pattern = pattern.lower()
#        print(pattern)
#        self._regex = re.compile(pattern)

    def fix(self, code, page, details):

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

        # hacky method to remove subsets
        # ( Capra aegagrus, Capra aegagrus hircus, Capra hircus ) => ( Capra aegagrus hircus, Capra hircus )
        all_matches = set(found for end_ind, found in self.auto.iter(clean))
        matches = [m for m in all_matches if all(not p.startswith(m) or p == m for p in all_matches)]

        if not matches:
            return [] if summary is None else page_text

        wikt = sectionparser.parse(page_text, page)

        fixes = []
        changes = False
        for m in matches:
            taxlink_data = self.taxons[m]

            pattern = r"(^|[ '\[]+)" + "[ '\[\]]+".join(map(re.escape, m.split(" "))) + r"([ '\]]+|$)"

            # matches may overlap, eg [[cat]] and ''[[cat]]''. Sort matches longest-shortest as an imperfect workaround
            exact_matches = sorted([m.group(0).strip() for m in re.finditer(pattern, page_text) if "'" in m.group(0) or "[" in m.group(0)], key=lambda x: (len(x)*-1, x))
            if not exact_matches:
                # Not really worth logging, mostly matches text inside templates and other places where it's not in italics or brackets
                #if " " in m:
                #    self.warn("missing_exact_match", page, m)
                continue

#            print("MATCH", exact_matches)

            new = make_taxlink(m, taxlink_data)

            for old in exact_matches:

                if old.startswith("[") and not old.endswith("]") or (old.count("[") != old.count("]")):
                    if not taxlink_data.no_auto:
                        self.warn("unbalanced_brackets", page, old)
                    continue

                if old.startswith("'") and not old.endswith("'") or old.count("'")%2:
                    if not taxlink_data.no_auto:
                        self.warn("unbalanced_quotes", page, old)
                    continue

                fix = (old, new)
                if fix not in fixes:

                    for section in wikt.ifilter_sections():

                        # Don't match hyper/hyponyms yet, may be better with another template
                        if section.title.endswith("nyms"):
                            continue

                        # Taxlinks flagged no_auto contain text like "Paris" or "Argentina" and should only
                        # replace matches inside Translingual, and not inside Translingual:Etymology
                        if taxlink_data.no_auto:
                            if "Translingual" not in section.path:
                                continue
                            if section.title == "Etymology":
                                continue

                        for idx, wikiline in enumerate(section.content_wikilines):

                            match_count = wikiline.count(old)
                            if not match_count:
                                continue

                            new_wikiline = sectionparser.utils.wiki_replace(old, new + "⏶", wikiline)
                            change_count = new_wikiline.count("⏶")
                            new_wikiline = new_wikiline.replace("⏶", "")
                            if change_count != match_count:
                                bad = sectionparser.utils.wiki_replace(old, "<BAD>" + new + "</BAD>", wikiline, invert_matches=True)
                                self.warn("unsafe_match", page, bad)

                            if change_count:
                                section.content_wikilines[idx] = new_wikiline
                                changed = True
                                if fix not in fixes:
                                    fixes.append(fix)


        if fixes:
            for fix in fixes:
                old, new = fix
                self.fix("match", page, f"replaced {old} with {new}")

#            details = "<pre>" + "\n".join(f"{old} => {new}" for old, new in fixes) + "</pre>"
#            self.fix("match", page, details)
#            print("FIX", page, details)

        if summary is None:
            return self._log

        if not summary:
            return page_text

        return str(wikt)
