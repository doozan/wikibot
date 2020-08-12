#### nym_sections_to_tags.py
This will search all entries with a specified language with (Syn|Ant|Homo|Hyper)nym categories
For all parts of speech having exactly one definition and containing a *nym category,
the category will be converted into an appropriate tag and added to the definition

It can be called directly from the command line to generate files with the pre/post changes for comparison purposes.

It can be used with the pywikibot replace.py script to actually make the changes with the following user-fixes.py:

```
from nym_sections_to_tags import NymSectionToTag
nym_fixer = NymSectionToTag("Spanish", "es")

def auto_fix_nyms(text):
    return nym_fixer.run_fix(text.group())

def manual_fix_nyms_with_sense(text):
    return nym_fixer.run_fix(text.group(), ["sense"])

fixes['simple_nyms']= {
    'regex': True,
    'msg': { '_default':'Bot: Convert nym sections to templates' },
    'replacements': [ (r"\n==Spanish==.*?(\n----\n|\n==[^=]+==)", auto_fix_nyms) ],
}

fixes['sense_nyms']= {
    'regex': True,
    'msg': { '_default':'Bot: Convert nym sections to templates' },
    'replacements': [ (r"\n==Spanish==.*?(\n----\n|\n==[^=]+==)", manual_fix_nyms_with_sense) ],
}
```

```replace.py -xml:enwiktionary-latest-pages-articles.xml.bz2 -dotall -fix:simple_nyms```
