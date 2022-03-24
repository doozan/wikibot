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
from ..nym_sections_to_tags import NymSectionToTag

fixer = NymSectionToTag("es")
en_fixer = NymSectionToTag("en")

def run_test(orig_text, expected_text, expected_flags, title="test"):

    fixer.clear_problems()
    new_text = fixer.run_fix(orig_text, [], title)
    assert orig_text == new_text

    first_expected = [ x for x in expected_flags if x != 'partial_fix' ]
    assert sorted(first_expected) == sorted([ x for x in fixer._problems.keys() if not x.startswith("_") and x != "partial_fix" ])

    fixer.clear_problems()
    new_text = fixer.run_fix(orig_text, expected_flags, title+"-fix", sections=["Synonyms","Antonyms","Hyponyms"])
    assert new_text == expected_text

def run_test_partial(orig_text, expected_text, expected_flags, title="test"):

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

# [[wordA]]
# [[wordB]]

====Synonyms====
* {{l|es|synA}}
"""
    expected_text = """==Spanish==

===Noun===
{{es-noun}}

# [[wordA]]
#: {{syn|es|synA}} <!-- FIXME, MATCH SENSE: '' -->
# [[wordB]]"""

    expected_flags = ["nymsense_matches_multiple_defs"]
    run_test(orig_text, expected_text, expected_flags)

def test_multi_defs2():

    orig_text = """==Spanish==

===Noun===
{{es-noun}}

# {{l|en|wordA}}
# [[wordB]]

====Synonyms====
* {{l|es|synA}}
"""
    expected_text = """==Spanish==

===Noun===
{{es-noun}}

# {{l|en|wordA}}
#: {{syn|es|synA}} <!-- FIXME, MATCH SENSE: '' -->
# [[wordB]]"""

    expected_flags = ["nymsense_matches_multiple_defs"]
    run_test(orig_text, expected_text, expected_flags)

def test_multi_nomerge():

    orig_text = """==Spanish==

===Noun===
{{es-noun}}

# {{l|en|wordA}}
# [[wordB]]

====Synonyms====
* {{sense|senseA}} {{l|es|synA}}
* {{sense|sense2}}  {{l|es|synB}}
"""
    expected_text = """==Spanish==

===Noun===
{{es-noun}}

# {{l|en|wordA}}
#: {{syn|es|synA}} <!-- FIXME, MATCH SENSE: 'senseA' -->
#: {{syn|es|synB}} <!-- FIXME, MATCH SENSE: 'sense2' -->
# [[wordB]]"""

    expected_flags = ["nymsense_matches_no_defs"]
    run_test(orig_text, expected_text, expected_flags)

def test_gloss():

    orig_text = """==Spanish==

===Noun===
{{es-noun}}

# [[wordA]]

====Synonyms====
* {{sense|wordA}} {{l|es|synA}} {{gloss|gloss as qualifier}}
"""
    expected_text = """==Spanish==

===Noun===
{{es-noun}}

# [[wordA]]
#: {{syn|es|synA|q1=gloss as qualifier}}"""

    expected_flags = ["automatch_sense", "using_gloss_as_qualifier"]
    new_text = fixer.run_fix(orig_text, expected_flags, "test-fix", sections=["Synonyms","Antonyms","Hyponyms"])
    assert expected_text == new_text

def test_gloss_as_sense():

    orig_text = """==Spanish==

===Noun===
{{es-noun}}

# [[wordA]]

====Synonyms====
* {{gloss|wordA}} {{l|es|synA}}
"""
    expected_text = """==Spanish==

===Noun===
{{es-noun}}

# [[wordA]]
#: {{syn|es|synA}}"""

    expected_flags = ["all"]
    #run_test(orig_text, expected_text, expected_flags)
    new_text = fixer.run_fix(orig_text, expected_flags, "test-fix", sections=["Synonyms","Antonyms","Hyponyms"])
    assert expected_text == new_text



def test_fix_subsection():
    orig_text = """==Spanish==

===Noun===
{{es-noun}}

# [[wordA]]

====Synonyms====
* {{l|es|synA}}

=====Subsection=====
* blah1

======Sub-Subsection======
* blah2

{{other stuff}}

=====Subsection2=====
* blah3

=====Subsection3=====
* blah4

"""
    expected_text = """==Spanish==

===Noun===
{{es-noun}}

# [[wordA]]
#: {{syn|es|synA}}

====Subsection====
* blah1

=====Sub-Subsection=====
* blah2

{{other stuff}}

====Subsection2====
* blah3

====Subsection3====
* blah4"""

    expected_flags = ["autofix_nymsection_has_subsections", "unexpected_section"]
    run_test(orig_text, expected_text, expected_flags)


def test_run_fix_viste():

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
#: {{syn|es|sabés|alt1=¿sabés?|no|alt2=¿no?}}\
"""
    expected_flags = ['automatch_nymsection_outside_pos']

    run_test(orig_text,expected_text,expected_flags)


def test_open_templates():

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
#: {{syn|es|otherword}}\
"""
    expected_flags = ["autofix"]

    run_test(orig_text,expected_text,expected_flags)


def test_sense_match_same_level():

    orig_text="""==Spanish==

===Noun===
{{es-noun|m}}

# {{senseid|es|worda}} {{l|en|word}} {{q|Mexico|Spain}} {{gloss|a long description}}
# {{l|en|wordb}}

===Synonyms===
* {{sense|worda}} {{l|es|otherword}}
"""
    expected_text="""==Spanish==

===Noun===
{{es-noun|m}}

# {{senseid|es|worda}} {{l|en|word}} {{q|Mexico|Spain}} {{gloss|a long description}}
#: {{syn|es|otherword}}
# {{l|en|wordb}}\
"""
    expected_flags = ['automatch_nymsection_outside_pos', 'automatch_sense']

    run_test(orig_text,expected_text,expected_flags)


def test_run_fix_complex():

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

    expected_text_partial="""==Spanish==

===Noun===
{{es-noun|f}}

# {{lb|es|art}} [[caricature]] (pictorial representation of someone for comic effect)
#: {{syn|es|dibujo}}
# {{lb|es|colloquial|Mexico}} [[animated cartoon]] (''specially in plural'')
#: {{syn|es|dibujos animados}}

====Hyponyms====
* {{l|es|caricatura editorial||editorial cartoon}}
* {{l|es|caricatura política}}\
"""

    expected_text_all="""==Spanish==

===Noun===
{{es-noun|f}}

# {{lb|es|art}} [[caricature]] (pictorial representation of someone for comic effect)
#: {{syn|es|dibujo}}
#: {{hypo|es|caricatura editorial|q1=editorial cartoon|caricatura política}} <!-- FIXME, MATCH SENSE: '' -->
# {{lb|es|colloquial|Mexico}} [[animated cartoon]] (''specially in plural'')
#: {{syn|es|dibujos animados}}\
"""

    expected_flags = ['automatch_sense', 'nymsense_matches_multiple_defs', 'partial_fix' ]
    run_test_partial(orig_text,expected_text_partial,expected_flags)

    expected_flags = ['all']
    run_test_partial(orig_text,expected_text_all,expected_flags)


def test_sense_match_senseid():

    orig_text="""==Spanish==

===Noun===
{{es-noun|m}}

# {{senseid|es|wordA}} {{l|en|word}} {{q|Mexico|Spain}} {{gloss|a long description}}
# {{l|en|wordB}}

====Synonyms====
* {{sense|wordA}} {{l|es|otherword}}
"""
    expected_text="""==Spanish==

===Noun===
{{es-noun|m}}

# {{senseid|es|wordA}} {{l|en|word}} {{q|Mexico|Spain}} {{gloss|a long description}}
#: {{syn|es|otherword}}
# {{l|en|wordB}}\
"""
    expected_flags = ["automatch_sense"]

    run_test(orig_text,expected_text,expected_flags)



def test_sense_match_def():

    orig_text="""==Spanish==

===Noun===
{{es-noun|m}}

# {{lb|en|sometimes}} [[wordA]] {{q|Mexico|Spain}} {{gloss|a long description}}
# [[wordB]]

====Synonyms====
* {{sense|wordB}} {{l|es|otherwordB}}
* {{sense|wordA}} {{l|es|otherword}}
"""
    expected_text="""==Spanish==

===Noun===
{{es-noun|m}}

# {{lb|en|sometimes}} [[wordA]] {{q|Mexico|Spain}} {{gloss|a long description}}
#: {{syn|es|otherword}}
# [[wordB]]
#: {{syn|es|otherwordB}}\
"""

    expected_flags = ["automatch_sense",  'sense_label_lang_mismatch']

    run_test(orig_text,expected_text,expected_flags)


def test_sense_match_multi_def():

    orig_text="""==Spanish==

===Noun===
{{es-noun|m}}

# [[wordA]], blah wordB blah
# [[wordB]]
# [[wordC]]

====Synonyms====
* {{sense|wordB}} {{l|es|synA}}
"""
    expected_text="""==Spanish==

===Noun===
{{es-noun|m}}

# [[wordA]], blah wordB blah
#: {{syn|es|synA}} <!-- FIXME, MATCH SENSE: 'wordB' -->
# [[wordB]]
# [[wordC]]"""

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


def notest_you():
    orig_text="""\
==English==

===Etymology===
From {{m|en|champ|champ (verb)|to chew noisily}} + {{m|en|bit||part of horse's harness held in its mouth}}; horses tend to chew on their bits when impatient at waiting.

===Pronunciation===
* {{audio|en|en-au-champ at the bit.ogg|Audio (AU)}}

===Verb===
{{en-verb|*}}

# {{lb|en|intransitive|horses}} To [[bite]] the [[bit]], especially when [[restless]].
# {{lb|en|intransitive|idiomatic|of a person}} To show [[impatience]] or [[frustration]] when [[delayed]].
#* '''2001:''' Byron Spice, Science Editor, Pittsburgh Post-Gazette, ''PG News'' read at [http://www.postgazette.com/healthscience/20011001terascale1001p3.asp] on 14 May 2006
#*: Pittsburgh supercomputer is complete, and scientists are '''champing at the bit''' to use it.
#* '''2006:''' Australian Broadcasting Corporation, webpage for ''Ideas with wings, a radio series supporting innovation'' read at [http://abc.net.au/science/wings/ http://abc.net.au/science/wings/] on 14 May 2006
#*: Everyone is '''champing at the bit''' to be labelled innovative.
#* '''2006:''' Al Rosenquist of Pastika’s Sport Shop, speaking to Terrell Boettcher of Sawyer County Record, Hayward, Wisconsin, ''Anglers '''champing at the bit''' ''read at [http://www.haywardwi.com/record/index.php?story_id=218863] on 14 May 2006
#*: We had quite a few people in last weekend. They’re '''champing at the bit''', ready to go.

====Synonyms====
* {{l|en|chafe at the bit}}

====Related terms====
* {{l|en|chomp at the bit}}

====Translations====
{{trans-top|of horse: to bite the bit}}
* Finnish: {{t|fi|[[purra]] [[kuolain|kuolainta]]}}
* French: {{t+|fr|prendre le mors aux dents}}
{{trans-mid}}
* German: {{t|de|auf dem Gebiss kauen}}
* Russian: {{t|ru|закуси́ть удила́}}
{{trans-bottom}}

{{trans-top|to show impatience when delayed}}
* Finnish: {{t|fi|hermoilla}}
* French: {{t+|fr|ronger son frein}}, {{t+|fr|se ronger les ongles}}
* German: {{t|de|mit den Hufen scharren}}
{{trans-mid}}
* Russian: {{t|ru|закуси́ть удила́}}
* Swedish: {{t|sv|brinna av iver}}, {{t|sv|brinna av otålighet}}
{{trans-bottom}}
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

    expected_flags = ['nymsense_matches_multiple_defs']

    title = "champ at the bit"

#    en_fixer.clear_problems()
#    new_text = en_fixer.run_fix(orig_text, [], title)
#    assert orig_text == new_text
#    assert sorted(expected_flags) == sorted([ x for x in en_fixer._problems.keys() if not x.startswith("_") and x != "partial_fix" ])

    en_fixer.clear_problems()
    new_text = en_fixer.run_fix(orig_text, expected_flags, title, sections=["Synonyms"])
    assert new_text == expected_text



def test_match_parent():

    orig_text="""==Spanish==

===Noun===
{{es-noun|m}}

# [[wordA]]

====Synonyms====
* {{l|es|synA}}

===Verb===
{{es-verb}}

# [[wordA]]
"""
    expected_text="""==Spanish==

===Noun===
{{es-noun|m}}

# [[wordA]]
#: {{syn|es|synA}}

===Verb===
{{es-verb}}

# [[wordA]]\
"""

    expected_flags = ["autofix"]

    run_test(orig_text,expected_text,expected_flags)



def test_match_parent2():

    orig_text="""
==Spanish==

===Etymology 1===

====Noun====
{{es-noun|m}}

# [[word]]

====Synonyms====
* {{l|es|syn}}

===Etymology 2===

===Verb===
{{es-verb}}}

# [[word]]
"""
    expected_text="""
==Spanish==

===Etymology 1===

====Noun====
{{es-noun|m}}

# [[word]]
#: {{syn|es|syn}}

===Etymology 2===

===Verb===
{{es-verb}}}

# [[word]]\
"""

    expected_flags = ['automatch_nymsection_outside_pos']

    run_test(orig_text,expected_text,expected_flags)


def no_test_stall():

    orig_text="""
==Portuguese==

===Noun===
{{pt-noun|f|s}}

# {{l|en|stall}} {{gloss|a small open-fronted shop}}
# {{l|en|booth}} {{gloss|a small stall for the display and sale of goods}}
# {{l|en|newsstand}} {{gloss|open stall where newspapers and magazines are on sale}}
# {{l|en|jury}} {{gloss|a group of people whose aim is to judge something}}

====Synonyms====
* {{sense|stall}} {{l|pt|estande}}
"""

    expected_text="""
==Portuguese==

===Noun===
{{pt-noun|f|s}}

# {{l|en|stall}} {{gloss|a small open-fronted shop}}
#: {{syn|pt|estande}}
# {{l|en|booth}} {{gloss|a small stall for the display and sale of goods}}
# {{l|en|newsstand}} {{gloss|open stall where newspapers and magazines are on sale}}
# {{l|en|jury}} {{gloss|a group of people whose aim is to judge something}}\
"""

    expected_flags = ["autofix"]

    run_test(orig_text,expected_text,expected_flags)


def test_front():

    orig_text="""
==Portuguese==

===Noun===
{{pt-noun|f}}

# {{l|en|front}} {{gloss|facing side}}
# {{l|en|front}} {{gloss|main entrance side}}
# {{lb|pt|military}} {{l|en|front}} {{gloss|area or line of conflict}}
# {{lb|pt|weather}} {{l|en|front}}

====Synonyms====
* {{sense|facing side}} {{l|pt|dianteira}}
* {{sense|entrance site}} {{l|pt|entrada}}
* {{sense|line of conflict}} {{l|pt|fronte}}
"""

    expected_text="""
==Portuguese==

===Noun===
{{pt-noun|f}}

# {{l|en|front}} {{gloss|facing side}}
#: {{syn|pt|dianteira}}
# {{l|en|front}} {{gloss|main entrance side}}
#: {{syn|pt|entrada}}
# {{lb|pt|military}} {{l|en|front}} {{gloss|area or line of conflict}}
#: {{syn|pt|fronte}}
# {{lb|pt|weather}} {{l|en|front}}\
"""

    expected_flags = ['automatch_sense', 'nymsense_fuzzy_match']

    run_test(orig_text,expected_text,expected_flags)

