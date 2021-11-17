import pytest
from ..sectionparser import SectionParser

def test_basic1():
    text = """\
{{also|Dictionary}}
==  English==
blah

=== Noun  ======= <!-- This is a comment -->
blah

<!--
=== Adjective ===
blah
!-->


----
==Thai==   

blah

====Noun====
# text


----


==Spanish==
[[Category:blah]]

=== Noun ====

[[Category:blah2]]
# blah

====Usage notes====
* info

===Anagrams===
# anagrams

===Further reading===
* {{R:DRAE}}
"""

    result = """\
{{also|Dictionary}}
==English==
blah

===Noun=======
<!-- This is a comment -->
blah

<!--
=== Adjective ===
blah
!-->

----

==Thai==
blah

====Noun====
# text

----

==Spanish==

===Noun====
# blah

====Usage notes====
* info

===Anagrams===
# anagrams

===Further reading===
* {{R:DRAE}}

[[Category:blah]]
[[Category:blah2]]
"""

    parsed = SectionParser(text, "test")

    assert len(parsed._children) == 3
    assert len(list(parsed.ifilter_sections())) == 9

    res = str(parsed)
    assert res.splitlines() == result.splitlines()

def test_l2_joiner():
    text = """\
==Translingual==
----
==English==

----
==Thai==

----

==Spanish==


----

"""

    result = """\
==Translingual==

----

==English==

----

==Thai==

----

==Spanish==
"""

    parsed = SectionParser(text, "test")
    res = str(parsed)
    print(res)
    assert res.splitlines() == result.splitlines()
