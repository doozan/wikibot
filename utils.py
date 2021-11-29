import re
from enwiktionary_parser.languages.all_ids import languages as lang_ids

FULL_PAGE = '(?s)^.*$'

def regex_lang(lang_id):

    TARGET_LANG = lang_ids[lang_id]
    start = rf"(^|\n)==\s*{TARGET_LANG}\s*=="
    re_endings = [ r"\n==[^=]+==", r"\n----( *\n)?", "$" ]
    endings = "|".join(re_endings)
    pattern = fr"(?s)(?P<full>(?P<body>{start}.*?)(?P<end>{endings}))"

    return pattern

def split_body_and_tail(match):
    """ match is the result of the regex_lang pattern
    return body (without any trailing whitespace lines)
    and tail, consisteding of whitespace lines, categories, and the ---- separator
    """

    body = match.group('body')
    tail = match.group('end')

    templates = [ "c", "C", "cat", "top", "topic", "topics", "categorize", "catlangname", "catlangcode", "cln", "DEFAULTSORT" ]
    re_templates = r"\{\{\s*(" + "|".join(templates) + r")\s*[|}][^{}]*\}*"
    re_categories = r"\[\[\s*Category\s*:[^\]]*\]\]"

    pattern = fr"(?s)(.*?\n)((\s*({re_templates}|{re_categories})\s*)*)$"
    m = re.match(pattern, body)

    if not m:
        return body, tail

    return m.group(1), m.group(2) + tail
