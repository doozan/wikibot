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
NGRAMDATA := ../ngram_data
BUILDDIR := $(SPANISH_DATA)/$(DATETAG_PRETTY)
PYPATH := PYTHONPATH=$(BUILDDIR)

DUMP_LEMMAS := $(PYPATH) $(BUILDDIR)/enwiktionary_wordlist/scripts/dump_lemmas

WIKI2TEXT := $(PYPATH) scripts/wiki2text
WIKIGREP := $(PYPATH) scripts/wikigrep
WIKISEARCH := $(PYPATH) scripts/wikisearch
WIKISORT := $(PYPATH) scripts/wikisort
GETLINKS := $(PYPATH) scripts/getlinks

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
LIST_SPLIT_NOUN_PLURALS := $(PYPATH) ./list_split_noun_plurals.py
LIST_SPLIT_VERB_DATA := $(PYPATH) ./list_split_verb_data.py

EXTERNAL := ../..
PUT := $(EXTERNAL)/put.py
FUN_REPLACE := $(EXTERNAL)/fun_replace.py
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

force: ;
# force used per https://www.gnu.org/software/make/manual/html_node/Overriding-Makefiles.html

$(BUILDDIR)/wiki.pages: $(BUILDDIR)/enwiktionary-$(DATETAG)-pages-articles.xml.bz2
>   @echo "Making $@..."
>   bzcat $< | grep -o '<title>[^<:/]*</title>' | sed 's|<title>\(.*\)</title>|\1|' > $@

$(BUILDDIR)/%.sortorder: $(BUILDDIR)/%.frequency.csv
>   @echo "Making $@..."
>   cat $< | tail -n +2 | grep -v NODEF | cut -d "," -f 2 > $@

$(BUILDDIR)/es-en.enwikt.allpages: $(BUILDDIR)/es-en.enwikt.txt.bz2
>   @echo "Making $@..."
>   $(WIKIGREP) $< "=\s*Spanish\s*=" | cut -d ":" -f 1 | sort -u > $@

$(BUILDDIR)/fr-en.enwikt.allpages: $(BUILDDIR)/fr-en.enwikt.txt.bz2
>   @echo "Making $@..."
>   $(WIKIGREP) $< "=\s*French\s*=" | cut -d ":" -f 1 | sort -u > $@

$(BUILDDIR)/%.lemmas: $(BUILDDIR)/%.data-full
>   @echo "Making $@..."
>   $(DUMP_LEMMAS) $< | sort > $@

$(BUILDDIR)/%.with_etymology: $(BUILDDIR)/%.data-full
>   @echo "Making $@..."
>   cat $<| perl -ne 'if (/^_____$$/) { undef $$entry } elsif (not defined $$entry) { $$entry = $$_ } elsif (/etymology:/) { print($$entry) }' | sort -u > $@

$(BUILDDIR)/%.lemmas_without_etymology: $(BUILDDIR)/%.lemmas $(BUILDDIR)/%.with_etymology
>   @echo "Making $@..."
>   comm -23 $(BUILDDIR)/$*.lemmas $(BUILDDIR)/$*.with_etymology > $@

# Lists

#../wikibot/src/list_t9n_problems.py
$(LIST)t9n_problems: $(BUILDDIR)/translations.bz2 $(BUILDDIR)/es-en.enwikt.allforms.csv
>   @echo "Running $@..."

>   $(LIST_T9N_PROBLEMS) --trans $< --allforms $(BUILDDIR)/es-en.enwikt.allforms.csv $(SAVE)
>   touch $@

#../wikibot/src/make_section_stats.py
$(LIST)section_stats: $(BUILDDIR)/enwiktionary-$(DATETAG)-pages-articles.xml.bz2
>   @echo "Running $@..."
# --tag $(DATETAG)
>   $(MAKE_SECTION_STATS) $< $(SAVE)
>   touch $@

$(LIST)forms_with_data: $(BUILDDIR)/enwiktionary-$(DATETAG)-pages-articles.xml.bz2
#../wikibot/src/list_forms_with_data.py
>   @echo "Running $@..."
>   $(LIST_FORMS_WITH_DATA) --xml $< $(SAVE)
>   touch $@

$(LIST)mismatched_headlines: $(BUILDDIR)/enwiktionary-$(DATETAG)-pages-articles.xml.bz2
#../wikibot/src/list_mismatched_headlines.py
>   @echo "Running $@..."

>   $(LIST_MISMATCHED_HEADLINES) --xml $<  $(SAVE)
>   touch $@

$(LIST)maybe_forms: $(BUILDDIR)/es-en.enwikt.data-full
#../wikibot/src/list_maybe_forms.py
>   @echo "Running $@..."

>   $(LIST_MAYBE_FORMS) --wordlist $< $(SAVE)
>   touch $@


$(LIST)missing_forms: $(BUILDDIR)/es-en.enwikt.allforms.csv $(BUILDDIR)/es-en.enwikt.data-full $(BUILDDIR)/wiki.pages $(BUILDDIR)/es-en.enwikt.txt.bz2
#../wikibot/src/list_missing_forms.py
>   echo "Running $@..."
>   $(LIST_MISSING_FORMS) --allforms $(BUILDDIR)/es-en.enwikt.allforms.csv --allpages $(BUILDDIR)/wiki.pages --articles $(BUILDDIR)/es-en.enwikt.txt.bz2 $(BUILDDIR)/es-en.enwikt.data-full $(SAVE)
>   touch $@

$(LIST)fr_missing_lemmas: $(BUILDDIR)/fr-en.enwikt.lemmas $(BUILDDIR)/fr-en.enwikt.allpages $(TLFI_LEMMAS)
>   @echo "Running $@..."
>   DEST="User:JeffDoozan/lists/fr_forms_with_tlfi_lemmata"
>   SUMMARY="French entries where we have forms but the TLFi has a lemma"
>   echo "still Running $@..."

>   comm -23 $(BUILDDIR)/fr-en.enwikt.allpages $(BUILDDIR)/fr-en.enwikt.lemmas > $@.formonly
>   comm -12 $@.formonly $(TLFI_LEMMAS) \
>   | awk '{print "; [["$$0"#French|"$$0"]] [https://www.cnrtl.fr/definition/"$$0" TLFi]"}' \
>   > $@.wiki.base

>   COUNT=`wc -l $@.wiki.base | cut -d " " -f 1`
>   echo "$$SUMMARY as of $(DATETAG_PRETTY) ($$COUNT entries)" > $@.wiki
>   cat $@.wiki.base >> $@.wiki

>   $(PUT) -textonly -force "-title:$$DEST" -file:$@.wiki -summary:"Updated with $(DATETAG_PRETTY) data"
>   rm -f $@.formonly $@.wiki.base
>   mv $@.wiki $@

$(LIST)es_missing_lemmas: $(BUILDDIR)/es-en.enwikt.lemmas $(BUILDDIR)/es-es.drae.lemmas $(BUILDDIR)/es-es.drae.sortorder $(BUILDDIR)/es-en.enwikt.allpages
>   @echo "Running $@..."
>   DEST="User:JeffDoozan/lists/es_forms_with_drae_lemmata"
>   SUMMARY="Spanish entries where we have forms but the DRAE has a lemma"

>   comm -23 $(BUILDDIR)/es-en.enwikt.allpages $(BUILDDIR)/es-en.enwikt.lemmas > $@.formonly
>   comm -12 $@.formonly $(BUILDDIR)/es-es.drae.lemmas > $@.sorted_az
>   $(WIKISORT) $(BUILDDIR)/es-es.drae.sortorder $@.sorted_az \
>   | awk '{print "; [["$$0"#Spanish|"$$0"]] [https://dle.rae.es/"$$0" drae]"}'\
>   > $@.wiki.base

>   COUNT=`wc -l $@.wiki.base | cut -d " " -f 1`
>   echo "$$SUMMARY as of $(DATETAG_PRETTY) ($$COUNT entries); sorted by lemma frequency" > $@.wiki
>   cat $@.wiki.base >> $@.wiki

>   $(PUT) -textonly -force "-title:$$DEST" -file:$@.wiki -summary:"Updated with $(DATETAG_PRETTY) data"
>   rm -f $@.formonly $@.sorted_az $@.wiki.base
>   mv $@.wiki $@

$(LIST)pl_missing_ety: $(BUILDDIR)/pl-en.enwikt.lemmas_without_etymology
>   @echo "Running $@..."
>   DEST="User:JeffDoozan/lists/pl/missing_ety"
>   SUMMARY="Lemmas without etymology info"

>   cat $< | awk '{print ": [["$$0"#Polish|"$$0"]]"}' > $@.wiki.base

>   COUNT=`wc -l $@.wiki.base | cut -d " " -f 1`
>   echo "$$SUMMARY as of $(DATETAG_PRETTY) ($$COUNT entries)" > $@.wiki
>   cat $@.wiki.base >> $@.wiki

>   $(PUT) -textonly -force "-title:$$DEST" -file:$@.wiki -summary:"Updated with $(DATETAG_PRETTY) data"
>   rm -f $@.wiki.base  $@.sorted_az
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
>   rm -f $@.wiki.base  $@.sorted_az
>   mv $@.wiki $@

$(LIST)fr_missing_tlfi: $(BUILDDIR)/fr-en.enwikt.txt.bz2 $(BUILDDIR)/fr-en.enwikt.lemmas $(TLFI_LEMMAS)
>   @echo "Running $@..."
>   DEST="User:JeffDoozan/lists/fr_missing_tlfi"
>   SUMMARY="Entries missing a link to TLFI"

>   $(WIKIGREP) $< "{{R:TLFi" | cut -d ":" -f 1 | sort -u > $@.with_tlfi
>   comm -23 $(BUILDDIR)/fr-en.enwikt.lemmas $@.with_tlfi > $@.without_tlfi
>   comm -12 $@.without_tlfi $(TLFI_LEMMAS) \
>   | grep -v "^.$$" \
>   | awk '{ print "; [["$$0"#French|"$$0"]]" }' \
>   > $@.wiki.base

>   COUNT=`wc -l $@.wiki.base | cut -d " " -f 1`
>   echo "$$SUMMARY as of $(DATETAG_PRETTY) ($$COUNT entries)" > $@.wiki
>   cat $@.wiki.base >> $@.wiki

>   $(PUT) -textonly -force "-title:$$DEST" -file:$@.wiki -summary:"Updated with $(DATETAG_PRETTY) data"
>   rm -f $@.with_tlf $@.without_tlfi $@.wiki.base
>   mv $@.wiki $@

$(LIST)es_missing_drae: $(BUILDDIR)/es-en.enwikt.txt.bz2 $(BUILDDIR)/es-en.enwikt.lemmas $(BUILDDIR)/es-es.drae.lemmas
>   @echo "Running $@..."
>   DEST="User:JeffDoozan/lists/es_missing_drae"
>   SUMMARY="Entries missing a link to DRAE"

>   $(WIKIGREP) $< "{{R:(D)?RAE" | cut -d ":" -f 1 | sort -u > $@.with_drae
>   comm -23 $(BUILDDIR)/es-en.enwikt.lemmas $@.with_drae > $@.without_drae
>   comm -12 $@.without_drae $(BUILDDIR)/es-es.drae.lemmas \
>   | grep -v "^.$$" \
>   | awk '{ print "; [["$$0"#Spanish|"$$0"]]" }' \
>   > $@.wiki.base

>   COUNT=`wc -l $@.wiki.base | cut -d " " -f 1`
>   echo "$$SUMMARY as of $(DATETAG_PRETTY) ($$COUNT entries)" > $@.wiki
>   cat $@.wiki.base >> $@.wiki

>   $(PUT) -textonly -force "-title:$$DEST" -file:$@.wiki -summary:"Updated with $(DATETAG_PRETTY) data"
>   rm -f $@.wiki.base $@.with_drae $@.without_drae
>   mv $@.wiki $@

$(LIST)es_untagged_demonyms: $(BUILDDIR)/es-en.enwikt.txt.bz2
>   @echo "Running $@..."
>   DEST="User:JeffDoozan/lists/es_untagged_demonyms"
>   SUMMARY="Entries that may be untagged demonyms"
>   $(WIKISEARCH) $< \
>       '^# .*(((one|body|person) from)|((native|resident|inhabitant) of|of or relat))' \
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
>   rm -f $@.wiki.base
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
>   rm -f $@.wiki.base $@.with_passage
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
>   rm -f $@.wiki.base $@.with_passage
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
>   rm -f $@.wiki.base
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
>   rm -f $@.wiki.base
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
>   rm -f $@.wiki.base $@.unsorted
>   mv $@.wiki $@

$(LIST)ismo_ista: $(BUILDDIR)/es-en.enwikt.allforms.csv $(BUILDDIR)/es-en.enwikt.txt.bz2
>   @echo "Running $@..."

>   $(LIST_ISMO_ISTA) $(SAVE) --allforms $< $(BUILDDIR)/es-en.enwikt.txt.bz2
>   touch $@

IGNORE_COORD2 := $(patsubst %,--ignore2 %,el la lo las los un una y i o u a al de del en se me te su mi tu nos os sus tus mis es que no en ha he has hemos había habían por con sin)
$(LIST)es_coord_terms: $(BUILDDIR)/es-en.enwikt.allforms.csv $(BUILDDIR)/es-1-1950.ngprobs $(patsubst %, $(NGRAMDATA)/spa/%-1950.coord,2 3 4)
>   @echo "Running $@..."

>   echo $(LIST_COORD_TERMS) --min-count 1000 --min-percent 25 --allforms $< $(SAVE) --ngprobs $(BUILDDIR)/es-1-1950.ngprobs $(IGNORE_COORD2) --coord2 $(NGRAMDATA)/spa/2-1950.coord --coord3 $(NGRAMDATA)/spa/3-1950.coord --coord4 $(NGRAMDATA)/spa/4-1950.coord
>   touch $@

$(LIST)es_usually_plural:  $(BUILDDIR)/es-en.enwikt.data $(BUILDDIR)/es-1-1950.ngprobs
>   @echo "Running $@..."

>   $(LIST_USUALLY_PLURAL) $(SAVE) --dictionary $< --ngprobs $(BUILDDIR)/es-1-1950.ngprobs
>   touch $@

$(LIST)es_split_verb_data:  $(BUILDDIR)/es-en.enwikt.data
>   @echo "Running $@..."

>   $(LIST_SPLIT_VERB_DATA) $(SAVE) --dictionary $<
>   touch $@

$(LIST)es_split_noun_plurals:  $(BUILDDIR)/es-en.enwikt.data
>   @echo "Running $@..."

>   $(LIST_SPLIT_NOUN_PLURALS) $(SAVE) --dictionary $<
>   touch $@

# Fixes
$(FIX)fr_missing_tlfi:
>   @
>   FIX="-fix:add_tlfi"
>   SRC="User:JeffDoozan/lists/fr_missing_tlfi"
>   MAX=500

>   LINKS=`$(GETLINKS) $$SRC | sort -u | wc -l`
>   [ $$LINKS -gt $$MAX ] && echo "Not running $@ too many links: $$LINKS > $$MAX" && exit
>   echo "Running fixer $@ on $$LINKS items from $$SRC..."
>   $(FUN_REPLACE) -links:$$SRC $$FIX $(ALWAYS)
>   echo $$LINKS > $@

$(FIX)es_missing_drae:
>   @
>   FIX="-fix:add_drae"
>   SRC="User:JeffDoozan/lists/es_missing_drae"
>   MAX=500

>   LINKS=`$(GETLINKS) $$SRC | sort -u | wc -l`
>   [ $$LINKS -gt $$MAX ] && echo "Not running $@ too many links: $$LINKS > $$MAX" && exit
>   echo "Running fixer $@ on $$LINKS items from $$SRC..."
>   $(FUN_REPLACE) -links:$$SRC $$FIX $(ALWAYS)
>   echo $$LINKS > $@

# TODO: some sort of list maker to check if they can be auto fixed
$(FIX)es_syns:
>   @
>   FIX="-fix:simple_nyms --lang:es --wordlist:$(SPANISH_DATA)/es-en.data --sections:Synonyms"
>   SRC="User:JeffDoozan/lists/es_with_synonyms"
>   MAX=200

>   LINKS=`$(GETLINKS) $$SRC | sort -u | wc -l`
>   [ $$LINKS -gt $$MAX ] && echo "Not running $@ too many links: $$LINKS > $$MAX" && exit
>   echo "Running fixer $@ on $$LINKS items from $$SRC..."
>   $(FUN_REPLACE) -links:$$SRC $$FIX $(ALWAYS)
>   echo $$LINKS > $@

$(FIX)pt_syns:
>   @
>   FIX="-fix:simple_nyms --lang:pt --wordlist:$(BUILDDIR)/pt-en.enwikt.data-full --sections:Synonyms"
>   SRC="User:JeffDoozan/lists/Portuguese_with_Synonyms"
>   MAX=1000

>   LINKS=`$(GETLINKS) $$SRC | sort -u | wc -l`
>   [ $$LINKS -gt $$MAX ] && echo "Not running $@ too many links: $$LINKS > $$MAX" && exit
>   echo "Running fixer $@ on $$LINKS items from $$SRC..."
>   $(FUN_REPLACE) -links:$$SRC $$FIX $(ALWAYS)
>   echo $$LINKS > $@

$(FIX)autofix_title:
>   @
>   FIX="-fix:cleanup_sections"
>   SRC="User:JeffDoozan/lists/autofix_title"
>   MAX=500

>   LINKS=`$(GETLINKS) $$SRC | sort -u | wc -l`
>   [ $$LINKS -gt $$MAX ] && echo "Not running $@ too many links: $$LINKS > $$MAX" && exit
>   echo "Running fixer $@ on $$LINKS items from $$SRC..."
>   $(FUN_REPLACE) -links:$$SRC $$FIX $(ALWAYS)
>   echo $$LINKS > $@

$(FIX)autofix_numbered_pos:
>   @
>   FIX="-fix:cleanup_sections"
>   SRC="User:JeffDoozan/lists/autofix_numbered_pos"
>   MAX=200

>   LINKS=`$(GETLINKS) $$SRC | sort -u | wc -l`
>   [ $$LINKS -gt $$MAX ] && echo "Not running $@ too many links: $$LINKS > $$MAX" && exit
>   echo "Running fixer $@ on $$LINKS items from $$SRC..."
>   $(FUN_REPLACE) -links:$$SRC $$FIX $(ALWAYS)
>   echo $$LINKS > $@

$(FIX)autofix_missing_references:
>   @
>   SRC="User:JeffDoozan/lists/autofix_missing_references"
>   FIX="-fix:cleanup_sections"
>   MAX=200

>   LINKS=`$(GETLINKS) $$SRC | sort -u | wc -l`
>   [ $$LINKS -gt $$MAX ] && echo "Not running $@ too many links: $$LINKS > $$MAX" && exit
>   echo "Running fixer $@ on $$LINKS items from $$SRC..."
>   $(FUN_REPLACE) -links:$$SRC $$FIX $(ALWAYS)
>   echo $$LINKS > $@

$(FIX)autofix_bad_l2:
>   @
>   SRC="User:JeffDoozan/lists/autofix_bad_l2"
>   FIX="-fix:cleanup_sections"
>   MAX=200

>   LINKS=`$(GETLINKS) $$SRC | sort -u | wc -l`
>   [ $$LINKS -gt $$MAX ] && echo "Not running $@ too many links: $$LINKS > $$MAX" && exit
>   echo "Running fixer $@ on $$LINKS items from $$SRC..."
>   $(FUN_REPLACE) -links:$$SRC $$FIX $(ALWAYS)
>   echo $$LINKS > $@

$(FIX)botfix_consolidate_forms:
>   @
>   SRC="User:JeffDoozan/lists/translations/by_error/botfix_consolidate_forms"
>   FIX="-fix:fix_t9n --allforms:$(SPANISH_DATA)/es_allforms.csv"
>   MAX=100

>   LINKS=`$(GETLINKS) $$SRC | sort -u | wc -l`
>   [ $$LINKS -gt $$MAX ] && echo "Not running $@ too many links: $$LINKS > $$MAX" && exit
>   echo "Running fixer $@ on $$LINKS items from $$SRC..."
>   $(FUN_REPLACE) -links:$$SRC $$FIX $(ALWAYS)
>   echo $$LINKS > $@

$(FIX)botfix_remove_gendertags:
>   @
>   SRC="User:JeffDoozan/lists/translations/by_error/botfix_remove_gendertags"
>   FIX="-fix:fix_t9n --allforms:$(SPANISH_DATA)/es_allforms.csv"
>   MAX=100

>   LINKS=`$(GETLINKS) $$SRC | sort -u | wc -l`
>   [ $$LINKS -gt $$MAX ] && echo "Not running $@ too many links: $$LINKS > $$MAX" && exit
>   echo "Running fixer $@ on $$LINKS items from $$SRC..."
>   $(FUN_REPLACE) -links:$$SRC $$FIX $(ALWAYS)
>   echo $$LINKS > $@

$(FIX)es_missing_entry:
>   @
>   SRC="User:JeffDoozan/lists/es/forms/missing_entry_autofix"
>   FIX="-fix:es_add_forms --lang:es --allforms:$(SPANISH_DATA)/es_allforms.csv --wordlist:$(SPANISH_DATA)/es-en.data"
>   MAX=200

>   LINKS=`$(GETLINKS) $$SRC | sort -u | wc -l`
>   [ $$LINKS -gt $$MAX ] && echo "Not running $@ too many links: $$LINKS > $$MAX" && exit
>   echo "Running fixer $@ on $$LINKS items from $$SRC..."
>   $(FUN_REPLACE) -links:$$SRC $$FIX $(ALWAYS)
>   echo $$LINKS > $@

$(FIX)es_missing_pos:
>   @
>   SRC="User:JeffDoozan/lists/es/forms/missing_pos_autofix"
>   FIX="-fix:es_add_forms --lang:es --allforms:$(SPANISH_DATA)/es_allforms.csv --wordlist:$(SPANISH_DATA)/es-en.data"
>   MAX=300

>   LINKS=`$(GETLINKS) $$SRC | sort -u | wc -l`
>   [ $$LINKS -gt $$MAX ] && echo "Not running $@ too many links: $$LINKS > $$MAX" && exit
>   echo "Running fixer $@ on $$LINKS items from $$SRC..."
>   $(FUN_REPLACE) -links:$$SRC $$FIX $(ALWAYS)
>   echo $$LINKS > $@

$(FIX)es_missing_sense:
>   @
>   SRC="User:JeffDoozan/lists/es/forms/missing_sense_autofix"
>   FIX="-fix:es_replace -fix:es_add_forms --lang:es --wordlist:$(SPANISH_DATA)/es-en.data --allforms:$(SPANISH_DATA)/es_allforms.csv --pos:v,n,adj"
>   MAX=1000

>   LINKS=`$(GETLINKS) $$SRC | sort -u | wc -l`
>   [ $$LINKS -gt $$MAX ] && echo "Not running $@ too many links: $$LINKS > $$MAX" && exit
>   echo "Running fixer $@ on $$LINKS items from $$SRC..."
>   $(FUN_REPLACE) -links:$$SRC $$FIX $(ALWAYS)
>   echo $$LINKS > $@



# not safe to run automatically
$(FIX)misplaced_translations_section:
>   @
>   SRC="User:JeffDoozan/lists/translations/by_error/outside_pos"
>   FIX="-fix:cleanup_sections"
>   MAX=300

>   LINKS=`$(GETLINKS) $$SRC | sort -u | wc -l`
>   [ $$LINKS -gt $$MAX ] && echo "Not running $@ too many links: $$LINKS > $$MAX" && exit
>   echo "Running fixer $@ on $$LINKS items from $$SRC..."
>   $(FUN_REPLACE) -links:$$SRC $$FIX
>   echo $$LINKS > $@

$(FIX)misnamed_references_section:
>   @
>   SRC="User:JeffDoozan/lists/misnamed_references_section"
>   FIX="-fix:cleanup_sections"
>   MAX=200

>   LINKS=`$(GETLINKS) $$SRC | sort -u | wc -l`
>   [ $$LINKS -gt $$MAX ] && echo "Not running $@ too many links: $$LINKS > $$MAX" && exit
>   echo "Running fixer $@ on $$LINKS items from $$SRC..."
>   $(FUN_REPLACE) -links:$$SRC $$FIX
>   echo $$LINKS > $@

$(FIX)autofix_empty_section:
>   @
>   SRC="User:JeffDoozan/lists/autofix_empty_section"
>   FIX="-fix:cleanup_sections"
>   MAX=200

>   LINKS=`$(GETLINKS) $$SRC | sort -u | wc -l`
>   [ $$LINKS -gt $$MAX ] && echo "Not running $@ too many links: $$LINKS > $$MAX" && exit
>   echo "Running fixer $@ on $$LINKS items from $$SRC..."
>   $(FUN_REPLACE) -links:$$SRC $$FIX
>   echo $$LINKS > $@

$(FIX)es_unexpected_form:
>   @
>   SRC="User:JeffDoozan/lists/es/forms/unexpected_form_autofix"
>   FIX="-fix:es_replace -fix:es_remove_forms --lang:es --wordlist:$(SPANISH_DATA)/es-en.data --allforms:$(SPANISH_DATA)/es_allforms.csv --pos:v,n,adj"
>   MAX=200

>   LINKS=`$(GETLINKS) $$SRC | sort -u | wc -l`
>   [ $$LINKS -gt $$MAX ] && echo "Not running $@ too many links: $$LINKS > $$MAX" && exit
>   echo "Running fixer $@ on $$LINKS items from $$SRC..."
>   $(FUN_REPLACE) -links:$$SRC $$FIX
>   echo $$LINKS > $@


all: lists

#data: enwiktionary-$(DATETAG)-pages-articles.xml.bz2 es-en.txt.bz2 pt-en.txt.bz2 fr-en.txt.bz2 spanish_data/es-en.data-full spanish_data/es-en.data es.allpages fr-en.data pt-en.data $(BUILDDIR)/wiki.pages translations.bz2 es.sortorder fr.lemmas fr.allpages es.lemmas drae.lemmas drae.with_etymology es.with_etymology es.lemmas_without_etymology

lists: $(patsubst %,$(LIST)%,t9n_problems section_stats mismatched_headlines maybe_forms missing_forms fr_missing_lemmas es_missing_lemmas es_missing_ety fr_missing_tlfi es_missing_drae es_untagged_demonyms es_duplicate_passages es_with_synonyms pt_with_synonyms es_verbs_missing_type forms_with_data ismo_ista es_mismatched_passages es_usually_plural es_split_verb_data es_split_noun_plurals)

autofixes: $(FIX)fr_missing_tlfi $(FIX)es_missing_drae $(FIX)es_syns $(FIX)pt_syns $(FIX)autofix_title $(FIX)autofix_numbered_pos $(FIX)misplaced_translations_section $(FIX)autofix_missing_references $(FIX)autofix_bad_l2 $(FIX)botfix_consolidate_forms $(FIX)botfix_remove_gendertags
allfixes: autofixes $(FIX)es_missing_entry $(FIX)es_missing_pos $(FIX)es_missing_sense $(FIX)es_unexpected_form

.PHONY: all data lists autofixes allfixes
