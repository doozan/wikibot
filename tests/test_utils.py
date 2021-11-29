import re
from ..utils import FULL_PAGE, regex_lang, split_body_and_tail


def test_get_full_page():

    text = """
==Asturian==

===Pronoun===
{{head|ast|pronoun|g=m-p}}

# {{l|en|you}} {{gloss|the group being addressed}}

====Synonyms====
* {{sense|subject pronoun: the group being addressed}} {{l|ast|vós}}

----

==Spanish==

===Noun===
# test

----

==Thai==

blah
"""

    pattern = FULL_PAGE
    m = re.search(pattern, text)

    assert len(m.groups()) == 0
    assert m.group(0) == text


def test_get_lang():

    texts = {}
    texts["en"] = """==English==

===Noun===
# blah"""

    texts["ast"] = """
==Asturian==

===Pronoun===
{{head|ast|pronoun|g=m-p}}

# {{l|en|you}} {{gloss|the group being addressed}}

====Synonyms====
* {{sense|subject pronoun: the group being addressed}} {{l|ast|vós}}"""

    texts["es"] = """
==Spanish==

===Noun===
# test"""

    texts["th"] = """
==Thai==

blah"""

    text = f"""\
{texts['en']}

----

{texts['ast']}
{texts['es']}
----

{texts['th']}\
"""

    print(text)

    for lang in ["en", "ast", "es", "th"]:
        pattern = regex_lang(lang)
        m = re.search(pattern, text)
        print("matching", lang)
        if not m:
            raise ValueError("no match")

        assert m.group('body').rstrip() == texts[lang]
        body, tail = split_body_and_tail(m)
        assert m.group('full') == m.group('body') + m.group('end')



def test_split_body_and_tail():

    text = """
==Spanish==

===Noun===
# test

----"""
    res_tail = "\n----"

    pattern = regex_lang("es")
    m = re.search(pattern, text)
    body, tail = split_body_and_tail(m)
    assert body+tail == text
    assert tail == res_tail


def test_split_body_and_tail2():

    text = """
==Spanish==

===Noun===
# test

{{c}}

[[Category:test]]

----"""

    res_tail = """
{{c}}

[[Category:test]]

----"""

    pattern = regex_lang("es")
    m = re.search(pattern, text)
    body, tail = split_body_and_tail(m)
    assert body+tail == text
    assert tail == res_tail


def test_split_body_and_tail3():

    text = """
==Spanish==

===Noun===
# test

{{cats are fuzzy}}
{{c}}
{{cln}}
{{top}} {{topic}}
----"""
    res_tail = '{{c}}\n{{cln}}\n{{top}} {{topic}}\n----'

    pattern = regex_lang("es")
    m = re.search(pattern, text)
    body, tail = split_body_and_tail(m)
    assert body+tail == text
    assert tail == res_tail

