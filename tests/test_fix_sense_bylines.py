from autodooz.fix_sense_bylines import BylineFixer

fixer = BylineFixer()

def test_fix_nym_with_bare_qualifier():


    tests = [
        ["{{syn|de|Schulterzucken}} {{i|not vulgar}}", "{{syn|de|Schulterzucken<qq:not vulgar>}}"],
        ["{{syn|mul|Tanagra albo-frenatus}} {{q|deprecated}}", "{{syn|mul|Tanagra albo-frenatus<qq:deprecated>}}"],
        ["{{syn|nl|Vossendarp}} (''Carnival nickname'')", "{{syn|nl|Vossendarp<qq:Carnival nickname>}}"],
        ["{{syn|tr|dansöz}} (female)", "{{syn|tr|dansöz<qq:female>}}"],
        ["{{syn|igl|ẹ́ñwu-anẹ̀}} ''(euphemistic)''", "{{syn|igl|ẹ́ñwu-anẹ̀<qq:euphemistic>}}"],
        ["{{syn|io|rubra}} {{qualifier|archaic}}", "{{syn|io|rubra<qq:archaic>}}"],
        ["{{syn|en|Fox Harbour}} {{q|''historical''}}", "{{syn|en|Fox Harbour<qq:historical>}}"],
        ["{{syn|pl|niesamowity|niezwykły|wspaniały}}, {{syn|pl|Thesaurus:dobry}}", "{{syn|pl|niesamowity|niezwykły|wspaniały|Thesaurus:dobry}}"],

    ]

    for text, expected in tests:
        print(text)
        assert fixer.fix_complex_byline("syn", text) == expected


text = """
# [[#English|on]], [[in]], [[at]], [[among]] {{+obj|ang|dat|or|ins}}
: {{ux|ang|'''On''' þæm huse|'''In''' the house}}
# [[#English|on]], [[during]] {{+obj|ang|acc}}
: {{ux|ang|'''On''' midne winter|'''In''' mid-winter}}
"""

expected = """
# [[#English|on]], [[in]], [[at]], [[among]] {{+obj|ang|dat|or|ins}}
#: {{ux|ang|'''On''' þæm huse|'''In''' the house}}
# [[#English|on]], [[during]] {{+obj|ang|acc}}
#: {{ux|ang|'''On''' midne winter|'''In''' mid-winter}}
"""


text = """
# [[stone]]
# [[money]]
{{ux|aer|Arelhe akangkeme anthurre '''apwerte''' akngerrele impeke.}}
"""

expected = """
# [[stone]]
# [[money]]
#: {{ux|aer|Arelhe akangkeme anthurre '''apwerte''' akngerrele impeke.}}
"""


text = """
# [[goods|Goods]] or [[service]]s that are for [[sale]].
#: ''The square was filled with booths, with vendors offering their '''wares'''.''
"""

expected = """
# [[goods|Goods]] or [[service]]s that are for [[sale]].
#: {{ux|The square was filled with booths, with vendors offering their '''wares'''.}}
"""

