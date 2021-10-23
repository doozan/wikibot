import collections
import re
import sys
import enwiktionary_parser as wtparser
from enwiktionary_parser.languages.all_ids import languages as lang_ids
from enwiktionary_parser.wtnodes.wordsense import WordSense
from enwiktionary_wordlist.utils import wiki_to_text
from enwiktionary_wordlist.sense import Sense
from enwiktionary_parser.sections.pos import ALL_POS
from enwiktionary_wordlist.wordlist import Wordlist
from enwiktionary_wordlist.all_forms import AllForms

# Some pos entries have multiple titles, pick favorites
POS_TO_TITLE = {v: k for k, v in ALL_POS.items()}
POS_TO_TITLE.update({
    "adj": "Adjective",
    "adv": "Adverb",
    "det": "Determiner",
    "n": "Noun",
    "prep": "Preposition",
    "v": "Verb",
})

pos_to_inflection = {
    "adj": "adj",
    "adv": "adv",
    "art": "art",
    "cnum": "cnum",
    "conj": "conj",
    "det": "det",
    "interj": "interjection",
    "n": "n",
    "num": "num",
    "onum": "onum",
    "postp": "postp",
    "prep": "prep",
    "pron": "pron",
    "prop": "proper",
    "v": "v",
}

class FormFixer():

    def __init__(self, wordlist):
        self.wordlist = wordlist

    @classmethod
    def get_word_genders(cls, word):
        if word.pos == "adj":
            if "m" in word.forms:
                raise ValueError(f"Adjective declaring a masculine form: {word.word}")
                return ["f"]
            if "f" in word.forms:
                return ["m"]
            else:
                return ["m", "f"]

        return [x for x in ["m", "f"] if word.genders and x in word.genders]

    @staticmethod
    def fpl_to_f(form, word):
        idx = word.forms["fpl"].index(form)
        fems = word.forms.get("f", [])

        # Only 'quichicientas'/'quichicientos' (plural only)
        if len(fems) != len(word.forms["fpl"]):
            return
 #           raise ValueError(form, f"Plural Mismatch: {word.word} {word.pos} - {word.forms['fpl']}, {word.forms.get('f')}")

        return fems[idx]



    @classmethod
    def get_declared_forms(cls, form, wordlist, allforms):
        """ Returns a list of (pos, formtype, lemma, [lemma_genders]) for each lemma that declares form """

        poslemmas = allforms.get_lemmas(form)

        declared_forms = []
        for poslemma in poslemmas:
            pos, lemma = poslemma.split("|")

            if lemma == form:
                continue

            for word in wordlist.get_words(lemma, pos):
                genders = cls.get_word_genders(word)
                for formtype, forms in word.forms.items():

                    if formtype not in ["m","f","mpl","fpl","pl"]:
                        continue

                    if form in forms:
                        # convert feminine plural of masculine noun to plural of feminine
                        if pos == "n" and formtype == "fpl":
                            new_lemma = cls.fpl_to_f(form, word)

                            if new_lemma:
                                lemma = new_lemma
                                genders = ["f"]
                                formtype = "pl"

                        # convert "pl" to "mpl" for words that have separate masculine/feminine forms
                        elif pos not in ["n", "prop"] and formtype == "pl" and "fpl" in word.forms:
                            formtype = "mpl"

                        item = (pos, formtype, lemma, genders)
                        if item not in declared_forms:
                            declared_forms.append(item)

        return declared_forms


    all_formtypes = {
        "m": ("m", "s"),
        "mpl": ("m", "p"),
        "f": ("f", "s"),
        "fpl": ("f", "p"),
        "pl": ("", "p"),
    }


    def get_gender_plural(self, formtype):

        """
        Returns (gender, quantity, and needs_gender), where gender is "m" or "f", number is "s"(ingular) or "p"(lural)
        """

        res = self.all_formtypes.get(formtype)
        if not res:
            raise ValueError(form, f"Unexpected genderplural {pos}: {formtype}")
            return "", ""
        return res


    def get_gender_param(self, form_obj):
        pos, formtype, lemma, lemma_genders = form_obj
        gender, plural = self.get_gender_plural(formtype)

        gender = ""
        if lemma_genders == ["m", "f"]:
            if plural:
                return "g=m-p|g2=f-p"
            raise ValueError("xx", f"It seems like {lemma} can only take a plural, but {formtype} is not plural")

        elif lemma_genders == ["m"]:
            if pos == "adj" and formtype in ["fpl", "f"]:
                gender = "f"
            else:
                gender = "m"
        elif lemma_genders == ["f"]:
            gender = "f"
        else:
            if formtype in ["m", "mpl"]:
                return "g=m"
            if formtype in ["f", "fpl"]:
                return "g=f"
            if formtype == "pl" and lemma_genders == []:
                return None
            raise ValueError("Unexpected genders", lemma_genders, pos, formtype, lemma, lemma_genders)

        res = f"g={gender}"
        if plural == "p":
            res+= "-p"

        return res

    def get_es_noun_plurals(self, lemma, pos):
        res = []

        forms = wiki_to_text("{{es-noun}}", lemma)
        for kv in forms.split("; "):
            k, v = kv.split("=")
            if k == "pl":
                res.append(v)

        return res

    def get_fem_irregular_plural(self, form, form_obj):
        pos, formtype, lemma, lemma_genders = form_obj

        # emperador -> emperadora, emperatriz
        # {{es-noun|m|f=emperatriz|f2=+}}

        words = [w for w in self.wordlist.get_words(lemma, pos) if formtype in w.forms and form in w.forms[formtype]]
        word = words[0]
        if len(words) > 1 and any(w for w in words[1:] if set(w.forms) - set(word.forms)):
            w = next(w for w in words[1:] if w.forms != word.forms)
            raise ValueError(form, f"Ambiguous forms: {w.forms} != {word.forms}, cannot insert")

        plurals = word.forms.get("fpl")

        if not plurals:
            return "-"

        if len(plurals) > 1:
            idx = word.forms.get("f").index(form)
            plurals = [ plurals[idx] ]

        if self.get_es_noun_plurals(form, pos) != plurals:
            return plurals[0]


    def get_noun_head(self, form, form_obj):
        pos, formtype, lemma, lemma_genders = form_obj
        gender, plural = self.get_gender_plural(formtype)

        if gender == "m" and plural == "s":
            raise ValueError("Singular masculine noun should probably be a lemma")

        # Feminine singular is a lemma
        if gender == "f" and plural == "s":
            irregular_plural = self.get_fem_irregular_plural(form, form_obj)
            if irregular_plural:
                return "{{es-noun|f|" + irregular_plural + "}}"
            return "{{es-noun|f}}"

        gender_param = self.get_gender_param(form_obj)
        if gender_param:
            return "{{head|es|noun form|" + gender_param + "}}"
        else:
            raise ValueError("Noun form needs a gender")

    def get_form_head(self, form, form_obj):

        pos = form_obj[0]
        if pos == "n":
            return self.get_noun_head(form, form_obj)

        return self.get_generic_head(form, form_obj)

    def get_generic_head(self, form, form_obj):

        # TODO: verify this is good are good
        pos = form_obj[0]
        form_name = POS_TO_TITLE[pos].lower()
        gender_param = self.get_gender_param(form_obj)
        if gender_param:
            return "{{head|es|" + form_name + " form|" + gender_param + "}}"
        return "{{head|es|" + form_name + " form}}"


    def get_adj_gloss(self, form_obj):
        pos, formtype, lemma, lemma_genders = form_obj
        gender, plural = self.get_gender_plural(formtype)

        genderplural = "|".join(x for x in [gender, plural] if x)
        return "# {{adj form of|es|" + lemma + "||" + genderplural + "}}"

    def get_noun_gloss(self, form_obj):
        pos, formtype, lemma, lemma_genders = form_obj
        gender, plural = self.get_gender_plural(formtype)

        if gender == "f" and plural == "s":
            return "# {{female equivalent of|es|" + lemma + "}}"

        return "# {{noun form of|es|" + lemma + "||" + plural + "}}"

    def get_generic_gloss(self, form_obj):
        pos, formtype, lemma, lemma_genders = form_obj
        gender, plural = self.get_gender_plural(formtype)

        genderplural = "|".join(x for x in [gender, plural] if x)
        return "# {{inflection of|es|" + lemma + "||" + genderplural + "|p=" + pos_to_inflection[pos] + "}}"

    def get_form_gloss(self, form_obj):
        pos = form_obj[0]
        if pos == "adj":
            return self.get_adj_gloss(form_obj)
        elif pos == "n":
            return self.get_noun_gloss(form_obj)
        elif pos in pos_to_inflection:
            return self.get_generic_gloss(form_obj)

        raise ValueError("unsupported pos", pos)

    def full_pos(self, title, level, forms):
        if not forms:
            raise ValueError(title, "no forms")

        pos = forms[0][0]
        if any(f for f in forms if f[0] != pos):
            raise ValueError(form, f"expected one type of pos, but got multiples: {f[0]} != {pos}")

        res = [ "="*level + POS_TO_TITLE[pos] + "="*level ]

        # TODO: Verify all forms share a lemma ?

        res.append(self.get_form_head(title, forms[0]))
        res.append("")


        added_forms = set()
        for form_obj in forms:
            pos, formtype, lemma, lemma_genders = form_obj
            if (pos, formtype, lemma) in added_forms:
                continue
            res.append(self.get_form_gloss(form_obj))
            added_forms.add((pos, formtype, lemma))

        return res

    def generate_full_entry(self, title, forms):

        res = [
            "==Spanish==",
#            "",
#            "===Pronunciation===",
#            "{{es-IPA}}"
         ]

        prev_pos = None
        pos_forms = []
        for form in sorted(forms):
            pos, formtype, lemma, lemma_genders = form
            if pos != prev_pos:
                if prev_pos:
                    res.append("")
                    res += self.full_pos(title, 3, pos_forms)
                pos_forms = []
            pos_forms.append(form)
            prev_pos = pos
        if pos_forms:
            res.append("")
            res += self.full_pos(title, 3, pos_forms)

        return "\n".join(res)


    @staticmethod
    def compare_forms(declared_forms, existing_forms):

        missing_forms = []
        unexpected_forms = set(existing_forms)

        for x in declared_forms:
            item = (x[0], x[1], x[2])

            # Consider mpl and pl to be the same
            if x[1] in ["mpl", "pl"]:
                alt_item = (x[0], "mpl", x[2]) if x[1] == "pl" else (x[0], "pl", x[2])
            else:
                alt_item = None

            if item in existing_forms:
                if item in unexpected_forms:
                    unexpected_forms.remove(item)
            elif alt_item and alt_item in existing_forms:
                if alt_item in unexpected_forms:
                    unexpected_forms.remove(alt_item)
            else:
                missing_forms.append(x)

        return missing_forms, unexpected_forms


    def add_language_entry(self, wikt, entry, language):

        # English is always the first language
        preceeding_targets = wikt.filter_languages(matches=lambda x: x.name.strip() in [ "English", "Translingual" ] or x.name.strip() < language)
        following_targets = wikt.filter_languages(matches=lambda x: x.name.strip() not in [ "English", "Translingual" ] and x.name.strip() > language)
        if preceeding_targets:
            # Inserting between two entries
            if following_targets:
                wikt.insert_after(preceeding_targets[-1],  entry + "\n\n----\n\n")

            # Appending to a single entry
            else:
                # Single entry, but ends with ---- (unusual, but exists)
                if re.search(r"\n----\s*$", str(preceeding_targets[-1])):
                    wikt.insert_after(preceeding_targets[-1], "\n" + entry )
                else:
                    wikt.insert_after(preceeding_targets[-1],  "\n\n----\n\n" + entry )

        elif following_targets:
            target = following_targets[0]
            wikt.insert_before(target, entry + "\n\n----\n\n")
        else:
            wikt.add_text(entry)


    @classmethod
    def get_existing_forms(cls, wikt):
        existing_forms = {}

        for sense in wikt.filter_wordsenses():
            pos_title = re.sub("[ 1-9]+$", "", sense._parent._parent.name)
            pos = ALL_POS[pos_title]

            if pos == "v" or pos not in pos_to_inflection:
                continue

            gloss = wiki_to_text(str(sense.gloss), "title").lstrip("# ")
            if " of " not in gloss:
                continue

            formtype, lemma, nonform = Sense.parse_form_of(gloss)

            # Limit to the formtypes we can handle, forms like "misspelling of" aren't our concern
            if formtype in cls.all_formtypes:

                lemma = lemma.strip()
                item = (pos, formtype, lemma)
                if item in existing_forms:
                    raise ValueError(f"duplicate formtypes {item} already in {existing_forms}")

                existing_forms[(pos, formtype, lemma)] = sense

        return existing_forms

    def lang_is_empty(self, lang):
        # check no other sections
        return not lang.problems and not any(lang.ifilter_wordsenses())

    def ety_is_empty(self, ety):
        # check no other sections
        return not ety.problems and not any(ety.ifilter_wordsenses())

    def pos_is_empty(self, pos):
        # check no other sections
        return not pos.problems and not any(pos.ifilter_wordsenses())

    def word_is_empty(self, word):
        return not word.problems and not any(word.ifilter_wordsenses())

    def remove_forms(self, title, wikt, unexpected_forms, ignore_errors):
        """ Removes the given list of forms from the entry, possibly leaving empty sections """

        existing_forms = self.get_existing_forms(wikt)

        print("removing unexpected", unexpected_forms)

        for uf in unexpected_forms:

            # Only remove forms from words that have good support
            if uf[0] == "v" or uf[0] not in pos_to_inflection:
                continue

            wordsense = existing_forms[uf]

            gloss = wiki_to_text(str(wordsense.gloss), title).lstrip("# ")
            if " of " not in gloss:
                continue

            formtype, lemma, nonform = Sense.parse_form_of(gloss)
            if nonform and not ignore_errors:
                raise ValueError(f"sense to be removed has data: {nonform}")
            if re.search(r"\n\s*\S", str(wordsense), re.S) and not ignore_errors:
                raise ValueError(f"sense to be removed has data: {wordsense}")
            if wordsense.problems and not ignore_errors:
                raise ValueError(f"sense to be removed was not parsed cleanly: {wordsense.problems}")

            word = wordsense._parent
            word.remove_child(wordsense)
            print("removing sense", wordsense)

            if not self.word_is_empty(word):
                continue

            pos = word._parent
            pos.remove_child(word)
            print("removing word", word)

            if not self.pos_is_empty(pos):
                continue

            parent = pos._parent
            parent.remove_child(pos)
            print("removing pos", pos)

            if parent.name.startswith("Etymology"):
                ety = parent
                if not self.ety_is_empty(ety):
                    continue

                lang = ety._parent
                lang.remove_child(ety)
                print("removing ety", ety)

                etys = lang.filter_etymology_sections()
                for i, ety in enumerate(etys, 1):
                    if len(etys) > 1:
                        ety._name = f"Etymology {i}"
                    else:
                        ety._name = "Etymology"
                        ety.raise_subsections()

            else:
                lang = parent

            if self.lang_is_empty(lang):
                lang._parent.remove_child(lang)
                print("removing lang")


    def _add_sense(self, word_target, form):

        senses = word_target.filter_wordsenses()
        target = senses[-1]

        pre_text = "" if str(target).endswith("\n") else "\n"
        gloss = pre_text + self.get_form_gloss(form) + "\n"

        sense = WordSense(gloss, parent=word_target, name=str(len(senses)+1))

        target._parent.insert_after(target, sense)

    @staticmethod
    def get_singular_genders(gender_list):
        return sorted(set(g.rstrip(" -pl") for g in gender_list))

    formtype_to_genders = {
        "mpl": ["m"],
        "fpl": ["f"],
        "f": ["f"],
        "m": ["m"],
    }

    def match_word_target(self, missing_form, word_targets):
        """ Attempts to find a compatable word target to handle a new 'form of' sense,
        This is really only used when replacing a bad form with a new form """

        pos, formtype, lemma, lemma_genders = missing_form

        # If the gender isn't part of the formtype, use the lemma's gender(s)
        if formtype == "pl":
            match_genders = sorted(set(lemma_genders))
        else:
            match_genders = self.formtype_to_genders[formtype]

        matches = []
        for word in word_targets:
            if not word.genders or self.get_singular_genders(word.genders) == match_genders \
                    or (match_genders == ["f"] and self.get_singular_genders == ["mf"]):
                matches.append(word)

        if len(matches) > 1:
            raise ValueError("Multiple word matches")

        if not len(matches):
            return None

        return matches[0]

    def _add_forms(self, title, wikt, missing_forms, skip_errors=False):
        if not missing_forms:
            return wikt

        changes = []
        missing = collections.defaultdict(list)
        for missing_form in sorted(missing_forms):
            pos, formtype, lemma, lemma_genders = missing_form

            # don't add masculine forms of female lemmas
            if formtype in ["m", "mpl"] and lemma_genders == ["f"]:
                continue
            missing[pos].append(missing_form)

        added_forms = set()

        for pos, forms in missing.items():

            # Word targets must match the POS and contain a "form of" link in their definitions
            word_targets = [x for x in wikt.filter_words(matches=lambda x: x.shortpos == pos) if self.get_existing_forms(x)]

            if word_targets:

                for missing_form in forms:
                    word_target = self.match_word_target(missing_form, word_targets)
                    if not word_target:
                        # TODO: Add new word to POS
                        if skip_errors:
                            continue
                        else:
                            raise ValueError(f"has POS, but no matching words: {missing_form}")

                    pos, formtype, lemma, lemma_genders = missing_form
                    if (pos, formtype, lemma) in added_forms:
                        continue

                    print("Inserting new sense", pos, formtype, lemma)
                    self._add_sense(word_target, missing_form)
                    added_forms.add((pos, formtype, lemma))

            # insert new POS
            else:

                print("Searching for title:", POS_TO_TITLE[pos])

                if any(wikt.ifilter_pos(matches=lambda x: x.name.strip().startswith(POS_TO_TITLE[pos]))):
                    if skip_errors:
                        continue
                    else:
                        raise ValueError(title, "has POS section, but no words")

                if len(list(wikt.filter_etymology_sections())) > 1:
                    if skip_errors:
                        continue
                    else:
                        raise ValueError(title, "multiple etymologies")


                preceeding_pos_targets = wikt.filter_pos(matches=lambda x: x.name.strip() < POS_TO_TITLE[pos])
                following_pos_targets = wikt.filter_pos(matches=lambda x: x.name.strip() > POS_TO_TITLE[pos])
                if preceeding_pos_targets:
                    target = preceeding_pos_targets[-1]
                    # Inserting between two entries
                    if len(following_pos_targets):
                        entry_text = "\n".join(self.full_pos(title, target._level, forms))
                        data = entry_text + "\n\n"

                    # Appending to a single entry
                    else:
                        entry_text = "\n".join(self.full_pos(title, target._level, forms))
                        data = "\n\n" + entry_text

                    changes.append(["after", target, data])
                else:
                    target = next(wikt.ifilter_pos())
                    entry_text = "\n".join(self.full_pos(title, target._level, forms))
                    data = entry_text + "\n\n"
                    changes.append(["before", target, data])


        for position, target, data in changes:
            if position == "after":
                wikt.insert_after(target, data)
                if not target:
                    raise ValueError(title, f"No POS targets")

            elif position == "before":
                wikt.insert_before(target, data)


    @classmethod
    def get_language_entry(cls, title, wikt, language):

        entries = wikt.filter_languages(matches=lambda x: x.name == language)
        if not entries:
            print(f"No {language} entries found")
            return

        if len(entries) > 1:
            raise ValueError(title, f"multiple '{language}' language entries")
            return text

        entry = entries[0]

        return entry

    def add_missing_forms(self, title, text, declared_forms, skip_errors=False):

        wikt = wtparser.parse_page(text, title=title, parent=None, skip_style_tags=True)

        entry = self.get_language_entry(title, wikt, "Spanish")
        if not entry:
            self.add_language_entry(wikt, self.generate_full_entry(title, declared_forms), "Spanish")
            return str(wikt)

        missing_forms, unexpected_forms = self.compare_forms(declared_forms, self.get_existing_forms(entry).keys())

        if missing_forms:
            self._add_forms(title, entry, missing_forms, skip_errors)

        return str(wikt)

    def remove_undeclared_forms(self, title, text, declared_forms, ignore_errors=False):

        wikt = wtparser.parse_page(text, title=title, parent=None, skip_style_tags=True)

        entry = self.get_language_entry(title, wikt, "Spanish")
        if not entry:
            return text

        missing_forms, unexpected_forms = self.compare_forms(declared_forms, self.get_existing_forms(entry).keys())

        if unexpected_forms:
            self.remove_forms(title, entry, unexpected_forms, ignore_errors)

        return str(wikt)


class FixRunner():

    """ Harness for running FormFixer from the fun_replace.py script """

    def __init__(self, lang_id, wordlist, allforms):
        self.language = lang_ids[lang_id]
        self._fixer = None
        self._wordlist = None
        self._allforms = None
        self._regex_pattern = None

        # If a filename is specified, save it for lazy-loading
        if isinstance(wordlist, str):
            self.wordlist_file = wordlist
        else:
            self._wordlist = wordlist

        if isinstance(allforms, str):
            self.allforms_file = allforms
        else:
            self._allforms = allforms

    @property
    def wordlist(self):
        if not self._wordlist:
            self._wordlist = Wordlist.from_file(self.wordlist_file)
        return self._wordlist

    @property
    def allforms(self):
        if not self._allforms:
            self._allforms = AllForms.from_file(self.allforms_file)
        return self._allforms

    @property
    def fixer(self):
        if not self._fixer:
            self._fixer = FormFixer(self.wordlist)
        return self._fixer

    def get_full_entry(self, page_text):
        m = re.search(self.entry_regex_pattern, page_text)
        if not m:
            return None

        return m.group('full')

    def get_lean_entry(self, page_text):

        m = re.search(self.entry_regex_pattern, page_text)
        if not m:
            return None, None

        body, tail = self.split_body_and_tail(m)
        return body, tail

    @property
    def entry_regex_pattern(self):
        if not self._regex_pattern:
            TARGET_LANG = self.language
            start = rf"(^|\n)=={TARGET_LANG}=="
            re_endings = [ r"\n==[^=]+==", r"\n----", "$" ]
            endings = "|".join(re_endings)
            pattern = fr"(?s)(?P<full>(?P<body>{start}.*?)(?P<end>{endings}))"
            self._regex_pattern = re.compile(pattern)

        return self._regex_pattern

    @staticmethod
    def split_body_and_tail(match):
        body = match.group('body')
        tail = match.group('end')

        templates = [ "c", "C", "cat", "top", "topic", "topics", "categorize", "catlangname", "catlangcode", "cln", "DEFAULTSORT" ]
        re_templates = r"\{\{\s*(" + "|".join(templates) + r")\s*[|}][^{}]*\}*"
        re_categories = r"\[\[\s*Category\s*:[^\]]*\]\]"

        pattern = fr"(?s)(.*?\n)((\s*({re_templates}|{re_categories})\s*)*)$"
        m = re.match(pattern, body)

        if not m:
            return body, tail

        return m.group(1), m.group(2) + tail


    def _remove_entry(self, title, page_text, can_blank=False):

        # Verify at least one entry exists, to avoid leaving junk entries with just headers like
        # {{also|1-A|1-a|1.a|1:a|1a}}

        new_text = re.sub(self.entry_regex_pattern, "", page_text)
        if "\n==" in new_text:
            log_message = f"{title}: entry will be removed"
            res = re.sub("\n+----\n+$", "", new_text)
        else:
            log_message = f"{title}: page needs to be deleted"
            res = "" if can_blank else page_text

        if not can_blank:
            print(log_message)
            with open("to_remove.log", "a") as outfile:
                outfile.write(log_message)
                outfile.write("\n")

        return res

    @staticmethod
    def can_handle_page(title):

        if title is None:
            raise ValueError("This must be run through fun_replace.py, not replace.py")

        if ":" in title:
            return False

        # TODO: until proper noun support, ignore capitals and letters
        if title[0] in "-1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            return False

        if title in ["antiinflamatoria", "antiinflamatorias", "aparecidos", "gama" ]:
            return False

        return True

    def _add_forms(self, page_text, title, skip_errors=False):

        declared_forms = self.fixer.get_declared_forms(title, self.wordlist, self.allforms)
        print("declared forms", declared_forms)
        supported_forms = [f for f in declared_forms if f[0] != "v" and f[0] in pos_to_inflection]
        if not supported_forms:
            print("no supported forms")
            return page_text

        lean_text, lean_tail = self.get_lean_entry(page_text)

        try:
            if lean_text:
                new_text = self.fixer.add_missing_forms(title, lean_text, supported_forms, skip_errors)
                if new_text == lean_text:
                    return page_text
                return self.alter_page(title, lean_text, lean_tail, new_text, page_text)
            else:
                return self.fixer.add_missing_forms(title, page_text, supported_forms, skip_errors)

#        try:
#            pass
        except BaseException as e:
            print("ERROR:", e)
            with open("error.log", "a") as outfile:
                print(f"{title} failed during add forms {e}")
                outfile.write(f"{title}: failed during add forms {e}\n")
            return page_text


    def _remove_forms(self, page_text, title, allow_blank=False, ignore_errors=False):

        declared_forms = self.fixer.get_declared_forms(title, self.wordlist, self.allforms)
        lean_text, lean_tail = self.get_lean_entry(page_text)

        # IF there's no spanish entry, there's nothing to remove
        if not lean_text:
            return page_text

        try:
            new_text = self.fixer.remove_undeclared_forms(title, page_text, declared_forms, ignore_errors)
        except BaseException as e:
            print("ERROR:", e)
            with open("error.log", "a") as outfile:
                outfile.write(f"{title}: failed during form removal {e}\n")
            return page_text

        # If there are no sections in the remaining text, remove the entry
        if "\n==" not in new_text:
            print("XX removing entry")
            return self._remove_entry(title, page_text, allow_blank)

        return new_text


    def alter_page(self, title, lean_text, lean_tail, new_text, page_text):

        # Fix for corner case, L3 adj followed by L4 verb isn't cleanly parsed and adding a following Noun goes awry
        if re.search(r"[^=\n]+===*[^\n=]*===", new_text):
            with open("error.log", "a") as outfile:
                print(f"{title} failed during add forms, matched === header not at the start of a line")
                outfile.write(f"{title}: failed during add forms, matched === header not at the start of a line\n")
                print(new_text)
            return page_text

        # Fix for pages with trailing ----
        new_text = re.sub("\n+----\n+----\n+", "\n\n----\n\n", new_text)

        # Condense any double newlines
        new_text = re.sub(r"\n\n\n*", r"\n\n", new_text)

        # Fix for trailing categories without empty newline
        if lean_tail and not lean_tail.startswith("\n"):
            new_text += "\n"

        return page_text.replace(lean_text, new_text)


    def add_forms(self, match, title, replacement=None):
        page_text = match.group(0)
        if not self.can_handle_page(title):
            return page_text

        # IF there's no spanish entry, pass the full page text so the language can be inserted in the right place
        if "#REDIRECT" in page_text:
            page_text = re.sub("^#REDIRECT.*$", "", page_text)
            if not re.match(r"\s*$", page_text, re.S):
                raise ValueError("{title}: has a redirect with extra text")

        if replacement:
            replacement._edit_summary = "Spanish: Added forms"
        return self._add_forms(page_text, title, skip_errors=True)

    def remove_forms(self, match, title, replacement=None):

        page_text = match.group(0)
        if not self.can_handle_page(title):
            return page_text

        if replacement:
             replacement._edit_summary = "Spanish: Removed forms"
        return self._remove_forms(page_text, title)

    def replace_forms(self, match, title, replacement=None):

        # TODO: limit only to matching pos pairs so it can be run automatically

        page_text = match.group(0)
        if not self.can_handle_page(title):
            return page_text

        new_text = self._remove_forms(page_text, title, allow_blank=True, ignore_errors=True)
        new_text = self._add_forms(new_text, title, skip_errors=True)

        if replacement:
            replacement._edit_summary = "Spanish: Replaced forms"
        return new_text

    def add_remove_forms(self, match, title, replacement=None):

        page_text = match.group(0)
        if not self.can_handle_page(title):
            return page_text

        new_text = self._add_forms(text, title)
        if new_text != text:
            changes = "Added forms"
        text = new_text
        new_text = self._remove_forms(text, title)
        if new_text != text:
            changes = "Removed forms"

        if replacement:
            replacement._edit_summary = "Spanish: " + "; ".join(changes)
        return new_text
