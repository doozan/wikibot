#### nym_sections_to_tags.py
This will search all entries with a specified language with (Syn|Ant|Homo|Hyper)nym categories
For all parts of speech having exactly one definition and containing a *nym category,
the category will be converted into an appropriate tag and added to the definition

It can be called directly from the command line to generate files with the pre/post changes for comparison purposes.

It can be used with the pywikibot replace.py script to actually make the changes with the following user-fixes.py:

```
TARGET_LANG="Spanish"
TARGET_LANG_ID="es"

import re
from nym_sections_to_tags import NymSectionToTag
nym_fixer = NymSectionToTag(TARGET_LANG, TARGET_LANG_ID)


start = rf"(^|\n)=={TARGET_LANG}=="
re_endings = [ r"\[\[\s*Category\s*:" r"==[^=]+==", r"----" ]
template_endings = [ "c", "C", "top", "topics", "categorize", "catlangname", "catlangcode", "cln", "DEFAULTSORT" ]
re_endings += [ r"\{\{\s*"+item+r"\s*\|" for item in template_endings ]
endings = "|".join(re_endings)
newlines = r"(\n\s*){1,2}"
pattern = fr"{start}.*?(?={newlines}({endings})|$)"


def auto_fix_nyms(text):
    return nym_fixer.run_fix(text.group(), ["autofix","automatch_senseid","automatch_sense"], sections=["Synonyms","Antonyms"])

fixes['simple_nyms']= {
    'regex': True,
    'msg': { '_default':'Bot: Convert nym sections to templates' },
    "replacements": [ (pattern, auto_fix_nyms) ],
}
```

```replace.py -xml:enwiktionary-latest-pages-articles.xml.bz2 -dotall -fix:simple_nyms```
