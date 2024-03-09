from autodooz.fix_missing_taxlinks import MissingTaxlinkFixer as Fixer

import os
import re

SPANISH_DATA = "../spanish_data"
NEWEST = max(f.name for f in os.scandir(SPANISH_DATA) if f.is_dir() and re.match(r"\d\d\d\d-\d\d-\d\d$", f.name))
NEWEST_DATA = os.path.join(SPANISH_DATA, NEWEST)
# TODO: generate sample files for testing instead of using real files
local = [ os.path.join(NEWEST_DATA, "local_taxons.tsv") ]
external = [ os.path.join(NEWEST_DATA, "external_taxons.tsv") ]
external += [f"!{file}" for file in local]

safe_fixer = Fixer(local=local, external=external, profile="wikitext_only")
fixer = Fixer(local=local, external=external, rename_local_taxlinks=True)


base = """\
==English==

===Noun===
# """


def test_fixes():

    tests = {
        "[[Salvia rosmarinus]]": "{{taxfmt|Salvia rosmarinus|species}}",
        "[[ Salvia rosmarinus ]]": "{{taxfmt|Salvia rosmarinus|species}}",
        "[[ '' Salvia rosmarinus '' ]]": "{{taxfmt|Salvia rosmarinus|species}}",

        "'''''[[Salvia rosmarinus]]'''''": " {{taxfmt|Salvia rosmarinus|species}}x ",
        "foo ''[[ '' Salvia rosmarinus '' ]]'' bar": "foo {{taxfmt|Salvia rosmarinus|species}} bar",

         "[[Salvia]] [[rosmarinus]]": "{{taxfmt|Salvia rosmarinus|species}}",
        "''[[Salvia]]'' ''[[rosmarinus]]''": "{{taxfmt|Salvia rosmarinus|species}}",

        # Replace links in italics, even inside unsafe templates
        "{{unsafe_template|head=[[''Salvia rosmarinus'']] test|i=1|g=f}}": "{{unsafe_template|head={{taxfmt|Salvia rosmarinus|species}} test|i=1|g=f}}",
        # But not bare links
        "{{unsafe_template|head=[[Salvia rosmarinus]] test|i=1|g=f}}": None,
        # and not italacized links # TODO: this would be okay, but needs to check that it doesn't replace '''[[x]]''' with '{{x}}'
        "{{unsafe_template|head=''[[Salvia rosmarinus]]'' test|i=1|g=f}}": None,


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

        "[[[Salvia rosmarinus]]": None,
        "[[[Salvia rosmarinus]]]": None,

        "[[Salvia rosmarinus]]]]": "{{taxfmt|Salvia rosmarinus|species}}]]",

        "''Salvia rosmarinus''": "{{taxfmt|Salvia rosmarinus|species}}",
        "''[[Salvia rosmarinus]]''": "{{taxfmt|Salvia rosmarinus|species}}",

        "''[[Salvia rosmarinus]], a plant''": "''{{taxfmt|Salvia rosmarinus|species}}, a plant''",
        "''a plant: [[Salvia rosmarinus]]''": "''a plant: {{taxfmt|Salvia rosmarinus|species}}''",

        # unhandled: Barewords inside links
        "[[Image:pretty.png|a plant: Salvia rosmarinus]]": None,
        "[[a page|a plant: Salvia rosmarinus]]": None,

        # TODO
        # allowed: Barewords as complete param value inside links
        "[[Image:pretty.png|Salvia rosmarinus]]": None, #"[[Image:pretty.png|{{taxfmt|Salvia rosmarinus|species}}]]",

        # replace complete templates with taxfmt (l, mul, ll)
        # formatted or barewords as 2=parameter inside l, mul, and ll templates and no other parameters besides 1=
        "{{l|mul|Salvia rosmarinus}}": "{{taxfmt|Salvia rosmarinus|species}}",

        "{{l|mul|Salvia rosmarinus|''Salvia rosmarinus''}}": "{{taxfmt|Salvia rosmarinus|species}}",
        "{{l|mul|Salvia rosmarinus|''Salvia'' ''rosmarinus''}}": "{{taxfmt|Salvia rosmarinus|species}}",

        # TODO: test that this fails on something with no_auto
        "{{l|anything-goes-here|Salvia rosmarinus}}": "{{taxfmt|Salvia rosmarinus|species}}",
        #"{{l|en|Salvia rosmarinus}}": "{{taxfmt|Salvia rosmarinus|species}}",
        #"{{ll|en|Salvia rosmarinus}}": "{{taxfmt|Salvia rosmarinus|species}}",
        "{{ll|mul|Salvia rosmarinus}}": "{{taxfmt|Salvia rosmarinus|species}}",
        "{{m|mul|Salvia rosmarinus}}": "{{taxfmt|Salvia rosmarinus|species}}",
        "''{{ll|mul|Salvia rosmarinus}}''": "{{taxfmt|Salvia rosmarinus|species}}",
#        "# {{senseid|en|Q753755}} a [[wader]] of species ''{{ll|mul|Metopidius indicus}}'', in the family {{taxfmt|Jacanidae|family}}.": "x",

        # no replacement when extra params
        "{{m|mul|Salvia rosmarinus|test=1}}": None,
        "{{unsupported|mul|Salvia rosmarinus}}": None,

        # Strip surrounding '' '' on replacements
        "''{{ll|mul|Salvia rosmarinus}}''": "{{taxfmt|Salvia rosmarinus|species}}",
        "''{{ll|mul|Salvia rosmarinus}}, {{ll|mul|Salvia rosmarinus}}''": "{{taxfmt|Salvia rosmarinus|species}}, {{taxfmt|Salvia rosmarinus|species}}",
        "'''{{ll|mul|Salvia rosmarinus}}'''": "'''{{taxfmt|Salvia rosmarinus|species}}'''",
        "'''''{{ll|mul|Salvia rosmarinus}}'''''": "'''{{taxfmt|Salvia rosmarinus|species}}'''",

        "{{gloss|test|Salvia rosmarinus|param=test}}": "{{gloss|test|Salvia rosmarinus|param=test}}",


        "({{l|mul|Salvia rosmarinus|''Salvia'' ''rosmarinus''}})": "({{taxfmt|Salvia rosmarinus|species}})",

        "[[Salvia rosmarinus|Salvia rosmarinus]]": None,
        #"[[Salvia rosmarinus|''Salvia rosmarinus'']]": "{{taxfmt|Salvia rosmarinus|species}}",
        "[[test|''Salvia rosmarinus'']]": None,
        #"[[Salvia rosmarinus#Translingual|''Salvia rosmarinus'']]": "{{taxfmt|Salvia rosmarinus|species}}",
        "[[test|Salvia rosmarinus]]": None,
        #"[[test|test ''Salvia rosmarinus'']]": "[[test|test {{taxfmt|Salvia rosmarinus|species}}]]",



        "''Salvia rosmarinus'' and ''{{l|mul|Salvia rosmarinus}}''": "{{taxfmt|Salvia rosmarinus|species}} and {{taxfmt|Salvia rosmarinus|species}}",


#        "{{suffix|en|Pteridaceae|ous}}": None,
#        "{{lb|en|botany}} Belonging to the [[Pteridaceae]].": "{{lb|en|botany}} Belonging to the {{taxfmt|Pteridaceae|family}}."

        # Bare text
#        "foo Salvia rosamarinus bar": "foo {{taxfmt|Salvia rosamarinus|species}} bar"
#        # But not in templates
#        "foo {{test|Salvia rosamarinus}} bar": None,
#        # or comments
#        "foo <!-- Salvia rosamarinus --> bar": None,

    }

    for test, expected in tests.items():
        print("----", test, "----")
        if expected is None:
            expected = test

        res_full = fixer.process(base + test, "test", [])
        res = res_full[len(base):]
        print("EXPECTED:", expected)
        print("RECIEVED:", res)
        assert res == expected

        # The safe fixer should generate the same results for these tests
        safe_full = safe_fixer.process(base + test, "test", [])
        assert safe_full == res_full


def test_careful_fixes():
    tests = {
        # Unhandled, first [[ matches as opening of a link named [Salvia rosmarinus
        "{{q|stuff [[Salvia rosmarinus]]}}": "{{q|stuff {{taxfmt|Salvia rosmarinus|species}}}}",
        "{{q|[[Salvia rosmarinus]]}}": "({{taxfmt|Salvia rosmarinus|species}})",
        "[[Image:pretty.png|a plant: [[Salvia rosmarinus]]]]": "[[Image:pretty.png|a plant: {{taxfmt|Salvia rosmarinus|species}}]]",

        # Replace linked/italacized text within supported templates
        "{{col3|a plant: [[Salvia rosmarinus]]}}": "{{col3|a plant: {{taxfmt|Salvia rosmarinus|species}}}}",
        "{{col3|a plant: ''[[Salvia rosmarinus]]''}}": "{{col3|a plant: {{taxfmt|Salvia rosmarinus|species}}}}",
        "{{col3|a plant: ''Salvia rosmarinus''}}": "{{col3|a plant: {{taxfmt|Salvia rosmarinus|species}}}}",

        # but not bare text
        "{{col3|a plant: Salvia rosmarinus}}": None,

        # and not inside unsupported templates
        "{{unsupported|en|a plant: ''Salvia rosmarinus''}}": None,
    }

    for test, expected in tests.items():
        print("----", test, "----")
        if expected is None:
            expected = test

        res_full = fixer.process(base + test, "test", [])
        res = res_full[len(base):]
        print("EXPECTED:", expected)
        print("RECIEVED:", res)
        assert res == expected

        # Sanity check: The safe fixer shouldn't make any replacements
        expected = test
        safe_full = safe_fixer.process(base + test, "test", [])
        safe_res = safe_full[len(base):]
        print("sanity check", [safe_res, expected])
        assert safe_res == expected


def test_nomatch_title():

    # Replacement as usual
    test = "''Salvia rosmarinus''"
    expected = "{{taxfmt|Salvia rosmarinus|species}}"
    res_full = fixer.process(base + test, "NOT Salvia rosmarinus", [])
    res = res_full[len(base):]
    assert res == expected


    # BUT, no replacement for text on the same page
    expected = test

    res_full = fixer.process(base + test, "Salvia rosmarinus", [])
    res = res_full[len(base):]
    assert res == expected


def test_convert_taxlink_to_taxfmt():

    tests = {
            # Rename taxlinks with local sources
            "{{taxlink|Salvia rosmarinus|species}}": "{{taxfmt|Salvia rosmarinus|species}}",

            # Preserve params
            "{{taxlink|Salvia rosmarinus|species|wplink=test|i=1}}": "{{taxfmt|Salvia rosmarinus|species|wplink=test|i=1}}",

            # Don't rename if mul=1
            "{{taxlink|Salvia rosmarinus|species|wplink=test|nomul=1|i=1}}": None,
    }

    for test, expected in tests.items():
        print("----", test, "----")
        if expected is None:
            expected = test

        res_full = fixer.process(base + test, "test", [])
        res = res_full[len(base):]
        print("EXPECTED:", expected)
        print("RECIEVED:", res)
        assert res == expected


    # DON'T  Preserve params

    res_full = fixer.process(base + test, "test", [])
    res = res_full[len(base):]
    assert res == expected


