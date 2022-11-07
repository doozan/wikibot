import pytest

from ..list_forms_with_data import check_page


def test_chimba():

    text = """
==Spanish==

===Pronunciation===
{{es-IPA}}

===Adjective===
{{head|es|adjective form}}

# {{adj form of|es|chimbo||f|s}}; [[crappy]], [[fake]]

===Noun===
{{es-noun|f}}

# {{lb|es|Colombia|colloquial}} [[enjoyable]], [[pleasurable]], [[attractive]] thing
#: {{uxi|es|Ese carro está muy '''chimba'''.|That car is very '''cool'''.}}
#: {{uxi|es|El computador que trajo es una '''chimba'''.|The computer he brought is pretty '''cool'''.}}

====Usage notes====
Equivalent to colloquial English ''[[cool]]''. It can be used with the verbs {{m|es|ser}} and {{m|es|estar||to be}}.

===Adverb===
{{es-adv}}

# {{lb|es|Colombia|colloquial}} [[properly]], [[pleasantly]]
#: {{ux|es|Esta me trata mucho más '''chimba''' que la otra.|t=This girl treats me way more '''pleasantly''' than the other one.}}

====Related terms====
[[chimbita]]

===Further reading===
* {{R:DRAE}}
"""

    title = "chimba"

    log = []
    def logger(*args):
        log.append(args)

    check_page(title, text, logger)

    assert any('has_text_outside_form' in entry for entry in log)
