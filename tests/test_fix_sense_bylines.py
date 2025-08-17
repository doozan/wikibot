from autodooz.fix_sense_bylines import BylineFixer
import enwiktionary_sectionparser as sectionparser

fixer = BylineFixer()

def test_fix_nym():


    tests = [
        ["{{syn|de|Schulterzucken}} {{i|not vulgar}}", "{{syn|de|Schulterzucken<qq:not vulgar>}}"],
        ["{{syn|mul|Tanagra albo-frenatus}} {{q|deprecated}}", "{{syn|mul|Tanagra albo-frenatus<qq:deprecated>}}"],
        ["{{syn|nl|Vossendarp}} (''Carnival nickname'')", "{{syn|nl|Vossendarp<qq:Carnival nickname>}}"],
        ["{{syn|tr|dansöz}} (female)", "{{syn|tr|dansöz<qq:female>}}"],
        ["{{syn|igl|ẹ́ñwu-anẹ̀}} ''(euphemistic)''", "{{syn|igl|ẹ́ñwu-anẹ̀<qq:euphemistic>}}"],
        ["{{syn|io|rubra}} {{qualifier|archaic}}", "{{syn|io|rubra<qq:archaic>}}"],
        ["{{syn|en|Fox Harbour}} {{q|''historical''}}", "{{syn|en|Fox Harbour<qq:historical>}}"],
        ["{{syn|pl|niesamowity|niezwykły|wspaniały}}, {{syn|pl|Thesaurus:dobry}}", "{{syn|pl|niesamowity|niezwykły|wspaniały|Thesaurus:dobry}}"],

#        ["{{syn|de|nym1}}, [[nym2]], [[nym3]]", "{{syn|de|nym1|nym2|nym3}}"],
    ]


    for text, expected in tests:

        page_text = f"""\
===Noun===
{{head|en|noun}}

# test
#: {text}
"""

        page_expected = f"""
===Noun===
{{head|en|noun}}

# test
#: {expected}
"""

        section = next(sectionparser.parse(page_text, "foo").ifilter_sections())
        pos = sectionparser.parse_pos(section)

        fixer.validate_sense_list(pos.senses, section)
        new_pos_text = str(pos)
        section.content_wikilines = [new_pos_text]

        assert(str(section) == page_expected)


text = """
# [[#English|on]], [[in]], [[at]], [[among]] {{+obj|ang|dat|or|ins}}
: {{ux|ang|'''On''' þæm huse|'''In''' the house}}
# [[#English|on]], [[during]] {{+obj|ang|acc}}
: {{ux|ang|'''On''' midne winter|'''In''' mid-winter}}
"""

expected = """
# [[#English|on]], [[in]], [[at]], [[among]] {{+obj|ang|dat|or|ins}}
#: {{ux|ang|'''On''' þæm huse|'''In''' the house}}
# [[#English|on]], [[during]] {{+obj|ang|acc}}
#: {{ux|ang|'''On''' midne winter|'''In''' mid-winter}}
"""


text = """
# [[stone]]
# [[money]]
{{ux|aer|Arelhe akangkeme anthurre '''apwerte''' akngerrele impeke.}}
"""

expected = """
# [[stone]]
# [[money]]
#: {{ux|aer|Arelhe akangkeme anthurre '''apwerte''' akngerrele impeke.}}
"""


text = """
# [[goods|Goods]] or [[service]]s that are for [[sale]].
#: ''The square was filled with booths, with vendors offering their '''wares'''.''
"""

expected = """
# [[goods|Goods]] or [[service]]s that are for [[sale]].
#: {{ux|The square was filled with booths, with vendors offering their '''wares'''.}}
"""



def test_add_missing_rfdef():

    # No change normal def
    text = """\
==English==

===Noun===
{{head|en|noun}}

# def
"""

    expected = text

    summary = []
    res = fixer.process(text, "page", summary)
    assert res == expected




    # Add missing rfdef
    text = """\
==English==

===Noun===
{{head|en|noun}}
"""

    expected = """\
==English==

===Noun===
{{head|en|noun}}

# {{rfdef|en}}\
"""

    summary = []
    res = fixer.process(text, "page", summary)
    assert res == expected



    # Don't add rfdef for templates that generate def lines
    text = """\
==Arabic==

===Noun===
{{ar-verb form|ألفى<IV>}}
"""

    expected = text

    summary = []
    res = fixer.process(text, "page", summary)
    assert res == expected




def test_merge_nyms():

    text = """\
==English==

===Noun===
{{en-noun}}

# {{lb|en|dated|now|offensive}} An Aboriginal person from [[Australia]] (descending from, or a member of, one of the [[indigenous]] [[people]](s) before British colonisation), [[Aboriginal]] [[Australian]].

====Synonyms====
* {{l|en|Aboriginal}}
* {{l|en|Aboriginal people}}
* {{l|en|Aboriginal Australian}} {{q|neutral term}}
"""

    expected = """\
==English==

===Noun===
{{en-noun}}

# {{lb|en|dated|now|offensive}} An Aboriginal person from [[Australia]] (descending from, or a member of, one of the [[indigenous]] [[people]](s) before British colonisation), [[Aboriginal]] [[Australian]].
#: {{syn|en|Aboriginal|Aboriginal people|Aboriginal Australian<qq:neutral term>}}\
"""

    summary = []
    res = fixer.process(text, "page", summary)
    assert res == expected



    text = """\
==English==

===Noun===
{{en-noun}}

# test
#: {{syn|en|syns}}
#: {{mero|en|mero}}

====Antonyms====
 * [[foo]]
"""

    expected = """\
==English==

===Noun===
{{en-noun}}

# test
#: {{syn|en|syns}}
#: {{ant|en|foo}}
#: {{mero|en|mero}}\
"""

    summary = []
    res = fixer.process(text, "page", summary)
    assert res == expected


def test_no_merge_nyms():

    text = """\
==Latin==

===Noun===
{{la-noun|aequālitās<3>}}

# [[equality]], [[similarity]], [[uniformity]]
# [[political]] equality
# equality of [[age]]
# [[evenness]], [[levelness]]

====Synonyms====
* {{sense|equality}} {{l|la|aequābilitās}}\
"""

    expected = text

    summary = []
    res = fixer.process(text, "page", summary)
    assert res == expected


    text = """\
==Spanish==

====Noun====
{{es-noun|mf}}

# [[baby]]
#: {{syn|es|guagua<q:Andes>|nene|nena}}

=====Synonyms=====
See also [[Thesaurus:bebé]].\
"""

    expected = text

    summary = []
    res = fixer.process(text, "page", summary)
    assert res == expected



    text = """\
==Portuguese==

===Conjunction===
{{head|pt|conjunction}}

# {{senseid|pt|noun clause connector}} [[that]] {{gloss|connecting noun clause}}
# {{senseid|pt|introduces a result}} [[that]] {{gloss|introducing the result of the main clause}}
# {{senseid|pt|than}} [[than]] {{gloss|used in comparisons, to introduce the basis of comparison}}
# {{senseid|pt|because}} {{lb|pt|only in subordinate clauses}} [[seeing as]]; [[since]]; [[for]]; [[because]] {{gloss|introduces explanatory clause}}
#: {{syn|pt|porque}}
# {{lb|pt|only in subordinate clauses}} [[and]] {{gloss|indicating the consequences of an action, often threateningly}}

====Synonyms====
* {{sense|than}} {{l|pt|do que}}
* {{sense|because}} {{l|pt|por causa que}}, {{l|pt|porque}}\
"""

    expected = text

    summary = []
    res = fixer.process(text, "page", summary)
    assert res == expected

