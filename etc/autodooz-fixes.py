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


import enwiktionary_sectionparser as sectionparser

from autodooz.fix_section_headers import SectionHeaderFixer
from autodooz.fix_section_levels import SectionLevelFixer
from autodooz.fix_section_order import SectionOrderFixer

def sectionparser_cleanup(text, title, summary, options):
    entry = sectionparser.parse(text, title)
    if not entry:
        return text

    changes = entry.changelog
    if not changes:
        return text

    summary.append(entry.changelog)
    return str(entry)

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
    "pre-fixes": [(sectionparser_cleanup, None)],
    "fixes": [(ele_cleanup, None)],
}

wikifix['cleanup_sections'] = {
    'mode': 'function',
    "fixes": [(sectionparser_cleanup, None)],
    "post-fixes": [(ele_cleanup, None)],
}

def misnamed_further_reading(text, title, summary, options):
    header_fixer = get_fixer(SectionHeaderFixer)
    return header_fixer.process(text, title, summary, {"fix_misnamed_further_reading": True})

wikifix['misnamed_further_reading'] = {
    'mode': 'function',
    "pre-fixes": [(sectionparser_cleanup, None)],
    "fixes": [(misnamed_further_reading, None)],
    "post-fixes": [(ele_cleanup, None)],
}


def misnamed_ety(text, title, summary, options):
    header_fixer = get_fixer(SectionHeaderFixer)
    return header_fixer.process(text, title, summary, {"fix_misnamed_etymology": True})

wikifix['misnamed_ety'] = {
    'mode': 'function',
    "pre-fixes": [(sectionparser_cleanup, None)],
    "fixes": [(misnamed_ety, None)],
    "post-fixes": [(ele_cleanup, None)],
}


def misnamed_pronunciation(text, title, summary, options):
    header_fixer = get_fixer(SectionHeaderFixer)
    return header_fixer.process(text, title, summary, {"fix_misnamed_pronunciation": True})

wikifix['misnamed_pronunciation'] = {
    'mode': 'function',
    "pre-fixes": [(sectionparser_cleanup, None)],
    "fixes": [(misnamed_pronunciation, None)],
    "post-fixes": [(ele_cleanup, None)],
}

def empty_sections(text, title, summary, options):
    header_fixer = get_fixer(SectionHeaderFixer)
    return header_fixer.process(text, title, summary, {"remove_empty": True})

wikifix['empty_sections'] = {
    'mode': 'function',
    "pre-fixes": [(sectionparser_cleanup, None)],
    "fixes": [(empty_sections, None)],
    "post-fixes": [(ele_cleanup, None)],
}


from autodooz.fix_fr_tlfi import fr_add_tlfi
wikifix['add_tlfi'] = {
    'mode': 'function',
    "pre-fixes": [(sectionparser_cleanup, None)],
    "fixes": [(fr_add_tlfi, None)],
    "post-fixes": [(ele_cleanup, None)],
}

#import autodooz.list_bad_parents as badparents
#wikifix['abandon_children'] = {
#    'mode': 'function',
#    "pre-fixes": [(sectionparser_cleanup, None)],
#    "fixes": [(badparents.process, None)]
#}


from autodooz.fix_t9n import T9nFixRunner
def wikifix_t9n(text, title, summary, options):
    fixer = get_fixer(T9nFixRunner, **options)
    return fixer.cleanup_tables(text, title, summary)

wikifix['fix_t9n'] = {
    'mode': 'function',
    "pre-fixes": [(sectionparser_cleanup, None)],
    "fixes": [(wikifix_t9n, {"allforms": f"{SPANISH_DATA}/es_allforms.csv"})],
    "post-fixes": [(ele_cleanup, None)],
}

from autodooz.fix_es_drae import DraeFixer
def es_drae_wrong(text, title, summary, options):
    fixer = get_fixer(DraeFixer, **options)
    return fixer.fix_wrong_drae(text, title, summary)

wikifix['es_drae_wrong'] = {
    'mode': 'function',
    "pre-fixes": [(sectionparser_cleanup, None)],
    "fixes": [(es_drae_wrong, { "link_filename": f"{DRAE_DATA}/drae.links" })],
    "post-fixes": [(ele_cleanup, None)],
}

def es_drae_missing(text, title, summary, options):
    fixer = get_fixer(DraeFixer, **options)
    return fixer.fix_missing_drae(text, title, summary)

wikifix['es_drae_missing'] = {
    'mode': 'function',
    "pre-fixes": [(sectionparser_cleanup, None)],
    "fixes": [(es_drae_missing, { "link_filename": f"{DRAE_DATA}/drae.links" })],
    "post-fixes": [(ele_cleanup, None)],
}

from autodooz.fix_es_forms import FixRunner
def es_add_forms(text, title, summary, options):
    fixer = get_fixer(FixRunner, **options)
    return fixer.add_forms(text, title, summary)

wikifix['es_add_forms'] = {
    'mode': 'function',
    "pre-fixes": [(sectionparser_cleanup, None)],
    "fixes": [(es_add_forms, {
        "lang_id": "es",
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
    "pre-fixes": [(sectionparser_cleanup, None)],
    "fixes": [(es_replace_forms, {
        "lang_id": "es",
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
    "pre-fixes": [(sectionparser_cleanup, None)],
    "fixes": [(pt_merge_verbs, {
        "pages": "split_verbs",
        })],
    "post-fixes": [(ele_cleanup, None)],
}

from autodooz.fix_bare_quotes import QuoteFixer
def fix_bare_quotes(text, title, summary, options):
    fixer = get_fixer(QuoteFixer)
    return fixer.process(text, title, summary)

wikifix['bare_quotes'] = {
    'mode': 'function',
    "pre-fixes": [(sectionparser_cleanup, None)],
    "fixes": [(fix_bare_quotes, None)],
    "post-fixes": [(ele_cleanup, None)],
}

from autodooz.fix_es_form_overrides import OverrideFixer
def es_form_overrides(text, title, summary, options):
    fixer = get_fixer(OverrideFixer)
    return fixer.process(text, title, summary)

wikifix['es_form_overrides'] = {
    'mode': 'function',
    "pre-fixes": [(sectionparser_cleanup, None)],
    "fixes": [(es_form_overrides, None)],
    "post-fixes": [(ele_cleanup, None)],
}

from autodooz.fix_inline_modifiers import InlineFixer
def inline_modifiers(text, title, summary, options):
    fixer = get_fixer(InlineFixer)
    return fixer.process(text, title, summary)

wikifix['inline_modifiers'] = {
    'mode': 'function',
    "pre-fixes": [(sectionparser_cleanup, None)],
    "fixes": [(inline_modifiers, None)],
    "post-fixes": [(ele_cleanup, None)],
}

from autodooz.fix_html_comments import CommentFixer
def fix_html_comments(text, title, summary, options):
    fixer = get_fixer(CommentFixer)
    return fixer.process(text, title, summary)

wikifix['html_comments'] = {
    'mode': 'function',
    "pre-fixes": [(sectionparser_cleanup, None)],
    "fixes": [(fix_html_comments, None)],
    "post-fixes": [(ele_cleanup, None)],
}



from autodooz.fix_list_to_col import ListToColFixer
def fix_list_to_col(text, title, summary, options):
    fixer = get_fixer(ListToColFixer)
    return fixer.process(text, title, summary, options)

wikifix['list_to_col'] = {
    'mode': 'function',
    "pre-fixes": [(sectionparser_cleanup, None)],
    "fixes": [(fix_list_to_col, {
        "lang_ids": ["cs"],
        "sections": ["Derived terms", "Related terms"],
        })],
    "post-fixes": [(ele_cleanup, None)],
}



from autodooz.nym_sections_to_tags import NymSectionToTag
simple_nym_fixes = [ #{
    "autofix",
    "automatch_sense",
    "automatch_nymsection_outside_word",
    "automatch_nymsection_outside_pos",
    "using_gloss_as_qualifier",
#    "long_nymline",
#    "autofix_bad_nymline",
    "pos_has_multiple_words",
    "autofix_gloss_has_quotes",
    "autofix_skip_duplicate_values",
    "unexpected_section",
    "autofix_nymsection_has_subsections",
    "autofix_gloss_as_sense",
    "autofix_parenthetical_as_sense",
    "both_nym_line_and_section",
    "duplicate_section",
#    "nymsection_matches_multiple_pos",
#    "nymsense_matches_no_defs",
#    "partial_fix",
    "link_wrong_lang",
    "link_is_multi_brackets",
] #}

def _fix_nyms(text, title, summary, options, fixes):
    fixer = get_fixer(NymSectionToTag, **options)
    return fixer.process(text, title, summary, fixes)

def fix_simple_nyms(text, title, summary, options):
    return _fix_nyms(text, title, summary, options, simple_nym_fixes)

def fix_all_nyms(text, title, summary, options):
    return _fix_nyms(text, title, summary, options, ["all"])

wikifix['es_simple_nyms'] = {
    'mode': 'function',
    "pre-fixes": [(sectionparser_cleanup, None)],
    "fixes": [(fix_simple_nyms, {
        "lang_id": "es",
        "wordlist": f"{SPANISH_DATA}/es-en.data",
        })],
    "post-fixes": [(ele_cleanup, None)],
}

# Not safe to run automatically
wikifix['es_all_nyms'] = {
    'mode': 'function',
    "pre-fixes": [(sectionparser_cleanup, None)],
    "fixes": [(fix_all_nyms, {
        "lang_id": "es",
        "wordlist": f"{SPANISH_DATA}/es-en.data",
        })],
    "post-fixes": [(ele_cleanup, None)],
}
