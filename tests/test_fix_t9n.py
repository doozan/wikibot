import pytest

import re
import enwiktionary_parser as wtparser
from enwiktionary_wordlist.wordlist import Wordlist
from enwiktionary_wordlist.all_forms import AllForms
from enwiktionary_translations import TranslationTable, TranslationLine, UNKNOWN_LANGS, LANG_PARENTS
from ..fix_t9n import T9nFixer, T9nFixRunner

@pytest.fixture(scope = 'module')
def wordlist():

    data = """\
_____
actor
pos: n
  meta: {{es-noun|m|f=actriz|f2=+}}
  g: m
  etymology: From Latin "actor".
  gloss: An actor (person who performs in a theatrical play or movie)
_____
actriz
pos: n
  meta: {{es-noun|f|m=actor}}
  gloss: actress
_____
alegre
pos: adj
  meta: {{es-adj}}
  gloss: joyful, cheerful
_____
dentista
pos: n
  meta: {{es-noun|mf}}
  g: mf
  etymology: diente + -ista
  gloss: dentist
_____
rojo
pos: adj
  meta: {{es-adj}}
  gloss: red
"""

    return Wordlist(data.splitlines())

@pytest.fixture(scope = 'module')
def allforms(wordlist):
    return AllForms.from_wordlist(wordlist)

@pytest.fixture(scope = 'module')
def fixer(allforms):
    return T9nFixer(allforms)

@pytest.fixture(scope = 'module')
def fixrunner(allforms):
    return T9nFixRunner(allforms)

def test_spanish_noun(fixrunner):

    text = """
==English==
===Noun===
====Translations====
{{trans-top-also|red}}
* Spanish: {{t+|es|rojo|m}}, {{t+|es|roja|f}}
{{trans-bottom}}
"""

    # No changes because nouns aren't compacted
    expected = text

    res = fixrunner.cleanup_tables(text, "red")
    assert res == expected

def test_spanish_adj(fixrunner):

    text = """
==English==
===Adjective===
====Translations====
{{trans-top-also|red}}
* Spanish: {{t+|es|rojo|m}}, {{t+|es|roja|f}}
{{trans-bottom}}
"""
    expected = """
==English==
===Adjective===
====Translations====
{{trans-top-also|red}}
* Spanish: {{t+|es|rojo}}
{{trans-bottom}}
"""

    res = fixrunner.cleanup_tables(text, "red")
    assert res == expected

def test_ttbc(fixrunner):

    text = """
==English==
===Adjective===
====Translations====
{{trans-top-also|red}}
* {{ttbc|es}}: {{t+check|es|rojo|m}}, {{t+check|es|roja|f}}
{{trans-bottom}}
"""
    expected = """
==English==
===Adjective===
====Translations====
{{trans-top-also|red}}
* Spanish: {{t+check|es|rojo|m}}, {{t+check|es|roja|f}}
{{trans-bottom}}
"""

    res = fixrunner.cleanup_tables(text, "red")
    assert res == expected


def test_ttbc_no_tcheck(fixrunner):

    text = """
==English==
===Adjective===
====Translations====
{{trans-top-also|red}}
* {{ttbc|es}}: junky [[terrible]] [[awful]] junk {{blah}}
{{trans-bottom}}
"""
    expected = text # no change, because no t-check template

    res = fixrunner.cleanup_tables(text, "red")
    assert res == expected

def test_t_is_l(fixrunner):

    text = """
==English==
===Adjective===
====Translations====
{{trans-top-also|red}}
* Spanish: {{l|es|hombre|g=m}}
{{trans-bottom}}
"""

    expected = """
==English==
===Adjective===
====Translations====
{{trans-top-also|red}}
* Spanish: {{t|es|hombre|m}}
{{trans-bottom}}
"""

    res = fixrunner.cleanup_tables(text, "red")
    assert res == expected


def test_link_to_t(fixrunner):

    text = """
==English==
===Adjective===
====Translations====
{{trans-top-also|red}}
* Spanish: [[hombre]] {{g|m}}, {{t|es|blah}}
{{trans-bottom}}
"""

    expected = """
==English==
===Adjective===
====Translations====
{{trans-top-also|red}}
* Spanish: {{t|es|hombre|m}}, {{t|es|blah}}
{{trans-bottom}}
"""

    res = fixrunner.cleanup_tables(text, "red")
    assert res == expected


def test_thing(fixrunner):

    text = """
====Translations====
{{trans-top|peanut served with its husk}}
* Finnish: {{t|fi|[[kuorimaton]] [[maapähkinä]]}}
{{trans-mid}}
* Spanish: [[cacahuate estilo español]] {{g|m}} {{qualifier|Mexico}}
{{trans-bottom}}
"""

    expected = text

    res = fixrunner.cleanup_tables(text, "red")
    assert res == expected


