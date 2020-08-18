import pytest
from nym_sections_to_tags import NymSectionToTag
from nym_sections_to_tags import Definition

fixer = NymSectionToTag("Spanish", "es")


def run_test(orig_text, expected_text, expected_flags):

    fixer._flagged = {}
    new_text = fixer.run_fix(orig_text, [], "test")
    assert orig_text == new_text
#    assert sorted(expected_flags) == sorted(fixer._flagged.keys())

    fixer._flagged = {}
    new_text = fixer.run_fix(orig_text, expected_flags, "test", sections=["Synonyms","Antonyms","Hyponyms"])
    assert expected_text == new_text


def test_nym_tables():
    orig_text="""==Spanish==

===Noun===
{{es-noun|m}}

# {{l|en|word}}

====Hyponyms====
{{col3|es
|grupo abeliano
|grupo corona
|grupo de la muerte
|grupo étnico
|{{l|es|grupo de presión||lobby, pressure group}}
|{{l|es|grupo de edad||age group, age range, age bracket}}
|grupo funcional
|grupo saliente
|grupo social
}}
"""
    expected_text = orig_text
    expected_flags = ["link_unexpected_template", "missing_link", "make_tag_failed"]

    run_test(orig_text,expected_text,expected_flags)



def test_run_fix_viste():

    orig_text="""==Spanish==

===Interjection===
{{head|es|interjection}}

# {{lb|es|interrogatively|informal|Rioplatense}} {{non-gloss definition|Used as a space filler, usually in the middle of a sentence, or when telling a story.}}
#: No sabía qué decirle, ¿'''viste'''? — I didn't know what to tell her, '''you know'''?

===Synonyms===
* [[sabés|¿sabés?]], [[no|¿no?]]
"""

    expected_text="""==Spanish==

===Interjection===
{{head|es|interjection}}

# {{lb|es|interrogatively|informal|Rioplatense}} {{non-gloss definition|Used as a space filler, usually in the middle of a sentence, or when telling a story.}}
#: No sabía qué decirle, ¿'''viste'''? — I didn't know what to tell her, '''you know'''?
#: {{syn|es|sabés|no}}
"""
    expected_flags = ['def_hashcolon_is_not_nym', 'has_nym_section_at_word_level', 'use_nym_section_from_word_level']

    run_test(orig_text,expected_text,expected_flags)


def test_open_templates():

    orig_text="""==Spanish==

===Noun===
{{es-noun|m}}

# {{l|en
|word}} {{q|Mexico
|Spain}} {{gloss
|a long description}}

====Synonyms====
* {{l
|es
|otherword
}}
"""
    expected_text="""==Spanish==

===Noun===
{{es-noun|m}}

# {{l|en
|word}} {{q|Mexico
|Spain}} {{gloss
|a long description}}
#: {{syn|es|otherword}}
"""
    expected_flags = ["autofix"]

    run_test(orig_text,expected_text,expected_flags)


def test_get_link():

    assert fixer.get_link("blah")["2"] == "blah"
    assert fixer.get_link("{{l|es|blah}}")["2"] == "blah"
    assert fixer.get_link("{{l|es|blah}} blah")["2"] == "blah blah"
    assert fixer.get_link("blah {{l|es|blah}} blah")["2"] == "blah blah blah"
    assert fixer.get_link("{{l|es|blah}} blah  {{link|es|blah}}")["2"] == "blah blah blah"

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

    expected_flags = ['automatch_sense', 'def_duplicate_nym_defs', 'link_has_param4', 'sense_matches_multiple_defs', 'unmatched_sense']
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

    expected_flags = ['automatch_sense', 'def_duplicate_nym_defs', 'link_has_param4', 'sense_matches_multiple_defs', 'unmatched_sense']

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
    results = fixer.parse_section_items(section)
    assert results == {'': [({'1': 'es', '2': 'salvadoreño'}, None, None), ({'1': 'es', '2': 'cuscatleco'}, None, None), ({'1': 'es', '2': 'Latinoamérica'}, ['Including all Romance languages'], None), ({'1': 'es', '2': 'dale'}, ['Argentina'], None), ({'1': 'es', '2': 'viñedo'}, None, None)]}

    tag="{{syn|es|salvadoreño|cuscatleco|Latinoamérica|q3=Including all Romance languages|dale|q4=Argentina|viñedo}}"
    assert tag == fixer.make_tag("syn", results[""])

    tests = {
        "====Synonyms====\n* {{l|es|salvadoreño}}, {{l|es|cuscatleco}}" : "{{syn|es|salvadoreño|cuscatleco}}",
        "====Synonyms====\n* {{l|es|calala|g=f}} (''Nicaragua'')": "{{syn|es|calala|q1=Nicaragua}}"
    }

    for test,value in tests.items():
        res = fixer.parse_section_items(test)
        print(res)
        assert value == fixer.make_tag("syn", fixer.parse_section_items(test)[""])


def test_stripformat():

    tests = {
            " test ": "test",
            "''a''": "a",
            "''b": "''b",
            "[[c]]": "c",
            "[[d": "[[d",
            "[  'e  ']": "e",
            "[[Mexico]] ": "Mexico"
        }
    for test,value in tests.items():
        assert value == fixer.stripformat(test)

def test_parse_word():
    tests = [
        { "test": "[[Mexico]] (colloquial)", "link": {"1":"es", "2":"Mexico"}, "q": ["colloquial"], "g": None, "errors": ["missing_link"] },
        { "test": "(Mexico, colloquial)", "link": None, "q": ["Mexico", "colloquial"], "g": None, "errors": ["missing_link"] },
        { "test": "(colloquial) [[Mexico]]", "link": {"1":"es", "2":"Mexico"}, "q": ["colloquial"], "g": None, "errors": [] },
        { "test": " (colloquial)  [[Mexico]] ", "link": {"1":"es", "2":"Mexico"}, "q": ["colloquial"], "g": None, "errors": [] },
        { "test": " [[Ciudad]] de [[Mexico]] ", "link": {"1":"es", "2":"Ciudad de Mexico"}, "q": None, "g": None, "errors": [] },
        { "test": "blah [[Ciudad]]", "link": {"1":"es", "2":"blah Ciudad"}, "q": None, "g": None, "errors": [] },
        { "test": "blah", "link": {"1":"es", "2":"blah"}, "q": None, "g": None, "errors": [] },
        { "test": "{{l|es|cuscatleco}}", "link":{"1": "es", "2": "cuscatleco"}, "q":None, "g":None },
        { "test": "{{l|es|dale}} {{qualifier|Argentina}}", "link": {"1": "es", "2": "dale"}, "q":["Argentina"], "g":None},
        { "test": "{{q|Colombia|Costa Rica|Ecuador|Guatemala|Southern Mexico|Venezuela}} {{l|es|danta}}", "link": {'1': 'es', '2': 'danta'}, "q":['Colombia', 'Costa Rica', 'Ecuador', 'Guatemala', 'Southern Mexico', 'Venezuela'], "g":None},
        { "test": "See [[Thesaurus:pared]].", "link": {"1": "es", "2": "Thesaurus:pared"}, "q":None, "g":None},
        { "test": "{{l|es|pambol}} (Mexico, colloquial)", "link": {"1": "es", "2": "pambol"}, "q":["Mexico", "colloquial"], "g":None},
        { "test": "{{l|es|calala|g=f}} (''Nicaragua'')", "link": {"1": "es", "2": "calala"}, "q":["Nicaragua"], "g":None},
    ]

    for t in tests:
        fixer._flagged = {}
        assert (t["link"], t["q"], t["g"]) == fixer.parse_word(t["test"])
#        assert (t["test"], sorted(t["errors"]) == (t["test"], sorted(fixer._flagged.keys()))

#    for test,value in tests.items():
#        assert value == fixer.parse_word(test)

def test_parse_word_fails():

    tests = [
        { "test": "{{l|es|calala|g=f}} [[blah]] blah", "errors":["link_has_template_and_brackets_and_text"] }, # Mixed Links
        { "test": "{{l|es|calala|g=f}} [[blah]]", "errors":["link_has_template_and_brackets"] }, # Mixed Links
        { "test": "[[blah]] blah", "errors":["link_has_brackets_and_text"] }, # Mixed Links
        { "test": "{{l|es|calala|g=f}} blah", "errors":["link_has_template_and_text"] }, # Mixed Links
        { "test": "{{q|blah}}", "errors":["missing_link"] }, # Missing Link
        { "test": "{{l|es|calala|g=f}} {{q|blah}} (blah2)", "errors":["qualifier_text_and_template"] }, # Multiple Qualifiers
        ]

    for t in tests:
        fixer._flagged = {}
        fixer.parse_word(t["test"])
        assert sorted(t["errors"]) == sorted(fixer._flagged.keys())

    for test,results in tests:
            assert fixer.parse_word(test)

#def test_strip_templates():
#    tests = {
#        "{{l|es|pambol}} (Mexico, colloquial)": " (Mexico, colloquial)",
#        "{{l|es|pambol}} (Mexico, colloquial) {{open": " (Mexico, colloquial) {{open",
#        "{{l|es|pambol}} (Mexico, colloquial) {{open {{blah}}": " (Mexico, colloquial) {{open {{blah}}",
#    }
#
#
#    d = Definition("es", "# [[word]]")
#    for test,results in tests.items():
#        assert results == d.strip_templates(test)

#    for test,errors in tests.items():
#        fixer._flagged = {}
#        #assert value == fixer.strip_templates(test)
#        assert sorted(errors) == sorted(fixer._flagged.keys())



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


def test_template_depth():

    d = Definition("es", "# [[word1]], [[word2]]; [[word3]]")
    assert d._template_depth == 0
    d.add(" }} {{ blah }}")
    assert d._template_depth == 0
    d.add(" {{test")
    assert d._template_depth == 1
    d.add(" }} {{ blah }}")
    assert d._template_depth == 0
    d.add(" {{test{{test2{{test3{{blah}}")
    assert d._template_depth == 3
    d.add("}} }} }}")
    assert d._template_depth == 0
    d.add("}} }} }}")
    assert d._template_depth == 0



def test_extract_templates_and_patterns():

    res = fixer.extract_templates_and_patterns(["syn"], [], "test {{syn|es|blah}} test2")
    assert res["text"] == "test  test2"
    assert res["patterns"] == []
    assert len(res["templates"])
    assert res["templates"][0].get("1") == "es"
#    assert template.params() == ["es", "blah"]


def test_extract_qualifier():

    test = "{{q|q1}} (q2) (q3) {{qualifier|q4}}"
    assert ["q1", "q2", "q3", "q4"] == sorted(fixer.extract_qualifier(test)[0])

    tests = {
        "word (qualifier)",
        "(qualifier) word",
        "{{l|es|word}} {{q|qualifier}}",
        "[[word]] (qualifier)",
        "[[word]] {{qualifier|qualifier}})"
    }

    for test in tests:
        assert (test, ["qualifier"]) == (test, fixer.extract_qualifier(test)[0])


def test_extract_gloss():
    assert fixer.extract_gloss("blah {{g|g1}} blah {{gloss|g2}}")[0] == ["g1", "g2"]

