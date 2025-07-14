from autodooz.fix_pronunciation import PronunciationFixer, extract_refs, parse_ipa_list, make_ipa_template
import enwiktionary_sectionparser as sectionparser

fixer = PronunciationFixer()


def test_ref():

    text = """\
==English==

===Pronunciation===
* {{IPA|en|/ˈhəʊbən/}} <ref name="test">{{cite-web |url=https://improveyouraccent.co.uk/tube/ |title=How to Pronounce London Underground Tube Stations |author=Luke Nicholson |work=Improve Your Accent }}</ref>
** {{audio|en|LL-Q7979-Soundguys-Holborn.wav|a=UK}}
* {{IPA|en|/ˈhɒlbərn/}} <!--see Wikipedia-->
* {{IPA|en|/ˈkɒk.s(ə)n/|a=RP}}; {{IPA|en|/ˈkɒkˌsweɪn/|a=[[spelling pronunciation]]}}
* {{IPA|en|/ˈkɒk.s(ə)n/}}; {{IPA|en|/ˈkɒkˌsweɪn/|a=[[spelling pronunciation]]}}
* {{IPA|en|/-ˌdɪs.ɪs/}} or {{IPA|en|/-ˈdiːsɪs/}}
* {{IPA|ja|/kòɡàjáʔꜜ/|a=Kagoshima}} (tone class B)<ref name="GNHD">{{R:Hirayama et al 1992-1994|page=1275}}</ref>
* {{IPA|en|/ɑbərˈdonjən/|/ebərˈdonjən/|a=Scotland}}<ref name="SND">{{R:DSL|pos=prop.n}}</ref>
test {{IPA|en|/ən/}}
* {{IPA|en|[ˈɡɒɹ̠wiː]|a=RP}};
* {{IPA|en|/koɹ/|a=GA}}<!-- comment --><ref>{{R:Dictionary.com|anemochore}}</ref>
* {{IPA|en|/ɑbərˈdonjən/|/ebərˈdonjən/|a=Scotland}}<ref name="SND">{{R:DSL|pos=prop.n}}</ref>
* {{IPA|ga|/eːn̪ˠ/|/eːnˠ/|ref2={{R:ga:Finck|II|94}}}}<ref name=DB />
"""

    expected = """\
==English==

===Pronunciation===
* {{IPA|en|/ˈhəʊbən/<ref:{{cite-web |url=https://improveyouraccent.co.uk/tube/ |title=How to Pronounce London Underground Tube Stations |author=Luke Nicholson |work=Improve Your Accent }}<<name:test>>>}}
** {{audio|en|LL-Q7979-Soundguys-Holborn.wav|a=UK}}
* {{IPA|en|/ˈhɒlbərn/}} <!--see Wikipedia-->
* {{IPA|en|/ˈkɒk.s(ə)n/<a:RP>|/ˈkɒkˌsweɪn/<a:[[spelling pronunciation]]>}}
* {{IPA|en|/ˈkɒk.s(ə)n/}}; {{IPA|en|/ˈkɒkˌsweɪn/|a=[[spelling pronunciation]]}}
* {{IPA|en|/-ˌdɪs.ɪs/|/-ˈdiːsɪs/}}
* {{IPA|ja|/kòɡàjáʔꜜ/|a=Kagoshima}} (tone class B)<ref name="GNHD">{{R:Hirayama et al 1992-1994|page=1275}}</ref>
* {{IPA|en|/ɑbərˈdonjən/|/ebərˈdonjən/|a=Scotland}}<ref name="SND">{{R:DSL|pos=prop.n}}</ref>
test {{IPA|en|/ən/}}
* {{IPA|en|[ˈɡɒɹ̠wiː]|a=RP}};
* {{IPA|en|/koɹ/|a=GA}}<!-- comment --><ref>{{R:Dictionary.com|anemochore}}</ref>
* {{IPA|en|/ɑbərˈdonjən/|/ebərˈdonjən/|a=Scotland}}<ref name="SND">{{R:DSL|pos=prop.n}}</ref>
* {{IPA|ga|/eːn̪ˠ/|/eːnˠ/|ref2={{R:ga:Finck|II|94}}}}<ref name=DB />
""".rstrip()

    summary = []
    res = fixer.process(text, "page", summary)
    print("SUMMARY", summary)
    print(res)
    assert res == expected

def test_multiline_ref():

    text = """\
==English==

===Pronunciation===
* {{IPA|en|/ˈhəʊbən/}}<ref> {{cite-web
|url=https://improveyouraccent.co.uk/tube/
|title=How to Pronounce London Underground Tube Stations
|author=Luke Nicholson
|work=Improve Your Accent
}}</ref>
** {{audio|en|LL-Q7979-Soundguys-Holborn.wav|a=UK}}
* {{IPA|en|/ˈhɒlbərn/}} <!--see Wikipedia-->
"""

    expected = """\
==English==

===Pronunciation===
* {{IPA|en|/ˈhəʊbən/<ref:{{cite-web
|url=https://improveyouraccent.co.uk/tube/
|title=How to Pronounce London Underground Tube Stations
|author=Luke Nicholson
|work=Improve Your Accent
}}>}}
** {{audio|en|LL-Q7979-Soundguys-Holborn.wav|a=UK}}
* {{IPA|en|/ˈhɒlbərn/}} <!--see Wikipedia-->\
"""

    summary = []
    res = fixer.process(text, "page", summary)
    assert res == expected



def test_misplaced_lines():

    text = """\
==English==

===Pronunciation===
* {{IPA|en|/ˈhəʊbən/}}
** {{audio|en|LL-Q7979-Soundguys-Holborn.wav|a=UK}}

{{wikipedia}}
[[File:Labe_udoli.jpg|right|thumb|View of the river]]

===Noun===
{{en-noun}}

# def
"""

    expected = """\
==English==

===Pronunciation===
* {{IPA|en|/ˈhəʊbən/}}
** {{audio|en|LL-Q7979-Soundguys-Holborn.wav|a=UK}}

===Noun===
{{wikipedia}}
[[File:Labe_udoli.jpg|right|thumb|View of the river]]
{{en-noun}}

# def\
"""

    summary = []
    res = fixer.process(text, "page", summary)
    assert res == expected


def test_missing_format():

    text = """\
==English==

===Pronunciation===
{{IPA|en|/ˈhəʊbən/}}
{{audio|en|LL-Q7979-Soundguys-Holborn.wav|a=UK}}
"""

    expected = """\
==English==

===Pronunciation===
* {{IPA|en|/ˈhəʊbən/}}
* {{audio|en|LL-Q7979-Soundguys-Holborn.wav|a=UK}}\
"""

    summary = []
    res = fixer.process(text, "page", summary)
    assert res == expected


def test_extract_refs():
    assert extract_refs("<ref>foo</ref>") == ("", ["foo"])
    assert extract_refs("bar <ref>foo</ref> baz") == ("bar  baz", ["foo"])
    assert extract_refs("<ref>foo</ref> <ref>bar</ref>") == (" ", ["foo", "bar"])
    assert extract_refs("<ref test='unhandled'>foo</ref>") == None
    assert extract_refs("<ref name='test'>foo</ref>") == ("", ["foo<<name:test>>"])
    assert extract_refs("""<ref group="ref'group'">foo</ref>""") == ("", ["foo<<group:ref'group'>>"])
    assert extract_refs("""<ref>foo</ref>   <ref name='name' group="group">bar</ref>""") == ("   ", ["foo", "bar<<name:name>><<group:group>>"])
    assert extract_refs("<ref name='test'></ref>") == ("", ["<<name:test>>"])
    assert extract_refs("<ref name='test' />") == ("", ["<<name:test>>"])


def test_parse_ipa_list():
    assert parse_ipa_list("{{IPA|en|foo}}") == [{1: 'en', 2: 'foo'}]
    assert parse_ipa_list("{{IPA|en|foo}}, {{IPA|en|bar}},  {{IPA|en|baz}}") == [{1: 'en', 2: 'foo'}, {1: 'en', 2: 'bar'}, {1: 'en', 2: 'baz'}]
    assert parse_ipa_list("{{IPA|en|foo}}; {{IPA|en|bar}}; {{IPA|en|baz}}") == [{1: 'en', 2: 'foo'}, {1: 'en', 2: 'bar'}, {1: 'en', 2: 'baz'}]
    assert parse_ipa_list("{{IPA|en|foo}} or {{IPA|en|bar}} or {{IPA|en|baz}}") == [{1: 'en', 2: 'foo'}, {1: 'en', 2: 'bar'}, {1: 'en', 2: 'baz'}]

    assert parse_ipa_list("{{IPA|en|/iː.deɪ ˈfiːks/|nocount=1}}, {{IPA|en|/i.deɪ fiks/}}") == [{1: 'en', 2: '/iː.deɪ ˈfiːks/', 'nocount': '1'}, {1: 'en', 2: '/i.deɪ fiks/'}] 
    assert parse_ipa_list("{{IPA|en|/iː.deɪ ˈfiːks/}} (''or as French'' {{IPA|en|/i.deɪ fiks/}})") == "unhandled_text"

    # Mixed spearators
    assert parse_ipa_list("{{IPA|en|foo}}, {{IPA|en|bar}};  {{IPA|en|baz}}") == "mismatched_delim"

    # NO IPA
    assert parse_ipa_list("{{IPA|en|foo}}, {{enPR|bar}},  {{IPA|en|baz}}") == "no_ipa"

    assert parse_ipa_list("{{IPA|en|foo}}, {{IPA|es|baz}}") == [{1: 'en', 2: 'foo'}, {1: 'es', 2: 'baz'}]

    # unhandled template
    assert parse_ipa_list("{{IPA|en|foo}}, {{IPA|bar}} {{unhandled|test}},  {{IPA|en|baz}}") == "unhandled_template"

    assert parse_ipa_list("{{q|test_qualifier}} {{IPA|en|foo}}") == [{1: 'en', 2: 'foo', 'q': 'test_qualifier'}]
    assert parse_ipa_list("{{q|unhandled}} {{IPA|en|foo}}") == "unhandled_qualifier"

#    assert parse_ipa_list("{{IPA|en|foo}} {{q|test}}") in ([{1: 'en', 2: 'foo', 'qq': 'test'}], "unhandled_qualifier")
#    assert parse_ipa_list("{{q|test}} {{IPA|en|foo}} {{q|test}}") in ([{1: 'en', 2: 'foo', 'q': 'test', 'qq': 'test'}], "unhandled_qualifier")
#    assert parse_ipa_list("{{q|test}} {{IPA|en|foo|qq=foo}}") in ([{1: 'en', 2: 'foo', 'qq': 'foo', 'q': 'test'}], "unhandled_qualifier")

    # multi q
    assert parse_ipa_list("{{IPA|en|foo}} {{q|test_qualifier}} {{q|test_qualifier}}") == "dup_qq"
    assert parse_ipa_list("{{IPA|en|foo}} {{q|test|foo}}") == "complex_qualifier"
    assert parse_ipa_list("{{q|test_qualifier}} {{IPA|en|foo|q=foo}}") == "q_collision"



def test_make_ipa_template():
    assert make_ipa_template([{1: 'en', 2: 'foo'}, {1: 'en', 2: 'bar'}, {1: 'en', 2: 'baz'}]) == "{{IPA|en|foo|bar|baz}}"
    assert make_ipa_template([{1: 'en', 2: 'foo', 'q': 'test'}, {1: 'en', 2: 'bar', 'q': 'test2'}, {1: 'en', 2: 'baz', 'q': 'test3'}]) == "{{IPA|en|foo<q:test>|bar<q:test2>|baz<q:test3>}}"
    assert make_ipa_template([{1: 'en', 2: 'foo', 'q': 'test'}, {1: 'en', 2: 'bar', 'a': 'test'}, {1: 'en', 2: 'baz', 'ref': 'test'}]) == None # "ambig_merged_param"
    assert make_ipa_template([{1: 'en', 2: 'foo', 'unhandled': 'test'}]) == None
    assert make_ipa_template([{1: 'en', 2: 'foo', 3: 'foobar', 'q2': 'test'}, {1: 'en', 2: 'bar'}, {1: 'en', 2: 'baz'}]) == None #'ambig_merged_param'

    # lang mismatch
    assert make_ipa_template([{1: 'en', 2: 'foo'}, {1: 'es', 2: 'bar'} ]) == None
