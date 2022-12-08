from ..fix_section_levels import SectionLevelFixer

def test_single_ety_no_children():

    text = """\
==English==

===Etymology===
blah

====Adjective====
# blah
"""

    result = """\
==English==

===Etymology===
blah

===Adjective===
# blah\
"""

    summary = []
    fixer = SectionLevelFixer()
    res = fixer.process(text, "test", summary)
    print(res)

    assert res == result


def test_multi_ety():

    text = """\
==English==

===Etymology===
blah

===Adjective===
# blah

===Etymology===
blah

===Noun===
# blah
"""

    result = """\
==English==

===Etymology 1===
blah

====Adjective====
# blah

===Etymology 2===
blah

====Noun====
# blah\
"""

    summary = []
    fixer = SectionLevelFixer()
    res = fixer.process(text, "test", summary)
    print(res)

    assert res == result


def test_single_ety_single_pronunciation():

    text = """\
==English==

===Etymology===
blah

===Pronunciation===
bl-ah

===Adjective===
# blah

===Noun===
# blah\
"""

    result = """\
==English==

===Etymology===
blah

===Pronunciation===
bl-ah

===Adjective===
# blah

===Noun===
# blah\
"""

    summary = []
    fixer = SectionLevelFixer()
    res = fixer.process(text, "test", summary)
    print(res)

    assert res == result

def test_multi_ety_single_pronunciation():

    text = """\
==English==

===Etymology===
blah

===Pronunciation===
bl-ah

===Adjective===
# blah

===Etymology===
blah

===Noun===
# blah
"""

    result = """\
==English==

===Pronunciation===
bl-ah

===Etymology 1===
blah

====Adjective====
# blah

===Etymology 2===
blah

====Noun====
# blah\
"""

    summary = []
    fixer = SectionLevelFixer()
    res = fixer.process(text, "test", summary)
    print(res)

    assert res == result

def test_multi_ety_single_pronunciation_not_first():

    text = """\
==English==

===Etymology===
blah

===Adjective===
# blah

===Etymology===
blah

===Pronunciation===
bl-ah

===Noun===
# blah
"""

    result = """\
==English==

===Etymology 1===
blah

====Adjective====
# blah

===Etymology 2===
blah

====Pronunciation====
bl-ah

====Noun====
# blah\
"""

    summary = []
    fixer = SectionLevelFixer()
    res = fixer.process(text, "test", summary)
    print(res)

    assert res == result

def test_multi_ety_single_pronunciation_with_child():

    text = """\
==English==

===Etymology===
blah

===Pronunciation===
bl-ah

====Adjective====
# blah

===Etymology===
blah

===Noun===
# blah
"""

    result = """\
==English==

===Pronunciation===
bl-ah

===Etymology 1===
blah

====Adjective====
# blah

===Etymology 2===
blah

====Noun====
# blah\
"""

    summary = []
    fixer = SectionLevelFixer()
    res = fixer.process(text, "test", summary)
    print(res)

    assert res == result


def test_multi_ety_multi_pronunciation():

    text = """\
==English==

===Etymology===
blah

===Pronunciation===
bl-ah

===Adjective===
# blah

===Etymology===
blah

===Pronunciation===
bl-ah2

===Noun===
# blah
"""

    result = """\
==English==

===Etymology 1===
blah

====Pronunciation====
bl-ah

====Adjective====
# blah

===Etymology 2===
blah

====Pronunciation====
bl-ah2

====Noun====
# blah\
"""

    summary = []
    fixer = SectionLevelFixer()
    res = fixer.process(text, "test", summary)
    print(res)

    assert res == result

def test_single_ety_multi_pronunciation():

    text = """\
==English==

===Etymology===
blah

===Pronunciation===
bl-ah

===Adjective===
# blah

===Pronunciation===
bl-ah2

===Noun===
# blah
"""

    result = """\
==English==

===Etymology===
blah

===Pronunciation 1===
bl-ah

====Adjective====
# blah

===Pronunciation 2===
bl-ah2

====Noun====
# blah\
"""

    summary = []
    fixer = SectionLevelFixer()
    res = fixer.process(text, "test", summary)
    print(res)

    assert res == result


def test_Hoth():
    # Multiple ety with multiple pronunciation, each ety should adopt the pronunciation
    # and each pronunciation should promote children to siblings

    text = """\
==English==
{wikipedia|Hoth (disambiguation)|Hoth|lang=en}

===Etymology 1===
{rfe|en}

===Pronunciation===
* {IPA|en|/hɒθ/|/hɒt/}

====Proper noun====
{en-proper noun|Hoths}

{surname|en}.

====Statistics====
* According to the 2010 United States Census, ''Hoth'' is the 26362<sup>nd</sup> most common surname in the United States, belonging to 926 individuals. ''Hoth'' is most common among White (90.71%) individuals.

===Etymology 2===
Named after the fictional ice planet of {w|lang=en|Hoth|''Hoth''} from the 1980 U.S. science fiction film ''{{w|lang=en|Star Wars (franchise)|Star Wars}}: Episode V: {{w|lang=en|The Empire Strikes Back}}'', due to its extremely cold surface temperature.

===Pronunciation===
* {IPA|en|/hɒθ/}

====Proper noun====
{en-proper-noun}

{C|en|Planets} {{lb|en|planets}} {{place|en|planet|star system:suf/OGLE-2005-BLG-390L|galaxy/Milky Way Galaxy|contellation:suf/Scorpius}}
#: {syn|en|OGLE-2005-BLG-390Lb|OGLE 2005-BLG-390L b|OGLE-05-BLG-390Lb|OGLE 05-BLG-390L b|EWS-2005-BUL-390b|EWS 2005-BUL-390 b|EWS-05-BUL-390b|EWS 05-BUL-390 b|EWS-2005-BLG-390b|EWS 2005-BLG-390 b|EWS-05-BLG-390b|EWS 05-BLG-390 b}

====Further reading====
* {pedia|lang=en|OGLE-2005-BLG-390Lb}

===Etymology 3===
See {m|en|Höðr}.

====Proper noun====
{en-proper-noun}

{alternative form of|en|Höðr}
"""

    result = """\
==English==
{wikipedia|Hoth (disambiguation)|Hoth|lang=en}

===Etymology 1===
{rfe|en}

====Pronunciation====
* {IPA|en|/hɒθ/|/hɒt/}

====Proper noun====
{en-proper noun|Hoths}

{surname|en}.

====Statistics====
* According to the 2010 United States Census, ''Hoth'' is the 26362<sup>nd</sup> most common surname in the United States, belonging to 926 individuals. ''Hoth'' is most common among White (90.71%) individuals.

===Etymology 2===
Named after the fictional ice planet of {w|lang=en|Hoth|''Hoth''} from the 1980 U.S. science fiction film ''{{w|lang=en|Star Wars (franchise)|Star Wars}}: Episode V: {{w|lang=en|The Empire Strikes Back}}'', due to its extremely cold surface temperature.

====Pronunciation====
* {IPA|en|/hɒθ/}

====Proper noun====
{en-proper-noun}

{C|en|Planets} {{lb|en|planets}} {{place|en|planet|star system:suf/OGLE-2005-BLG-390L|galaxy/Milky Way Galaxy|contellation:suf/Scorpius}}
#: {syn|en|OGLE-2005-BLG-390Lb|OGLE 2005-BLG-390L b|OGLE-05-BLG-390Lb|OGLE 05-BLG-390L b|EWS-2005-BUL-390b|EWS 2005-BUL-390 b|EWS-05-BUL-390b|EWS 05-BUL-390 b|EWS-2005-BLG-390b|EWS 2005-BLG-390 b|EWS-05-BLG-390b|EWS 05-BLG-390 b}

====Further reading====
* {pedia|lang=en|OGLE-2005-BLG-390Lb}

===Etymology 3===
See {m|en|Höðr}.

====Proper noun====
{en-proper-noun}

{alternative form of|en|Höðr}\
"""

    summary = []
    fixer = SectionLevelFixer()
    res = fixer.process(text, "test", summary)
    print(res)

    assert res == result



def test_abecedaria():

    # ===Ety 1===
    # ====Pronunciation 1====
    # ===Pronunciation 2===
    # ===Ety 2===
    #
    # Ety 1 should adopt Pro2, making it a L4
    #
    # Detect page order of countables

    text = """\
==Latin==

===Etymology 1===
Substantive from {{m|la|abecedārius||alphabetical}}.

====Pronunciation 1====
* {{la-IPA|abecedāria|cl=no}}

=====Noun=====
{{la-noun|abecedāria<1>}}

# An [[elementary]] [[instruction]].

===Pronunciation 2===
* {{la-IPA|abecedāriā|cl=no}}

====Noun====
{{la-noun-form|abecedāriā|g=f}}

# {{inflection of|la|abecedāria||abl|s}}

===Etymology 2===

====Noun====
{{la-noun-form|abecedāria}}

# {{inflection of|la|abecedārium||nom//acc//voc|p}}
"""

    result = """\
==Latin==

===Etymology 1===
Substantive from {{m|la|abecedārius||alphabetical}}.

====Pronunciation 1====
* {{la-IPA|abecedāria|cl=no}}

=====Noun=====
{{la-noun|abecedāria<1>}}

# An [[elementary]] [[instruction]].

====Pronunciation 2====
* {{la-IPA|abecedāriā|cl=no}}

=====Noun=====
{{la-noun-form|abecedāriā|g=f}}

# {{inflection of|la|abecedāria||abl|s}}

===Etymology 2===

====Noun====
{{la-noun-form|abecedāria}}

# {{inflection of|la|abecedārium||nom//acc//voc|p}}\
"""

    summary = []
    fixer = SectionLevelFixer()
    res = fixer.process(text, "test", summary)
    print(res)

    assert res == result


def test_nested_sibling():

    # ===Ety 1===
    # ====Ety 2====
    #
    # Ety 1 should promote Ety 2 to sibling, and both should preserve numbering

    text = """\
==Latin==

===Etymology 1===
Substantive from {{m|la|abecedārius||alphabetical}}.

====Noun====
{{la-noun|abecedāria<1>}}

# An [[elementary]] [[instruction]].

====Etymology 2====

====Noun====
{{la-noun-form|abecedāria}}

# {{inflection of|la|abecedārium||nom//acc//voc|p}}
"""

    result = """\
==Latin==

===Etymology 1===
Substantive from {{m|la|abecedārius||alphabetical}}.

====Noun====
{{la-noun|abecedāria<1>}}

# An [[elementary]] [[instruction]].

===Etymology 2===

====Noun====
{{la-noun-form|abecedāria}}

# {{inflection of|la|abecedārium||nom//acc//voc|p}}\
"""

    summary = []
    fixer = SectionLevelFixer()
    res = fixer.process(text, "test", summary)
    print(res)

    assert res == result


# very few hits, safer to leave for manual review
def no_test_l3_language():


    text = """\
==Latin==

===Noun===
# test

===Spanish===

====Noun====
# test
"""

    result = """\
==Latin==

===Noun===
# test

----

==Spanish==

===Noun===
# test\
"""

    summary = []
    fixer = SectionLevelFixer()
    res = fixer.process(text, "test", summary)
    print(res)

    assert res == result

def test_pos_adopt():

    text = """\
==English==

===Etymology===

===Noun===

===Synonyms===

===Derived terms===

===Related terms===

===Translations===\
"""

    result = """\
==English==

===Etymology===

===Noun===

====Synonyms====

====Derived terms====

====Related terms====

====Translations====\
"""

    summary = []
    fixer = SectionLevelFixer()
    res = fixer.process(text, "test", summary)
    print(res)

    assert res == result


def test_pos_adopt_without_ety():

    text = """\
==English==

===Noun===

===Synonyms===

===Derived terms===

===Related terms===

===Translations===\
"""

    result = """\
==English==

===Noun===

====Synonyms====

====Derived terms====

====Related terms====

====Translations====\
"""

    summary = []
    fixer = SectionLevelFixer()
    res = fixer.process(text, "test", summary)
    print(res)

    assert res == result


def test_complex():

    # L4 Derived terms should become L5

    text = """\
==English==

===Etymology 1===

====Noun====

=====Synonyms=====

====Derived terms====

=====Related terms=====

=====Translations=====

===Etymology 2===

====Verb====\
"""

    result = """\
==English==

===Etymology 1===

====Noun====

=====Synonyms=====

=====Derived terms=====

=====Related terms=====

=====Translations=====

===Etymology 2===

====Verb====\
"""

    summary = []
    fixer = SectionLevelFixer()
    res = fixer.process(text, "test", summary)
    print(res)

    assert res == result


def test_complex2():

    # sorting

    text = """\
==English==

===Etymology 1===

====Noun====

=====Synonyms=====

=====Translations=====

====Derived terms====

====Related terms====

===Etymology 2===

====Verb====\
"""

    result = """\
==English==

===Etymology 1===

====Noun====

=====Synonyms=====

=====Derived terms=====

=====Related terms=====

=====Translations=====

===Etymology 2===

====Verb====\
"""

    summary = []
    fixer = SectionLevelFixer()
    res = fixer.process(text, "test", summary)
    print(res)

    assert res == result


def test_complex_single_entry():

    # L4 Derived terms should become L5

    text = """\
==English==

===Etymology===

===Noun===

====Synonyms====

===Derived terms===

====Related terms====

====Translations====\
"""

    result = """\
==English==

===Etymology===

===Noun===

====Synonyms====

====Derived terms====

====Related terms====

====Translations====\
"""

    summary = []
    fixer = SectionLevelFixer()
    res = fixer.process(text, "test", summary)
    print(res)

    assert res == result


def test_nested_countable():

    # L4 Derived terms should become L5

    text = """\
==Latin==

===Etymology 1===

====Pronunciation====

=====Definitions=====

====Pronunciation====

=====Definitions=====

===Etymology 2===

====Pronunciation====\
"""

    result = """\
==Latin==

===Etymology 1===

====Pronunciation 1====

=====Definitions=====

====Pronunciation 2====

=====Definitions=====

===Etymology 2===

====Pronunciation====\
"""

    summary = []
    fixer = SectionLevelFixer()
    res = fixer.process(text, "test", summary)
    print(res)

    assert res == result


def test_bad_nested_countable():

    # Order of operations, because Pronunciation is first,
    # it should detect the solitary Pronunciation and promote all children
    # Then then it should find both Etymologies on the same level and handle
    # them accordingly

    text = """\
==Latin==

===Pronunciation===

====Etymology 1====

====Noun====

===Etymology 2===

====Noun====\
"""

    result = """\
==Latin==

===Pronunciation===

===Etymology 1===

====Noun====

===Etymology 2===

====Noun====\
"""

    summary = []
    fixer = SectionLevelFixer()
    res = fixer.process(text, "test", summary)
    print(res)

    assert res == result


def test_adopt_matched_cousin():

    # Final POS should adopt "See also" since Letter already has a "See also" section

    text = """\
==Albanian==

===Pronunciation===

===Letter===

====See also====

===Preposition===

===Article===

===See also===

===Related terms===\
"""

    result = """\
==Albanian==

===Pronunciation===

===Letter===

====See also====

===Preposition===

===Article===

====See also====

===Related terms===\
"""

    summary = []
    fixer = SectionLevelFixer()
    res = fixer.process(text, "test", summary)
    print(res)

    assert res == result

def test_multi_adoptions():

    text = """\
==Manx==

===Etymology===

===Proper noun===

====Derived terms====

===Mutation===

----

==Welsh==

===Etymology===

===Proper noun===

====Derived terms====

===Mutation===\
"""

    result = """\
==Manx==

===Etymology===

===Proper noun===

====Mutation====

====Derived terms====

----

==Welsh==

===Etymology===

===Proper noun===

====Mutation====

====Derived terms====\
"""


    summary = []
    fixer = SectionLevelFixer()
    res = fixer.process(text, "test", summary)
#    print(res)

    assert res == result

def test_adopt_grandchildren():

    # L3 Usage Notes + L4 See also should result in both as L4,
    # which is different than if both started as L3, then only Usage notes would be adopted

    text = """\
==Mandarin==

===Letter===

===Usage notes===

====See also====\
"""

    result = """\
==Mandarin==

===Letter===

====Usage notes====

====See also====\
"""

    summary = []
    fixer = SectionLevelFixer()
    res = fixer.process(text, "test", summary)
#    print(res)

    assert res == result

def test_dont_adopt_uncles():

    # L3 Usage Notes + L4 See also should result in both as L4,
    # which is different than if both started as L3, then only Usage notes would be adopted

    text = """\
==English==

===Etymology 1===

====Noun====

===Etymology 2===

====Verb====

===Usage notes===\
"""

    result = """\
==English==

===Etymology 1===

====Noun====

===Etymology 2===

====Verb====

===Usage notes===\
"""

    summary = []
    fixer = SectionLevelFixer()
    res = fixer.process(text, "test", summary)
#    print(res)

    assert res == result

def test_no_nested_pos():

    # POS should not contain another POS

    text = """\
==Hawaiian==

===Etymology 1===

====Determiner====

===Etymology 2===

===Noun===

====Verb====\
"""

    result = """\
==Hawaiian==

===Etymology 1===

====Determiner====

===Etymology 2===

====Noun====

====Verb====\
"""

    summary = []
    fixer = SectionLevelFixer()
    res = fixer.process(text, "test", summary)
#    print(res)

    assert res == result

def test_fix_anagrams():

    # Anagrams should always be childless, L3

    text = """\
==Hawaiian==

===Noun===

====Anagrams====

=====Further reading=====\
"""

    result = """\
==Hawaiian==

===Noun===

====Further reading====

===Anagrams===\
"""


    summary = []
    fixer = SectionLevelFixer()
    res = fixer.process(text, "test", summary)
#    print(res)

    assert res == result
