#!/usr/bin/python3

import enwiktionary_sectionparser as sectionparser
import re
import sqlite3
import requests
import json
import urllib.parse
import mwparserfromhell as mwparser

import pywikibot
from pywikibot.comms import http
site = None

# Templates that might generate <ref>s when called with given params
conditional_ref_templates = {
    # Template    re_paramname   re_inline_modifier
    "ja-acc-multi":  (r".*_ref", ),
    "ja-pron":  (r".*_ref", ),
    "ryu-pron": (r".*_ref", ),
    "ja-IPA":   (r".*_ref", ),
    "fr-IPA":   (r"n\d*", "n" ),
    "af":       (r"ref\d*",     "ref" ),
    "col":      (r"ref\d*",     "ref" ),
    "IPA":      (r"ref\d*",     "ref" ),
    "IPAchar":  (r"ref\d*",     "ref" ),
    "inh+":     (r"ref\d*",     "ref" ),
    "uder":     (r"ref\d*",     "ref" ),
    "syn":      (r"ref\d*",     "ref" ),
    "audio":    (r"ref\d*",     "ref" ),
    "etydate":  (r"ref[n]?\d*", ),
    "defdate":  (r"ref[n]?\d*", ),
    "etymon":   (None,          "ref" ),

    "ja-kanji forms-IVS":   ("ref", ),
    "smn-.*":   ("ref", ),
    "it-noun":   ("ref", "ref" ),
    #"ux":   ("ref", ),
    "archaic form of":   ("ref", ),
    "[a-z]+-(IPA|pr)":      (r"ref\d*",     "(ref|r)" ),
}

PATTERN_CONDITIONAL_REFS = r"\{\{\s*(" + "|".join([k for k in conditional_ref_templates]) + r")\s*[|}]"

maybe_ref_templates = [ "vi-readings", "it-verb-rfc", "it-verb", "desctree", "ki-tonal classes"]
PATTERN_MAYBE_REFS = r"\{\{\s*(" + "|".join(maybe_ref_templates) + r")\s*[|}]"

# Templates that always generate a <ref> link
always_ref_templates = ["U:de:separated", "U:la:month", "U:la:distributive numeral", "U:hu:stimulus-subject verbs", "U:de:unadapted", "ref", "refn", "U:en:illegal person",
                        "U:en:HM and HMG", "U:hu:purpose-solid", "U:hu:unmarked possessive not written as solid", "hu-ref-semivowel", "ux:tpw:Barbosa 1956", "U:mi:cardinal directions",
                        "U:de:Du", "U:de:dass", "U:la:month", "pl-freq 1990", "ryu-OG", "RQ:Pyramid Texts", "U:hu:abbrev-full-last", "U:hu:abbrev-full-last", "sia-infl-dem",
                        "sia-infl-dem", "yi-infl-note", "ajp-usg-Ci-Cu", "U:Nkoo:RTL digits", "Khaisan letters", "U:de:-ed participle" ]
PATTERN_ALWAYS_REFS = r"\{\{\s*(" + "|".join(always_ref_templates) + r")\s*[|}]"


def generates_references(text):
    # returns 0 if text NEVER generates references
    # 1 if text MAYBE generates references
    # 2 if text DEFINITELY generates references

    if re.search(r"<ref(\s|>)", text, flags=re.IGNORECASE):
        #print("has <ref>")
        return 2

    m = re.search(PATTERN_ALWAYS_REFS, text, flags=re.DOTALL)
    if m:
        #print("MATCH", m.group(0))
        return 2

    m = re.search(PATTERN_CONDITIONAL_REFS, text, flags=re.DOTALL)
    if m:
        wiki = mwparser.parse(text)
        for t in wiki.ifilter_templates():
            name = str(t.name).strip()
            for k, v in conditional_ref_templates.items():
                if k == name or re.match(f"^{k}$", name):
                    param_re = v[0]
                    inline_re = v[1] if len(v) > 1 else None
                    # conditional template, check for params that match
                    for p in t.params:
                        if param_re and re.match(f"^{param_re}$", str(p.name).strip()) and str(p.value).strip():
                            #print("PARAM MATCH", t, [p])
                            return 2
                        elif inline_re and re.search(f"<({inline_re}):", str(p.value)):
                            #print("INLINE MATCH", t, [p])
                            return 2

    m = re.search(PATTERN_MAYBE_REFS, text, flags=re.DOTALL)
    if m:
        #print("MATCH", m.group(0))
        return 1

    return 0


# Tags that generate <references/>
PATTERN_REFS = r"(?i)(<\s*references|{{\s*reflist|{{\s*references)"
def is_reference(line):
    return bool(re.match(PATTERN_REFS, line))

def shows_references(text):
    return bool(re.search(PATTERN_REFS, text))


# Set up the SQLite database connection
def setup_database(db_name='wiki_cache.db'):
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS wiki_to_html (wiki TEXT PRIMARY KEY, html TEXT)")
    conn.commit()
    return conn

def expand_templates(section):
    global site
    if not site:
        site = pywikibot.Site("en", "wiktionary")

    pagename = section.page

    text = str(section)
    text = re.sub("<!--.*?-->", "", text, flags=re.DOTALL).strip()

    # Connect to the database
    conn = setup_database()
    cur = conn.cursor()

    # Check for cached results
    cur.execute('SELECT html FROM wiki_to_html WHERE wiki=?', (text,))
    result = cur.fetchone()

    if result:
        # Return cached wikitext
        conn.close()
        return result[0]


    # If not found in cache, query the Wikimedia API
    params = {
        'action': 'expandtemplates',
        'prop': 'wikitext',
        'text': text, #urllib.parse.quote(text),
        'format': 'json'
    }
    path = "{}/api.php".format(site.scriptpath())
    if len(text) > 7000:
        print("long text", len(text))
        return None

    response = http.request(site, path, params=params)
    print(path, section.page, section.path, len(response.text))

    if response.status_code != 200:
        conn.close()
        print("failed to expand templates", len(text))
        return None
        raise Exception("Error fetching data from Wikimedia API")

    data = response.json()
    if 'expandtemplates' not in data:
        conn.close()
        raise Exception("Templates not expanded")

    # Extract wikitext from the API response
    data = json.loads(response.text)
    html = data["expandtemplates"]["wikitext"]

    # Store the newly fetched data in the database
    cur.execute('INSERT INTO wiki_to_html (wiki, html) VALUES (?, ?)', (text, html))
    conn.commit()
    conn.close()

    return html


def get_page_html(pagename):
    global site
    if not site:
        site = pywikibot.Site("en", "wiktionary")

    page = pywikibot.Page(site, pagename)

    if not page.exists():
        return ""

    path = '{}/index.php?title={}'.format(site.scriptpath(), page.title(as_url=True))
    r = http.request(site, path)

    print(pagename, path, len(r.text))

    return r.text

def has_references(html):
    return '<div class="mw-references-wrap">' in html


class ReferenceFixer():

    def __init__(self):
        # Only used when calling functions directly during unit testing
        # all other uses should just call process() which will set these variables
        self._summary = None
        self._log = []
        self.page_title = "test"

    def remove_ref(self, section):

        refs = section.filter_sections(matches="References")
        if not len(refs) == 1:
            self.warn("multi_refs", section.path)
            return

        ref = refs[0]
        new_wikilines = [l for l in ref.content_wikilines if not is_reference(l)]

        if not new_wikilines:
            self.fix("remove_ref_section", ref, f"removed empty References section")
            ref.parent._children.remove(ref)
            return True

        elif new_wikilines and len(new_wikilines) != len(ref.content_wikilines):
            ref.content_wikilines = new_wikilines
            self.fix("remove_ref_line", ref, f"removed unneeded <references/> tag")
            return True


    def cleanup_references(self, entry):

        all_l2 = entry.filter_sections(recursive=False)
        for section in all_l2:

            text = str(section)
            text = re.sub("<!--.*?-->", "", text, flags=re.DOTALL)

            uses_refs = generates_references(text)
            displays_refs = shows_references(text)

            if displays_refs and not uses_refs:

                if self._summary is None:
                    self.warn("check_ref", section.path)
                else:

                    html = get_page_html(section.page)
                    if not has_references(html):
                        self.remove_ref(section)

                    else:
                        if len(all_l2) == 1:
                            print("NEEDS REF", section.page)
                            self.warn("needed_ref", section.path)
                        else:
                            wiki = expand_templates(section)
                            if wiki is not None:
                                # if the expanded templates include <ref>, the there should be a references section
                                if re.search(r"<ref(\s|>)", wiki, flags=re.IGNORECASE):
                                    print("SECTION NEEDS REF", section.page, section.path)
                                    self.warn("multi_needed_ref", section.path)
                                else:
                                    self.remove_ref(section)

            elif uses_refs == 2 and not displays_refs:
                #print("USES REFS", uses_refs.group(0))
                ref_section = next(section.ifilter_sections(matches="References"), None)
                if ref_section:
                    ref_section.content_wikilines.insert(0, "<references/>")
                    self.fix("missing_ref_target", ref_section, "added missing <references/>")
                    continue

                new_section = sectionparser.Section(entry, 3, "References")
                new_section.add("<references/>")

                # Anagrams is always the last section, otherwise References is the last
                if section._children and section._children[-1].title == "Anagrams":
                    section._children.insert(-1, new_section)
                else:
                    section._children.append(new_section)

                self.fix("missing_ref_section", section, "added References section")

    def split_bulky_references(self, entry):
        """
        EXPERIMENTAL: Move everything except <references/> from the References section to Further reading
        Not safe to run generally """
        for section in entry.ifilter_sections(matches = lambda x: x.title == "References"):
            moved_idx = []
            for idx, wikiline in enumerate(section.content_wikilines):
                if not re.match(PATTERN_REFS, wikiline.strip(" #:*")):
                    moved_idx.append(idx)

            if not moved_idx:
                continue

            moved_wikilines = []
            for idx in reversed(moved_idx):
                moved_wikilines.insert(0, section.content_wikilines.pop(idx))

            existing_section = next(section.parent.ifilter_sections(matches = lambda x: x.title == "Further reading"), None)
            if existing_section:
                self.fix("moved_further_reading", section, "moved non-footnotes to Further reading")
                for line in moved_wikilines:
                    if line not in existing_section.content_wikilines:
                        existing_section.content_wikilines.append(line)

            else:
                self.fix("split_further_reading", section, "split non-footnotes to Further reading")
                new_section = sectionparser.Section(section.parent, section.level, "Further reading")
                new_section.content_wikilines = moved_wikilines
                section.parent._children.append(new_section)

    def fix(self, code, section, details):

        if isinstance(section, sectionparser.SectionParser):
            page = section.page
            path = ""
            target = page
        else:
            page = section.page
            path = section.path

        if self._summary is not None:
            if path:
                self._summary.append(f"/*{path}*/ {details}")
            else:
                self._summary.append(f"{details}")

        self._log.append(("autofix_" + code, page, path, details))

    def warn(self, code, section, details=None):
        self._log.append((code, self.page_title, section, details))

    def process(self, page_text, page_title, summary=None, options=None):

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

        self.page_title = page_title

        if ":" in page_title or "/" in page_title:
            return page_text if summary is not None else self._log

        entry = sectionparser.parse(page_text, page_title)
        if not entry:
            return page_text if summary is not None else self._log

        self.cleanup_references(entry)

        return str(entry) if summary is not None else self._log
