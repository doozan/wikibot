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

        if title_matches and not title_matches(entry.title):
            continue

        if text_matches and not text_matches(entry.text):
            continue

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



def get_nest_depth(text, opener, closer, start_depth=0):
    """ Returns the level of depth inside ```start``` at the end of the line
    opener and closer are the nest opening and closing strings
    starting_depth, optional is the starting depth level

    zero }} zero {{ one {{ two {{ three }} two }} one }} zero }} zero
    """

    if start_depth < 0:
        raise ValueError("start_level cannot be negative")

    depth = start_depth

    first = True
    for t in text.split(opener):
        if first:
            first = False
            if not depth:
                continue
        else:
            depth += 1

        depth = max(0, depth - t.count(closer))

    return depth

def get_template_depth(text, start_depth=0):
    """
    Returns the depth of template templates at the end of the given line
    zero }} zero {{ one {{ two {{ three }} two }} one }} zero }} zero
    """

    return get_nest_depth(text, "{{", "}}", start_depth=start_depth)

def nest_aware_iterator(iterator, nests, delimiter=""):
    results = []
    items = []
    depth = {}

    for item in iterator:
        items.append(item)
        depth = { nest:get_nest_depth(item, nest[0], nest[1], depth.get(nest, 0)) for nest in nests }
        if any(depth.values()):
            continue

        yield delimiter.join(items)
        items = []

    if len(items):
        yield delimiter.join(items)

def nest_aware_resplit(pattern, text, nests, flags=re.DOTALL):

    if not pattern.startswith("("):
        pattern = "(" + pattern + ")"

    results = []
    items = []
    depth = {}

    it = iter(re.split(pattern, text, flags))
    for item in it:
        delimiter = next(it,"")
        items.append(item)
        depth = { nest:get_nest_depth(item, nest[0], nest[1], depth.get(nest, 0)) for nest in nests }
        if any(depth.values()):
            items.append(delimiter)
            continue

        yield ("".join(items), delimiter)
        items = []

    if len(items):
        yield (delimiter.join(items), "")

def nest_aware_splitlines(text, nests, keepends=False):
    return nest_aware_iterator(text.splitlines(keepends), nests)

def nest_aware_split(delimiter, text, nests):
    return nest_aware_iterator(text.split(delimiter), nests, delimiter)

def nest_aware_index(delimiter, text, nests):
    part = next(nest_aware_split(delimiter, text, nests), None)
    if len(part)==len(text):
        return -1

    return len(part)

def nest_aware_contains(delimiter, text, nests):
    return nest_aware_index(delimiter, text, nests) != -1

def template_aware_splitlines(text, keepends=False):
    return nest_aware_iterator(text.splitlines(keepends), [("{{","}}")])

def template_aware_split(delimiter, text):
    return nest_aware_iterator(text.split(delimiter), [("{{","}}")], delimiter)

def template_aware_resplit(pattern, text):
    return nest_aware_resplit(pattern, text, [("{{","}}")])


