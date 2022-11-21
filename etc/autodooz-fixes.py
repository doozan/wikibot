import re
import sys

wikifix = {}

"""
wikifix['fix_name'] = {
    'mode': 'text'|'regex'|'function'
    'context': 'line'|'section'|'full_section'|'page'
    'summary': SUMMARY_STRING
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
def get_fixer(cls, params):
    item = (cls, params)
    if item not in _fixers:
        _fixers[item] = cls(*params)
    return _fixers[item]

import autodooz.fix_section_headers
wikifix['cleanup_sections'] = {
    'mode': 'function',
    "pre-fixes": [(autodooz.fix_section_headers.default_cleanup, None)],
    "fixes": [(autodooz.fix_section_headers.cleanup_sections, None)],
}

from autodooz.fix_tlfi import fr_add_tlfi
wikifix['add_tlfi'] = {
    'mode': 'function',
    'summary': 'French: Added TLFi link (bot edit)',
    "pre-fixes": [(autodooz.fix_section_headers.default_cleanup, None)],
    "fixes": [(fr_add_tlfi, None)],
}

#import autodooz.list_bad_parents as badparents
#wikifix['abandon_children'] = {
#    'mode': 'function',
#    "pre-fixes": [(autodooz.fix_section_headers.default_cleanup, None)],
#    "fixes": [(badparents.process, None)]
#}

import autodooz.sort_sections
wikifix['sort_l2'] = {
    'mode': 'function',
    "pre-fixes": [
        (autodooz.fix_section_headers.default_cleanup, None),
        (autodooz.fix_section_headers.cleanup_sections, None)],
    "fixes": [(autodooz.sort_sections.sort_l2, None)]
}

wikifix['sort_l3'] = {
    'mode': 'function',
    "pre-fixes": [
        (autodooz.fix_section_headers.default_cleanup, None),
        (autodooz.fix_section_headers.cleanup_sections, None)],
    "fixes": [(autodooz.sort_sections.sort_l3, None)]
}

from autodooz.t9n_fixer import T9nFixRunner
def wikifix_t9n(text, title, summary, options):
    fixer = get_fixer(T9nFixRunner, tuple(options[k] for k in ["allforms"]))
    return fixer.cleanup_tables(text, title, summary)

wikifix['fix_t9n'] = {
    'mode': 'function',
    "pre-fixes": [(autodooz.fix_section_headers.default_cleanup, None)],
    "fixes": [(wikifix_t9n, {"allforms": f"{SPANISH_DATA}/es_allforms.csv"})]
}

from autodooz.drae_fixer import DraeFixer
def es_drae_wrong(text, title, summary, options):
    fixer = get_fixer(DraeFixer, tuple(options[k] for k in ["drae_links"]))
    return fixer.fix_wrong_drae(text, title, summary)

wikifix['es_drae_wrong'] = {
    'mode': 'function',
    "pre-fixes": [(autodooz.fix_section_headers.default_cleanup, None)],
    "fixes": [(es_drae_wrong, { "drae_links": f"{DRAE_DATA}/drae.links" })]
}

def es_drae_missing(text, title, summary, options):
    fixer = get_fixer(DraeFixer, tuple(options[k] for k in ["drae_links"]))
    return fixer.fix_missing_drae(text, title, summary)

wikifix['es_drae_missing'] = {
    'mode': 'function',
    "pre-fixes": [(autodooz.fix_section_headers.default_cleanup, None)],
    "fixes": [(es_drae_missing, { "drae_links": f"{DRAE_DATA}/drae.links" })]
}

from autodooz.form_fixer import FixRunner
def es_add_forms(text, title, summary, options):
    fixer = get_fixer(FixRunner, tuple(options[k] for k in ["lang", "wordlist", "allforms"]))
    return fixer.add_forms(text, title, summary)

wikifix['es_add_forms'] = {
    'mode': 'function',
    "pre-fixes": [(autodooz.fix_section_headers.default_cleanup, None)],
    "fixes": [(es_add_forms, {
        "lang": "es",
        "allforms": f"{SPANISH_DATA}/es_allforms.csv",
        "wordlist": f"{SPANISH_DATA}/es-en.data",
        })]
}

def es_replace_forms(text, title, summary, options):
    fixer = get_fixer(FixRunner, tuple(options[k] for k in ["lang", "wordlist", "allforms"]))
    return fixer.replace_pos(text, title, summary, options["pos"])

wikifix['es_replace_pos'] = {
    'mode': 'function',
    "pre-fixes": [(autodooz.fix_section_headers.default_cleanup, None)],
    "fixes": [(es_replace_forms, {
        "lang": "es",
        "allforms": f"{SPANISH_DATA}/es_allforms.csv",
        "wordlist": f"{SPANISH_DATA}/es-en.data",
        "pos": ["v", "n", "adj"],
        })]
}




def es_add_forms(text, title, summary, options):
    fixer = get_fixer(FixRunner, tuple(options[k] for k in ["lang", "wordlist", "allforms"]))
    return fixer.add_pos(text, title, summary, options["pos"])

wikifix['es_replace_pos'] = {
    'mode': 'function',
    "pre-fixes": [(autodooz.fix_section_headers.default_cleanup, None)],
    "fixes": [(es_add_forms, {
        "lang": "es",
        "allforms": f"{SPANISH_DATA}/es_allforms.csv",
        "wordlist": f"{SPANISH_DATA}/es-en.data",
        "pos": ["v", "n", "adj"],
        })],
    "post-fixes": [(autodooz.sort_sections.sort_l3, None)]
}
