from ..section_to_links import extract_titles, get_links, section_to_links, brackets_to_links
import mwparserfromhell as mwparser
import enwiktionary_sectionparser as sectionparser


def test_brackets_to_links():

    assert brackets_to_links("en", "[[test]]") == "{{l|en|test}}"
    assert brackets_to_links("en", "[[test#English]]") == "{{l|en|test}}"
    assert brackets_to_links("en", "[[test]]ing") == "{{l|en|test|alt=testing}}"
    assert brackets_to_links("en", "[[test|testing]]") == "{{l|en|test|alt=testing}}"
    assert brackets_to_links("en", "[[test|testing]]abc") == "{{l|en|test|alt=testingabc}}"  # matches wiki behavior
    assert brackets_to_links("en", "[[foo]], [[bar]]") == "{{l|en|foo}}, {{l|en|bar}}"
    assert brackets_to_links("en", "[[foo]][[bar]]") == "{{l|en|foo}}{{l|en|bar}}"
    assert brackets_to_links("en", "[[foo]]test[[bar]]") == "{{l|en|foo|alt=footest}}{{l|en|bar}}"

def test_extract_titles():

    page_text = """\
==English==

===Synonyms===
* [[test]] {{q|post}}
* [[test2]]
* {{l|en|test3}}
"""
    section = sectionparser.parse(page_text, "foo").filter_sections()[1]


    assert extract_titles(section, "* {{q|test}}") == (("test",), "")
    assert extract_titles(section, "*    {{qual|test}}    ") == (("test",), "")
    assert extract_titles(section, "* {{q|test|test2}}") == ((None,), "* {{q|test|test2}}")

    assert extract_titles(section, "** {{q|test}}")[0] == (None,)
    assert extract_titles(section, "{{q|test}}")[0] == ("test",)

    assert extract_titles(section, "{{sense|test}}")[0] == ("test",)

    assert extract_titles(section, "* {{sense|test}} foo, bar") == (("test",), " foo, bar")

    assert extract_titles(section, "* {{q|test}}: foo, bar")[0] == ("test",)
    assert extract_titles(section, "* {{q|test}} foo, bar")[0] == (None,)

    assert extract_titles(section, "{{col3|en|title=test|foo|bar}}") == (('test',), '{{col3|en|foo|bar}}')


    assert extract_titles(section, "* {{s|island in Hong Kong}} {{l|en|Aberdeen Island}}") == (('island in Hong Kong',), ' {{l|en|Aberdeen Island}}')
    assert extract_titles(section, "* {{sense|test1|test2}} foo, bar") == (("test1", "test2"), " foo, bar")

    #assert extract_titles(section, "{{der-top|test}}") == "test"
    #assert extract_titles(section, "{{der-top}}") == ""


def test_get_links():

    page_text = """\
==English==

===Synonyms===
* [[test]] {{q|post}}
* [[test2]]
* {{l|en|test3}}
"""
    section = sectionparser.parse(page_text, "foo").filter_sections()[1]
    test = lambda x: get_links("en", section, x)

    assert test("* [[test]]") == ["test"]
    assert test("[[test]]") == ["test"]
    assert test("[[test]]ed") == ["test<alt:tested>"]
    assert test("[[test]], [[test2]]") == ["test", "test2"]

    assert test("[[test]], see also [[Thesaurus:test]]") == ["test", "Thesaurus:test"]

    assert test("* {{l|fi|[[Ecuadorin]] [[tasavalta]]}} {{q|official name}}") == ['[[Ecuadorin]] [[tasavalta]]<qq:official name>']


    assert test("* {{q|foo}} [[test]] {{q|bar}}") == ["test<q:foo><qq:bar>"]

    assert test("* {{taxlink|Elater oculatus|species}} {{q|[[basionym]]}}") == ['{{taxlink|Elater oculatus|species}}<qq:[[basionym]]>']

    # ambiguous qualifiers
    assert test("* {{q|foo}} [[test]], [[test2]]") == None
    assert test("* [[test]], [[test2]] {{q|foo}}") == None

    assert test("* {{l|en|link|alttext}}") == ["link<alt:alttext>"]



def test_section_to_links2():

    page_text = """\
==English==

===Synonyms===
* [[test]] {{q|post}}
* [[test2]]
* {{l|en|test3}}
"""
    section = sectionparser.parse(page_text, "foo").filter_sections()[1]
    #pos = sectionparser.parse_pos(section)

    assert section_to_links(section) == {None: ["test<qq:post>", "test2", "test3"]}



    page_text = """\
==English==

===Synonyms===
* {{sense|sense1}} {{l|en|foo}}, {{l|en|bar}}
* {{sense|sense2}} {{l|en|bar}}, {{l|en|foo}}
"""
    section = sectionparser.parse(page_text, "foo").filter_sections()[1]
    #pos = sectionparser.parse_pos(section)

    assert section_to_links(section) == { 'sense1': ['foo', 'bar'], 'sense2': ['bar', 'foo'], }



    page_text = """\
==English==

===Synonyms===
{{sense|sense1}}
* {{l|en|foo}}
* {{l|en|bar}}

{{sense|sense2}}
* {{l|en|bar}}, {{l|en|foo}}
"""
    section = sectionparser.parse(page_text, "foo").filter_sections()[1]
    #pos = sectionparser.parse_pos(section)

    assert section_to_links(section) == { 'sense1': ['foo', 'bar'], 'sense2': ['bar', 'foo'], }



    page_text = """\
==English==

===Synonyms===
{{col3|en|
|'cue
|cue
|'que
|que
}}
"""
    section = sectionparser.parse(page_text, "foo").filter_sections()[1]
    #pos = sectionparser.parse_pos(section)

    assert section_to_links(section) == {None: ["'cue", 'cue', "'que", 'que']}





    page_text = """\
==English==

===Synonyms===
* {{qualifier|US}} {{l|en|Civil War}}
* {{qualifier|US, especially Southern US}} {{l|en|War Between the States}}
* {{qualifier|US, almost exclusively Southern US}} {{l|en|War of Northern Aggression}}
* {{qualifier|US, chiefly Northern US}} {{l|en|War of the Rebellion}}
* {{qualifier|US, chiefly Northern US}} {{l|en|Great Rebellion}}
* {{qualifier|Outside the US}} {{l|en|Secession War}}
* {{l|en|U.S. Civil War}}
"""
    section = sectionparser.parse(page_text, "foo").filter_sections()[1]
    #pos = sectionparser.parse_pos(section)

    assert section_to_links(section) == {None: ['Civil War<q:US>', 'War Between the States<q:US, especially Southern US>', 'War of Northern Aggression<q:US, almost exclusively Southern US>', 'War of the Rebellion<q:US, chiefly Northern US>', 'Great Rebellion<q:US, chiefly Northern US>', 'Secession War<q:Outside the US>', 'U.S. Civil War']}



    page_text = """\

==English==

====Synonyms====
* {{l|en|Oldowan}}
* {{qualifier|dated}} [[Chellian]]<ref>{{R:American Heritage Dictionary|edition=1971|page=1}}</ref>
* {{qualifier|nowadays}} [[Lower Acheulean]]<ref name=oxf>{{R:OCD2|page=1}}</ref>
* {{l|en|Chellean}}<ref name=RH>{{R:RHCD|page=1}}</ref>
"""
    section = sectionparser.parse(page_text, "foo").filter_sections()[1]
    #pos = sectionparser.parse_pos(section)

    assert section_to_links(section) == None




    # Fail on duplicate labels (military equipment)
    page_text = """\

==English==

====Synonyms====
* {{sense|auxiliary parts|military equipment}} {{l|de|Armierung}}
* {{sense|military equipment}} {{l|de|Kriegsgerät}}
* {{sense|faucet or valve}} {{l|de|Hahn}}, {{l|de|Kran}}, {{l|de|Wasserhahn}}, {{l|de|Wasserkran}}
"""
    section = sectionparser.parse(page_text, "foo").filter_sections()[1]
    #pos = sectionparser.parse_pos(section)

    assert section_to_links(section) == None






