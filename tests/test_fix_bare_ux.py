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
