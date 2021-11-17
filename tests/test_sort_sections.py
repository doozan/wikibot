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

==Votic==

----

==Võro==

----

==Yoruba==

----

==Yámana==
"""

    parsed = SectionParser(text, "test")
    sort_languages(parsed)

    res = str(parsed)
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

