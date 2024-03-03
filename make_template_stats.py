#!/usr/bin/python3

import argparse
import csv
import json
import os
import re
import sys

from collections import defaultdict, namedtuple

# https://www.mediawiki.org/wiki/Help:Magic_words
MAGIC_WORDS = [ "FULLPAGENAME", "PAGENAME", "BASEPAGENAME", "NAMESPACE", "!", "SUBPAGENAME", "lc:", "fullurl:" ]

def main():
    parser = argparse.ArgumentParser(description="Find errors in sense lists")
    parser.add_argument("json", help="template data")
    parser.add_argument("tsv", help="template count")
    parser.add_argument("outfile", help="target for combined json data")
    args = parser.parse_args()

    _counts = namedtuple("counts", [ "uses", "pages" ])

    with open(args.tsv) as infile:
        template_count = {x[0]:_counts(int(x[1]), int(x[2])) for x in csv.reader(infile, delimiter="\t")}

    with open(args.json) as infile:
        template_data = json.load(infile)
        templates = template_data["templates"]
        redirects = template_data["redirects"]

    lua_templates = set()
    mixed_templates = set()
    wiki_templates = set()
    static_templates = set()
    maybe_mixed_templates = set()

    # First pass:
    #   add counts
    #   detect all Lua template
    #   detect all static templates
    #   detect obvious mixed templates
    #   detect obvious wiki templates
    for template, data in templates.items():
        data["count"] = template_count[template].uses if template in template_count else 0
        data["page_count"] = template_count[template].pages if template in template_count else 0
        if "params" not in data and "templates" not in data:
            modules = data.get("modules", [])
            if not modules:
                static_templates.add(template)
            elif len(data.get("modules", [])) == 1:
                lua_templates.add(template)
            else:
                mixed_templates.add(template)

        elif "templates" in data and "modules" in data:
            mixed_templates.add(template)

        elif "templates" not in data:

            if "modules" not in data:
                wiki_templates.add(template)
            else:
                mixed_templates.add(template)

        else:
            maybe_mixed_templates.add(template)

    # multiple passess, detect mixed templates that call other mixed templates
    found = True
    while found:
        found = set()
        for template in maybe_mixed_templates:
            for i in templates[template]["templates"]:
                i = redirects.get(i, i)
                if i in mixed_templates:
                    found.add(template)

        for template in found:
            mixed_templates.add(template)
            maybe_mixed_templates.remove(template)

    wiki_templates |= maybe_mixed_templates

    for flag, items in [
        ("lua", lua_templates),
        ("mixed", mixed_templates),
        ("wiki", wiki_templates),
        ("static", static_templates),
    ]:
        for template in items:
            templates[template]["type"] = flag

    with open(args.outfile, 'w', encoding='utf-8') as outfile:
        json.dump({
            "templates": templates,
            "redirects": redirects,
            }, outfile, ensure_ascii=False, indent=4)



    def print_header(range):
        print(f"""\
===Templates with {range} uses===
<div class="NavFrame">
<div class="NavHead" style="text-align: left;">Templates with {range} uses</div>
<div class="NavContent derivedterms" style="text-align: left;">

{{| class="wikitable sortable"
|-
!Template!!type!!count!!pages!!modules included!!templates invoked""")

    def print_footer():
        print("|}")
        print("</div></div>")

    def get_included_templates(template, ignore=[]):
        included = [redirects.get(t, t) for t in templates.get(template, {}).get("templates", [])]
        child_included = []

        for child in included:
            child = redirects.get(child, child)
            if child not in ignore and child not in child_included:
                child_included += get_included_templates(child, ignore+included+child_included)
        return included + child_included

    print(f"; {len(templates):,} total templates")
    min_count = 100000
    print_header(f">{min_count:,}")
    for template, data in sorted(templates.items(), key=lambda x: (x[1]["count"]*-1, x[0])):
        count = data['count']
        included_templates = sorted(set(get_included_templates(template)))
        included_modules = sorted(set(templates.get(template).get("modules", []) + [m for t in included_templates for m in templates.get(t,{}).get("modules", [])]))

        if count < min_count:
            if min_count > 1:
                prev_min_count = min_count
                if min_count <= 4:
                    break
                if min_count==1000:
                    min_count = 512
                elif min_count <= 512:
                    min_count = int(min_count/2)
                else:
                    min_count = int(min_count/10)
                title = f"{min_count:,}-{prev_min_count:,}"
            else:
                min_count = 0
                title = 0

            print_footer()
            print_header(title)

        print("|-")
        space = " " if template[0] in "|-+" else ""
        print(f"|{space}{template}||{data['type']}||{data['count']:,}||{data['page_count']:,}||{'; '.join(included_modules)}||{'; '.join(included_templates)}")

    print_footer()

if __name__ == "__main__":
    main()
