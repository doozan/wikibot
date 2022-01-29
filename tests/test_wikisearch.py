import pytest
from ..wikisearch import wiki_search

def test_basic1():
    text = """\
START
  blah1
END

START
  blah2
END

START
  blah3
START
  blah4
END

END

START
  blah5
"""

    res = wiki_search(text, "START")
    res = list(map(str.splitlines,res))
    print(res)
    assert res == [['START', '  blah1', 'END', ''], ['START', '  blah2', 'END', ''], ['START', '  blah3'], ['START', '  blah4', 'END', '', 'END', ''], ['START', '  blah5']]

    res = wiki_search(text, "START", "END", False)
    res = list(map(str.splitlines,res))
    print(res)
    assert res == [['START', '  blah1', 'END'], ['START', '  blah2', 'END'], ['START', '  blah3'], ['START', '  blah4', 'END'], ['START', '  blah5']]

    res = wiki_search(text, "START", "END", True)
    res = list(map(str.splitlines,res))
    print(res)
    assert res == [['START', '  blah1', 'END'], ['START', '  blah2', 'END'], ['START', '  blah3', 'START', '  blah4', 'END']]


def test_ignore_templates():
    text = """\
START
  blah1
END
{{template|
START
  blah2
END
}}
"""

    res = wiki_search(text, "START", "END")
    res = list(map(str.splitlines,res))
    print(res)
    assert res == [['START', '  blah1', 'END']]

    res = wiki_search(text, "START", "END", ignore_templates=True)
    res = list(map(str.splitlines,res))
    print(res)
    assert res == [['START', '  blah1', 'END'], ['START', '  blah2', 'END']]


def test_ignore_nowiki():
    text = """\
START
  blah1
END
<nowiki>
START
  blah2
END
</nowiki>
"""

    res = wiki_search(text, "START", "END", ignore_nowiki=False)
    res = list(map(str.splitlines,res))
    print(res)

    res = wiki_search(text, "START", "END", ignore_nowiki=True)
    res = list(map(str.splitlines,res))
    print(res)


def test_ignore_comments():
    text = """\
<!-- comment -->
START
  blah1
END
<!--
START
  blah2
END
-->
<!--START
blah3
END-->
"""

    res = wiki_search(text, "START", "END")
    res = list(map(str.splitlines,res))
    print(res)
    assert res == [['START', '  blah1', 'END']]

    res = wiki_search(text, "START", "END", ignore_comments=True)
    res = list(map(str.splitlines,res))
    print(res)
    assert res == [['START', '  blah1', 'END'], ['START', '  blah2', 'END'], ['START', 'blah3', 'END']]


def test_ignore_nested():
    text = """\
START
  blah1
END
{{template|
<nowiki>
START
  blah2
END
</nowiki>
}}
"""

    res = wiki_search(text, "START", "END")
    res = list(map(str.splitlines,res))
    assert res == [['START', '  blah1', 'END']]

    res = wiki_search(text, "START", "END", ignore_nowiki=True)
    res = list(map(str.splitlines,res))
    assert res == [['START', '  blah1', 'END']]

    res = wiki_search(text, "START", "END", ignore_templates=True)
    res = list(map(str.splitlines,res))
    assert res == [['START', '  blah1', 'END']]

    res = wiki_search(text, "START", "END", ignore_nowiki=True, ignore_templates=True)
    res = list(map(str.splitlines,res))
    assert res == [['START', '  blah1', 'END'], ['START', '  blah2', 'END']]

def test_veggie():

    text = """\
before
pre {{trans-top}} post
blah
{{trans-mid}}
pre {{trans-bottom}} post
after
"""

    TOP_TEMPLATES = ("trans-top", "trans-top-see", "trans-top-also", "checktrans-top", "ttbc-top")
    BOTTOM_TEMPLATES = ("checktrans-bottom", "trans-bottom", "ttbc-bottom")
    SKIP_LINES = ["{{trans-mid}}"]
    RE_TOP_TEMPLATES = "|".join(TOP_TEMPLATES)
    RE_BOTTOM_TEMPLATES = "|".join(BOTTOM_TEMPLATES)


    res = wiki_search(text,
                fr"^.*{{{{\s*({RE_TOP_TEMPLATES})",
                fr"{{{{\s*({RE_BOTTOM_TEMPLATES})\s*}}}}.*$",
                end_required=False,
                ignore_templates=True,
                ignore_nowiki=True,
            )

    res = list(map(str.splitlines,res))
    assert res == [['pre {{trans-top}} post', 'blah', '{{trans-mid}}', 'pre {{trans-bottom}} post']]

