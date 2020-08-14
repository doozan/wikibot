import pytest
from nym_sections_to_tags import NymSectionToTag

synfixer = NymSectionToTag("Spanish", "es")

def test_run_fix_simple():

    orig_text="""==Spanish==

===Noun===
{{es-noun|mf|aboriginales}}

# {{l|en|Aborigine}} {{gloss|original inhabitant of Australia}}

====Synonyms====
* {{l|es|aborigen}}
"""
    expected_text="""==Spanish==

===Noun===
{{es-noun|mf|aboriginales}}

# {{l|en|Aborigine}} {{gloss|original inhabitant of Australia}}
#: {{syn|es|aborigen}}
"""
    synfixer._flagged = {}
    new_text = synfixer.run_fix(orig_text, [], "test")
    assert new_text == expected_text


def test_run_fix_complex():

    orig_text="""==Spanish==

===Noun===
{{es-noun|f}}

# {{lb|es|art}} [[caricature]] (pictorial representation of someone for comic effect)
# {{lb|es|colloquial|Mexico}} [[animated cartoon]] (''specially in plural'')

====Synonyms====
* {{sense|caricature}} {{l|es|dibujo}}
* {{sense|cartoon}} {{l|es|dibujos animados}}

====Hyponyms====
* {{l|es|caricatura editorial||editorial cartoon}}
* {{l|es|caricatura política}}
"""

    expected_text="""==Spanish==

===Noun===
{{es-noun|f}}

# {{lb|es|art}} [[caricature]] (pictorial representation of someone for comic effect)
# {{lb|es|colloquial|Mexico}} [[animated cartoon]] (''specially in plural'')
#: {{syn|es|dibujos animados}}
#: {{syn|es|dibujo}}
#: {{hypo|es|caricatura editorial|caricatura política}}
"""

    synfixer._flagged = {}
    new_text = synfixer.run_fix(orig_text, [], "test")
    assert new_text == orig_text

    tools = sorted(synfixer._flagged.keys())

    assert ['def_duplicate_nym_defs', 'sense_matches_multiple_defs', 'unmatched_sense'] == tools

    fixed = synfixer.run_fix(orig_text, tools, "test")
    assert fixed == expected_text


def test_run_fix_complex2():

    orig_text="""==Spanish==

===Noun===
{{es-noun|f}}

# {{lb|es|art}} [[caricature]] (pictorial representation of someone for comic effect)
# {{lb|es|colloquial|Mexico}} [[animated cartoon]] (''specially in plural'')

====Hyponyms====
* {{l|es|caricatura editorial||editorial cartoon}}
* {{l|es|caricatura política}}

====Synonyms====
* {{sense|caricature}} {{l|es|dibujo}}
* {{sense|cartoon}} {{l|es|dibujos animados}}
"""

    expected_text="""==Spanish==

===Noun===
{{es-noun|f}}

# {{lb|es|art}} [[caricature]] (pictorial representation of someone for comic effect)
# {{lb|es|colloquial|Mexico}} [[animated cartoon]] (''specially in plural'')
#: {{syn|es|dibujos animados}}
#: {{syn|es|dibujo}}
#: {{hypo|es|caricatura editorial|caricatura política}}
"""

    synfixer._flagged = {}
    new_text = synfixer.run_fix(orig_text, [], "test")
    assert new_text == orig_text

    tools = sorted(synfixer._flagged.keys())

    assert ['def_duplicate_nym_defs', 'sense_matches_multiple_defs', 'unmatched_sense'] == tools

    fixed = synfixer.run_fix(orig_text, tools, "test")
    assert fixed == expected_text


def test_parse_section_items():

    section="""====Synonyms====
* {{l|es|salvadoreño}}, {{l|es|cuscatleco}}
* {{qualifier|Including all Romance languages}} {{l|es|Latinoamérica}}
* {{l|es|dale}} {{qualifier|Argentina}}
* {{l|es|viñedo|g=m}}
"""
    results = synfixer.parse_section_items(section)
    assert results == {'': [({'1': 'es', '2': 'salvadoreño'}, None, None), ({'1': 'es', '2': 'cuscatleco'}, None, None), ({'1': 'es', '2': 'Latinoamérica'}, ['Including all Romance languages'], None), ({'1': 'es', '2': 'dale'}, ['Argentina'], None), ({'1': 'es', '2': 'viñedo'}, None, None)]}

    tag="{{syn|es|salvadoreño|cuscatleco|Latinoamérica|q3=Including all Romance languages|dale|q4=Argentina|viñedo}}"
    assert tag == synfixer.make_tag("syn", results[""])

    tests = {
        "====Synonyms====\n* {{l|es|salvadoreño}}, {{l|es|cuscatleco}}" : "{{syn|es|salvadoreño|cuscatleco}}",
        "====Synonyms====\n* {{l|es|calala|g=f}} (''Nicaragua'')": "{{syn|es|calala|q1=Nicaragua}}"
    }

    for test,value in tests.items():
        res = synfixer.parse_section_items(test)
        print(res)
        assert value == synfixer.make_tag("syn", synfixer.parse_section_items(test)[""])


def test_parse_word():

    tests = {
        "{{l|es|cuscatleco}}": ( {"1": "es", "2": "cuscatleco"}, None, None),
        "{{l|es|dale}} {{qualifier|Argentina}}": ( {"1": "es", "2": "dale"}, ["Argentina"], None),
        "{{q|Colombia|Costa Rica|Ecuador|Guatemala|Southern Mexico|Venezuela}} {{l|es|danta}}": ({'1': 'es', '2': 'danta'}, ['Colombia', 'Costa Rica', 'Ecuador', 'Guatemala', 'Southern Mexico', 'Venezuela'], None),
        "See [[Thesaurus:pared]].": ({"1": "es", "2": "Thesaurus:pared"}, None, None),
        "{{l|es|pambol}} (Mexico, colloquial)": ({"1": "es", "2": "pambol"}, ["Mexico", "colloquial"], None),
        "{{l|es|calala|g=f}} (''Nicaragua'')": ({"1": "es", "2": "calala"}, ["Nicaragua"], None),
    }

    for test,value in tests.items():
        assert value == synfixer.parse_word(test)

def test_parse_word_fails():

    tests = [
        { "test": "{{l|es|calala|g=f}} [[blah]]", "errors":["duplicate_text_and_template"] }, # Multiple Links
        { "test": "{{q|blah}}", "errors":["missing_link"] }, # Missing Link
        { "test": "{{l|es|calala|g=f}} {{q|blah}} (blah2)", "errors":["duplicate_text_and_template"] }, # Multiple Qualifiers
        ]

    for t in tests:
        synfixer._flagged = {}
        #assert value == synfixer.strip_templates(test)
        synfixer.parse_word(t["test"])
        assert sorted(t["errors"]) == sorted(synfixer._flagged.keys())

    for test,results in tests:
            assert synfixer.parse_word(test)

def test_strip_templates():
    tests = {
        "{{l|es|pambol}} (Mexico, colloquial)": " (Mexico, colloquial)"
    }


    for test,results in tests.items():
        assert results == synfixer.strip_templates(test)

#    for test,errors in tests.items():
#        synfixer._flagged = {}
#        #assert value == synfixer.strip_templates(test)
#        assert sorted(errors) == sorted(synfixer._flagged.keys())


def test_get_item_from_text():

    tests = [
        { "test": "(Mexico, colloquial)", "link": None, "qualifiers": ["Mexico", "colloquial"], "gloss": None, "errors": [] },
        { "test": "[[Mexico]] (colloquial)", "link": {"1":"es", "2":"Mexico"}, "qualifiers": ["colloquial"], "gloss": None, "errors": [] },
        { "test": "(colloquial) [[Mexico]]", "link": {"1":"es", "2":"Mexico"}, "qualifiers": ["colloquial"], "gloss": None, "errors": [] },
        { "test": " (colloquial)  [[Mexico]] ", "link": {"1":"es", "2":"Mexico"}, "qualifiers": ["colloquial"], "gloss": None, "errors": [] },
        { "test": " [[Ciudad]] de [[Mexico]] ", "link": {"1":"es", "2":"Ciudad"}, "qualifiers": None, "gloss": None, "errors": ["nym_unexpected_text"] },
        { "test": "blah [[Ciudad]]", "link": {"1":"es", "2":"Ciudad"}, "qualifiers": None, "gloss": None, "errors": ["nym_unexpected_text"] },
        { "test": "blah", "link": None, "qualifiers": None, "gloss": None, "errors": ["nym_unexpected_text"] },
        { "test": " [[Ciudad]] [[Mexico]] ", "link": {"1":"es", "2":"Ciudad"}, "qualifiers": None, "gloss": None, "errors": ["nym_unexpected_text"] },
    ]


    for t in tests:
        synfixer._flagged = {}
        assert (t["link"], t["qualifiers"], t["gloss"]) == synfixer.get_item_from_text(t["test"])
        assert sorted(t["errors"]) == sorted(synfixer._flagged.keys())


#        "[[Mexico]] (colloquial)": ({ "1": "es", "2": "Mexico" }, ["colloquial"], None),
#        "(colloquial) [[Mexico]]": ({ "1": "es", "2": "Mexico" }, ["colloquial"], None),

#    for test,value in tests.items():
#        assert value == synfixer.get_item_from_text(test)

def test_get_item_from_text_fails():

    tests = {
        "[[Cuiudad]] de [[Mexico]]": ["nym_unexpected_text"],
        "blah [[Mexico]]": ["nym_unexpected_text"],
        "blah": ["nym_unexpected_text"],
        "[[Mexico]], [[Korea]]": ["nym_unexpected_text"],
        "[[Mexico]] (blah) (blah)": ["nym_unexpected_text"],
        "[[Mexico]] [[Mexico2]]": ["nym_unexpected_text"],
        "(blah) (blah)": ["nym_unexpected_text"],
        }

    for test,results in tests.items():
        synfixer._flagged = {}
        synfixer.get_item_from_text(test)
        assert sorted(results) == sorted(synfixer._flagged.keys())


def test_get_item_from_templates_fails():

    tests = {
        "{{l|es|calala|g=f}} {{q|blah}} {{q|blah2}}": [ "multi_qualifier" ],

        # TODO: this should raise more than just multi_qualifier
        "de {{l|es|calala|g=f}} {{q|blah}} {{q|blah2}}": [ "multi_qualifier" ],
    }

    for test,results in tests.items():
        synfixer._flagged = {}
        synfixer.get_item_from_templates(test)
        for flag in results:
#            raise ValueError("XXX", synfixer._flagged.keys())
            assert flag in synfixer._flagged.keys()

