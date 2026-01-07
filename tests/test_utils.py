import autodooz.utils as utils

def test_split_namespace():
    split_namespace = utils.split_namespace

    assert split_namespace("Template:test") == ("Template", "test")
    assert split_namespace("TEMPLATE:test") == ("Template", "test")
    assert split_namespace("TeMpLaTE:test") == ("Template", "test")
    print(utils.ALIAS_TO_NAMESPACE)
    assert split_namespace("T:test") == ("Template", "test")

    assert split_namespace("R:test") == (None, "R:test")

def test_template_aware_finditer():
    template_aware_finditer = utils.template_aware_finditer
    assert list((m.start(), m.end())  for m in template_aware_finditer("t.*?t", "{{test}}")) == []
    assert list((m.start(), m.end())  for m in template_aware_finditer("t.*?t", "{{test}} test")) == [(9,13)]


def test_get_nest_depth():

    get_nest_depth = utils.get_nest_depth

    assert get_nest_depth("{{test", "{{", "}}") == 1
    assert get_nest_depth("{{", "{{", "}}") == 1
    assert get_nest_depth("{{test}}", "{{", "}}") == 0
    assert get_nest_depth("{{test{{test", "{{", "}}") == 2
    assert get_nest_depth("{{test{{test}}", "{{", "}}") == 1
    assert get_nest_depth("{{test{{test}}}", "{{", "}}") == 1
    assert get_nest_depth("{{test{{test}}}}", "{{", "}}") == 0

def test_nest_aware_split():
    test = utils.nest_aware_split
    assert list(test(",", "(a,(b,(c))),d,(e,f)", [("(",")")])) == ['(a,(b,(c)))', 'd', '(e,f)']

    assert list(test("(", "(a,(b,(c))),d,(e,f)", [("(",")")])) == ['', 'a,(b,(c))),d,', 'e,f)']

def test_nest_aware_find():
    nest_aware_find = utils.nest_aware_find
    assert nest_aware_find(",", "(a,b),c,d", [("<",">")]) == 2
    assert nest_aware_find(",", "(a,b),c,d", [("(",")")]) == 5

def test_nest_aware_rfind():
    nest_aware_rfind = utils.nest_aware_rfind
    text = "a, b, (c, d)"
    assert text.rfind(",") == 8
    assert nest_aware_rfind(",", text, [("<",">")]) == 8
    assert nest_aware_rfind(",", text, [("(",")")]) == 4

    assert text.rfind(", ") == 8
    assert nest_aware_rfind(", ", text, [("<",">")]) == 8
    assert nest_aware_rfind(", ", text, [("(",")")]) == 4

    assert nest_aware_rfind("(", text, [("(",")")]) == 6
    assert nest_aware_rfind("(", "foo(bar(test))", [("(",")")]) == 3
