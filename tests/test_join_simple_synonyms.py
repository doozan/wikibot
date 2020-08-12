from join_simple_synonyms import SynFixer

synfixer = SynFixer("Spanish", "es")

def test_parse_section_items():

    section="""====Synonyms====
* {{l|es|salvadoreño}}, {{l|es|cuscatleco}}
* {{qualifier|Including all Romance languages}} {{l|es|Latinoamérica}}
* {{l|es|dale}} {{qualifier|Argentina}}
* {{l|es|viñedo|g=m}}
"""
    tag="{{syn|es|salvadoreño|cuscatleco|Latinoamérica|q3=Including all Romance languages|dale|q4=Argentina|viñedo}}"
    assert tag == synfixer.make_tag("syn", synfixer.parse_section_items(section))

    tests = {
        "====Synonyms====\n* {{l|es|salvadoreño}}, {{l|es|cuscatleco}}" : "{{syn|es|salvadoreño|cuscatleco}}",
        "====Synonyms====\n* {{l|es|calala|g=f}} (''Nicaragua'')": "{{syn|es|calala|q1=Nicaragua}}"
    }

    for test,value in tests.items():
        res = synfixer.parse_section_items(test)
        print(res)
        assert value == synfixer.make_tag("syn", synfixer.parse_section_items(test))


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


def test_strip_templates():
    tests = {
        "{{l|es|pambol}} (Mexico, colloquial)": " (Mexico, colloquial)"
    }

    for test,value in tests.items():
        assert value == synfixer.strip_templates(test)


def test_get_item_from_text():
    tests = {
        "(Mexico, colloquial)": (None, ["Mexico", "colloquial"], None),
        "[[Mexico]] (colloquial)": ({ "1": "es", "2": "Mexico" }, ["colloquial"], None),
    }

    for test,value in tests.items():
        assert value == synfixer.get_item_from_text(test)

