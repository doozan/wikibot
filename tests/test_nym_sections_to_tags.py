import pytest
from nym_sections_to_tags import NymSectionToTag

fixer = NymSectionToTag("Spanish", "es")

def run_test(orig_text, expected_text, expected_flags):

    fixer._flagged = {}
    new_text = fixer.run_fix(orig_text, [], "test")
    assert orig_text == new_text
#    assert sorted(expected_flags) == sorted(fixer._flagged.keys())

    fixer._flagged = {}
    new_text = fixer.run_fix(orig_text, expected_flags, "test", sections=["Synonyms","Antonyms","Hyponyms"])
    assert expected_text == new_text


def xtest_run_fix_viste():

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


def xtest_open_templates():

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


def xtest_sense_match_same_level():

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


def xtest_run_fix_complex():

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


def xtest_run_fix_complex2():

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


def xtest_sense_match_senseid():

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



def xtest_sense_match_def():

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

