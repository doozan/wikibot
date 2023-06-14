from autodooz.quotes.parser import QuoteParser, LINK
parser = QuoteParser(debug=True)

def test_cleanup_text():
    assert parser.cleanup_text("[http://link.foo ''bar'']") == "''[http://link.foo bar]''"
    assert parser.cleanup_text('[http://link.foo "bar"]') == '"[http://link.foo bar]"'
    assert parser.cleanup_text('[http://link.foo “bar”]') == '“[http://link.foo bar]”'
    assert parser.cleanup_text('[http://link.foo ‘bar’]') == '‘[http://link.foo bar]’'
    assert parser.cleanup_text("""[http://link.foo ''bar"]""") == """[http://link.foo ''bar"]"""
    assert parser.cleanup_text("[[foo|''bar'']]") == "''[[foo|bar]]''"
    assert parser.cleanup_text("[[foo|''bar'']") == "[[foo|''bar'']"

    assert parser.cleanup_text("{{lang|fr|''foo''}}") == "''{{lang|fr|foo}}''"
    assert parser.cleanup_text("{{w|Fer-de-Lance (book)|''Fer-de-Lance''}}") == "''{{w|Fer-de-Lance (book)|Fer-de-Lance}}''"
    assert parser.cleanup_text('[https://web.archive.org/web/20140811201712/http://etext.virginia.edu/etcbin/ot2www-pubeng?specfile=%2Ftexts%2Fenglish%2Fmodeng%2Fpublicsearch%2Fmodengpub.o2w "Plain Facts for Old and Young"]') == '"[https://web.archive.org/web/20140811201712/http://etext.virginia.edu/etcbin/ot2www-pubeng?specfile=%2Ftexts%2Fenglish%2Fmodeng%2Fpublicsearch%2Fmodengpub.o2w Plain Facts for Old and Young]"'


def test_get_leading_section():

    tests = (
        'volume 4, part 1, page 128',
        "issue [http://www.spiegel.de/spiegel/print/index-2010-49.html 49/2010], page 80",
        "[[s:de:Seite:Die Gartenlaube (1877) 157.jpg|page 157]]",
    )
    for text in tests:
        print(text)
        res = parser.get_leading_section(text)
        print(res)
        assert res == (text, "")

    text = "Part{{nbsp}}6, Chapter{{nbsp}}4, p.{{nbsp}}428,[https://archive.org/details/judeobscure00hard/page/428/mode/1up?q=Acherontic]"
    assert parser.get_leading_section(text) == ('Part{{nbsp}}6, Chapter{{nbsp}}4, p.{{nbsp}}428,[https://archive.org/details/judeobscure00hard/page/428/mode/1up?q=Acherontic]', '')
    # If section contains trailing raw html, it should be split into a "url" no matter what

    text = "#15"
    assert parser.get_leading_section(text) == ('#15', '')

def test_get_leading_publisher():
    assert parser.get_leading_publisher('NYU Press ({{ISBN|9780814767498}}), page 104:') == ('NYU Press', ' ({{ISBN|9780814767498}}), page 104:')
    assert parser.get_leading_publisher('NYU Press, Inc ({{ISBN|9780814767498}}), page 104:') == ('NYU Press, Inc', ' ({{ISBN|9780814767498}}), page 104:')
    assert parser.get_leading_publisher('NYU Press, Inc. ({{ISBN|9780814767498}}), page 104:') == ('NYU Press, Inc.', ' ({{ISBN|9780814767498}}), page 104:')
    assert parser.get_leading_publisher('NYU Press, Inc, LLC ({{ISBN|9780814767498}}), page 104:') == ('NYU Press, Inc, LLC', ' ({{ISBN|9780814767498}}), page 104:')
    assert parser.get_leading_publisher('NYU Press and sons ({{ISBN|9780814767498}}), page 104:') == ('NYU Press and sons', ' ({{ISBN|9780814767498}}), page 104:')
    assert parser.get_leading_publisher('NYU Press and sons ({{ISBN|9780814767498}}), page 104:') == ('NYU Press and sons', ' ({{ISBN|9780814767498}}), page 104:')
    assert parser.get_leading_publisher('NYU Press&son ({{ISBN|9780814767498}}), page 104:') == ('NYU Press&son', ' ({{ISBN|9780814767498}}), page 104:')
    assert parser.get_leading_publisher('NYU Press&sonreir ({{ISBN|9780814767498}}), page 104:') == None
    assert parser.get_leading_publisher('University of Nowhere') == None
    assert parser.get_leading_publisher('Springer Science & Business Media {{ISBN|9783540379010}}, page 266') == ('Springer Science & Business Media', ' {{ISBN|9783540379010}}, page 266')


#    with open("quotes/publisher.all") as infile:
#        assert "Springer Science & Business Media".lower() in [line.strip().lower() for line in infile]



def test_get_leading_link():
    res = parser.get_leading_link('[[w:Classical Philology (journal)|Classical Philology]] test')
    print(res)
    assert res == ('Classical Philology', LINK(target='w:Classical Philology (journal)', text='Classical Philology', orig='[[w:Classical Philology (journal)|Classical Philology]]'), ' test')

def test_get_leading_url():
    assert parser.get_leading_url('http://site.com/foo... bar') == ('', LINK(target='http://site.com/foo', text='', orig='http://site.com/foo'), '... bar')
    assert parser.get_leading_url('(http://site.com/foo) bar') == None #('', LINK(target='http://site.com/foo', text='', orig='http://site.com/foo'), ' bar')
    assert parser.get_leading_url('(http://site.com/foo bar)') == None


def test_normalize_et_al():
    assert parser.normalize_et_al("blah et al.; test") == "blah, et al; test"
    assert parser.normalize_et_al("blah ''et al.''; test") == "blah, et al; test"
    assert parser.normalize_et_al("blah (''& al''); test") == "blah, et al; test"
    assert parser.normalize_et_al("blah, [et alios]; test") == "blah, et al; test"

def notest_season_episode():

    assert parser.get_season_episode('s01e12') == ("01", "12", " ")
    assert parser.get_season_episode('x s01e12 x') == ("01", "12", "x x")
    assert parser.get_season_episode('xs01e12') == ("", "", "xs01e12")
    assert parser.get_season_episode('s01e12x') == ("", "", "s01e12x")


def test_get_leading_location():

    assert parser.get_leading_location('Australia: Publisher') == ("Australia", ": Publisher")
    assert parser.get_leading_location('Australia Publisher') == None
    assert parser.get_leading_location('Australian: Publisher') == None
    assert parser.get_leading_location('New York: University Press') == ('New York', ': University Press')
    assert parser.get_leading_location('New York Times') == None
    assert parser.get_leading_location('New York University Press') == None
    assert parser.get_leading_location('University of Nebraska, 1990:') == None
    assert parser.get_leading_location('Pacific Search Press') == None
    assert parser.get_leading_location('East Aurora, NY: Roycrofters') == ('East Aurora, NY', ': Roycrofters')
    #assert parser.get_leading_location('') == None

def test_get_leading_unhandled():

    assert parser.get_leading_unhandled('Australia: Publisher') == ("Australia", ": Publisher")
    assert parser.get_leading_unhandled(':Australia: Publisher') == (":", "Australia: Publisher")
    assert parser.get_leading_unhandled('{{Australia}} Publisher') == ("{{Australia}}", " Publisher")
    assert parser.get_leading_unhandled('[Australia] Publisher') == ("[Australia]", " Publisher")
    assert parser.get_leading_unhandled('[[Australia]] Publisher') == ("[[Australia]]", " Publisher")
    assert parser.get_leading_unhandled('{{Australia Publisher') == ('{{', 'Australia Publisher')
    assert parser.get_leading_unhandled('[[Australia Publisher') == ('[[', 'Australia Publisher')
    assert parser.get_leading_unhandled('[Australia Publisher') == ('[', 'Australia Publisher')
    assert parser.get_leading_unhandled('john.doe123@email-address.co.uk, blah') == ('john.doe123@email-address.co.uk', ', blah')

def test_get_leading_journal():

    assert parser.get_leading_journal('Time') == ('Time', '')
    assert parser.get_leading_journal('Time, Blah') == ('Time', ', Blah')
    assert parser.get_leading_journal('Time Blah') == None
    assert parser.get_leading_journal('{{w|Newsweek}} December 7, 1987') == ('{{w|Newsweek}}', ' December 7, 1987')

def test_get_leading_isbn():

    assert parser.get_leading_isbn('{{ISBN|123456890}} test') == (['123456890'], 'test')
    assert parser.get_leading_isbn('ISBN: 123456890 test') == (['123456890'], 'test')
    assert parser.get_leading_isbn('{{ISBN|123456890}}, {{ISBN|123456890}}') == (['123456890', '123456890'], '')
    assert parser.get_leading_isbn('978-0123456789, 978-0123456789') == (['978-0123456789', '978-0123456789'], '')

def test_get_leading_names():

    res = parser.get_leading_names("J.D. Doe, This is not part of the name string.")
    assert res == ({'author': ['J.D. Doe']}, ', This is not part of the name string.')

    res = parser.get_leading_names("J.D. Doe, Jane not-a-valid-name-but-explicitly-labelled Doe (editor)")
    #assert res == ({'author': ['J.D. Doe'], 'editor': ['Jane not-a-valid-name-but-explicitly-labelled Doe']}, '')
    assert res == ({'author': ['J.D. Doe']}, ', Jane not-a-valid-name-but-explicitly-labelled Doe (editor)')

    res = parser.get_leading_names("J.D. Doe, Jane not-a-valid-name Doe, John Doe")
    assert res == ({'author': ['J.D. Doe']}, ', Jane not-a-valid-name Doe, John Doe')

    res = parser.get_leading_names("J.D. Doe, Jane (not a valid name) Doe")
    assert res == ({'author': ['J.D. Doe']}, ', Jane (not a valid name) Doe')

    res = parser.get_leading_names("edited by J.D. Doe, This is not a valid name")
    assert res == ({'editor': ['J.D. Doe']}, ', This is not a valid name')

    res = parser.get_leading_names("Ms Patricia MacCormack, ''Cinesexuality''")
    assert res == ({'author': ['Ms Patricia MacCormack']}, ", ''Cinesexuality''")

    res = parser.get_leading_names("Knud H. Thomsen, Knud H. Thomsen (Pichard), ''Klokken i Makedonien'',")
    print(res)
    assert res == ({'author': ['Knud H. Thomsen']}, ", Knud H. Thomsen (Pichard), ''Klokken i Makedonien'',")

    res = parser.get_leading_names("edited by Claire Bowern, Bethwyn Evans, Luisa Miceli)")
    print(res)
    assert res == ({'editor': ['Claire Bowern', 'Bethwyn Evans', 'Luisa Miceli']}, '')

    res = parser.get_leading_names("Dr. John Smith")
    print(res)
    assert res == ({'author': ['Dr. John Smith']}, '')

    res = parser.get_leading_names("Oscar Hijuelos: ''The Fourteen Sisters of Emilio Montez O'Brien''.")
    print(res)
    assert res == ({'author': ['Oscar Hijuelos']}, ": ''The Fourteen Sisters of Emilio Montez O'Brien''.")

    res = parser.get_leading_names("Dr. John Smith ''et al''")
    print(res)
    assert res == ({'author': ['Dr. John Smith', 'et al']}, '')

    res = parser.get_leading_names("Dr. John Smith ''[et. alia]''")
    print(res)
    assert res == ({'author': ['Dr. John Smith', 'et al']}, '')


def test_get_leading_names_safe():
    assert parser.get_leading_names_safe("ed. W. Anderson, ''Treasury of the Animal World. For the Young.'', p.154") == ({'editor': ['W. Anderson']}, ", ''Treasury of the Animal World. For the Young.'', p.154")
    assert parser.get_leading_names_safe("ed. W. Anderson, [http://link.com article] p.154") == ({'editor': ['W. Anderson']}, ', [http://link.com article] p.154')

    res = parser.get_leading_names_safe("edited by J.D. Doe, This is not a valid name")
    assert res == ({'editor': ['J.D. Doe']}, ', This is not a valid name')

    assert parser.get_leading_names_safe("edited by Claire Bowern, Bethwyn Evans, Luisa Miceli") == ({'editor': ['Claire Bowern', 'Bethwyn Evans', 'Luisa Miceli']}, "")
    assert parser.get_leading_names_safe("eds. Claire Bowern, Bethwyn Evans, Luisa Miceli") == ({'editor': ['Claire Bowern', 'Bethwyn Evans', 'Luisa Miceli']}, "")
    assert parser.get_leading_names_safe("ed. Claire Bowern, Bethwyn Evans, Luisa Miceli") == ({'editor': ['Claire Bowern', 'Bethwyn Evans', 'Luisa Miceli']}, "")
    assert parser.get_leading_names_safe("Claire Bowern, Bethwyn Evans, Luisa Miceli") == None

def test_classify_names():

    res = parser.classify_names("John Doe, Jr., Jane Doe (translator), Ed Foo, Ed Bar (eds.)", "~author")
    print(res)
    assert res == ({"author": ["John Doe, Jr."], "translator": ["Jane Doe"], "editor": ["Ed Foo", "Ed Bar"]}, "")

    res = parser.classify_names("translated by John Doe, Jr. and Jane Doe, Ed Foo (editor)", "~author")
    print(res)
    assert res == ({'translator': ['John Doe, Jr.', 'Jane Doe'], 'editor': ['Ed Foo']}, "")


    # Fail if conflicting labels
    res = parser.classify_names("translated by John Doe, Jr. (editor)", "~author")
    print(res)
    assert res == None


    # Fail if conflicting multi-labels
    res = parser.classify_names("translated by John Doe, Jr. and Jane Doe, Ed Foo (editors)", "~author")
    print(res)
    assert res == None


    res = parser.classify_names("David Squire et al", "~editor")
    print(res)
    assert res == None
#    assert res == ({'editor': ['David Squire', 'et al']}, "")

#    res = parser.classify_names("Lewis B. Ware ''et al.''", "~editor")
#    print(res)
#    assert res == ({'editor': ['Lewis B. Ware', 'et al']}, "")

#    res = parser.classify_names("John Doe ''et al.'' Jane Doe", "~author")
#    print(res)
#    assert res == ({'author': ['John Doe', 'et al', 'Jane Doe']}, "")

    res = parser.classify_names("John Doe, This is not a valid name.", "~author")
    print(res)
    assert res == ({'author': ['John Doe']}, ', This is not a valid name.')

    res = parser.classify_names("This is not a valid name, John Doe", "~author")
    print(res)
    assert res == None

    # Explicit labels apply unconditionally to the first name and then to each valid name afterwards
    res = parser.classify_names("edited by This is not a valid name, John Doe", "~author")
    print(res)
    assert res ==  None #({'editor': ['This is not a valid name', 'John Doe']}, "")

    # Explicit labels apply unconditionally to the first name and then to each valid name afterwards
    res = parser.classify_names("edited by This is not a valid name, John Doe, Also not valid", "~author")
    print(res)
    assert res == None # ({'editor': ['This is not a valid name', 'John Doe']}, "Also not valid")


    # Explicit labels apply unconditionally to the first name and then to each valid name afterwards
    res = parser.classify_names("edited by John Doe, This is not a valid name", "~author")
    print(res)
    assert res == ({'editor': ['John Doe']}, ', This is not a valid name')

    # Retroactively labelled names must all pass validation
    res = parser.classify_names("Jane Doe, John Doe (editors)", "~author")
    print(res)
    assert res == ({'editor': ['Jane Doe', 'John Doe']}, "")

    # Retroactively labelled names must all pass validation
    res = parser.classify_names("This is not a valid name, John Doe (editors)", "~author")
    print(res)
    assert res == None

    # Names wrapped in {{w }} must also pass validation
    res = parser.classify_names('{{w|Y Beibl cyssegr-lan}}, Genesis 28:15:', "~author")
    print(res)
    assert res == None

    res = parser.classify_names('{{w|John Doe}}, Genesis 28:15:', "~author")
    assert res == ({'author': ['{{w|John Doe}}']}, ', Genesis 28:15:')

    # parse et al and variations
#    res = parser.classify_names("Jane Doe et al.", "~author")
#    assert res == ({'author': ['Jane Doe', 'et al']}, '')#
#    res = parser.classify_names("Jane Doe, et al.", "~author")
#    assert res == ({'author': ['Jane Doe', 'et al']}, '')
#    res = parser.classify_names("Jane Doe, et alii, invalid-name", "~author")
#    assert res == ({'author': ['Jane Doe', 'et al']}, 'invalid-name')

    # Invalid name followed by et al gets restored properly
    res = parser.classify_names("Jane Doe, invalid-name, et alii, another-invalid-name", "~author")
    assert res == ({'author': ['Jane Doe']}, ', invalid-name, et alii, another-invalid-name')

#    res = parser.classify_names("Jane Doe, et alii", "~author")
#    assert res == ({'author': ['Jane Doe', 'et al']}, '')

#    res = parser.classify_names("Jane Doe, et alias", "~author")
#    print(res)
#    assert res == ({'author': ['Jane Doe']}, ' et alias')

#    res = parser.classify_names("Jane Doe, & al.", "~author")
#    assert res == ({'author': ['Jane Doe', 'et al']}, '')
#    res = parser.classify_names("Jane Doe, [[et al]].", "~author")
#    assert res == ({'author': ['Jane Doe', 'et al']}, '')


    res = parser.classify_names("Judith Lynn Sebesta (editor and translator), Jeffrey M. Duban (translator)", "~author")
    assert res == None


def test_get_leading_month():
    assert parser.get_leading_month("May, test") == ("May", ", test")
    assert parser.get_leading_month("May 30, 2001") == None

def test_get_leading_date_retrieved():
    assert parser.get_leading_date_retrieved("Accessed 3 June 2019") == ('2019', 'June', -3, '')
    assert parser.get_leading_date_retrieved("retrieved: 3 June 2019") == ('2019', 'June', -3, '')
    assert parser.get_leading_date_retrieved("accessed on 3 June 2019") == ('2019', 'June', -3, '')

def test_get_leading_date():

    assert parser.get_leading_date("'''1953''', May Davies Martenet") == None

    assert parser.get_leading_date("2001, May 30") == ('2001', 'May', 30, '')
    assert parser.get_leading_date("2001, May 30th") == ('2001', 'May', 30, '')
    assert parser.get_leading_date("30 May") == (None, 'May', -30, '')
    assert parser.get_leading_date("May 30") == (None, 'May', 30, '')
    assert parser.get_leading_date("May 30, 2001") == ('2001', 'May', 30, '')
    assert parser.get_leading_date("2001, May") == None
    assert parser.get_leading_date("2001 12") == None


    assert parser.get_leading_date('11 July, 2012 abcd') == ('2012', 'July', -11, ' abcd')
    assert parser.get_leading_date('12 Jul, 2012 abcd') == ('2012', 'Jul', -12, ' abcd')
    assert parser.get_leading_date('13 July abcd') == (None, 'July', -13, ' abcd')
    assert parser.get_leading_date('July 14, 2012 abcd') == ('2012', 'July', 14, ' abcd')
    assert parser.get_leading_date('Jul 15, 2012 abcd') == ('2012', 'Jul', 15, ' abcd')
    assert parser.get_leading_date('Jul 16 abcd') == (None, 'Jul', 16, ' abcd')
    assert parser.get_leading_date('7 16 abcd') == None
    assert parser.get_leading_date('7 16 2001 abcd') == ('2001', 'Jul', 16, ' abcd')

#    assert parser.get_leading_date('2012-02-02x') == None
    assert parser.get_leading_date('2012-02-02') == ('2012', 'Feb', 2, '')
    assert parser.get_leading_date('2012-02') == None
    assert parser.get_leading_date('2012-2-2 abcd') == None
    assert parser.get_leading_date('2012 12/12 abcd') == None
    assert parser.get_leading_date('2012 12/13 abcd') == ('2012', 'Dec', 13, ' abcd')
    assert parser.get_leading_date('2012 12/31 abcd') == ('2012', 'Dec', 31, ' abcd')
    assert parser.get_leading_date('2012-09-18') == ('2012', 'Sep', 18, '')
    assert parser.get_leading_date('2012.09.18') == ('2012', 'Sep', 18, '')
    assert parser.get_leading_date('2012/09/18') == ('2012', 'Sep', 18, '')
    assert parser.get_leading_date('2012 09 18') == ('2012', 'Sep', 18, '')
    # Feb 31 is invalid
    assert parser.get_leading_date('2012-02-31 abcd') == None

    assert parser.get_leading_date('16 Jan 2016') == ('2016', 'Jan', -16, '')
    assert parser.get_leading_date('16 Jan. 2016') == ('2016', 'Jan', -16, '')
    assert parser.get_leading_date('22 Sept 2017') == ('2017', 'Sept', -22, '')
    assert parser.get_leading_date('22nd Sept 2017') == ('2017', 'Sept', -22, '')
    assert parser.get_leading_date('8 Sept. 2009') == ('2009', 'Sept', -8, '')

    assert parser.get_leading_date('Sun 8 Sept. 2009') == ('2009', 'Sept', -8, '')
    assert parser.get_leading_date('Fri.Sep.8.2009') == ('2009', 'Sep', 8, '')
    assert parser.get_leading_date('Sunday, 8 Sept. 2009') == ('2009', 'Sept', -8, '')
    assert parser.get_leading_date('Tues 8 Sept. 2009') == ('2009', 'Sept', -8, '')
    assert parser.get_leading_date('Tue. 8 September') == (None, 'September', -8, '')
    assert parser.get_leading_date('September 2009') == None
    assert parser.get_leading_date('Tue. September 2009') == None

    assert parser.get_leading_date("2001, May") == None
    assert parser.get_leading_date("2001, May 30") == ('2001', 'May', 30, '')
    assert parser.get_leading_date("2001, 30 May") == ('2001', 'May', -30, '')
    assert parser.get_leading_date("2001, 30 Mayx") == None

    assert parser.get_leading_date("'''(2001)''', May 30") == ('2001', 'May', 30, '')
    assert parser.get_leading_date("[2001], May 30") == ('2001', 'May', 30, '')
    assert parser.get_leading_date("(2001), May 30") == ('2001', 'May', 30, '')
    assert parser.get_leading_date("'''[(2001)]''', May 30") == ('2001', 'May', 30, '')

    assert parser.get_leading_date("20 Jan 08") == None
    assert parser.get_leading_date("01/02/03") == None

def test_get_leading_year():
    assert parser.get_leading_year("2002 blah") == ('2002', 'blah')
    assert parser.get_leading_year("'''2002''' blah") == ('2002', 'blah')
    assert parser.get_leading_year("(2002) blah") == ('2002', 'blah')
    assert parser.get_leading_year("(2002) blah") == ('2002', 'blah')
    assert parser.get_leading_year("[2002] blah") == ('2002', 'blah')
    assert parser.get_leading_year("'''(2002)''' blah") == ('2002', 'blah')
    assert parser.get_leading_year("('''2002''') blah") == ('2002', 'blah')
    assert parser.get_leading_year("('''2002'''), blah") == ('2002', 'blah')

    assert parser.get_leading_year("0002 blah") == None
    assert parser.get_leading_year("2200 blah") == None
    assert parser.get_leading_year("12345 blah") == None
    assert parser.get_leading_year("'''2002 blah") == None
    assert parser.get_leading_year("2002) blah") == None
    assert parser.get_leading_year("[2002) blah") == None

    assert parser.get_leading_year("2002-2012 blah") == ('2002', '-', '2012', 'blah')
    assert parser.get_leading_year("2002,2012 blah") == ('2002', ',', '2012', 'blah')
    assert parser.get_leading_year("2002 and 2012 blah") == ('2002', ' & ', '2012', 'blah')
    assert parser.get_leading_year("2002 or 2012 blah") == ('2002', ' or ', '2012', 'blah')

    assert parser.get_leading_year("2002, or 2012 blah") == ('2002', "or 2012 blah")

def test_get_leading_edition():
    assert parser.get_leading_edition("2015 Limited edition, blah") == ('2015 Limited', ', blah')
    assert parser.get_leading_edition("Limited 2015 ILLUSTRATED traveler's ed., blah") == ("Limited 2015 ILLUSTRATED traveler's", ', blah')
    assert parser.get_leading_edition("10th edition blah") == ("10th", " blah")

def test_get_leading_countable():
    assert parser.get_leading_countable("VOLUME 12, test") == ('volume', '12', ', test')
    assert parser.get_leading_countable("volume12, test") == ('volume', '12', ', test')
    assert parser.get_leading_countable("Vol.12, test") == ('volume', '12', ', test')
    assert parser.get_leading_countable("v.12, test") == ('volume', '12', ', test')
    assert parser.get_leading_countable("v 12, test") == ('volume', '12', ', test')
    assert parser.get_leading_countable("p 12, test") == ('page', '12', ', test')
    assert parser.get_leading_countable("page 12, test") == ('page', '12', ', test')
    assert parser.get_leading_countable("p12, test") == ('page', '12', ', test')
    assert parser.get_leading_countable("p ix, test") == ('page', 'ix', ', test')
    assert parser.get_leading_countable("pix, test") == None
    assert parser.get_leading_countable("p one, test") == ('page', '1', ', test')
    assert parser.get_leading_countable("p A1, test") == ('page', 'A1', ', test')
    assert parser.get_leading_countable("pA1, test") == None
    assert parser.get_leading_countable("pone, test") == None
    assert parser.get_leading_countable("page 12a, test") == ('page', '12a', ', test')
    assert parser.get_leading_countable("page 12ab, test") == None
    assert parser.get_leading_countable("page a12b, test") == None
    assert parser.get_leading_countable("page x, test") == ('page', 'x', ', test')
    assert parser.get_leading_countable("page xii, test") == ('page', 'xii', ', test')
    assert parser.get_leading_countable("page XV, test") == ('page', 'XV', ', test')
    assert parser.get_leading_countable("page Xv, test") == None
    assert parser.get_leading_countable("page a12, test") == ('page', 'a12', ', test')
    assert parser.get_leading_countable("page #12, test") == ('page', '12', ', test')
    assert parser.get_leading_countable("P 12, test") == None
    assert parser.get_leading_countable("pages 12 - 15, test") == ('page', '12', '-', '15', ', test')
    assert parser.get_leading_countable("pages #12 - #15, test") == ('page', '12', '-', '15', ', test')
    assert parser.get_leading_countable("chapter One, test") == ('chapter', '1', ', test')
    assert parser.get_leading_countable("chapter ThirtyOne, test") == ('chapter', '31', ', test')
    assert parser.get_leading_countable("chapter Thirty-One, test") == ('chapter', '31', ', test')
    assert parser.get_leading_countable("chapter Thirty One, test") == ('chapter', '31', ', test')
    assert parser.get_leading_countable("chapter seventeen, test") == ('chapter', '17', ', test')

    assert parser.get_leading_countable("page 1213") == ('page', '1213', '')
    assert parser.get_leading_countable("page 1,213") == ('page', '1213', '')
    assert parser.get_leading_countable("pages 12,13") ==  ('page', '12', ',13')
    assert parser.get_leading_countable("pages 12, 13") ==  ('page', '12', ', 13')
    assert parser.get_leading_countable("Issue 32, 9 October 2013, page 11:") ==  ('issue', '32', ', 9 October 2013, page 11:')

    #assert parser.get_leading_countable('EPM Publications') == None
    #"pages 12, 13") ==  ('page', '12', ',', '13', '')

def test_get_leading_italics():
    assert parser.get_leading_italics("'''''bold''''' stuff") == ("'''bold'''", " stuff")
    assert parser.get_leading_italics("''The ''''Nice Guy'''<nowiki>'</nowiki> Syndrome'', Self-Help Informational Resources") == ("The ''''Nice Guy'''<nowiki>'</nowiki> Syndrome", ', Self-Help Informational Resources')

def test_get_leading_start_stop():
    assert parser.get_leading_start_stop("[", "]", "[foo] bar") == ('foo', ' bar')
    assert parser.get_leading_start_stop("[", "]", "[fo{{w|X]X}}o] bar") == ('fo{{w|X]X}}o', ' bar')


def test_nice():
    #text="""'''1999''', ''The ''''Nice Guy'''<nowiki>'</nowiki> Syndrome'', Self-Help Informational Resources, The Counseling Center for Human Development, The University of South Florida [https://web.archive.org/web/19991013184527/http://usfweb.usf.edu/counsel/self-hlp/niceguy.htm]"""
    #text = """'''2002''', Laura Schlessinger (quoting a correspondent, "Herb"), ''Ten Stupid Things Couples Do to Mess Up Their Relationships'' (page 6)"""
    #text="""'''2004''', Keith Smith, ''Re: A Jacobite Stamp''[http://groups.google.co.uk/group/alt.talk.royalty/msg/bc020a3dbfbd96b0], alt.talk.royalty ''Usenet''"""
    #text="""'''1591''', [[w:William Shakespeare|Shakespeare]] (disputed), ''The True Tragedie of Richard Duke of York, and the Death of Good King Henrie the Sixt'', Thomas Millington (octavo, 1595), read in Alexander Dyce, Robert Dodsley, Thomas Amyot, ''A Supplement to Dodsley's Old Plays'', Shakespeare Society (1853) [http://books.google.com/books?vid=OCLC04162141&id=zbqQPlMoKyoC&pg=RA2-PA176&lpg=RA2-PA176&dq=%22wilt+thou+stab+Caesar%22&num=100 p. 176], [note that although this play is generally believed to be an early version of ''[[w:Henry_VI%2C_part_3|Henry VI, Part Three]]'', the phrase does not appear in the latter (or in the 1600 edition of the former)]"""
    #text="""'''2012''', Ms Patricia MacCormack, ''Cinesexuality'':"""
    #text="""'''1994''', Annukka Aukio (ed.), Rauni Vornanen (ed.), ''Uusi sivistyssanakirja'', Otava, Keuruu, 14th ed."""
    #text="""'''1983''', {{w|Alasdair Gray}}, ‘The Great Bear Cult’, Canongate 2012 (''Every Short Story 1951-2012''), p. 57:"""
    #text="""'''2010''', Knud H. Thomsen, Knud H. Thomsen (Pichard), ''Klokken i Makedonien'', Gyldendal A/S ({{ISBN|9788702104905}})"""
    #text="""'''2021''', Leo Löwenthal; unter Mitarbeit von Norbert Guterman; Susanne Hoppmann-Löwenthal (transl.): ''Falsche Propheten: Studien zur faschistischen Agitation'', 1st edition, Berlin: Suhrkamp, {{ISBN|978-3-518-58762-1}}, page 114:<br />Translation:<br />'''1949''', [[w:Leo Löwenthal|Leo Löwenthal]], [[w:Norbert Guterman|Norbert Guterman]]: ''[[w:Prophets of Deceit|Prophets of Deceit: A Study of the Techniques of the American Agitator]]'', New York: Harper & Brothers, page [https://archive.org/details/ProphetsOfDeceitAStudyOfTheTechniquesOfTheAmericanAgitator1949/page/n88/mode/1up 69]:"""
    #text="""'''2001''', {{w|Anthea Bell}}, translating WG Sebald, ''Austerlitz'', Penguin 2011, p. 122"""
    #text="""'''2007''' [publication date], Maggie Bullock, "Home Improvement", [[w:Elle|''Elle'']], January 2008 ed., page 108,"""
    #text="""'''1789''', {{w|Edward Gibbon}}, letter to {{w|John Baker Holroyd, 1st Earl of Sheffield|Lord Sheffield}} dated August 1789, in ''Miscellaneous Works,'' London: A. Strahan ''[[et al.]],'' 1796, p.{{nbsp}}201,<sup>[http://name.umdl.umich.edu/004849601.0001.001]</sup>"""
    #text="""'''1588''', {{w|Y Beibl cyssegr-lan}}, Genesis 28:15:"""
    #text="""'''2005''' Muhammad Khalid Masud et al - Dispensing Justice in Islam: Qadis and Their Judgements"""

    #assert parser.get_params(text) == "X"
    pass

def test_get_leading_newsgroup():
    assert parser.get_leading_newsgroup("on newsgroup ''rec.games.programmer''") == ('rec.games.programmer', '')
    assert parser.get_leading_newsgroup("in {{monospace|soc.culture.palestine}}, ''Usenet'':") == ('soc.culture.palestine', ":")
    assert parser.get_leading_newsgroup("{{monospace|net.unix-wizards}}") == ('net.unix-wizards', '')
    assert parser.get_leading_newsgroup("{{monospace|soc.culture.palestine}}, ''Usenet'':") == ('soc.culture.palestine', ":")
    assert parser.get_leading_newsgroup("soc.culture.palestine blah") == ('soc.culture.palestine', "blah")

def test_get_leading_bold():
    assert parser.get_leading_bold("'''''italics''''' stuff") == ("''italics''", " stuff")

def test_strip_wrapper_templates():
    assert parser.strip_wrapper_templates("ABC", ["temp1", "temp2"]) == "ABC"
    assert parser.strip_wrapper_templates("{{temp1|ABC}}", ["temp1"]) == "ABC"
    assert parser.strip_wrapper_templates("{{temp1|ABC}}", ["ABC", "temp1"]) == "ABC"
    assert parser.strip_wrapper_templates("AB{{temp1|blah}}CD {{temp2|X}} X{{temp1| x }}X {{temp1|{{temp2|ABC}}}}", ["temp1", "temp2"]) == \
            "ABblahCD X X x X ABC"


