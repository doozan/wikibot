from autodooz.fix_missing_taxlinks import MissingTaxlinkFixer as Fixer

import os
import re

SPANISH_DATA = "../spanish_data"
NEWEST = max(f.name for f in os.scandir(SPANISH_DATA) if f.is_dir() and re.match(r"\d\d\d\d-\d\d-\d\d$", f.name))
NEWEST_DATA = os.path.join(SPANISH_DATA, NEWEST)
fixer = Fixer(os.path.join(NEWEST_DATA, "taxons.tsv"))

def test_process():

    test_base = """\
==English==

===Noun===
# """

    expected_base = """\
==English==

===Noun===
# """

    tests = {
        "[[Salvia rosmarinus]]": "{{taxfmt|Salvia rosmarinus|species}}",
        "[[ Salvia rosmarinus ]]": "{{taxfmt|Salvia rosmarinus|species}}",
        "[[ '' Salvia rosmarinus '' ]]": "{{taxfmt|Salvia rosmarinus|species}}",

        "'''''[[Salvia rosmarinus]]'''''": " {{taxfmt|Salvia rosmarinus|species}}x ",
        "foo '' [[ '' Salvia rosmarinus '' ]] '' bar": "foo {{taxfmt|Salvia rosmarinus|species}} bar",

         "[[Salvia]] [[rosmarinus]]": "{{taxfmt|Salvia rosmarinus|species}}",
        "''[[Salvia]]'' ''[[rosmarinus]]''": "{{taxfmt|Salvia rosmarinus|species}}",

        # don't match yet, but should
        "''[[Salvia]]'' [[rosmarinus]]": None, #"{{taxfmt|Salvia rosmarinus|species}}",
        "Salvia [[rosmarinus]]": None, #"{{taxfmt|Salvia rosmarinus|species}}",
        "[[Salvia]] ''[[rosmarinus]]''": None, #"{{taxfmt|Salvia rosmarinus|species}}",

        "''[[Salvia rosmarinus]]''": "{{taxfmt|Salvia rosmarinus|species}}",
        "'''[[Salvia rosmarinus]]'''": "'''{{taxfmt|Salvia rosmarinus|species}}'''",
        "'''''[[Salvia rosmarinus]]'''''": "'''{{taxfmt|Salvia rosmarinus|species}}'''",
        "''([[Salvia rosmarinus]])''": "({{taxfmt|Salvia rosmarinus|species}})",
        "'''''([[Salvia rosmarinus]])'''''": "'''({{taxfmt|Salvia rosmarinus|species}})'''",
        "[[Salvia rosmarinus]]]": "{{taxfmt|Salvia rosmarinus|species}}]",
        "[[''Salvia rosmarinus'']]": "{{taxfmt|Salvia rosmarinus|species}}",
        "''Salvia rosmarinus''": "{{taxfmt|Salvia rosmarinus|species}}",
        "'''Salvia rosmarinus'''": None,
        "'''''Salvia rosmarinus'''''": "'''{{taxfmt|Salvia rosmarinus|species}}'''",

        # Unhandled, first [[ matches as opening of a link named [Salvia rosmarinus
        "[[[Salvia rosmarinus]]": None,
        "[[[Salvia rosmarinus]]]": None,

        "[[Salvia rosmarinus]]]]": "{{taxfmt|Salvia rosmarinus|species}}]]",

        "''Salvia rosmarinus''": "{{taxfmt|Salvia rosmarinus|species}}",
        "''[[Salvia rosmarinus]]''": "{{taxfmt|Salvia rosmarinus|species}}",

        "''[[Salvia rosmarinus]], a plant''": "''{{taxfmt|Salvia rosmarinus|species}}, a plant''",
        "''a plant: [[Salvia rosmarinus]]''": "''a plant: {{taxfmt|Salvia rosmarinus|species}}''",
        "[[Image:pretty.png|a plant: [[Salvia rosmarinus]]]]": "[[Image:pretty.png|a plant: {{taxfmt|Salvia rosmarinus|species}}]]",

        # unhandled: Barewords not complete param value
        "[[Image:pretty.png|a plant: Salvia rosmarinus]]": None,

        # TODO
        # allowed: Barewords as complete param value inside links
        "[[Image:pretty.png|Salvia rosmarinus]]": None, #"[[Image:pretty.png|{{taxfmt|Salvia rosmarinus|species}}]]",

        # replace complete templates with taxfmt (l, mul, ll)
        # formatted or barewords as 2=parameter inside l, mul, and ll templates and no other parameters besides 1=
        "{{l|mul|Salvia rosmarinus}}": "{{taxfmt|Salvia rosmarinus|species}}",
        "{{l|anything-goes-here|Salvia rosmarinus}}": "{{taxfmt|Salvia rosmarinus|species}}",
        "{{l|en|Salvia rosmarinus}}": "{{taxfmt|Salvia rosmarinus|species}}",
        "{{ll|en|Salvia rosmarinus}}": "{{taxfmt|Salvia rosmarinus|species}}",
        "{{ll|mul|Salvia rosmarinus}}": "{{taxfmt|Salvia rosmarinus|species}}",
        "{{m|mul|Salvia rosmarinus}}": "{{taxfmt|Salvia rosmarinus|species}}",
        "''{{ll|mul|Salvia rosmarinus}}''": "{{taxfmt|Salvia rosmarinus|species}}",
#        "# {{senseid|en|Q753755}} a [[wader]] of species ''{{ll|mul|Metopidius indicus}}'', in the family {{taxfmt|Jacanidae|family}}.": "x",

        # no replacement when extra params
        "{{m|mul|Salvia rosmarinus|test=1}}": None,
        "{{unsupported|mul|Salvia rosmarinus}}": None,

        # Strip surrounding '' '' on replacements
        "''{{ll|mul|Salvia rosmarinus}}''": "{{taxfmt|Salvia rosmarinus|species}}",
        "''{{ll|mul|Salvia rosmarinus}}, {{ll|en|Salvia rosmarinus}}''": "{{taxfmt|Salvia rosmarinus|species}}, {{taxfmt|Salvia rosmarinus|species}}",
        "'''{{ll|mul|Salvia rosmarinus}}'''": "'''{{taxfmt|Salvia rosmarinus|species}}'''",
        "'''''{{ll|mul|Salvia rosmarinus}}'''''": "'''{{taxfmt|Salvia rosmarinus|species}}'''",

        # Replace linked/italacized text within supported templates
        "{{l|en|a plant: [[Salvia rosmarinus]]}}": "{{l|en|a plant: {{taxfmt|Salvia rosmarinus|species}}}}",
        "{{l|en|a plant: ''[[Salvia rosmarinus]]''}}": "{{l|en|a plant: {{taxfmt|Salvia rosmarinus|species}}}}",
        "{{l|en|a plant: ''Salvia rosmarinus''}}": "{{l|en|a plant: {{taxfmt|Salvia rosmarinus|species}}}}",

        # but not bare text
        "{{l|en|a plant: Salvia rosmarinus}}": None,

        # and not inside unsupported templates
        "{{unsupported|en|a plant: ''Salvia rosmarinus''}}": None,


        "{{gloss|test|Salvia rosmarinus|param=test}}": "{{gloss|test|Salvia rosmarinus|param=test}}",


        "[[Salvia rosmarinus|''Salvia rosmarinus'']]": "{{taxfmt|Salvia rosmarinus|species}}",
        "[[Salvia rosmarinus#Translingual|''Salvia rosmarinus'']]": "{{taxfmt|Salvia rosmarinus|species}}",
        "[[test|Salvia rosmarinus]]": None,
        #"[[test|test ''Salvia rosmarinus'']]": "[[test|test {{taxfmt|Salvia rosmarinus|species}}]]",

        "{{suffix|en|Pteridaceae|ous}}": None,
        "{{lb|en|botany}} Belonging to the [[Pteridaceae]].": "{{lb|en|botany}} Belonging to the {{taxfmt|Pteridaceae|family}}."

        # Bare text
#        "foo Salvia rosamarinus bar": "foo {{taxfmt|Salvia rosamarinus|species}} bar"
#        # But not in templates
#        "foo {{test|Salvia rosamarinus}} bar": None,
#        # or comments
#        "foo <!-- Salvia rosamarinus --> bar": None,

    }

    for test, expected in tests.items():
        print("-----", test)
        res = fixer.process(test_base + test, "test", [])
        print([res[len(expected_base):]])
        if expected is None:
            expected = test
        assert res == expected_base + expected
