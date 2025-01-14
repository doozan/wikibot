from autodooz.fix_missing_headers import HeaderFixer

fixer = HeaderFixer()

def test_add_missing_rfdef():

    text = """\
==English==

===Adjective===
{{en-adj}}

# Having crinkles

{{trans-top|having crinkles}}
* Esperanto: {{t|eo|krispa}}
{{trans-bottom}}

====Derived terms====
* stuff\
"""

    expected = """\
==English==

===Adjective===
{{en-adj}}

# Having crinkles

====Translations====
{{trans-top|having crinkles}}
* Esperanto: {{t|eo|krispa}}
{{trans-bottom}}

====Derived terms====
* stuff\
"""


    summary = []
    res = fixer.process(text, "page", summary)
    assert res == expected





    # Add missing header
    text = """\
==English==

===Noun===
{{head|en|noun}}

# def



{{trans-top}}
blah
{{trans-bottom}}


"""

    expected = """\
==English==

===Noun===
{{head|en|noun}}

# def

====Translations====
{{trans-top}}
blah
{{trans-bottom}}\
"""

    summary = []
    res = fixer.process(text, "page", summary)
    assert res == expected
