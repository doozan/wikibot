import pytest

from ..sectionparser import SectionParser
import autodooz.fix_section_headers as fixer

def test_fix_section_titles():

    text = """\
==English==

===Etymoloxx===
===adjective===
===Nouns===
====Nouns====
===Proper Noun===
===Referencxx===
===UsagX Notes===
"""

    result = """\
==English==

===Etymology===

===Adjective===

===Noun===

====Nouns====

===Proper noun===

===References===

===Usage notes===
"""

    entry = SectionParser(text, "test")
    assert fixer.fix_section_titles(entry) == True

    res = str(entry)
    print(res)

    entry = SectionParser(res, "test")
    assert fixer.fix_section_titles(entry) == False

    assert res.splitlines() == result.splitlines()


def test_fix_section_levels():

    text = """\
==English==
====Noun====
======Test======
========Test 1========
=======Test 2=======
===Adjective===
=====BlahA=====
====BlahB====
======BlahC======
"""

    result = """\
==English==

===Noun===

====Test====

=====Test 1=====

=====Test 2=====

===Adjective===

====BlahA====

====BlahB====

=====BlahC=====
"""

    entry = SectionParser(text, "test")

    assert fixer.fix_section_levels(entry) == True
    res = str(entry)
    entry = SectionParser(res, "test")
    assert fixer.fix_section_levels(entry) == False
    print(res)
    assert res.splitlines() == result.splitlines()


    text = """\
===Noun===
"""

    entry = SectionParser(text, "test")
    assert str(entry).strip() == text.strip()
#    with pytest.raises(Exception) as e_info:
#        fixer.fix_section_levels(entry)


def test_fix_remove_pos_counters():

    text = """\
==English==

===Etymology 1===
====Noun 1====
====Adjective 1====
====Noun 2====
===Etymology 2===
====Pronunciation 1====
=====Noun=====
"""

    result = """\
==English==

===Etymology 1===

====Noun====

====Adjective====

====Noun====

===Etymology 2===

====Pronunciation 1====

=====Noun=====
"""

    entry = SectionParser(text, "test")

    assert fixer.fix_remove_pos_counters(entry) == True
    res = str(entry)
    entry = SectionParser(res, "test")
    assert fixer.fix_remove_pos_counters(entry) == False
    print(res)

    assert res.splitlines() == result.splitlines()



def test_fix_section_counters():

    text = """\
==English==

===Etymology 1===
====Noun====
===Etymology 2===
====Pronunciation 1====
=====Noun=====
"""

    result = """\
==English==

===Etymology 1===

====Noun====

===Etymology 2===

====Pronunciation====

=====Noun=====
"""

    entry = SectionParser(text, "test")

    assert fixer.fix_counters(entry) == True
    res = str(entry)
    entry = SectionParser(res, "test")
    assert fixer.fix_counters(entry) == False
    print(res)

    assert res.splitlines() == result.splitlines()

def test_remove_empty_sections():

    text = """\
==English==

===Etymology 1===
====Adjective====
====Noun====
blah
=====Test=====
======Test======
"""

    result = """\
==English==

===Etymology 1===

====Noun====
blah
"""

    entry = SectionParser(text, "test")

    assert fixer.remove_empty_sections(entry) == True
    res = str(entry)
    entry = SectionParser(res, "test")
    assert fixer.remove_empty_sections(entry) == False
    print(res)

    assert res.splitlines() == result.splitlines()

def test_fix_bad_l2():

    text = """\
==English==

===Noun===
# test

== References ==
{{reflist}}
"""

    result = """\
==English==

===Noun===
# test

===References===
{{reflist}}
"""

    entry = SectionParser(text, "test")
    print(entry)

    assert fixer.fix_bad_l2(entry) == True
    res = str(entry)
    entry = SectionParser(res, "test")
    assert fixer.fix_bad_l2(entry) == False
    print(res)

    assert res.splitlines() == result.splitlines()


def test_t9n_moving():

    text = """
==English==

===Etymology 1===

====Noun====
{{en-noun}}

# {{lb|en|parapsychology}} An object that is spontaneously moved or "teleported" to another place.

=====Coordinate terms=====
* {{l|en|apport}}

===Translations===
{{trans-top}}
{{trans-mid}}
* Polish: {{t|pl|asport|m}}
{{trans-bottom}}

===Etymology 2===
Borrowed from {{bor|en|la|asportō}}.

====Alternative forms====
* {{alter|en|asportate||considered a mistake}}

====Verb====
{{en-verb}} {{tlb|en|US|legalese}}

# To take and move to a certain other place, to [[carry away]].

=====Related terms=====
* {{l|en|asportation}}

===Anagrams===
* {{anagrams|en|a=aoprst|Portas|Sproat|pastor|portas|sap rot|saprot}}
"""

    expected = """
==English==

===Etymology 1===

====Noun====
{{en-noun}}

# {{lb|en|parapsychology}} An object that is spontaneously moved or "teleported" to another place.

=====Coordinate terms=====
* {{l|en|apport}}

=====Translations=====
{{trans-top}}
{{trans-mid}}
* Polish: {{t|pl|asport|m}}
{{trans-bottom}}

===Etymology 2===
Borrowed from {{bor|en|la|asportō}}.

====Alternative forms====
* {{alter|en|asportate||considered a mistake}}

====Verb====
{{en-verb}} {{tlb|en|US|legalese}}

# To take and move to a certain other place, to [[carry away]].

=====Related terms=====
* {{l|en|asportation}}

===Anagrams===
* {{anagrams|en|a=aoprst|Portas|Sproat|pastor|portas|sap rot|saprot}}
"""

    entry = SectionParser(text, "test")
    assert fixer.move_misplaced_translations(entry) == True

    res = str(entry)
    assert res == expected


def test_t9n_moving2():

    text = """
==English==

===Etymology===
{{suffix|en|ataxia|ic}}

===Pronunciation===
* {{rhymes|en|æksɪk|s=3}}

===Adjective===
{{head|en|adjective}}

# Pertaining to [[ataxia]]
#* {{quote-text|en|year=1934|author={{w|George Orwell}}|title={{w|Burmese Days}}|chapter=15|url=http://www.gutenberg.net.au/ebooks02/0200051h.html|passage=Mr Lackersteen tottered after her, with a strange '''ataxic''' step caused partly by earth-tremors and partly by gin.}}
# {{lb|en|geology}} Not [[eutaxic]]

====Synonyms====
* {{l|en|atactic}}

===Translations===
{{trans-top|pertaining to ataxia}}
{{trans-mid}}
* Polish: {{t|pl|ataktyczny}}
{{trans-bottom}}

{{trans-top|geology}}
{{trans-mid}}
{{trans-bottom}}

===Noun===
{{en-noun}}

# A person suffering from [[ataxia]].

===Translations===
{{trans-top}}
{{trans-mid}}
{{trans-bottom}}

"""
    expected = """
==English==

===Etymology===
{{suffix|en|ataxia|ic}}

===Pronunciation===
* {{rhymes|en|æksɪk|s=3}}

===Adjective===
{{head|en|adjective}}

# Pertaining to [[ataxia]]
#* {{quote-text|en|year=1934|author={{w|George Orwell}}|title={{w|Burmese Days}}|chapter=15|url=http://www.gutenberg.net.au/ebooks02/0200051h.html|passage=Mr Lackersteen tottered after her, with a strange '''ataxic''' step caused partly by earth-tremors and partly by gin.}}
# {{lb|en|geology}} Not [[eutaxic]]

====Synonyms====
* {{l|en|atactic}}

====Translations====
{{trans-top|pertaining to ataxia}}
{{trans-mid}}
* Polish: {{t|pl|ataktyczny}}
{{trans-bottom}}

{{trans-top|geology}}
{{trans-mid}}
{{trans-bottom}}

===Noun===
{{en-noun}}

# A person suffering from [[ataxia]].

====Translations====
{{trans-top}}
{{trans-mid}}
{{trans-bottom}}
"""

    entry = SectionParser(text, "test")
    assert fixer.move_misplaced_translations(entry) == True

    res = str(entry)
    assert res == expected
