import pytest

import re
import enwiktionary_parser as wtparser
from enwiktionary_wordlist.wordlist import Wordlist
from enwiktionary_wordlist.all_forms import AllForms
from ..form_fixer import FormFixer, FixRunner

@pytest.fixture(scope = 'module')
def wordlist():

    data = """\
_____
Señor
pos: n
  meta: {{es-noun|m|f=+}}
  g: m
  gloss: alternative letter-case form of "señor", used before a name (also Sr.)
_____
Señora
pos: n
  meta: {{es-noun|f|m=Señor}}
  g: f
  gloss: alternative letter-case form of "señora", used before a name
_____
abjad
pos: n
  meta: {{es-noun|m}}
  g: m
  gloss: abjad (writing system)
    q: linguistics
_____
abuelito
pos: n
  meta: {{es-noun|m|f=abuelita}}
  g: m
  gloss: diminutive of "abuelo", grandfather, gramps, grandpa
_____
abyad
pos: n
  meta: {{es-noun|m}}
  g: m
  gloss: alternative form of "abjad"
_____
académico
pos: adj
  meta: {{es-adj}}
  gloss: academic
pos: n
  meta: {{es-noun|m|f=académica}}
  g: m
  gloss: academician, academic
_____
actor
pos: n
  meta: {{es-noun|m|f=actriz|f2=+}}
  g: m
  etymology: From Latin "actor".
  gloss: An actor (person who performs in a theatrical play or movie)
pos: n
  meta: {{es-noun|m|f=+}}
  g: m
  etymology: From Latin "actor".
  gloss: A defendant
    q: law
_____
aduanero
pos: adj
  meta: {{es-adj}}
  etymology: From aduana + -ero.
  gloss: customs
    q: relational
    syn: aduanal
pos: n
  meta: {{es-noun|mf|f=aduanera}}
  g: mf
  etymology: From aduana + -ero.
  gloss: customs officer
_____
alegre
pos: adj
  meta: {{es-adj}}
  gloss: joyful, cheerful
_____
ambos
pos: adj
  meta: {{head|es|adjective|g=m-p|feminine plural|ambas}}
  g: m-p
  gloss: both
    syn: los dos, las dos
pos: num
  meta: {{head|es|numeral}}
  gloss: both
pos: pron
  meta: {{head|es|pronoun}}
  gloss: both
_____
amigue
pos: n
  meta: {{es-noun|m|g2=f|m=amigo|f=amiga}}
  g: m; f
  gloss: friend
    q: gender-neutral, neologism
_____
aparecido
pos: adj
  meta: {{es-adj}}
  gloss: appeared
pos: adj
  meta: {{es-noun|m}}
  g: m
  gloss: ghost, apparition, revenant
_____
aquél
pos: pron
  meta: {{head|es|pronoun|demonstrative||feminine|aquélla|neuter|aquello|masculine plural|aquéllos|feminine plural|aquéllas|g=m}}
  g: m
  gloss: that one (far from speaker and listener)
_____
ayuda
pos: n
  meta: {{es-noun|f}}
  g: f
  etymology: From ayudar (“to help”).
  gloss: help, aid, assistance
    syn: asistencia
pos: n
  meta: {{es-noun|mf}}
  g: mf
  etymology: From ayudar (“to help”).
  gloss: helper
    syn: ayudante
_____
bosniaca
pos: n
  meta: {{es-noun|f|m=bosniaco}}
  g: f
  gloss: female equivalent of "bosniaco"
_____
bosniaco
pos: n
  meta: {{es-noun|m|f=bosniaca}}
  g: m
  gloss: alternative spelling of "bosníaco"
_____
cabra
pos: n
  meta: {{es-noun|f|m=cabro}}
  g: f
  gloss: goat (unknown gender)
 _____
caldeo
pos: adj
  meta: {{es-adj}}
  etymology: From Latin "Chaldaeus", from Ancient Greek "Χαλδαῖος", from Akkadian "𒅗𒀠𒌅".
  gloss: Chaldean
pos: n
  meta: {{es-noun|m|f=caldea}}
  g: m
  etymology: From Latin "Chaldaeus", from Ancient Greek "Χαλδαῖος", from Akkadian "𒅗𒀠𒌅".
  gloss: Chaldean
pos: v
  meta: {{head|es|verb form}}
  etymology: See caldear
  gloss: inflection of "caldear"
_____
chama
pos: n
  meta: {{es-noun|m}}
  g: m
  gloss: chama
_____
chamo
pos: n
  meta: {{es-noun|m|f=chama}}
  g: m
  gloss: kid, child
    q: Venezuela, colloquial
_____
crudívoro
pos: adj
  meta: {{es-adj}}
  gloss: crudivorous
pos: n
  meta: {{es-noun|m|f=crudívora}}
  g: m
  gloss: crudivore
_____
del mismo
pos: adj
  meta: {{es-adj|f=de la misma|mpl=de los mismos|fpl=de las mismas}}
  gloss: of it, them (substantive, refers back to a previous word in the text [see usage notes])
_____
dentista
pos: n
  meta: {{es-noun|mf}}
  g: mf
  etymology: diente + -ista
  gloss: dentist
_____
estanciera
pos: n
  meta: {{es-noun|f|m=estanciero}}
  g: f
  gloss: ranch owner
_____
exconseller
pos: n
  meta: {{es-noun|m|+|pl2=exconsellers}}
  g: m
  etymology: ex- + conseller
  gloss: former conseller
_____
fulano
pos: prop
  meta: {{head|es|proper noun|g=m|plural|fulanos|feminine|fulana|feminine plural|fulanas}}
  g: m
  gloss: alternative letter-case form of "Fulano", what's-his-name, so-and-so
_____
gongo
pos: n
  meta: {{es-noun|m}}
  g: m
  gloss: alternative form of "gong"
  gloss: bell or cowbell
    q: Puerto Rico
    syn: campana; cencerro
_____
granado
pos: adj
  meta: {{es-adj}}
  gloss: grained
pos: n
  meta: {{es-noun|m}}
  g: m
  gloss: pomegranate tree
_____
hijodalgo
pos: n
  meta: {{es-noun|m|hijosdalgo|f=hijadalgo|fpl=hijasdalgo|pl2=hijosdalgos}}
  g: m
  etymology: contraction of "hijo de algo"
  gloss: alternative form of "hidalgo"
_____
huila
pos: n
  meta: {{es-noun|f}}
  g: f
  etymology: From Mapudungun.
  gloss: rags (tattered clothes)
    q: colloquial, Chile
pos: n
  meta: {{es-noun|f}}
  g: f
  gloss: female equivalent of "huilo"
pos: adj
  meta: {{head|es|adjective form}}
  gloss: feminine singular of "huilo"
_____
huilo
pos: adj
  meta: {{es-adj}}
  gloss: crippled
    q: colloquial, Mexico
    syn: tullido
pos: n
  meta: {{es-noun|m|f=huila}}
  g: m
  gloss: a crippled person
    q: colloquial, Mexico
_____
kirguiso
pos: adj
  meta: {{es-adj}}
  gloss: of Kyrgyzstan; Kyrgyzstani (of or relating to Kyrgyzstan)
pos: n
  meta: {{es-noun|m|f=kirguisa}}
  g: m
  gloss: Kyrgyzstani (native or inhabitant of Kyrgyzstan)
_____
kirguís
pos: adj
  meta: {{es-adj}}
  gloss: Kyrgyz (Turkic ethnic group)
  gloss: alternative form of "kirguiso"
pos: n
  meta: {{es-noun|m|f=+}}
  g: m
  gloss: Kyrgyz (Turkic ethnic group)
  gloss: alternative form of "kirguiso" (inhabitant)
_____
malayo
pos: adj
  meta: {{es-adj}}
  gloss: Malay (from Malaysia)
pos: n
  meta: {{es-noun|m|f=+}}
  g: m
  gloss: Malay (person)
pos: n
  meta: {{es-noun|m|-}}
  g: m
  gloss: Malay (language)
_____
parada
pos: n
  meta: {{es-noun|f}}
  g: f
  etymology: From the feminine past participle of parar.
  gloss: stop (the act of stopping)
  gloss: station (a location where things stop)
pos: n
  meta: {{es-noun|f|m=parado}}
  g: f
  etymology: From the feminine past participle of parar.
  gloss: female equivalent of "parado"
_____
parado
pos: n
  meta: {{es-noun|m|f=parada}}
  g: m
  gloss: unemployed person
    syn: desempleado; cesante
_____
vosotres
pos: pron
  meta: {{head|es|pronoun|masculine|vosotros|feminine|vosotras|g=m|g2=f}}
  g: m; f
  gloss: you (plural)
    q: gender-neutral, neologism
"""

    return Wordlist(data.splitlines())

@pytest.fixture(scope = 'module')
def fixer(wordlist):
    return FormFixer(wordlist)

@pytest.fixture(scope = 'module')
def allforms(fixer):
    return AllForms.from_wordlist(fixer.wordlist, resolve_true_lemmas=False)

@pytest.fixture(scope = 'module')
def fixrunner(wordlist, allforms):
    return FixRunner("es", wordlist, allforms)

def test_get_declared_forms(fixer, allforms):

    tests = {

        # Ignore masculines of feminine nouns, if they have lemma
        "Señor": [],
        "Señores": [('n', 'pl', 'Señor', ['m'])],

        "alegre": [],
        "alegres": [('adj', 'pl', 'alegre', ['m', 'f'])],

         # gender neutral plurals
        "amigues": [('n', 'pl', 'amigue', ['m', 'f'])],
        "amigo": [],
        "amiga": [],

        "aquélla":  [('pron', 'f', 'aquél', ['m'])],
        "aquéllas":  [('pron', 'fpl', 'aquél', ['m'])],

        # neuter forms not handled
        "aquéllo": [],
        "":  [],
        "aquéllos":  [('pron', 'mpl', 'aquél', ['m'])],

        "vosotres": [],
        "vosotros": [],
        "vosotras": [],

        # declared by multiple versions of same lemma
        "ayudas": [('n', 'pl', 'ayuda', ['f']), ('n', 'pl', 'ayuda', ['m', 'f'])],

        "académico": [],
        "académica": [('adj', 'f', 'académico', ['m']), ('n', 'f', 'académico', ['m'])],
        "académicos": [('adj', 'mpl', 'académico', ['m']), ('n', 'pl', 'académico', ['m'])],
        "académicas": [('adj', 'fpl', 'académico', ['m']), ('n', 'pl', 'académica', ['f'])],

        # form of
        "abyades": [('n', 'pl', 'abyad', ['m'])],

        # multiple feminines
        "actora": [('n', 'f', 'actor', ['m'])],
        "actoras": [('n', 'pl', 'actora', ['f'])],
        "actrices": [('n', 'pl', 'actriz', ['f'])],

        # weird header
        "ambas": [('adj', 'fpl', 'ambos', ['m', 'f'])],

        # masculine and plural
        "dentista": [],
        "dentistas": [('n', 'pl', 'dentista', ['m', 'f'])],

        # irregular plural noun
        "hijodalgo": [],
        "hijosdalgos": [('n', 'pl', 'hijodalgo', ['m'])],
        "hijadalgo": [('n', 'f', 'hijodalgo', ['m'])],
        "hijasdalgo": [('n', 'pl', 'hijadalgo', ['f'])],

        # female lemmas
        "cabra": [],
        "cabro": [('n', 'm', 'cabra', ['f'])],

        # masculines declared by femninine nouns should be ignored
        "bosniacos": [('n', 'pl', 'bosniaco', ['m'])],

        # feminines declared by femninine form of and masculine form of, should be both
        "bosniacas": [('n', 'pl', 'bosniaca', ['f']), [('n', 'fpl', 'bosniaco', ['m'])] ],
    }

    for title, forms in tests.items():
        print("checking", title)
        assert fixer.get_declared_forms(title, fixer.wordlist, allforms) == forms

def test_full_entries(fixer, allforms):

    tests = {
        "alegres": """\
==Spanish==

===Adjective===
{{head|es|adjective form|g=m-p|g2=f-p}}

# {{adj form of|es|alegre||p}}""",


        "académica": """\
==Spanish==

===Adjective===
{{head|es|adjective form|g=f}}

# {{adj form of|es|académico||f|s}}

===Noun===
{{es-noun|f}}

# {{female equivalent of|es|académico}}""",


        "académicos": """\
==Spanish==

===Adjective===
{{head|es|adjective form|g=m-p}}

# {{adj form of|es|académico||m|p}}

===Noun===
{{head|es|noun form|g=m-p}}

# {{noun form of|es|académico||p}}""",


        "académicas": """\
==Spanish==

===Adjective===
{{head|es|adjective form|g=f-p}}

# {{adj form of|es|académico||f|p}}

===Noun===
{{head|es|noun form|g=f-p}}

# {{noun form of|es|académica||p}}""",


        "abyades": """\
==Spanish==

===Noun===
{{head|es|noun form|g=m-p}}

# {{noun form of|es|abyad||p}}""",


        "actora": """\
==Spanish==

===Noun===
{{es-noun|f}}

# {{female equivalent of|es|actor}}""",


        "actoras": """\
==Spanish==

===Noun===
{{head|es|noun form|g=f-p}}

# {{noun form of|es|actora||p}}""",


        "actrices": """\
==Spanish==

===Noun===
{{head|es|noun form|g=f-p}}

# {{noun form of|es|actriz||p}}""",

        "ayudas": """\
==Spanish==

===Noun===
{{head|es|noun form|g=f-p}}

# {{noun form of|es|ayuda||p}}""",

        "dentistas": """\
==Spanish==

===Noun===
{{head|es|noun form|g=m-p|g2=f-p}}

# {{noun form of|es|dentista||p}}""",


        "hijosdalgos": """\
==Spanish==

===Noun===
{{head|es|noun form|g=m-p}}

# {{noun form of|es|hijodalgo||p}}""",


        "hijadalgo": """\
==Spanish==

===Noun===
{{es-noun|f|hijasdalgo}}

# {{female equivalent of|es|hijodalgo}}""",


        "hijasdalgo": """\
==Spanish==

===Noun===
{{head|es|noun form|g=f-p}}

# {{noun form of|es|hijadalgo||p}}""",
    }

    for title, page in tests.items():
        df = fixer.get_declared_forms(title, fixer.wordlist, allforms)
        res = fixer.generate_full_entry(title, df)
        if res != page:
            print(f'\n\n        "{title}": """\\\n{res}""",')
        assert res == page

#    assert False

def test_adding_new_entry_only_english(fixer, allforms):
    title = "alegres"

    text = """
==English==

===Verb===
{{es-verb}}

# blah"""

    result = """
==English==

===Verb===
{{es-verb}}

# blah

----

==Spanish==

===Adjective===
{{head|es|adjective form|g=m-p|g2=f-p}}

# {{adj form of|es|alegre||p}}"""

    declared_forms = fixer.get_declared_forms(title, fixer.wordlist, allforms)
    res = fixer.add_missing_forms(title, text, declared_forms)
    print(res)
    assert res.split("\n") == result.split("\n")
    assert res == result

def test_inserting_new_entry(fixer, allforms):
    title = "alegres"

    text = """
==English==

===Verb===
{{es-verb}}

# blah

----

==Armenian==

===Verb===
{{head|verb}}

# blah

{{cat|blah}}

----

==Swedish==

===Verb===
{{head|verb}}

# blah
"""

    result = """
==English==

===Verb===
{{es-verb}}

# blah

----

==Armenian==

===Verb===
{{head|verb}}

# blah

{{cat|blah}}

----

==Spanish==

===Adjective===
{{head|es|adjective form|g=m-p|g2=f-p}}

# {{adj form of|es|alegre||p}}

----

==Swedish==

===Verb===
{{head|verb}}

# blah
"""

    declared_forms = fixer.get_declared_forms(title, fixer.wordlist, allforms)
    res = fixer.add_missing_forms(title, text, declared_forms)
    res = fixer.add_missing_forms(title, text, declared_forms)
    print(res)
    assert res.split("\n") == result.split("\n")
    assert res == result


def test_prepend_new_entry(fixer, allforms):
    title = "alegres"

    text = """
==Swedish==

===Verb===
{{head|verb}}

# blah
"""

    result = """
==Spanish==

===Adjective===
{{head|es|adjective form|g=m-p|g2=f-p}}

# {{adj form of|es|alegre||p}}

----

==Swedish==

===Verb===
{{head|verb}}

# blah
"""

    declared_forms = fixer.get_declared_forms(title, fixer.wordlist, allforms)
    res = fixer.add_missing_forms(title, text, declared_forms)
    print(res)
    assert res.split("\n") == result.split("\n")
    assert res == result


def test_append_new_entry(fixer, allforms):
    title = "alegres"

    text = """
==English==

===Verb===
{{head|verb}}

# blah"""

    result = """
==English==

===Verb===
{{head|verb}}

# blah

----

==Spanish==

===Adjective===
{{head|es|adjective form|g=m-p|g2=f-p}}

# {{adj form of|es|alegre||p}}"""

    declared_forms = fixer.get_declared_forms(title, fixer.wordlist, allforms)
    res = fixer.add_missing_forms(title, text, declared_forms)
    print(res)
    assert res.split("\n") == result.split("\n")


def test_prepending_new_pos(fixer, allforms):

    text = """
==Spanish==

===Verb===
{{es-verb}}

# blah"""

    result = """
==Spanish==

===Noun===
{{head|es|noun form|g=m-p|g2=f-p}}

# {{noun form of|es|dentista||p}}

===Verb===
{{es-verb}}

# blah"""

    title = "dentistas"
    declared_forms = fixer.get_declared_forms(title, fixer.wordlist, allforms)
    assert fixer.add_missing_forms(title, text, declared_forms) == result


def test_append_new_pos(fixer, allforms):

    text = """
==Spanish==

===Adjective===
{{es-adj}}

# blah"""

    result = """
==Spanish==

===Adjective===
{{es-adj}}

# blah

===Noun===
{{head|es|noun form|g=m-p|g2=f-p}}

# {{noun form of|es|dentista||p}}"""

    title = "dentistas"
    declared_forms = fixer.get_declared_forms(title, fixer.wordlist, allforms)
    assert fixer.add_missing_forms(title, text, declared_forms) == result


def test_insert_new_pos(fixer, allforms):

    text = """
==Spanish==

===Adjective===
{{es-adj}}

# blah

===Verb===
{{es-verb}}

# blah"""

    result = """
==Spanish==

===Adjective===
{{es-adj}}

# blah

===Noun===
{{head|es|noun form|g=m-p|g2=f-p}}

# {{noun form of|es|dentista||p}}

===Verb===
{{es-verb}}

# blah"""

    title = "dentistas"
    declared_forms = fixer.get_declared_forms(title, fixer.wordlist, allforms)
    assert fixer.add_missing_forms(title, text, declared_forms) == result


def test_fix_feminine_plural(fixer, allforms):

    text = """
==Spanish==

===Adjective===
{{head|es|adjective form|g=f-p}}

# {{adj form of|es|académico||f|p}}

===Noun===
{{head|es|noun form|g=f-p}}

# {{feminine plural of|es|académico}}

===Verb===
{{es-verb}}

# blah"""

    result = """
==Spanish==

===Adjective===
{{head|es|adjective form|g=f-p}}

# {{adj form of|es|académico||f|p}}

===Noun===
{{head|es|noun form|g=f-p}}

# {{noun form of|es|académica||p}}

===Verb===
{{es-verb}}

# blah"""

    title = "académicas"
    declared_forms = fixer.get_declared_forms(title, fixer.wordlist, allforms)

    wikt = wtparser.parse_page(text, title=title, parent=None, skip_style_tags=True)

    missing_forms, unexpected_forms = fixer.compare_forms(declared_forms, fixer.get_existing_forms(title, wikt))
    assert missing_forms ==  [('n', 'pl', 'académica', ['f'])]
    assert unexpected_forms == {('n', 'fpl', 'académico')}

    res = fixer.add_missing_forms(title, text, declared_forms)
    res = fixer.remove_undeclared_forms(title, res, declared_forms)

    assert res.split("\n") == result.split("\n")
    assert res == result

def test_remove_unexpected_first_pos(fixer, allforms):

    text = """
==Spanish==

===Adjective===
{{head|es|adjective form|g=f-p}}

# {{adj form of|es|test||f|p}}

===Noun===
{{es-noun}}

# gloss
"""

    result = """
==Spanish==

===Noun===
{{es-noun}}

# gloss
"""

    title = "test"
    declared_forms = fixer.get_declared_forms(title, fixer.wordlist, allforms)

    wikt = wtparser.parse_page(text, title=title, parent=None, skip_style_tags=True)

    missing_forms, unexpected_forms = fixer.compare_forms(declared_forms, fixer.get_existing_forms(title, wikt))
    assert missing_forms ==  []
    assert unexpected_forms == {('adj', 'fpl', 'test')}

    res = fixer.remove_undeclared_forms(title, text, declared_forms)

    assert res.split("\n") == result.split("\n")
    assert res == result

def test_remove_unexpected_inner_pos(fixer, allforms):

    text = """
==Spanish==

===Adjective===
{{es-adj}}

# gloss

===Noun===
{{es-noun}}

# {{plural of|es|blah}}

===Verb===
{{es-verb}}

# gloss
"""

    result = """
==Spanish==

===Adjective===
{{es-adj}}

# gloss

===Verb===
{{es-verb}}

# gloss
"""

    title = "test"
    declared_forms = fixer.get_declared_forms(title, fixer.wordlist, allforms)

    wikt = wtparser.parse_page(text, title=title, parent=None, skip_style_tags=True)

    missing_forms, unexpected_forms = fixer.compare_forms(declared_forms, fixer.get_existing_forms(title, wikt))
    assert missing_forms ==  []
    assert unexpected_forms == {('n', 'pl', 'blah')}

    res = fixer.remove_undeclared_forms(title, text, declared_forms)

    assert res.split("\n") == result.split("\n")
    assert res == result

def test_remove_unexpected_last_pos(fixer, allforms):

    text = """
==Spanish==

===Adjective===
{{es-adj}}

# gloss

===Noun===
{{es-noun}}

# {{plural of|es|blah}}
"""

    result = """
==Spanish==

===Adjective===
{{es-adj}}

# gloss

"""

    title = "test"
    declared_forms = fixer.get_declared_forms(title, fixer.wordlist, allforms)

    wikt = wtparser.parse_page(text, title=title, parent=None, skip_style_tags=True)

    missing_forms, unexpected_forms = fixer.compare_forms(declared_forms, fixer.get_existing_forms(title, wikt))
    assert missing_forms ==  []
    assert unexpected_forms == {('n', 'pl', 'blah')}

    res = fixer.remove_undeclared_forms(title, text, declared_forms)

    assert res.split("\n") == result.split("\n")
    assert res == result

def test_remove_unexpected_form_only(fixer, allforms):

    text = """
==Spanish==

===Adjective===
{{es-adj}}

# {{plural of|es|blah2}}
# gloss
# {{plural of|es|blah}}
"""

    result = """
==Spanish==

===Adjective===
{{es-adj}}

# gloss
"""

    title = "test"
    declared_forms = fixer.get_declared_forms(title, fixer.wordlist, allforms)

    wikt = wtparser.parse_page(text, title=title, parent=None, skip_style_tags=True)

    missing_forms, unexpected_forms = fixer.compare_forms(declared_forms, fixer.get_existing_forms(title, wikt))
    assert missing_forms ==  []
    assert unexpected_forms == {('adj', 'pl', 'blah'), ('adj', 'pl', 'blah2')}

    res = fixer.remove_undeclared_forms(title, text, declared_forms)

    assert res.split("\n") == result.split("\n")
    assert res == result

def test_remove_unexpected_word(fixer, allforms):

    text = """
==Spanish==

===Noun===
{{es-noun}}

# gloss

{{head|es|noun form|g=m-p}}

# {{plural of|es|blah}}

{{es-noun}}
# gloss 2
"""

    result = """
==Spanish==

===Noun===
{{es-noun}}

# gloss


{{es-noun}}
# gloss 2
"""

    title = "test"
    declared_forms = fixer.get_declared_forms(title, fixer.wordlist, allforms)
    res = fixer.remove_undeclared_forms(title, text, declared_forms)

    assert res.split("\n") == result.split("\n")
    assert res == result

def test_remove_unexpected_ety(fixer, allforms):

    text = """
==Spanish==

===Etymology 1===

====Noun====
{{es-noun}}

# gloss

=====Subsection=====
# blah

===Etymology 2===

====Noun====
{{es-noun}}

# {{plural of|es|blah}}
"""

    result = """
==Spanish==

===Etymology===

===Noun===
{{es-noun}}

# gloss

====Subsection====
# blah

"""

    title = "test"
    declared_forms = fixer.get_declared_forms(title, fixer.wordlist, allforms)
    res = fixer.remove_undeclared_forms(title, text, declared_forms)

    print(res)

    assert res.split("\n") == result.split("\n")
    assert res == result


def test_remove_unexpected_ety_renumber(fixer, allforms):

    text = """
==Spanish==

===Etymology 1===

====Noun====
{{es-noun}}

# gloss

===Etymology 2===

====Noun====
{{es-noun}}

# {{plural of|es|blah}}

===Etymology 3===

====Noun====
{{es-noun}}

# gloss2
"""

    result = """
==Spanish==

===Etymology 1===

====Noun====
{{es-noun}}

# gloss

===Etymology 2===

====Noun====
{{es-noun}}

# gloss2
"""

    title = "test"
    declared_forms = fixer.get_declared_forms(title, fixer.wordlist, allforms)
    res = fixer.remove_undeclared_forms(title, text, declared_forms)

    assert res.split("\n") == result.split("\n")
    assert res == result


def test_remove_last_lang(fixer, allforms):

    text = """
==English==

===Verb===
{{en-verb}}

# blah

----

==Spanish==

====Noun====
{{es-noun}}

# {{plural of|es|blah}}
"""

    result = """
==English==

===Verb===
{{en-verb}}

# blah

----

"""

    title = "test"
    declared_forms = fixer.get_declared_forms(title, fixer.wordlist, allforms)
    res = fixer.remove_undeclared_forms(title, text, declared_forms)

    assert res.split("\n") == result.split("\n")
    assert res == result

def test_remove_middle_lang(fixer, allforms):

    text = """
==English==

===Verb===
{{en-verb}}

# blah

----

==Spanish==

====Noun====
{{es-noun}}

# {{plural of|es|blah}}

----

==Thai==

===Noun===

# gloss

"""

    result = """
==English==

===Verb===
{{en-verb}}

# blah

----

==Thai==

===Noun===

# gloss

"""

    title = "test"
    declared_forms = fixer.get_declared_forms(title, fixer.wordlist, allforms)
    res = fixer.remove_undeclared_forms(title, text, declared_forms)

    assert res.split("\n") == result.split("\n")
    assert res == result

def test_remove_first_lang(fixer, allforms):

    text = """
==Spanish==

====Noun====
{{es-noun}}

# {{plural of|es|blah}}

----

==Thai==

===Noun===

# gloss

"""

    result = """
==Thai==

===Noun===

# gloss

"""

    title = "test"
    declared_forms = fixer.get_declared_forms(title, fixer.wordlist, allforms)
    res = fixer.remove_undeclared_forms(title, text, declared_forms)

    assert res.split("\n") == result.split("\n")
    assert res == result

def test_caldea(fixer, allforms):

    text = """

==Spanish==

===Verb===
{{head|es|verb form}}

# {{es-verb form of|person=third-person|number=singular|tense=present|mood=indicative|ending=ar|caldear}}
# {{es-verb form of|formal=no|person=second-person|number=singular|sense=affirmative|mood=imperative|ending=ar|caldear}}
"""

    result = """

==Spanish==

===Adjective===
{{head|es|adjective form|g=f}}

# {{adj form of|es|caldeo||f|s}}

===Noun===
{{es-noun|f}}

# {{female equivalent of|es|caldeo}}

===Verb===
{{head|es|verb form}}

# {{es-verb form of|person=third-person|number=singular|tense=present|mood=indicative|ending=ar|caldear}}
# {{es-verb form of|formal=no|person=second-person|number=singular|sense=affirmative|mood=imperative|ending=ar|caldear}}
"""

    title = "caldea"
    declared_forms = fixer.get_declared_forms(title, fixer.wordlist, allforms)
    assert declared_forms == [('adj', 'f', 'caldeo', ['m']), ('n', 'f', 'caldeo', ['m'])]
    res = fixer.add_missing_forms(title, text, declared_forms)
#    res = fixer.add_missing_forms(title, text, declared_forms)

    print(res)

    assert res.split("\n") == result.split("\n")
    assert res == result

def test_aduanero(fixer, allforms):

    text = """
==Spanish==

===Adjective===
{{head|es|adjective form}}

# {{feminine singular of|es|aduanero}}"""

    result = """
==Spanish==

===Adjective===
{{head|es|adjective form}}

# {{feminine singular of|es|aduanero}}

===Noun===
{{es-noun|f}}

# {{female equivalent of|es|aduanero}}"""

    title = "aduanera"
    declared_forms = fixer.get_declared_forms(title, fixer.wordlist, allforms)
    assert declared_forms == [('adj', 'f', 'aduanero', ['m']), ('n', 'f', 'aduanero', ['m', 'f'])]
    res = fixer.add_missing_forms(title, text, declared_forms)
#    res = fixer.add_missing_forms(title, text, declared_forms)

    print(res)

    assert res.split("\n") == result.split("\n")
    assert res == result


def test_get_form_head(fixer):

    # Test buggy noun declarations (says mf, but gives separate f form)
    #  {{es-noun|mf|f=aduanera}}
    assert fixer.get_form_head('aduanera', ('n', 'f', 'aduanero', ['m', 'f'])) == "{{es-noun|f}}"
    assert fixer.get_form_head('actriz', ('n', 'f', 'actor', ['m'])) == "{{es-noun|f}}"
    assert fixer.get_form_head('hijadalgo', ('n', 'f', 'hijodalgo', ['m'])) == "{{es-noun|f|hijasdalgo}}"


def test_crudivora(fixer, allforms):

    text = """
{{also|crudivora}}
==Spanish==

===Adjective===
{{head|es|adjective form}}

# {{plural of|es|crudívoro}}
"""

    result = """
{{also|crudivora}}
==Spanish==

===Adjective===
{{head|es|adjective form}}

# {{adj form of|es|crudívoro||f|s}}


===Noun===
{{es-noun|f}}

# {{female equivalent of|es|crudívoro}}"""

    title = "crudívora"
    declared_forms = fixer.get_declared_forms(title, fixer.wordlist, allforms)
    assert declared_forms == [('adj', 'f', 'crudívoro', ['m']), ('n', 'f', 'crudívoro', ['m'])]
    res = fixer.add_missing_forms(title, text, declared_forms)
    res = fixer.remove_undeclared_forms(title, res, declared_forms)

    print(res)

    assert res.split("\n") == result.split("\n")
    assert res == result



def test_kirguisa(fixer, allforms):

    text = """
==Spanish==

===Adjective===
{{head|es|adjective form}}

# {{feminine singular of|es|kirguís}}"""

    result = """
==Spanish==

===Adjective===
{{head|es|adjective form}}

# {{feminine singular of|es|kirguís}}
# {{adj form of|es|kirguiso||f|s}}


===Noun===
{{es-noun|f}}

# {{female equivalent of|es|kirguiso}}
# {{female equivalent of|es|kirguís}}"""

    title = "kirguisa"
    declared_forms = fixer.get_declared_forms(title, fixer.wordlist, allforms)
    assert declared_forms == [('adj', 'f', 'kirguiso', ['m']), ('n', 'f', 'kirguiso', ['m']), ('adj', 'f', 'kirguís', ['m']), ('n', 'f', 'kirguís', ['m'])]
    res = fixer.add_missing_forms(title, text, declared_forms)
    res = fixer.remove_undeclared_forms(title, res, declared_forms)

    print(res)

    assert res.split("\n") == result.split("\n")
    assert res == result


# Currently this is handled on the bot side
def notest_append_new_pos2(fixer, allforms):

    text = """
==Spanish==

===Adjective===
{{es-adj}}

# blah

{{C|es|Occupations}}
"""

    result = """
==Spanish==

===Adjective===
{{es-adj}}

# blah

===Noun===
{{head|es|noun form|g=m-p|g2=f-p}}

# {{noun form of|es|dentista||p}}

{{C|es|Occupations}}
"""

    title = "dentistas"
    declared_forms = fixer.get_declared_forms(title, fixer.wordlist, allforms)
    assert fixer.add_missing_forms(title, text, declared_forms) == result


# Currently this is handled on the bot side
def notest_append_new_pos3(fixer, allforms):

    text = """
==Spanish==

===Adjective===
{{es-adj}}

# blah

----

===Thai===

===Noun===

# gloss
"""

    result = """
==Spanish==

===Adjective===
{{es-adj}}

# blah

===Noun===
{{head|es|noun form|g=m-p|g2=f-p}}

# {{noun form of|es|dentista||p}}

----

===Thai===

===Noun===

# gloss
"""

    title = "dentistas"
    declared_forms = fixer.get_declared_forms(title, fixer.wordlist, allforms)
    assert fixer.add_missing_forms(title, text, declared_forms) == result


def test_paradas(fixer, allforms):

    text = """
==Spanish==

===Pronunciation===
{{es-IPA}}

===Noun 1===
{{head|es|noun form|g=f-p}}

# {{inflection of|es|parada|t=stop||p}}

===Noun 2===
{{head|es|noun form|g=f-p}}

# {{inflection of|es|parado|t=unemployed person||f|p}}

===Verb===
{{head|es|past participle form|g=f-p}}

# {{es-verb form of|mood=participle|ending=ar|parar|gen=f|num=p}}
"""

    result = """
==Spanish==

===Pronunciation===
{{es-IPA}}

===Noun 1===
{{head|es|noun form|g=f-p}}

# {{inflection of|es|parada|t=stop||p}}

===Noun 2===
{{head|es|noun form|g=f-p}}

# {{inflection of|es|parado|t=unemployed person||f|p}}

===Verb===
{{head|es|past participle form|g=f-p}}

# {{es-verb form of|mood=participle|ending=ar|parar|gen=f|num=p}}
"""


    title = "paradas"
    declared_forms = fixer.get_declared_forms(title, fixer.wordlist, allforms)
    assert declared_forms == [('n', 'pl', 'parada', ['f'])]

    res = fixer.add_missing_forms(title, text, declared_forms)
    with pytest.raises(ValueError) as e:
        res = fixer.remove_undeclared_forms(title, text, declared_forms)

    assert res == result



def test_add_new_word(fixrunner):

    text = """
==Spanish==

===Noun===
{{es-noun|m}}

# [[#English|chama]]
"""
    result = """
==Spanish==

===Noun 1===
{{es-noun|m}}

# [[#English|chama]]

{{es-noun|f}}

===Noun 2===
{{es-noun|f}}

# {{female equivalent of|es|chamo}}"""

    title = "chama"
    res = fixrunner.add_forms(re.match("(?s).*", text), title)
#    assert res.split("\n") == result.split("\n")
    assert res == text #result

def test_chamas(fixer, allforms):

    text = """
==Spanish==

===Noun===
{{head|es|noun form|g=f-p}}

# {{feminine plural of|es|chamo}}
"""

    result = """
==Spanish==

===Noun===
{{head|es|noun form|g=f-p}}

# {{noun form of|es|chama||p}}
"""

    title = "chamas"
    declared_forms = fixer.get_declared_forms(title, fixer.wordlist, allforms)
    assert declared_forms ==  [('n', 'pl', 'chama', ['m'])] #, ('n', 'pl', 'chama', ['f'])]

    res = fixer.add_missing_forms(title, text, declared_forms)
    res = fixer.remove_undeclared_forms(title, res, declared_forms)

    assert res == result


def test_dont_remove_sense_with_data2(fixer, allforms):

    text = """
==Spanish==

===Adjective===
{{es-adj}}

# gloss

===Noun===
{{es-noun}}

# {{plural of|es|blah}}; extra info
"""

    title = "test"
    declared_forms = fixer.get_declared_forms(title, fixer.wordlist, allforms)

    with pytest.raises(ValueError) as e:
        res = fixer.remove_undeclared_forms(title, text, declared_forms)

def test_dont_remove_sense_with_data(fixer, allforms):

    text = """
==Spanish==

===Adjective===
{{es-adj}}

# gloss

===Noun===
{{es-noun}}

# {{plural of|es|blah}}
#* {{quote-journal|es|date=November 16, 2015|author=|title=La policía belga lleva a cabo una redada en Molenbeek|work=El País|url=http://internacional.elpais.com/internacional/2015/11/16/actualidad/1447670004_552313.html
"""

    title = "test"
    declared_forms = fixer.get_declared_forms(title, fixer.wordlist, allforms)

    with pytest.raises(ValueError) as e:
        res = fixer.remove_undeclared_forms(title, text, declared_forms)

def test_amigues(fixer, allforms):

    text = """
==Spanish==

===Pronunciation===
{{es-IPA}}

===Noun===
{{head|es|noun form}}

# {{plural of|es|amigue}}
"""
    # Don't delete existing

    assert False


def test_add_entry_to_empty_page(fixer, allforms):
    text = ""

    result = """==Spanish==

===Noun===
{{head|es|noun form|g=m-p}}

# {{noun form of|es|gongo||p}}"""

    title = "gongos"
    declared_forms = fixer.get_declared_forms(title, fixer.wordlist, allforms)
    assert declared_forms ==  [('n', 'pl', 'gongo', ['m'])]
    res = fixer.add_missing_forms(title, text, declared_forms)
    res = fixer.remove_undeclared_forms(title, res, declared_forms)
    print(res)
    assert res == result


def test_amigues(fixer, allforms):
    text = """
==Spanish==

===Pronunciation===
{{es-IPA}}

===Verb===
{{head|es|verb form}}

# {{es-verb form of|ending=ar|mood=imperative|sense=negative|pers=2|formal=no|number=singular|amigar}}
# {{es-verb form of|ending=ar|mood=subjunctive|tense=present|pers=2|formal=no|number=singular|amigar}}

===Noun===
{{head|es|noun form}}

# {{plural of|es|amigue}}
"""

    result = text

    title = "amigues"
    declared_forms = fixer.get_declared_forms(title, fixer.wordlist, allforms)
    assert declared_forms == [('n', 'pl', 'amigue', ['m', 'f'])]
    res = fixer.add_missing_forms(title, text, declared_forms)
    res = fixer.remove_undeclared_forms(title, res, declared_forms)
    print(res)
    assert res == result


def test_huilas(fixer, allforms):

    text = """
==Spanish==

===Etymology 1===

====Adjective====
{{head|es|adjective form}}

# {{adj form of|es|huilo||f|p}}

====Noun====
{{head|es|noun form|g=f-p}}

# {{inflection of|es|huilo||f|p}}

===Etymology 2===

====Noun====
{{head|es|noun form|g=f-p}}

# {{inflection of|es|huila||p}}
"""

    result = """
==Spanish==

===Etymology 1===

====Adjective====
{{head|es|adjective form}}

# {{adj form of|es|huilo||f|p}}

===Etymology 2===

====Noun====
{{head|es|noun form|g=f-p}}

# {{inflection of|es|huila||p}}
"""


    title = "huilas"
    declared_forms = fixer.get_declared_forms(title, fixer.wordlist, allforms)
    assert declared_forms == [('n', 'pl', 'huila', ['f']), ('adj', 'fpl', 'huilo', ['m'])]

    res = fixer.add_missing_forms(title, text, declared_forms)
    assert res == text

    res = fixer.remove_undeclared_forms(title, res, declared_forms)
    assert res.split("\n") == result.split("\n")


def test_granados(fixrunner):

    text = """
==Spanish==

===Pronunciation===
{{es-IPA}}

===Adjective===
{{head|es|adjective form}}

# {{adj form of|es|granado||m|p}}

====Verb====
{{head|es|past participle form}}

# {{es-verb form of|mood=participle|gen=m|num=p|ending=ar|granar}}"""

    title = "granados"
    res = fixrunner.add_forms(re.match("(?s).*", text), title)

    print(res)
    # No change, because the result is messy because Verb is L4 and not L3
    assert res == text

def test_fulanos(fixrunner):

    text = """\
{{also|Fulanos}}
==Portuguese==

===Noun===
{{head|pt|noun form}}

# {{plural of|pt|fulano}}

----
"""

    result = """\
{{also|Fulanos}}
==Portuguese==

===Noun===
{{head|pt|noun form}}

# {{plural of|pt|fulano}}

----

==Spanish==

===Proper noun===
{{head|es|proper noun form|g=m-p}}

# {{inflection of|es|fulano||p|p=proper}}\
"""


    title = "fulanos"
    res = fixrunner.add_forms(re.match("(?s).*", text), title)
    assert res.split("\n") == result.split("\n")

def test_delete_page(fixrunner):

    text = """
==Spanish==

====Noun====
{{es-noun}}

# {{plural of|es|blah}}
"""

    title = "test"
    res = fixrunner.remove_forms(re.match("(?s).*", text), title)
    assert res == text


def test_female_lemma(fixrunner):

    # Feminine nouns that have a masculine declaration are lemmas and not just
    # a 'feminine of' lemma-ish noun form

    text = """
==Spanish==

===Noun===
{{es-noun|f|m=abuelito}}

# {{diminutive of|es|abuela}}
"""

    result = """
==Spanish==

===Noun===
{{es-noun|f|m=abuelito}}

# {{diminutive of|es|abuela}}
"""

    title = "abuelita"
    res = fixrunner.replace_forms(re.match("(?s).*", text), title)
    assert res == text


def test_female_lemma2(fixrunner):

    # Feminine nouns that have a masculine declaration are lemmas and not just
    # a 'feminine of' lemma-ish noun form

    text = """
==Spanish==

===Noun===
{{es-noun|f|m=abuelito}}, [[granny]]

# {{diminutive of|es|abuela}}
"""

    result = """
==Spanish==

===Noun===
{{es-noun|f|m=abuelito}}, [[granny]]

# {{diminutive of|es|abuela}}
"""

    title = "abuelita"
    res = fixrunner.replace_forms(re.match("(?s).*", text), title)
    assert res == text

    # Deleted pages aren't changed, but an error is logged to error.log

def test_female_lemma2(fixrunner):

    # Don't add masculine form of feminine noun

    text = ""

    result = ""

    title = "estanciero"
    res = fixrunner.replace_forms(re.match("(?s).*", text), title)
    assert res == text



def test_get_existing(fixer, allforms):

    text = """
==Spanish==

===Noun===
{{es-noun|f|m=busero}}

# [[bus driver]]
"""

    title = "busera"

    wikt = wtparser.parse_page(text, title=title, parent=None, skip_style_tags=True)
    assert fixer.get_existing_forms(title, wikt) == {('n', 'f', 'busero'): None}


    text = """
==Spanish==

===Noun===
{{es-noun|m|f=busera}}

# [[bus driver]]
"""

    title = "busero"

    wikt = wtparser.parse_page(text, title=title, parent=None, skip_style_tags=True)
    assert fixer.get_existing_forms(title, wikt) == {('n', 'm', 'busera'): None}


def test_actriz(fixer, allforms):
    title = "actriz"

    text = """
==Spanish==

===Noun===
{{es-noun|f|m=actor}}

# [[actress]]
"""

    declared_forms = fixer.get_declared_forms(title, fixer.wordlist, allforms)
    assert declared_forms == [('n', 'f', 'actor', ['m'])]

    wikt = wtparser.parse_page(text, title=title, parent=None, skip_style_tags=True)
    existing_forms = fixer.get_existing_forms(title, wikt)
    assert existing_forms == {('n', 'f', 'actor'): None}

    missing_forms, unexpected_forms = fixer.compare_forms(declared_forms, existing_forms)

    assert missing_forms == []
    assert unexpected_forms == set()


