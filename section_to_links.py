from enwiktionary_templates import ALL_LANGS, ALL_LANG_IDS
from enwiktionary_templates import ALIASES
from collections import defaultdict
from .utils import nest_aware_split, template_aware_finditer

import mwparserfromhell as mwparser
import re
import sys

_GET_ALIASES = None
def get_aliases(*templates):
    global _GET_ALIASES
    if _GET_ALIASES is None:
        _GET_ALIASES = defaultdict(list)
        for k,v in ALIASES.items():
            _GET_ALIASES[v].append(k)

    aliases = []
    for template in templates:
        if template not in _GET_ALIASES and template in ALIASES:
            new_template = ALIASES[template]
            print(f"WARNING: {template} is an alias of {new_template}", file=sys.stderr)
            template = new_template

        aliases.append(template)
        aliases += _GET_ALIASES.get(template, [])
    return list(set(aliases))

TOP_TEMPLATES = get_aliases("box-top", "der-top", "rel-top")
LINK_TEMPLATES = get_aliases("link", "mention", "ll", "l-lite", "seeSynonyms", "see")
#LANG_LINK_TEMPLATES = get_aliases("zh-l", "vi-l", "he-l", "ja-r", "ko-l", "th-l", "ja-l")
LANG_LINK_TEMPLATES = []
Q_TEMPLATES = get_aliases("qualifier")
SENSE_TEMPLATES = get_aliases("sense", "sense-lite", "antsense")

# kinda hacky - global variable overridden by call to section_to_list() that passes a variable
# to collect parser warnings
_log = None
def warn(code, section, details):
    if _log is None:
        print("WARN:", code, section.page, section.path, " :: ", details, file=sys.stderr)
    else:
        _log.append((code, section.page, section.path,  details))

def strip_templates(text):
    old_text = None
    while text != old_text:
        old_text = text
        text = re.sub(r"\{\{[^{}]*?\}\}", "", old_text)

    return text



def link_template(lang_id, target, alt):
    if alt:
        return "{{l|" + lang_id + "|" + target + "|alt=" + alt + "}}"

    return "{{l|" + lang_id + "|" + target + "}}"

def brackets_to_links(lang_id, text):
    """ convert [[wikilinks]] to {{l|en|template links}} """

    prev_text = ""
    while prev_text != text:
        prev_text = text

        changes = []

        # Convert [[link]] to {{l|XX|link}}
        m = next(template_aware_finditer(r"\[\[\s*([^\{\[\]\|]*?)(?:\s*\|\s*(?P<alt>.*))?\s*\]\](?P<tail>[^\W_]*)", text), None)
        if not m:
            break

        target = m.group(1).split("#")[0]

        if target.startswith("WS:"):
            target = "Thesaurus:" + target[3:]

        # Don't convert links like [[w:entry]]
#        if ":" in target and "Thesaurus:" not in target:
#            return match.group(0)

        alt = m.group('alt') if m.group('alt') else ""
        if m.group('tail'):
            alt = alt + m.group('tail') if alt else target + m.group('tail')

        if alt == target:
            alt = None

        text = text[:m.start()] + link_template(lang_id, target, alt) + text[m.end():]

    return text



def get_link(lang_id, section, line, refs):
    """
    Returns a string
    return None if item cannot be parsed
    """
    item = None
    params = {}

    def handle_refs(m):
        if "ref" not in params:
            params["ref"] = []
        params["ref"].append(refs[int(m.group(1))])
        return ""

    # convert ##REFS## placeholders to ref params
    line = re.sub(r"##REF(\d+)##", handle_refs, line)

    #text = bare_text_to_link(lang_id, line)
    text = brackets_to_links(lang_id, line)


    no_templates = strip_templates(text)
    if no_templates.strip("\n ,;*#:."):
        warn("text_outside_template_item", section, line)
        return

    wikicode = mwparser.parse(text)
    for template in wikicode.filter_templates(recursive=False):

        t_name = template.name.strip()

        if t_name in ["vern", "taxlink", "taxfmt"]:
            if item:
                warn("multiple_link_templates", section, line)
                return
            item = str(template)

        elif t_name in LANG_LINK_TEMPLATES:
            if item:
                warn("multiple_link_templates", section, line)
                return

            if len(template.params) != 1 or not template.has("1"):
                warn("unhandled_lang_link_params", section, str(template))
            item = str(template.get("1").value).strip()

        elif t_name in LINK_TEMPLATES:
            if item:
                warn("multiple_link_templates", section, line)
                return

            for l_param in template.params:
                k = l_param.name.strip()
                v = l_param.value.strip()

                if not v:
                    continue

                if k.isnumeric():
                    if k == "1":
                        continue
                    elif k == "2":
                        item = v
                        continue
                    elif k == "3":
                        k = "alt"
                    elif k == "4":
                        k = "t"
                    else:
                        warn("l_has_params", section, str(template))
                        return

                if k == "gloss":
                    k = "t"

                if k in [ 'alt', 't', 'tr', 'lit', 'ts', 'pos', 'id', 'sc', 'g' ]:
                    params[k] = v

                else:
                    warn("l_has_params", section, str(template))
                    return

        # TODO: handle {{w}} as a link-like template

        elif template.name.strip() == "g":
            if len(template.params) != 1:
                warn("g_has_multiple_params", section, str(template))
                return

            gender = template.get(1).value.strip()
            if "g" in params and params["g"] != gender:
                warn("item_has_multiple_genders", section, str(template))
                return

            params["g"] = gender

        elif template.name.strip() in Q_TEMPLATES:
            if not all(str(p.name).strip().isdigit() for p in template.params):
                warn("qualifier_has_unhandled_param", section, str(template))

            q = "qq" if item else "q"
            if q in params:
                warn("item_has_multiple_qualifiers", section, str(template))
                return

            params[q] = ", ".join(str(p.value).strip() for p in template.params)

        else:
            if template.name.strip() not in [ "zh-l", "zh-dial", "syn-saurus", "ja-r", "ko-l", "vi-l", "dial syn", "zh-Christian-syn", "th-l", "kne-xnn-synonyms", "dialect synonyms", "he-l", "ja-l", "syndiff", "zh-dial-syn", "ryu-r", "l/ja", "fi-dial" ]:
                warn(f"unexpected_template_{str(template.name).strip()}", section, str(template))
            return

    if not item:
        warn("no_item", section, line)
        return

    res = [item]
    for k,v in sorted(params.items(), key=lambda x: ({'pos':0, 'g':1, 'alt':2, 't':3, 'tr':4, 'lit':5, 'ts':6, 'id':7, 'sc':8}.get(x[0], 9), x[0], x[1])):
        if k == "ref":
            if len(v) > 1:
                warn("multi_ref", section, line)
                return
            v = v[0]
        elif "<" in v or ">" in v or "{" in v:
            warn("bad_parameters", section, v)
            return
        res.append(f"<{k}:{v}>")


    if any(t is None for t in res):
        warn("unparsable_list", section, line)
        #lang, page = list(section.lineage)[-2:]
        #print(f"error: null value in res\n{res}\n {line}\n{page}:{section.path}")
        return

    link = "".join(res)

    # strip empty comments
    link = re.sub(r"<!--\s*-->", "", link, flags=re.DOTALL)

    return link



def get_links(lang_id, section, line, refs=[]):

    if line.startswith("*"):
        line = line[1:]
    line = line.strip()
    if not line:
        warn("no_line_data", section, line)
        return

    # Strip "see also" and variants
    # also convert any leading ";" to ","
    replacements = []
    for m in template_aware_finditer(r"[;,]*\s*('')?[Ss]ee( also)?('')?\s*", line):
        replacements.append((m.start(), m.end()))
    for start, end in reversed(replacements):
        line = line[:start] + ", " + line[end:]

    line = line.strip(" ,")


    if "<ref" in line or "{{R:" in line or "{{RQ:" in line:
        warn("has_references", section, line)
        return

    #print("LINE:", line)

    for splitter in [",", ";", "/"]:
        parts = [part for part in nest_aware_split(splitter, line, [("{{", "}}"), ("[[","]]"), ("<", ">")]) if part.strip()]
        if len(parts) > 1:
            #print("PART", parts, [line])
            links = [get_link(lang_id, section, part, refs) for part in parts if part.strip()]
            if not links:
                continue

            if any(link is None for link in links):
                return

            # disallow mixed qualified/unqualified in a list
            if not sum(1 if "<q:" in link else 0 for link in links) in [0, len(links)]:
                warn("ambig_q_qualifiers", section, line)
                return

            if not sum(1 if "<qq:" in link else 0 for link in links) in [0, len(links)]:
                warn("ambig_qq_qualifiers", section, line)
                return

            return links

    #print("UNSPLIT LINE")

    # check if it's a single {{colX template
    if line.startswith("{{col"):
        wikicode = mwparser.parse(line)
        template = next(wikicode.ifilter_templates())
        if str(template.name).strip() not in ["col", "col1", "col2", "col3", "col4", "col5", "col6"]:
            warn("unhandled_column_template", section, line)
            return

        if str(template) != line.strip():
            warn("text_outside_col_template", section, line)
            return


        values = []
        for p in template.params:
            name = str(p.name).strip()

            if name in ["n", "collapse"]:
                continue

            if not name.isdigit():
                # TODO: convert xN values to <x:> inline modifiers
                warn("unhandled_col_params", section, str(template))
                return

            if str(name) == "1":
                continue

            val = str(p.value).strip()
            if not val:
                continue

            if "{{" in val:
                warn("complex_col_values", section, str(template))
                return

            values.append(val)

        return values


    link = get_link(lang_id, section, line, refs)
    if link:
        #print("LINK" ,link)
        return [link]



def _extract_refs(m, refs):
    name = None
    if m.group(1).strip():
        match = re.match(r'''name\s*=\s*(?:"(.*?)"|'(.*?)'|([a-zA-Z\d_-]+))\s*$''', m.group(1))
        if not match:
            warn("unhandled ref", section, line)
            return m.group(0)
        if match.group(1):
            name = match.group(1)
        elif match.group(2):
            name = match.group(2)
        else:
            name = match.group(3)

    data = m.group(2).strip() if len(m.groups())>1 else ""

    if name:
        refs.append(f"<<name:{name}>>{data}")
    else:
        refs.append(data)

    return f"##REF{len(refs)-1}##"


# input "test <ref>foo</ref> <ref>bar<ref>"
# returns ["foo", "bar"], "test ##REF1## ##REF2##"
def extract_refs(section, line):
    refs = []

    # <ref name="test"/>
    line = re.sub(r"<ref\s+([^>]*)\s*/\s*>", lambda x: _extract_refs(x, refs), line)
    # <ref>blah</ref>
    # <ref name="test">blah</ref>
    line = re.sub(r"<ref\s*([^/>]*)>(.*)?<\s*/\s*ref\s*>", lambda x: _extract_refs(x, refs), line)

    return refs, line


LABEL_TEMPLATES = get_aliases("label")
ALL_TITLE_TEMPLATES = sorted(LABEL_TEMPLATES + SENSE_TEMPLATES + Q_TEMPLATES)

def extract_titles(section, line):

    m = re.match(r"^(\*?\s*)\{\{\s*(" + "|".join(ALL_TITLE_TEMPLATES) + r")\s*\|", line)
    if m:
#        print("MATCH", line)
        wikicode = mwparser.parse(line)
        template = next(wikicode.ifilter_templates(), None)

        name = str(template.name).strip()
        if not all(str(p.name).strip().isdigit() for p in template.params):
            warn("unhandled_title_params", section, str(template))

        if name in LABEL_TEMPLATES:
            titles = tuple(str(p.value).strip() for p in template.params if str(p.name).strip() != "1" and str(p.value).strip() not in ("", ",", ";", "_"))
        else:
            titles = tuple(str(p.value).strip() for p in template.params)

        remaining_text = line[len(m.group(1))+len(str(template)):]
        # strip trailing : after template
        padding = re.match(r"^\s*:?\s*", remaining_text).group(0)
        if padding:
            remaining_text = remaining_text[len(padding):]
        trailing_semicolon = ":" in padding

        # Q templates only count as titles when followed by a colon as in "Q: foo, bar" or when simply "Q" on its own line
        if name in Q_TEMPLATES and (remaining_text != "" and not trailing_semicolon):
            return (None,), line

        return titles, remaining_text

    if "|title=" in line:
        wikicode = mwparser.parse(line)
        template = next(wikicode.ifilter_templates(), None)
        if template and template.has("title"):
            title = str(template.get("title").value).strip()
            template.remove("title")
            return (title,), str(template)


    #print("NO MATCH", line)
    return (None,), line




def section_to_links(section, log=None):
    global _log
    _log = log

    lang, page = list(section.lineage)[-2:]
    lang_id = ALL_LANGS[lang]

    links = {}

    content_lines = [line for line in section.content_wikilines if line.strip()]
    if not content_lines:
        warn("no_content_data", section, "")
        return

    titles = (None,)
    all_links = defaultdict(list)
    for line in content_lines:

        line = line.strip()
        if not line:
            #print("NO LINE")
            continue

        # Run this before extract_titles to avoid matching "title=" in reference citations
        refs, line = extract_refs(section, line)

        new_titles, line = extract_titles(section, line)
        if new_titles != (None,):
            #print("NEW TITLE", new_title)
            for t in new_titles:
                if t in all_links:
                    warn("dup_title", section, t)
                    return

            # error: titled lines after non-titled lines
            if None in all_links:
                warn("mixed_untitled_titled", section, new_titles)
                return

            titles = new_titles
            if not line:
                continue



        links = get_links(lang_id, section, line, refs)
        #print(links, line)
        if links is None:
            #print("NO LINK", line)
            # unparsable
            return

        if any(l is None for l in links):
            #print("NULL LINK", links)
            return

        for title in titles:
            all_links[title] += links

    return all_links
