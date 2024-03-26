import os
import re
import sys

def iter_xml(filename, limit=None, show_progress=False, *extra, title_matches=None, text_matches=None):
    from pywikibot import xmlreader
    dump = xmlreader.XmlDump(filename)
    parser = dump.parse()

    count = 0
    for entry in parser:
        if not count % 1000 and show_progress:
            print(count, end = '\r', file=sys.stderr)

        if limit and count >= limit:
            break
        count += 1

        if title_matches and not title_matches(entry.title):
            continue

        if text_matches and not text_matches(entry.text):
            continue

        yield entry.text, entry.title, *extra


def iter_wxt(filename, limit=None, show_progress=False, *extra, title_matches=None, text_matches=None):

    if not os.path.isfile(filename):
        raise FileNotFoundError(f"Cannot open: {filename}")

    from enwiktionary_wordlist.wikiextract import WikiExtractWithRev
    parser = WikiExtractWithRev.iter_articles_from_bz2(filename)

    count = 0
    for entry in parser:

        if not count % 1000 and show_progress:
            print(count, end = '\r', file=sys.stderr)

        if limit and count >= limit:
            break
        count += 1

        yield entry.text, entry.title, *extra


NAMESPACE = {
    "Talk": ("talk",),
    "User": ("user",),
    "User talk": ("user talk",),
    "Wiktionary": ("wt", "wiktionary",),
    "Wiktionary talk": ("wiktionary talk",),
    "File": ("file", "image",),
    "File talk": ("file talk", "image talk",),
    "Mediawiki": ("mediawiki",),
    "Template": ("t", "template",),
    "Template talk": ("template talk",),
    "Help": ("help",),
    "Help talk": ("help talk",),
    "Category": ("cat", "c", "category",),
    "Category talk": ("category talk",),
    "Thread": ("thread",),
    "Thread talk": ("thread talk",),
    "Summary": ("summary",),
    "Summary talk": ("summary talk",),
    "Appendix": ("ap", "appendix",),
    "Appendix talk": ("appendix talk",),
    "Rhymes": ("rhymes",),
    "Rhymes talk": ("rhymes talk",),
    "Transwiki": ("transwiki",),
    "Transwiki talk": ("transwiki talk",),
    "Thesaurus": ("ws", "thesaurus", "wikisaurus",),
    "Thesaurus talk": ("thesaurus talk", "wikisaurus talk",),
    "Citations": ("citations",),
    "Citations talk": ("citations talk",),
    "Sign gloss": ("sign gloss",),
    "Sign gloss talk": ("sign gloss talk",),
    "Reconstruction": ("rc", "reconstruction",),
    "Reconstruction talk": ("reconstruction talk",),
    "Module": ("mod", "module",),
    "Module talk": ("module talk",),
}
ALIAS_TO_NAMESPACE = {alias:namespace for namespace, aliases in NAMESPACE.items() for alias in aliases}
_ns_pat = "^([:]?(" + "|".join(ALIAS_TO_NAMESPACE.keys()) + ")):"

def split_namespace(target):
    if ":" not in target:
        return None, target

    m = re.match(_ns_pat, target, re.IGNORECASE)
    if not m:
        return None, target

    alias = m.group(1)
    alias = alias.lstrip(":").lower()
    return ALIAS_TO_NAMESPACE[alias], target.removeprefix(m.group(0))
