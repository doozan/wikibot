import re
import sys

wikifix = {}

"""
wikifix['fix_name'] = {
    'mode': 'text'|'regex'|'function'
    'context': 'line'|'section'|'full_section'|'page'
    'fixes': [ (PATTERN, REPLACEMENT)|(TEXT, REPLACEMENT)|(FUNCTION, ARGS) ]
}

MODE can be 'text', 'regex', 'section', 'line', 'function'

  'text' - simple text search/replace
  'regex' - regex pattern search/replace
  'function' - replace the entire page with the result of a function

CONTEXT is used to specify exactly how the text or regex pattern
should match. If ommitted or empty, text will match anywhere on the page.
Not used when MODE is 'function'
Possible values are:

  'line' - must match an entire line
  'section' - must match an entire section (ignoring child section)
  'full_section' - must match an entire section (including child sections)
  'L2' - must match an entire L2 section
  'page' - must match the entire page

FIXES must be an array of 2-tuples
each fix will be applied in order to the page

if MODE is 'regex', then the tuple must be:
(PATTERN, REPLACEMENT)

if MODE is 'text', then the tuple must be:
(SEARCH, REPLACEMENT)

if MODE is 'function', then the tuple must be:
(fix_function, CUSTOM_PARAMS)
where fix_funciton is a function that will be called as
fix(page_text, page_title, summary, CUSTOM_PARAMS)
  where 'summary' is an empty array that, if populated,
  will be used in place of any other specified summary

"""

SPANISH_DATA = "../spanish_data"
DRAE_DATA = "../drae_data"

_fixers = {}
def get_fixer(cls, **kwparams):
    item = (cls, *kwparams)
    if item not in _fixers:
        _fixers[item] = cls(**kwparams)
    return _fixers[item]


import autodooz.sectionparser

from autodooz.fix_section_headers import SectionHeaderFixer
from autodooz.fix_section_levels import SectionLevelFixer
from autodooz.fix_section_order import SectionOrderFixer

def repeat_until_stable(function, text, title, summary, options):
    old_text = None
    loop = 0
    while text != old_text:
        old_text = text
        old_summary_len = len(summary)
        text = function(text, title, summary, options)
        loop += 1
        if loop > 4:
            print(summary)
            raise ValueError("loop", title)

    if old_summary_len != len(summary):
        raise ValueError("summary change but no text change", summary)
    return text

def ele_cleanup(text, title, summary, options):
    header_fixer = get_fixer(SectionHeaderFixer)
    level_fixer = get_fixer(SectionLevelFixer)
    order_fixer = get_fixer(SectionOrderFixer)

    def _ele_fixes(text, title, summary, options):
        text = header_fixer.process(text, title, summary, options)
        text = repeat_until_stable(level_fixer.process, text, title, summary, options)
        text = order_fixer.process(text, title, summary, options)
        return text

    text = repeat_until_stable(_ele_fixes, text, title, summary, options)
    return text

wikifix['ele_cleanup'] = {
    'mode': 'function',
    "pre-fixes": [(autodooz.sectionparser.cleanup_summary, None)],
    "fixes": [(ele_cleanup, None)],
}

wikifix['cleanup_sections'] = {
    'mode': 'function',
    "fixes": [(autodooz.sectionparser.cleanup_summary, None)],
    "post-fixes": [(ele_cleanup, None)],
}

def misnamed_further_reading(text, title, summary, options):
    header_fixer = get_fixer(SectionHeaderFixer)
    return header_fixer.process(text, title, summary, {"fix_misnamed_further_reading": True})

wikifix['misnamed_further_reading'] = {
    'mode': 'function',
    "pre-fixes": [(autodooz.sectionparser.cleanup_summary, None)],
    "fixes": [(misnamed_further_reading, None)],
    "post-fixes": [(ele_cleanup, None)],
}


from autodooz.fix_fr_tlfi import fr_add_tlfi
wikifix['add_tlfi'] = {
    'mode': 'function',
    "pre-fixes": [(autodooz.sectionparser.cleanup_summary, None)],
    "fixes": [(fr_add_tlfi, None)],
    "post-fixes": [(ele_cleanup, None)],
}

#import autodooz.list_bad_parents as badparents
#wikifix['abandon_children'] = {
#    'mode': 'function',
#    "pre-fixes": [(autodooz.sectionparser.cleanup_summary, None)],
#    "fixes": [(badparents.process, None)]
#}


from autodooz.fix_t9n import T9nFixRunner
def wikifix_t9n(text, title, summary, options):
    fixer = get_fixer(T9nFixRunner, **options)
    return fixer.cleanup_tables(text, title, summary)

wikifix['fix_t9n'] = {
    'mode': 'function',
    "pre-fixes": [(autodooz.sectionparser.cleanup_summary, None)],
    "fixes": [(wikifix_t9n, {"allforms": f"{SPANISH_DATA}/es_allforms.csv"})],
    "post-fixes": [(ele_cleanup, None)],
}

from autodooz.fix_es_drae import DraeFixer
def es_drae_wrong(text, title, summary, options):
    fixer = get_fixer(DraeFixer, **options)
    return fixer.fix_wrong_drae(text, title, summary)

wikifix['es_drae_wrong'] = {
    'mode': 'function',
    "pre-fixes": [(autodooz.sectionparser.cleanup_summary, None)],
    "fixes": [(es_drae_wrong, { "link_filename": f"{DRAE_DATA}/drae.links" })],
    "post-fixes": [(ele_cleanup, None)],
}

def es_drae_missing(text, title, summary, options):
    fixer = get_fixer(DraeFixer, **options)
    return fixer.fix_missing_drae(text, title, summary)

wikifix['es_drae_missing'] = {
    'mode': 'function',
    "pre-fixes": [(autodooz.sectionparser.cleanup_summary, None)],
    "fixes": [(es_drae_missing, { "link_filename": f"{DRAE_DATA}/drae.links" })],
    "post-fixes": [(ele_cleanup, None)],
}

from autodooz.fix_es_forms import FixRunner
def es_add_forms(text, title, summary, options):
    fixer = get_fixer(FixRunner, **options)
    return fixer.add_forms(text, title, summary)

wikifix['es_add_forms'] = {
    'mode': 'function',
    "pre-fixes": [(autodooz.sectionparser.cleanup_summary, None)],
    "fixes": [(es_add_forms, {
        "lang": "es",
        "allforms": f"{SPANISH_DATA}/es_allforms.csv",
        "wordlist": f"{SPANISH_DATA}/es-en.data",
        })],
    "post-fixes": [(ele_cleanup, None)],
}

def es_replace_forms(text, title, summary, options):
    fixer = get_fixer(FixRunner, **options)
    return fixer.replace_pos(text, title, options["pos"], summary)

wikifix['es_replace_pos'] = {
    'mode': 'function',
    "pre-fixes": [(autodooz.sectionparser.cleanup_summary, None)],
    "fixes": [(es_replace_forms, {
        "lang": "es",
        "allforms": f"{SPANISH_DATA}/es_allforms.csv",
        "wordlist": f"{SPANISH_DATA}/es-en.data",
        "pos": ["v", "n", "adj", "part"],
        })],
    "post-fixes": [(ele_cleanup, None)],
}


from autodooz.merge import MergeRunner
import autodooz.fix_pt_verbs

def pt_merge_verbs(text, title, summary, options):
    fixer = get_fixer(MergeRunner, **options)
    return fixer.merge_pages(text, title, summary, options)

wikifix['pt_merge_verbs'] = {
    'mode': 'function',
    "pre-fixes": [(autodooz.sectionparser.cleanup_summary, None)],
    "fixes": [(pt_merge_verbs, {
        "pages": "split_verbs",
        })],
    "post-fixes": [(ele_cleanup, None)],
}
