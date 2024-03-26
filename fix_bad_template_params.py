import copy
import csv
import enwiktionary_sectionparser as sectionparser
import re
import multiprocessing
import os
import sys
import mwparserfromhell as mwparser
import json
import urllib

from Levenshtein import distance
from autodooz.escape_template import escape, unescape


IGNORE_TEMPLATES = [
]

IGNORE_PER_TEMPLATE = {
}

REMOVE_GLOBAL = [ "lang" ]

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
    "R:ine:IEW": ["vol"],

    "cite-book": [ "editor-link", "editor2-link", "format", "accessyear", "url-status", "url-access", "doi-access", "type", "indent", "other", "asin", "work", "via", "ref", "website", "prefix", "lastauthoramp", "s2cid", "i2" ],
#    "R:TDK": ["lang"],
#    "RQ:Browne Hydriotaphia": { "3": "passage" },
#    "RQ:Maupassant Short Stories": {"story": "chapter"},
#    "RQ:Hooker Laws": {"section": "chapter"}
}

RENAME_PER_TEMPLATE = {

    # prefixing a parameter name with "=" allows renaming valid parameters, chose "=" because it can't possibly occurn in a valid param name
    "az-variant": { "=c": "1", "=a": "2" },
    #"cite-web": { "titel": "title", "website": "site", "urn": "url", "tilte": "title" },
    "cite-book": { "titel": "title", "place": "location", "city": "location", "first1": "first", "last1": "last", "author1": "author", "titel": "title", "pag": "page", "pge": "page", "edietor": "editor",
        "editor1": "editor",
        "archive-url": "archiveurl", "archive-date": "archivedate", "vol": "volume", "author-link": "authorlink", "p": "page", "publihser": "publisher", "edietor": "editor",
        "contributor": "author",
        "authorlink1": "authorlink",
        "authorurl": "authorlink",
        "contributors": "authors", "access_date": "accessdate",
        "coauthor": "author2",
        #"orig-date": "origdate",
        "publication-date": "date_published",
        "publication-place": "location",
        "OCoLC": "OCLC",
        "sbn": "isbn",
        "ed": "editor",
        "=trans": "translator", "=access-date": "accessdate", "=link": "pageurl", "head": "entry", "booklink": "url", "=book-link": "url", "=quote": "text"},
    "cite-journal": { "vol": "volume", "place": "location" },
#    "RQ:Browne Hydriotaphia": { "3": "passage" },
#    "RQ:Maupassant Short Stories": {"story": "chapter"},
#    "RQ:Hooker Laws": {"section": "chapter"}
}


# rename A -> B where A is a redirect to B
RENAME_REDIRECTS = {
    "R:tr:TDK"
}

def normalize_template_name(template_name):
    template_name = template_name.replace("_", " ")

    for prefix in ["T:", "Template:"]:
        if template_name.startswith(prefix):
            return template_name.removeprefix(prefix)

    return template_name

def clean_name(obj):
    text = re.sub(r"<!--.*?-->", "", unescape(str(obj.name)), flags=re.DOTALL)
    return text.strip()

def clean_value(obj):
    text = re.sub(r"<!--.*?-->", "", unescape(str(obj.value)), flags=re.DOTALL)
    return text.strip()

def escape_url(text):
    #if "?" not in text:
    #    return text

    return urllib.parse.quote(text, safe=':/?&;+%#,. ')

    #site, _, params = text.partition("?")
    #return site + "?" + urllib.parse.quote(params)


ALLOWED_MODULES = { "string", "ugly hacks", "italics", "checkparams" }
class ParamFixer():

    def __init__(self, template_data, redirects, allpages=None):
        self._summary = None
        self._log = []

        self._allpages = None
        if allpages:
            with open(allpages) as f:
                self._allpages = set(l.strip() for l in f)

        with open(template_data) as f:
            _template_data = json.load(f)
            self._templates = {k:v.get("params", []) for k,v in _template_data["templates"].items() if v["type"] in ["static", "wiki", "mixed"] and not set(v.get("modules", [])) - ALLOWED_MODULES }
#            self._templates |= {k:[] for k in ["suffix", "der", "der2", "der3", "der4", "rel2", "rel3", "rel4", "col-auto", "inflection of", "mention", "link", "taxon"] }
            print("LOADED", len(self._templates), "templates")

        with open(redirects) as infile:
            self._redirects = {x[0].removeprefix("Template:"):x[1].removeprefix("Template:") for x in csv.reader(infile, delimiter="\t") if x[0].startswith("Template:")}
            print("LOADED", len(self._redirects), "redirects")

        for template, replacements in RENAME_PER_TEMPLATE.items():
            if template not in self._templates:
                print(f"WARNING: RENAME_PER_TEMPLATE: {template}: is not a supported template name, ignoring")
                continue

            to_remove = []
            for old_name, new_name in replacements.items():
                if old_name in self._templates[template]:
                    print(f"WARNING: RENAME_PER_TEMPLATE: {template}: param {old_name} is a supported param name and will NOT be renamed")
                    to_remove.append(old_name)
                elif new_name not in self._templates[template]:
                    print(f"WARNING: RENAME_PER_TEMPLATE: {template}: param {new_name} is NOT a supported param name and will be ignored")
                    to_remove.append(old_name)

            for old_name in to_remove:
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

    def highlight_bad_params(self, template_orig, keys):

        template = copy.deepcopy(template_orig)

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
                p.name = "<BAD_POS>"
                p.showkey = True
            else:
                p.name = "<BAD>" + str(p.name)

            p.value = str(p.value) + "</BAD>"

        return str(template).replace("<BAD_POS>=", "<BAD>")


    def warn(self, code, page, template, keys=None):

        if self._summary is not None:
            print(code, page, clean_name(template), keys)
            return

        if isinstance(keys, str):
            keys = [keys]

        if isinstance(keys, list):
            key_str = ", ".join(keys)
            try:
                bad_text = unescape(self.highlight_bad_params(template, keys))
            except Exception as e:
                raise ValueError("mismatch", code, page, template, keys)
        else:
            assert keys == None
            key_str = keys
            bad_text = None

        t_name = clean_name(template)
        t_name = normalize_template_name(t_name)

        #print("WARN", (code, page, clean_name(template), key, details))
        self._log.append((code, page, t_name, key_str, unescape(str(template)), bad_text))

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

        #Thread:User talk:CodeCat/Wiktionary:Foreign Word of the Day/2012/October 13/reply (2)
        if page.startswith("Thread:"):
            return page_text if summary is not None else []

        if page in ["Appendix:Greek verbs/Ξ2", "Ἰωάννα", "Wiktionary:Grease pit/2007/April", "Template:ko-basic-verb2", "Template:ko-basic-embed", "Template:bg-decl-noun-old", "Template:outdent", "Wiktionary:Grease pit/2012/October"]:
            return page_text if summary is not None else []

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
            page_text = escape(page_text, escape_comments=False)

        wiki = mwparser.parse(page_text)
        to_replace_str = []

        count = 0
        #print("scanning", page)
        #print([clean_name(x) for x in wiki.ifilter_templates()])

        for t in wiki.ifilter_templates(recursive=True):

            t_name = clean_name(t)
            if t_name in ["PAGENAME", "=", "!", "CURRENTYEAR", "SUBPAGENAME", "SUBJECTSPACE", "BASEPAGENAME", "NAMESPACE"]:
                continue

            t_normal = normalize_template_name(t_name)
            if t_normal != t_name and self._allpages and "Template:" + t_normal in self._allpages:
                if ":" not in t_normal:
                    print(page, t_name, f"renamed template to {t_normal}")
                    self.fix("normalized", page, t, None, f"normalized template name to {t_normal}")
                    t.name = str(t.name).replace(t_name, t_normal)
                    continue

            t_name = t_normal

            if any(c in t_name for c in "{}"):
                self.warn("unparsable_template_name", page, t)
                continue

            if self._allpages and "Template:" + t_name not in self._allpages:
                self.warn("template_redlink", page, t)
                continue

            # resolve any redirects
            new_name = self._redirects.get(t_name, t_name)

            # Limit processing to templates with detected params
            if not new_name in self._templates:
                continue

            count += 1
            #print("scanning", t)

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


            allowed = self._templates.get(t_name, [])
            bad_params = []
            to_rename = []
            to_remove = []
            fixed_editors = False
            fixed_translators = False
            unused_empty_params = []
            can_remove_empty_positional = False
            for p in t.params:
                p_name = clean_name(p)
                p_value = clean_value(p)
                if p_name == "":  # {{code|=foo}} is the same as {{code|1=foo}}, used to allow constructs like {{code|=foo=bar}}
                    p_name = "1"


                if t_name == "cite-book" and p_name == "script-title":
                    if t.has("title"):
                        title_param = t.get("title")
                        to_rename.append((title_param, "trans-title"))
                    to_rename.append((p, "title"))
                    continue

                if t_name == "cite-book" and p_name == "title" and t.has("script-title"):
                    continue


                if t_name == "cite-book" and p_name in ["orig-year", "original year"]:
                    if t.has("year"):
                        year_param = t.get("year")
                        #print((clean_value(year_param), p_value))
                        #assert int(clean_value(year_param)) > int(p_value)
                        to_rename.append((year_param, "year_published"))
                    to_rename.append((p, "year"))
                    continue

                if t_name == "cite-book" and p_name == "year" and t.has("orig-year"):
                    continue

                if t_name in ["cite-book", "cite-journal", "cite-web"] and str(p.value).replace("<!--", "").replace("-->", "").strip() == "" and not p_name.isdigit():
                    to_remove.append(p)
                    continue

                if t_name == "cite-book" and p_name.startswith("editor") and "-" in p_name:
                    if fixed_editors:
                        to_remove.append(p)
                        continue

                    editors = []
                    for x in ["", "1", "2", "3", "4"]:
                        name = ""
                        if t.has(f"editor{x}-last"):
                            name = str(t.get(f"editor{x}-last").value).strip()

                        if t.has(f"editor{x}-first"):
                            if not name:
                                #print("BAD", t)
                                editors = []
                                break
                            name += ", " + str(t.get(f"editor{x}-first").value).strip()

                        if t.has(f"editor{x}-middle"):
                            assert ", " in name
                            name += " " + str(t.get(f"editor{x}-middle").value).strip()


                        if name:
                            #print("NAME MATCH1", name)
                            editors.append(name)

                        if x == "":
                            continue

                        name = ""
                        if t.has(f"editor-last{x}"):
                            name = str(t.get(f"editor-last{x}").value).strip()
                        if t.has(f"editor-first{x}"):
                            if not name:
                                #print("BAD first name without last name", t)
                                editors = []
                                break
                            name += ", " + str(t.get(f"editor-first{x}").value).strip()
                        if t.has(f"editor-middle{x}"):
                            assert ", " in name
                            name += " " + str(t.get(f"editor-middle{x}").value).strip()

                        if name:
                            #print("name match2", name)
                            editors.append(name)

                    if editors:
                        p.value = "; ".join(editors)
                        to_rename.append((p, "editor"))
                        fixed_editors = True
                        #print("fix", p_name, p.value)
                        self.fix("editors", page, t, p_name, f"merged various editor params into 'editor='")
                        continue

                if t_name == "cite-book" and p_name.startswith("translator") and "-" in p_name:
                    if fixed_translators:
                        to_remove.append(p)
                        continue

                    translators = []
                    for x in ["", "1", "2", "3", "4"]:
                        name = ""
                        if t.has(f"tranlator{x}-last"):
                            name = str(t.get(f"translator{x}-last").value).strip()

                        if t.has(f"translator{x}-first"):
                            if not name:
                                #print("BAD", t)
                                translators = []
                                break
                            name += ", " + str(t.get(f"translator{x}-first").value).strip()

                        if t.has(f"translator{x}-middle"):
                            assert ", " in name
                            name += " " + str(t.get(f"translator{x}-middle").value).strip()


                        if name:
                            #print("NAME MATCH1", name)
                            translators.append(name)

                        if x == "":
                            continue

                        name = ""
                        if t.has(f"translator-last{x}"):
                            name = str(t.get(f"translator-last{x}").value).strip()
                        if t.has(f"translator-first{x}"):
                            if not name:
                                #print("BAD first name without last name", t)
                                translators = []
                                break
                            name += ", " + str(t.get(f"translator-first{x}").value).strip()
                        if t.has(f"translator-middle{x}"):
                            assert ", " in name
                            name += " " + str(t.get(f"translator-middle{x}").value).strip()

                        if name:
                            #print("name match2", name)
                            translators.append(name)

                    if translators:
                        p.value = "; ".join(translators)
                        to_rename.append((p, "translator"))
                        fixed_translators = True
                        #print("fix", p_name, p.value)
                        self.fix("translators", page, t, p_name, f"merged various translator params into 'tranlator='")
                        continue


                # allow forcefully renaming/removing recognized params
                if p_name in allowed:

                    # Remove empty positional params
                    if can_remove_empty_positional and p_name.isdigit() and not p_value and not any(clean_name(x).isdigit() and int(clean_name(x)) > int(p_name) and str(x.value).strip() for x in t.params):
                        unused_empty_params.append(p)
                        continue

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
                    if any(c in p_name for c in """{}[]"'"""):
                        print("unparsable", page, p_name[:100])
                        self.warn("unparsable", page, t, p_name)
                        continue

                    if t_name == "cite-book" and p_name == "titel" and p_value == "Archived copy":
                        to_remove.append(p)

                    # Handle case mismatch
                    case_mismatch = [p for p in allowed if p.lower() == p_name.lower()]
                    if len(case_mismatch) == 1:
                        new_name = case_mismatch[0]
                        to_rename.append((p, new_name))
                        continue

                    # Handle unneeded "-"
                    sep_mismatch = [p for p in allowed if p == p_name.replace("-", "")]
                    if len(sep_mismatch) == 1:
                        new_name = sep_mismatch[0]
                        to_rename.append((p, new_name))
                        continue

                    # Handle typos
#                    typos = [p for p in allowed if p.isalpha() and p_name.isalpha() and (p.endswith("s") == p_name.endswith("s")) and len(p_name) >= 5 and distance(p, p_name) <= 1 ]
#                    if len(typos) == 1:
#                        new_name = typos[0]
#                        if not t.has(new_name) and not any(p_name.startswith(x) for x in ["no", "fpl"]) and not p_name in ["absnote", "volumes", "isbn"]:
#                            to_rename.append((p, new_name))
#                            continue

                    # handle positional params with urls containing "="
                    if re.match("http[s]?://", p_name) and clean_value(p) and " " not in clean_value(p):
                        old_str = str(p.name) + "=" + clean_value(p)
                        new_str = escape_url(old_str.strip())
                        to_replace_str.append((t, old_str, new_str))

                    elif p_name in REMOVE_PER_TEMPLATE.get(t_name, []):
                        to_remove.append(p)

                    elif not p_value:
                        # An empty numbered param N is only safe to remove if all other params >N are unhandled and empty
                        # use str(x.value).strip() instead of clean_name(x) to avoid removing params that contain only comments
                        #if p_name.isdigit() and any(clean_name(x).isdigit() and int(clean_name(x)) > int(p_name) and (clean_name(x) in allowed or str(x.value).strip()) for x in t.params):
                        if p_name.isdigit():
                            if any(clean_name(x).isdigit() and int(clean_name(x)) > int(p_name) and str(x.value).strip() for x in t.params):
                                self.warn("bad_pos_param", page, t, p_name)
                                continue
                            can_remove_empty_positional = True

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
                        #print("BAD", t_name, p_name, p_value)
                        bad_params.append(p_name)

            for p, new_name in to_rename:
                old_name = clean_name(p)
                p.name = new_name
                p.showkey = not p.name.isdigit()
                if not fixed_editors and not fixed_translators:
                    self.fix("misnamed_param", page, t, p_name, f"renamed param '{old_name}' to '{new_name}'")

            # only remove empty params if all param names look valid
            if all(len(clean_name(p)) < 12 and re.match(r"([1-9]|1[0-9]|[A-Za-z]+([_-][a-zA-Z]+)?[1-9]?)$", clean_name(p)) for p in unused_empty_params):
                for p in unused_empty_params:
                    p_name = clean_name(p)
                    self.fix("empty_param", page, t, p_name, f"removed empty param '{p_name}'")
                    t.remove(p)
            else:
                bad_params += [clean_name(p) for p in unused_empty_params]

            if to_remove:
                for p in to_remove:
                    p_name = clean_name(p)
                    t.remove(p)

                if not fixed_editors and not fixed_translators:
                    if len(to_remove) == 1:
                        self.fix("bad_param", page, t, p_name, f"removed unused param '{p_name}'")
                    else:
                        self.fix("bad_param", page, t, p_name, f"""removed unused params '{"', '".join(clean_name(p) for p in to_remove)}'""")

            if bad_params:
                self.warn("bad_param", page, t, bad_params)

        new_page_text = str(wiki)

        for t_name, old_str, new_str in to_replace_str:
            self.fix("unescaped_url", page, t_name, None, f"escaped url containing = in a positional param")
            new_page_text = new_page_text.replace(old_str, new_str)

        if summary is None:
            return count, self._log

        return unescape(new_page_text)

