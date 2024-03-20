import enwiktionary_sectionparser as sectionparser
import re
import multiprocessing
import os
import sys
import mwparserfromhell as mwparser
import json
import urllib


def clean_name(obj):
    text = re.sub(r"<!--.*?-->", "", str(obj.name), flags=re.DOTALL)
    return text.strip()

def clean_value(obj):
    text = re.sub(r"<!--.*?-->", "", str(obj.value), flags=re.DOTALL)
    return text.strip()

class BracketFixer():

    def __init__(self):
        self._summary = None
        self._log = []

    def fix(self, code, page, template, keys, details):

        if isinstance(keys, str):
            keys = [keys]

        # report-mode
        if self._summary is None:
            self._log.append(("autofix_" + code, page, clean_name(template), None, details, None))

        # fix-mode
        else:
            msg = f"{clean_name(template)}: {details}"
            if msg not in self._summary:
                self._summary.append(msg)

    def highlight_bad_params(self, template, keys):

        bad_params = []
        for p in template.params:
            if clean_name(p) in keys:
                bad_params.append(p)

        assert len(bad_params) == len(keys)

        for p in bad_params:
            if not p.showkey:
                p.name = "<BAD>"
                p.showkey = True
            else:
                p.name = "<BAD>" + str(p.name)

            p.value = str(p.value) + "</BAD>"

#        m = re.search("[|]\s*" + re.escape(str(template.get(key))), str(template))
#        if not m:
#            raise ValueError("no match")
#        bad_data = m.group(0)



    def warn(self, code, page, template, keys, details=None):

        if self._summary is not None:
            print(code, page, clean_name(template), keys, details)
            return

        if isinstance(keys, str):
            keys = [keys]

        self.highlight_bad_params(template, keys)

        # fix for numbered parameters that become named parameters
        bad_text = str(template).replace("<BAD>=", "<BAD>")
        key_str = ", ".join(keys)

        #print("WARN", (code, page, clean_name(template), key, details))
        self._log.append((code, page, clean_name(template), key_str, details, bad_text))

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

        if "cite-" not in page_text and "quote-" not in page_text:
            return [] if summary is None else page_text

        wiki = mwparser.parse(page_text)
        to_replace_str = []

        for t in wiki.ifilter_templates(recursive=True, matches=lambda x: clean_name(x).startswith("quote-") or clean_name(x).startswith("cite-")):

            t_name = clean_name(t)
            bad_params = []

            for p in t.params:
                p_name = clean_name(p)
                p_value = clean_value(p)

                OPEN =  ["[", "&lbrack;", "&#91;", "&lsqb;"]
                CLOSE = ["]", "&rbrack;", "&#93;", "&rsqb;"]

                openers = sum(p_value.count(x) for x in OPEN)
                closers = sum(p_value.count(x) for x in CLOSE)

                if openers != closers:
                    bad_params.append(p_name)

            if sorted(bad_params) == ["location", "publisher"]:
                loc = t.get("location")
                pub = t.get("publisher")
            elif sorted(bad_params) == ["location2", "publisher2"]:
                loc = t.get("location2")
                pub = t.get("publisher2")
            else:
                loc = None
                pub = None

            # attempt to fix split brackets [location, publisher]
            if loc and pub:
                loc_value = clean_value(loc)

                loc_openers = sum(loc_value.count(x) for x in OPEN)
                loc_closers = sum(loc_value.count(x) for x in CLOSE)

                pub_value = clean_value(pub)
                pub_openers = sum(pub_value.count(x) for x in OPEN)
                pub_closers = sum(pub_value.count(x) for x in CLOSE)

                loc_starting_bracket = [x for x in OPEN if loc_value.startswith(x)]
                pub_ending_bracket = [x for x in CLOSE if pub_value.endswith(x)]

                if loc_starting_bracket and loc_openers == 1 and loc_closers == 0 and \
                    pub_ending_bracket and pub_openers == 0 and pub_closers == 1:
                        print("FIXING")

                        cleanup = [(loc, str(loc.value).strip().removeprefix(loc_starting_bracket[0]).strip()),
                                   (pub, str(pub.value).strip().removesuffix(pub_ending_bracket[0]).strip())]

                        for param, value in cleanup:
                            if ":" in value or "{" in value or "/" in value:
                                param.value = "&lbrack;" + value + "&rbrack;"
                            else:
                                param.value = "[" + value + "]"

#                else:
#                    print("NOT FIXING", [loc_starting_bracket, loc_openers, loc_closers], [pub_ending_bracket, pub_openers, pub_closers])
#                    print("publisher", pub_value)
                self.fix("split_brackets", page, t, bad_params, "bracketed publisher and location individually")
                bad_params = []


            if bad_params:
                self.warn("bad_param", page, t, bad_params)

        if summary is None:
            return self._log

        if not summary:
            return page_text

        new_page_text = str(wiki)
        return new_page_text

