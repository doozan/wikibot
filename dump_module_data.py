#!/usr/bin/python3

import argparse
import json
import multiprocessing
import re
import sys

from autodooz.utils import iter_wxt, iter_xml

def main():
    parser = argparse.ArgumentParser(description="Find errors in sense lists")
    parser.add_argument("target", help="target filename")
    parser.add_argument("--xml", help="XML file to load")
    parser.add_argument("--wxt", help="Wiktionary extract file to load")
    parser.add_argument("--limit", type=int, help="Limit processing to first N articles")
    parser.add_argument("--progress", help="Display progress", action='store_true')
    parser.add_argument("-j", help="run N jobs in parallel (default = # CPUs - 1", type=int)
    args = parser.parse_args()

    if (not args.xml and not args.wxt) or (args.xml and args.wxt):
        print("use either --xml or --wxt")
        exit(1)

    if not args.j:
        args.j = multiprocessing.cpu_count()-1

    if args.wxt:
        iter_entries = iter_wxt(args.wxt, args.limit, args.progress, title_matches=lambda x: x.startswith("Module:"))
    else:
        iter_entries = iter_xml(args.xml, args.limit, args.progress, title_matches=lambda x: x.startswith("Module:"))

    dump_module_data(iter_entries, args.target)


def get_module_stats(args):

    entry_text, entry_title = args
    entry_title = entry_title.removeprefix("Module:")

    m = re.match(r"^\s*#REDIRECT[:]?\s*\[\[\s*([:]?M(?:odule)?:(.*?))\s*\]\]", entry_text, re.IGNORECASE)
    if m:
        return entry_title, "redirect", m.group(2).strip()

    wiki_calls = "expandTemplate", "callParserFunction", "preprocess", "newParserValue", "newTemplateParserValue"
    used_wiki_calls = [f for f in wiki_calls if f in entry_text]

    used_modules = sorted(set(m.group(1).removeprefix("Module:").replace("_", " ").rstrip("/") for m in re.finditer("""(?:require|require_when_needed)\s*\(\s*["']\s*(.+?)\s*["']""", entry_text)))

    # if no modules are detected inside require() or require_when_needed(), search for all strings with "Module:xx"
    # yields false positives and calls to module/data loads
#    if not used_modules:
#        used_modules = sorted(set(m.group(1).strip() for m in re.finditer("""["']\s*(Module:.+?)\s*["']""", entry_text)))
#        if used_modules:
#            print(entry_title, used_modules)

#    if used_modules:
#        print(entry_title, used_modules)

    return entry_title, "module", used_modules, used_wiki_calls

def dump_module_data(iter_entries, filename):
    iter_items = map(get_module_stats, iter_entries)


    modules = {}
    redirects = {}
    for res in iter_items:
        module, module_type, *extra = res
        if module_type == "redirect":
            redirects[module] = extra[0]
            continue

        used_modules, used_wiki_calls = extra
        modules[module] = {k:v for k,v in [
            ("modules", used_modules),
            ("funcions", used_wiki_calls),
        ] if v}


    def get_submodules(module_name, module_data, seen=None):
        all_submodules = set()
        if not seen:
            seen = set()

        if "submodules" in module_data:
            return module_data["submodules"]

        for submodule_name in module_data.get("modules", []):

            all_submodules.add(submodule_name)
            submodule_name = redirects.get(submodule_name, submodule_name)
            if submodule_name in seen:
                continue
            seen.add(submodule_name)

            if submodule_name not in modules:
                continue
            submodule_data = modules[submodule_name]

            if "submodules" not in submodule_data:
                submodules = get_submodules(submodule_name, submodule_data, seen)
                submodule_data["submodules"] = submodules

            all_submodules |= submodule_data["submodules"]

        return all_submodules

    # Resolve all module inter-dependencies
    for module_name, module_data in modules.items():
        if "submodules" in module_data:
            continue
        submodules = get_submodules(module_name, module_data)
        module_data["submodules"] = submodules

    for module_name, module_data in modules.items():
        subs = module_data["submodules"]
        if subs:
            module_data["submodules"] = sorted(subs)
        else:
            del module_data["submodules"]



    with open(filename, 'w', encoding='utf-8') as outfile:
        json.dump({
            "modules": modules,
            "redirects": redirects,
            }, outfile, ensure_ascii=False, indent=4, sort_keys=True)

if __name__ == "__main__":
    main()
