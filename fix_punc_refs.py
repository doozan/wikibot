import re

def make_pat(start, end):

    start = f"[" + start + "]\s*" if start else "\s*"
    end = f"\s*[" + end + "]" if end else "\s*"

    return fr"""(?x)
        {start}
        (
          [<]\s*ref
          (
            \b[^>]*[/]\s*>                 # match <ref name="test" />
            |
            [^<]*[<]\s*[/]\s*ref[^>]*>     # match <ref ...>test</ref>
          )
        )
        {end}
    """

def fix_punc_refs(text, title, summary, options):
    if re.search("ja-pron.*acc_ref=.*\<ref", text):
        return text

    patterns = [
        {
            "old": make_pat(',', ','),
            "new": r',\1',
            "msg": "Replaced ,<ref></ref>, with ,<ref></ref>"
        },
        {
            "old": make_pat('.', '.'),
            "new": r'.\1',
            "msg": "Replaced .<ref></ref>. with .<ref></ref>"
        },
        {
            "old": make_pat(',', '.'),
            "new": r'.\1',
            "msg": "Replaced ,<ref></ref>. with .<ref></ref>"
        },
        {
            "old": make_pat('.', ','),
            "new": r',\1',
            "msg": "Replaced .<ref></ref>, with ,<ref></ref>"
        },
        {
            "old": make_pat('', ','),
            "new": r',\1',
            "msg": "Replaced <ref></ref>, with ,<ref></ref>"
        },
        {
            "old": make_pat('', '.'),
            "new": r'.\1',
            "msg": "Replaced <ref></ref>. with .<ref></ref>"
        },
        {
            "old": make_pat('', ';'),
            "new": r';\1',
            "msg": "Replaced <ref></ref>; with ;<ref></ref>"
        },
    ]

    orig_text = None
    while orig_text != text:
        orig_text = text
        for p in patterns:
            new_text = re.sub(p["old"], p["new"], text)
            if new_text != text:
                summary.append(p["msg"])
                text = new_text
                break

    return new_text
