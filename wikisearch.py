"""
Finds sections of data on a wiktionary page, with basic awareness
of templates, html comments and <nowiki> tags
"""

import re

def wiki_search(text, start, end=None, end_required=False, ignore_comments=False, ignore_nowiki=False, ignore_templates=False):

    in_comment = None
    in_nowiki = None
    template_depth = []

    if not end:
        end_required = False

    separators = []
    if not ignore_comments:
        separators += ["<!--", "-->"]
    if not ignore_nowiki:
        separators += ["<nowiki>", "</nowiki>"]
    if not ignore_templates:
        separators += [r"(?<!\\)({{|}})"]

    if start in separators:
        raise ValueError(f"Invalid search value: {start}")
    if end and end in separators:
        raise ValueError(f"Invalid search value: {end}")

    pattern = f"((?P<start>{start})"
    if end:
        pattern += f"|(?P<end>{end})"

    pattern += "|(?P<sep>" + "|".join(separators) + "))"

    start_pos = None
    for m in re.finditer(pattern, text, re.MULTILINE):

        if m.group('start'):
            if in_comment or in_nowiki or template_depth:
                continue

            if start_pos and not end_required:
                yield m.string[start_pos.start():m.start()]
                start_pos = m

            if not start_pos:
                start_pos = m

        elif end and m.group('end'):
            if in_comment or in_nowiki or template_depth:
                continue
            if not start_pos:
                continue
            yield m.string[start_pos.start():m.end()]
            start_pos = None

        elif in_comment and m.group('sep') == "-->":
            in_comment = None

        elif in_nowiki and m.group('sep') == "</nowiki>":
            in_nowiki = None

        elif not ignore_templates and (template_depth and m.group('sep') == "}}"):
            template_depth.pop()

        elif not ignore_templates and m.group('sep') == "{{":
            template_depth.append(m)

        elif not ignore_comments and m.group('sep') == "<!--":
            in_comment = m

        elif not ignore_nowiki and m.group('sep') == "<nowiki>":
            in_nowiki = m

    if start_pos and not end_required:
        yield m.string[start_pos.start():]
