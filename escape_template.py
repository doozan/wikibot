import re

_tr_orig = "[]|<>/="
_tr_alt = "⎣⎦⌇≺≻⌿⎓"

_tr_orig_with_braces = "{}" + _tr_orig
_tr_alt_with_braces = "⎨⎬" + _tr_alt

_tr = str.maketrans(_tr_orig, _tr_alt)
_tr_with_braces = str.maketrans(_tr_orig_with_braces, _tr_alt_with_braces)

_tr_unescape = str.maketrans(_tr_alt_with_braces, _tr_orig_with_braces)

def escape(text, escape_comments=True, escape_nowiki=True):
    """
    Escapes items that can't be properly parsed by mwparserfromhell on template pages:
        variables:  {{{foo|{{{bar}}}}}}
        logic: {{#if|statements}}
        magic commands: {{uc:test|blah}}
    """

    matches = [(m.start(), m.end()) for m in re.finditer(r"<\s*noinclude\s*>.*?<\s*/\s*noinclude\s*>", text, re.DOTALL)]
    if escape_comments:
        matches += [(m.start(), m.end()) for m in re.finditer(r"<!--.*?-->", text, re.DOTALL)]
    if escape_nowiki:
        matches = [(m.start(), m.end()) for m in re.finditer(r"<\s*nowiki\s*>.*?<\s*/\s*nowiki\s*>", text, re.DOTALL)]
    text = escape_sections(text, matches)

    # it's important to escape triple before pound so that "}}}}}}" counts as two triple closes and not three double closes
    text = escape_triple_braces(text)
    text = escape_pound_braces(text)
    text = escape_magic(text)

    pattern = r"<(\s*[/]?\s*(nowiki|noinclude|includeonly)\s*[/]?\s*)>"
    matches = [(m.start(), m.end()) for m in re.finditer(pattern, text, re.DOTALL)]
    text = escape_sections(text, matches)

    return text

def unescape(text):
    return text.translate(_tr_unescape)

def _get_escapable(text, triple_close=False):

    # bracketed text inside of a pound brace should not be escaped
    # {{#if:{{{A}}}|do this|do {{THAT|OTHER|THING}} }}
    escapable = []
    escape_start = 0
    depth = 1

    for m in re.finditer(r"(\{\{|\}\})", text):
        if m.group(0) == "{{":
            if depth == 1:
                escapable.append((escape_start, m.start()))
            depth += 1
        if m.group(0) == "}}":
            depth -= 1
            if depth == 1:
                escape_start = m.end()
            if depth <= 0:
                if triple_close:
                    if m.end() < len(text) and text[m.end()] == "}":
                        escapable.append((escape_start, m.end()+1))
                        break
                    else:
                        depth = 1
                        continue

                escapable.append((escape_start, m.end()))
                break

    # unclosed template, don't escape
    if depth:
        escapable = []

    return escapable

def escape_magic(text):
    #escapes {{magic:foo|bar}}
    # use negative lookahead to get rightmost match
    m = re.search(r"\{\{[a-z]+:(?!.*\{\{[a-z]+:)", text)

    prev_offset = -1
    offset = 0
    while m and prev_offset != offset:
        prev_offset = offset
        offset = m.end()

        escapable = [(start+offset, end+offset) for start, end in _get_escapable(text[offset:])]
        if escapable:
            text = escape_sections(text, escapable, escape_braces=False)
            start = m.start()
            end = escapable[-1][1]
            text = text[:start] + "⎨⎨" + text[start+2:end-2] + "⎬⎬" + text[end:]

        # use negative lookahead to get rightmost match
        m = re.search(r"\{\{[a-z]+:(?!.*\{\{[a-z]+:)", text)

    return text

def escape_pound_braces(text):
    prev_offset = -1
    offset = 0
    while "{{#" in text and offset != prev_offset:
        prev_offset = offset
        offset = text.rindex("{{#") + 3

        escapable = [(start+offset, end+offset) for start, end in _get_escapable(text[offset:])]
        if escapable:
            text = escape_sections(text, escapable, escape_braces=False)
            start = offset-3
            end = escapable[-1][1]
            text = text[:start] + "⎨⎨" + text[start+2:end-2] + "⎬⎬" + text[end:]

    return text



def escape_triple_braces(text):

    prev_offset = -1
    offset = 0
    while "{{{" in text and offset != prev_offset:
        prev_offset = offset
        offset = text.rindex("{{{") + 3

        escapable = [(start+offset, end+offset) for start, end in _get_escapable(text[offset:], triple_close=True)]

        if escapable:
            text = escape_sections(text, escapable, escape_braces=False)
            start = offset-3
            end = escapable[-1][1]
            text = text[:start] + "⎨⎨⎨" + text[start+3:end-3] + "⎬⎬⎬" + text[end:]

    return text


def escape_sections(text, sections, escape_braces=True):

    # TODO: Option to escape_pipes_inside_braces, should be False for escape_triple and friends

    tr = _tr_with_braces if escape_braces else _tr
    for start, end in sections:
        #print("escaping", escape_braces, [text[start:end]])
        text = text[:start] + text[start:end].translate(tr) + text[end:]
        #print("escaped ", escape_braces, [text[start:end]])
    return text

