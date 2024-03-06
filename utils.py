import os
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
