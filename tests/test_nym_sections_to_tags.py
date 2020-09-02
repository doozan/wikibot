import pytest
from nym_sections_to_tags import NymSectionToTag

fixer = NymSectionToTag("Spanish", "es")

def run_test(orig_text, expected_text, expected_flags):

    fixer.clear_problems()
    new_text = fixer.run_fix(orig_text, [], "test")
    assert orig_text == new_text
    assert sorted(expected_flags) == sorted(fixer.problems.keys())

    fixer.clear_problems()
    new_text = fixer.run_fix(orig_text, expected_flags, "test", sections=["Synonyms","Antonyms","Hyponyms"])
    assert new_text == expected_text

def test():

    orig_text = """==Spanish==

===Noun===
{{es-noun}}

# [[word]]

====Synonyms====
* {{l|es|gabacho}} {{qualifier|Spain, Mexico}}
* {{l|es|guiri}} {{qualifier|Spain}}
"""
    expected_text = """==Spanish==

===Noun===
{{es-noun}}

# [[word]]
#: {{syn|es|gabacho|q1=Spain, Mexico|guiri|q2=Spain}}"""

    expected_flags = ["autofix"]
    run_test(orig_text, expected_text, expected_flags)

def test_multi_defs():

    orig_text = """==Spanish==

===Noun===
{{es-noun}}

# [[word1]]
# [[word2]]

====Synonyms====
* {{l|es|syn1}}
"""
    expected_text = """==Spanish==

===Noun===
{{es-noun}}

# [[word1]]
#: {{syn|es|syn1}}
# [[word2]]"""

    expected_flags = ["nym_matches_multiple_defs"]
    run_test(orig_text, expected_text, expected_flags)

def test_multi_defs2():

    orig_text = """==Spanish==

===Noun===
{{es-noun}}

# {{l|en|word1}}
# [[word2]]

====Synonyms====
* {{l|es|syn1}}
"""
    expected_text = """==Spanish==

===Noun===
{{es-noun}}

# {{l|en|word1}}
#: {{syn|es|syn1}}
# [[word2]]"""

    expected_flags = ["nym_matches_multiple_defs"]
    run_test(orig_text, expected_text, expected_flags)

def test_multi_nomerge():

    orig_text = """==Spanish==

===Noun===
{{es-noun}}

# {{l|en|word1}}
# [[word2]]

====Synonyms====
* {{sense|sense1}} {{l|es|syn1}}
* {{sense|sense2}}  {{l|es|syn2}}
"""
    expected_text = """==Spanish==

===Noun===
{{es-noun}}

# {{l|en|word1}}
#: {{syn|es|syn1}} <!-- FIXME, MATCH SENSE: 'sense1' -->
#: {{syn|es|syn2}} <!-- FIXME, MATCH SENSE: 'sense2' -->
# [[word2]]"""

    expected_flags = ["nym_matches_multiple_defs", "nym_matches_no_defs"]
    run_test(orig_text, expected_text, expected_flags)

def test_gloss():

    orig_text = """==Spanish==

===Noun===
{{es-noun}}

# [[word1]]

====Synonyms====
* {{l|es|syn1}} {{gloss|gloss as qualifier}}
"""
    expected_text = """==Spanish==

===Noun===
{{es-noun}}

# [[word1]]
#: {{syn|es|syn1|q1=gloss as qualifier}}"""

    expected_flags = ["using_gloss_as_qualifier"]
    run_test(orig_text, expected_text, expected_flags)



def test_brocolli():
    entry_text="""==Spanish==
{{wikipedia|lang=es}}

===Etymology===
Alteration of {{m|es|bróculi}}.

===Pronunciation===
* {{es-IPA}}

===Noun===
{{es-noun|m|brécoles}}

# [[broccoli]]

====Synonyms====
* {{l|es|brócoli}}
* {{l|es|bróculi}}

===Further reading===
* {{R:DRAE 2001}}"""

    lang_entry = fixer.get_language_entry(entry_text)
    assert lang_entry == entry_text

def test_fix_subsection():
    orig_text = """==Spanish==

===Noun===
{{es-noun}}

# [[word1]]

====Synonyms====
* {{l|es|syn1}}

=====Subsection=====
* blah

======Sub-Subsection======
* blah

{{other stuff}}

=====Subsection2=====
* blah

=====Subsection3=====
* blah

"""
    expected_text = """==Spanish==

===Noun===
{{es-noun}}

# [[word1]]
#: {{syn|es|syn1}}

=====Subsection=====
* blah

======Sub-Subsection======
* blah

{{other stuff}}

=====Subsection2=====
* blah

=====Subsection3=====
* blah"""

    expected_flags = ["autofix_nym_section_has_subsections", "unexpected_section"]
    run_test(orig_text, expected_text, expected_flags)


def test_lang_parser():
    pre_text="""====Declension====
{{sh-decl-noun
|idèāl|ideali
|ideála|ideala
|idealu|idealima
|ideal|ideale
|ideale|ideali
|idealu|idealima
|idealom|idealima
}}

----

"""
    spanish_text="""
==Spanish==

===Etymology===
From {{der|es|la|ideālis}}.

===Pronunciation===
* {{es-IPA}}

===Adjective===
{{es-adj|pl=ideales}}

# {{l|en|ideal}}

====Derived terms====
{{der2|es|idealizar|idealmente}}

===Noun===
{{es-noun|m}}

# {{l|en|ideal}}"""

    post_text="""

----

==Swedish==

===Pronunciation===
* {{audio|sv|Sv-ideal.ogg|audio}}

===Noun===
{{sv-noun|n}}

# [[#English|ideal]]; perfect standard
# {{lb|sv|mathematics}} [[#English|ideal]]; special subsets of a [[ring]]

====Declension====
{{sv-infl-noun-n-zero}}

===Anagrams===
* {{anagrams|sv|a=adeil|ilade}}

----

==Turkish==

"""
    entry_text = pre_text+spanish_text+post_text

    lang_entry = fixer.get_language_entry(entry_text)
    assert lang_entry == spanish_text



def test_lang_parser():
    pre_text="""====Declension====
{{sh-decl-noun
|idèāl|ideali
|ideála|ideala
|idealu|idealima
|ideal|ideale
|ideale|ideali
|idealu|idealima
|idealom|idealima
}}

----

"""
    spanish_text="""
==Spanish==

===Etymology===
From {{der|es|la|ideālis}}.

===Pronunciation===
* {{es-IPA}}

===Adjective===
{{es-adj|pl=ideales}}

# {{l|en|ideal}}

====Derived terms====
{{der2|es|idealizar|idealmente}}

===Noun===
{{es-noun|m}}

# {{l|en|ideal}}"""

    entry_text = pre_text+spanish_text

    lang_entry = fixer.get_language_entry(entry_text)
    assert lang_entry == spanish_text



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

