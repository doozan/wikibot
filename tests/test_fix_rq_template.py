from autodooz.fix_rq_template import RqTemplateFixer

fixer = RqTemplateFixer(None)


def test_escape():

#    assert fixer.replace_pound_brackets("test {{#if:{{{blah}}} == test }|} } {{2}}}}aa") == "test ⎨⎨#if:{{{blah}}} == test }|} } {{2}}⎬⎬aa"

#    assert fixer.replace_triple_brackets("test {{{a|}}} {{{b|}}} {{{c|{{{d|}}}}}}") == 'test ⎨⎨⎨a|⎬⎬⎬ ⎨⎨⎨b|⎬⎬⎬ ⎨⎨⎨c|⎨⎨⎨d|⎬⎬⎬⎬⎬⎬'


    text = " {{#ifeq:{{{version|}}}|Hg }} "
    expected = " ⎨⎨#ifeq:⎨⎨⎨version⌇⎬⎬⎬⌇Hg ⎬⎬ "
    res = fixer.escape(text)
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


    res = fixer.escape(text)
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
    ⌇ {{fullurl:s:en:White Fang⌿⎨⎨#switch:⎨⎨⎨part⌇1⎬⎬⎬
        ⌇ 1 = ⎨⎨⎨chapter⌇⎨⎨⎨1⌇⎬⎬⎬⎬⎬⎬
        ⌇ 2 = ⎨⎨#expr:⎨⎨⎨chapter⌇⎬⎬⎬+3⎬⎬
        ⌇ 3 = ⎨⎨#expr:⎨⎨⎨chapter⌇⎨⎨⎨1⌇⎬⎬⎬⎬⎬⎬+8⎬⎬
        ⌇ 4 = ⎨⎨#expr:⎨⎨⎨chapter⌇⎨⎨⎨1⌇⎬⎬⎬⎬⎬⎬+14⎬⎬
        ⌇ 5 = ⎨⎨#expr:⎨⎨⎨chapter⌇⎨⎨⎨1⌇⎬⎬⎬⎬⎬⎬+20⎬⎬
     ⎬⎬}}
 ⎬⎬
"""

    res = fixer.escape(text)
    print(res)
    assert res == expected

    text     = "{{#invoke:string|replace|{{{chapter|{{{3|{{#invoke:string|replace|{{{chapter|{{{3|}}}}}}|'|’}}}}}}}}|’’|''}}"
    expected = "⎨⎨#invoke:string⌇replace⌇⎨⎨⎨chapter⌇⎨⎨⎨3⌇⎨⎨#invoke:string⌇replace⌇⎨⎨⎨chapter⌇⎨⎨⎨3⌇⎬⎬⎬⎬⎬⎬⌇'⌇’⎬⎬⎬⎬⎬⎬⎬⎬⌇’’⌇''⎬⎬"
    res = fixer.escape(text)
    print(res)
    assert res == expected

def test_jane():

#    text     = "{{#ifexpr:{{#if:{{num|{{{letter|}}}{{{2|}}}}}|{{{letter|{{{2|}}}}}}|{{R2A|{{{letter|{{{2|}}}}}}}}}}<43|I|II}}"
#    expected = "⎨⎨#ifexpr:⎨⎨#if:{{num⌇⎨⎨⎨letter⌇⎬⎬⎬⎨⎨⎨2⌇⎬⎬⎬}}⌇⎨⎨⎨letter⌇⎨⎨⎨2⌇⎬⎬⎬⎬⎬⎬⌇{{R2A⌇⎨⎨⎨letter⌇⎨⎨⎨2⌇⎬⎬⎬⎬⎬⎬}}⎬⎬≺43⌇I⌇II⎬⎬"
#    res = fixer.escape(text)
#    print(res)
#    assert res == expected


    text = """
{{{1|
  {{#if:|
    {{R2A|}}}}
}}}
"""

    expected = """
⎨⎨⎨1⌇
  ⎨⎨#if:⌇
    {{R2A⌇}}⎬⎬
⎬⎬⎬
"""
    res = fixer.escape(text)
    print(res)
    assert res == expected

    text = """
|pageurl        = https://archive.org/details/lettersofjaneaus0{{#switch:{{uc:{{{volume|}}}{{{1|
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
|pageurl        = https://archive.org/details/lettersofjaneaus0⎨⎨#switch:⎨⎨uc:⎨⎨⎨volume⌇⎬⎬⎬⎨⎨⎨1⌇
    ⎨⎨#if:⎨⎨⎨letter⌇⎬⎬⎬⎨⎨⎨2⌇⎬⎬⎬
        ⌇ ⎨⎨#ifexpr:⎨⎨#if:{{num⌇⎨⎨⎨letter⌇⎬⎬⎬⎨⎨⎨2⌇⎬⎬⎬}}⌇⎨⎨⎨letter⌇⎨⎨⎨2⌇⎬⎬⎬⎬⎬⎬⌇{{R2A⌇⎨⎨⎨letter⌇⎨⎨⎨2⌇⎬⎬⎬⎬⎬⎬}}⎬⎬≺43⌇I⌇II⎬⎬
      ⎬⎬
  ⎬⎬⎬⎬⎬
    ⌇ I = 1aust⌿page⌿⎨⎨#ifexpr:{{num⌇⎨⎨⎨page⌇⎬⎬⎬⎨⎨⎨pageref⌇⎬⎬⎬⎨⎨⎨4⌇⎬⎬⎬}}
        ⌇ ⎨⎨#ifeq:⎨⎨⎨page⌇⎬⎬⎬⎨⎨⎨pageref⌇⎬⎬⎬⎨⎨⎨4⌇⎬⎬⎬⌇1
            ⌇ n20
            ⌇ ⎨⎨⎨page⌇⎨⎨⎨pageref⌇⎨⎨⎨4⌇⎬⎬⎬⎬⎬⎬⎬⎬⎬
          ⎬⎬
        ⌇ n⎨⎨#expr:{{R2A⌇⎨⎨⎨page⌇⎨⎨⎨pageref⌇⎨⎨⎨4⌇⎬⎬⎬⎬⎬⎬⎬⎬⎬}}+3⎬⎬
      ⎬⎬
    ⌇ 2aust⌿page⌿⎨⎨#ifeq:⎨⎨⎨page⌇⎬⎬⎬⎨⎨⎨pageref⌇⎬⎬⎬⎨⎨⎨4⌇⎬⎬⎬⌇1
        ⌇ n14
        ⌇ ⎨⎨⎨page⌇⎨⎨⎨pageref⌇⎨⎨⎨4⌇⎬⎬⎬⎬⎬⎬⎬⎬⎬
      ⎬⎬
  ⎬⎬/mode/1up
"""
    res = fixer.escape(text)
    print(res)
    assert res == expected



def test_get_synonyms():

    text = " {{{4|{{{ passage | {{{text}}}}}}}}} "
    text= fixer.escape(text)
    assert fixer.get_synonyms(text) == ["4", "passage", "text"]

    text = " {{{4|{{{ passage | {{{text|}}}}}}}}} "
    text= fixer.escape(text)
    assert fixer.get_synonyms(text) == ["4", "passage", "text"]

    text = "{{{4|}}}"
    text= fixer.escape(text)
    assert fixer.get_synonyms(text) == ["4"]

    text = "{{{4}}}"
    text= fixer.escape(text)
    assert fixer.get_synonyms(text) == ["4"]

    text = "{{{4}}} {{{5}}}"
    text= fixer.escape(text)
    assert fixer.get_synonyms(text) == None

    text = "test"
    text= fixer.escape(text)
    assert fixer.get_synonyms(text) == None

    text = ""
    text= fixer.escape(text)
    assert fixer.get_synonyms(text) == []
