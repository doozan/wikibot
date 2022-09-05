import timeit

import collections
import re
import sys
import enwiktionary_parser as wtparser
import enwiktionary_templates as templates
from enwiktionary_parser.languages.all_ids import languages as lang_ids
from enwiktionary_parser.wtnodes.wordsense import WordSense
from enwiktionary_wordlist.utils import wiki_to_text
from enwiktionary_wordlist.sense import Sense
from enwiktionary_wordlist.word import Word
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

DeclaredForm = collections.namedtuple("Form", [ "form", "pos", "formtype", "lemma", "lemma_genders" ])
ExistingForm = collections.namedtuple("ExistingForm", [ "form", "pos", "formtype", "lemma" ])

smart_inflection_formtypes = {
    'cond_1p', 'cond_1s', 'cond_2p', 'cond_2pf', 'cond_2s', 'cond_2sf', 'cond_3p', 'cond_3s',
    'fut_1p', 'fut_1s', 'fut_2p', 'fut_2pf', 'fut_2s', 'fut_2sf', 'fut_3p', 'fut_3s',
    'fut_sub_1p', 'fut_sub_1s', 'fut_sub_2p', 'fut_sub_2pf', 'fut_sub_2s', 'fut_sub_2sf', 'fut_sub_3p', 'fut_sub_3s',
    'gerund', 'gerund_comb_se',
    'infinitive_comb_se',
    'imp_1p', 'imp_1s', 'imp_2p', 'imp_2pf', 'imp_2s', 'imp_2sf', 'imp_2sv',
    'imp_1p_comb_nos',
    'imp_2p_comb_lo', 'imp_2p_comb_la' 'imp_2p_comb_los', 'imp_2p_comb_les', 'imp_2p_comb_nos', 'imp_2p_comb_os',
    'imp_2pf_comb_lo', 'imp_2pf_comb_la' 'imp_2pf_comb_los', 'imp_2pf_comb_les', 'imp_2pf_comb_nos', 'imp_2pf_comb_os',
    'imp_2sf_comb_se',
    'imp_2pf_comb_se',
    'imp_3p_comb_se',
    'impf_1p', 'impf_1s', 'impf_2p', 'impf_2pf', 'impf_2s', 'impf_2sf', 'impf_3p', 'impf_3s',
    'impf_sub_ra_1p', 'impf_sub_ra_1s', 'impf_sub_ra_2p', 'impf_sub_ra_2pf', 'impf_sub_ra_2s', 'impf_sub_ra_2sf', 'impf_sub_ra_3p', 'impf_sub_ra_3s',
    'impf_sub_se_1p', 'impf_sub_se_1s', 'impf_sub_se_2p', 'impf_sub_se_2pf', 'impf_sub_se_2s', 'impf_sub_se_2sf', 'impf_sub_se_3p', 'impf_sub_se_3s',
    'neg_imp_1p', 'neg_imp_2p', 'neg_imp_2pf', 'neg_imp_2s', 'neg_imp_2sf',
    'pp_fp', 'pp_fs', 'pp_mp', 'pp_ms',
    'pres_1p', 'pres_1s', 'pres_2p', 'pres_2pf', 'pres_2s', 'pres_2sf', 'pres_2sv', 'pres_3p', 'pres_3s',
    'pres_sub_1p', 'pres_sub_1s', 'pres_sub_2p', 'pres_sub_2pf', 'pres_sub_2s', 'pres_sub_2sf', 'pres_sub_2sv', 'pres_sub_3p', 'pres_sub_3s',
    'pret_1p', 'pret_1s', 'pret_2p', 'pret_2pf', 'pret_2s', 'pret_2sf', 'pret_3p', 'pret_3s'
}

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



    @classmethod
    def get_declared_forms(cls, form, wordlist, allforms):
        """ Returns a list of Forms for each lemma that declares the given form """

        imp_to_comb = {
           "imp_2s" : "imp_2s_comb_te",
           "imp_2sf" : "imp_2sf_comb_se",
           "imp_2sv" : "imp_2sv_comb_te",

           "imp_1p" : "imp_1p_comb_nos",
           "imp_2p" : "imp_2p_comb_os",
           "imp_2pf" : "imp_2pf_comb_se",

           "gerund": "gerund_comb_se",
        }
        comb_to_imp = {v:k for k,v in imp_to_comb.items()}

        poslemmas = allforms.get_lemmas(form)

        se_verbs = set()
        non_se_verbs = set()
        for pos, lemma in [poslemma.split("|") for poslemma in poslemmas]:
            if pos not in ["v", "part"]:
                continue

            if lemma.endswith("rse") and \
                any(form in forms
                    for word in wordlist.get_words(lemma, "v")
                    for formtype, forms in word.forms.items()):
                    se_verbs.add(lemma[:-2])

            elif lemma[-2:] in ["ar", "er", "ir", "ír"] and \
                any(form in forms
                    for word in wordlist.get_words(lemma, "v")
                    for formtype, forms in word.forms.items()):
                    non_se_verbs.add(lemma)

        # Now that everything is cleaned up, this should be VERY rare
        # probably rare enough to flag it instead of using a workaround
        se_and_non_se_verbs = se_verbs & non_se_verbs
        if se_and_non_se_verbs:
            print("se_and_non_se", se_verbs, non_se_verbs, se_and_non_se_verbs)

        declared_forms = []
        for pos, lemma in [poslemma.split("|") for poslemma in poslemmas]:

            if lemma == form:
                continue

            # If pos is 'part', the lemma will be a verb, not a "part"
            all_words =  wordlist.get_words(lemma, "v") if pos == "part" else wordlist.get_words(lemma, pos)
            for word in all_words:
                if se_and_non_se_verbs and word.word.endswith("rse") and word.word[:-2] in se_and_non_se_verbs:
                    continue

                has_reflexive = word.word.endswith("rse") or any(s for s in word.senses if s.qualifier and re.search("(reflexive|pronominal)", s.qualifier))

                genders = cls.get_word_genders(word)
                for formtype, forms in word.forms.items():

                    # part will return all verb forms, limit to just the part forms
                    if pos == "part" and formtype not in ["pp_ms", "pp_mp", "pp_fs", "pp_fp"]:
                        continue

                    # Likewise, verb will still contain the part forms, but they should be ignored
                    if pos == "v" and formtype in ["pp_ms", "pp_mp", "pp_fs", "pp_fp"]:
                        continue

                    if form not in forms:
                        continue

                    if not cls.can_handle_formtype(formtype):
                        continue

                    if has_reflexive and formtype == "infinitive_comb_se":
                        formtype = "reflexive"

                    if pos == "v" \
                        and (formtype in smart_inflection_formtypes) \
                        or (word.word.endswith("rse") and formtype == 'gerund_comb_se'):
                           formtype = "smart_inflection"

                    # with condensed verbs, the neg_imp will be the same as the imp_ forms in the 3rds person
#                    # imp_2sf', 'abandonar', []), ('v', 'neg_imp_2sf',
                    if formtype in ["neg_imp_3s", "neg_imp_3p"]:
                        #print("skipping -rse", formtype)
                        continue

                    # and in 2nd person singular plural with non-reflexive verbs (ustedes no hablen, hablen ustedes)
                    if lemma in non_se_verbs and formtype in ["neg_imp_2sf", "neg_imp_1p", "neg_imp_2pf"]:
                        #print("skipping non-rse", formtype)
                        continue

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

                    item = DeclaredForm(form, pos, formtype, lemma, genders)
                    if item not in declared_forms:

                        # There's a conflict between imp_xxx and imp_xxx_comb on -se verb conjugations
                        # when a non -se verb include {{es-conj|xxxse}}, it will generate the same form for imp_2s
                        # that the -r verb generates for imp_2s_comb_te
                        #
                        # When there are both -se and -r verbs, prefer the imp_2s_comb_te entry, but when
                        # there is only a -se verb or only a -r verb, we want to prefer the imp_2s entry
                        if formtype in comb_to_imp or formtype in imp_to_comb:
                            if lemma in se_and_non_se_verbs:
                                remove_form = comb_to_imp.get(formtype)
                                prefer_form = imp_to_comb.get(formtype)
                            else:
                                remove_form = imp_to_comb.get(formtype)
                                prefer_form = comb_to_imp.get(formtype)

                            if remove_form:
                                remove_item = DeclaredForm(item.form, pos, remove_form, lemma, genders)
                                if remove_item in declared_forms:
                                    declared_forms.remove(remove_item)


                            elif prefer_form:
                                prefer_item = DeclaredForm(item.form, pos, prefer_form, lemma, genders)
                                if prefer_item in declared_forms:
                                    continue

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

        # inflections should be replaced with more specific templates
        if formtype == "inflection":
            return True

        # Generated by es-conj, but only used internally for wiki linking
        if formtype == "infinitive_linked":
            return False

        if formtype in {
#        "reflexive",
#        "infinitive",
#        "infinitive_comb_se",
        "gerund",
#        "pp_ms",
#        "pp_mp",
#        "pp_fs",
#        "pp_fp",
        }:
#            return False
            return True

        if formtype == "smart_inflection":
             return True

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
            raise ValueError("xx", f"It seems like {lemma} can only take a plural, but {formtype} is not plural")

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
        #pos, formtype, lemma, lemma_genders = form_obj
        if form_obj.formtype == "pp_ms":
            if not form_obj.form.endswith("o"):
                raise ValueError("Unexpected singular past participle")

            conj_params = self.get_verb_conj_params(form_obj)
            impersonal = "|inv=1" if "only3s" in conj_params else ""
            return "{{es-past participle" + impersonal + "}}"

        elif form_obj.formtype in [ "pp_mp", "pp_fs", "pp_fp" ]:
            g = form_obj.formtype[-2] + "-" + form_obj.formtype[-1]
            return "{{head|es|past participle form|g=" + g + "}}"

        return self.get_generic_head(form_obj)

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
            raise ValueError("Noun form needs a gender")

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


    slot_to_props = {
        'cond': {"mood": "conditional"},
        'fut': {"tense": "future", "mood": "indicative"},
        'fut_sub': {"tense": "future", "mood": "subjunctive"},
        'gerund': {"mood": "gerund"},
        'imp': {"mood": "imperative", "sense": "affirmative"},
        'impf': {"tense": "imperfect", "mood": "indicative"},
        'impf_sub_ra': {"tense": "imperfect", "mood": "subjunctive", "sera": "ra"},
        'impf_sub_se': {"tense": "imperfect", "mood": "subjunctive", "sera": "se"},
        'neg_imp': {"mood": "imperative", "sense": "negative"},
        'pp_fs': {"mood": "participle", "gender": "f", "number": "s"},
        'pp_fp': {"mood": "participle", "gender": "f", "number": "p"},
        'pp_ms': {"mood": "participle", "gender": "m", "number": "s"},
        'pp_mp': {"mood": "participle", "gender": "m", "number": "p"},
        'pres': {"tense": "present", "mood": "indicative"},
        'pres_sub': {"tense": "present", "mood": "subjunctive"},
        'pret': {"tense": "preterite", "mood": "indicative"},
    }

    person_props = {
    "1s": {"person": "1", "number": "s"},
    "2s": {"person": "2", "number": "s", "formal": "n"},
    "2sv": {"person": "2", "number": "s", "formal": "n", "voseo": "y", "region": "Latin America"},
    "2sf": {"person": "2", "number": "s", "formal": "y"},
    "3s": {"person": "3", "number": "s"},
    "1p": {"person": "1", "number": "p"},
    "2p": {"person": "2", "number": "p", "formal": "n", "region": "Spain"},
    "2pf": {"person": "2", "number": "p", "formal": "y"},
    "3p": {"person": "3", "number": "p"},
}

    param_order = {k:i for i,k in enumerate(["mood", "tense", "sense", "formal", "person", "gender", "number", "voseo", "sera", "participle", "region", "ending"])}

    def get_verb_gloss(self, form_obj):
        if form_obj.formtype == "infinitive":
            return "# {{inflection of|es|" + form_obj.lemma + "||inf}}"
        elif form_obj.formtype == "reflexive":
            return "# {{reflexive of|es|" + form_obj.lemma + "}}"
        elif "_comb_" in form_obj.formtype:
            return self.get_verb_compound_gloss(form_obj)
        else:
            return self.get_verb_form_gloss(form_obj)

    def get_verb_form_gloss(self, form_obj):
        if form_obj.formtype == "smart_inflection":
            return self.get_smart_verb_form_gloss(form_obj)
        return self.get_param_verb_form_gloss(form_obj)


    def get_verb_conj_params(self, form_obj):

        meta = self._conj_cache.get(form_obj.lemma)
        if meta is not None:
            return meta

        words = self.wordlist.get_words(form_obj.lemma, "v")

        # It's possible the same word has multiple conjections (acostar)

        can_cache = True
        if len(words) > 1:
            can_cache = False

        if form_obj.formtype == "smart_inflection":
            words = [w for w in words
                        for formtype, forms in w.forms.items()
                            if formtype in smart_inflection_formtypes
                                and form_obj.form in forms]
        else:
            words = [w for w in words if form_obj.formtype in w.forms and form_obj.form in w.forms[form_obj.formtype]]
        if not words:
            raise ValueError("No word matches entry for", form_obj)

        all_meta = []
        for word in words:
            for meta in re.findall("{{es-conj[|]?[^<]*([^|}]*)", word.meta):
                if (meta == "" or "<" in meta) and meta not in all_meta:
                    all_meta.append(meta)

        if not all_meta:
            raise ValueError("no meta", form_obj, words)

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

    def get_smart_verb_form_gloss(self, form_obj):
        conj_params = self.get_verb_conj_params(form_obj)
        if not conj_params:
            conj_params = ""
        return "# {{es-verb form of|" + form_obj.lemma + conj_params + "}}"

    def get_param_verb_form_gloss(self, form_obj):
        # TODO: handle this better
        if " " in form_obj.lemma:
            raise ValueError("unsupported lemma", form_obj.lemma)

        data = {}

        parts = form_obj.formtype.split("_")
        last = parts[-1]
        if last in self.person_props:
           parts.pop()
           data.update(self.person_props[last])

        item = "_".join(parts)
        if item not in self.slot_to_props:
            raise ValueError("invalid verb type", item, form_obj)

        data.update(self.slot_to_props[item])

        # some imperatives are the same in the affirmative and the negative
        if form_obj.formtype in ["imp_3s", "imp_3p"]:
            #print("using generic imperative", formtype)
            del data["sense"]
        elif form_obj.formtype in ["imp_2sf", "imp_1p", "imp_2pf"] and not form_obj.lemma.endswith("rse"):
            #print("using generic imperative", formtype)
            del data["sense"]

        data["ending"] = form_obj.lemma[-4:-2] if form_obj.lemma[-2:] == "se" else form_obj.lemma[-2:]
        if data["ending"] not in ["ar", "er", "ir", "ír"]:
            raise ValueError("unsupported lemma (can't find verb ending)", form_obj.lemma)

        gloss = "# {{es-verb form of|" + "|".join(f"{k}={v}" for k,v in sorted(data.items(), key=lambda x: self.param_order[x[0]])) + "|" + form_obj.lemma + "}}"
        return gloss


    def get_verb_compound_gloss(self, form_obj):
        # formtypes: imp_2s_comb_melo

        # TODO: handle this better
        if " " in form_obj.lemma:
            raise ValueError("unsupported lemma", form_obj.lemma)

        ending = form_obj.lemma[-4:-2] if form_obj.lemma[-2:] == "se" else form_obj.lemma[-2:]
        if ending not in ["ar", "er", "ir", "ír"]:
            raise ValueError("unsupported lemma (can't find verb ending)", form_obj.lemma)

        stem = form_obj.lemma[:-4] if form_obj.lemma[-2:] == "se" else form_obj.lemma[:-2]
        splits = form_obj.formtype.split("_")
        combo = splits[-1]
        if len(combo) > 3 and combo[-2:] in ["lo", "la", "le"]:
            pronoun1 = combo[:-2]
            pronoun2 = combo[-2:]
        elif len(combo) > 3 and combo[-3:] in ["los", "las"]:
            pronoun1 = combo[:-3]
            pronoun2 = combo[-3:]
        else:
           pronoun1 = combo
           pronoun2 = None

        if form_obj.formtype.startswith("imp_"):
            mood = "imperative"
        elif form_obj.formtype.startswith("gerund_"):
            mood = "gerund"
        elif form_obj.formtype.startswith("infinitive_"):
            mood = "infinitive"
        else:
            raise ValueError("unsupported formtype", form_obj.formtype)

        if mood == "imperative":
            pidx = splits.index("imp") + 1
            person_tag = splits[pidx]

            person = {"2s": "tú",
                    "2sf": "usted",
                    "1p": "nosotros",
                    "2p": "vosotros",
                    "2pf": "ustedes"}[person_tag]
        else:
            person = None

        shortform = unstress(form_obj.form[:-1*(len(combo))])
        # if shortform is 1p, it may have dropped the s
        if mood == "imperative" and person == "nosotros":
            if not shortform.endswith("s"):
                shortform += "s"

        params = [stem, ending, shortform, pronoun1]
        if pronoun2:
            params.append(pronoun2)

        params.append("mood=" + mood)
        if person:
            params.append("person=" + person)

        gloss = "# {{es-compound of|" + "|".join(params) + "}}"

        return gloss


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
            return self.get_smart_verb_form_gloss(form_obj)
        elif self.can_handle(form_obj):
            return self.get_generic_gloss(form_obj)

        raise ValueError("unsupported pos", pos)

    def full_pos(self, title, level, forms):
        if not forms:
            raise ValueError(title, "no forms")

        pos = forms[0].pos
        if any(f for f in forms if f.pos != pos):
            raise ValueError(f"expected one type of pos, but got multiples: {f.pos} != {pos}", f)

        res = [ "="*level + POS_TO_TITLE[pos] + "="*level ]

        # TODO: Verify all forms share a lemma ?

        res.append(self.get_form_head(forms[0]))
        res.append("")


        added_forms = set()
        for form_obj in forms:
            item = ExistingForm(form_obj.form, form_obj.pos, form_obj.formtype, form_obj.lemma)
            if item in added_forms:
                continue
            res.append(self.get_form_gloss(form_obj))
            added_forms.add(item)

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
            #pos, formtype, lemma, lemma_genders = form
            if form.pos != prev_pos:
                if prev_pos:
                    res.append("")
                    res += self.full_pos(title, 3, pos_forms)
                pos_forms = []
            pos_forms.append(form)
            prev_pos = form.pos
        if pos_forms:
            res.append("")
            res += self.full_pos(title, 3, pos_forms)

        return "\n".join(res)


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

            # combined forms of reflexive verbs use the infinitive
            # TODO: unless it's exclusively a reflexive verb
            elif "_comb" in item.formtype and item.lemma.endswith("rse"):
                alt_item = item._replace(lemma=item.lemma[:-2])

            elif item.formtype in smart_inflection_formtypes:
                alt_item = item._replace(formtype = "smart_inflection")

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

    @classmethod
    def get_existing_forms(cls, title, wikt):
        existing_forms = {}

        # if feminine noun with masculine, add form of masculine
        for word in wikt.filter_words():

            #for formtype, forms in word.forms.items():
            if "f" in word.genders: # or "m" in word.genders:
                gender = "f" # if "f" in word.genders else "m"
                mate =  "m" #if gender == "f" else "f"

                wlword = Word(title, [("meta", word.headword), ("pos", word.shortpos)])
                if mate in wlword.forms:
                    for mate_lemma in wlword.forms[mate]:
                        item = ExistingForm(title, word.shortpos, gender, mate_lemma)
                        existing_forms[item] = None

        for sense in wikt.filter_wordsenses():
            pos_title = re.sub("[ 1-9]+$", "", sense._parent._parent.name)
            pos = ALL_POS[pos_title]

            gloss = wiki_to_text(str(sense.gloss), "title").lstrip("# ")
            if " of " not in gloss:
                continue

            formtype, lemma, nonform = Sense.parse_form_of(gloss)

            # Limit to the formtypes we can handle, forms like "misspelling of" aren't our concern
            if cls.can_handle_formtype(formtype):

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
        if missing_form.pos == "v":
            if len(word_targets) > 1:
                raise ValueError("Multiple word matches")
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

                    data = "\n".join(self.full_pos(title, target._level, forms)) + "\n\n"
                    changes.append(["after", target, data])
                else:
                    target = next(wikt.ifilter_pos(), None)
                    level = target._level if target else 3
                    data = "\n".join(self.full_pos(title, level, forms)) + "\n\n"
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
            self.remove_forms(title, entry, unexpected_forms, ignore_errors)

        return str(wikt)


    def replace_pos(self, title, page_text, x_forms, target_pos):
        """ Removes the pos section entirely and then re-creates it with the given forms
        fails if the existing pos has anything other than generic form or data """

        forms = [f for f in x_forms if f.pos == target_pos]

        if not forms:
            return page_text

        wikt = wtparser.parse_page(page_text, title=title, parent=None, skip_style_tags=True)
        entry = self.get_language_entry(title, wikt, "Spanish")
        if not entry:
            return page_text

        removeable = []
        for item in entry.ifilter_pos(matches=lambda x: x.name.strip().startswith(POS_TO_TITLE[target_pos])):
            if item not in removeable:

                removeable.append(item)

                # remove conjugations section, since it's not appropriate for forms
                if any(x.name != "Conjugation" for x in item.ifilter_sections()):
                    raise ValueError(title, "Can't remove - has subsections")

                for sense in item.ifilter_wordsenses():
                    if "|t=" in str(sense) or "|gloss=" in str(sense):
                        raise ValueError(title, "Can't remove - sense has gloss", str(sense))

                    # strip syn/ant templates before checking for extra text
                    sense_temp = str(sense)
                    sense_temp = re.sub("{{(syn|ant)[^}]}}", "", sense_temp)
                    sense_text = wiki_to_text(sense_temp, title).strip("\n #:")
                    if "\n" in sense_text:
                        raise ValueError(title, "Can't remove - sense has extra info", str(sense))

                    formtype, lemma, nonform = Sense.parse_form_of(sense_text)
                    if not formtype:
                        raise ValueError(title, "Can't remove - sense has non-form gloss", str(sense))

        for i, item in enumerate(removeable):
            if i == 0:
                new_lines = self.full_pos(title, item._level, forms) + ["", ""]
                new_text = "\n".join(new_lines)
                item._parent.insert_before(item, new_text)

            item._parent.remove_child(item)

        res = str(wikt).rstrip()

        # Sloppy workaround when the last item has been replaced
        if not res.endswith("----") and page_text.rstrip().endswith("----"):
            res = res + "\n----"

        res += "\n"

        # if the only difference is "|g=m-p" and just return the normal page
        if re.sub(r" form\|g=([mfps-]*)}}", " form}}", res.rstrip()) == re.sub(r" form\|g=([mfps-]*)}}", " form}}", page_text.rstrip()):
            return page_text

        return res

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
            #raise e
            with open("error.log", "a") as outfile:
                print(f"{title} failed during add forms {e}")
                outfile.write(f"{title}: failed during add forms {e}\n")
            return page_text


    def _replace_pos(self, page_text, title, pos):
        forms = self.fixer.get_declared_forms(title, self.wordlist, self.allforms)

        forms = [f for f in forms if f.pos in pos]
        return self.fixer.replace_pos(title, page_text, forms, pos)


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


    def add_forms(self, match, title, replacement=None):

        page_text = match.group(0)
        if not self.can_handle_page(title):
            return page_text

        # IF there's no spanish entry, pass the full page text so the language can be inserted in the right place
        if "#REDIRECT" in page_text:
            page_text = re.sub("^#REDIRECT.*$", "", page_text)
            if not re.match(r"\s*$", page_text, re.S):
                raise ValueError(f"{title}: has a redirect with extra text")

        if replacement:
            replacement._edit_summary = "Spanish: Added forms"

        try:
            return self._add_forms(page_text, title, skip_errors=True)
        except BaseException as e:
            print("ERROR:", e)
            #raise e
            with open("error.log", "a") as outfile:
                print(f"{title} failed during add forms {e}")
                outfile.write(f"{title}: failed during add forms {e}\n")
            return page_text



    def remove_forms(self, match, title, replacement=None):

        page_text = match.group(0)
        if not self.can_handle_page(title):
            return page_text

        if replacement:
             replacement._edit_summary = "Spanish: Removed forms"
        return self._remove_forms(page_text, title)

    def replace_pos(self, match, title, replacement, pos_list):

        page_text = match.group(0)
        if not self.can_handle_page(title):
            return page_text

        replaced = set()
        new_text = page_text
        for pos in pos_list:
            try:
                text = self._replace_pos(new_text, title, pos)
                if text != new_text:
                    replaced.add(f"Replaced {pos} forms")
                    new_text = text

            except BaseException as e:
                print("ERROR:", title, e)
                #raise e
                with open("error.log", "a") as outfile:
                    print(f"{title} failed during replace pos {pos} {e}")
                    outfile.write(f"{title}: failed during replace pos {e}\n")

        if replacement and replaced:
            replacement._edit_summary = f"Spanish: " + "; ".join(sorted(replaced))

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
