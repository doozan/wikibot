SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c
.ONESHELL:
.DELETE_ON_ERROR:
MAKEFLAGS += --warn-undefined-variables
MAKEFLAGS += --no-builtin-rules
MAKEFLAGS += --keep-going

# don't delete any intermediary files
.SECONDARY:

ifeq ($(origin .RECIPEPREFIX), undefined)
  $(error This Make does not support .RECIPEPREFIX. Please use GNU Make 4.0 or later)
endif
.RECIPEPREFIX = >

# Uncomment this to autofix
#ALWAYS := -always
ALWAYS := 

DATETAG := $(shell curl -s https://dumps.wikimedia.org/enwiktionary/ | grep '>[0-9]*/<' | cut -b 10-17 | tail -1)
DATETAG_PRETTY := $(shell date --date="$(DATETAG)" +%Y-%m-%d)

SPANISH_DATA := ../spanish_data
DRAEDATA := ../drae_data
BUILDDIR := $(SPANISH_DATA)/$(DATETAG_PRETTY)
PYPATH := PYTHONPATH=$(BUILDDIR)

NGRAMDATA := ../ngram_data
NGYEAR := 1950

DUMP_LEMMAS := $(PYPATH) $(BUILDDIR)/enwiktionary_wordlist/scripts/dump_lemmas

WIKI2TEXT := $(PYPATH) scripts/wiki2text
WIKIGREP := $(PYPATH) scripts/wikigrep
WIKISEARCH := $(PYPATH) scripts/wikisearch
WIKISORT := $(PYPATH) scripts/wikisort
GETLINKS := $(PYPATH) scripts/getlinks
GETIGNORE := $(PYPATH) scripts/getignore
WIKIFIX := $(PYPATH) scripts/wikifix

LIST_DUPLICATE_PASSAGES := $(PYPATH) ./list_duplicate_passages.py
LIST_VERBS_MISSING_TYPE := $(PYPATH) ./list_verbs_missing_type.py
LIST_MISSING_FORMS := $(PYPATH) ./list_missing_forms.py
LIST_MAYBE_FORMS := $(PYPATH) ./list_maybe_forms.py
LIST_MISMATCHED_HEADLINES := $(PYPATH) ./list_mismatched_headlines.py
LIST_FORMS_WITH_DATA := $(PYPATH) ./list_forms_with_data.py
MAKE_SECTION_STATS := $(PYPATH) ./make_section_stats.py
LIST_T9N_PROBLEMS := $(PYPATH) ./list_t9n_problems.py
LIST_ISMO_ISTA := $(PYPATH) ./list_ismo_ista.py
LIST_COORD_TERMS := $(PYPATH) ./list_coord_terms.py
LIST_USUALLY_PLURAL := $(PYPATH) ./list_usually_plural.py
LIST_SPLIT_VERB_DATA := $(PYPATH) ./list_split_verb_data.py
LIST_SECTION_HEADER_ERRORS := $(PYPATH) ./list_section_header_errors.py
LIST_SECTION_ORDER_ERRORS := $(PYPATH) ./list_section_order_errors.py
LIST_SECTION_LEVEL_ERRORS := $(PYPATH) ./list_section_level_errors.py
LIST_DRAE_ERRORS := $(PYPATH) ./list_drae_errors.py
LIST_MISSING_DRAE := $(PYPATH) ./list_missing_drae.py
LIST_DRAE_MISMATCHED_GENDERS := $(PYPATH) ./list_drae_mismatched_genders.py
LIST_ES_FORM_OVERRIDES := $(PYPATH) ./list_es_form_overrides.py
LIST_BARE_QUOTES := $(PYPATH) ./list_bare_quotes.py
LIST_CONVERT_LIST_TO_COL := $(PYPATH) ./list_convert_list_to_col.py
LIST_UNBALANCED_DELIMITERS := $(PYPATH) ./list_unbalanced_delimiters.py
LIST_QUOTE_WITH_BARE_PASSAGE := $(PYPATH) ./list_quote_with_bare_passage.py
LIST_SENSE_BYLINES := $(PYPATH) ./list_sense_byline_errors.py
LIST_BARE_UX := $(PYPATH) ./list_bare_ux.py
DUMP_RQ_TEMPLATE_PARAMS := $(PYPATH) ./dump_rq_template_params.py
DUMP_TEMPLATE_DATA := $(PYPATH) ./dump_template_data.py
DUMP_MODULE_DATA := $(PYPATH) ./dump_module_data.py
LIST_BAD_TEMPLATE_PARAMS := $(PYPATH) ./list_bad_template_params.py
COUNT_TEMPLATE_USE := $(PYPATH) ./count_template_use.py
MAKE_TEMPLATE_STATS := $(PYPATH) ./make_template_stats.py
DUMP_TAXONS := $(PYPATH) ./dump_taxons.py
LIST_LOCAL_TAXONS := $(PYPATH) ./list_local_taxons.py
LIST_EXTERNAL_TAXONS := $(PYPATH) ./list_external_taxons.py
LIST_POSSIBLE_TAXONS := $(PYPATH) ./list_possible_taxons.py
LIST_MISSING_TAXLINKS := $(PYPATH) ./list_missing_taxlinks.py
LIST_TAXONS_WITH_REDLINKS := $(PYPATH) ./list_taxons_with_redlinks.py
DUMP_TEMPLATE_USE := $(PYPATH) ./dump_template_use.py
LIST_DEF_TEMPLATE_IN_ETY := $(PYPATH) ./list_def_template_in_ety.py


EXTERNAL := ../..
PUT := $(PYPATH) $(EXTERNAL)/put.py
FUN_REPLACE := $(PYPATH) $(EXTERNAL)/fun_replace.py
TLFI_LEMMAS := $(EXTERNAL)/tlfi.lemmas


# prefix for list files
LIST := $(BUILDDIR)/.list.
FIX := $(BUILDDIR)/.fix.

SAVE := --save "Updated with $(DATETAG_PRETTY) data"

# Call into the spanish_data makefile to build anything not declared here
$(BUILDDIR)/%.data-full: force
>   @echo "Subcontracting $@..."
>   $(MAKE) -C $(SPANISH_DATA) $(@:$(SPANISH_DATA)/%=%)

$(BUILDDIR)/%.data: force
>   @echo "Subcontracting $@..."
>   $(MAKE) -C $(SPANISH_DATA) $(@:$(SPANISH_DATA)/%=%)

$(BUILDDIR)/%.frequency.csv: force
>   @echo "Subcontracting $@..."
>   $(MAKE) -C $(SPANISH_DATA) $(@:$(SPANISH_DATA)/%=%)

$(BUILDDIR)/%.json: force
>   @echo "Subcontracting $@..."
>   $(MAKE) -C $(SPANISH_DATA) $(@:$(SPANISH_DATA)/%=%)

force: ;
# force used per https://www.gnu.org/software/make/manual/html_node/Overriding-Makefiles.html

$(BUILDDIR)/%.sortorder: $(BUILDDIR)/%.frequency.csv
>   @echo "Making $@..."
>   cat $< | tail -n +2 | grep -v NODEF | cut -d "," -f 2 > $@

$(BUILDDIR)/es-es.drae.sortorder: $(DRAEDATA)/drae.freq.csv
>   @echo "Making $@..."
>   cat $< | tail -n +2 | grep -v NODEF | cut -d "," -f 2 > $@

$(BUILDDIR)/%.pages: $(BUILDDIR)/%.txt.bz2
>   @echo "Making $@..."
>   bzcat $< | perl -ne '/^_____([^_]+):[^_]+_____$$/ && print "$$1\n"' > $@.unsorted
>   sort -u $@.unsorted > $@.sorted
>   $(RM) $@.unsorted
>   mv $@.sorted $@

$(BUILDDIR)/%.lemmas: $(BUILDDIR)/%.data-full
>   @echo "Making $@..."
>   $(DUMP_LEMMAS) $< | sort > $@

$(BUILDDIR)/%.with_etymology: $(BUILDDIR)/%.data-full
>   @echo "Making $@..."
>   cat $<| perl -ne 'if (/^_____$$/) { undef $$entry } elsif (not defined $$entry) { $$entry = $$_ } elsif (/etymology:/) { print($$entry) }' | sort -u > $@

$(BUILDDIR)/%.lemmas_without_etymology: $(BUILDDIR)/%.lemmas $(BUILDDIR)/%.with_etymology
>   @echo "Making $@..."
>   comm -23 $(BUILDDIR)/$*.lemmas $(BUILDDIR)/$*.with_etymology > $@

$(BUILDDIR)/wikt.sentences: $(BUILDDIR)/es-en.enwikt.txt.bz2
>   @echo "Making $@..."
>   $(LIST_DUPLICATE_PASSAGES) $^ --dump > $@

$(BUILDDIR)/spa.sentences: $(BUILDDIR)/eng-spa.tsv
>   @echo "Making $@..."
>   cp $< $@

/var/local/wikt/%.sentences.tgz: $(BUILDDIR)/%.sentences $(BUILDDIR)/%.json
>   @echo "Making $@..."
>   tar czvf $@ -C $(BUILDDIR) $*.sentences $*.json

$(BUILDDIR)/rq_template_params.json: $(BUILDDIR)/templates.enwikt.txt.bz2
>   echo "Making $@..."
>   $(DUMP_RQ_TEMPLATE_PARAMS) --wxt $< $@

$(BUILDDIR)/template_data.json: $(BUILDDIR)/templates.enwikt.txt.bz2
>   @echo "Making $@..."
>   $(DUMP_TEMPLATE_DATA) --wxt $< $@

$(BUILDDIR)/module_data.json: $(BUILDDIR)/modules.enwikt.txt.bz2
>   @echo "Making $@..."
>   $(DUMP_MODULE_DATA) --wxt $< $@

$(BUILDDIR)/template_count.tsv: $(BUILDDIR)/enwiktionary-$(DATETAG)-pages-articles.xml.bz2
>   @echo "Making $@..."
>   $(COUNT_TEMPLATE_USE) --xml $< > $@

$(BUILDDIR)/taxons.txt.bz2: $(BUILDDIR)/enwiktionary-$(DATETAG)-pages-articles.xml.bz2
>   @echo "Making $@..."
>   $(DUMP_TAXONS) --xml $< | bzip2 > $@

$(BUILDDIR)/taxlinks.txt.bz2: $(BUILDDIR)/enwiktionary-$(DATETAG)-pages-articles.xml.bz2
>   @echo "Making $@..."
>   $(DUMP_TEMPLATE_USE) -t taxlink --xml $< | bzip2 > $@

$(BUILDDIR)/local_taxons.tsv $(LIST)local_taxons &: $(BUILDDIR)/taxons.txt.bz2
>   @echo "Making $@..."
>   $(LIST_LOCAL_TAXONS) --wxt $< $(SAVE) > $@

$(BUILDDIR)/external_taxons.tsv $(LIST)external_taxons &: $(BUILDDIR)/taxlinks.txt.bz2
>   @echo "Making $@..."
>   $(LIST_EXTERNAL_TAXONS) --wxt $< $(SAVE) > $@

# Lists


$(LIST)t9n_problems: $(BUILDDIR)/translations.bz2 $(BUILDDIR)/es-en.enwikt.allforms.csv
>   @echo "Running $@..."

>   $(LIST_T9N_PROBLEMS) --trans $< --allforms $(BUILDDIR)/es-en.enwikt.allforms.csv $(SAVE)
>   touch $@

$(LIST)section_stats: $(BUILDDIR)/all-en.enwikt.txt.bz2
>   @echo "Running $@..."
# --tag $(DATETAG)
>   $(MAKE_SECTION_STATS) $< $(SAVE)
>   touch $@

$(LIST)es_forms_with_data: $(BUILDDIR)/es-en.enwikt.txt.bz2
>   @echo "Running $@..."
>   $(LIST_FORMS_WITH_DATA) --file $< $(SAVE)
>   touch $@

$(LIST)mismatched_headlines: $(BUILDDIR)/all-en.enwikt.txt.bz2
>   @echo "Running $@..."

>   $(LIST_MISMATCHED_HEADLINES) $<  $(SAVE)
>   touch $@

$(LIST)es_maybe_forms: $(BUILDDIR)/es-en.enwikt.data-full
>   @echo "Running $@..."

>   $(LIST_MAYBE_FORMS) --wordlist $< $(SAVE)
>   touch $@

$(LIST)es_missing_forms: $(BUILDDIR)/es-en.enwikt.allforms.csv $(BUILDDIR)/es-en.enwikt.data-full $(BUILDDIR)/all-en.enwikt.pages $(BUILDDIR)/es-en.enwikt.txt.bz2
>   echo "Running $@..."
>   $(LIST_MISSING_FORMS) --allforms $(BUILDDIR)/es-en.enwikt.allforms.csv --allpages $(BUILDDIR)/all-en.enwikt.pages --articles $(BUILDDIR)/all-en.enwikt.txt.bz2 $(BUILDDIR)/es-en.enwikt.data-full $(SAVE)
>   touch $@

$(LIST)fr_missing_lemmas: $(BUILDDIR)/fr-en.enwikt.lemmas $(BUILDDIR)/fr-en.enwikt.pages $(TLFI_LEMMAS)
>   @echo "Running $@..."
>   DEST="User:JeffDoozan/lists/fr_forms_with_tlfi_lemmata"
>   SUMMARY="French entries where we have forms but the TLFi has a lemma"
>   echo "still Running $@..."

>   comm -23 $(BUILDDIR)/fr-en.enwikt.pages $(BUILDDIR)/fr-en.enwikt.lemmas > $@.formonly
>   comm -12 $@.formonly $(TLFI_LEMMAS) \
>   | awk '{print "; [["$$0"#French|"$$0"]] [https://www.cnrtl.fr/definition/"$$0" TLFi]"}' \
>   > $@.wiki.base

>   COUNT=`wc -l $@.wiki.base | cut -d " " -f 1`
>   echo "$$SUMMARY as of $(DATETAG_PRETTY) ($$COUNT entries)" > $@.wiki
>   cat $@.wiki.base >> $@.wiki

>   $(PUT) -textonly -force "-title:$$DEST" -file:$@.wiki -summary:"Updated with $(DATETAG_PRETTY) data"
>   $(RM) $@.formonly $@.wiki.base
>   mv $@.wiki $@

$(LIST)es_missing_lemmas: $(BUILDDIR)/es-en.enwikt.lemmas $(BUILDDIR)/es-es.drae.lemmas $(BUILDDIR)/es-es.drae.sortorder $(BUILDDIR)/es-en.enwikt.pages
>   @echo "Running $@..."
>   DEST="User:JeffDoozan/lists/es_forms_with_drae_lemmata"
>   SUMMARY="Spanish entries where we have forms but the DRAE has a lemma"

>   comm -23 $(BUILDDIR)/es-en.enwikt.pages $(BUILDDIR)/es-en.enwikt.lemmas > $@.formonly
>   comm -12 $@.formonly $(BUILDDIR)/es-es.drae.lemmas > $@.sorted_az
>   $(WIKISORT) $(BUILDDIR)/es-es.drae.sortorder $@.sorted_az \
>   | awk '{print "; [["$$0"#Spanish|"$$0"]] [https://dle.rae.es/"$$0" drae]"}'\
>   > $@.wiki.base

>   COUNT=`wc -l $@.wiki.base | cut -d " " -f 1`
>   echo "$$SUMMARY as of $(DATETAG_PRETTY) ($$COUNT entries); sorted by lemma frequency" > $@.wiki
>   cat $@.wiki.base >> $@.wiki

>   $(PUT) -textonly -force "-title:$$DEST" -file:$@.wiki -summary:"Updated with $(DATETAG_PRETTY) data"
>   $(RM) $@.formonly $@.sorted_az $@.wiki.base
>   mv $@.wiki $@

$(LIST)es_missing_ety: $(BUILDDIR)/es-es.drae.with_etymology $(BUILDDIR)/es-en.enwikt.lemmas_without_etymology $(BUILDDIR)/es-en.enwikt.sortorder
>   @echo "Running $@..."
>   DEST="User:JeffDoozan/lists/es_missing_ety"
>   SUMMARY="Spanish words with etymology info in DRAE but not Wiktionary"

>   comm -12 $(BUILDDIR)/es-es.drae.with_etymology $(BUILDDIR)/es-en.enwikt.lemmas_without_etymology > $@.sorted_az
>   $(WIKISORT) $(BUILDDIR)/es-en.enwikt.sortorder $@.sorted_az \
>   | awk '{print "; [["$$0"#Spanish|"$$0"]] [https://dle.rae.es/"$$0" drae]"}' \
>   > $@.wiki.base

>   COUNT=`wc -l $@.wiki.base | cut -d " " -f 1`
>   echo "$$SUMMARY as of $(DATETAG_PRETTY) ($$COUNT entries); sorted by lemma frequency" > $@.wiki
>   cat $@.wiki.base >> $@.wiki

>   $(PUT) -textonly -force "-title:$$DEST" -file:$@.wiki -summary:"Updated with $(DATETAG_PRETTY) data"
>   $(RM) $@.wiki.base  $@.sorted_az
>   mv $@.wiki $@

$(LIST)fr_missing_tlfi: $(BUILDDIR)/fr-en.enwikt.txt.bz2 $(BUILDDIR)/fr-en.enwikt.lemmas $(TLFI_LEMMAS)
>   @echo "Running $@..."
>   DEST="User:JeffDoozan/lists/fr_missing_tlfi"
>   SUMMARY="Entries missing a link to TLFI"

>   $(WIKIGREP) $< "{{R:fr:TLFi" | cut -d ":" -f 1 | sort -u > $@.with_tlfi
>   comm -23 $(BUILDDIR)/fr-en.enwikt.lemmas $@.with_tlfi > $@.without_tlfi
>   comm -12 $@.without_tlfi $(TLFI_LEMMAS) \
>   | grep -v "^.$$" \
>   | awk '{ print "; [["$$0"#French|"$$0"]]" }' \
>   > $@.wiki.base

>   COUNT=`wc -l $@.wiki.base | cut -d " " -f 1`
>   echo "$$SUMMARY as of $(DATETAG_PRETTY) ($$COUNT entries)" > $@.wiki
>   cat $@.wiki.base >> $@.wiki

>   $(PUT) -textonly -force "-title:$$DEST" -file:$@.wiki -summary:"Updated with $(DATETAG_PRETTY) data"
>   $(RM) $@.with_tlf $@.without_tlfi $@.wiki.base
>   mv $@.wiki $@

$(LIST)es_missing_drae: $(BUILDDIR)/es-en.enwikt.allforms.csv
>   echo "Making $@..."
>   DEST="User:JeffDoozan/lists/es_missing_drae"
>   SUMMARY="DRAE entries missing from Wiktionary"
>
>   $(GETIGNORE) "$$DEST" > $@.ignore
>
>   $(LIST_MISSING_DRAE) \
>       --min-use 4000 \
>       --wikt $(BUILDDIR)/es-en.enwikt.allforms.csv \
>       --drae $(DRAEDATA)/drae.allforms.csv \
>       --drae-links $(DRAEDATA)/drae.links \
>       --wordlist $(DRAEDATA)/drae.data \
>       --freq $(DRAEDATA)/drae.freq.csv \
>       --counts $(DRAEDATA)/drae.txt \
>       --forced-forms $(DRAEDATA)/patterns.csv \
>       --ignore $@.ignore \
>       > $@.wiki.base
>
>   echo "$$SUMMARY as of $(DATETAG_PRETTY)" > $@.wiki
>   cat $@.wiki.base >> $@.wiki
>   $(PUT) -textonly -force "-title:$$DEST" -file:$@.wiki -summary:"Updated with $(DATETAG_PRETTY) data"
>
>   $(RM) $@.ignore $@.wiki $@.wiki.base
>   touch $@

$(LIST)es_drae_errors: $(BUILDDIR)/es-en.enwikt.txt.bz2 $(SPANISH_DATA)/es-en.data
>   echo "Running $@..."
>   $(LIST_DRAE_ERRORS) --wordlist $(SPANISH_DATA)/es-en.data $(BUILDDIR)/es-en.enwikt.txt.bz2 --draelinks $(DRAEDATA)/drae.links $(SAVE)
>   touch $@

$(LIST)es_drae_mismatched_genders: $(SPANISH_DATA)/es-en.data
>   @echo "Running $@..."
>   $(LIST_DRAE_MISMATCHED_GENDERS) $(SAVE) \
>       --wikt $< \
>       --drae $(DRAEDATA)/drae.data \
>       --ngramdb $(NGRAMDATA)/spa/ngram-1950.db
>   touch $@

$(LIST)es_untagged_demonyms: $(BUILDDIR)/es-en.enwikt.txt.bz2
>   @echo "Running $@..."
>   DEST="User:JeffDoozan/lists/es_untagged_demonyms"
>   SUMMARY="Entries that may be untagged demonyms"
>   $(WIKISEARCH) $< \
>       '^# .*(((one|body|person) from)|((native|resident|inhabitant) of|of or relat)|\(person\))' \
>       --path-filter ".*:Noun" \
>       --not Demonyms \
>   | grep -iv "President of" \
>   | $(WIKI2TEXT) \
>   | sed -e 's/: [#*: ]*/: /' \
>   | sort \
>   | awk -F: '{ x=$$1; $$1=""; print "; [["x"#Spanish|"x"]]:" $$0 }' \
>   > $@.wiki.base

>   COUNT=`wc -l $@.wiki.base | cut -d " " -f 1`
>   echo "$$SUMMARY as of $(DATETAG_PRETTY) ($$COUNT entries)" > $@.wiki
>   cat $@.wiki.base >> $@.wiki

>   $(PUT) -textonly -force "-title:$$DEST" -file:$@.wiki -summary:"Updated with $(DATETAG_PRETTY) data"
>   $(RM) $@.wiki.base
>   mv $@.wiki $@

$(LIST)es_duplicate_passages: $(BUILDDIR)/es-en.enwikt.txt.bz2
>   @echo "Running $@..."
>   DEST="User:JeffDoozan/lists/es duplicate passages"
>   SUMMARY="Entries with duplicate untranslated passages"

>   $(LIST_DUPLICATE_PASSAGES) $(BUILDDIR)/es-en.enwikt.txt.bz2 --missing-trans > $@.wiki.base

>   COUNT=`wc -l $@.wiki.base | cut -d " " -f 1`
>   echo "$$SUMMARY as of $(DATETAG_PRETTY) ($$COUNT entries)" > $@.wiki
>   cat $@.wiki.base >> $@.wiki

>   $(PUT) -textonly -force "-title:$$DEST" -file:$@.wiki -summary:"Updated with $(DATETAG_PRETTY) data"
>   $(RM) $@.wiki.base $@.with_passage
>   mv $@.wiki $@

$(LIST)es_mismatched_passages: $(BUILDDIR)/es-en.enwikt.txt.bz2
>   @echo "Running $@..."
>   DEST="User:JeffDoozan/lists/es mismatched passages"
>   SUMMARY="Entries with mismatched passage translations"

>   $(LIST_DUPLICATE_PASSAGES) $(BUILDDIR)/es-en.enwikt.txt.bz2 --mismatched-trans > $@.wiki.base

>   COUNT=`grep "^'''" $@.wiki.base | wc -l | cut -d " " -f 1`
>   echo -e "$$SUMMARY as of $(DATETAG_PRETTY) ($$COUNT entries)\n" > $@.wiki
>   cat $@.wiki.base >> $@.wiki

>   $(PUT) -textonly -force "-title:$$DEST" -file:$@.wiki -summary:"Updated with $(DATETAG_PRETTY) data"
>   $(RM) $@.wiki.base $@.with_passage
>   mv $@.wiki $@

$(LIST)es_with_synonyms: $(BUILDDIR)/es-en.enwikt.txt.bz2
>   @echo "Running $@..."
>   DEST="User:JeffDoozan/lists/es_with_synonyms"
>   SUMMARY="Entries with synonyms section"

>   $(WIKIGREP) $< "==\s*Synonyms\s*==" \
>   | cut -d ":" -f 1 \
>   | sort -u \
>   |  awk -F: '{ print "; [["$$0"#Spanish|"$$0"]]" }' \
>   > $@.wiki.base

>   COUNT=`wc -l $@.wiki.base | cut -d " " -f 1`
>   echo "$$SUMMARY as of $(DATETAG_PRETTY) ($$COUNT entries)" > $@.wiki
>   cat $@.wiki.base >> $@.wiki

>   $(PUT) -textonly -force "-title:$$DEST" -file:$@.wiki -summary:"Updated with $(DATETAG_PRETTY) data"
>   $(RM) $@.wiki.base
>   mv $@.wiki $@

$(LIST)pt_with_synonyms: $(BUILDDIR)/pt-en.enwikt.txt.bz2
>   @echo "Running $@..."
>   DEST="User:JeffDoozan/lists/Portuguese_with_Synonyms"
>   SUMMARY="Entries with synonyms section"

>   $(WIKIGREP) $< "==\s*Synonyms\s*==" \
>   | cut -d ":" -f 1 \
>   | sort -u \
>   |  awk -F: '{ print "; [["$$0"#Portuguese|"$$0"]]" }' \
>   > $@.wiki.base

>   COUNT=`wc -l $@.wiki.base | cut -d " " -f 1`
>   echo "$$SUMMARY as of $(DATETAG_PRETTY) ($$COUNT entries)" > $@.wiki
>   cat $@.wiki.base >> $@.wiki

>   $(PUT) -textonly -force "-title:$$DEST" -file:$@.wiki -summary:"Updated with $(DATETAG_PRETTY) data"
>   $(RM) $@.wiki.base
>   mv $@.wiki $@

$(LIST)es_verbs_missing_type: $(BUILDDIR)/es-en.enwikt.data $(BUILDDIR)/es-en.enwikt.sortorder
>   @echo "Running $@..."
>   DEST="User:JeffDoozan/lists/es/verbs_missing_type"
>   SUMMARY="Verbs missing a type label in at least one sense"

>   $(LIST_VERBS_MISSING_TYPE) $< > $@.unsorted
>   $(WIKISORT) $(BUILDDIR)/es-en.enwikt.sortorder $@.unsorted | awk '{ print "; [["$$0"#Spanish|"$$0"]]" }' > $@.wiki.base

>   COUNT=`wc -l $@.wiki.base | cut -d " " -f 1`
>   echo "$$SUMMARY as of $(DATETAG_PRETTY) ($$COUNT entries); sorted by lemma frequency" > $@.wiki
>   cat $@.wiki.base >> $@.wiki

>   $(PUT) -textonly -force "-title:$$DEST" -file:$@.wiki -summary:"Updated with $(DATETAG_PRETTY) data"
>   $(RM) $@.wiki.base $@.unsorted
>   mv $@.wiki $@

$(LIST)ismo_ista: $(BUILDDIR)/es-en.enwikt.allforms.csv $(BUILDDIR)/es-en.enwikt.txt.bz2
>   @echo "Running $@..."

>   $(LIST_ISMO_ISTA) $(SAVE) --allforms $< $(BUILDDIR)/es-en.enwikt.txt.bz2
>   touch $@

IGNORE_COORD2 := $(patsubst %,--ignore2 %,el la lo las los un una y i o u a al de del en se me te su mi tu nos os sus tus mis es que no en ha he has hemos había habían por con sin)
$(LIST)es_coord_terms: $(BUILDDIR)/es-en.enwikt.allforms.csv $(BUILDDIR)/es-1-1950.ngprobs $(patsubst %, $(NGRAMDATA)/spa/%-filtered-1950.coord,2 3 4 5)
>   @echo "Running $@..."

>   $(LIST_COORD_TERMS) --min-count 1000 --min-percent 25 --allforms $< $(SAVE) --ngprobs $(BUILDDIR)/es-1-1950.ngprobs $(IGNORE_COORD2) --coord2 $(NGRAMDATA)/spa/2-filtered-1950.coord --coord3 $(NGRAMDATA)/spa/3-filtered-1950.coord --coord4 $(NGRAMDATA)/spa/4-filtered-1950.coord --coord5 $(NGRAMDATA)/spa/5-filtered-1950.coord
>   touch $@

$(LIST)es_usually_plural: $(BUILDDIR)/es-en.enwikt.data $(BUILDDIR)/es-1-1950.ngprobs $(NGRAMDATA)/spa/es-1-1950.ngcase
>   @echo "Running $@..."

>   $(LIST_USUALLY_PLURAL) $(SAVE) --dictionary $< --ngprobs $(BUILDDIR)/es-1-1950.ngprobs --ngcase $(NGRAMDATA)/spa/es-1-1950.ngcase
>   touch $@

$(LIST)es_split_verb_data: $(BUILDDIR)/es-en.enwikt.data
>   @echo "Running $@..."

>   $(LIST_SPLIT_VERB_DATA) $(SAVE) --lang es --dictionary $<
>   touch $@

$(LIST)pt_split_verb_data: $(BUILDDIR)/pt-en.enwikt.data
>   @echo "Running $@..."

>   $(LIST_SPLIT_VERB_DATA) $(SAVE) --lang pt --dictionary $<
>   touch $@

$(LIST)section_header_errors: $(BUILDDIR)/all-en.enwikt.txt.bz2
>   @echo "Running $@..."

>   $(LIST_SECTION_HEADER_ERRORS) $(SAVE) $^
>   touch $@

$(LIST)section_level_errors: $(BUILDDIR)/all-en.enwikt.txt.bz2
>   @echo "Running $@..."

>   $(LIST_SECTION_LEVEL_ERRORS) $(SAVE) $^
>   touch $@

$(LIST)section_order_errors: $(BUILDDIR)/all-en.enwikt.txt.bz2
>   @echo "Running $@..."

>   $(LIST_SECTION_ORDER_ERRORS) $(SAVE) $^
>   touch $@

$(LIST)es_form_overrides: $(BUILDDIR)/es-en.enwikt.txt.bz2
>   @echo "Running $@..."

>   $(LIST_ES_FORM_OVERRIDES) $(SAVE) $^
>   touch $@

$(LIST)bare_quotes: $(BUILDDIR)/all-en.enwikt.txt.bz2
>   @echo "Running $@..."

>   $(LIST_BARE_QUOTES) $(SAVE) $^
>   touch $@

$(LIST)convert_list_to_col: $(BUILDDIR)/all-en.enwikt.txt.bz2
>   @echo "Running $@..."

>   $(LIST_CONVERT_LIST_TO_COL) $(SAVE) $^ --section "Related terms" --section "Derived terms" \
>       --lang cs \
>       --lang es \
>       --lang mt \
>       --lang pl \
>       --lang zlw-opl

>   touch $@

$(LIST)unbalanced_delimiters: $(BUILDDIR)/all-en.enwikt.txt.bz2
>   @echo "Running $@..."

>   $(LIST_UNBALANCED_DELIMITERS) $(SAVE) $^
>   touch $@

$(LIST)quote_with_bare_passage: $(BUILDDIR)/rq_template_params.json $(BUILDDIR)/all-en.enwikt.txt.bz2
>   @echo "Running $@..."

>   $(LIST_QUOTE_WITH_BARE_PASSAGE) $(SAVE) --json $^
>   touch $@

$(LIST)sense_bylines: $(BUILDDIR)/all-en.enwikt.txt.bz2
>   @echo "Running $@..."

>   $(LIST_SENSE_BYLINES) $(SAVE) $^
>   touch $@

$(LIST)bare_ux: $(BUILDDIR)/all-en.enwikt.txt.bz2
>   @echo "Running $@..."

>   $(LIST_BARE_UX) $(SAVE) $^
>   touch $@

$(LIST)bad_template_params $(BUILDDIR)/bad_template_calls.json &: $(BUILDDIR)/template_data.json $(BUILDDIR)/enwiktionary-$(DATETAG)-pages-articles.xml.bz2
>   @echo "Running $@..."

>   $(LIST_BAD_TEMPLATE_PARAMS) $(SAVE) --json $< --xml $(BUILDDIR)/enwiktionary-$(DATETAG)-pages-articles.xml.bz2 --dump-json $(BUILDDIR)/bad_template_calls.json
>   touch $@

$(LIST)possible_taxons: $(BUILDDIR)/all-en.enwikt.txt.bz2 $(BUILDDIR)/local_taxons.tsv $(BUILDDIR)/external_taxons.tsv $(BUILDDIR)/all-en.enwikt.pages
>   @echo "Running $@..."

>   $(LIST_POSSIBLE_TAXONS) --wxt $< --taxons $(BUILDDIR)/local_taxons.tsv --taxons $(BUILDDIR)/external_taxons.tsv --bluelinks $(BUILDDIR)/all-en.enwikt.pages $(SAVE) --date $(DATETAG_PRETTY)
>   touch $@

$(LIST)missing_taxlinks: $(BUILDDIR)/all-en.enwikt.txt.bz2 $(BUILDDIR)/local_taxons.tsv $(BUILDDIR)/external_taxons.tsv
>   @echo "Running $@..."

>   $(LIST_MISSING_TAXLINKS) --local $(BUILDDIR)/local_taxons.tsv --external $(BUILDDIR)/external_taxons.tsv --wxt $< $(SAVE)
>   touch $@

$(LIST)taxons_with_redlinks: $(BUILDDIR)/taxons.txt.bz2 $(BUILDDIR)/all-en.enwikt.pages
>   @echo "Running $@..."

>   $(LIST_TAXONS_WITH_REDLINKS) --wxt $< --bluelinks $(BUILDDIR)/all-en.enwikt.pages $(SAVE) --date $(DATETAG_PRETTY)
>   touch $@

$(LIST)def_template_in_ety: $(BUILDDIR)/all-en.enwikt.txt.bz2
>   @echo "Running $@..."

>   $(LIST_DEF_TEMPLATE_IN_ETY) $< $(SAVE)
>   touch $@

$(LIST)template_stats: $(BUILDDIR)/template_data.json $(BUILDDIR)/template_count.tsv $(BUILDDIR)/module_data.json
>   @echo "Making $@..."
>   $(MAKE_TEMPLATE_STATS) --templates $(BUILDDIR)/template_data.json --count $(BUILDDIR)/template_count.tsv --modules $(BUILDDIR)/module_data.json > $@


# Fixes
$(FIX)fr_missing_tlfi:
>   @
>   FIX="--fix add_tlfi --log-fixes $@.fixes --log-matches $@.matches --config=etc/autodooz-fixes.py"
>   SRC="User:JeffDoozan/lists/fr_missing_tlfi"
>   MAX=500

>   LINKS=`$(GETLINKS) $$SRC | sort -u | wc -l`
>   [ $$LINKS -gt $$MAX ] && echo "Not running $@ too many links: $$LINKS > $$MAX" && exit 1
>   echo "Running fixer $@ on $$LINKS items from $$SRC..."
>   $(WIKIFIX) -links:$$SRC $$FIX $(ALWAYS)
>   echo $$LINKS > $@

# TODO: some sort of list maker to check if they can be auto fixed
$(FIX)es_syns:
>   @
>   FIX="--fix es_simple_nyms"
>   SRC="User:JeffDoozan/lists/es_with_synonyms"
>   MAX=200

>   LINKS=`$(GETLINKS) $$SRC | sort -u | wc -l`
>   [ $$LINKS -gt $$MAX ] && echo "Not running $@ too many links: $$LINKS > $$MAX" && exit 1
>   echo "Running fixer $@ on $$LINKS items from $$SRC..."
>   $(WIKIFIX) -links:$$SRC $$FIX $(ALWAYS)
>   echo $$LINKS > $@

$(FIX)pt_syns:
>   @
>   FIX="-fix:simple_nyms --lang:pt --wordlist:$(BUILDDIR)/pt-en.enwikt.data-full --sections:Synonyms"
>   SRC="User:JeffDoozan/lists/Portuguese_with_Synonyms"
>   MAX=100

>   LINKS=`$(GETLINKS) $$SRC | sort -u | wc -l`
>   [ $$LINKS -gt $$MAX ] && echo "Not running $@ too many links: $$LINKS > $$MAX" && exit 1
>   echo "Running fixer $@ on $$LINKS items from $$SRC..."
>   $(FUN_REPLACE) -links:$$SRC $$FIX $(ALWAYS)
>   echo $$LINKS > $@

$(FIX)section_headers:
>   @
>   SRC="User:JeffDoozan/lists/section_headers/fixes"
>   FIX="--fix ele_cleanup --log-fixes $@.fixes --log-matches $@.matches --config etc/autodooz-fixes.py"
>   MAX=1500

>   LINKS=`$(GETLINKS) $$SRC | sort -u | wc -l`
>   [ $$LINKS -gt $$MAX ] && echo "Not running $@ too many links: $$LINKS > $$MAX" && exit 1
>   echo "Running fixer $@ on $$LINKS items from $$SRC..."
>   $(WIKIFIX) -links:$$SRC $$FIX $(ALWAYS)
>   echo $$LINKS > $@

$(FIX)section_levels:
>   @
>   SRC="User:JeffDoozan/lists/section_levels/fixes"
>   FIX="--fix ele_cleanup --log-fixes $@.fixes --log-matches $@.matches --config etc/autodooz-fixes.py"
>   MAX=1500

>   LINKS=`$(GETLINKS) $$SRC | sort -u | wc -l`
>   [ $$LINKS -gt $$MAX ] && echo "Not running $@ too many links: $$LINKS > $$MAX" && exit 1
>   echo "Running fixer $@ on $$LINKS items from $$SRC..."
>   $(WIKIFIX) -links:$$SRC $$FIX $(ALWAYS)
>   echo $$LINKS > $@

$(FIX)section_order:
>   @
>   SRC="User:JeffDoozan/lists/section_order/fixes"
>   FIX="--fix ele_cleanup --log-fixes $@.fixes --log-matches $@.matches --config etc/autodooz-fixes.py"
>   MAX=800

>   LINKS=`$(GETLINKS) $$SRC | sort -u | wc -l`
>   [ $$LINKS -gt $$MAX ] && echo "Not running $@ too many links: $$LINKS > $$MAX" && exit 1
>   echo "Running fixer $@ on $$LINKS items from $$SRC..."
>   $(WIKIFIX) -links:$$SRC $$FIX $(ALWAYS)
>   echo $$LINKS > $@

$(FIX)t9n_consolidate_forms:
>   @
>   SRC="User:JeffDoozan/lists/translations/by_error/botfix_consolidate_forms"
>   FIX="--fix fix_t9n --log-fixes $@.fixes --log-matches $@.matches --config etc/autodooz-fixes.py"
>   MAX=100

>   LINKS=`$(GETLINKS) $$SRC | sort -u | wc -l`
>   [ $$LINKS -gt $$MAX ] && echo "Not running $@ too many links: $$LINKS > $$MAX" && exit 1
>   echo "Running fixer $@ on $$LINKS items from $$SRC..."
>   $(WIKIFIX) -links:$$SRC $$FIX $(ALWAYS)
>   echo $$LINKS > $@

$(FIX)t9n_remove_gendertags:
>   @
>   SRC="User:JeffDoozan/lists/translations/by_error/botfix_remove_gendertags"
>   FIX="--fix fix_t9n --log-fixes $@.fixes --log-matches $@.matches --config etc/autodooz-fixes.py"
>   MAX=100

>   LINKS=`$(GETLINKS) $$SRC | sort -u | wc -l`
>   [ $$LINKS -gt $$MAX ] && echo "Not running $@ too many links: $$LINKS > $$MAX" && exit 1
>   echo "Running fixer $@ on $$LINKS items from $$SRC..."
>   $(WIKIFIX) -links:$$SRC $$FIX $(ALWAYS)
>   echo $$LINKS > $@

$(FIX)es_missing_entry:
>   @
>   SRC="User:JeffDoozan/lists/es/forms/missing_entry_autofix"
>   FIX="--fix es_add_forms --log-fixes $@.fixes --log-matches $@.matches --config etc/autodooz-fixes.py"
>   MAX=200

>   LINKS=`$(GETLINKS) $$SRC | sort -u | wc -l`
>   [ $$LINKS -gt $$MAX ] && echo "Not running $@ too many links: $$LINKS > $$MAX" && exit 1
>   echo "Running fixer $@ on $$LINKS items from $$SRC..."
>   $(WIKIFIX) -links:$$SRC $$FIX $(ALWAYS)
>   echo $$LINKS > $@

$(FIX)es_missing_pos:
>   @
>   SRC="User:JeffDoozan/lists/es/forms/missing_pos_autofix"
>   FIX="--fix es_add_forms --log-fixes $@.fixes --log-matches $@.matches --config etc/autodooz-fixes.py"
>   MAX=300

>   LINKS=`$(GETLINKS) $$SRC | sort -u | wc -l`
>   [ $$LINKS -gt $$MAX ] && echo "Not running $@ too many links: $$LINKS > $$MAX" && exit 1
>   echo "Running fixer $@ on $$LINKS items from $$SRC..."
>   $(WIKIFIX) -links:$$SRC $$FIX $(ALWAYS)
>   echo $$LINKS > $@

$(FIX)es_missing_sense:
>   @
>   SRC="User:JeffDoozan/lists/es/forms/missing_sense_autofix"
>   FIX="--fix es_replace_pos --log-fixes $@.fixes --log-matches $@.matches --config etc/autodooz-fixes.py" # --fix es_add_forms"
>   MAX=200

>   LINKS=`$(GETLINKS) $$SRC | sort -u | wc -l`
>   [ $$LINKS -gt $$MAX ] && echo "Not running $@ too many links: $$LINKS > $$MAX" && exit 1
>   echo "Running fixer $@ on $$LINKS items from $$SRC..."
>   $(WIKIFIX) -links:$$SRC $$FIX $(ALWAYS)
>   echo $$LINKS > $@

$(FIX)es_unexpected_form:
>   @
>   SRC="User:JeffDoozan/lists/es/forms/unexpected_form_autofix"
>   FIX="--fix es_replace_pos --log-fixes $@.fixes --log-matches $@.matches --config etc/autodooz-fixes.py"
>   MAX=200

>   LINKS=`$(GETLINKS) $$SRC | sort -u | wc -l`
>   [ $$LINKS -gt $$MAX ] && echo "Not running $@ too many links: $$LINKS > $$MAX" && exit 1
>   echo "Running fixer $@ on $$LINKS items from $$SRC..."
>   $(WIKIFIX) -links:$$SRC $$FIX
>   echo $$LINKS > $@

$(FIX)es_drae_missing:
>   SRC="User:JeffDoozan/lists/es/drae_link_missing_autofix"
>   FIX="--fix es_drae_missing --log-fixes $@.fixes --log-matches $@.matches --config etc/autodooz-fixes.py"
>   MAX=500

>   LINKS=`$(GETLINKS) $$SRC | sort -u | wc -l`
>   [ $$LINKS -gt $$MAX ] && echo "Not running $@ too many links: $$LINKS > $$MAX" && exit 1
>   echo "Running fixer $@ on $$LINKS items from $$SRC..."
>   $(WIKIFIX) -links:$$SRC $$FIX
>   echo $$LINKS > $@

$(FIX)es_drae_wrong:
>   SRC="User:JeffDoozan/lists/es/drae_link_wrong_target_autofix"
>   FIX="--fix es_drae_wrong --log-fixes $@.fixes --log-matches $@.matches --config etc/autodooz-fixes.py"
>   MAX=200

>   LINKS=`$(GETLINKS) $$SRC | sort -u | wc -l`
>   [ $$LINKS -gt $$MAX ] && echo "Not running $@ too many links: $$LINKS > $$MAX" && exit 1
>   echo "Running fixer $@ on $$LINKS items from $$SRC..."
>   $(WIKIFIX) -links:$$SRC $$FIX
>   echo $$LINKS > $@

$(FIX)es_form_overrides:
>   SRC="User:JeffDoozan/lists/es/autofix_form_overrides"
>   FIX="--fix es_form_overrides --log-fixes $@.fixes --log-matches $@.matches --config etc/autodooz-fixes.py"
>   MAX=200

>   LINKS=`$(GETLINKS) $$SRC | sort -u | wc -l`
>   [ $$LINKS -gt $$MAX ] && echo "Not running $@ too many links: $$LINKS > $$MAX" && exit 1
>   echo "Running fixer $@ on $$LINKS items from $$SRC..."
>   $(WIKIFIX) -links:$$SRC $$FIX
>   echo $$LINKS > $@

$(FIX)bare_quotes:
>   SRC="User:JeffDoozan/lists/bare_quotes/fixes"
>   FIX="--fix bare_quotes --log-fixes $@.fixes --log-matches $@.matches --config etc/autodooz-fixes.py"
>   MAX=200

>   LINKS=`$(GETLINKS) $$SRC | sort -u | wc -l`
>   [ $$LINKS -gt $$MAX ] && echo "Not running $@ too many links: $$LINKS > $$MAX" && exit 1
>   echo "Running fixer $@ on $$LINKS items from $$SRC..."
>   $(WIKIFIX) -links:$$SRC $$FIX
>   echo $$LINKS > $@

$(FIX)%_list_to_col:
>   SRC="User:JeffDoozan/lists/$*/der_rel_terms/fixes"
>   FIX="--fix list_to_col --log-fixes $@.fixes --log-matches $@.matches --config etc/autodooz-fixes.py"
>   MAX=2000

>   LINKS=`$(GETLINKS) $$SRC | sort -u | wc -l`
>   [ $$LINKS -gt $$MAX ] && echo "Not running $@ too many links: $$LINKS > $$MAX" && exit 1
>   echo "Running fixer $@ on $$LINKS items from $$SRC..."
>   $(WIKIFIX) -links:$$SRC $$FIX
>   echo $$LINKS > $@

$(FIX)quote_with_bare_passage:
>   SRC="User:JeffDoozan/lists/quote_with_bare_passage/fixes"
>   FIX="--fix quote_with_bare_passage --log-fixes $@.fixes --log-matches $@.matches --config etc/autodooz-fixes.py"
>   MAX=2000

>   LINKS=`$(GETLINKS) $$SRC | sort -u | wc -l`
>   [ $$LINKS -gt $$MAX ] && echo "Not running $@ too many links: $$LINKS > $$MAX" && exit 1
>   echo "Running fixer $@ on $$LINKS items from $$SRC..."
>   $(WIKIFIX) -links:$$SRC $$FIX
>   echo $$LINKS > $@

$(FIX)sense_bylines:
>   SRC="User:JeffDoozan/lists/sense_bylines/fixes"
>   FIX="--fix sense_bylines --log-fixes $@.fixes --log-matches $@.matches --config etc/autodooz-fixes.py"
>   MAX=2000

>   LINKS=`$(GETLINKS) $$SRC | sort -u | wc -l`
>   [ $$LINKS -gt $$MAX ] && echo "Not running $@ too many links: $$LINKS > $$MAX" && exit 1
>   echo "Running fixer $@ on $$LINKS items from $$SRC..."
>   $(WIKIFIX) -links:$$SRC $$FIX
>   echo $$LINKS > $@

$(FIX)bare_ux:
>   SRC="User:JeffDoozan/lists/bare_ux/fixes"
>   FIX="--fix bare_ux --log-fixes $@.fixes --log-matches $@.matches --config etc/autodooz-fixes.py"
>   MAX=200

>   LINKS=`$(GETLINKS) $$SRC | sort -u | wc -l`
>   [ $$LINKS -gt $$MAX ] && echo "Not running $@ too many links: $$LINKS > $$MAX" && exit 1
>   echo "Running fixer $@ on $$LINKS items from $$SRC..."
>   $(WIKIFIX) -links:$$SRC $$FIX
>   echo $$LINKS > $@

$(FIX)punc_refs:
>   $(WIKIFIX) --fix punc_refs -namespace:0 -search:"insource:/ref[ \n]*>[ ]*[,.;]/"
>   $(WIKIFIX) --fix punc_refs -namespace:0 -search:"insource:/\<ref[^>]*\/[ ]*\>[ ]*[.,;]/"

$(FIX)rq_templates: $(BUILDDIR)/rq_template_params.json
>   $(WIKIFIX) --fix rq_template -search:"insource:/\{quote-/ -insource:/quote-meta/ prefix:Template:RQ:"
>   $(WIKIFIX) --fix rq_template -search:"insource:/allowparams[ ]*=[ ]*\*/ prefix:Template:RQ:"

$(FIX)template_params: $(BUILDDIR)/template_data.json
>   SRC="User:JeffDoozan/lists/template_params/fixes"
>   FIX="--fix bad_template_params --log-fixes $@.fixes --log-matches $@.matches --config etc/autodooz-fixes.py"
>   MAX=2000

>   LINKS=`$(GETLINKS) $$SRC | sort -u | wc -l`
>   [ $$LINKS -gt $$MAX ] && echo "Not running $@ too many links: $$LINKS > $$MAX" && exit 1
>   echo "Running fixer $@ on $$LINKS items from $$SRC..."
>   $(WIKIFIX) -links:$$SRC $$FIX
>   echo $$LINKS > $@

$(FIX)missing_taxlinks: $(BUILDDIR)/local_taxons.tsv $(BUILDDIR)/external_taxons.tsv
>   SRC="User:JeffDoozan/lists/missing_taxlink/fixes"
>   FIX="--fix missing_taxlinks --log-fixes $@.fixes --log-matches $@.matches --config etc/autodooz-fixes.py"
>   MAX=200000

>   LINKS=`$(GETLINKS) $$SRC | sort -u | wc -l`
>   [ $$LINKS -gt $$MAX ] && echo "Not running $@ too many links: $$LINKS > $$MAX" && exit 1
>   echo "Running fixer $@ on $$LINKS items from $$SRC..."
>   $(WIKIFIX) -links:$$SRC $$FIX
>   echo $$LINKS > $@



lists: /var/local/wikt/wikt.sentences.tgz /var/local/wikt/spa.sentences.tgz $(patsubst %,$(LIST)%,es_drae_errors es_missing_drae es_forms_with_data es_maybe_forms es_missing_lemmas es_missing_ety es_untagged_demonyms es_duplicate_passages es_mismatched_passages es_with_synonyms es_verbs_missing_type ismo_ista es_coord_terms es_usually_plural es_split_verb_data es_drae_mismatched_genders es_form_overrides fr_missing_lemmas fr_missing_tlfi pt_with_synonyms mismatched_headlines quote_with_bare_passage sense_bylines bare_ux unbalanced_delimiters section_header_errors section_level_errors section_order_errors t9n_problems convert_list_to_col bad_template_params es_missing_forms section_stats missing_taxlinks) # slower stuff last

# Fixes that are safe to run automatically and without supervision
autofixes: $(patsubst %,$(FIX)%,fr_missing_tlfi t9n_consolidate_forms t9n_remove_gendertags es_drae_wrong es_drae_missing section_headers section_levels section_order es_form_overrides cs_list_to_col es_list_to_col mt_list_to_col pl_list_to_col zlw-opl_list_to_col quote_with_bare_passage sense_bylines bare_ux punc_refs rq_templates)

# Fixes that may make mistakes and need human supervision
otherfixes: $(patsubst %,$(FIX)%,es_missing_entry es_missing_pos es_missing_sense es_unexpected_form template_params)

# Fixes that need fun_replace and not wikifix
oldfixes: $(patsubst %,$(FIX)%,es_syns pt_syns)

allfixes: autofixes otherfixes oldfixes

all: lists

.PHONY: all lists autofixes otherfixes oldfixes allfixes
