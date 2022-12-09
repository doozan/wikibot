import pytest

import re
import enwiktionary_parser as wtparser
from autodooz.sectionparser import SectionParser
from enwiktionary_wordlist.wordlist import Wordlist
from enwiktionary_wordlist.all_forms import AllForms
from ..fix_es_drae import DraeFixer

def test():

    text = """\
==Spanish==

===Etymology===
{{af|es|reproducir|-ción}}

===Pronunciation===
{{es-IPA}}

===Noun===
{{es-noun|f}}

# [[reproduction]], [[procreation]] {{gloss|the act of reproducing new individuals biologically}}
# [[reproduction]] {{gloss|the act of making copies}}
# [[reproduction]], [[copy]], [[duplicate]] {{gloss|a copy of something, as in a piece of art; a duplicate}}
# {{lb|es|computing}} [[playback]] {{gloss|the replaying of something previously recorded, especially sound or moving images}}
#: {{ux|es|La '''reproducción''' estaba dañada por los rayones en la superficie del DVD.|The '''playback''' was damaged by scratches on the DVD's surface.}}
# {{lb|es|computing}} [[play]] {{gloss|an instance of watching or listening to digital media}}
#: {{ux|es|La '''reproducción automática''' está desactivada de forma predeterminada.|'''Autoplay''' is turned off by default.}}
# {{lb|es|internet}} [[view]] {{gloss|an individual viewing of a video by a user}}
#:{{synonyms|es|visualización|visita}}
#: {{ux|es|Ese vídeo de YouTube tiene 1.000.000 '''reproducciones'''.|That YouTube video has 1,000,000 '''views'''.}}

====Derived terms====
{{der4|es
|lista de reproducción
}}

===Further reading===
* {{R:es:DRAE}}"""

    title = "reproducción"
    summary = []

    fixer = DraeFixer("../drae_data/drae.links")
    res = fixer.fix_missing_drae(text, title, summary)

    print(summary)
    assert res == text

