import enwiktionary_sectionparser as sectionparser
import mwparserfromhell as mwparser
import re
from collections import defaultdict

# TODO: support redirects/aliases

def get_page_fixes(page, all_fixes):
    return [f for f in all_fixes if f.get("title", "*") in [page, "*"]]

def get_section_fixes(section_path, all_fixes):
    if section_path == "*":
        return all_fixes

    fixes = []
    for f in all_fixes:
        section_match = f.get("section", "*")

        if section_match == "*":
            fixes.append(f)

        elif any(c in f for c in "*?^$"):
            if re.match(section_match, section_path):
                fixes.append(f)

        elif ":" in section_match:
            if section_match == section_path:
                fixes.append(f)

        elif section_path == section_match:
            fixes.append(f)

        elif section_path.endswith(":" + section_match):
            fixes.append(f)

    return fixes

def name_matches(template, match):
    template_name = str(template.name).strip()
    if "name_regex" in match:
        matches = bool(re.search(match["name_regex"], template_name, flags=re.DOTALL))
        return bool(re.search(match["name_regex"], template_name, flags=re.DOTALL))
    if "name" in match:
        return template_name == match["name"]
    raise ValueError("no name match specified")

def get_template_changes(template, wiki_context, fixes):

    for fix in fixes:
        for match in fix["templates"]:
            tmpl = match["template"]
            if not name_matches(template, tmpl):
                continue

            context_pattern = tmpl.get("context_regex")
            if context_pattern:
                #assert "{{TMPL}}" in context_pattern

                orig_name = str(template.name)
                template.name = "AUTODOOZ_MATCH"
                context_pattern = context_pattern.replace("{{TMPL}}", re.escape(str(template)))
                context_match = re.search(context_pattern, str(wiki_context), flags=re.DOTALL)
                template.name = orig_name

                if not context_match:
                    continue
                return match["changes"]

            pattern = tmpl.get("regex")
            if pattern and (pattern == "*" or re.search(pattern, str(template).strip())):
                return match["changes"]

            # exact match by parameter comparison
            params = tmpl.get("parameters")
            # possible bug if duplicate params
            if params and len(params) == len(template.params) and all(template.has(p[0]) and str(template.get(p[0]).value).strip() == p[1] for p in params):
                return match["changes"]

            # exact match by string
            wikitext = tmpl.get("wikitext")
            if wikitext and wikitext.strip() and wikitext.strip() == str(template).strip():
                return match["changes"]

            # no filtering, just match by template name
            #return match["changes"]



def apply_template_changes(t, changes, summary):

    t_name = str(t.name).strip()

    for change in changes:
        assert "action" in change
        assert change.keys() - {"action", "summary"} == set()
        action, *values = change["action"]
        if action == "rename_template":
            assert len(values) == 1
            new_name = values[0]
            t.name = new_name
        if action == "rename_template_regex":
            assert len(values) == 2
            new_name = re.sub(values[0], values[1], str(t.name))
            assert new_name != str(t.name)
            t.name = new_name
        elif action == "remove":
            assert len(values) == 1
            key = values[0]
            if t.has(key):
                t.remove(t.get(key))
        elif action == "add":
            assert len(values) == 2
            key, value = values
            if t.has(key):
                t.get(key).value = value
            if not t.has(key):
                t.add(key, value)

        elif action == "rename_param":
            assert len(values) == 2
            old, new = values
            if t.has(old):
                assert not t.has(new)
                k = t.get(old)
                k.name = str(k.name).replace(old, new)
                if not new.isdigit():
                    k.showkey = True
                if new == "1":
                    k.showkey = False

        elif action == "set":
            assert len(values) == 2
            name, new_value = values
            if t.has(name):
                k = t.get(name)
                k.value = str(k.value).replace(str(k.value).strip(), new_value)

        elif action == "regex_sub":
            # "regex_sub" is processed later
            continue
        else:
            raise ValueError("Unsupported action", action, change)

        if "summary" in change:
            message = "[[T:" + t_name + "|{{" + t_name + "}}]] - " + change["summary"]
            if message not in summary:
                summary.append(message)


def fix_templates(entry_text, entry_title, summary, all_fixes):

    page_fixes = get_page_fixes(entry_title, all_fixes)
    if not page_fixes:
        return entry_text

    uses_section_filters = any(f for f in page_fixes if f.get("section", "*") != "*")
    if uses_section_filters:
        entry = sectionparser.parse(entry_text, entry_title)
        if not entry:
            return entry_text
        for section in entry.ifilter_sections():
            section_fixes = get_section_fixes(section.path, page_fixes)
            if not section_fixes:
                continue
            section_lines = "\n".join(section.content_wikilines)
            wiki = mwparser.parse(section_lines)

            replacements = []
            for t in wiki.ifilter_templates():

                changes = get_template_changes(t, wiki, section_fixes)
                if not changes:
                    continue

                old = str(t)
                apply_template_changes(t, changes, summary)
                new = str(t)

                # "regex_sub" is allowed only as the very last change
                change = changes[-1]
                action, *values = change["action"]
                if action == "regex_sub":
                    assert len(values) == 2
                    pattern, replacement = values
                    assert "{{TMPL}}" in pattern
                    replacement = replacement.replace("{{TMPL}}", str(t))

                    orig_name = str(t.name)
                    placeholder_name = "AUTODOOZ_MATCH" + str(len(changes)+1)
                    t.name = placeholder_name
                    pattern = pattern.replace("{{TMPL}}", re.escape(str(t)))
                    re_old = re.search(pattern, str(wiki), flags=re.MULTILINE)


                    #print([pattern, str(wiki), re_old])
                    if re_old:
                        old = re_old.group(0)
                        new = re.sub(pattern, replacement, old, flags=re.MULTILINE)
                        new = new.replace(placeholder_name, orig_name)

                        message = "[[T:" + orig_name + "|{{" + orig_name + "}}]] - " + change["summary"]
                        if message not in summary:
                            summary.append(message)
                    else:
                        t.name = orig_name

                    #print("FIX:", [old,new])
                else:
                    new = str(t)

                if old != new:
                    replacements.append((old, new))

            if replacements:
                #print("CHANGES", replacements)
                new_section_lines = str(wiki)
                for old, new in replacements:
                    new_section_lines = new_section_lines.replace(old, new)

                #print(new_section_lines)
                section.content_wikilines = [new_section_lines]

        new_text = str(entry)

    else:
        wiki = mwparser.parse(entry_text)
        for t in wiki.ifilter_templates():

            changes = get_template_changes(t, wiki, page_fixes)
            if not changes:
                continue

            apply_template_changes(t, changes, summary)
        new_text = str(wiki)

    if not summary:
        return entry_text

    return new_text
