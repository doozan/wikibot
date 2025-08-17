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

