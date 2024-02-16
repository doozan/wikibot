from autodooz.fix_bare_ux import BareUxFixer

fixer = BareUxFixer()


def test_basic():

    header = """\
==Spanish==

===Noun===
{{es-head}}

# [[sense]]
"""

    test = [
       "#: ''the ux line must be completely italacized, have a '''bold''' word, and not contain wikilinks''",
       "#:: And the translation must have a '''bold''' word, start with a capital and end with punctuation."
    ]
    expected = [
       "#: {{ux|es|the ux line must be completely italacized, have a '''bold''' word, and not contain wikilinks",
       "|t=And the translation must have a '''bold''' word, start with a capital and end with punctuation.}}"
    ]
    text = header + "\n".join(test)
    expected_text = header + "\n".join(expected)
    res = fixer.process(text, "test", [], [])
    assert str(res) == expected_text


    test = [
       "#: ''the ux line must be completely italacized, have a '''bold''' word, and not contain [[wikilinks]]''",
       "#:: And the translation must have a '''bold''' word, start with a capital and end with punctuation."
    ]
    text = header + "\n".join(test)
    res = fixer.process(text, "test", [], [])
    assert str(res) == text


    test = [
       "#: '''this line is bold with no italics'''",
       "#:: And the translation must have a '''bold''' word, start with a capital and end with punctuation."
    ]

    text = header + "\n".join(test)
    res = fixer.process(text, "test", [], [])
    assert str(res) == text


    test = [
       "#: ''the ux line must be completely italacized, have a '''bold''' word, and not contain wikilinks''",
       "#:: This translation has no bold."
    ]

    text = header + "\n".join(test)
    res = fixer.process(text, "test", [], [])
    assert str(res) == text


    test = [
       "#: ''the ux line must be completely italacized, have a '''bold''' word, and not contain wikilinks''",
       "#:: This translation '''doesn't''' end with punctuation. (parenthesis doesn't count)"
    ]
    text = header + "\n".join(test)
    res = fixer.process(text, "test", [], [])
    assert str(res) == text



    test = [
       "#: ''the ux line must be completely italacized, have a '''bold''' word, and not contain wikilinks''",
       "#:: This translation '''has''' [[a link]]",
    ]
    text = header + "\n".join(test)
    res = fixer.process(text, "test", [], [])
    assert str(res) == text


    test = [
       "#: ''the ux line must be completely italacized, have a '''bold''' word, and not contain wikilinks''",
       "#:: One '''translation''' line.",
       "#:: Two '''translation''' lines is too many.",
    ]
    text = header + "\n".join(test)
    res = fixer.process(text, "test", [], [])
    assert str(res) == text



    test = [
       "#: ''the ux line must be completely italacized, have a '''bold''' word, and not contain wikilinks''",
       "#:: One '''translation''' line.",
       "#::: Translation '''with''' a child is unhandled.",
    ]
    text = header + "\n".join(test)
    res = fixer.process(text, "test", [], [])
    assert str(res) == text



    test = [
       "#: ''the ux line must be completely italacized, have a '''bold''' word, and not contain wikilinks''",
       "#:: ''Strip italics from '''translation''' line.''",
    ]
    expected = [
       "#: {{ux|es|the ux line must be completely italacized, have a '''bold''' word, and not contain wikilinks",
       "|t=Strip italics from '''translation''' line.}}"
    ]
    text = header + "\n".join(test)
    expected_text = header + "\n".join(expected)
    res = fixer.process(text, "test", [], [])
    assert str(res) == expected_text



def test_vada():

    text = """
==Swedish==

===Adverb===
{{head|sv|adverb}}

# [[what]]?
#: ''– Gör det där!''
#:: ''– Gör '''vadå'''?''
#: – Do that!
#:: – Do '''what'''?
"""

    res = fixer.process(text, "test", [], [])
    assert str(res) == text

def test_geometri():

    text = """
==Swedish==

===Noun===
{{sv-noun|c}}

# {{lb|sv|mathematics}} [[geometry]]; a specific set of rules defining the possible [[spatial]] [[relationship]]s
#: ''Genom att modifiera Euklides parallellaxiom kunde Lobatjevskij definiera en ny sorts '''geometri.'''''
#:: By modifying the [[parallel postulate]] of [[w:Euclid|Euclid]], [[w:Nikolai Ivanovich Lobachevsky|Lobachevsky]] defined a new kind of geometry.
# a [[geometry]], a [[shape]]; an item's relative [[spatial]] [[attribute]]s
#: ''När ett nytt ämne med en annan '''geometri''' ska bearbetas, utarbetas ett nytt NC-program.''
#:: When a new object with a different geometry is to be manufactured, a new CNC program is developed.\
"""

    expected = """
==Swedish==

===Noun===
{{sv-noun|c}}

# {{lb|sv|mathematics}} [[geometry]]; a specific set of rules defining the possible [[spatial]] [[relationship]]s
#: ''Genom att modifiera Euklides parallellaxiom kunde Lobatjevskij definiera en ny sorts '''geometri.'''''
#:: By modifying the [[parallel postulate]] of [[w:Euclid|Euclid]], [[w:Nikolai Ivanovich Lobachevsky|Lobachevsky]] defined a new kind of geometry.
# a [[geometry]], a [[shape]]; an item's relative [[spatial]] [[attribute]]s
#: {{ux|sv|När ett nytt ämne med en annan '''geometri''' ska bearbetas, utarbetas ett nytt NC-program.
|t=When a new object with a different geometry is to be manufactured, a new CNC program is developed.}}\
"""

    res = fixer.process(text, "test", [], [])
    assert str(res) == expected
