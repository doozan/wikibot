import pytest
from nym_sections_to_tags import NymSectionToTag
from nym_sections_to_tags import Definition

synfixer = NymSectionToTag("Spanish", "es")


def run_test(orig_text, expected_text, expected_flags):

    synfixer._flagged = {}
    new_text = synfixer.run_fix(orig_text, [], "test")
    assert orig_text == new_text
    assert sorted(expected_flags) == sorted(synfixer._flagged.keys())

    synfixer._flagged = {}
    new_text = synfixer.run_fix(orig_text, expected_flags, "test")
    assert expected_text == new_text


def test_sense_match_same_level():

    orig_text="""==Spanish==

===Noun===
{{es-noun|m}}

# {{senseid|es|word1}} {{l|en|word}} {{q|Mexico|Spain}} {{gloss|a long description}}
# {{l|en|word2}}

===Synonyms===
* {{sense|word1}} {{l|es|otherword}}
"""
    expected_text="""==Spanish==

===Noun===
{{es-noun|m}}

# {{senseid|es|word1}} {{l|en|word}} {{q|Mexico|Spain}} {{gloss|a long description}}
#: {{syn|es|otherword}}
# {{l|en|word2}}
"""
    expected_flags = ["has_nym_section_at_word_level", "use_nym_section_from_word_level", "automatch_senseid"]

    run_test(orig_text,expected_text,expected_flags)


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
    expected_flags = ["autofix"]

    run_test(orig_text,expected_text,expected_flags)


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
#: {{syn|es|dibujo}}
#: {{syn|es|dibujos animados}}
#: {{hypo|es|caricatura editorial|caricatura política}}
# {{lb|es|colloquial|Mexico}} [[animated cartoon]] (''specially in plural'')
"""

    expected_flags = ['automatch_sense', 'def_duplicate_nym_defs', 'sense_matches_multiple_defs', 'unmatched_sense']
    run_test(orig_text,expected_text,expected_flags)


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
#: {{syn|es|dibujo}}
#: {{syn|es|dibujos animados}}
#: {{hypo|es|caricatura editorial|caricatura política}}
# {{lb|es|colloquial|Mexico}} [[animated cartoon]] (''specially in plural'')
"""

    expected_flags = ['automatch_sense', 'def_duplicate_nym_defs', 'sense_matches_multiple_defs', 'unmatched_sense']

    run_test(orig_text,expected_text,expected_flags)


def test_sense_match_senseid():

    orig_text="""==Spanish==

===Noun===
{{es-noun|m}}

# {{senseid|es|word1}} {{l|en|word}} {{q|Mexico|Spain}} {{gloss|a long description}}
# {{l|en|word2}}

====Synonyms====
* {{sense|word1}} {{l|es|otherword}}
"""
    expected_text="""==Spanish==

===Noun===
{{es-noun|m}}

# {{senseid|es|word1}} {{l|en|word}} {{q|Mexico|Spain}} {{gloss|a long description}}
#: {{syn|es|otherword}}
# {{l|en|word2}}
"""
    expected_flags = ["automatch_senseid"]

    run_test(orig_text,expected_text,expected_flags)



def test_sense_match_def():

    orig_text="""==Spanish==

===Noun===
{{es-noun|m}}

# {{lb|en|sometimes}} [[word1]] {{q|Mexico|Spain}} {{gloss|a long description}}
# [[word2]]

====Synonyms====
* {{sense|word2}} {{l|es|otherword2}}
* {{sense|word1}} {{l|es|otherword}}
"""
    expected_text="""==Spanish==

===Noun===
{{es-noun|m}}

# {{lb|en|sometimes}} [[word1]] {{q|Mexico|Spain}} {{gloss|a long description}}
#: {{syn|es|otherword}}
# [[word2]]
#: {{syn|es|otherword2}}
"""

    expected_flags = ["automatch_sense"]

    run_test(orig_text,expected_text,expected_flags)


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


def test_definition():

    d = Definition("es", "# [[word]]")
    assert d.has_nym("Synonyms") == False
    assert d.is_good() == True

    d.add("#: {{syn|es|word2}}")
    assert d.has_nym("Synonyms") == True
    assert d.is_good() == True

    d.add("#: {{ant|es|notword}}")
    assert d.has_nym("Antonyms") == True
    assert d.is_good() == True

    d.add("#: {{synonyms|es|word3}}")
    assert d.has_nym("Synonyms") == True
    assert d.is_good() == False
    assert sorted([ k for k,v in d.get_problems() ]) == sorted([ "duplicate_nym_defs" ])



    d = Definition("es", "# [[word]]")
    d.add("#: {{unknown|es|word3}}")
    assert sorted([ k for k,v in d.get_problems() ]) == sorted([ "hashcolon_is_not_nym" ])

     # TODO: Check nym language matches lang_id
     # Nym lines are currently not parsed beyond getting the template name
#    d = Definition("es", "# [[word]]")
#    d.add("#: {{ant|en|word2}}")
#    assert sorted([ k for k,v in d.get_problems() ]) == sorted([ "nym_language_mismatch" ])

    d = Definition("es", "# {{senseid|es|word}} [[word]] (qualifier)")
    assert d.get_senseid() == "word"
    assert sorted([ k for k,v in d.get_problems() ]) == sorted([ ])

    d = Definition("es", "# {{senseid|en|word}} [[word]] (qualifier)")
    assert d.get_senseid() == ""
    assert sorted([ k for k,v in d.get_problems() ]) == sorted(["senseid_lang_mismatch"])


def test_definition_stripping():

    d = Definition("es", "# [[word1]], [[word2]]; [[word3]]")
    assert d.has_sense("word1")
    assert d.has_sense("word2")
    assert d.has_sense("word1|word2")
    assert d.has_sense("word2|word1")
    assert not d.has_sense("word3")

    assert d.strip_to_text( "{{blah}} test1, (blah) [[test2]], test3 ") == "test1,  test2, test3"



