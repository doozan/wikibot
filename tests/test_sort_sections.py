import pytest

from ..sectionparser import SectionParser
from ..sort_sections import sort_languages, sort_pos

def test_sort_languages():
    text = """\
==Thai==
==Translingual==
==Spanish==
==English==
==Aisi==
==Estonian==
==Finnish==
==Hawaiian==
==Yoruba==
==Yámana==
==Votic==
==Võro==
"""

    result = """\
==Translingual==

----

==English==

----

==Aisi==

----

==Estonian==

----

==Finnish==

----

==Hawaiian==

----

==Spanish==

----

==Thai==

----

==Võro==

----

==Votic==

----

==Yámana==

----

==Yoruba==
"""

    parsed = SectionParser(text, "test")
    sort_languages(parsed)

    res = str(parsed)
    print(res)
    assert res.splitlines() == result.splitlines()


def test_l3_sort():
    text = """\
==Spanish==
{{wikipedia|lang=es}}

===Etymology===
Borrowed from {{bor|es|la|āctiō|āctiō, āctiōnem}}, from {{m|la|ago|agere}}.

===Pronunciation===
{{es-IPA}}
* {{rhymes|es|on|s=2}}
* {{hyphenation|es|ac|ción}}
* {{audio|es|Es-am-lat-acción.ogg|Audio (Latin America)}}

===Noun===
{{es-noun|f}}

# [[action]], [[act]], [[deed]] {{gloss|something done}}
#: {{syn|es|acto}}

===Interjection===
{{head|es|interjection}}

# [[action]] {{gloss|demanding the start of something}}\
"""

    # out of order lemmas retain their original order
    result = text

    entry = SectionParser(text, "test")
    spanish = next(entry.ifilter_sections(matches=lambda x: x.title == "Spanish", recursive=False))
    sort_pos(spanish)

    res = str(entry)
    print(res)
    assert res.splitlines() == result.splitlines()




def test_l3_sort_lemma_first():
    text = """\
==Spanish==

===Pronunciation===
{{es-IPA}}

===Adjective===
{{head|es|adjective form}}

# {{adj form of|es|abajero||f|s}}

===Noun===
{{es-noun|f}}

# {{lb|es|Argentina|Chile|Uruguay}} [[saddlecloth]]

===Further reading===
* {{R:es:DRAE}}\
"""

    result = """\
==Spanish==

===Pronunciation===
{{es-IPA}}

===Noun===
{{es-noun|f}}

# {{lb|es|Argentina|Chile|Uruguay}} [[saddlecloth]]

===Adjective===
{{head|es|adjective form}}

# {{adj form of|es|abajero||f|s}}

===Further reading===
* {{R:es:DRAE}}\
"""

    entry = SectionParser(text, "test")
    spanish = next(entry.ifilter_sections(matches=lambda x: x.title == "Spanish", recursive=False))
    sort_pos(spanish)

    res = str(entry)
    print(res)
    assert res.splitlines() == result.splitlines()




def notest_ety():
    text = """\
==Slovak==

===Pronunciation===
* {{sk-IPA|ďeďinčaňia}}

===Etymology 1===

===Noun===
{{sk-noun|g=m-p}}

# [[countryfolk]]

===Etymology 2===
{{nonlemma}}

===Noun===
{{head|sk|noun form}}

# {{inflection of|sk|dedinčan||nom|p}}

[[Category:sk:People]]
"""

    result = """\
==Slovak==

===Pronunciation===
* {{sk-IPA|ďeďinčaňia}}

===Etymology 1===

====Noun====
{{sk-noun|g=m-p}}

# [[countryfolk]]

===Etymology 2===
{{nonlemma}}

====Noun====
{{head|sk|noun form}}

# {{inflection of|sk|dedinčan||nom|p}}

[[Category:sk:People]]
"""

    res = str(SectionSorter(text, "test"))
    print(res)

    #assert res.splitlines() == text.splitlines()
    assert res.splitlines() == result.splitlines()



def notest_multi_references():
    text = """\
==Slovak==

===Pronunciation===
* {{sk-IPA|ďeďinčaňia}}

====References====
<references/>

===Noun===
{{sk-noun|g=m-p}}

# [[countryfolk]]

===References===
* {{R:PSJC}}
"""

    result = """\
==Slovak==

===Pronunciation===
* {{sk-IPA|ďeďinčaňia}}

===Noun===
{{sk-noun|g=m-p}}

# [[countryfolk]]

===References===
<references/>
* {{R:PSJC}}
"""

    res = str(SectionSorter(text, "test"))
    print(res)

    #assert res.splitlines() == text.splitlines()
    assert res.splitlines() == result.splitlines()

