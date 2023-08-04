from autodooz.fix_quote_with_bare_passage import QuoteFixer

fixer = QuoteFixer()

def test_merge_passage_and_translation():

    text = """\
==German==

===Noun===
#* {{quote-book|de|author=test|title=bar}}
#*: line 1
#*: line 2
#*:: trans1
#*:: trans2
"""

    expected = """\
==German==

===Noun===
#* {{quote-book|de|author=test|title=bar
|passage=line 1<br>line 2
|translation=trans1<br>trans2}}\
"""

    res = fixer.process(text, "test", [])
    print([res])
    assert res == expected


def test_merge_ux():

    text = """\
==German==

===Noun===
#* {{quote-book|de|author=test|title=bar}}
#*: {{ux|de|passage_text|translation_text|tr=test}}
"""

    expected = """\
==German==

===Noun===
#* {{quote-book|de|author=test|title=bar
|passage=passage_text
|translation=translation_text
|transliteration=test}}\
"""

    res = fixer.process(text, "test", [])
    print([res])
    assert res == expected

