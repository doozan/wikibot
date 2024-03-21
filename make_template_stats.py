#!/usr/bin/python3

import argparse
import csv
import json
import os
import re
import sys

from collections import defaultdict, namedtuple

def main():
    parser = argparse.ArgumentParser(description="Find errors in sense lists")
    parser.add_argument("--count", help="TSV with template count", required=True)
    parser.add_argument("--modules", help="module data", required=True)
    parser.add_argument("--templates", help="JSON with template data", required=True)
    parser.add_argument("--redirects", help="TSV with redirect data", required=True)
    args = parser.parse_args()

    _counts = namedtuple("counts", [ "uses", "pages" ])

    with open(args.count) as infile:
        template_count = {x[0]:_counts(int(x[1]), int(x[2])) for x in csv.reader(infile, delimiter="\t")}

    with open(args.templates) as infile:
        template_data = json.load(infile)
        templates = template_data["templates"]

    with open(args.redirects) as infile:
        redirects = {x[0].removeprefix("Template:"):x[1].removeprefix("Template:") for x in csv.reader(infile, delimiter="\t") if x[0].startswith("Template:")}

    with open(args.modules) as infile:
        module_data = json.load(infile)
        modules = module_data["modules"]

    with open(args.redirects) as infile:
        module_redirects = {x[0].removeprefix("Module:"):x[1].removeprefix("Module:") for x in csv.reader(infile, delimiter="\t") if x[0].startswith("Module:")}

    for template, template_data in templates.items():
        template_data["count"] = template_count[template].uses if template in template_count else 0
        template_data["page_count"] = template_count[template].pages if template in template_count else 0


    for template_name, template_data in templates.items():
        if template_data["type"] == "lua":
            template_modules = template_data["modules"]
            assert len(template_modules) == 1
            module_name = template_modules[0]
            if module_name not in modules:
                template_data["checks_params"] = ""
                continue
            module_data = modules[module_name]
            module_data["is_template_module"] = 1

            if "parameters" in module_data.get("modules", []):
                checks_params = "Y"
            elif "parameters" in module_data.get("submodules", []):
                checks_params = "?"
            else:
                checks_params = "N"

        elif template_data["type"] == "mixed":
            mods = template_data.get("modules", [])
            if "parameters" in mods:
                checks_params = "Y"
            elif any("parameters" in modules.get(m, {}).get("submodules", []) for m in mods):
                checks_params = "?"
            else:
                checks_params = "N"

        else:
            checks_params = ""
        template_data["checks_params"] = checks_params


    def print_header(range):
        print(f"""\
===Templates with {range} uses===
<div class="NavFrame">
<div class="NavHead" style="text-align: left;">Templates with {range} uses</div>
<div class="NavContent derivedterms" style="text-align: left;">

{{| class="wikitable sortable"
|-
!Template!!type!!count!!pages!!x!!modules included!!templates invoked""")

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
        print(f"|{space}{template}||{data['type']}||{data['count']:,}||{data['page_count']:,}||{data['checks_params']}||{'; '.join(included_modules)}||{'; '.join(included_templates)}")

    print_footer()

if __name__ == "__main__":
    main()
