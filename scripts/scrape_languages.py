#!/usr/bin/python3
# -*- python-mode -*-

import csv
import json
import requests
import sys
import urllib

from collections import defaultdict

def expand_template(data):
    url = 'https://en.wiktionary.org/w/api.php?action=expandtemplates&format=json&prop=wikitext&text=' + urllib.parse.quote(data)

    res = requests.get( url )
    json_data = res.json()
    return json_data['expandtemplates']['wikitext']

def main():
    response = expand_template("{{#invoke:User:DTLHS/languages|export_languages|en}}")

    data =  json.loads(response)

    ALL_LANG_IDS = {k: v["1"] for k,v in data.items()}
    print("ALL_LANG_IDS =", json.dumps(ALL_LANG_IDS, indent=4, sort_keys=True, ensure_ascii=False))

    ALL_LANGS = {v["1"]: k for k,v in data.items()}
    print("ALL_LANGS =", json.dumps(ALL_LANGS, indent=4, sort_keys=True, ensure_ascii=False))

    ALT_LANGS = {}
    for k,v in sorted(data.items()):

        for alt_src in ["aliases", "otherNames"]:
            # as of 1/31/2024 one entry returns "aliases" as a hash instead of a list, just ignore it
            #  "ii" : {"1" : "Sichuan Yi", "2" : 34235, "3" : "tbq-nlo", "4" : "Yiii", "translit" : "ii-translit", "type" : "regular", "aliases" : {"1" : "Nuosu", "2" : "Nosu", "3" : "Northern Yi", "4" : "Liangshan Yi", "zh" : [ "四川彝語" ]}}
            if not isinstance(v.get(alt_src), list):
                continue
            for a in v.get(alt_src, []):
                if a not in ALT_LANGS:
                    ALT_LANGS[a] = [v["1"]]
                else:
                    ALT_LANGS[a].append(v["1"])
                    print(f"{a} is an alt_name of multiple languages: {ALT_LANGS[a]}", file=sys.stderr)
    print("ALT_LANGS =", json.dumps(ALT_LANGS, indent=4, sort_keys=True, ensure_ascii=False))

    assert len(ALL_LANG_IDS) == len(ALL_LANGS)


def main_old():
    #response = expand_template("{{#invoke:User:DTLHS/languages|export_languages|en}}")
    #response = expand_template("{{#invoke:JSON data|export_languages}}")
    response = expand_template("{{#invoke:list of languages, csv format|show}}")

    lines = [line for line in response.splitlines() if line and not line.startswith("<pre")]


    #with open("lang.data") as infile:
    #    lines = [line for line in infile if line and not line.startswith("<pre")]

    csvreader = csv.DictReader(lines, delimiter=';')
    data = {r["code"]: r["canonical name"] for r in csvreader}
    len_all_lang_ids = len(data)

    if not data:
        print("Unable to parse data: ", response, file=sys.stderr)
        exit(1)

    print("ALL_LANG_IDS =", json.dumps(data, indent=4, sort_keys=True, ensure_ascii=False))

    csvreader = csv.DictReader(lines, delimiter=';')
    data = {r["canonical name"]: r["code"] for r in csvreader}
    len_all_langs = len(data)
    print("ALL_LANGS =", json.dumps(data, indent=4, sort_keys=True, ensure_ascii=False))

    assert len_all_langs == len_all_lang_ids

#    line;code;canonical name;category;type;family code;family;sortkey?;autodetect?;exceptional?;script codes;other names;standard characters

    csvreader = csv.DictReader(lines, delimiter=';')
    data = defaultdict(list)
    for r in csvreader:
        for alt_name in r["other names"].split(","):
            if not alt_name:
                continue
            if alt_name in data:
                print(f"{alt_name} is an alt_name of {r['canonical name']} and {data[alt_name]}", file=sys.stderr)
            data[alt_name].append(r['canonical name'])
    print("ALT_LANGS =", json.dumps(data, indent=4, sort_keys=True, ensure_ascii=False))

main()
