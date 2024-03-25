from autodooz.fix_rq_template import RqTemplateFixer, escape, unescape, escape_triple_braces, escape_pound_braces, escape_magic

fixer = RqTemplateFixer(None)


def test_escape():

#    assert fixer.replace_pound_brackets("test {{#if:{{{blah}}} == test }|} } {{2}}}}aa") == "test ⎨⎨#if:{{{blah}}} == test }|} } {{2}}⎬⎬aa"

#    assert fixer.replace_triple_brackets("test {{{a|}}} {{{b|}}} {{{c|{{{d|}}}}}}") == 'test ⎨⎨⎨a|⎬⎬⎬ ⎨⎨⎨b|⎬⎬⎬ ⎨⎨⎨c|⎨⎨⎨d|⎬⎬⎬⎬⎬⎬'


    text = " {{#ifeq:{{{version|}}}|Hg }} "
    expected = " ⎨⎨#ifeq:⎨⎨⎨version⌇⎬⎬⎬⌇Hg ⎬⎬ "
    res = escape(text)
    print(res)
    assert res == expected

    text = """
|section        = {{#ifeq:{{{version|}}}|Hg
    | {{#if:{{{folio|}}}{{{2|}}}
        | folio{{#if:{{{folioend|}}}|s}} {{{folio|{{{2|}}}}}}, {{#if:{{{verso|}}}|verso|recto}}
      }}
  }}
"""

    expected = """
|section        = ⎨⎨#ifeq:⎨⎨⎨version⌇⎬⎬⎬⌇Hg
    ⌇ ⎨⎨#if:⎨⎨⎨folio⌇⎬⎬⎬⎨⎨⎨2⌇⎬⎬⎬
        ⌇ folio⎨⎨#if:⎨⎨⎨folioend⌇⎬⎬⎬⌇s⎬⎬ ⎨⎨⎨folio⌇⎨⎨⎨2⌇⎬⎬⎬⎬⎬⎬, ⎨⎨#if:⎨⎨⎨verso⌇⎬⎬⎬⌇verso⌇recto⎬⎬
      ⎬⎬
  ⎬⎬
"""


    res = escape(text)
    print(res)
    assert res == expected

    text = """
|chapterurl     = {{#if:{{{page|}}}{{{pageref|}}}{{{2|}}}
    |<!--Do nothing-->
    | {{fullurl:s:en:White Fang/{{#switch:{{{part|1}}}
        | 1 = {{{chapter|{{{1|}}}}}}
        | 2 = {{#expr:{{{chapter|}}}+3}}
        | 3 = {{#expr:{{{chapter|{{{1|}}}}}}+8}}
        | 4 = {{#expr:{{{chapter|{{{1|}}}}}}+14}}
        | 5 = {{#expr:{{{chapter|{{{1|}}}}}}+20}}
     }}}}
 }}
"""
    expected = """
|chapterurl     = ⎨⎨#if:⎨⎨⎨page⌇⎬⎬⎬⎨⎨⎨pageref⌇⎬⎬⎬⎨⎨⎨2⌇⎬⎬⎬
    ⌇≺!--Do nothing--≻
    ⌇ ⎨⎨fullurl:s:en:White Fang⌿⎨⎨#switch:⎨⎨⎨part⌇1⎬⎬⎬
        ⌇ 1 ⎓ ⎨⎨⎨chapter⌇⎨⎨⎨1⌇⎬⎬⎬⎬⎬⎬
        ⌇ 2 ⎓ ⎨⎨#expr:⎨⎨⎨chapter⌇⎬⎬⎬+3⎬⎬
        ⌇ 3 ⎓ ⎨⎨#expr:⎨⎨⎨chapter⌇⎨⎨⎨1⌇⎬⎬⎬⎬⎬⎬+8⎬⎬
        ⌇ 4 ⎓ ⎨⎨#expr:⎨⎨⎨chapter⌇⎨⎨⎨1⌇⎬⎬⎬⎬⎬⎬+14⎬⎬
        ⌇ 5 ⎓ ⎨⎨#expr:⎨⎨⎨chapter⌇⎨⎨⎨1⌇⎬⎬⎬⎬⎬⎬+20⎬⎬
     ⎬⎬⎬⎬
 ⎬⎬
"""

    res = escape(text)
    print(res)
    assert res == expected

    text     = "{{#invoke:string|replace|{{{chapter|{{{3|{{#invoke:string|replace|{{{chapter|{{{3|}}}}}}|'|’}}}}}}}}|’’|''}}"
    expected = "⎨⎨#invoke:string⌇replace⌇⎨⎨⎨chapter⌇⎨⎨⎨3⌇⎨⎨#invoke:string⌇replace⌇⎨⎨⎨chapter⌇⎨⎨⎨3⌇⎬⎬⎬⎬⎬⎬⌇'⌇’⎬⎬⎬⎬⎬⎬⎬⎬⌇’’⌇''⎬⎬"
    res = escape(text)
    print(res)
    assert res == expected

def test_escape2():


    text     = "{{#ifexpr:{{#if:{{num|{{{letter|}}}{{{2|}}}}}|{{{letter|{{{2|}}}}}}|{{R2A|{{{letter|{{{2|}}}}}}}}}}<43|I|II}}"
    expected = "⎨⎨#ifexpr:⎨⎨#if:{{num|⎨⎨⎨letter⌇⎬⎬⎬⎨⎨⎨2⌇⎬⎬⎬}}⌇⎨⎨⎨letter⌇⎨⎨⎨2⌇⎬⎬⎬⎬⎬⎬⌇{{R2A|⎨⎨⎨letter⌇⎨⎨⎨2⌇⎬⎬⎬⎬⎬⎬}}⎬⎬≺43⌇I⌇II⎬⎬"
    res = escape(text)
    print(res)
    assert res == expected


    text     = "{{{a|{{foo|bar}}}}}"
    expected = "⎨⎨⎨a⌇{{foo|bar}}⎬⎬⎬"
    res = escape(text)
    print(res)
    assert res == expected



    text = """
{{{1|
  {{#if:|
    {{R2A|x}}}}
}}}
"""

    expected = """
⎨⎨⎨1⌇
  ⎨⎨#if:⌇
    {{R2A|x}}⎬⎬
⎬⎬⎬
"""
    res = escape(text)
    print(res)
    assert res == expected

    text = """
{{#switch:{{uc:{{{volume|}}}{{{1|
    {{#if:{{{letter|}}}{{{2|}}}
        | {{#ifexpr:{{#if:{{num|{{{letter|}}}{{{2|}}}}}|{{{letter|{{{2|}}}}}}|{{R2A|{{{letter|{{{2|}}}}}}}}}}<43|I|II}}
      }}
  }}}}}
    | I = 1aust/page/{{#ifexpr:{{num|{{{page|}}}{{{pageref|}}}{{{4|}}}}}
        | {{#ifeq:{{{page|}}}{{{pageref|}}}{{{4|}}}|1
            | n20
            | {{{page|{{{pageref|{{{4|}}}}}}}}}
          }}
        | n{{#expr:{{R2A|{{{page|{{{pageref|{{{4|}}}}}}}}}}}+3}}
      }}
    | 2aust/page/{{#ifeq:{{{page|}}}{{{pageref|}}}{{{4|}}}|1
        | n14
        | {{{page|{{{pageref|{{{4|}}}}}}}}}
      }}
  }}/mode/1up
"""

    expected = """
⎨⎨#switch:⎨⎨uc:⎨⎨⎨volume⌇⎬⎬⎬⎨⎨⎨1⌇
    ⎨⎨#if:⎨⎨⎨letter⌇⎬⎬⎬⎨⎨⎨2⌇⎬⎬⎬
        ⌇ ⎨⎨#ifexpr:⎨⎨#if:{{num|⎨⎨⎨letter⌇⎬⎬⎬⎨⎨⎨2⌇⎬⎬⎬}}⌇⎨⎨⎨letter⌇⎨⎨⎨2⌇⎬⎬⎬⎬⎬⎬⌇{{R2A|⎨⎨⎨letter⌇⎨⎨⎨2⌇⎬⎬⎬⎬⎬⎬}}⎬⎬≺43⌇I⌇II⎬⎬
      ⎬⎬
  ⎬⎬⎬⎬⎬
    ⌇ I ⎓ 1aust⌿page⌿⎨⎨#ifexpr:{{num|⎨⎨⎨page⌇⎬⎬⎬⎨⎨⎨pageref⌇⎬⎬⎬⎨⎨⎨4⌇⎬⎬⎬}}
        ⌇ ⎨⎨#ifeq:⎨⎨⎨page⌇⎬⎬⎬⎨⎨⎨pageref⌇⎬⎬⎬⎨⎨⎨4⌇⎬⎬⎬⌇1
            ⌇ n20
            ⌇ ⎨⎨⎨page⌇⎨⎨⎨pageref⌇⎨⎨⎨4⌇⎬⎬⎬⎬⎬⎬⎬⎬⎬
          ⎬⎬
        ⌇ n⎨⎨#expr:{{R2A|⎨⎨⎨page⌇⎨⎨⎨pageref⌇⎨⎨⎨4⌇⎬⎬⎬⎬⎬⎬⎬⎬⎬}}+3⎬⎬
      ⎬⎬
    ⌇ 2aust⌿page⌿⎨⎨#ifeq:⎨⎨⎨page⌇⎬⎬⎬⎨⎨⎨pageref⌇⎬⎬⎬⎨⎨⎨4⌇⎬⎬⎬⌇1
        ⌇ n14
        ⌇ ⎨⎨⎨page⌇⎨⎨⎨pageref⌇⎨⎨⎨4⌇⎬⎬⎬⎬⎬⎬⎬⎬⎬
      ⎬⎬
  ⎬⎬/mode/1up
"""
    res = escape(text)
    print(res)
    assert res == expected


    text     = """{{subst:ko new/pron/table|{{subst:ko new/pron/analysis|f|{{{7|}}}}}}}"""
    expected = """⎨⎨subst:ko new⌿pron⌿table⌇⎨⎨subst:ko new⌿pron⌿analysis⌇f⌇⎨⎨⎨7⌇⎬⎬⎬⎬⎬⎬⎬"""
    res = escape(text)
    print(res)
    assert res == expected

    text     = """{{subst:ko new/pron/table|{{subst:ko new/pron/analysis|f|{{{7|}}}}}"""
    expected = """{{subst:ko new/pron/table|⎨⎨subst:ko new⌿pron⌿analysis⌇f⌇⎨⎨⎨7⌇⎬⎬⎬⎬⎬"""
    res = escape(text)
    print(res)
    assert res == expected

    text     = """cat={{#if:1||{{template|foo}}}}"""
    expected = """cat=⎨⎨#if:1⌇⌇{{template|foo}}⎬⎬"""
    res = escape(text)
    print(res)
    assert res == expected

    text = """
{{myv-noun-table<!--
-->|x={{{x|}}}<!--
-->|type=back-vowel stem ({{m|myv|ума|tr=-}}) type<!--

-->|1a={{PAGENAME}}<!--
-->|2a={{#if:{{{sg|}}}||{{PAGENAME}}т}}<!--
-->|3a={{PAGENAME}}нь<!--
-->|5a={{PAGENAME}}нень<!--
-->|7a={{PAGENAME}}до<!--
-->|9a={{PAGENAME}}со<!--
-->|11a={{PAGENAME}}сто<!--
-->|13a={{PAGENAME}}с<!--
-->|15a={{PAGENAME}}ва<!--
-->|17a={{PAGENAME}}шка<!--
-->|19a={{PAGENAME}}кс<!--
-->|21a={{PAGENAME}}втомо<!--
-->|cat={{#if:{{{nocat|}}}||{{catlangname|myv|uma-type nominals}}}}<!--

-->}}<!--
"""
    expected = """cat=⎨⎨#if:1⌇⌇{{template|foo}}⎬⎬"""
    res = escape(text)
    print(res)
    assert res == expected




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


def test_fix_escape_triple_braces():

    text     = "{{{a|{{{b}}}}}}"
    expected = "⎨⎨⎨a⌇⎨⎨⎨b⎬⎬⎬⎬⎬⎬"
    res = escape(text)
    print(res)
    assert res == expected

    # unclosed }}}
    text     = "{{{a|{{{b}}}}}"
    expected = "{{{a|⎨⎨⎨b⎬⎬⎬}}"
    res = escape(text)
    print(res)
    assert res == expected

    assert escape_triple_braces("test {{{a|}}} {{{b|}}} {{{c|{{{d|}}}}}}") == 'test ⎨⎨⎨a⌇⎬⎬⎬ ⎨⎨⎨b⌇⎬⎬⎬ ⎨⎨⎨c⌇⎨⎨⎨d⌇⎬⎬⎬⎬⎬⎬'

    assert escape_triple_braces("{{#if:{{{document|}}}|&#32;{{{document}}.}}}") == "{{#if:⎨⎨⎨document⌇⎬⎬⎬|&#32;⎨⎨⎨document}}.⎬⎬⎬"

