from ..fix_list_to_col import ListToColFixer
fixer = ListToColFixer()

def test_line_to_template():

    tests = {
        ("* {{q|test}} {{l|cs|one}}, {{l|cs|two}}", "{{col|cs|title=test|one|two}}"),
#        ("* {{q|test}} {{l|cs|one}}; ,,;,  {{l|cs|two}}, ", "{{col|cs|title=test|one|two}}"),
        ("* {{q|test}} {{l|cs|one}}, {{l|cs|two}}, {{l|cs|one}}", "{{col|cs|title=test|one|two}}"),
        ("* {{q|test}} {{l|cs|one}}, {{l|cs|two}}, three", None),
        ("*: {{q|test}} {{l|cs|one}}, {{l|cs|two}}", None),
        ("# {{q|test}} {{l|cs|one}}, {{l|cs|two}}", None),
        ("* {{q|test}} {{l|cs|one}}, {{XX|cs|two}}", None),
        ("* {{l|cs|one}}, {{l|cs|two}}", "{{col|cs|one|two}}"),
        ("* {{q|test}}", None),
    }

    for text, expected in tests:
        print("")
        print(text)
        print(expected)
        res = fixer.line_to_template("cs", text, None, None)
        print(res)
        assert res == expected

def test_convert_titled_lists_to_templates():

    lines = [
        "* {{q|adjectives}} {{l|cs|a1}}, {{l|cs|a2, a2;2}}; {{l|cs|a3}}",
        "* {{q|nouns}} {{l|cs|n1}}, {{l|cs|n2}}, {{l|cs|n3}}",
    ]
    expected = [
        "{{col|cs|title=adjectives|a1|a2, a2;2|a3}}",
        "{{col|cs|title=nouns|n1|n2|n3}}",
    ]

    res = fixer.convert_titled_lists_to_templates("cs", lines, None, None)
    print(res)
    assert res == expected

    res = fixer.process_lines("cs", lines)
    print(res)
    assert res == expected


def test_convert_top_templates():

    lines = [
        "{{rel-top3|Related terms}}",
        "* {{l|cs|r1}}",
        "* {{l|cs|r2}}",
        "{{rel-bottom}}",
        "{{der-top}}",
        "* {{l|cs|d1}}",
        "* {{l|cs|d2}}",
        "{{der-bottom}}",
        "{{top}}",
        "* {{l|cs|t1}}",
        "* {{l|cs|t2}}",
        "{{bottom}}",
        ]
    expected = [
        "{{col|cs|r1|r2}}",
        "{{col|cs|d1|d2}}",
        "{{col|cs|t1|t2}}",
    ]

    res = fixer.convert_top_templates("cs", lines, None, None)
    print(res)
    assert res == expected

    res = fixer.process_lines("cs", lines)
    print(res)
    assert res == expected

def test_process_lines():

    lines = [
        "* {{l|cs|a1}}",
        "*{{l|cs|a2}}",
        "*   {{l|cs|a3}}",
        "* [[a4]]",
    ]
    expected = [
        "{{col|cs|a1|a2|a3|a4}}",
    ]

    assert fixer.process_lines("cs", lines) == expected

    lines = [
        "* {{l|cs|a1}}",
        "* [[a4|a4alt]]",  # Links with | should produce alt
    ]
    expected =  ["""\
{{col|cs
|a1
|a4<alt:a4alt>
}}"""]
    assert fixer.process_lines("cs", lines) == expected

    lines = [
        "* {{l|cs|a1}}",
        "* {{l|cs|a2|g=m}}",
        "* {{l|cs|a3}} {{g|f}}",
    ]
    expected = [
        """{{col|cs
|a1
|a2<g:m>
|a3<g:f>
}}""",
    ]
    assert fixer.process_lines("cs", lines) == expected

    lines = [
        "* {{l|cs|a1}}",
        "* {{l|cs|a2}} blah",
        "* {{l|cs|a3}}",
    ]
    expected = None
    assert fixer.process_lines("cs", lines) == expected

    lines = [
        "* {{l|cs|a1}}",
        "* {{x|cs|a2}}",
        "* {{l|cs|a3}}",
    ]
    expected = None
    assert fixer.process_lines("cs", lines) == expected

    lines = [
        ": {{l|cs|a1}}",
        ": {{l|cs|a2}}",
        ": {{l|cs|a3}}",
    ]
    expected = None
    assert fixer.process_lines("cs", lines) == expected

    lines = [
        "* {{l|cs|a1|param2}}",
        "* {{l|cs|a2}}",
        "* {{l|cs|a3}}",
    ]
    expected = [
        """{{col|cs
|a1<alt:param2>
|a2
|a3
}}"""
    ]
    assert fixer.process_lines("cs", lines) == expected


    # Convert existing templates
    lines = [
        "* See {{l|xx|blah}}",
        "{{col2|cs|c1|c2|c3}}",
        "{{der3|cs|d1|d2|d3}}",
        "{{rel4|cs|r1|r2|r3}}",
        "* See {{l|xx|blah}}",
    ]
    expected = [
        "* See {{l|xx|blah}}",
        "{{col|cs|c1|c2|c3}}",
        "{{col|cs|d1|d2|d3}}",
        "{{col|cs|r1|r2|r3}}",
        "* See {{l|xx|blah}}",
    ]
    assert fixer.process_lines("cs", lines) == expected


    lines = [
        "* See {{l|xx|blah}}",
    ]
    expected = [
        "* See {{l|xx|blah}}",
    ]
    assert fixer.process_lines("cs", lines) == expected


    # Convert existing templates
    lines = [
        "{{col2",
        "|cs|c1",
        "|c2",
        "|c3}}",
    ]
    expected = [
        "{{col|cs|c1|c2|c3}}",
    ]
    assert fixer.process_lines("cs", lines) == expected


    lines = [
        "* {{l|cs|a1}}",
        "* {{l|cs|a2}}",
        "* {{l|cs|a3}}",
    ]
    expected = [
        "{{col|cs|a1|a2|a3}}",
    ]

    res = fixer.process_lines("cs", lines)
    print(res)
    assert res == expected



    lines = [
        "* {{l|cs|a1}}, {{l|cs|a2}}, {{l|cs|a3}}",
    ]
    expected = [
        "{{col|cs|a1|a2|a3}}",
    ]

    res = fixer.process_lines("cs", lines)
    print(res)
    assert res == expected



    lines = [
        "* {{l|es|barbechar|pos=v}}",
        "* {{l|es|barbechera}} {{g|f}}",
        "* {{l|es|en barbecho}}",
    ]
    expected = [
        """\
{{col|cs
|barbechar<pos:v>
|barbechera<g:f>
|en barbecho
}}"""]

    res = fixer.process_lines("cs", lines)
    print(res)
    assert res == expected



    lines = [
        "{{col|es|{{l|es|Juanita}} {{q|diminutive}}}}"
    ]
    expected = [
        """\
{{col|cs
|Juanita<qq:diminutive>
}}"""]

    res = fixer.process_lines("cs", lines)
    print(res)
    assert res == expected


    lines = [
        "* {{l|en|*}}",
        "* {{l|en|V*}}",
        "* {{l|en|Cl}}",
        "* {{l|en|ClG}}",
    ]
    expected = [ "{{col|en|*|V*|Cl|ClG}}" ]
    res = fixer.process_lines("en", lines)
    print(res)
    assert res == expected


def test_strip_templates():
    assert fixer.strip_templates("abc {{foo|{{bar|{{baz|xxx}}|test}}|more}} def") == "abc  def"

def test_split_label():
    assert fixer.split_label("{{q|test}} foo bar", None, None) == ("test", " foo bar")


def test_brackets_to_links():
    assert fixer.brackets_to_links("xx", "[[test]]") == "{{l|xx|test}}"
    assert fixer.brackets_to_links("xx", "[[test]] [[bar]]") == "{{l|xx|test}} {{l|xx|bar}}"
    assert fixer.brackets_to_links("xx", "[[test [[foo]] [[bar]]]]") == "[[test {{l|xx|foo}} {{l|xx|bar}}]]"
    assert fixer.brackets_to_links("xx", "[[test]]ing") == "{{l|xx|test|alt=testing}}"
    assert fixer.brackets_to_links("xx", "[[test|testing]]abc") == "{{l|xx|test|alt=testingabc}}"
    assert fixer.brackets_to_links("xx", "[[w:test]]") == "[[w:test]]"


def test_get_item():
    tests = {
        "[[test]]": "test",
        "{{l|es|test}}": "test",
        "{{l|es|test}} {{q|foo}}": "test<qq:foo>",
        "{{q|foo}} {{l|es|test}}": "test<q:foo>",
        "{{q|foo}} {{l|es|test}} {{q|bar}}": "test<q:foo><qq:bar>",
        "{{q|foo}} {{l|es|test}} {{q|bar}} {{g|m}}": "test<q:foo><qq:bar><g:m>",

        "{{l|es|test|foo}}": "test<alt:foo>",
        "{{l|es|test|foo|bar}}": "test<alt:foo><t:bar>",
        "{{l|es|test||bar}}": "test<t:bar>",
    }

    for item, expected in tests.items():
        res = fixer.get_item("xx", item, None, None)
        print([item, expected, res])
        assert expected == res


    item = "[[test]] ([[alt1]], [[alt2]])"
    assert fixer.get_item("xx", item, None, None) == None
    assert fixer.get_item("xx", item, None, None, True) == item

