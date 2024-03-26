from autodooz.fix_rq_template import RqTemplateFixer
from autodooz.escape_template import escape

fixer = RqTemplateFixer(None)

def test_get_synonyms():

    text = " {{{4|{{{ passage | {{{text}}}}}}}}} "
    text= escape(text)
    print(text)
    assert fixer.get_synonyms(text) == ["4", "passage", "text"]

    text = " {{{4|{{{ passage | {{{text|}}}}}}}}} "
    text= escape(text)
    assert fixer.get_synonyms(text) == ["4", "passage", "text"]

    text = "{{{4|}}}"
    text= escape(text)
    assert fixer.get_synonyms(text) == ["4"]

    text = "{{{4}}}"
    text= escape(text)
    assert fixer.get_synonyms(text) == ["4"]

    text = "{{{4}}} {{{5}}}"
    text= escape(text)
    assert fixer.get_synonyms(text) == None

    text = "test"
    text= escape(text)
    assert fixer.get_synonyms(text) == None

    text = ""
    text= escape(text)
    assert fixer.get_synonyms(text) == []



