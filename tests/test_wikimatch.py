import re
from ..wikimatch import Match, get_matches

def test_get_match():

    title = "test"
    full_text = """\
==Latin==

===Adjective===
{{la-adj-comp|abascantior|pos=abascantus}}

# more [[unenvied]]

====Declension====
{{la-adecl|abascantior}}
"""

    re_not = None
    no_path = ""
    dotall = False
    path_filter = None

    re_match = "la-adj-comp"
    match_context = "section"
    no_children = True

    res = get_matches(title, full_text, re_match, re_not, match_context, no_path, dotall, path_filter, no_children)
    assert res == [Match(path='test:Latin:Adjective', path_index=None, match_index=None, start=11, end=91)]

    # Match header
    re_match = '===Adjective==='
    res = get_matches(title, full_text, re_match, re_not, match_context, no_path, dotall, path_filter, no_children)
    assert res == [Match(path='test:Latin:Adjective', path_index=(2, 2), match_index=None, start=11, end=91)]

    # Match inside header
    re_match = 'djectiv'
    res = get_matches(title, full_text, re_match, re_not, match_context, no_path, dotall, path_filter, no_children)
    assert res == [Match(path='test:Latin:Adjective', path_index=(3, 3), match_index=None, start=11, end=91)]

    # Match end of section
    re_matche = re.escape('# more [[unenvied]]\n')
    res = get_matches(title, full_text, re_match, re_not, match_context, no_path, dotall, path_filter, no_children)
    assert res == [Match(path='test:Latin:Adjective', path_index=(4, 4), match_index=None, start=11, end=91)]

    # Match entire section
    re_match = "^" + re.escape('===Adjective===\n{{la-adj-comp|abascantior|pos=abascantus}}\n\n# more [[unenvied]]\n') + "$"
    res = get_matches(title, full_text, re_match, re_not, match_context, no_path, dotall, path_filter, no_children)
    assert res == [Match(path='test:Latin:Adjective', path_index=(5, 5), match_index=None, start=11, end=91)]


