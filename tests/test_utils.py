import autodooz.utils as utils

def test_split_namespace():
    split_namespace = utils.split_namespace

    assert split_namespace("Template:test") == ("Template", "test")
    assert split_namespace("TEMPLATE:test") == ("Template", "test")
    assert split_namespace("TeMpLaTE:test") == ("Template", "test")
    print(utils.ALIAS_TO_NAMESPACE)
    assert split_namespace("T:test") == ("Template", "test")

    assert split_namespace("R:test") == (None, "R:test")
