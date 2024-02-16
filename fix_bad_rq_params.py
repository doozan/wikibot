import enwiktionary_sectionparser as sectionparser
import re
import multiprocessing
import os
import sys
import mwparserfromhell as mwparser
import json


IGNORE_TEMPLATES = [
    "RQ:Paul.Fest.",
    "RQ:Fitzgerald Beautiful and Damned",
    "RQ:Johnson History of the Pyrates",
    "RQ:Chapman Works",
    "RQ:Ruskin Modern Painters",
    "RQ:Acevedo Díaz Ismael",
    "RQ:it:Commedia",
    "RQ:Coryat Crudities",
    "RQ:Zweig Schachnovelle",
    "RQ:Milton Of Reformation",
    "RQ:pl:Calep",
    "RQ:Dryden Astraea Redux",
    "RQ:Cervantes Don Quijote I",
    "RQ:zlw-opl:DłKlejn",
    "RQ:McCarthy Blood Meridian",
    "RQ:Galdós Fortunata y Jacinta",
    "RQ:Bulwer-Lytton Pelham",
    "RQ:交隣須知",
    "RQ:Wodehouse Summer Lightning",
    "RQ:zhx-teo:Fielde Dictionary",
]

RENAME = {
    "footnote": "footer",
    "txt": "text",
    "chapoter": "chapter",
    "chapoter": "chapter",
    "chaper": "chapter",
    "line": "stanza",
    "lines": "stanzas",
    "quote": "passage",
    "passager": "passage",
    "pasasge": "passage",
    "pgae": "page",
    "voume": "volume",
    "pageurl": "pageref",
}

RENAME_PER_TEMPLATE = {
    "RQ:Browne Hydriotaphia": { "3": "passage" },
    "RQ:Maupassant Short Stories": {"story": "chapter"},
    "RQ:Hooker Laws": {"section": "chapter"}
}


class RqParamFixer():

    def __init__(self, template_data):
        self._summary = None
        self._log = []

        with open(template_data) as f:
            self._templates = json.load(f)


    def fix(self, code, page, template, key, details):
        key = str(key)

        if self._summary is not None:
            self._summary.append(f"{template.name.strip()}: {details}")

        m = re.search("[|]\s*" + re.escape(str(template.get(key))), str(template))
        if not m:
            raise ValueError("no match")
        bad_text = m.group(0)

        self._log.append(("autofix_" + code, page, template.name.strip(), key.strip(), details, str(template), bad_text))

    def warn(self, code, page, template, key, details=None):
        key = str(key)
        m = re.search("[|]\s*" + re.escape(str(template.get(key))), str(template))
        if not m:
            raise ValueError("no match")
        bad_data = m.group(0)

        #print("WARN", (code, page, template.name.strip(), key, details))
        self._log.append((code, page, template.name.strip(), key.strip(), details, str(template), bad_data))

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

        wiki = mwparser.parse(page_text)

        for t in wiki.ifilter_templates(recursive=False, matches=lambda x: x.name.strip() in self._templates):

            # skip manually adjusted templates
            if t.name.strip() in IGNORE_TEMPLATES:
                continue

            allowed = self._templates[t.name.strip()]
            for p in t.params:
#                print("CHECKING", p.name.strip(), allowed)
                if p.name.strip() not in allowed:

                    # Handle case sensitive
                    if p.name.strip().lower() in allowed:
                        old_name = p.name.strip()
                        new_name = old_name.lower()
                        p.name = p.name.lower()
                        self.fix("misnamed_param", page, t, p.name, f"renamed param '{old_name}' to '{new_name}'")

                    elif not p.value.strip():
                        if p.name.strip().isdigit() and any(x.name.strip().isdigit() and int(x.name.strip()) > int(p.name.strip()) for x in t.params):
                            self.warn("bad_pos_param", page, t, p.name)
                            continue

                        self.fix("bad_param", page, t, p.name, f"removed unused empty param '{p.name.strip()}'")
                        t.remove(p)

                    elif p.name.strip() in RENAME and RENAME[p.name.strip()] in allowed:
                        old_name = p.name.strip()
                        new_name = RENAME[p.name.strip()]
                        self.fix("misnamed_param", page, t, p.name, f"renamed param '{old_name}' to '{new_name}'")
                        p.name = new_name
                        p.show_key = True

                    elif str(t.name.strip()) in RENAME_PER_TEMPLATE and p.name.strip() in RENAME_PER_TEMPLATE[t.name.strip()]:
                        old_name = p.name.strip()
                        new_name = RENAME_PER_TEMPLATE[t.name.strip()][old_name]
                        self.fix("misnamed_param", page, t, p.name, f"renamed param '{old_name}' to '{new_name}'")
                        p.name = new_name
                        p.showkey = True
                        print("RENAMED", p, [new_name, page])

                    elif "Swift Gulliver" in str(t.name) and p.name.strip() == "2":
                        if t.has("3") and t.has("page"):
                            self.fix("bad_param", page, t, p.name, f"removed unused params '{p.name.strip()}' and '3'")
                            t.remove("3")
                        elif t.has("3"):
                            self.fix("bad_param", page, t, p.name, f"removed unused param '{p.name.strip()}', renamed param '3' to 'page'")
                            t.get("3").name = "page"
                        else:
                            self.fix("bad_param", page, t, p.name, f"removed unused param '{p.name.strip()}'")
                        t.remove(p)

                    elif p.name.strip() in ["url", "format", "year", "chapter", "book", "author", "title", "pageurl", "edition"]:
                        self.fix("bad_param", page, t, p.name, f"removed unused param '{p.name.strip()}'")
                        t.remove(p)

                    else:
                        self.warn("bad_param", page, t, p.name)

        if summary is None:
            return self._log

        return str(wiki)
