from ..fix_list_to_col import ListToColFixer
fixer = ListToColFixer()

def test_line_to_template():

    tests = {
        ("* {{q|test}} {{l|cs|one}}, {{l|cs|two}}", "{{col-auto|cs|title=test|one|two}}"),
        ("* {{q|test}} {{l|cs|one}}; ,,;,  {{l|cs|two}}, ", "{{col-auto|cs|title=test|one|two}}"),
        ("* {{q|test}} {{l|cs|one}}, {{l|cs|two}}, {{l|cs|one}}", "{{col-auto|cs|title=test|one|two}}"),
        ("* {{q|test}} {{l|cs|one}}, {{l|cs|two}}, three", None),
        ("*: {{q|test}} {{l|cs|one}}, {{l|cs|two}}", None),
        ("# {{q|test}} {{l|cs|one}}, {{l|cs|two}}", None),
        ("* {{q|test}} {{l|cs|one}}, {{XX|cs|two}}", None),
        ("* {{l|cs|one}}, {{l|cs|two}}", None),
        ("* {{q|test}}", None),
    }

    for text, expected in tests:
        print("")
        print(text)
        print(expected)
        res = fixer.line_to_template("cs", text)
        print(res)
        assert res == expected

def test_titled_lists_to_templates():

    lines = [
        "* {{q|adjectives}} {{l|cs|a1}}, {{l|cs|a2}}, {{l|cs|a3}}",
        "* {{q|nouns}} {{l|cs|n1}}, {{l|cs|n2}}, {{l|cs|n3}}",
    ]
    expected = [
        "{{col-auto|cs|title=adjectives|a1|a2|a3}}",
        "{{col-auto|cs|title=nouns|n1|n2|n3}}",
    ]

    res = fixer.titled_lists_to_templates("cs", lines)
    print(res)
    assert res == expected

    res = fixer.cleanup_lines("cs", lines)
    print(res)
    assert res == expected

def test_lines_to_template():

    lines = [
        "* {{l|cs|a1}}",
        "* {{l|cs|a2}}",
        "* {{l|cs|a3}}",
    ]
    expected = [
        "{{col-auto|cs|a1|a2|a3}}",
    ]

    res = fixer.lines_to_template("cs", lines)
    print(res)
    assert res == expected

    res = fixer.cleanup_lines("cs", lines)
    print(res)
    assert res == expected


def test_cleanup_lines():

    lines = [
        "* {{l|cs|a1}}",
        "* {{l|cs|a2}}",
        "* {{l|cs|a3}}",
    ]
    expected = [
        "{{col-auto|cs|a1|a2|a3}}",
    ]

    assert fixer.lines_to_template("cs", lines) == expected

    lines = [
        "* {{l|cs|a1}}",
        "* {{l|cs|a2}} blah",
        "* {{l|cs|a3}}",
    ]
    assert fixer.cleanup_lines("cs", lines) == None

    lines = [
        "* {{l|cs|a1}}",
        "* {{x|cs|a2}}",
        "* {{l|cs|a3}}",
    ]
    assert fixer.cleanup_lines("cs", lines) == None

    lines = [
        ": {{l|cs|a1}}",
        ": {{l|cs|a2}}",
        ": {{l|cs|a3}}",
    ]
    assert fixer.cleanup_lines("cs", lines) == None

    lines = [
        "* {{l|cs|a1|param2}}",
        "* {{l|cs|a2}}",
        "* {{l|cs|a3}}",
    ]
    assert fixer.cleanup_lines("cs", lines) == None


    # Convert existing templates
    lines = [
        "* See {{l|xx|blah}}",
        "{{col2|cs|c1|c2|c3}}",
        "{{der3|cs|d1|d2|d3}}",
        "{{rel4|cs|r1|r2|r3}}",
    ]
    expected = [
        "* See {{l|xx|blah}}",
        "{{col-auto|cs|c1|c2|c3}}",
        "{{col-auto|cs|d1|d2|d3}}",
        "{{col-auto|cs|r1|r2|r3}}",
    ]
    assert fixer.cleanup_lines("cs", lines) == expected


    # Convert existing templates
    lines = [
        "{{col2",
        "|cs|c1",
        "|c2",
        "|c3}}",
    ]
    expected = [
        "{{col-auto",
        "|cs|c1",
        "|c2",
        "|c3}}",
    ]
    assert fixer.cleanup_lines("cs", lines) == expected
