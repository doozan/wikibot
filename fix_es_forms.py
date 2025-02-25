import collections
import enwiktionary_sectionparser as sectionparser
import re
import sys
import enwiktionary_parser as wtparser
import enwiktionary_templates as templates

from enwiktionary_parser.wtnodes.wordsense import WordSense
from enwiktionary_wordlist.utils import wiki_to_text
from enwiktionary_wordlist.sense import Sense
from enwiktionary_wordlist.word import Word
from enwiktionary_wordlist.wordlist import Wordlist
from enwiktionary_wordlist.all_forms import AllForms
from enwiktionary_templates import ALL_LANGS, ALL_LANG_IDS

# Some pos entries have multiple titles, pick favorites
POS_TO_TITLE = {v: k for k, v in sectionparser.ALL_POS.items()}
POS_TO_TITLE.update({
    "adj": "Adjective",
    "adv": "Adverb",
    "det": "Determiner",
    "n": "Noun",
    "part": "Participle",
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
    "part": "part",
    "postp": "postp",
    "prep": "prep",
    "pron": "pron",
    "prop": "proper",
    "v": "v",
}

DeclaredForm = collections.namedtuple("DeclaredForm", [ "form", "pos", "formtype", "lemma", "lemma_genders" ])
ExistingForm = collections.namedtuple("ExistingForm", [ "form", "pos", "formtype", "lemma" ])

_unstresstab = str.maketrans("áéíóú", "aeiou")
def unstress(text):
    return text.translate(_unstresstab)

class FormFixer():

    def __init__(self, wordlist):
        self.wordlist = wordlist
        self._conj_cache = {}

    @staticmethod
    def can_handle(item):
        return item.pos in pos_to_inflection

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

    @staticmethod
    def is_reflexive(verb):
        return bool(re.search(r"[aeií]rse\b", verb) and not re.search(r"[aeií]r\b", verb))

    @staticmethod
    def strip_reflexive_clitic(verb):
        return re.sub(r"([aeií]r)se\b", r"\1", verb)

    @classmethod
    def remove_dup_refl_verbs(cls, poslemmas, form, wordlist):

        res = []
        for poslemma in poslemmas:
            pos, lemma = poslemma.split("|")
            if pos in ["v"] and cls.is_reflexive(lemma):
                # If the non-reflexive lemma also exists in poslemmas,
                # skip this reflexive poslemma
                alt_lemma = cls.strip_reflexive_clitic(lemma)
                alt_poslemma = "|".join([pos, alt_lemma])
                if alt_poslemma in poslemmas:
                    continue
            res.append(poslemma)
        return res

    @staticmethod
    def get_declared_poslemmas(form, wordlist, allforms):
        res = []

        # Verify that each form is actually declared by the lemma
        for poslemma in allforms.get_lemmas(form):
            pos, lemma = poslemma.split("|")

            words = wordlist.get_words(lemma, pos)
            if any(w.has_form(form) for w in words):
                res.append(poslemma)

        return res

    @classmethod
    def get_declared_forms(cls, form, wordlist, allforms):
        """ Returns a list of Forms for each lemma that declares the given form """

        poslemmas = cls.get_declared_poslemmas(form, wordlist, allforms)
        poslemmas = cls.remove_dup_refl_verbs(poslemmas, form, wordlist)

        declared_forms = []

        for poslemma in poslemmas:
            pos, lemma = poslemma.split("|")

            if lemma == form:
                continue

            all_words =  wordlist.get_words(lemma, pos)
            for word in all_words:

                genders = cls.get_word_genders(word)
                for formtype in word.get_formtypes(form):

                    form_pos = pos
                    form_lemma = lemma

                    if pos == "v" and formtype in ["pp_ms", "pp_mp", "pp_fs", "pp_fp"]:
                        form_pos = "part"

                        if formtype != "pp_ms":
                            idx = word.forms[formtype].index(form)
                            form_lemma = word.forms["pp_ms"][idx]

                    if not cls.can_handle_formtype(formtype):
                        continue

                    if form_pos == "v":
                        formtype = "smart_inflection"

                    # convert feminine plural of masculine noun to plural of feminine
                    if form_pos == "n" and formtype == "fpl":
                        new_lemma = cls.fpl_to_f(form, word)

                        if new_lemma:
                            form_lemma = new_lemma
                            genders = ["f"]
                            formtype = "pl"

                    # convert "pl" to "mpl" for words that have separate masculine/feminine forms
                    elif form_pos not in ["n", "prop"] and formtype == "pl" and "fpl" in word.forms:
                        formtype = "mpl"

                    item = DeclaredForm(form, form_pos, formtype, form_lemma, genders)
                    if item not in declared_forms:
                        declared_forms.append(item)

        return declared_forms


    formtype_to_genderplural = {
        "m": ("m", "s"),
        "mpl": ("m", "p"),
        "f": ("f", "s"),
        "fpl": ("f", "p"),
        "pl": ("", "p"),
    }

    @classmethod
    def can_handle_formtype(cls, formtype):
        if not formtype:
            return False

        if formtype in cls.formtype_to_genderplural:
            return True

        if formtype == "smart_inflection":
            return True

        # Existing forms than can be replaced with smart_inflection
        if formtype in ["gerund", "reflexive"]:
            return True

#        if formtype in ["pp_ms", "pp_mp", "pp_fs", "pp_fp"]:
#            return True

        if "_" in formtype:
            return True

    @classmethod
    def get_gender_plural(cls, formtype):

        """
        Returns (gender, quantity, and needs_gender), where gender is "m" or "f", number is "s"(ingular) or "p"(lural)
        """

        res = cls.formtype_to_genderplural.get(formtype)
        if not res:
            return "", ""
            #raise ValueError(form, f"Unexpected genderplural {pos}: {formtype}")
        return res


    @classmethod
    def get_gender_param(cls, form_obj):
#        pos, formtype, lemma, lemma_genders = form_obj
        gender, plural = cls.get_gender_plural(form_obj.formtype)

        if form_obj.pos == "v":
            return ""

        gender = ""
        if form_obj.lemma_genders == ["m", "f"]:
            if plural:
                return "g=m-p|g2=f-p"
            raise ValueError("xx", f"It seems like {form_obj.lemma} can only take a plural, but {form_obj.formtype} is not plural")

        elif form_obj.lemma_genders == ["m"]:
            if form_obj.pos == "adj" and form_obj.formtype in ["fpl", "f"]:
                gender = "f"
            else:
                gender = "m"
        elif form_obj.lemma_genders == ["f"]:
            gender = "f"
        else:
            if form_obj.formtype in ["m", "mpl"]:
                return "g=m"
            if form_obj.formtype in ["f", "fpl"]:
                return "g=f"
            if form_obj.lemma_genders == []:
                return None
            raise ValueError("Unexpected genders", form_obj)

        res = f"g={gender}"
        if plural == "p":
            res+= "-p"

        return res

    @staticmethod
    def get_es_noun_plurals(lemma, pos):
        res = []

        forms = wiki_to_text("{{es-noun}}", lemma)
        for kv in forms.split("; "):
            k, v = kv.split("=")
            if k == "pl":
                res.append(v)

        return res

    def get_fem_irregular_plural(self, form_obj):
        # emperador -> emperadora, emperatriz
        # {{es-noun|m|f=emperatriz|f2=+}}

        words = [w for w in self.wordlist.get_words(form_obj.lemma, form_obj.pos) if form_obj.formtype in w.forms and form_obj.form in w.forms[form_obj.formtype]]
        if not words:
            raise ValueError("no words", form_obj)
        word = words[0]
        if len(words) > 1 and any(w for w in words[1:] if set(w.forms) - set(word.forms)):
            w = next(w for w in words[1:] if w.forms != word.forms)
            raise ValueError(form_obj.form, f"Ambiguous forms: {w.forms} != {word.forms}, cannot insert")

        plurals = word.forms.get("fpl")

        if not plurals:
            return "-"

        if len(plurals) > 1:
            idx = word.forms.get("f").index(form_obj.form)
            plurals = [ plurals[idx] ]

        if self.get_es_noun_plurals(form_obj.form, form_obj.pos) != plurals:
            return plurals[0]

    def get_part_head(self, form_obj):

        if form_obj.formtype == "pp_ms":
#            if not form_obj.form.endswith("o"):
#                raise ValueError("Unexpected singular past participle", form_obj.form, form_obj.formtype, form_obj)

            conj_params = self.get_verb_conj_params(form_obj)
            impersonal = "|inv=1" if "only3s" in conj_params else ""
            return "{{es-past participle" + impersonal + "}}"

        elif form_obj.formtype in [ "pp_mp", "pp_fs", "pp_fp" ]:
            g = form_obj.formtype[-2] + "-" + form_obj.formtype[-1]
            return "{{head|es|past participle form|g=" + g + "}}"

        raise ValueError("Unexpected part formtype", form_obj.formtype, form_obj)

    def get_noun_head(self, form_obj):
        gender, plural = self.get_gender_plural(form_obj.formtype)

        if gender == "m" and plural == "s":
            raise ValueError("Singular masculine noun should probably be a lemma")

        # Feminine singular is a lemma
        if gender == "f" and plural == "s":
            irregular_plural = self.get_fem_irregular_plural(form_obj)
            if irregular_plural:
                return "{{es-noun|f|" + irregular_plural + "}}"
            return "{{es-noun|f}}"

        gender_param = self.get_gender_param(form_obj)
        if gender_param:
            return "{{head|es|noun form|" + gender_param + "}}"
        else:
            raise ValueError("Noun form needs a gender", form_obj)

    def get_form_head(self, form_obj):
        if form_obj.pos == "n":
            return self.get_noun_head(form_obj)

        if form_obj.pos == "part":
            return self.get_part_head(form_obj)

        return self.get_generic_head(form_obj)

    def get_generic_head(self, form_obj):

        # TODO: verify this is good
        pos = form_obj.pos
        form_name = POS_TO_TITLE[pos].lower()
        gender_param = self.get_gender_param(form_obj)
        if gender_param:
            return "{{head|es|" + form_name + " form|" + gender_param + "}}"
        return "{{head|es|" + form_name + " form}}"


    def get_adj_gloss(self, form_obj):
        gender, plural = self.get_gender_plural(form_obj.formtype)

        genderplural = "|".join(x for x in [gender, plural] if x)
        return "# {{adj form of|es|" + form_obj.lemma + "||" + genderplural + "}}"


    def get_verb_conj_params(self, form_obj):

        meta = self._conj_cache.get(form_obj.lemma)
        if meta is not None:
            return meta

        words = self.wordlist.get_words(form_obj.lemma, "v")

        # It's possible the same word has multiple conjections (acostar)

        can_cache = True
        if len(words) > 1:
            can_cache = False

        words = [w for w in words for formtype, forms in w.forms.items() if form_obj.form in forms]
        if not words:
            raise ValueError("No word matches entry for", form_obj)

        all_meta = []
        for word in words:
            for meta in re.findall(r"{{es-(?:verb|conj)[|]?[^<]*([^|}]*)", word.meta):
                if (meta == "" or "<" in meta) and meta not in all_meta:
                    all_meta.append(meta)

        if not all_meta:
            raise ValueError("no meta", form_obj, words, [w.meta for w in words])

        if len(all_meta) > 1:
            can_cache = False

        # Use the first possible matching meta that can generate the given form
        meta = all_meta[0]

#        meta = re.sub(r".*{{es-conj[|]?([^}]*)}}.*", r"\1", words[0].meta)
#        if "<" not in meta:
#            meta = ""
#        if "|" in meta or "{" in meta or "=" in meta:
#            raise ValueError("bad meta", form_obj, [words[0].meta, meta])

        if can_cache:
            self._conj_cache[form_obj.lemma] = meta

        return meta

    def get_verb_gloss(self, form_obj):
        conj_params = self.get_verb_conj_params(form_obj)
        if not conj_params:
            conj_params = ""
        return "# {{es-verb form of|" + form_obj.lemma + conj_params + "}}"

    def get_part_gloss(self, form_obj):
        if form_obj.formtype == "pp_ms":
            return "# {{past participle of|es|" + form_obj.lemma + "}}"
        else:
            #part_lemma = self.get_part_lemma(form_obj)
            if form_obj.formtype == "pp_mp":
                return "# {{masculine plural of|es|" + form_obj.lemma + "}}"
            if form_obj.formtype == "pp_fs":
                return "# {{feminine singular of|es|" + form_obj.lemma + "}}"
            elif form_obj.formtype == "pp_fp":
                return "# {{feminine plural of|es|" + form_obj.lemma + "}}"
            else:
                raise ValueError("unexpected participle type", form_obj.formtype, form_obj)

    def get_noun_gloss(self, form_obj):
        gender, plural = self.get_gender_plural(form_obj.formtype)

        if gender == "f" and plural == "s":
            return "# {{female equivalent of|es|" + form_obj.lemma + "}}"

        return "# {{noun form of|es|" + form_obj.lemma + "||" + plural + "}}"

    def get_generic_gloss(self, form_obj):
        gender, plural = self.get_gender_plural(form_obj.formtype)

        genderplural = "|".join(x for x in [gender, plural] if x)
        return "# {{inflection of|es|" + form_obj.lemma + "||" + genderplural + "|p=" + pos_to_inflection[form_obj.pos] + "}}"

    def get_form_gloss(self, form_obj):
        pos = form_obj.pos
        if pos == "adj":
            return self.get_adj_gloss(form_obj)
        elif pos == "n":
            return self.get_noun_gloss(form_obj)
        elif pos == "v":
            return self.get_verb_gloss(form_obj)
        elif pos == "part":
            return self.get_part_gloss(form_obj)
        elif self.can_handle(form_obj):
            return self.get_generic_gloss(form_obj)

        raise ValueError("unsupported pos", pos)

    def full_pos(self, level, forms):
        if not forms:
            raise ValueError(title, "no forms")

        pos = forms[0].pos
        if any(f for f in forms if f.pos != pos):
            raise ValueError(f"expected one type of pos, but got multiples: {f.pos} != {pos}", f)

        title = POS_TO_TITLE[pos]

        # TODO: Verify all forms share a lemma ?

        lines = [self.get_form_head(forms[0])]
        lines.append("")

        added_forms = set()
        for form_obj in forms:
            item = ExistingForm(form_obj.form, form_obj.pos, form_obj.formtype, form_obj.lemma)
            if item in added_forms:
                continue
            lines.append(self.get_form_gloss(form_obj))
            added_forms.add(item)

        section = sectionparser.Section(None, level, title)
        section.content_wikilines = lines
        return section

    def generate_full_entry(self, title, forms):

        spanish = sectionparser.Section(None, 2, "Spanish")

        prev_pos = None
        pos_forms = []
        for form in sorted(forms):
            if form.pos != prev_pos:
                if prev_pos:
                    child = self.full_pos(3, pos_forms)
                    child.parent = spanish
                    spanish._children.append(child)
                pos_forms = []
            pos_forms.append(form)
            prev_pos = form.pos
        if pos_forms:
            child = self.full_pos(3, pos_forms)
            child.parent = spanish
            spanish._children.append(child)

        return str(spanish).rstrip()


    @staticmethod
    def compare_forms(declared_forms, existing_forms):

        missing_forms = []
        unexpected_forms = set(existing_forms)

        for x in declared_forms:

            item = ExistingForm(x.form, x.pos, x.formtype, x.lemma)

            # Consider mpl and pl to be the same
            alt_item = None
            if x.formtype in ["pl", "mpl"]:
                alt = "pl" if x.formtype == "mpl" else "mpl"
                alt_item = item._replace(formtype=alt)

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
                wikt.insert_after(preceeding_targets[-1],  entry + "\n\n")

            # Appending to a single entry
            else:
                wikt.insert_after(preceeding_targets[-1],  "\n\n" + entry )

        elif following_targets:
            target = following_targets[0]
            wikt.insert_before(target, entry + "\n\n")
        else:
            wikt.add_text(entry)


    @staticmethod
    def get_forms_from_headword(word):
        for template in templates.iter_templates(word.headword):
            if template.name == "head":
                data = self.get_head_forms(template)
            else:
                data = templates.expand_template(template, self.word)
            self.add_forms(self.parse_list(data))


    @staticmethod
    def parse_list(line):
        items = {}
        for match in re.finditer(r"\s*(.*?)=(.*?)(; |$)", line):
            k = match.group(1)
            v = match.group(2)
            if k not in items:
                items[k] = [v]
            else:
                items[k].append(v)

        return items

    #@classmethod
    #def get_existing_forms(cls, title, wikt):
    def get_existing_forms(self, title, wikt):
        existing_forms = {}

        # if feminine noun with masculine, add form of masculine
        for word in wikt.filter_words():

            #for formtype, forms in word.forms.items():
            if "f" in word.genders: # or "m" in word.genders:
                gender = "f" # if "f" in word.genders else "m"
                mate =  "m" #if gender == "f" else "f"

                wlword = Word(self.wordlist, title, [("meta", word.headword), ("pos", word.shortpos)])
                if mate in wlword.forms:
                    for mate_lemma in wlword.forms[mate]:
                        item = ExistingForm(title, word.shortpos, gender, mate_lemma)
                        existing_forms[item] = None

        for sense in wikt.filter_wordsenses():
            pos_title = re.sub("[ 1-9]+$", "", sense._parent._parent.name)
            pos = sectionparser.ALL_POS[pos_title]

            gloss = wiki_to_text(str(sense.gloss), "title").lstrip("# ")
            if " of " not in gloss:
                continue

            formtype, lemma, nonform = Sense.parse_form_of(gloss)

            # Limit to the formtypes we can handle, forms like "misspelling of" aren't our concern
            if self.can_handle_formtype(formtype):

                if pos == "part":
                    formtype = {"f": "pp_fs", "fpl": "pp_fp", "mpl": "pp_mp"}.get(formtype,formtype)

                lemma = lemma.strip()
                item = ExistingForm(title, pos, formtype, lemma)
                if item in existing_forms:
                    continue
                    #raise ValueError(f"duplicate formtypes {item} already in {existing_forms}")

                existing_forms[item] = sense

        return existing_forms

    def lang_is_empty(self, lang):
        return not lang.problems and not any(lang.ifilter_sections(
            matches=lambda x: x.name not in ["Pronunciation"]))

    def ety_is_empty(self, ety):
        # check no other sections
        return not ety.problems and not any(ety.ifilter_sections())

    def pos_is_empty(self, pos):
        # check no other sections
        if pos.problems:
            return False

        if any(pos.ifilter_wordsenses()):
            return False

        if any(pos.ifilter_sections()):
            return False

        return True

    def word_is_empty(self, word):
        return not word.problems and not any(word.ifilter_wordsenses())

    def remove_forms(self, title, wikt, unexpected_forms, ignore_errors, limit=None):
        """ Removes the given list of forms from the entry, possibly leaving empty sections """

        existing_forms = self.get_existing_forms(title, wikt)

        for uf in unexpected_forms:

            # Only remove forms from words that have good support
            if not self.can_handle(uf):
                continue

            wordsense = existing_forms[uf]

            # Don't remove matches
            if not wordsense:
                continue

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
            #print("removing sense", wordsense)

            if not self.word_is_empty(word):
                continue

            if limit == "sense":
                continue

            pos = word._parent
            pos.remove_child(word)
            #print("removing word", word)

            if not self.pos_is_empty(pos):
                continue

            if limit == "word":
                continue

            parent = pos._parent
            parent.remove_child(pos)
            #print("removing pos", pos)

            if limit == "pos":
                continue

            if parent.name.startswith("Etymology"):
                ety = parent
                if not self.ety_is_empty(ety):
                    continue

                lang = ety._parent
                lang.remove_child(ety)
                #print("removing ety", ety)

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
                #print("removing lang")


    def _add_sense(self, form, word_target, form_obj):

        senses = word_target.filter_wordsenses()
        target = senses[-1]

        pre_text = "" if str(target).endswith("\n") else "\n"
        gloss = pre_text + self.get_form_gloss(form_obj) + "\n"

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

        #pos, formtype, lemma, lemma_genders = missing_form

        # If the gender isn't part of the formtype, use the lemma's gender(s)
        if missing_form.pos in ["v", "part"]:
            if len(word_targets) > 1:
                raise ValueError("Multiple word matches", missing_form, word_targets)
            return word_targets[0]

        if missing_form.formtype == "pl":
            match_genders = sorted(set(missing_form.lemma_genders))
        else:
            match_genders = self.formtype_to_genders.get(missing_form.formtype)
            if not match_genders:
                return None

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
            return

        changes = []
        missing = collections.defaultdict(list)
        for missing_form in sorted(missing_forms, key=lambda x: (x.pos, x.lemma, x.formtype)):
            #pos, formtype, lemma, lemma_genders = missing_form

            # don't add masculine forms of female lemmas
            if missing_form.formtype in ["m", "mpl"] and missing_form.lemma_genders == ["f"]:
                continue
            missing[missing_form.pos].append(missing_form)

        added_forms = set()

        for pos, forms in missing.items():

            # Word targets must match the POS and contain a "form of" link in their definitions
            word_targets = [x for x in wikt.filter_words(matches=lambda x: x.shortpos == pos) if self.get_existing_forms(title, x)]

            if word_targets:

                for missing_form in forms:
                    word_target = self.match_word_target(missing_form, word_targets)
                    if not word_target:
                        # TODO: Add new word to POS
                        if skip_errors:
                            continue
                        else:
                            raise ValueError(f"has POS, but no matching words: {missing_form}")

                    #pos, formtype, lemma, lemma_genders = missing_form
                    item = ExistingForm(missing_form.form, missing_form.pos, missing_form.formtype, missing_form.lemma)
                    if item in added_forms:
                        continue

                    #print("Inserting new sense", pos, formtype, lemma)
                    self._add_sense(title, word_target, missing_form)
                    added_forms.add(item)

            # insert new POS
            else:

#                print("Searching for title:", POS_TO_TITLE[pos])

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

                    data = str(self.full_pos(target._level, forms)) + "\n"
                    changes.append(["after", target, data])
                else:
                    target = next(wikt.ifilter_pos(), None)
                    level = target._level if target else 3
                    data = str(self.full_pos(level, forms)) + "\n"
                    if not target:
                        changes.append(["after", wikt, data])
                    else:
                        changes.append(["before", target, data])


        for position, target, data in changes:
            if position == "after":
                if not target.endswith("\n\n"):
                    if target.endswith("\n"):
                        target.add_text("\n")
                    else:
                        target.add_text("\n\n")
                wikt.insert_after(target, data)

            elif position == "before":
                wikt.insert_before(target, data)


    @classmethod
    def get_language_entry(cls, title, wikt, language):

        entries = wikt.filter_languages(matches=lambda x: x.name == language)
        if not entries:
            #print(f"No {language} entries found")
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
        else:
            missing_forms, unexpected_forms = self.compare_forms(declared_forms, self.get_existing_forms(title, entry).keys())

            if not missing_forms:
                return text

            self._add_forms(title, entry, missing_forms, skip_errors)

        return str(wikt)

    def remove_undeclared_forms(self, title, text, declared_forms, ignore_errors=False):

        wikt = wtparser.parse_page(text, title=title, parent=None, skip_style_tags=True)

        entry = self.get_language_entry(title, wikt, "Spanish")
        if not entry:
            return text

        missing_forms, unexpected_forms = self.compare_forms(declared_forms, self.get_existing_forms(title, entry).keys())

        if unexpected_forms:
            print("removing", unexpected_forms)
            self.remove_forms(title, entry, unexpected_forms, ignore_errors)

        return str(wikt)

    @staticmethod
    def is_form_header(text):
        return bool(re.match(r"\s*{{(head|head-lite)\|es\|(past participle|[^|]* form[ |}])", text, re.MULTILINE)) \
                or "{{es-past participle" in text

    @classmethod
    def is_form(cls, section):
        wikiline = ""
        # Skip leading empty lines (shouldn't exist, but just to be safe)
        for wikiline in section.content_wikilines:
            if wikiline.strip():
                break
        return cls.is_form_header(wikiline)

    ALLOWED_FORMTYPES = {
            'f', 'pl', 'fpl', 'mpl', 'infinitive', 'reflexive', 'smart_inflection', 'form'
    }

    @classmethod
    def is_allowed_formtype(cls, formtype):
        if not formtype:
            return False
        if "_comb_" in formtype:
            return True
        if formtype in cls.ALLOWED_FORMTYPES:
            return True

        if cls.can_handle_formtype(formtype):
            return True

        print("unhandled formtype:", formtype)
        return False

    @classmethod
    def is_form_sense(cls, text, log=lambda *x: x):
        sense_text = wiki_to_text(text, "page")
        formtype, lemma, nonform = Sense.parse_form_of(sense_text)
        if not formtype:
            log("not_form_sense", sense_text)
            return False
        elif nonform:
            log("has_text_outside_form", nonform)
            return False

        return cls.is_allowed_formtype(formtype)

    @classmethod
    def is_generated(cls, section, log=lambda *x: x):
        if section._children:
            log("has_subsection")
            return False

        first_wikiline = True
        for wikiline in section.content_wikilines:

            # Remove generic labels
            wikiline = wikiline.replace("{{lb|es|uds.}}", "")
            wikiline = wikiline.replace("{{lb|es|Latin America|uds.}}", "")
            wikiline = wikiline.replace("{{lb|es|Latin America}}", "")
            # Remove formatting
            wikiline = wikiline.strip(" *#:")

            if not wikiline:
                continue

            # The first wikiline must be a form headline
            if first_wikiline:
                if not cls.is_form_header(wikiline):
                    log("not_form_header", wikiline)
                    return False
                first_wikiline = False
                continue

            # All other lines must be valid form declarations
            if not cls.is_form_sense(wikiline, log):
                return False

        return True


    def replace_pos(self, title, page_text, x_forms, target_pos, summary):
        """ Removes the pos section entirely and then re-creates it with the given forms
        fails if the existing pos has anything other than generic form or data """

        forms = [f for f in x_forms if f.pos == target_pos]

        if not forms:
            return page_text

        entry = sectionparser.parse(page_text, title)
        if not entry:
            return page_text

        languages = entry.filter_sections(matches=lambda x: x.title == "Spanish", recursive=False)
        if len(languages) != 1:
            return page_text

        spanish = languages[0]

        removeable = []
        sections = spanish.filter_sections(matches=lambda x: x.title == POS_TO_TITLE[target_pos])

        # If there are multiple target sections, don't make any changes
        if len(sections) != 1:
            print(title, target_pos, f"Can't replace, multiple matching sections")
            return page_text

        section = sections[0]
        if section not in removeable:
            if not self.is_generated(section):
                print(title, section.path, "Can't replace, has non-form data")
                return page_text
            removeable.append(section)

        if not removeable:
            return page_text

        changes = []
        section = removeable[0]
        new_section = self.full_pos(section.level, forms)
        section.content_wikilines = new_section.content_wikilines
        changes.append(f"/*{section.path}*/ regenerated section using new templates")

        for item in removeable[1:]:
            changes.append(f"/*{item.path}*/ removed")
            item.parent._children.remove(item)

        res = str(entry).rstrip()

        # if the only difference is "|g=m-p" and just return the normal page
        if re.sub(r" form\|g=([mfps-]*)}}", " form}}", res.rstrip()) == re.sub(r" form\|g=([mfps-]*)}}", " form}}", page_text.rstrip()):
            return page_text

        if summary is not None:
            summary += changes
        return res

class FixRunner():

    """ Harness for running FormFixer from the fun_replace.py script """

    def __init__(self, lang_id, wordlist, allforms, **kwargs):
        self.language = ALL_LANG_IDS[lang_id]
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

        # TODO: until better verb support, ignore pages with spaces
        if " " in title:
            return False

        return True

    def _add_forms(self, page_text, title, skip_errors=False):

        declared_forms = self.fixer.get_declared_forms(title, self.wordlist, self.allforms)
        supported_forms = [f for f in declared_forms if self.fixer.can_handle(f)]
        if not supported_forms:
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
            raise e
            with open("error.log", "a") as outfile:
                print(f"{title} failed during add forms {e}")
                outfile.write(f"{title}: failed during add forms {e}\n")
            return page_text



    def _remove_forms(self, page_text, title, allow_blank=False, ignore_errors=False):

        declared_forms = self.fixer.get_declared_forms(title, self.wordlist, self.allforms)

        try:
            new_text = self.fixer.remove_undeclared_forms(title, page_text, declared_forms, ignore_errors)
        except BaseException as e:
            print("ERROR:", e)
            #raise e
            with open("error.log", "a") as outfile:
                outfile.write(f"{title}: failed during form removal {e}\n")
            return page_text

        # If there are no sections in the remaining text, remove the entry
        if "\n==" not in new_text:
            return self._remove_entry(title, page_text, allow_blank)

        return new_text


    def alter_page(self, title, lean_text, lean_tail, new_text, page_text):

        # Fix for corner case, L3 adj followed by L4 verb isn't cleanly parsed and adding a following Noun goes awry
        res = re.search(r"(?<![=\n])===*[^\n=]+===", new_text)
        if res:
            with open("error.log", "a") as outfile:
                #raise e
                print(f"{title} failed during add forms, matched === header not at the start of a line")
                outfile.write(f"{title}: failed during add forms, matched === header not at the start of a line\n")
                #print(res)
                #print(new_text)
            return page_text

        # Fix for pages with trailing ----
        new_text = re.sub("\n+----\n+----\n+", "\n\n----\n\n", new_text)

        # Condense any double newlines
        new_text = re.sub(r"\n\n\n*", r"\n\n", new_text)

        # Fix for trailing categories without empty newline
        if lean_tail and not lean_tail.startswith("\n"):
            new_text += "\n"

        return page_text.replace(lean_text, new_text)


    def add_forms(self, page_text, title, summary=None):

        if not self.can_handle_page(title):
            return page_text

        # IF there's no spanish entry, pass the full page text so the language can be inserted in the right place
        if "#REDIRECT" in page_text:
            page_text = re.sub("^#REDIRECT.*$", "", page_text)
            if not re.match(r"\s*$", page_text, re.S):
                raise ValueError(f"{title}: has a redirect with extra text")

        if summary is not None:
            summary.append("/*Spanish*/ Added forms")

        try:
            return self._add_forms(page_text, title, skip_errors=True)
        except BaseException as e:
            print("ERROR:", e)
            raise e
            with open("error.log", "a") as outfile:
                print(f"{title} failed during add forms {e}")
                outfile.write(f"{title}: failed during add forms {e}\n")
            return page_text



    def remove_forms(self, page_text, title, summary=None):

        if not self.can_handle_page(title):
            return page_text

        if summary is not None:
             summary.append("/*Spanish*/ Removed forms")
        return self._remove_forms(page_text, title)

    def replace_pos(self, page_text, title, pos_list, summary=None):

        if not self.can_handle_page(title):
            return page_text

        replaced = set()
        new_text = page_text

        declared_forms = self.fixer.get_declared_forms(title, self.wordlist, self.allforms)

        for pos in pos_list:
            forms = [f for f in declared_forms if f.pos in pos]
            if not forms:
                continue
            text = self.fixer.replace_pos(title, new_text, forms, pos, summary)
            if text != new_text:
                new_text = text

        return new_text

    def add_remove_forms(self, page_text, title, summary=None):

        if not self.can_handle_page(title):
            return page_text

        new_text = self._add_forms(text, title)
        if new_text != text:
            changes = "Added forms"
        text = new_text
        new_text = self._remove_forms(text, title)
        if new_text != text:
            changes = "Removed forms"

        if summary is not None:
            summary.append("/*Spanish*/ " + "; ".join(changes))
        return new_text
