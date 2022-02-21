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
blah

==References==
"""

    result = """\
==English==

===Noun===
blah

===References===
"""

    entry = SectionParser(text, "test")
    print(entry)

    assert fixer.fix_bad_l2(entry) == True
    res = str(entry)
    entry = SectionParser(res, "test")
    assert fixer.fix_bad_l2(entry) == False
    print(res)

    assert res.splitlines() == result.splitlines()

