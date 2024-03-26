import enwiktionary_sectionparser as sectionparser
import json
import re
import multiprocessing
import os
import sys
import mwparserfromhell as mwparser

from autodooz.sections import ALL_POS, COUNTABLE_SECTIONS, ALL_LANGS
from .list_mismatched_headlines import is_header


def clean_name(obj):
    text = re.sub(r"<!--.*?-->", "", str(obj.name), flags=re.DOTALL)
    return text.strip()

def clean_value(t, key):
    text = re.sub(r"<!--.*?-->", "", unescape(str(t.get(key).value)))
    return text.strip()




class RqTemplateFixer():

    def __init__(self, bad_template_file):
        self._summary = None
        self._log = []

        if bad_template_file:
            with open(bad_template_file) as infile:
                self._ignore_templates = set(json.load(infile))
        else:
            self._ignore_templates = set()

        self._ignore_templates |= { "RQ:Darwin Origin of Species", "RQ:nod:NT", "RQ:pi:Sinhala Majjhimanikaya 2", "RQ:pi:Sinhala Majjhimanikaya 1", "RQ:pi:Dhtm", "RQ:pi:PTS Petavatthu", "RQ:pi:DN3 cty", "RQ:sa:Tamil Sahasranama" }  #, "RQ:Barrow Pope's Supremacy" }



    def fix(self, code, page, details):
        if self._summary is not None:
            self._summary.append(details)

        self._log.append(("autofix_" + code, page, details))

    def warn(self, code, page, details=None):
        #print(code, page, details)
        self._log.append((code, page, details))

    def process(self, page_text, page, summary=None, options=None):

        # This function runs in two modes: fix and report
        #
        # When summary is None, this function runs in 'report' mode and
        # returns [(code, page, details)] for each fix or warning
        #
        # When run using wikifix, summary is not null and the function
        # runs in 'fix' mode.
        # summary will be appended with a description of any changes made
        # and the function will return the modified page text

        self._summary = summary
        self._log = []

#        if "/" in page:
#            return page_text if summary is not None else []

        if "#REDIRECT" in page_text:
            return page_text if summary is not None else []

#        if page != "Template:RQ:Orwell Animal Farm":
#            return page_text if summary else []

#        if not page.startswith("Template:RQ:"):
#            return page_text if summary is not None else []

        if page.removeprefix("Template:") in self._ignore_templates:
            print("SKIPPING KNOWN BAD TEMPLATE", page)
            return page_text if summary is not None else []

        ALLOWED_INVOKE = [ "quote", "string", "reference information", "ugly hacks" ]
        invokes = [m.group(1).strip() for m in re.finditer("{{#invoke:(.*?)[|}]", page_text, re.DOTALL)]
        if not all(i in ALLOWED_INVOKE for i in invokes):
            print("Unhandled module call to", [i for i in invokes if i not in ALLOWED_INVOKE])
            #return page_text if summary is not None else []

        quote_invokes = len([i for i in invokes if i == "quote"])
        if quote_invokes > 1:
            print("Unhandled: multiple quote invokes")
            return page_text if summary is not None else []

        if quote_invokes == 1:
            page_text = self.cleanup_template(page_text, page)

        else:
            page_text = self.convert_template(page_text, page)

        if summary is None:
            return self._log

        return page_text

    @staticmethod
    def get_synonyms(text):

        # if text is composed only of a list of synonymous variables, like
        # "{{{text|{{{passage|{{{4|}}}}}}}}}", return the variable names
        # otherwise, return None

        syns = []
        pattern = r"^\s*⎨⎨⎨\s*([a-zA-Z0-9 _-]+)\s*⌇?\s*(.*?)\s*⎬⎬⎬\s*$"
        m = re.match(pattern, text)

        while m:
            syns.append(m.group(1).strip())
            text = m.group(2)
            m = re.match(pattern, text)

        if not text:
            return syns

    @staticmethod
    def remove_params(template, params):
        to_remove = []
        for p in template.params:
            if clean_name(p) in params:
                to_remove.append(p)

        for p in to_remove:
            template.remove(p)

        return bool(p)

    def get_includeonly(self, page_text, page):

        stripped = re.sub(r"<(\s*[/]?\s*(includeonly)\s*[/]?\s*)>", "", page_text)
        stripped = re.sub(r"<\s*noinclude\s*>.*?<\s*/\s*noinclude\s*>", "", stripped, flags=re.DOTALL)
        stripped = re.sub(r"<\s*nowiki\s*>.*?<\s*/\s*nowiki\s*>", "", stripped, flags=re.DOTALL)
        stripped = re.sub(r"<!--.*?-->", "", stripped, flags=re.DOTALL)
        stripped = stripped.strip()

        return stripped


    def parse_single_template(self, page_text, page):

        stripped = self.get_includeonly(page_text, page)
        stripped = escape(stripped)

        wiki = mwparser.parse(stripped)
        try:
            t = next(wiki.ifilter_templates(recursive=False))
        except StopIteration:
            self.warn("no_template", page)
            return

        orig_name = str(t.name)
        t_name = clean_name(t)
        t_min_len = len(str(t))

        if str(t) != stripped:
            self.warn("text_outside_template", page)
            #print(stripped)
            #print("-----")
            #print(t)
            # TODO: uncomment
            #return page_text

        # Now that we know that there's a single template, start over with the unstripped text
        # and escape everything that the parser should ignore

        escaped = escape(page_text)
        try:
            escaped = re.sub(r"{{\s*" + re.escape(orig_name) + r"\s*≺!--.*?--≻\s*[|]", "{{" + orig_name + "\n|", escaped, flags=re.DOTALL)
        except:
            print("failed", [page, orig_name])
            exit()


        wiki = mwparser.parse(escaped)
        try:
            t = next(wiki.ifilter_templates(recursive=False))
        except StopIteration:
            print("no template found", page)
            return
            print("----")
            print(escaped)
            print("----")
            print("failed", page)
            exit(1)

        # Sanity check, should never trip
        #print([clean_name(t), t_name], page)
        #print(escaped)
        if clean_name(t) != t_name:
            self.warn("parse_error", page, f"mismatched template names after escaping: new: '{clean_name(t)}', old: '{t_name}'")
            print("mismatched template names after escaping",[page, clean_name(t), t_name])
            return

        # Sanity check, trips when bad parsing
        if len(str(t)) < t_min_len:
            self.warn("parse_error", page, f"mismatched template lengths after escaping: new: '{len(str(t))}', old: '{t_min_len}'")
            print("parse_error, mismatch between stripped template and escaped template", page)
            #print(page_text)
            #print("_------------")
            #print(escaped)
            #print("_------------")
            #print(t)
            return

        return wiki

    def convert_template(self, page_text, page):

        wiki = self.parse_single_template(page_text, page)
        if not wiki:
            return page_text
        t = next(wiki.ifilter_templates(recursive=False))

        t_name = clean_name(t)

        if t_name not in ["quote-book", "quote-journal", "quote-text", "quote-web", "quote-av", "quote-song", "quote-video game"]:
            self.warn("unhandled_template", page, t_name)
            return

        # cleanup overzealous line break handling
        for p in t.params:
            p.value = re.sub(r"≺!--\s*\n\s*--≻", "\n", str(p.value), flags=re.DOTALL)


        if t.has("author") and  str(t.get("author").value).strip().startswith("w:"):
            t.get("author").value = t.get("author").value.lstrip().removeprefix("w:")
#            self.warn("authorlink", page, str(t.get("author")))
#            return page_text


        parsed_params = [ clean_name(p) for p in t.params if clean_name(p) != "1" ]
        if any(p.isdigit() for p in parsed_params):
            self.warn("uses_positional_params", page, parsed_params)
            return page_text

        propagate_params = []
        remove_params = []
        for p in t.params:
            name = clean_name(p)
            if re.match(fr"^⎨⎨⎨\s*{name}\s*[⌇]?\s*⎬⎬⎬$", p.value.strip()):
                propagate_params.append(name)
                remove_params.append(name)

        pageparams = []
        if "pages" in parsed_params and "pages" not in propagate_params:
            self.warn("complex_pages", page, propagate_params)
        else:
            if "page" in parsed_params and "page" not in propagate_params:
                pageparams = self.get_synonyms(t.get("page").value.strip())
#                if pageparams is None:
#                    self.warn("page_param_not_syns", page)
#                    return page_text

                # If there are no aliases, don't generate pageparams
                if pageparams and all(p in ["page", "pages"] for p in pageparams):
                    pageparams = []

                if pageparams:

                    # using pageparams= implies "page" and "pages", so no need to include them
                    for k in ["page", "pages"]:
                        if k in pageparams:
                            pageparams.remove(k)
                        if k in parsed_params and k not in remove_params:
                            remove_params.append(k)

                    if pageparams:
                        for k in ["page", "pages"] + pageparams:
                            # only "page" can have complex values, everything else should be not declared or a simple propagate
                            if k in parsed_params and k not in propagate_params and k != "page":
                                self.warn("page_syn_has_other_use", page, k)
                                return page_text
                            if k in propagate_params:
                                propagate_params.remove(k)
                                if k not in remove_params:
                                    remove_params.append(k)


        assert not ("passage" in parsed_params and "text" in parsed_params)

        textparams = []
        for k in ["passage", "text"]:
            if k not in parsed_params:
                continue

            # Simple pass-through, delete it and let the auto propagation handle it
            if k in propagate_params:
                propagate_params.remove(k)

            # handle textparams= if it's a list of synonyms
            else:
                #print([k, t.get(k).value.strip()])
                textparams = self.get_synonyms(t.get(k).value.strip())
                if textparams is None:
                    self.warn("text_param_not_syns", page, k)
                    # TODO: uncomment
#                    return page_text

                if textparams:

                    # "text" and "passage" are automatically propagated
                    for k in ["text", "passage"]:
                        if k in textparams:
                            textparams.remove(k)
                        if k in propagate_params:
                            propagate_params.remove(k)
                        if k not in remove_params:
                            remove_params.append(k)

                    # any synonyms in textparams don't need to be included in propagateparams
                    for k in textparams:

                        # only generate pageparams= if it will a synonym other than "page" and "pages"
                        if k in parsed_params:

                            # only "passage" or "text" can have complex values, everything else should be not declared or a simple propagate
                            if k in parsed_params and k not in propagate_params and k not in ["passage", "text"]:
                                self.warn("text_syn_has_other_use", page, k)

                            if k in propagate_params:
                                propagate_params.remove(k)
                            if k not in remove_params:
                                remove_params.append(k)



        sep_before_eq = " " if any(str(p.name).endswith(" ") for p in t.params) else ""
        sep_after_eq = " " if any(str(p.value).startswith(" ") for p in t.params) else ""
        eol = "\n" if any(str(p.value).endswith("\n") for p in t.params) else ""

        if textparams:

            replace_param = None
            for p in t.params:
                if clean_name(p) in ["passage", "text"]:
                    replace_param = p
                    break

            name = "textparam" + sep_before_eq
            value = sep_after_eq + ",".join(textparams)

            if replace_param:
                remove_params.remove(clean_name(replace_param))
                replace_param.name = name
                replace_param.value = value + eol
            else:
                t.add(name, value) # eol handled automatically by Template

        if pageparams:

            replace_param = None
            for p in t.params:
                if clean_name(p) in ["page", "pages"]:
                    replace_param = p
                    break


            name = "pageparam" + sep_before_eq
            value = sep_after_eq + ",".join(pageparams)

            if replace_param:
                remove_params.remove(clean_name(replace_param))
                replace_param.name = name
                replace_param.value = value + eol
            else:
                t.add(name, value) # eol handled automatically by Template


        # remove the propagated params
        self.remove_params(t, remove_params)

        # strip out auto propagated params
        propagate_params = [p for p in propagate_params if p not in ["brackets", "footer", "text", "passage"]]

        if propagate_params:

            for p in propagate_params:
                if p.isdigit():
                    self.warn("numbered_propagateparams", page, propagate_params)
                    return page_text

            prev_param = t.params[-1]
            if not "\n" in str(prev_param.value) and not str(prev_param.name).strip().isdigit():
                prev_param.value = str(prev_param.value) + "\n"
            name = "propagateparams" + sep_before_eq
            value = sep_after_eq + ",".join(propagate_params) + "\n"
            t.add(name, value, preserve_spacing=False)

        allowparams = self.get_allowparams(unescape(str(wiki)), page)
        if allowparams is None:
            self.warn("failed_generating_allowparams", page)
            return page_text

        if allowparams:
            prev_param = t.params[-1]
            if not "\n" in str(prev_param.value) and not str(prev_param.name).strip().isdigit():
                prev_param.value = str(prev_param.value) + "\n"
            name = "allowparams" + sep_before_eq
            value = sep_after_eq + ",".join(allowparams) + "\n"
            t.add(name, value, preserve_spacing=False)


        template_name = clean_name(t)
        assert template_name in ["quote-book", "quote-journal", "quote-text", "quote-web", "quote-av", "quote-song", "quote-video game"]

        template_line = "" if clean_name(t) == "quote-book" else f"|template={clean_name(t)}\n"

        new_text = unescape(str(wiki))
        new_text = new_text.replace(str(t.name), f"#invoke:quote|call_quote_template\n{template_line}")


#        if len(allowparams) > 5 and len(new_text) < 3000 and ":pl:" not in page and "zlw-opl:" not in page:
#            print(page)

        self.fix("converted", page, "converted to Module:quote")
        return new_text


    def cleanup_template(self, page_text, page):

        #allow_params = self.old_get_allowparams(page_text, page)
        allow_params = self.get_allowparams(page_text, page)
        if not allow_params:
            return page_text

#        print(allow_params)
#        exit()

        new_params = ",".join(allow_params)

        m = re.search(r"^\s*[|]\s*allowparams\s+=\s+(.+)\s*$", page_text, re.MULTILINE)
        if not m and not new_params:
            return page_text

        if not m:
            self.warn("missing_allowparams", page)
            return page_text

        old_line = m.group(0)
        old_params = m.group(1)
        #print("OLD", [old_line])


        if sorted(old_params) == sorted(new_params):
            return page_text


        if not new_params:
            self.fix("remove_allowparams", page, "removed allowparams=")
            new_line = ""

        else:
            self.fix("set_allowparams", page, "set allowparams=")
            new_line = old_line.replace(old_params, new_params)

        page_text = page_text.replace(old_line, new_line)
        return page_text


    def old_get_allowparams(self, page_text, page):

        used_params = self.get_used_params(page_text)
        auto_props = self.get_auto_props(page_text, page)
        if auto_props is None:
            self.warn("unparsable", page)
            return page_text

        declared_params = self.get_declared_params(page_text)

        return [p for p in used_params if p not in declared_params]

    @staticmethod
    def get_param_value_list(template, key):

        if not template.has(key):
            return []

        value = clean_value(template, key)

        m = re.match(r"^([a-zA-Z0-9,_ -]*)$", value)
        if not m:
            print("NO MATCH", clean_name(template.get(key)), value)
            #print(text)
            return

        return [p.strip() for p in m.group(1).split(",")]


    def get_allowparams(self, page_text, page):

#        used_params = self.get_used_params(text)
#        auto_props = self.get_auto_props(text, page)
#        if auto_props is None:
#            return
#
#        declared_params = self.get_declared_params(text)
#
#        return [p for p in used_params if p not in declared_params]


        wiki = self.parse_single_template(page_text, page)
        if not wiki:
            return page_text
        t = next(wiki.ifilter_templates(recursive=False))


        propagate_params = self.get_param_value_list(t, "propagateparams")
        #print("prop", propagate_params)
        if propagate_params is None:
            return

        textparams = self.get_param_value_list(t, "textparam")
        #print("textparams", propagate_params)
        if textparams is None:
            return

        pageparams = self.get_param_value_list(t, "pageparam")
        #print("pageparams", propagate_params)
        if pageparams is None:
            return

        auto_propagated = propagate_params + ["brackets", "footer", "text", "passage"] + textparams + pageparams
        if pageparams:
            auto_propagated += ["page", "pages"]
        allowparams = [p for p in self.get_used_params(page_text) if p not in auto_propagated]

        return allowparams

    @staticmethod
    def get_used_params(text):
        return list({m.group(1):1 for m in re.finditer(r"\{\{\{([a-zA-Z0-9 _-]+?)[|}]", text)}.keys())

    @staticmethod
    def get_declared_params(text):
        return list({m.group(1):1 for m in re.finditer(r"[|]\s*(:?text|page)param\s+=\s+([0-9])\s*$", text, re.MULTILINE)}.keys())

    @classmethod
    def get_auto_props(cls, text, title):

        text_params = cls.get_params("textparam", text, title)
        if text_params is None:
            return

        if text_params != ["-"]:
            text_params += ["text", "passage"]

        page_params = cls.get_params("pageparam", text, title)
        if page_params is None:
            return
        if page_params:
            page_params += ["page", "pages"]

        return ["brackets", "footer"] + text_params + page_params

    @staticmethod
    def get_params(key, text, title):

        if key not in text:
            return []

        manual_props = []
        m = re.search(r"[|]\s*" + key + r"\s*=\s*([^{=}]*?)\s*($|[}|])", text)
        if not m:
            return None
            print(f"UNABLE TO PARSE {key} in {title}")
            print("-----")
            print(text)
            print("-----")
            raise ValueError("unparsable")

        res = [p.strip() for p in m.group(1).split(",")]

        return res



