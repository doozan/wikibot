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

EXTERNAL := ../..
PUT := $(EXTERNAL)/put.py
REPLACE := $(EXTERNAL)/replace.py
FUN_REPLACE := $(EXTERNAL)/fun_replace.py
TLFI_LEMMAS := $(EXTERNAL)/tlfi.lemmas


# prefix for list files
LIST := $(BUILDDIR)/.list.
FIX := $(BUILDDIR)/.fix.

SAVE := --save "Updated with $(DATETAG_PRETTY) data"

# Call into the spanish_data makefile to build anything not declared here
$(BUILDDIR)/%.data-full $(BUILDDIR)/%.data $(BUILDDIR)/%.frequency.csv: force
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

>   $(WIKISEARCH) $< '^# .*(((one|body|person) from)|((native|resident|inhabitant) of|of or relat))' --not Demonyms \
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

>   $(WIKIGREP) $< "passage=" | grep -v "t=" | cut -d ":" -f 1 > $@.with_passage
>   $(LIST_DUPLICATE_PASSAGES) $(BUILDDIR)/es-en.enwikt.txt.bz2 $@.with_passage > $@.wiki.base

>   COUNT=`wc -l $@.wiki.base | cut -d " " -f 1`
>   echo "$$SUMMARY as of $(DATETAG_PRETTY) ($$COUNT entries)" > $@.wiki
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


# Fixes
$(FIX)fr_missing_tlfi: $(LIST)fr_missing_tlfi
>   @
>   FIX="-fix:add_tlfi"
>   SRC="User:JeffDoozan/lists/fr_missing_tlfi"
>   MAX=500

>   LINKS=`$(GETLINKS) $$SRC | sort -u | wc -l`
>   [ $$LINKS -gt $$MAX ] && echo "Not running $@ too many links: $$LINKS > $$MAX" && exit
>   echo "Running fixer $@ on $$LINKS items from $$SRC..."
>   $(REPLACE) -links:$$SRC $$FIX $(ALWAYS)
>   echo $$LINKS > $@

$(FIX)es_missing_drae: $(LIST)es_missing_drae
>   @
>   FIX="-fix:add_drae"
>   SRC="User:JeffDoozan/lists/es_missing_drae"
>   MAX=500

>   LINKS=`$(GETLINKS) $$SRC | sort -u | wc -l`
>   [ $$LINKS -gt $$MAX ] && echo "Not running $@ too many links: $$LINKS > $$MAX" && exit
>   echo "Running fixer $@ on $$LINKS items from $$SRC..."
>   $(REPLACE) -links:$$SRC $$FIX $(ALWAYS)
>   echo $$LINKS > $@

# TODO: some sort of list maker to check if they can be auto fixed
$(FIX)es_syns: $(BUILDDIR)/es-en.enwikt.txt.bz2 $(BUILDDIR)/es-en.enwikt.data
>   @
>   FIX="-fix:es_simple_nyms"
>   SRC="User:JeffDoozan/lists/es_with_synonyms"
>   MAX=200

>   LINKS=`$(GETLINKS) $$SRC | sort -u | wc -l`
>   [ $$LINKS -gt $$MAX ] && echo "Not running $@ too many links: $$LINKS > $$MAX" && exit
>   echo "Running fixer $@ on $$LINKS items from $$SRC..."
>   $(FUN_REPLACE) -links:$$SRC $$FIX $(ALWAYS)
>   echo $$LINKS > $@

$(FIX)pt_syns: $(BUILDDIR)/pt-en.enwikt.data
>   @
>   FIX="-fix:pt_simple_nyms"
>   SRC="User:JeffDoozan/lists/Portuguese_with_Synonyms"
>   MAX=1000

>   LINKS=`$(GETLINKS) $$SRC | sort -u | wc -l`
>   [ $$LINKS -gt $$MAX ] && echo "Not running $@ too many links: $$LINKS > $$MAX" && exit
>   echo "Running fixer $@ on $$LINKS items from $$SRC..."
>   $(FUN_REPLACE) -links:$$SRC $$FIX $(ALWAYS)
>   echo $$LINKS > $@

$(FIX)autofix_title: $(LIST)section_stats
>   @
>   FIX="-fix:cleanup_sections"
>   SRC="User:JeffDoozan/lists/autofix_title"
>   MAX=300

>   LINKS=`$(GETLINKS) $$SRC | sort -u | wc -l`
>   [ $$LINKS -gt $$MAX ] && echo "Not running $@ too many links: $$LINKS > $$MAX" && exit
>   echo "Running fixer $@ on $$LINKS items from $$SRC..."
>   $(FUN_REPLACE) -links:$$SRC $$FIX $(ALWAYS)
>   echo $$LINKS > $@

$(FIX)autofix_numbered_pos: $(LIST)section_stats
>   @
>   FIX="-fix:cleanup_sections"
>   SRC="User:JeffDoozan/lists/autofix_numbered_pos"
>   MAX=200

>   LINKS=`$(GETLINKS) $$SRC | sort -u | wc -l`
>   [ $$LINKS -gt $$MAX ] && echo "Not running $@ too many links: $$LINKS > $$MAX" && exit
>   echo "Running fixer $@ on $$LINKS items from $$SRC..."
>   $(FUN_REPLACE) -links:$$SRC $$FIX $(ALWAYS)
>   echo $$LINKS > $@

$(FIX)misplaced_translations_section: $(LIST)section_stats
>   @
>   SRC="User:JeffDoozan/lists/translations/by_error/outside_pos"
>   FIX="-fix:cleanup_sections"
>   MAX=300

>   LINKS=`$(GETLINKS) $$SRC | sort -u | wc -l`
>   [ $$LINKS -gt $$MAX ] && echo "Not running $@ too many links: $$LINKS > $$MAX" && exit
>   echo "Running fixer $@ on $$LINKS items from $$SRC..."
>   $(FUN_REPLACE) -links:$$SRC $$FIX $(ALWAYS)
>   echo $$LINKS > $@

$(FIX)autofix_missing_references: $(LIST)section_stats
>   @
>   SRC="User:JeffDoozan/lists/autofix_missing_references"
>   FIX="-fix:cleanup_sections"
>   MAX=200

>   LINKS=`$(GETLINKS) $$SRC | sort -u | wc -l`
>   [ $$LINKS -gt $$MAX ] && echo "Not running $@ too many links: $$LINKS > $$MAX" && exit
>   echo "Running fixer $@ on $$LINKS items from $$SRC..."
>   $(FUN_REPLACE) -links:$$SRC $$FIX $(ALWAYS)
>   echo $$LINKS > $@

$(FIX)autofix_bad_l2: $(LIST)section_stats
>   @
>   SRC="User:JeffDoozan/lists/autofix_bad_l2"
>   FIX="-fix:cleanup_sections"
>   MAX=200

>   LINKS=`$(GETLINKS) $$SRC | sort -u | wc -l`
>   [ $$LINKS -gt $$MAX ] && echo "Not running $@ too many links: $$LINKS > $$MAX" && exit
>   echo "Running fixer $@ on $$LINKS items from $$SRC..."
>   $(FUN_REPLACE) -links:$$SRC $$FIX $(ALWAYS)
>   echo $$LINKS > $@

$(FIX)botfix_consolidate_forms: $(LIST)t9n_problems
>   @
>   SRC="User:JeffDoozan/lists/translations/by_error/botfix_consolidate_forms"
>   FIX="-fix:fix_t9n"
>   MAX=300

>   LINKS=`$(GETLINKS) $$SRC | sort -u | wc -l`
>   [ $$LINKS -gt $$MAX ] && echo "Not running $@ too many links: $$LINKS > $$MAX" && exit
>   echo "Running fixer $@ on $$LINKS items from $$SRC..."
>   $(FUN_REPLACE) -links:$$SRC $$FIX $(ALWAYS)
>   echo $$LINKS > $@

$(FIX)es_missing_entry: $(LIST)missing_forms
>   @
>   SRC="User:JeffDoozan/lists/es/forms/missing_entry_autofix"
>   FIX="-fix:es_add_forms"
>   MAX=200

>   LINKS=`$(GETLINKS) $$SRC | sort -u | wc -l`
>   [ $$LINKS -gt $$MAX ] && echo "Not running $@ too many links: $$LINKS > $$MAX" && exit
>   echo "Running fixer $@ on $$LINKS items from $$SRC..."
>   $(FUN_REPLACE) -links:$$SRC $$FIX $(ALWAYS)
>   echo $$LINKS > $@

$(FIX)es_missing_pos: $(LIST)missing_forms
>   @
>   SRC="User:JeffDoozan/lists/es/forms/missing_pos_autofix"
>   FIX="-fix:es_add_forms"
>   MAX=200

>   LINKS=`$(GETLINKS) $$SRC | sort -u | wc -l`
>   [ $$LINKS -gt $$MAX ] && echo "Not running $@ too many links: $$LINKS > $$MAX" && exit
>   echo "Running fixer $@ on $$LINKS items from $$SRC..."
>   $(FUN_REPLACE) -links:$$SRC $$FIX $(ALWAYS)
>   echo $$LINKS > $@

$(FIX)es_missing_sense: $(LIST)missing_forms
>   @
>   SRC="User:JeffDoozan/lists/es/forms/missing_sense_autofix"
>   FIX="-fix:es_replace_forms -fix:es_add_forms"
>   MAX=1000

>   LINKS=`$(GETLINKS) $$SRC | sort -u | wc -l`
>   [ $$LINKS -gt $$MAX ] && echo "Not running $@ too many links: $$LINKS > $$MAX" && exit
>   echo "Running fixer $@ on $$LINKS items from $$SRC..."
>   $(FUN_REPLACE) -links:$$SRC $$FIX $(ALWAYS)
>   echo $$LINKS > $@



# not safe to run automatically
$(FIX)misnamed_references_section: $(LIST)section_stats
>   @
>   SRC="User:JeffDoozan/lists/misnamed_references_section"
>   FIX="-fix:cleanup_sections"
>   MAX=200

>   LINKS=`$(GETLINKS) $$SRC | sort -u | wc -l`
>   [ $$LINKS -gt $$MAX ] && echo "Not running $@ too many links: $$LINKS > $$MAX" && exit
>   echo "Running fixer $@ on $$LINKS items from $$SRC..."
>   $(FUN_REPLACE) -links:$$SRC $$FIX
>   echo $$LINKS > $@

$(FIX)autofix_empty_section: $(LIST)section_stats
>   @
>   SRC="User:JeffDoozan/lists/autofix_empty_section"
>   FIX="-fix:cleanup_sections"
>   MAX=200

>   LINKS=`$(GETLINKS) $$SRC | sort -u | wc -l`
>   [ $$LINKS -gt $$MAX ] && echo "Not running $@ too many links: $$LINKS > $$MAX" && exit
>   echo "Running fixer $@ on $$LINKS items from $$SRC..."
>   $(FUN_REPLACE) -links:$$SRC $$FIX
>   echo $$LINKS > $@

$(FIX)es_unexpected_form: $(LIST)missing_forms $(FIX)es_missing_sense
>   @
>   SRC="User:JeffDoozan/lists/es/forms/unexpected_form_autofix"
>   FIX="-fix:es_replace_forms -fix:es_remove_forms"
>   MAX=200

>   LINKS=`$(GETLINKS) $$SRC | sort -u | wc -l`
>   [ $$LINKS -gt $$MAX ] && echo "Not running $@ too many links: $$LINKS > $$MAX" && exit
>   echo "Running fixer $@ on $$LINKS items from $$SRC..."
>   $(FUN_REPLACE) -links:$$SRC $$FIX
>   echo $$LINKS > $@


all: lists

#data: enwiktionary-$(DATETAG)-pages-articles.xml.bz2 es-en.txt.bz2 pt-en.txt.bz2 fr-en.txt.bz2 spanish_data/es-en.data-full spanish_data/es-en.data es.allpages fr-en.data pt-en.data $(BUILDDIR)/wiki.pages translations.bz2 es.sortorder fr.lemmas fr.allpages es.lemmas drae.lemmas drae.with_etymology es.with_etymology es.lemmas_without_etymology

#forms_with_data
lists: $(patsubst %,$(LIST)%,t9n_problems section_stats  mismatched_headlines maybe_forms missing_forms fr_missing_lemmas es_missing_lemmas es_missing_ety fr_missing_tlfi es_missing_drae es_untagged_demonyms es_duplicate_passages es_with_synonyms pt_with_synonyms es_verbs_missing_type)

#fixes: .fix.add_tlfi_links .fix.add_drae_links .fix.es_syns .fix.pt_syns .fix.autofix_title .fix.autofix_numbered_pos .fix.misnamed_references_section .fix.misplaced_translations_section .fix.autofix_empty_section .fix.autofix_bad_l2 .fix.autofix_missing_references .fix.botfix_consolidate_forms .fix.es_missing_entry .fix.es_missing_pos .fix.es_missing_sense .fix.es_unexpected_form

.PHONY: all data lists fixes
