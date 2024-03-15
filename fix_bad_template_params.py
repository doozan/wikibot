import enwiktionary_sectionparser as sectionparser
import re
import multiprocessing
import os
import sys
import mwparserfromhell as mwparser
import json
import urllib


from autodooz.fix_rq_template import escape, unescape


IGNORE_TEMPLATES = [
]

IGNORE_PER_TEMPLATE = {
}

REMOVE_PER_TEMPLATE = {
    "az-variant": [ "r", "l" ],
    "en-symbol": [ "1" ],
    "en-det": [ "1" ],
    "en-part": [ "1" ],
    "en-prep": [ "1" ],
    "en-symbol": [ "1" ],
    "en-letter": [ "1", "upper", "lower" ],
    "vern": [ "pedia" ],
    "R:tr:TDK": [ "lang" ],
    "ws header": [ "lang" ],
    "Navbox": [ "listalign", "lisalign", "listclass" ],
    "BCE": [ "nodots" ],
    "B.C.E.": [ "dots" ],
    "CE": [ "nodots" ],
    "C.E.": [ "dots" ],
    "Latn-def-lite": [ "nocap" ],
    "list helper 2": [ "lang" ],

#    "cite-book": [ "accessyear", "accessmonth" ],
#    "R:TDK": ["lang"],
#    "RQ:Browne Hydriotaphia": { "3": "passage" },
#    "RQ:Maupassant Short Stories": {"story": "chapter"},
#    "RQ:Hooker Laws": {"section": "chapter"}
}

RENAME_PER_TEMPLATE = {

    # prefixing a parameter name with "=" allows renaming valid parameters, chose "=" because it can't possibly occurn in a valid param name
    "az-variant": { "=c": "1", "=a": "2" },
    "cite-web": { "titel": "title", "website": "site", "urn": "url", "tilte": "title" },
    "cite-book": { "titel": "title" },
    "cite-journal": { "vol": "volume", "place": "location" },
#    "RQ:Browne Hydriotaphia": { "3": "passage" },
#    "RQ:Maupassant Short Stories": {"story": "chapter"},
#    "RQ:Hooker Laws": {"section": "chapter"}
}


# rename A -> B where A is a redirect to B
RENAME_REDIRECTS = {
    "R:tr:TDK"
}


def clean_name(obj):
    text = re.sub(r"<!--.*?-->", "", unescape(str(obj.name)), flags=re.DOTALL)
    return text.strip()

def clean_value(obj):
    text = re.sub(r"<!--.*?-->", "", unescape(str(obj.value)), flags=re.DOTALL)
    return text.strip()

def escape_url(text):
    if "?" not in text:
        return text

    return urllib.parse.quote(text, safe=':/?&;+%')

    #site, _, params = text.partition("?")
    #return site + "?" + urllib.parse.quote(params)


ALLOWED_MODULES = { "string", "ugly hacks", "italics" }
class ParamFixer():

    def __init__(self, template_data):
        self._summary = None
        self._log = []

        with open(template_data) as f:
            _template_data = json.load(f)
            self._templates = {k:v.get("params", []) for k,v in _template_data["templates"].items() if v["type"] in ["static", "wiki", "mixed"] and not set(v.get("modules", [])) - ALLOWED_MODULES }
            self._redirects = _template_data["redirects"]
            print("LOADED", len(self._templates))

        for template, replacements in RENAME_PER_TEMPLATE.items():
            if template not in self._templates:
                print(f"WARNING: RENAME_PER_TEMPLATE: {template}: is not a supported template name, ignoring")
                continue

            for old_name, new_name in replacements.items():
                if old_name in self._templates[template]:
                    print(f"WARNING: RENAME_PER_TEMPLATE: {template}: param {old_name} is a supported param name and will NOT be renamed")
                    del replacements[old_name]
                elif new_name not in self._templates[template]:
                    print(f"WARNING: RENAME_PER_TEMPLATE: {template}: param {new_name} is NOT a supported param name and will be ignored")
                    del replacements[old_name]


    def fix(self, code, page, template, keys, details):

        if isinstance(keys, str):
            keys = [keys]

        # report-mode
        if self._summary is None:
            #if keys:
            #    self.highlight_bad_params(template, keys)
            #    bad_text = str(template).replace("<BAD>=", "<BAD>")
            #    key_str = ", ".join(keys)
            #else:
            #    bad_text = None
            #    key_str = None

            #self._log.append(("autofix_" + code, page, clean_name(template), key_str, details, bad_text))
            self._log.append(("autofix_" + code, page, clean_name(template), None, details, None))

        # fix-mode
        else:
            msg = f"{clean_name(template)}: {details}"
            if msg not in self._summary:
                self._summary.append(msg)

    def highlight_bad_params(self, template, keys):

        bad_params = []
        for p in template.params:
            p_name = clean_name(p)
            if p_name == "":
                p_name = "1"
            if p_name in keys:
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



    def warn(self, code, page, template, keys):

        if self._summary is not None:
            print(code, page, clean_name(template), keys)
            return

        if isinstance(keys, str):
            keys = [keys]

        template_str = unescape(str(template))
        #template_str = str(template)

        self.highlight_bad_params(template, keys)

        # fix for numbered parameters that become named parameters
        bad_text = unescape(str(template).replace("<BAD>=", "<BAD>"))
        #bad_text = str(template).replace("<BAD>=", "<BAD>")
        key_str = ", ".join(keys)

        #print("WARN", (code, page, clean_name(template), key, details))
        self._log.append((code, page, clean_name(template), key_str, template_str, bad_text))

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

        if "{{" not in page_text:
            return page_text if summary is not None else []

        if "{{{" in page_text or "{{#" in page_text:
            # Don't treat pages that already contain the 'escape' characters
            if unescape(page_text) != page_text:
                print(page, "uses escape char")
                # TODO: Log these, or use better escape chars
                # as of 2024-03-01, only happens on a handful of pages, all discussions that start Wiktionary: plus "Template:R:cu:Sin:psal"
                if summary is None:
                    return 0, self._log
                return page_text
            page_text = escape(page_text)



        wiki = mwparser.parse(page_text)
        to_replace_str = []

        count = 0
        for t in wiki.ifilter_templates(recursive=True, matches=lambda x: self._redirects.get(clean_name(x), clean_name(x)) in self._templates):
            count += 1

            t_name = clean_name(t)
            # resolve any redirects
            new_name = self._redirects.get(t_name, t_name)

            # Rename redirects to use direct template name
            if new_name != t_name:
                if new_name in RENAME_REDIRECTS:
                    self.fix("renamed_redirect", page, t, None, f"renamed template to {new_name}")
                    t.name = new_name
                t_name = new_name

            # skip manually adjusted templates
            if t_name in IGNORE_TEMPLATES:
                continue

#            if t_name == "cite-book":
#                if t.has("lang") or t.has(1) and re.match(r"^([a-z][a-z]|[a-z][a-z][a-z])$", str(t.get(1).value)):
#                    pass
#                elif "{{lang" in str(t):
#                    pass
#                elif "English:" in page:
#                    pass
#                else:
#                    tid = "X" #page.split(":")[-1].rstrip("_")
#                    if t.has("title"):
#                        tid += "::" + str(t.get("title").value)
#                    self.fix("missing_lang", page, t, "lang", f"missing lang :: {tid}")


            allowed = self._templates[t_name]
            bad_params = []
            to_rename = []
            to_remove = []
            unused_empty_params = []
            for p in t.params:
                p_name = clean_name(p)
                p_value = clean_value(p)
                if p_name == "":  # {{code|=foo}} is the same as {{code|1=foo}}, used to allow constructs like {{code|=foo=bar}}
                    p_name = "1"

                # Allow forcefully renaming/removing recognized params
                if p_name in allowed:

                    forced_p_name = "=" + p_name
                    if RENAME_PER_TEMPLATE.get(t_name, {}).get(forced_p_name):
                        new_name = RENAME_PER_TEMPLATE[t_name][forced_p_name]
                        if t.has(new_name):
                            continue
                        to_rename.append((p, new_name))

                    elif forced_p_name in REMOVE_PER_TEMPLATE.get(t_name, []):
                        to_remove.append(p)

                # Handle unrecognized parameters
                else:
                    # Handle case mismatch
                    case_mismatch = [p for p in allowed if p.lower() == p_name.lower()]
                    if case_mismatch and len(case_mismatch) == 1:
                        new_name = case_mismatch[0]
                        to_rename.append((p, new_name))

                    # handle positional params with urls containing "="
                    elif re.match("http[s]?://", p_name) and clean_value(p) and " " not in clean_value(p):
                        old_str = str(p.name) + "=" + clean_value(p)
                        new_str = escape_url(old_str.strip())
                        to_replace_str.append((t, old_str, new_str))

                    elif p_name in REMOVE_PER_TEMPLATE.get(t_name, []):
                        to_remove.append(p)

                    elif not p_value:
                        # An empty numbered param N is only safe to remove if all other params >N are unhandled and empty
                        # use str(x.value).strip() instead of clean_name(x) to avoid removing params that contain only comments
                        if p_name.isdigit() and any(clean_name(x).isdigit() and int(clean_name(x)) > int(p_name) and (clean_name(x) in allowed or str(x.value).strip()) for x in t.params):
                            self.warn("bad_pos_param", page, t, p_name)
                            continue

                        unused_empty_params.append(p)

                    elif RENAME_PER_TEMPLATE.get(t_name, {}).get(p_name):
                        new_name = RENAME_PER_TEMPLATE[t_name][p_name]
                        if t.has(new_name):
                            continue
                        to_rename.append((p, new_name))

#                    elif p_name in ["url", "format", "year", "chapter", "book", "author", "title", "pageurl", "edition"]:
#                        self.fix("bad_param", page, t, p_name, f"removed unused param '{p_name}'")
#                        t.remove(p)

                    elif p_name in IGNORE_PER_TEMPLATE.get(t_name, []):
                        continue

                    else:
                        bad_params.append(p_name)

            for p, new_name in to_rename:
                old_name = clean_name(p)
                p.name = new_name
                p.showkey = not p.name.isdigit()
                self.fix("misnamed_param", page, t, p_name, f"renamed param '{old_name}' to '{new_name}'")

            # only remove empty params if all param names look valid
            if all(len(clean_name(p)) < 12 and re.match(r"([1-9]|1[0-9]|[A-Za-z]+([_-][a-zA-Z]+)?[1-9]?)$", clean_name(p)) for p in unused_empty_params):
                for p in unused_empty_params:
                    p_name = clean_name(p)
                    self.fix("bad_param", page, t, p_name, f"removed unused empty param '{p_name}'")
                    t.remove(p)
            else:
                bad_params += [clean_name(p) for p in unused_empty_params]

            if to_remove:
                for p in to_remove:
                    p_name = clean_name(p)
                    self.fix("bad_param", page, t, p_name, f"removed unused param '{p_name}'")
                    t.remove(p)

            if bad_params:
                self.warn("bad_param", page, t, bad_params)

        new_page_text = str(wiki)

        for t_name, old_str, new_str in to_replace_str:
            self.fix("unescaped_url", page, t_name, None, f"escaped url containing = in a positional param")
            new_page_text = new_page_text.replace(old_str, new_str)

        if summary is None:
            return count, self._log

        return unescape(new_page_text)

