#
# Copyright (c) 2020 Jeff Doozan
#
# This is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import pytest
from nym_sections_to_tags import NymSectionToTag

fixer = NymSectionToTag("Spanish", "es")

def run_test(orig_text, expected_text, expected_flags, title="test"):

    fixer.clear_problems()
    new_text = fixer.run_fix(orig_text, [], title)
    assert orig_text == new_text
    assert sorted(expected_flags) == sorted([ x for x in fixer._problems.keys() if not x.startswith("_") and x != "partial_fix" ])

    fixer.clear_problems()
    new_text = fixer.run_fix(orig_text, expected_flags, title+"-fix", sections=["Synonyms","Antonyms","Hyponyms"])
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
#: {{syn|es|syn1}} <!-- FIXME, MATCH SENSE: '' -->
# [[word2]]"""

    expected_flags = ["nymsense_matches_multiple_defs"]
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
#: {{syn|es|syn1}} <!-- FIXME, MATCH SENSE: '' -->
# [[word2]]"""

    expected_flags = ["nymsense_matches_multiple_defs"]
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

    expected_flags = ["nymsense_matches_multiple_defs", "nymsense_matches_no_defs"]
    run_test(orig_text, expected_text, expected_flags)

def test_gloss():

    orig_text = """==Spanish==

===Noun===
{{es-noun}}

# [[word1]]

====Synonyms====
* {{sense|word1}} {{l|es|syn1}} {{gloss|gloss as qualifier}}
"""
    expected_text = """==Spanish==

===Noun===
{{es-noun}}

# [[word1]]
#: {{syn|es|syn1|q1=gloss as qualifier}}"""

    expected_flags = ["automatch_sense", "using_gloss_as_qualifier"]
    new_text = fixer.run_fix(orig_text, expected_flags, "test-fix", sections=["Synonyms","Antonyms","Hyponyms"])
    assert expected_text == new_text

def test_gloss_as_sense():

    orig_text = """==Spanish==

===Noun===
{{es-noun}}

# [[word1]]

====Synonyms====
* {{gloss|word1}} {{l|es|syn1}}
"""
    expected_text = """==Spanish==

===Noun===
{{es-noun}}

# [[word1]]
#: {{syn|es|syn1}}"""

    expected_flags = ["all"]
    #run_test(orig_text, expected_text, expected_flags)
    new_text = fixer.run_fix(orig_text, expected_flags, "test-fix", sections=["Synonyms","Antonyms","Hyponyms"])
    assert expected_text == new_text



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

    expected_flags = ["autofix_nymsection_has_subsections", "unexpected_section"]
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
    expected_flags = ['def_hashcolon_is_not_nym', 'has_nymsection_at_word_level', 'use_nymsection_from_word_level']

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
    expected_flags = ["has_nymsection_at_word_level", "use_nymsection_from_word_level", "automatch_senseid"]

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


def test_sense_match_multi_def():

    orig_text="""==Spanish==

===Noun===
{{es-noun|m}}

# [[word1]], blah word2 blah
# [[word2]]
# [[word3]]

====Synonyms====
* {{sense|word2}} {{l|es|syn1}}
"""
    expected_text="""==Spanish==

===Noun===
{{es-noun|m}}

# [[word1]], blah word2 blah
#: {{syn|es|syn1}} <!-- FIXME, MATCH SENSE: 'word2' -->
# [[word2]]
# [[word3]]"""

    expected_flags = ["automatch_sense", 'both_nym_line_and_section', "nymsense_matches_multiple_defs"]

    run_test(orig_text,expected_text,expected_flags)



def test_sense_match_multi_def():

    orig_text="""==Spanish==

===Noun===
{{es-noun|m}}

# {{lb|es|Chile|Argentina}} public [[bus]]
# {{lb|es|Mexico}} [[minibus]]

====Synonyms====
* {{l|es|ómnibus}}
* {{sense|Argentina}} {{l|es|colectivo}}
* {{sense|Mexico}} {{l|es|pesero}}, {{l|es|combi}}
"""
    expected_text="""==Spanish==

===Noun===
{{es-noun|m}}

# {{lb|es|Chile|Argentina}} public [[bus]]
#: {{syn|es|ómnibus}} <!-- FIXME, MATCH SENSE: '' -->
#: {{syn|es|colectivo}}
# {{lb|es|Mexico}} [[minibus]]
#: {{syn|es|pesero|combi}}"""

    expected_flags = ["automatch_sense", "nymsense_matches_multiple_defs"]

    run_test(orig_text,expected_text,expected_flags, "test_multi")

def test_sense_match_multi_words():

    orig_text="""==Spanish==

===Noun===
{{es-noun|m}}

# {{l|en|drama}} {{gloss|genre in art, film, theatre and literature or a work of said genre}}
# {{l|en|drama}}, [[tragedy]], [[plight]] {{gloss|quality of intense or high emotion or situation of enormous gravity that heightens such emotions}}
# {{l|en|drama}} {{gloss|theatre studies}}
# [[play]] {{gloss|work of theatre}}
# [[big deal]], [[fuss]], [[scene]]

====Synonyms====
* {{sense|play}} {{l|es|obra}}
* {{sense|big deal, fuss}} {{l|es|gran}} {{l|es|cosa}}, {{l|es|escándalo}}, {{l|es|escena}}
"""

    expected_text="""==Spanish==

===Noun===
{{es-noun|m}}

# {{l|en|drama}} {{gloss|genre in art, film, theatre and literature or a work of said genre}}
# {{l|en|drama}}, [[tragedy]], [[plight]] {{gloss|quality of intense or high emotion or situation of enormous gravity that heightens such emotions}}
# {{l|en|drama}} {{gloss|theatre studies}}
# [[play]] {{gloss|work of theatre}}
#: {{syn|es|obra}}
# [[big deal]], [[fuss]], [[scene]]
#: {{syn|es|gran cosa|escándalo|escena}}"""

    expected_flags = ["automatch_sense", "link_is_complicated"]

    run_test(orig_text,expected_text,expected_flags, "test_multiword")


def test_sense_match_multi_words2():

    orig_text="""==Spanish==

===Noun===
{{es-noun|m}}

# [[gem]]
# {{lb|es|botany}} [[bud]], [[shoot]]

====Synonyms====
* {{sense|bud|shoot}} {{l|es|botón|g=m}}, {{l|es|yema|g=f}}
"""

    expected_text="""==Spanish==

===Noun===
{{es-noun|m}}

# [[gem]]
# {{lb|es|botany}} [[bud]], [[shoot]]
#: {{syn|es|botón|yema}}"""

    expected_flags = ["automatch_sense"]

    run_test(orig_text,expected_text,expected_flags, "test_multiword")

def xtest_sense_match_multi_wordsxxx():

    orig_text="""==Spanish==

===Noun===
{{es-noun|m}}

# [[gem]]
# {{lb|es|botany}} [[bud]], [[shoot]]

====Synonyms====
* {{l|es|buen rollo}} {{qualifier|Argentina|Chile|Mexico|Spain}}
* {{l|es|buena onda}} {{qualifier|Mexico}}
* {{l|es|chévere}} {{qualifier|Caribbean|Venezuela|Peru}}
* {{l|es|genial}}
* {{l|es|chido}} {{qualifier|Mexico}}
* {{l|es|padre}} {{qualifier|Mexico}}
* {{l|es|diacachimba}} {{qualifier|Nicaragua}}
* {{l|es|diaverga}} {{qualifier|Nicaragua}}
"""

    expected_text="""==Spanish==

===Noun===
{{es-noun|m}}

# [[gem]]
# {{lb|es|botany}} [[bud]], [[shoot]]
#: {{syn|es|botón|yema}}"""

    expected_flags = ['long_nymline', 'nymsense_matches_multiple_defs']

    run_test(orig_text,expected_text,expected_flags, "test_multiword")

def test_sense_match_diestro():
    orig_text="""\
==Spanish==
===Adjective===
{{es-adj|f=diestra}}

# [[right]], [[right-hand]] {{gloss|direction}}
# [[right-handed]]
# [[skillful]], [[dexterous]], [[adroit]]
# {{lb|es|heraldry}} [[dexter]], [[dextral]]

====Synonyms====
* {{sense|right-hand}} {{l|es|derecho}}
* {{sense|skillful}} {{l|es|hábil}}, {{l|es|habiloso}}

====Antonyms====
* {{sense|right-handed}} {{l|es|zurdo}}
* {{sense|right-hand}} {{l|es|izquierdo}}, {{l|es|siniestro}}
"""
    expected_text="""\
==Spanish==
===Adjective===
{{es-adj|f=diestra}}

# [[right]], [[right-hand]] {{gloss|direction}}
#: {{syn|es|derecho}}
#: {{ant|es|izquierdo|siniestro}}
# [[right-handed]]
#: {{ant|es|zurdo}}
# [[skillful]], [[dexterous]], [[adroit]]
#: {{syn|es|hábil|habiloso}}
# {{lb|es|heraldry}} [[dexter]], [[dextral]]"""

    expected_flags = ['automatch_sense']

    run_test(orig_text,expected_text,expected_flags, "test_multiword")

def test_sense_match_aguja():
    orig_text="""\
==Spanish==
===Noun===
{{es-noun|f}}

# [[needle]]
#: {{ux|es|¿Tiene usted una '''aguja''' para coser estos botones?|Do you have a needle to sew on these buttons?}}
# [[hand]] {{gloss|of a clock}}
# {{lb|es|military}} [[firing pin]]
# {{lb|es|architecture}} [[spire]], [[steeple]]
# {{lb|es|plant}} [[Venus' comb]]

====Synonyms====
* {{s|hand}} {{l|es|saeta}}, {{l|es|manecilla}}
* {{sense|plant}} {{l|es|peine de Venus}}
"""
    expected_text="""\
==Spanish==
===Noun===
{{es-noun|f}}

# [[needle]]
#: {{ux|es|¿Tiene usted una '''aguja''' para coser estos botones?|Do you have a needle to sew on these buttons?}}
# [[hand]] {{gloss|of a clock}}
#: {{syn|es|saeta|manecilla}}
# {{lb|es|military}} [[firing pin]]
# {{lb|es|architecture}} [[spire]], [[steeple]]
# {{lb|es|plant}} [[Venus' comb]]
#: {{syn|es|peine de Venus}}"""

    expected_flags = ['automatch_sense']

    run_test(orig_text,expected_text,expected_flags, "test_multiword")



def test_sense_match_thesaurus():
    orig_text="""\
==Spanish==

===Noun===
{{es-noun|f}}

# [[word]]

====Synonyms====
* See [[Thesaurus:test]].
"""
    expected_text="""\
==Spanish==

===Noun===
{{es-noun|f}}

# [[word]]
#: {{syn|es|Thesaurus:test}}"""

    expected_flags = ['autofix']

    run_test(orig_text,expected_text,expected_flags, "test_multiword")

    orig_text="""\
==Spanish==

===Noun===
{{es-noun|f}}

# [[word]]

====Synonyms====
* See [[Thesaurus:test]]
"""
    run_test(orig_text,expected_text,expected_flags, "test_multiword")

    expected_flags=["automatch_sense"]
    orig_text="""\
==Spanish==

===Noun===
{{es-noun|f}}

# [[word]]

====Synonyms====
* {{s|word}} See [[Thesaurus:test]]
"""
    run_test(orig_text,expected_text,expected_flags, "test_multiword")

    orig_text="""\
==Spanish==

===Noun===
{{es-noun|f}}

# [[word]]

====Synonyms====
* {{sense|word}} See [[Thesaurus:test]]
"""
    run_test(orig_text,expected_text,expected_flags, "test_multiword")


def test_sense_match_3():
    orig_text="""\
==Spanish==

===Noun===
{{es-noun|f}}

# {{lb|es|colloquial}} [[drunkenness]]
# {{lb|es|colloquial}} [[year]] (used in talking about ages)

====Synonyms====
* {{sense|drunkenness}} See [[Thesaurus:borrachera]].
* {{sense|year}} {{l|es|año}}
"""
    expected_text="""\
==Spanish==

===Noun===
{{es-noun|f}}

# {{lb|es|colloquial}} [[drunkenness]]
#: {{syn|es|Thesaurus:borrachera}}
# {{lb|es|colloquial}} [[year]] (used in talking about ages)
#: {{syn|es|año}}"""

    expected_flags = ['automatch_sense']

    run_test(orig_text,expected_text,expected_flags, "test_multiword")



def test_partial_fixes():

    orig_text = """==Spanish==

===Noun===
{{es-noun}}

# [[word]]

====Synonyms====
* {{l|es|gabacho}} {{qualifier|Spain, Mexico}}
* {{l|es|guiri}} {{qualifier|Spain}}
* {{sense|nomatch}} {{l|es|guiri}} {{qualifier|Spain}}
"""
    expected_text = """==Spanish==

===Noun===
{{es-noun}}

# [[word]]
#: {{syn|es|gabacho|q1=Spain, Mexico|guiri|q2=Spain}}

====Synonyms====
* {{sense|nomatch}} {{l|es|guiri}} {{qualifier|Spain}}"""


    fixer.clear_problems()
    new_text = fixer.run_fix(orig_text, [], "test_partial")
    assert orig_text == new_text

    expected_flags = ["nymsense_matches_no_defs", "partial_fix"]
    assert sorted(expected_flags) == sorted([ x for x in fixer._problems.keys() if not x.startswith("_")])

    fixer.clear_problems()
    new_text = fixer.run_fix(orig_text, ["partial_fix"], "partial_fix-fix", sections=["Synonyms","Antonyms","Hyponyms"])
    assert new_text == expected_text


def test_tortilla():
    orig_text="""\
==Spanish==

===Noun===
{{es-noun|f}}

# {{lb|es|Spain and most Hispanic countries}} [[Spanish omelette]], {{l|en|tortilla}}
# {{lb|es|Spain and most Hispanic countries}} [[omelette]]
# {{lb|es|Mexico and Central America}} {{l|en|tortilla}}

====Synonyms====
* {{gloss|Spanish omelette}} {{l|es|tortilla de patatas}} {{qualifier|Spain}}, {{l|es|tortilla de papas}} {{qualifier|Hispanic America|Canary Islands}}, {{l|es|tortilla española}}
* {{gloss|omelette}} {{l|es|tortilla francesa}}
* {{gloss|tortilla}} {{l|es|tortilla de harina de trigo}}, {{l|es|tortilla de harina}}, {{l|es|tortilla de trigo}}
"""

    expected_text = """\
==Spanish==

===Noun===
{{es-noun|f}}

# {{lb|es|Spain and most Hispanic countries}} [[Spanish omelette]], {{l|en|tortilla}}
#: {{syn|es|tortilla de patatas|q1=Spain|tortilla de papas|q2=Hispanic America, Canary Islands|tortilla española}}
#: {{syn|es|tortilla francesa}} <!-- FIXME, MATCH SENSE: 'omelette' -->
#: {{syn|es|tortilla de harina de trigo|tortilla de harina|tortilla de trigo}} <!-- FIXME, MATCH SENSE: 'tortilla' -->
# {{lb|es|Spain and most Hispanic countries}} [[omelette]]
# {{lb|es|Mexico and Central America}} {{l|en|tortilla}}"""

    expected_flags = ['autofix_gloss_as_sense', 'automatch_sense', 'nymsense_matches_multiple_defs']

    run_test(orig_text,expected_text,expected_flags, "test_multiword")

