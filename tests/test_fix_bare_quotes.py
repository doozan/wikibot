from autodooz.fix_bare_quotes import QuoteFixer
from autodooz.quotes.parser import QuoteParser, Parsed, LINK
from collections import defaultdict

#from ..fix_bare_quotes import QuoteFixer
fixer = QuoteFixer(debug=True)


def test_parse_text():

    for text, expected in [
        ( "", [] ),
        (
            " a song",
            [Parsed(type='classifier', values=[{'song': 'a song'}], orig='a song')]
        ),
        (
            """'''2007''', William D. Popkin, ''Evolution of the Judicial Opinion: Institutional and Individual Styles'', NYU Press ({{ISBN|9780814767498}}), page 104:""",
#            [Parsed(type='year', values=['2007'], orig="'''2007''', "), Parsed(type='author', values=['William D. Popkin'], orig=None), Parsed(type='separator', values=[', '], orig=', '), Parsed(type='italics', values=['Evolution of the Judicial Opinion: Institutional and Individual Styles'], orig=None), Parsed(type='separator', values=[', '], orig=', '), Parsed(type='publisher', values=['NYU Press'], orig='NYU Press'), Parsed(type='separator', values=[' '], orig=' '), Parsed(type='paren::isbn', values=[['9780814767498']], orig='{{ISBN|9780814767498}}'), Parsed(type='separator', values=[', '], orig=', '), Parsed(type='page', values=['104'], orig='page 104'), Parsed(type='separator', values=[':'], orig=':')]
#            [Parsed(type='year', values=['2007'], orig="'''2007''', "), Parsed(type='author', values=['William D. Popkin'], orig=None), Parsed(type='separator', values=[', '], orig=', '), Parsed(type='italics', values=['Evolution of the Judicial Opinion: Institutional and Individual Styles'], orig="''Evolution of the Judicial Opinion: Institutional and Individual Styles''"), Parsed(type='separator', values=[', '], orig=', '), Parsed(type='publisher', values=['NYU Press'], orig='NYU Press'), Parsed(type='separator', values=[' '], orig=' '), Parsed(type='paren::isbn', values=[['9780814767498']], orig='{{ISBN|9780814767498}}'), Parsed(type='section', values=['page 104'], orig=', page 104')]
            [Parsed(type='year', values=['2007'], orig="'''2007''', "), Parsed(type='author', values=['William D. Popkin'], orig=None), Parsed(type='separator', values=[', '], orig=', '), Parsed(type='italics', values=['Evolution of the Judicial Opinion: Institutional and Individual Styles'], orig="''Evolution of the Judicial Opinion: Institutional and Individual Styles''"), Parsed(type='separator', values=[', '], orig=', '), Parsed(type='publisher', values=['NYU Press'], orig='NYU Press'), Parsed(type='separator', values=[' '], orig=' '), Parsed(type='paren::isbn', values=[['9780814767498']], orig='{{ISBN|9780814767498}}'), Parsed(type='separator', values=[', '], orig=', '), Parsed(type='page', values=['104'], orig='page 104')]

        ),
        (
            """'''2006''', John G. Radcliffe, ''The Geometry of Hyperbolic Manifolds of Dimension a least 4'', András Prékopa, Emil Molnár (editors), ''Non-Euclidean Geometries: János Bolyai Memorial Volume'', [https://books.google.com.au/books?id=ZXgKflOpXc8C&pg=PA270&dq=%22120-cell%22%7C%22120-cells%22&hl=en&sa=X&ved=0ahUKEwjb3q7Siu3MAhUj5aYKHYosD-IQ6AEIWDAM#v=onepage&q=%22120-cell%22%7C%22120-cells%22&f=false page 270],""",
            #[Parsed(type='year', values=['2006'], orig="'''2006''', "), Parsed(type='author', values=['John G. Radcliffe'], orig=None), Parsed(type='separator', values=[', '], orig=', '), Parsed(type='italics', values=['The Geometry of Hyperbolic Manifolds of Dimension a least 4'], orig=None), Parsed(type='separator', values=[', '], orig=', '), Parsed(type='editor', values=['András Prékopa', 'Emil Molnár'], orig=None), Parsed(type='separator', values=[', '], orig=', '), Parsed(type='italics2', values=['Non-Euclidean Geometries: János Bolyai Memorial Volume'], orig=None), Parsed(type='separator', values=[', '], orig=', '), Parsed(type='url', values=LINK(target='https://books.google.com.au/books?id=ZXgKflOpXc8C&pg=PA270&dq=%22120-cell%22%7C%22120-cells%22&hl=en&sa=X&ved=0ahUKEwjb3q7Siu3MAhUj5aYKHYosD-IQ6AEIWDAM#v=onepage&q=%22120-cell%22%7C%22120-cells%22&f=false', text='page 270', orig='[https://books.google.com.au/books?id=ZXgKflOpXc8C&pg=PA270&dq=%22120-cell%22%7C%22120-cells%22&hl=en&sa=X&ved=0ahUKEwjb3q7Siu3MAhUj5aYKHYosD-IQ6AEIWDAM#v=onepage&q=%22120-cell%22%7C%22120-cells%22&f=false page 270]'), orig='[https://books.google.com.au/books?id=ZXgKflOpXc8C&pg=PA270&dq=%22120-cell%22%7C%22120-cells%22&hl=en&sa=X&ved=0ahUKEwjb3q7Siu3MAhUj5aYKHYosD-IQ6AEIWDAM#v=onepage&q=%22120-cell%22%7C%22120-cells%22&f=false page 270]'), Parsed(type='url::page', values=['270'], orig='page 270'), Parsed(type='separator', values=[','], orig=',')]
            [Parsed(type='year', values=['2006'], orig="'''2006''', "), Parsed(type='author', values=['John G. Radcliffe'], orig=None), Parsed(type='separator', values=[', '], orig=', '), Parsed(type='italics', values=['The Geometry of Hyperbolic Manifolds of Dimension a least 4'], orig="''The Geometry of Hyperbolic Manifolds of Dimension a least 4''"), Parsed(type='separator', values=[', '], orig=', '), Parsed(type='editor', values=['András Prékopa', 'Emil Molnár'], orig=None), Parsed(type='separator', values=[', '], orig=', '), Parsed(type='italics2', values=['Non-Euclidean Geometries: János Bolyai Memorial Volume'], orig="''Non-Euclidean Geometries: János Bolyai Memorial Volume''"), Parsed(type='separator', values=[', '], orig=', '), Parsed(type='url', values=LINK(target='https://books.google.com.au/books?id=ZXgKflOpXc8C&pg=PA270&dq=%22120-cell%22%7C%22120-cells%22&hl=en&sa=X&ved=0ahUKEwjb3q7Siu3MAhUj5aYKHYosD-IQ6AEIWDAM#v=onepage&q=%22120-cell%22%7C%22120-cells%22&f=false', text='page 270', orig='[https://books.google.com.au/books?id=ZXgKflOpXc8C&pg=PA270&dq=%22120-cell%22%7C%22120-cells%22&hl=en&sa=X&ved=0ahUKEwjb3q7Siu3MAhUj5aYKHYosD-IQ6AEIWDAM#v=onepage&q=%22120-cell%22%7C%22120-cells%22&f=false page 270]'), orig='[https://books.google.com.au/books?id=ZXgKflOpXc8C&pg=PA270&dq=%22120-cell%22%7C%22120-cells%22&hl=en&sa=X&ved=0ahUKEwjb3q7Siu3MAhUj5aYKHYosD-IQ6AEIWDAM#v=onepage&q=%22120-cell%22%7C%22120-cells%22&f=false page 270]'), Parsed(type='url::page', values=['270'], orig='page 270')]

        )
    ]:
        print(text)
        res = fixer.parser.parse_text(text)
        print(res)
        assert res == expected

def test_get_fingerprint():

    for text, expected in [

        (
            """'''2002''', ''a'', '''1''', ''c'', '''2''', ''e'', '''3'''""",
            ('year', 'italics', 'bold', 'italics2', 'bold2', 'italics3', 'bold3')
        ),
        (
            """'''2007''', William D. Popkin, ''Evolution of the Judicial Opinion: Institutional and Individual Styles'', NYU Press ({{ISBN|9780814767498}}), page 104:""",
            ('year', 'author', 'italics', 'publisher', 'paren::isbn', 'page')

        ),
        (
            """'''2007''', Jonathan Small, ''Chic geek: Ex model {{w|Matthew Gray Gubler}} channels his inner [[nerd]] on ''{{w|Criminal Minds}}'', in ''{{w|TV guide}}'' '', February 26, p. 23:""",
            ('year', 'author', 'italics', 'unhandled<{{w|Criminal Minds}}>', 'italics2', 'journal', 'italics3', 'date', 'page'),
#            ('year', 'author', 'italics', 'unhandled<{{w|Criminal Minds}}>', 'italics2', 'journal', 'italics3', 'date', 'page')
#            ('year', 'author', 'italics', 'author2', 'italics2', 'author3', 'italics3', 'date', 'page')

        ),
        (
            """'''1583''', Robert Harrison, “A Little Treatise vppon the firste Verse of the 122. Psalm”, as printed in Leland Henry Carlson and Albert Peel (editors, 1953), ''Elizabethan Non-Conformist Texts, Volume II: The Writings of Robert Harrison and [[w:Robert Browne (Brownist)|Robert Browne]]'', Routledge (2003), {{ISBN|978-0-415-31990-4}}, [http://books.google.com/books?id=w5QDcRGBXi0C&pg=PA91&dq=woulders pages 91–92]:""",
            ('year', 'author', 'fancy_double_quotes', 'unhandled<as printed in Leland Henry Carlson and Albert Peel>', 'paren', 'italics', 'publisher', 'year2', 'isbn', 'url', 'url::pages')
        ),
        (
            """'''1925''', {{w|Ford Madox Ford}}, ''No More Parades'', Penguin 2012 (''Parade's End''), p. 397:""",
            ('year', 'author', 'italics', 'publisher', 'year2', 'paren::italics', 'page')
        ),
        (
            # TODO: Don't search "publisher" after "date"
            """'''2015''', Steven E. Kuehn, "I'm Printing Your Prescription Now, Ma'am", ''Pharmaceutical Manufacturing'', September 2015, Putnam Media, page 7:""",
#            ('year', 'author', 'double_quotes::unhandled<I>', 'double_quotes::section', 'italics', 'unhandled<September>', 'year2', 'publisher', 'page')
            ('year', 'author', 'double_quotes', 'italics', 'month', 'year2', 'publisher', 'page')
        ),


    ]:
        print("___")
        print(text)
        parsed = fixer.parser.parse_text(text)
        assert parsed
        print(parsed)
        fingerprint = fixer.get_fingerprint(parsed)
        print(fingerprint)
        assert fingerprint == expected



def test_get_paramsx():
    for text, expected in [
        (
            # Publisher not in () with no ISBN
            """'''2000''', Paul Wilkes, ''And They Shall Be My People: An American Rabbi and His Congregation'', Grove Press, p. 135:""",
            {"_source": "book", 'year': '2000', 'author': 'Paul Wilkes', 'title': 'And They Shall Be My People: An American Rabbi and His Congregation', 'page': '135', 'publisher': 'Grove Press'}
        ),
        (
            """'''2007''', Eli Maor, ''The Pythagorean Theorem: A 4,000-year History'', {{w|Princeton University Press}}, [https://books.google.com.au/books?id=Z5VoBGy3AoAC&pg=PA1&dq=%22Fermat%27s+Last+Theorem%22&hl=en&sa=X&ved=0ahUKEwiSltz2xMnWAhUMzLwKHcAiBiY4ZBDoAQhcMAk#v=onepage&q=%22Fermat's%20Last%20Theorem%22&f=false page 1],""",
            {"_source": "book", 'year': '2007', 'author': 'Eli Maor', 'title': 'The Pythagorean Theorem: A 4,000-year History', 'pageurl': "https://books.google.com.au/books?id=Z5VoBGy3AoAC&pg=PA1&dq=%22Fermat%27s+Last+Theorem%22&hl=en&sa=X&ved=0ahUKEwiSltz2xMnWAhUMzLwKHcAiBiY4ZBDoAQhcMAk#v=onepage&q=%22Fermat's%20Last%20Theorem%22&f=false", 'page': '1', 'publisher': '{{w|Princeton University Press}}'}
        ),
#        (
#            """'''1937''', [[w:Zora Neale Hurston|Zora Neale Hurston]], ''Their Eyes Were Watching God'', Harper (2000), page 107:""",
#            {"_source": "book", 'year': '1937', 'author': '[[w:Zora Neale Hurston|Zora Neale Hurston]]', 'title': 'Their Eyes Were Watching God', 'page': '107', 'publisher': 'Harper', 'year_published': '2000'}
#        ),


    ]:
        print(text)
        parsed = fixer.parser.get_parsed(text)
        res = fixer.convert_parsed_to_params(parsed)
        assert res == expected



def test_get_params_old():
    for text, expected in [
        (
            # google books link, page in link
            """'''2006''', W. Stanley Taft Jr. and James W. Mayer, ''The Science of Paintings'', {{ISBN|9780387217413}}, [https://books.google.ca/books?id=nobhBwAAQBAJ&pg=PA9&dq=%22deattributions%22&hl=en&sa=X&redir_esc=y#v=onepage&q=%22deattributions%22&f=false p. 9 (Google preview)]:""",
            {'year': '2006', 'author': 'W. Stanley Taft Jr.; James W. Mayer', 'title': 'The Science of Paintings', 'isbn': '9780387217413', 'pageurl': 'https://books.google.ca/books?id=nobhBwAAQBAJ&pg=PA9&dq=%22deattributions%22&hl=en&sa=X&redir_esc=y#v=onepage&q=%22deattributions%22&f=false', 'page': '9'}
        ),
        (
            # translator
            """'''2013''', Charles Dickens (tr. by Hans Jørgen Birkmose), ''Oliver Twist'', Klim ({{ISBN|9788771292855}})#""",
            {'year': '2013', 'translator': 'Hans Jørgen Birkmose', 'author': 'Charles Dickens', 'title': 'Oliver Twist', 'publisher': 'Klim', 'isbn': '9788771292855'}
        ),
        (
            # Title URL
            """'''2006''', Henrik Ibsen, trans. by Odd Tangerud, ''[http://www.gutenberg.org/files/20162/20162-h/20162-h.htm La kolonoj de la socio]'', {{ISBN|82-91707-52-9}}""",
            {'year': '2006', 'translator': 'Odd Tangerud', 'author': 'Henrik Ibsen', 'url': 'http://www.gutenberg.org/files/20162/20162-h/20162-h.htm', 'title': 'La kolonoj de la socio', 'isbn': '82-91707-52-9'}
        ),
        (
            # Translator first
            """'''2012''', Judit Szántó (translator), {{w|Kathy Reichs}}, ''Csont és bőr'', Ulpius-ház {{ISBN|978 963 254 598 1}}, chapter 11, page 169:""",
            {'year': '2012', 'translator': 'Judit Szántó', 'author': '{{w|Kathy Reichs}}', 'title': 'Csont és bőr', 'publisher': 'Ulpius-ház', 'isbn': '9789632545981', 'chapter': '11', 'page': '169'}
        ),
        (
            # reprint
            """'''1971''', Peter Brown, ''The World of Late Antiquity: AD 150—750'', Thames & Hudson LTD (2013 reprint), {{ISBN|0393958035}}, page 54.""",
            {'year': '1971', 'author': 'Peter Brown', 'title': 'The World of Late Antiquity: AD 150—750', 'page': '54', 'publisher': 'Thames & Hudson LTD', 'year_published': '2013', 'isbn': '0393958035'}
        ),
        (
            # illustrated edition
            """'''2001''', [[w:Yann Martel|Yann Martel]], ''Life of Pi'' (illustrated 2007 edition), {{ISBN|9780156035811}}, [http://books.google.ca/books?id=RmkhNOzuV5YC&pg=PA186&dq=%22calendar+day%22+subject:%22fiction%22&hl=en&sa=X&ei=ChOEU8PrEMiT8QHQxoC4Bw&ved=0CCwQ6AEwADgK#v=onepage&q=%22calendar%20day%22%20subject%3A%22fiction%22&f=false p. 186 (Google preview)]:""",
            {'year': '2001', 'author': '[[w:Yann Martel|Yann Martel]]', 'title': 'Life of Pi', 'pageurl': 'http://books.google.ca/books?id=RmkhNOzuV5YC&pg=PA186&dq=%22calendar+day%22+subject:%22fiction%22&hl=en&sa=X&ei=ChOEU8PrEMiT8QHQxoC4Bw&ved=0CCwQ6AEwADgK#v=onepage&q=%22calendar%20day%22%20subject%3A%22fiction%22&f=false', 'page': '186', 'year_published': '2007', 'isbn': '9780156035811'}
        ),
        (
            # ''et alii''
            """'''1964''': Nikolay Rimsky-Korsakov ''et alii'', ''Principles of orchestration: with musical examples drawn from his own works'', [http://books.google.co.uk/books?id=erS-2XR-kPUC&pg=PA112&dq=crescendi&ei=58nkSeaJIYyykASju4yfDQ page 112] ([http://store.doverpublications.com/0486212661.html DoverPublications.com]; {{ISBN|0486212661}}""",
            {'year': '1964', 'author': 'Nikolay Rimsky-Korsakov; et al', 'title': 'Principles of orchestration: with musical examples drawn from his own works', 'pageurl': 'http://books.google.co.uk/books?id=erS-2XR-kPUC&pg=PA112&dq=crescendi&ei=58nkSeaJIYyykASju4yfDQ', 'page': '112', 'publisher': '[http://store.doverpublications.com/0486212661.html DoverPublications.com]', 'isbn': '0486212661'}
        ),
        (
            # translator
            """'''1865''', [[w:Homer|Homer]] and [[w:Edward Smith-Stanley, 14th Earl of Derby|Edward Smith-Stanley, 14th Earl of Derby]] (translator), ''[[w:Iliad|Iliad]]'', volume 1, [http://books.google.co.uk/books?id=EEYbAAAAYAAJ&pg=PP14&dq=%22Heph%C3%A6stus%22&ei=PWSiSru7DYmGzATwjoCBCA#v=onepage&q=%22Heph%C3%A6stus%22&f=false page viii]:""",
            {'year': '1865', 'author': '[[w:Homer|Homer]]', 'translator': '[[w:Edward Smith-Stanley, 14th Earl of Derby|Edward Smith-Stanley, 14th Earl of Derby]]', 'title': '[[w:Iliad|Iliad]]', 'volume': '1', 'pageurl': 'http://books.google.co.uk/books?id=EEYbAAAAYAAJ&pg=PP14&dq=%22Heph%C3%A6stus%22&ei=PWSiSru7DYmGzATwjoCBCA#v=onepage&q=%22Heph%C3%A6stus%22&f=false', 'page': 'viii'}
        ),
        (
            # Strip (novel) from unparsed text
             """'''1959''', [[w:James Michener|James Michener]], ''[[w:Hawaii (novel)|Hawaii]]'' (novel),<sup >[http://books.google.com/books?id=1QHYAAAAMAAJ ]</sup> Fawcett Crest (1986), {{ISBN|9780449213353}}, page 737:""",
            {'year': '1959', 'author': '[[w:James Michener|James Michener]]', 'title': '[[w:Hawaii (novel)|Hawaii]]', 'pageurl': 'http://books.google.com/books?id=1QHYAAAAMAAJ', 'page': '737', 'publisher': 'Fawcett Crest', 'year_published': '1986', 'isbn': '9780449213353'}
        ),
        (
            # Strip (novel) from unparsed text
             """'''2003''', Karin Slaughter, ''A Faint Cold Fear'' (novel), HarperCollins, {{ISBN|978-0-688-17458-3}}, [http://books.google.com/books?id=n8yT5KxPzNAC&pg=PA169&dq=rolling page 169]:""",
            {'year': '2003', 'author': 'Karin Slaughter', 'title': 'A Faint Cold Fear', 'pageurl': 'http://books.google.com/books?id=n8yT5KxPzNAC&pg=PA169&dq=rolling', 'page': '169', 'publisher': 'HarperCollins', 'isbn': '978-0-688-17458-3'}
        ),
        (
            # Pages in link text
             """'''2009''', Steve Scott, ''Insiders - Outsiders'', {{ISBN|9781907172205}}, [http://books.google.ca/books?id=LKaOUC90pKUC&pg=PA37&dq=%22ashamed+me%22&hl=en&sa=X&ei=uPlIUqWICfPb4AOc34CACQ&ved=0CDoQ6AEwAjgK#v=snippet&q=%22ashamed%20me%22&f=false pp. 36-37 (Google preview)]:""",
            {'year': '2009', 'author': 'Steve Scott', 'title': 'Insiders - Outsiders', 'pageurl': 'http://books.google.ca/books?id=LKaOUC90pKUC&pg=PA37&dq=%22ashamed+me%22&hl=en&sa=X&ei=uPlIUqWICfPb4AOc34CACQ&ved=0CDoQ6AEwAjgK#v=snippet&q=%22ashamed%20me%22&f=false', 'pages': '36-37', 'isbn': '9781907172205'}
        ),
        (
            # multi ISBN
             """'''2008''': Martin Walters, ''Chinese Wildlife: A Visitor’s Guide'', [http://books.google.co.uk/books?id=yIqTV8t_ElAC&pg=PA25&dq=%22Chinese+grapefruit%22&ei=nJNLSv60J42mM7HXzK4K page 25] ([https://web.archive.org/web/20090917020647/http://www.bradt-travelguides.com/details.asp?prodid=177 Bradt Travel Guides]; {{ISBN|1841622206}}, 9781841622200)""",
            {'year': '2008', 'author': 'Martin Walters', 'title': 'Chinese Wildlife: A Visitor’s Guide', 'pageurl': 'http://books.google.co.uk/books?id=yIqTV8t_ElAC&pg=PA25&dq=%22Chinese+grapefruit%22&ei=nJNLSv60J42mM7HXzK4K', 'page': '25', 'publisher': '[https://web.archive.org/web/20090917020647/http://www.bradt-travelguides.com/details.asp?prodid=177 Bradt Travel Guides]', 'isbn': '1841622206', 'isbn2': '9781841622200'}
        ),
        (
            # Multiple editors
             """'''2014''', Cornel Sandvoss & Laura Kearns, "From Interpretive Communities to Interpretive Fairs: Ordinary Fandom, Textual Selection and Digital Media", in ''The Ashgate Research Companion to Fan Cultures'' (eds. Stijn Reijnders, Koos Zwaan, & Linda Duits), Ashgate (2014), {{ISBN|9781409455622}}, [https://books.google.com/books?id=sfTiBAAAQBAJ&pg=PA93&dq=%22aca-fans%22 page 93]:""",
            {'year': '2014', 'editor': 'Stijn Reijnders; Koos Zwaan; Linda Duits', 'author': 'Cornel Sandvoss; Laura Kearns', 'chapter': 'From Interpretive Communities to Interpretive Fairs: Ordinary Fandom, Textual Selection and Digital Media', 'title': 'The Ashgate Research Companion to Fan Cultures', 'pageurl': 'https://books.google.com/books?id=sfTiBAAAQBAJ&pg=PA93&dq=%22aca-fans%22', 'page': '93', 'publisher': 'Ashgate', 'isbn': '9781409455622'}
        ),
        (
            """'''2017''', Masaki Kohana ''et al.'', "A Topic Trend on P2P Based Social Media", in ''Advances in Network-Based Information Systems: The 20th International Conference on Network-Based Information Systems (NBiS-2017)'' (eds Leonard Barolli, Makoto Takizawa, & Tomoya Enokido), [https://www.google.com/books/edition/Advances_in_Network_Based_Information_Sy/W3syDwAAQBAJ?hl=en&gbpv=1&dq=%22instance%22+mastodon&pg=PA1140&printsec=frontcover page 1140]""",
            {'year': '2017', 'editor': 'Leonard Barolli; Makoto Takizawa; Tomoya Enokido', 'author': 'Masaki Kohana; et al', 'chapter': 'A Topic Trend on P2P Based Social Media', 'title': 'Advances in Network-Based Information Systems: The 20th International Conference on Network-Based Information Systems (NBiS-2017)', 'pageurl': 'https://www.google.com/books/edition/Advances_in_Network_Based_Information_Sy/W3syDwAAQBAJ?hl=en&gbpv=1&dq=%22instance%22+mastodon&pg=PA1140&printsec=frontcover', 'page': '1140'}
        ),
#        (
#            """'''1910''', Patrick Weston Joyce, ''[[s:English as we speak it in Ireland|English as we speak it in Ireland]]'', [[s:English as we speak it in Ireland/IV|chapter 5]]""",
#            {'year': '1910', 'author': 'Patrick Weston Joyce', 'title': '[[s:English as we speak it in Ireland|English as we speak it in Ireland]]', 'chapter': '[[s:English as we speak it in Ireland/IV|chapter 5]]'}
#        ),
#        (
            # Trailing date
    #'''2022''', Adela Suliman, "[https://www.washingtonpost.com/sports/2022/07/20/quidditch-quadball-name-change-jk-rowling/ Quidditch is now quadball, distancing game from J.K. Rowling, league says]", ''The Washington Post'', 20 July 2022:
    #'''2023''', Munza Mushtaq, ''[https://www.csmonitor.com/World/Making-a-difference/2023/0106/In-Sri-Lanka-Pastor-Moses-shows-the-power-of-a-free-lunch In Sri Lanka, Pastor Moses shows the power of a free lunch]'', in: The Christian Science Monitor, January 6 2023
#
#        ),
#        (
#            # Month Year
#            """'''2012''', Adam Mathew, "Mass Effect 3", ''PlayStation Magazine'' (Australia), April 2012, [https://archive.org/details/Official_AUS_Playstation_Magazine_Issue_067_2012_04_Derwent_Howard_Publishing_AU/page/60/mode/2up?q=me3 page 60]:""",
#            {'year': '2012', 'author': 'Adam Mathew', 'chapter': 'Mass Effect 3', 'title': 'PlayStation Magazine', 'month': 'April', 'url': 'https://archive.org/details/Official_AUS_Playstation_Magazine_Issue_067_2012_04_Derwent_Howard_Publishing_AU/page/60/mode/2up?q=me3', 'page': '60'}
#        ),
        (
            # Start-End for issue number
            """'''2004''' September-October, ''American Cowboy'', volume 11, number 2, page 53:""",
            {'year': '2004', 'issue': 'September-October', 'title': 'American Cowboy', 'volume': '11', 'number': '2', 'page': '53'}
        ),
        (
            # Lines
            """'''1850''' [[w:Dante Gabriel Rossetti|Dante Gabriel Rossetti]], ''The Blessed Damozel'', lines 103-108""",
            {'year': '1850', 'author': '[[w:Dante Gabriel Rossetti|Dante Gabriel Rossetti]]', 'title': 'The Blessed Damozel', 'lines': '103-108'}
        ),
        (
            # Line
            """'''1798''', [[w:William Cowper|William Cowper]], ''On Receipt of My Mother's Picture'', [https://web.archive.org/web/20090228072946/http://rpo.library.utoronto.ca/poem/564.html line 60]""",
            {'year': '1798', 'author': '[[w:William Cowper|William Cowper]]', 'title': "On Receipt of My Mother's Picture", 'line': '60', 'url': 'https://web.archive.org/web/20090228072946/http://rpo.library.utoronto.ca/poem/564.html'}
        ),
        (
            """'''1775''', María Francisca Isla y Losada, ''Romance''""",
             {'author': 'María Francisca Isla y Losada', 'title': 'Romance', 'year': '1775'}
        ),
        (
            # TODO: Extract and process the URL links individually
            # Then try to identify the URL class from the text
            #
            # [“"']*(URL)[”"']*
            """'''1874''', G. M. Towle (translating {{w|Jules Verne}}), ''{{w|Around the World in 80 Days}}''""",
             {'year': '1874', 'translator': 'G. M. Towle', 'author': '{{w|Jules Verne}}', 'title': '{{w|Around the World in 80 Days}}'}
        ),
#        (
            #  '''2011''', Joyce Cho and Višnja Rogošic, "Burning the Rules", ''PAJ: Journal of Performance and Art'', Volume 33, Number 2, May 2011:
            #  '''2016''', Sune Engel Rasmussen, ''The Guardian'', 22 August:
            #
            #  strip {{nowrap}} ?
            #   '''1759''', George Sale et al., ''The Modern Part of an Universal History'', {{nowrap|volume XXIX}}: ''History of the German Empire'', [http://books.google.com/books?id=dFtjAAAAMAAJ&pg=PA2 page&nbsp;2]:
            #
            #   '''1992''', ''Black Enterprise'' (volume 23, number 5, December 1992, page 66)
            #
            #   '''1998''', Derel Leebaert, ''Present at the Creation'', Derek Leebaert (editor), ''The Future of the Electronic Marketplace'', [http://books.google.com.au/books?id=yo43oViNGMgC&pg=PA24&dq=%22more|most+rapt%22+-intitle:%22%22+-inauthor:%22%22&hl=en&sa=X&ei=XJX6T6bVH6-XiAeDodTaBg&redir_esc=y#v=onepage&q=%22more|most%20rapt%22%20-intitle%3A%22%22%20-inauthor%3A%22%22&f=false page 24],
            #
            #   '''2014''', [[w:Paul Doyle (journalist)|Paul Doyle]], "[http://www.theguardian.com/football/2014/oct/18/southampton-sunderland-premier-league-match-report Southampton hammer eight past hapless Sunderland in barmy encounter]", ''The Guardian'', 18 October 2014:
    ]:
        expected = None
        print(text)
        parsed = fixer.parser.get_parsed(text)
        res = fixer.convert_parsed_to_params(parsed)
        assert res == expected

def test_get_params_unhandled():

    expected = None
    for text in [


        """'''2005''', {{w|Chamillionaire}} (featuring {{w|Krayzie Bone}}), "{{w|Ridin'}}", ''{{w|The Sound of Revenge}}'':""",


        # Fail if published date newer than citation date (usually used in journals, not needed here in a book citation)
        """'''1772''', {{w|Frances Burney}}, ''Journals & Letters'', Penguin 2001, 30 May:""",

        # Extra title, unhandled
        """'''2010''', S. Suzanne Nielsen, ed, ''Food Analysis, fourth edition'', {{ISBN|978-1-4419-1477-4}}, Chapter 12, "Traditional Methods for Mineral Analysis", page 213""",



        # Multiple URLS
        """'''2009''', Roger Ebert, ''Roger Ebert's Movie Yearbook 2010'',<sup >[http://books.google.com/books?id=-1aM7D_ymdAC ][http://www.amazon.com/Roger-Eberts-Movie-Yearbook-2010/dp/B003STCR2E ]</sup> Andrews McMeel Publishing, {{ISBN|978-0-7407-8536-8}}, page 363:""",



        # bad publisher
        """'''1964''', {{w|J. D. Salinger}} (author), Judit Gyepes (translator), ''Zabhegyező'' [''{{w|The Catcher in the Rye}}''], Budapest: Európa Könyvkiadó (1998), {{ISBN|9630764024}}, chapter 11, page 95:""",

        # crap after author
        """'''2004''', John P. Frayne and Madeleine Marchaterre, “Notes” to ''The Collected Works of W. B. Yeats, Volume IX: Early Articles and Reviews'', Scribner, {{ISBN|0-684-80730-0}}, [http://books.google.com/books?id=61IX00wwuYYC&pg=PA553&dq=in-memoriam page 553]:""",

        """'''2013''', [[w:Tom Hanks|Tom Hanks]], introduction to ''Two Sides of the Moon: Our Story of the Cold War Space Race'' by Alexei Leonov and David Scott, Open Road Media {{ISBN|9781480448742}}""",

        # crap after author
        """'''2004''', John P. Frayne and Madeleine Marchaterre, “Notes” to ''The Collected Works of W. B. Yeats, Volume IX: Early Articles and Reviews'', Scribner, {{ISBN|0-684-80730-0}}, [http://books.google.com/books?id=61IX00wwuYYC&pg=PA553&dq=in-memoriam page 553]:""",

        """#* '''2006''', Irvine Welsh, Federico Corriente Basús transl., ''Porno'', Anagrama ({{ISBN|9788433938565}})""",

        # Translator, extra junk
        """'''1974''': [[w:Plato|Plato]] (author) and Desmond Lee (translator), ''[[w:The Republic (Plato)|The Republic]]'' (2nd edition, revised; Penguin Classics; {{ISBN|0140440488}}, Translator’s Introduction, pages 51 and 53:""",


        """'''2010''', L. A. Banks, &quot;Dog Tired (of the Drama!)&quot;, in ''Blood Lite II: Overbite'' (ed. Kevin J. Anderson), Gallery Books (2010), {{ISBN|9781439187654}}, [http://books.google.com/books?id=5ckoF81np3sC&amp;pg=PA121&amp;dq=%22beta%22+%22alpha+males%22 page 121]:""",

        """'''1756''', {{w|Thomas Thistlewood}}, diary, quoted in '''2001''', Glyne A. Griffith, ''Caribbean Cultural Identities'', Bucknell University Press ({{ISBN|9780838754757}}), page 38:""",

        """'''1986''', Anthony Burgess, ''Homage to Qwert Yuiop'' (published as ''But Do Blondes Prefer Gentlemen?'' in USA)""",



        """'''2016''', "The Veracity Elasticity", season 10, episode 7 of ''{{w|The Big Bang Theory}}''""",



        # Fail on bad name
        """'''1885''', Joseph Parker,T''he people's Bible: discourses upon Holy Scripture'', volume 16, page 83""",

        # Multi chapter, should be journal
        """'''1935''', {{w|Arthur Leo Zagat}}, ''Girl of the Goat God'', in ''Dime Mystery Magazine'', November 1935, Chapter IV, [http://gutenberg.net.au/ebooks13/1304651h.html]""",


    ]:
        print(text)
        parsed = fixer.parser.get_parsed(text)
        res = fixer.convert_parsed_to_params(parsed)
        assert res == expected


#def test_aggressive():
#    fixer = QuoteFixer(debug=True, aggressive=True)
#
#    text = """'''1956''' [[Kawabata]], ''[[Snow Country]]''"""
#    res = fixer.get_params(text)
#    assert res == expected

def test_get_params_books():

    for text, expected_fingerprint, expected_params in [
        #( """ """, "", "" ),
#        (
#            """'''2008''', Austin Modine, "[http://www.theregister.co.uk/2008/10/16/internet_stimulates_brain_more_than_books_study/ Internet searches stimulate brain more than books]: Assuming good Google-fu", ''[[w:The Register|The Register]]'', October 16:""",
#            ('year', 'author', 'double_quotes', 'italics::journal', 'date')
#            ""
#        ),
        (
            # Publisher after page
            """'''1992''', {{w|Samuel Beckett}}, ''{{w|Dream of Fair to Middling Women}}'', p. 71. John Calder {{ISBN|978-0714542133}}:""",
            ('year', 'author', 'italics', 'page', 'publisher', 'isbn'),
            {'_source': 'book', 'year': '1992', 'author': '{{w|Samuel Beckett}}', 'title': '{{w|Dream of Fair to Middling Women}}', 'page': '71', 'publisher': 'John Calder', 'isbn': '978-0714542133'}
        ),
        (
            """'''1996''', Joan M. Drury, ''Silent Words'', Spinsters Ink, page [http://books.google.com/books?id=SYdaAAAAMAAJ&q=%22pick+up+some+McDonald%27s%22 36]:""",
            ('year', 'author', 'italics', 'publisher', 'url', 'url::page'),
            {'_source': 'book', 'year': '1996', 'author': 'Joan M. Drury', 'title': 'Silent Words', 'publisher': 'Spinsters Ink', 'pageurl': 'http://books.google.com/books?id=SYdaAAAAMAAJ&q=%22pick+up+some+McDonald%27s%22', 'page': '36'}
        ),
#        (
#            """'''2016''': "'BRAAAM!': The Sound that Invaded the Hollywood" by Adrian Daub, ''Longreads ''""",
#            ('year', 'double_quotes', 'author', 'italics::journal'),
#            ""
#        ),
        (
            """'''1903''', {{w|Giovanni Pascoli}}, ''Myricae'', Raffaello Giusti (1903), page [https://archive.org/stream/myricaep00pascuoft#page/86/mode/1up 86], “Il miracolo”:""",
            ('year', 'author', 'italics', 'publisher', 'year2', 'url', 'url::page', 'fancy_double_quotes'),
            {'_source': 'book', 'year': '1903', 'author': '{{w|Giovanni Pascoli}}', 'title': 'Myricae', 'publisher': 'Raffaello Giusti', 'pageurl': 'https://archive.org/stream/myricaep00pascuoft#page/86/mode/1up', 'page': '86', 'chapter': 'Il miracolo'}
        ),
        (
            """'''2007''', Tim Pooley, “The Uneasy Interface”, in Yuji Kawaguchi et al. (editors), ''Corpus-Based Perspectives in Linguistics'', John Benjamins Publishing Company, {{ISBN|978-90-272-3318-9}}, [http://books.google.com/books?id=0qrZwAZSQq4C&pg=PA175&dq=Torontarians page 175]:""",
            ('year', 'author', 'fancy_double_quotes', 'editor', 'italics', 'publisher', 'isbn', 'url', 'url::page'),
            {'_source': 'book', 'year': '2007', 'author': 'Tim Pooley', 'chapter': 'The Uneasy Interface', 'editors': 'Yuji Kawaguchi; et al', 'title': 'Corpus-Based Perspectives in Linguistics', 'publisher': 'John Benjamins Publishing Company', 'isbn': '978-90-272-3318-9', 'pageurl': 'http://books.google.com/books?id=0qrZwAZSQq4C&pg=PA175&dq=Torontarians', 'page': '175'}
        ),
        (
            """'''1989''', Richard Winston & al. translating [[w:Carl Jung|Carl Jung]] & al. as ''Memories, Dreams, Reflections'', p. 108:""",
            ('year', 'translator', 'author', 'italics', 'page'),
            {'_source': 'book', 'year': '1989', 'translators': 'Richard Winston; et al', 'author': '[[w:Carl Jung|Carl Jung]]; et al', 'title': 'Memories, Dreams, Reflections', 'page': '108'}
        ),
        (
            # Publisher location
            """'''2008''', David Squire et al, ''The First-Time Garden Specialist'' ({{ISBN|1845379268}}), page 12:""",
            ('year', 'author', 'italics', 'paren::isbn', 'page'),
            {'_source': 'book', 'year': '2008', 'author': 'David Squire; et al', 'title': 'The First-Time Garden Specialist', 'isbn': '1845379268', 'page': '12'}
        ),
        (
            """'''1759''', George Sale et al., ''The Modern Part of an Universal History'', {{nowrap|volume XXIX}}: ''History of the German Empire'', [http://books.google.com/books?id=dFtjAAAAMAAJ&pg=PA2 page&nbsp;2]""",
            ('year', 'author', 'italics', 'volume', 'italics2', 'url', 'url::page'),
            {'_source': 'book', 'year': '1759', 'author': 'George Sale; et al', 'chapter': 'The Modern Part of an Universal History', 'volume': 'XXIX', 'title': 'History of the German Empire', 'pageurl': 'http://books.google.com/books?id=dFtjAAAAMAAJ&pg=PA2', 'page': '2'}
        ),
        (
            # No publisher, date
            """'''1958''', [[w:John Kenneth Galbraith|John Kenneth Galbraith]], ''The Affluent Society'' (1998 edition), {{ISBN|9780395925003}}, [http://books.google.ca/books?id=IfH010hvIqcC&printsec=frontcover&source=gbs_ge_summary_r&cad=0#v=onepage&q=niggardly&f=false p. 186]:""",
            ('year', 'author', 'italics', 'paren::edition', 'isbn', 'url', 'url::page'),
            {'_source': 'book', 'year': '1958', 'author': '[[w:John Kenneth Galbraith|John Kenneth Galbraith]]', 'title': 'The Affluent Society', 'edition': '1998', 'isbn': '9780395925003', 'pageurl': 'http://books.google.ca/books?id=IfH010hvIqcC&printsec=frontcover&source=gbs_ge_summary_r&cad=0#v=onepage&q=niggardly&f=false', 'page': '186'}
        ),
        (
            # pages
            """'''1991''', Katie Hafner & [[w:John Markoff|John Markoff]], ''Cyberpunk: Outlaws and Hackers on the Computer Frontier'' (1995 revised edition), Simon and Schuster, {{ISBN|0684818620}}, pp. 255-256:""",
            ('year', 'author', 'italics', 'paren::edition', 'publisher', 'isbn', 'pages'),
            {'_source': 'book', 'year': '1991', 'author': 'Katie Hafner; [[w:John Markoff|John Markoff]]', 'title': 'Cyberpunk: Outlaws and Hackers on the Computer Frontier', 'edition': '1995 revised', 'publisher': 'Simon and Schuster', 'isbn': '0684818620', 'pages': '255-256'}
        ),
        (
            # ''et al.'' in editor
            """'''1842''', [[w:Solomon Ludwig Steinheim|Solomon Ludwig Steinheim]], "On the Perennial and the Ephemeral in Judaism" in ''The Jewish Philosophy Reader'' (2000), edited by Daniel H. Frank ''et al.'', {{ISBN|9780415168601}}, [http://books.google.ca/books?id=_UbNP_Y0edQC&dq=platitudinize+OR+platitudinizes+OR+platitudinized&q=%22platitudinized%2C%3A#v=snippet&q=%22platitudinized%2C%3A&f=false p. 402]:""",
            ('year', 'author', 'double_quotes', 'italics', 'year2', 'editor', 'isbn', 'url', 'url::page'),
            {'_source': 'book', 'year': '1842', 'author': '[[w:Solomon Ludwig Steinheim|Solomon Ludwig Steinheim]]', 'chapter': 'On the Perennial and the Ephemeral in Judaism', 'title': 'The Jewish Philosophy Reader', 'year_published': '2000', 'editors': 'Daniel H. Frank; et al', 'isbn': '9780415168601', 'pageurl': 'http://books.google.ca/books?id=_UbNP_Y0edQC&dq=platitudinize+OR+platitudinizes+OR+platitudinized&q=%22platitudinized%2C%3A#v=snippet&q=%22platitudinized%2C%3A&f=false', 'page': '402'},
        ),
        (
            # Chapter title
            """'''2009''', Cate Robertson, "Half-Crown Doxy", in ''Bitten: Dark Erotic Stories'' (ed. Susie Bright), Chronicle Books (2009), {{ISBN|9780811864251}}, [http://books.google.com/books?id=GWFpxR443xEC&pg=PA126&dq=%22his+grundle%22#v=onepage&q=%22his%20grundle%22&f=false page 126]:""",
            ('year', 'author', 'double_quotes', 'italics', 'paren::editor', 'publisher', 'year2', 'isbn', 'url', 'url::page'),
            {'_source': 'book', 'year': '2009', 'author': 'Cate Robertson', 'chapter': 'Half-Crown Doxy', 'title': 'Bitten: Dark Erotic Stories', 'editor': 'Susie Bright', 'publisher': 'Chronicle Books', 'isbn': '9780811864251', 'pageurl': 'http://books.google.com/books?id=GWFpxR443xEC&pg=PA126&dq=%22his+grundle%22#v=onepage&q=%22his%20grundle%22&f=false', 'page': '126'}
        ),
        (
            # Chapter title
             """'''2008''', Ian Black, "An earthquake hits Newcastle" in ''Geordies vs Mackems & Mackems vs Geordies'', Black & White Publishing {{ISBN|9781845028619}}, page 97""",
             ('year', 'author', 'double_quotes', 'italics', 'publisher', 'isbn', 'page'),
             {'_source': 'book', 'year': '2008', 'author': 'Ian Black', 'chapter': 'An earthquake hits Newcastle', 'title': 'Geordies vs Mackems & Mackems vs Geordies', 'publisher': 'Black & White Publishing', 'isbn': '9781845028619', 'page': '97'}
        ),
        (
             """'''1999''', K. Zakrzewska, R. Lavery, "Modelling DNA-protein interactions", in ''Computational Molecular Biology'' (edited by J. Leszczynski; {{ISBN|008052964X}}:""",
             ('year', 'author', 'double_quotes', 'italics', 'editor', 'isbn'),
             {'_source': 'book', 'year': '1999', 'author': 'K. Zakrzewska; R. Lavery', 'chapter': 'Modelling DNA-protein interactions', 'title': 'Computational Molecular Biology', 'editor': 'J. Leszczynski', 'isbn': '008052964X'}
        ),
        (
            """'''1999''', Mark Warren, ''Mark Warren's Atlas of Australian Surfing'', traveller's edition 1999, {{ISBN|0-7322-6731-5}}, page 103""",
            ('year', 'author', 'italics', 'edition', 'year2', 'isbn', 'page'),
            {'_source': 'book', 'year': '1999', 'author': 'Mark Warren', 'title': "Mark Warren's Atlas of Australian Surfing", 'edition': "traveller's", 'isbn': '0-7322-6731-5', 'page': '103'}
        ),
        (
            # Numbered edition
            """'''2007''', John Merryman, Rogelio Pérez-Perdomo, ''The Civil Law Tradition'', 3rd edition {{ISBN|0804768331}}, page 107:""",
            ('year', 'author', 'italics', 'edition', 'isbn', 'page'),
            {'_source': 'book', 'year': '2007', 'author': 'John Merryman; Rogelio Pérez-Perdomo', 'title': 'The Civil Law Tradition', 'edition': '3rd', 'isbn': '0804768331', 'page': '107'}
        ),
        (
            # Numbered edition
             """'''2007''', John Howells, Don Merwin, ''Choose Mexico for Retirement'', 10th edition {{ISBN|0762753544}}, page 49:""",
             ('year', 'author', 'italics', 'edition', 'isbn', 'page'),
             {'_source': 'book', 'year': '2007', 'author': 'John Howells; Don Merwin', 'title': 'Choose Mexico for Retirement', 'edition': '10th', 'isbn': '0762753544', 'page': '49'}
        ),
        (
            """'''1877''', {{w|John Harvey Kellogg}}, [https://web.archive.org/web/20140811201712/http://etext.virginia.edu/etcbin/ot2www-pubeng?specfile=%2Ftexts%2Fenglish%2Fmodeng%2Fpublicsearch%2Fmodengpub.o2w "Plain Facts for Old and Young"]:""",
            ('year', 'author', 'double_quotes::url', 'double_quotes::url::text'),
            {'_source': 'text', 'year': '1877', 'author': '{{w|John Harvey Kellogg}}', 'url': 'https://web.archive.org/web/20140811201712/http://etext.virginia.edu/etcbin/ot2www-pubeng?specfile=%2Ftexts%2Fenglish%2Fmodeng%2Fpublicsearch%2Fmodengpub.o2w', 'title': 'Plain Facts for Old and Young'}
        ),
        (
            """'''2012''', Frances Wilson, ‘Evergreen Architecture’, ''Literary Review'', 402:""",
            ('year', 'author', 'fancy_quote', 'italics::journal', 'section'),
            {'_source': 'journal', 'year': '2012', 'author': 'Frances Wilson', 'title': 'Evergreen Architecture', 'journal': 'Literary Review', 'section': '402'}
        ),
        (
            """'''1943''', {{w|William Saroyan}}, {{w|The Human Comedy (novel)|''The Human Comedy''}}, chapter 3,""",
            ('year', 'author', 'italics', 'chapter'),
            {'_source': 'book', 'year': '1943', 'author': '{{w|William Saroyan}}', 'title': '{{w|The Human Comedy (novel)|The Human Comedy}}', 'chapter': '3'}
        ),
        (
            """'''2001''', [[w:Ken Follett|Ken Follett]], [[w:Jackdaws|''Jackdaws'']], Dutton, {{ISBN|0525946284}}, page 359""",
            ('year', 'author', 'italics', 'publisher', 'isbn', 'page'),
            {'_source': 'book', 'year': '2001', 'author': '[[w:Ken Follett|Ken Follett]]', 'title': '[[w:Jackdaws|Jackdaws]]', 'publisher': 'Dutton', 'isbn': '0525946284', 'page': '359'}
        ),
        (
            """'''1876''', Ebenezer Thorne, [https://books.google.com/books?id=IdkNAAAAQAAJ ''The Queen of the Colonies, or, Queensland as I Knew It''], 58""",
            ('year', 'author', 'italics::url', 'italics::url::text', 'section'),
            {'_source': 'text', 'year': '1876', 'author': 'Ebenezer Thorne', 'url': 'https://books.google.com/books?id=IdkNAAAAQAAJ', 'title': 'The Queen of the Colonies, or, Queensland as I Knew It', 'section': '58'}
        ),
        (
            """'''1612''', {{w|Michael Drayton}}, {{w|Poly-Olbion}} song{{nbsp}}5 p.{{nbsp}}78[http://poly-olbion.exeter.ac.uk/the-text/full-text/song-6/]:""",
            ('year', 'author', 'unhandled<{{w|Poly-Olbion}}>', 'section', 'url'),
            {'_source': 'book', 'year': '1612', 'author': '{{w|Michael Drayton}}', 'title': '{{w|Poly-Olbion}}', 'section': 'song 5 p. 78', 'sectionurl': 'http://poly-olbion.exeter.ac.uk/the-text/full-text/song-6/'}
        ),
        (
            """'''1695''', {{w|John Woodward (naturalist)|John Woodward}}, ''An Essay toward a Natural History of the Earth and Terrestrial Bodies'', London: Richard Wilkin, Part 4, p.{{nbsp}}198,<sup>[http://name.umdl.umich.edu/A67007.0001.001]</sup>""",
            ('year', 'author', 'italics', 'location', 'publisher', 'section', 'url'),
            {'_source': 'book', 'year': '1695', 'author': '{{w|John Woodward (naturalist)|John Woodward}}', 'title': 'An Essay toward a Natural History of the Earth and Terrestrial Bodies', 'location': 'London', 'publisher': 'Richard Wilkin', 'section': 'Part 4, p. 198', 'url': 'http://name.umdl.umich.edu/A67007.0001.001'}
        ),
        (
            # Part, not yet handled
            """'''2002''', John Maynard, ''Aborigines and the ‘Sport of Kings’: Aboriginal Jockeys in Australian Racing History'', Aboriginal Studies Press (2013), {{ISBN|9781922059543}}, part II, {{gbooks|4erLAgAAQBAJ|96|streeted}}:""",
            ('year', 'author', 'italics', 'publisher', 'year2', 'isbn', 'section'),
#            ('year', 'author', 'italics', 'publisher', 'year2', 'section')
            {'_source': 'book', 'year': '2002', 'author': 'John Maynard', 'title': 'Aborigines and the ‘Sport of Kings’: Aboriginal Jockeys in Australian Racing History', 'publisher': 'Aboriginal Studies Press', 'year_published': '2013', 'isbn': '9781922059543', 'section': 'part II, {{gbooks|4erLAgAAQBAJ|96|streeted}}'},
        ),
        (
            # gbooks for page
            """'''2001''', Rudi Bekkers, ''Mobile Telecommunications Standards: GSM, UMTS, TETRA, and ERMES'', Artech House ({{ISBN|9781580532501}}), page {{gbooks|PrG2URuUfioC|250|patent|pool}}:""",
            ('year', 'author', 'italics', 'publisher', 'paren::isbn', 'section'),
            {'_source': 'book', 'year': '2001', 'author': 'Rudi Bekkers', 'title': 'Mobile Telecommunications Standards: GSM, UMTS, TETRA, and ERMES', 'publisher': 'Artech House', 'isbn': '9781580532501', 'section': 'page {{gbooks|PrG2URuUfioC|250|patent|pool}}'}
        ),
        (
            # roman numerals
            """'''2004''', Rob Shein, ''Zero-Day Exploit: Countdown to Darkness'', Syngress ({{ISBN|9780080543925}}), page [https://books.google.de/books?id=ddGYYKnja1UC&lpg=PR21&dq=%22zero-day%20exploit%22&pg=PR21#v=onepage&q=%22zero-day%20exploit%22&f=false xxi]:""",
            ('year', 'author', 'italics', 'publisher', 'paren::isbn', 'section'),
            {'_source': 'book', 'year': '2004', 'author': 'Rob Shein', 'title': 'Zero-Day Exploit: Countdown to Darkness', 'publisher': 'Syngress', 'isbn': '9780080543925', 'section': 'page [https://books.google.de/books?id=ddGYYKnja1UC&lpg=PR21&dq=%22zero-day%20exploit%22&pg=PR21#v=onepage&q=%22zero-day%20exploit%22&f=false xxi]'}
        ),
        (
            """'''1921''', John Griffin, "Trailing the Grizzly in Oregon", in ''Forest and Stream'', pages 389-391 and 421-424, republished by Jeanette Prodgers in '''1997''' in ''The Only Good Bear is a Dead Bear'', page 35:""",
            ('year', 'author', 'double_quotes', 'italics::journal', 'pages', 'unhandled<and 421-424, republished>', 'author2', 'year2', 'italics2', 'page'),
#            ('year', 'author', 'double_quotes', 'italics::journal', 'pages', 'unhandled<*>', 'author2', 'year2', 'italics2', 'page'),
            None
        ),
        (
            """'''2010''' June, Martha C. Howell, ''Commerce Before Capitalism in Europe, 1300–1600'', “Introduction”, [http://books.google.co.uk/books?id=ZKhZTqkqfkEC&pg=PA26&dq=%22Yprois%22&hl=en&sa=X&ei=pS_2ToSYCtP-8QP2zrmvAQ&ved=0CDsQ6AEwAQ#v=onepage&q=%22Yprois%22&f=false page 26], footnote 42""",
            ('year', 'month', 'author', 'italics', 'fancy_double_quotes', 'section'),
            {'_source': 'text', 'year': '2010', 'month': 'June', 'author': 'Martha C. Howell', 'title': 'Commerce Before Capitalism in Europe, 1300-1600', 'chapter': 'Introduction', 'section': '[http://books.google.co.uk/books?id=ZKhZTqkqfkEC&pg=PA26&dq=%22Yprois%22&hl=en&sa=X&ei=pS_2ToSYCtP-8QP2zrmvAQ&ved=0CDsQ6AEwAQ#v=onepage&q=%22Yprois%22&f=false page 26], footnote 42'}
        ),
        (
            """'''1877''', Victor Blüthgen, ''Aus gährender Zeit'', in: ''{{w|Die Gartenlaube}}'', year 1877, [[s:de:Seite:Die Gartenlaube (1877) 157.jpg|page 157]]:""",
            ('year', 'author', 'italics', 'italics::journal', 'year2', 'section'),
            {'_source': 'journal', 'year': '1877', 'author': 'Victor Blüthgen', 'title': 'Aus gährender Zeit', 'journal': '{{w|Die Gartenlaube}}', 'section': '[[s:de:Seite:Die Gartenlaube (1877) 157.jpg|page 157]]'}
            #('year', 'author', 'italics', 'italics::journal', 'year2', 'link', 'link::page'),
            #{'_source': 'journal', 'year': '1876', 'author': 'Victor Blüthgen', 'title': 'Aus gährender Zeit', 'journal': '{{w|Die Gartenlaube}}', 'page': '[[s:de:Seite:Die Gartenlaube (1877) 157.jpg|page 157]]'}
        ),
        (
            # Pages and no section, should be pages
            """'''1999''', Peter McPhee, ''Runner'', {{ISBN|1550286749}}, page 10:""",
            ('year', 'author', 'italics', 'isbn', 'page'),
            {'_source': 'book', 'year': '1999', 'author': 'Peter McPhee', 'title': 'Runner', 'isbn': '1550286749', 'page': '10'}
        ),
        (
            # Pages before section should be merged into section (and preserve original text)
            """'''1999''', Peter McPhee, ''Runner'', {{ISBN|1550286749}}, p. 10, caption:""",
            ('year', 'author', 'italics', 'isbn', 'section'),
            {'_source': 'text', 'year': '1999', 'author': 'Peter McPhee', 'title': 'Runner', 'isbn': '1550286749', 'section': 'p. 10, caption'}
        ),
        (
            # ''et al.'' multiple authors
            """'''2019''', Pierre Terjanian, Andrea Bayer, et al., ''The Last Knight: The Art, Armor, and Ambition of Maximilian I'', Metropolitan Museum of Art ({{ISBN|9781588396747}}), page 96:""",
            ('year', 'author', 'italics', 'publisher', 'paren::isbn', 'page'),
            {'_source': 'book', 'year': '2019', 'author': 'Pierre Terjanian; Andrea Bayer; et al', 'title': 'The Last Knight: The Art, Armor, and Ambition of Maximilian I', 'publisher': 'Metropolitan Museum of Art', 'isbn': '9781588396747', 'page': '96'}
        ),
        (
            # 1975 Dover Edition
            """'''1945''', Neva L. Boyd, ''Handbook of Recreational Games'', 1975 [[w:Dover Publications|Dover]] edition, {{ISBN|0486232042}}, [http://books.google.com/books?id=12qZwZpIwCIC&pg=PA16&dq=candlelight p.16]:""",
            ('year', 'author', 'italics', 'year2', 'publisher', 'isbn', 'url', 'url::page'),
            {'_source': 'book', 'year': '1945', 'author': 'Neva L. Boyd', 'title': 'Handbook of Recreational Games', 'pageurl': 'http://books.google.com/books?id=12qZwZpIwCIC&pg=PA16&dq=candlelight', 'page': '16', 'publisher': '[[w:Dover Publications|Dover]]', 'year_published': '1975', 'isbn': '0486232042'}
        ),
        (
            # Pages
            """'''1999''', Peter McPhee, ''Runner'', {{ISBN|1550286749}}, pp. 37{{ndash}}8:""",
            ('year', 'author', 'italics', 'isbn', 'pages'),
            {'_source': 'text', 'year': '1999', 'author': 'Peter McPhee', 'title': 'Runner', 'isbn': '1550286749', 'pages': '37-8'}
        ),
        (
            # publisher followed by ed.
            """'''1940''', [[w:Carson McCullers|Carson McCullers]], ''[[w:The Heart Is a Lonely Hunter|The Heart Is a Lonely Hunter]]'', 2004 Houghton Mifflin ed., {{ISBN|0618526412}}, page 306,""",
            ('year', 'author', 'italics', 'year2', 'publisher', 'isbn', 'page'),
#            ('year', 'author', 'italics::link', 'italics::link::text', 'year2', 'publisher', 'isbn', 'page'),

#            ('year', 'author', 'italics', 'year2', 'publisher', 'isbn', 'page'),
            {'_source': 'book', 'year': '1940', 'author': '[[w:Carson McCullers|Carson McCullers]]', 'title': '[[w:The Heart Is a Lonely Hunter|The Heart Is a Lonely Hunter]]', 'year_published': '2004', 'publisher': 'Houghton Mifflin', 'isbn': '0618526412', 'page': '306'}
        ),
        (
            # unnumbered page
             """'''2018''', Adrian Besley, ''BTS: Icons of K-Pop'', [https://books.google.com/books?id=QcxmDwAAQBAJ&pg=PT170&dq=%22army+are+clever%22 unnumbered page]:""",
            ('year', 'author', 'italics', 'url', 'url::page'),
            {'_source': 'book', 'year': '2018', 'author': 'Adrian Besley', 'title': 'BTS: Icons of K-Pop', 'pageurl': 'https://books.google.com/books?id=QcxmDwAAQBAJ&pg=PT170&dq=%22army+are+clever%22', 'page': 'unnumbered'}
        ),
        (
            # editors, author
            """'''1995''', Solomon Feferman, John W. Dawson, Jr., Warren Goldfarb, Charlers Parsons, Robert N. Solovay (editors), {{w|Kurt Gödel}}, ''Kurt Gödel: Collected Works: Volume III'', {{w|Oxford University Press}}, [https://books.google.com.au/books?id=gDzbuUwma5MC&pg=PA419&dq=%22Hausdorff+gap%22%7C%22Hausdorff+gaps%22&hl=en&newbks=1&newbks_redir=0&sa=X&ved=2ahUKEwjo-o7D9OT7AhVQJUQIHaSlBIgQ6AF6BAhXEAI#v=onepage&q=%22Hausdorff%20gap%22%7C%22Hausdorff%20gaps%22&f=false page 419]""",
            ('year', 'editor', 'author', 'italics', 'publisher', 'url', 'url::page'),
            {'_source': 'book', 'year': '1995', 'author': '{{w|Kurt Gödel}}', 'editors': 'Solomon Feferman; John W. Dawson, Jr.; Warren Goldfarb; Charlers Parsons; Robert N. Solovay', 'title': 'Kurt Gödel: Collected Works: Volume III', 'pageurl': 'https://books.google.com.au/books?id=gDzbuUwma5MC&pg=PA419&dq=%22Hausdorff+gap%22%7C%22Hausdorff+gaps%22&hl=en&newbks=1&newbks_redir=0&sa=X&ved=2ahUKEwjo-o7D9OT7AhVQJUQIHaSlBIgQ6AF6BAhXEAI#v=onepage&q=%22Hausdorff%20gap%22%7C%22Hausdorff%20gaps%22&f=false', 'page': '419', 'publisher': '{{w|Oxford University Press}}'}
        ),

#        (
#        # bold not italics
#            """'''1974''', Per Lord Hailsham, '''Smedleys Ltd v Breed [1974]2 All ER 21(HL) at 24'''""",
#            "",
#            ""
#        ),
        (
            """'''1319''', M. Lucas Álvarez & P. Lucas Domínguez (eds.), ''El monasterio de San Clodio do Ribeiro en la Edad Media''. Sada / A Coruña: Edicións do Castro, page 451:""",
            ('year', 'editor', 'italics', 'location', 'publisher', 'page'),
            {'_source': 'book', 'year': '1319', 'editors': 'M. Lucas Álvarez; P. Lucas Domínguez', 'title': 'El monasterio de San Clodio do Ribeiro en la Edad Media', 'location': 'Sada / A Coruña', 'publisher': 'Edicións do Castro', 'page': '451'}
        ),
#        (
#            """'''1999''', ''{{w|Survivor (novel)|Survivor}}'', {{w|Chuck Palahniuk}}""", "", ""
#        ),
        (
            # Trailing bare link
            """'''2000''', Edgar Allan Poe, translated by Edwin Grobe, ''La Falo de Uŝero-Domo'', Arizona-Stelo-Eldonejo, http://www.gutenberg.org/files/17425/17425-h/17425-h.htm""",
            ('year', 'author', 'translator', 'italics', 'publisher', 'url'),
            {'_source': 'text', 'year': '2000', 'author': 'Edgar Allan Poe', 'translator': 'Edwin Grobe', 'title': 'La Falo de Uŝero-Domo', 'publisher': 'Arizona-Stelo-Eldonejo', 'url': 'http://www.gutenberg.org/files/17425/17425-h/17425-h.htm'}
        ),
        (
            """'''1965''', Australia. Bureau of Mineral Resources, Geology and Geophysics, ''U-K-A. Wandoan No. 1, Queensland of Union Oil Development Corporation, Kern County Land Company and Australian Oil and Gas Corporation Limited''""",
            ('year', 'author', 'italics'),
            {'_source': 'text', 'year': '1965', 'author': 'Australia. Bureau of Mineral Resources, Geology and Geophysics', 'title': 'U-K-A. Wandoan No. 1, Queensland of Union Oil Development Corporation, Kern County Land Company and Australian Oil and Gas Corporation Limited'}
        ),
        (
            """'''1872'''. A. Braun, ''Die Ergebnisse der Sprachwissenschaft in populärer Darstellung'', Cassel, p. 78:""",
            ('year', 'author', 'italics', 'publisher', 'page'),
            {'_source': 'book', 'year': '1872', 'author': 'A. Braun', 'title': 'Die Ergebnisse der Sprachwissenschaft in populärer Darstellung', 'publisher': 'Cassel', 'page': '78'}
        ),
        (
            """'''1832''' Bell, James ''A system of geography, popular and scientific''""",
            ('year', 'author', 'italics'),
            {'_source': 'text', 'year': '1832', 'author': 'Bell, James', 'title': 'A system of geography, popular and scientific'}
        ),
        (
            # Chapter title in ''
            """'''2002''' Dave Margoshes, ''Faith, Hope, Charity'', in ''Purity of Absence'', Dundurn Press Ltd., {{ISBN|0888784198}}, page 106:""",
            ('year', 'author', 'italics', 'italics2', 'publisher', 'isbn', 'page'),
            {'_source': 'book', 'year': '2002', 'author': 'Dave Margoshes', 'chapter': 'Faith, Hope, Charity', 'title': 'Purity of Absence', 'page': '106', 'publisher': 'Dundurn Press Ltd.', 'isbn': '0888784198'}
        ),
        (
            # publisher followed by year
            """'''2007''' Rachel M. Harper: ''Brass Ankle Blues''. Simon&Schuster 2007. {{ISBN|0743296583}} page 88:""",
            ('year', 'author', 'italics', 'publisher', 'year2', 'isbn', 'page'),
            {'_source': 'book', 'year': '2007', 'author': 'Rachel M. Harper', 'title': 'Brass Ankle Blues', 'page': '88', 'publisher': 'Simon&Schuster', 'isbn': '0743296583'}
        ),
        (
            # colon after author
            """'''1996''' Sherman Alexie: ''Indian Killer'' {{ISBN|0-87113-652-X}} page 102:""",
            ('year', 'author', 'italics', 'isbn', 'page'),
            {'_source': 'book', 'year': '1996', 'author': 'Sherman Alexie', 'title': 'Indian Killer', 'isbn': '0-87113-652-X', 'page': '102'}
        ),

        (
            # Pages in link text
             """'''2006''', {{w|Alexander McCall Smith}}, ''Love Over Scotland'', Random House Digital (2007), {{ISBN|978-0-307-27598-1}}, [http://books.google.com/books?id=_SLjwNeumpoC&pg=PA242&dq=third-person pages 243-4]:""",
            ('year', 'author', 'italics', 'publisher', 'year2', 'isbn', 'url', 'url::pages'),
            {'_source': 'book', 'year': '2006', 'author': '{{w|Alexander McCall Smith}}', 'title': 'Love Over Scotland', 'publisher': 'Random House Digital', 'year_published': '2007', 'isbn': '978-0-307-27598-1', 'pageurl': 'http://books.google.com/books?id=_SLjwNeumpoC&pg=PA242&dq=third-person', 'pages': '243-4'}

        ),
        (
            # publisher is link
            """'''1996''', Marc Parent, ''Turning Stones'', [[w:Harcourt Brace & Company|Harcourt Brace & Company]], {{ISBN|0151002045}}, page 93,""",
            ('year', 'author', 'italics', 'publisher', 'isbn', 'page'),
            {'_source': 'book', 'year': '1996', 'author': 'Marc Parent', 'title': 'Turning Stones', 'page': '93', 'publisher': '[[w:Harcourt Brace & Company|Harcourt Brace & Company]]', 'isbn': '0151002045'}
        ),
        (
            # sup tags
            """'''1998''', [[w:Frank M. Robinson|Frank M. Robinson]] and Lawrence Davidson, ''Pulp Culture: The Art of Fiction Magazines'',<sup >[http://books.google.com/books?id=mhYfL6Dn5g8C ]</sup> Collectors Press, Inc., {{ISBN|1-888054-12-3}}, page 103""",
            ('year', 'author', 'italics', 'url', 'publisher', 'isbn', 'page'),
            {'_source': 'book', 'year': '1998', 'author': '[[w:Frank M. Robinson|Frank M. Robinson]]; Lawrence Davidson', 'title': 'Pulp Culture: The Art of Fiction Magazines', 'url': 'http://books.google.com/books?id=mhYfL6Dn5g8C', 'publisher': 'Collectors Press, Inc.', 'isbn': '1-888054-12-3', 'page': '103'}
        ),
#        (
#            # TODO: Don't failed names text to start with "and"
#            """'''2011''', Connie Green, Religious Diversity and Children's Literature, p 156""",
#            ('year', 'author', 'unhandled<*>', 'page')
#            None
#        ),
        (
            """'''2013''', Robert Miraldi, ''Seymour Hersh'', Potomac Books, Inc. ({{ISBN|9781612344751}}), page 187:""",
            ('year', 'author', 'italics', 'publisher', 'paren::isbn', 'page'),
            {'_source': 'book', 'year': '2013', 'author': 'Robert Miraldi', 'title': 'Seymour Hersh', 'publisher': 'Potomac Books, Inc.', 'isbn': '9781612344751', 'page': '187'}
        ),
        (
            # no publisher, period after title, colon after author
            """'''1993''' Oscar Hijuelos: ''The Fourteen Sisters of Emilio Montez O'Brien''. {{ISBN|0-14-023028-9}} page 75:""",
            ('year', 'author', 'italics', 'isbn', 'page'),
            {'_source': 'book', 'year': '1993', 'author': 'Oscar Hijuelos', 'title': "The Fourteen Sisters of Emilio Montez O'Brien", 'isbn': '0-14-023028-9', 'page': '75'}
        ),
        (
            # ''et al.''
            """'''1988''', Lewis B. Ware ''et al.'', ''Low-Intensity Conflict in the Third World,'' Air Univ. Press, {{ISBN|978-1585660223}}, p. 139:""",
            ('year', 'author', 'italics', 'publisher', 'isbn', 'page'),
            {'_source': 'book', 'year': '1988', 'author': 'Lewis B. Ware; et al', 'title': 'Low-Intensity Conflict in the Third World', 'page': '139', 'publisher': 'Air Univ. Press', 'isbn': '978-1585660223'}
#            {'_source': 'book', 'year': '1988', 'author': 'Lewis B. Ware', 'chapter': 'et al.', 'title': 'Low-Intensity Conflict in the Third World', 'publisher': 'Air Univ. Press', 'isbn': '978-1585660223', 'page': '139'}

        ),
        (
            # Parenthesis around publisher, isbn
            """'''1995''', Gill Van Hasselt, ''Childbirth: Your Choices for Managing Pain'' (Taylor Pub, {{ISBN|9780878339020}}):""",
            ('year', 'author', 'italics', 'paren::publisher', 'paren::isbn'),
            {'_source': 'text', 'year': '1995', 'author': 'Gill Van Hasselt', 'title': 'Childbirth: Your Choices for Managing Pain', 'publisher': 'Taylor Pub', 'isbn': '9780878339020'}
        ),
        (
            """'''1926''', Robertus Love, ''The Rise and Fall of Jesse James'', University of Nebraska, 1990:""",
            ('year', 'author', 'italics', 'publisher', 'year2'),
            {'_source': 'text', 'year': '1926', 'author': 'Robertus Love', 'title': 'The Rise and Fall of Jesse James', 'publisher': 'University of Nebraska', 'year_published': '1990'}
        ),
        (
            """'''2006''', M.Gori, M.Ernandes, G.Angelini, "Cracking Crosswords: The Computer Challenge", ''Reasoning, Action and Interaction in AI Theories and Systems: Essays Dedicated to Luigia Carlucci Aiello'', edited by Oliviero Stock, Marco Schaerf, Springer Science & Business Media {{ISBN|9783540379010}}, page 266""",
            ('year', 'author', 'double_quotes', 'italics', 'editor', 'publisher', 'isbn', 'page'),
            {'_source': 'book', 'year': '2006', 'author': 'M.Gori; M.Ernandes; G.Angelini', 'chapter': 'Cracking Crosswords: The Computer Challenge', 'title': 'Reasoning, Action and Interaction in AI Theories and Systems: Essays Dedicated to Luigia Carlucci Aiello', 'editors': 'Oliviero Stock; Marco Schaerf', 'publisher': 'Springer Science & Business Media', 'isbn': '9783540379010', 'page': '266'}
        ),
        (
            """'''1905''', {{w|Robert Louis Stevenson}}, ''Travels with a Donkey in the Cevennes'', [[s:Travels with a Donkey in the Cevennes/Velay|chapter 1]]""",
            ('year', 'author', 'italics', 'section'),
#            ('year', 'author', 'italics', 'link', 'link::chapter'),
#            None
# TODO: Handle links?
            {'_source': 'text', 'year': '1905', 'author': '{{w|Robert Louis Stevenson}}', 'title': 'Travels with a Donkey in the Cevennes', 'section': '[[s:Travels with a Donkey in the Cevennes/Velay|chapter 1]]'}
        ),
        (
            """'''1905''', [[w:Robert Louis Stevenson|Robert Louis Stevenson]], ''[[s:Travels_with_a_Donkey_in_the_Cevennes_(1905)|Travels with a Donkey in the Cévennes]]'', [[s:Travels with a Donkey in the Cevennes/The Country of the Camisards|page 166]]""",
            ('year', 'author', 'italics', 'section'),
            {'_source': 'text', 'year': '1905', 'author': '[[w:Robert Louis Stevenson|Robert Louis Stevenson]]', 'title': '[[s:Travels_with_a_Donkey_in_the_Cevennes_(1905)|Travels with a Donkey in the Cévennes]]', 'section': '[[s:Travels with a Donkey in the Cevennes/The Country of the Camisards|page 166]]'}
            #('year', 'author', 'italics::link', 'italics::link::text', 'link', 'link::page'),
#            None
            #('year', 'author', 'italics::link', 'italics::link::text', 'section'),
            #{'_source': 'text', 'year': '1905', 'author': '[[w:Robert Louis Stevenson|Robert Louis Stevenson]]', 'title': '[[s:Travels_with_a_Donkey_in_the_Cevennes_(1905)|Travels with a Donkey in the Cévennes]]', 'section': '[[s:Travels with a Donkey in the Cevennes/The Country of the Camisards|page 166]]'}
        ),
        (
            # Multiple pages
            """'''2013''', Terry Pratchett, ''Raising Steam'', Doubleday, {{ISBN|978-0-857-52227-6}}, pages 345–346:""",
            ('year', 'author', 'italics', 'publisher', 'isbn', 'pages'),
            {'_source': 'book', 'year': '2013', 'author': 'Terry Pratchett', 'title': 'Raising Steam', 'publisher': 'Doubleday', 'isbn': '978-0-857-52227-6', 'pages': '345-346'}

        ),
        (
            # Editor prefixed
            """'''2008''', ''The New Black Lace Book of Women's Sexual Fantasies'' (ed. Mitzi Szereto), Black Lace (2008), {{ISBN|9780352341723}}, [http://books.google.com/books?id=XI7MR8XZSh8C&pg=PA38&dq=%22alphas%22#v=onepage&q=%22alphas%22&f=false page 38]""",
            ('year', 'italics', 'paren::editor', 'publisher', 'year2', 'isbn', 'url', 'url::page'),
            {'_source': 'book', 'year': '2008', 'editor': 'Mitzi Szereto', 'title': "The New Black Lace Book of Women's Sexual Fantasies", 'pageurl': 'http://books.google.com/books?id=XI7MR8XZSh8C&pg=PA38&dq=%22alphas%22#v=onepage&q=%22alphas%22&f=false', 'page': '38', 'publisher': 'Black Lace', 'isbn': '9780352341723'}
        ),
        (
            """'''1875''', Arthur Crump, ''The Theory of Stock Exchange Speculation'' (page 28)""",
            ('year', 'author', 'italics', 'paren::page'),
            {'_source': 'book', 'year': '1875', 'author': 'Arthur Crump', 'title': 'The Theory of Stock Exchange Speculation', 'page': '28'}
        ),
        (
            """'''2008''', Paul Black, ''Pronominal Accretions in Pama-Nyungan'', in ''Morphology and Language History'' {{ISBN|9027290962}}, edited by Claire Bowern, Bethwyn Evans, Luisa Miceli)""",
            ('year', 'author', 'italics', 'italics2', 'isbn', 'editor'),
            {'_source': 'book', 'year': '2008', 'author': 'Paul Black', 'chapter': 'Pronominal Accretions in Pama-Nyungan', 'title': 'Morphology and Language History', 'isbn': '9027290962', 'editors': 'Claire Bowern; Bethwyn Evans; Luisa Miceli'}
        ),
        (
            """'''1727''', John Gaspar Scheuchzer translating Engelbert Kaempfer's ''History of Japan'', Vol. I, p. 287:""",
            ('year', 'translator', 'author', 'italics', 'volume', 'page'),
            {'_source': 'book', 'year': '1727', 'translator': 'John Gaspar Scheuchzer', 'author': 'Engelbert Kaempfer', 'title': 'History of Japan', 'volume': 'I', 'page': '287'}
        ),
        (
            # Volume
            """'''2008''', John L. Capinera, ''Encyclopedia of Entomology'' {{ISBN|1402062427}}, volume 4, page 3326:""",
            ('year', 'author', 'italics', 'isbn', 'volume', 'page'),
            {'_source': 'book', 'year': '2008', 'author': 'John L. Capinera', 'title': 'Encyclopedia of Entomology', 'volume': '4', 'page': '3326', 'isbn': '1402062427'}
        ),
        (
            # x, y, and z authors
            """'''2001''', Delys Bird, Robert Dixon, and Christopher Lee, ''Authority and Influence'', [http://books.google.co.uk/books?id=DABZAAAAMAAJ&q=ambilaevous&dq=ambilaevous&ei=QiuSSImiGIHAigHKibD6DA&pgis=1 page 54] (University of Queensland Press; {{ISBN|0702232033}}, 9780702232039)""",
            ('year', 'author', 'italics', 'url', 'url::page', 'paren::publisher', 'paren::isbn'),
            {'_source': 'book', 'year': '2001', 'author': 'Delys Bird; Robert Dixon; Christopher Lee', 'title': 'Authority and Influence', 'pageurl': 'http://books.google.co.uk/books?id=DABZAAAAMAAJ&q=ambilaevous&dq=ambilaevous&ei=QiuSSImiGIHAigHKibD6DA&pgis=1', 'page': '54', 'publisher': 'University of Queensland Press', 'isbn': '0702232033; 9780702232039'}
        ),
#        (
#            """'''1977''', Olga Kuthanová, translating Jan Hanzák & Jiří Formánek, ''The Illustrated Encyclopedia of Birds'', London 1992, p. 177:""",
#            ('year', 'translator', 'author', 'italics', 'location', 'year2', 'page'),
#            {'_source': 'book', 'year': '1977', 'translator': 'Olga Kuthanová', 'author': 'Jan Hanzák; Jiří Formánek', 'title': 'The Illustrated Encyclopedia of Birds', 'page': '177', 'location': 'London', 'year_published': '1992'}
#        ),
        (
            # Publisher in parenthesis, not handled - other items can be in parethensis
            """'''2010''' Frank Buchmann-Moller ''Someone to Watch Over Me: The Life and Music of Ben Webster'' (University of Michigan Press) {{ISBN|0472025988}} p.57""",
            ('year', 'author', 'italics', 'paren::publisher', 'isbn', 'page'),
            {'_source': 'book', 'year': '2010', 'author': 'Frank Buchmann-Moller', 'title': 'Someone to Watch Over Me: The Life and Music of Ben Webster', 'publisher': 'University of Michigan Press', 'isbn': '0472025988', 'page': '57'}
        ),
        (
            # Volume info, no publisher
            """'''2006''', Renaat Declerck, Susan Reed, Bert Cappelle, ''The Grammar of the English Verb Phrase'', vol. 1, ''The Grammar of the English Tense System'', {{ISBN|9783110185898}}, page 6:""",
            ('year', 'author', 'italics', 'volume', 'italics2', 'isbn', 'page'),
            {'_source': 'book', 'year': '2006', 'author': 'Renaat Declerck; Susan Reed; Bert Cappelle', 'chapter': 'The Grammar of the English Verb Phrase', 'volume': '1', 'title': 'The Grammar of the English Tense System', 'isbn': '9783110185898', 'page': '6'}
        ),
        (
            """'''2007''', William D. Popkin, ''Evolution of the Judicial Opinion: Institutional and Individual Styles'', NYU Press ({{ISBN|9780814767498}}), page 104:""",
            ('year', 'author', 'italics', 'publisher', 'paren::isbn', 'page'),
            {'_source': 'book', 'year': '2007', 'author': 'William D. Popkin', "title": 'Evolution of the Judicial Opinion: Institutional and Individual Styles', "publisher": "NYU Press", "isbn": "9780814767498", "page": "104"}
        ),
        (
            # No publisher
            """'''2017''', Rebecca Tuhus-Dubrow, ''Personal Stereo'' ({{ISBN|1501322834}}), page 45:""",
            ('year', 'author', 'italics', 'paren::isbn', 'page'),
            {'_source': 'book', 'year': '2017', 'author': 'Rebecca Tuhus-Dubrow', 'title': 'Personal Stereo', 'isbn': '1501322834', 'page': '45'}
        ),
        (
            # Multi authors
            """'''2015''', Thomas J. Gradel, Dick Simpson, ''Corrupt Illinois: Patronage, Cronyism, and Criminality'', University of Illinois Press ({{ISBN|9780252097034}}), page 117:""",
            ('year', 'author', 'italics', 'publisher', 'paren::isbn', 'page'),
            {'_source': 'book', 'year': '2015', 'author': 'Thomas J. Gradel; Dick Simpson', 'title': 'Corrupt Illinois: Patronage, Cronyism, and Criminality', 'publisher': 'University of Illinois Press', 'isbn': '9780252097034', 'page': '117'}
        ),
        (
            """'''1998''', Anton Pavlovich Chekhov, Ronald Hingley, ''Five Plays'', Oxford University Press, USA ({{ISBN|9780192834126}}), page 148:""",
            ('year', 'author', 'italics', 'publisher', 'paren::isbn', 'page'),
            {'_source': 'book', 'year': '1998', 'author': 'Anton Pavlovich Chekhov; Ronald Hingley', 'title': 'Five Plays', 'publisher': 'Oxford University Press, USA', 'isbn': '9780192834126', 'page': '148'}
        ),
        (
            # No publisher, no page
            """'''2013''', Larry Munson, Tony Barnhart, ''From Herschel to a Hobnail Boot: The Life and Times of Larry Munson'', Triumph Books ({{ISBN|9781623686826}}), page 52:""",
            ('year', 'author', 'italics', 'publisher', 'paren::isbn', 'page'),
            {'_source': 'book', 'year': '2013', 'author': 'Larry Munson; Tony Barnhart', 'title': 'From Herschel to a Hobnail Boot: The Life and Times of Larry Munson', 'publisher': 'Triumph Books', 'isbn': '9781623686826', 'page': '52'}
        ),
        (
            # page before ISBN
            """'''2011''', Steve Urick, ''Practical Christian Living'', p. 214 ({{ISBN|978-1-4520-8297-4}}):""",
            ('year', 'author', 'italics', 'page', 'paren::isbn'),
            {'_source': 'book', 'year': '2011', 'author': 'Steve Urick', 'title': 'Practical Christian Living', 'page': '214', 'isbn': '978-1-4520-8297-4'}
        ),
        (
            """'''1922''', {{w|Emily Post}}, ''{{w|Etiquette in Society, in Business, in Politics, and at Home}},'' New York: Funk & Wagnalls, 1923, Chapter 21, pp.{{nbsp}}338-9,<sup>[https://archive.org/details/etiquetteinsoci00postgoog]</sup>""",
            ('year', 'author', 'italics', 'location', 'publisher', 'year2', 'chapter', 'pages', 'url'),
            {'_source': 'book', 'year': '1922', 'author': '{{w|Emily Post}}', 'title': '{{w|Etiquette in Society, in Business, in Politics, and at Home}}', 'location': 'New York', 'publisher': 'Funk & Wagnalls', 'year_published': '1923', 'chapter': '21', 'pages': '338-9', 'url': 'https://archive.org/details/etiquetteinsoci00postgoog'}
        ),
        (
            # google link, chapter in link
            """'''2010''', Rachel Cohn, ''Very Lefreak'', Random House, {{ISBN|9780375895524}}, [http://books.google.com/books?id=B7jw88zb_jEC&pg=PT19&dq=Wikipediaing chapter 3]:""",
            ('year', 'author', 'italics', 'publisher', 'isbn', 'url', 'url::chapter'),
            {'_source': 'book', 'year': '2010', 'author': 'Rachel Cohn', 'title': 'Very Lefreak', 'publisher': 'Random House', 'isbn': '9780375895524', 'chapterurl': 'http://books.google.com/books?id=B7jw88zb_jEC&pg=PT19&dq=Wikipediaing', 'chapter': '3'}
        ),
        (
            """'''2007''', ''Introduction: Phonoplay: Recasting Film Music'', Daniel Goldmark, Lawrence Kramer, Richard D. Leppert (editors), ''Beyond the Soundtrack: Representing Music in Cinema'', [http://books.google.com.au/books?id=3E3sCFxtww4C&pg=PA1&dq=%22hobgoblin%22%7C%22hobgoblins%22&hl=en&sa=X&ei=-n-WU9rpC8egkwXQoIGwBA&redir_esc=y#v=onepage&q=%22hobgoblin%22%7C%22hobgoblins%22&f=false page 1] """,
            ('year', 'italics', 'editor', 'italics2', 'url', 'url::page'),
            {'_source': 'book', 'year': '2007', 'chapter': 'Introduction: Phonoplay: Recasting Film Music', 'editors': 'Daniel Goldmark; Lawrence Kramer; Richard D. Leppert', 'title': 'Beyond the Soundtrack: Representing Music in Cinema', 'pageurl': 'http://books.google.com.au/books?id=3E3sCFxtww4C&pg=PA1&dq=%22hobgoblin%22%7C%22hobgoblins%22&hl=en&sa=X&ei=-n-WU9rpC8egkwXQoIGwBA&redir_esc=y#v=onepage&q=%22hobgoblin%22%7C%22hobgoblins%22&f=false', 'page': '1'}
        ),
        (
            # (editors)
            """'''2005''', John Schaeffer, Doug Pratt (editors), ''Appendix'', ''Gaiam Real Goods Solar Living Sourcebook'', [http://books.google.com.au/books?id=im-No5TYyy8C&pg=PA517&dq=%22awg%22&hl=en&sa=X&ei=k5wEUbnbB8OhkQXZtoEY&redir_esc=y#v=onepage&q=%22awg%22&f=false page 517],""",
            ('year', 'editor', 'italics', 'italics2', 'url', 'url::page'),
            {'_source': 'book', 'year': '2005', 'editors': 'John Schaeffer; Doug Pratt', 'chapter': 'Appendix', 'title': 'Gaiam Real Goods Solar Living Sourcebook', 'pageurl': 'http://books.google.com.au/books?id=im-No5TYyy8C&pg=PA517&dq=%22awg%22&hl=en&sa=X&ei=k5wEUbnbB8OhkQXZtoEY&redir_esc=y#v=onepage&q=%22awg%22&f=false', 'page': '517'}
        ),
        (
            """'''1892''', Carl Deite translating William Theodore Brannt as ''A Practical Treatise on the Manufacture of Perfumery'', p. 230""",
            ('year', 'translator', 'author', 'italics', 'page'),
            {'_source': 'book', 'year': '1892', 'translator': 'Carl Deite', 'author': 'William Theodore Brannt', 'title': 'A Practical Treatise on the Manufacture of Perfumery', 'page': '230'}
        ),
        (
            # Sub-title
             """'''2006''', Timothy M. Gay, ''Tris Speaker'', ''The Rough-and-Tumble Life of a Baseball Legend'', U of Nebraska Press, {{ISBN|0803222068}}, page 37:""",
            ('year', 'author', 'italics', 'italics2', 'publisher', 'isbn', 'page'),
            {'_source': 'book', 'year': '2006', 'author': 'Timothy M. Gay', 'chapter': 'Tris Speaker', 'title': 'The Rough-and-Tumble Life of a Baseball Legend', 'publisher': 'U of Nebraska Press', 'isbn': '0803222068', 'page': '37'}
        ),
        (
            # '''''
            """'''2014''', Larisa Kharakhinova, ''Heart-to-heart letters: to MrRight from '''CCCP''''', Litres {{ISBN|9785457226449}}, page 22""",
            ('year', 'author', 'italics', 'publisher', 'isbn', 'page'),
            {'_source': 'book', 'year': '2014', 'author': 'Larisa Kharakhinova', 'title': "Heart-to-heart letters: to MrRight from '''CCCP'''", 'page': '22', 'publisher': 'Litres', 'isbn': '9785457226449'}
        ),
        (
            # OCLC instad of ISBN
            """'''1847''': Charles Sealsfield, ''Rambleton: A Romance of Fashionable Life in New-York during the Great Speculation of 1836'' {{OCLC|12337689}}, page 127""",
            ('year', 'author', 'italics', 'oclc', 'page'),
            {'_source': 'book', 'year': '1847', 'author': 'Charles Sealsfield', 'title': 'Rambleton: A Romance of Fashionable Life in New-York during the Great Speculation of 1836', 'page': '127', 'oclc': '12337689'}
        ),
        (
            # Publisher followed by "," page abbreviated
            """'''2016''', Justin O. Schmidt, ''The Sting of the Wild'', Johns Hopkins University Press, {{ISBN|978-1-4214-1928-2}}, p. 55""",
            ('year', 'author', 'italics', 'publisher', 'isbn', 'page'),
            {'_source': 'book', 'year': '2016', 'author': 'Justin O. Schmidt', 'title': 'The Sting of the Wild', 'publisher': 'Johns Hopkins University Press', 'isbn': '978-1-4214-1928-2', 'page': '55'}
        ),
        (
            # p.230
            """'''1994''', R. Jeffrey Ringer, ''Queer Words, Queer Images: Communication and Construction of Homosexuality'' {{ISBN|0814774415}}, p.230""",
            ('year', 'author', 'italics', 'isbn', 'page'),
            {'_source': 'book', 'year': '1994', 'author': 'R. Jeffrey Ringer', 'title': 'Queer Words, Queer Images: Communication and Construction of Homosexuality', 'isbn': '0814774415', 'page': '230'}
        ),
        (
            # p&nbsp;66
            """'''2003''', Gillian Cloke, ''This Female Man of God: Women and Spiritual Power in the Patristic Age, 350–450 AD'', Routledge, {{ISBN|9781134868254}}, [https://books.google.com/books?id=KCGIAgAAQBAJ&lpg=PA66&dq=%22inchastity%22&pg=PA66#v=onepage&q=%22inchastity%22&f=false p.&nbsp;66]:""",
            ('year', 'author', 'italics', 'publisher', 'isbn', 'url', 'url::page'),
            {'_source': 'book', 'year': '2003', 'author': 'Gillian Cloke', 'title': 'This Female Man of God: Women and Spiritual Power in the Patristic Age, 350-450 AD', 'publisher': 'Routledge', 'isbn': '9781134868254', 'pageurl': 'https://books.google.com/books?id=KCGIAgAAQBAJ&lpg=PA66&dq=%22inchastity%22&pg=PA66#v=onepage&q=%22inchastity%22&f=false', 'page': '66'}
        ),
#        (
#            # Semicolon separator for authors
#            """'''2013''', Judy Faust; Punch Faust, ''The MOTs File: Memories, Observations, and Thoughts'', AuthorHouse {{ISBN|9781491827123}}, page 88""",
#            ('year', 'author', 'italics', 'publisher', 'isbn', 'page'),
#            {'_source': 'book', 'year': '2013', 'author': 'Judy Faust; Punch Faust', 'title': 'The MOTs File: Memories, Observations, and Thoughts', 'publisher': 'AuthorHouse', 'isbn': '9781491827123', 'page': '88'}
#        ),
        (
            # ISBN last
            """'''2006''' Kelly Pyrek, ''Forensic Nursing'', page 514, {{ISBN|084933540X}}.""",
            ('year', 'author', 'italics', 'page', 'isbn'),
            {'_source': 'book', 'year': '2006', 'author': 'Kelly Pyrek', 'title': 'Forensic Nursing', 'page': '514', 'isbn': '084933540X'}
        ),
        (
            # Published year
             """'''1936''', {{w|George Weller}}, ''Clutch and Differential'', Ayer, 1970, {{ISBN|0836936590}}, page 196,""",
            ('year', 'author', 'italics', 'publisher', 'year2', 'isbn', 'page'),
            {'_source': 'book', 'year': '1936', 'author': '{{w|George Weller}}', 'title': 'Clutch and Differential', 'page': '196', 'publisher': 'Ayer', 'year_published': '1970', 'isbn': '0836936590'}
        ),
        (
            # Published year same as year
            """'''2007''', David J. Wishart, ''Encyclopedia of the Great Plains Indians'', University of Nebraska Press (2007), {{ISBN|0-8032-9862-5}}, [http://books.google.ca/books?id=646oX4hA8EkC&lpg=PA32&dq=%22quilled%22&pg=PA32#v=onepage&q=%22quilled%22&f=false page 32]:""",
            ('year', 'author', 'italics', 'publisher', 'year2', 'isbn', 'url', 'url::page'),
            {'_source': 'book', 'year': '2007', 'author': 'David J. Wishart', 'title': 'Encyclopedia of the Great Plains Indians', 'pageurl': 'http://books.google.ca/books?id=646oX4hA8EkC&lpg=PA32&dq=%22quilled%22&pg=PA32#v=onepage&q=%22quilled%22&f=false', 'page': '32', 'publisher': 'University of Nebraska Press', 'isbn': '0-8032-9862-5'}
        ),
        (
            # Publisher location
            """'''1978''', Marguerite V. Burke, ''The Ukrainian Canadians'', Toronto: Van Nostrand Reinhold, {{ISBN|0442298633}}, p 48:""",
            ('year', 'author', 'italics', 'location', 'publisher', 'isbn', 'page'),
            {'_source': 'book', 'year': '1978', 'author': 'Marguerite V. Burke', 'title': 'The Ukrainian Canadians', 'page': '48', 'publisher': 'Van Nostrand Reinhold', 'location': 'Toronto', 'isbn': '0442298633'}
        ),


        (
            # Author with , Jr.
            """'''2010''', E. San Juan, Jr., ''SUTRANG KAYUMANGGI'', Lulu.com {{ISBN|9780557274277}}, page 24""",
            ('year', 'author', 'italics', 'publisher', 'isbn', 'page'),
            {'_source': 'book', 'year': '2010', 'author': 'E. San Juan, Jr.', 'title': 'SUTRANG KAYUMANGGI', 'publisher': 'Lulu.com', 'isbn': '9780557274277', 'page': '24'}
        ),

        (
            # Double chapter declarations should be merged, warned, i dunno
            """'''1865''', Henry David Thoreau, ''Cape Cod'', Chapter IV. "The Beach", page 54.""",
            ('year', 'author', 'italics', 'chapter', 'double_quotes', 'page'),
            None
        ),
        (
            """'''2006''', John G. Radcliffe, ''The Geometry of Hyperbolic Manifolds of Dimension a least 4'', András Prékopa, Emil Molnár (editors), ''Non-Euclidean Geometries: János Bolyai Memorial Volume'', [https://books.google.com.au/books?id=ZXgKflOpXc8C&pg=PA270&dq=%22120-cell%22%7C%22120-cells%22&hl=en&sa=X&ved=0ahUKEwjb3q7Siu3MAhUj5aYKHYosD-IQ6AEIWDAM#v=onepage&q=%22120-cell%22%7C%22120-cells%22&f=false page 270],""",
            ('year', 'author', 'italics', 'editor', 'italics2', 'url', 'url::page'),
            {'_source': 'book', 'year': '2006', 'author': 'John G. Radcliffe', 'chapter': 'The Geometry of Hyperbolic Manifolds of Dimension a least 4', 'editors': 'András Prékopa; Emil Molnár', 'title': 'Non-Euclidean Geometries: János Bolyai Memorial Volume', 'pageurl': 'https://books.google.com.au/books?id=ZXgKflOpXc8C&pg=PA270&dq=%22120-cell%22%7C%22120-cells%22&hl=en&sa=X&ved=0ahUKEwjb3q7Siu3MAhUj5aYKHYosD-IQ6AEIWDAM#v=onepage&q=%22120-cell%22%7C%22120-cells%22&f=false', 'page': '270'}
        ),
        (
            """'''1995''', Michael Darnell, “Preverbal nominals in Colville-Okanagan” in Pamela Downing and Michael P. Noonan (eds.), ''Word Order in Discourse'', page 91:""",
            ('year', 'author', 'fancy_double_quotes', 'editor', 'italics', 'page'),
            {'_source': 'book', 'year': '1995', 'author': 'Michael Darnell', 'chapter': 'Preverbal nominals in Colville-Okanagan', 'editors': 'Pamela Downing; Michael P. Noonan', 'title': 'Word Order in Discourse', 'page': '91'}
        ),
        (
             """'''1955''', {{w|W. H. Auden}}, “Lakes” in ''Selected Poetry of W. H. Auden'', New York: Modern Library, 1959, p.{{nbsp}}149,<sup>[https://openlibrary.org/ia/selectedpoetry00whau]</sup>""",
             ('year', 'author', 'fancy_double_quotes', 'italics', 'location', 'publisher', 'year2', 'page', 'url'),
             {'_source': 'book', 'year': '1955', 'author': '{{w|W. H. Auden}}', 'chapter': 'Lakes', 'title': 'Selected Poetry of W. H. Auden', 'url': 'https://openlibrary.org/ia/selectedpoetry00whau', 'page': '149', 'publisher': 'Modern Library', 'year_published': '1959', 'location': 'New York'}
        ),
        (
            """'''1399''', M. Lucas Alvarez & M. J. Justo Martín (eds.), ''Fontes documentais da Universidade de Santiago de Compostela. Pergameos da serie Bens do Arquivo Histórico Universitario (Anos 1237-1537)''. Santiago: Consello da Cultura Galega, page 268:""",
            ('year', 'editor', 'italics', 'location', 'publisher', 'page'),
            {'_source': 'book', 'year': '1399', 'editors': 'M. Lucas Alvarez; M. J. Justo Martín', 'title': 'Fontes documentais da Universidade de Santiago de Compostela. Pergameos da serie Bens do Arquivo Histórico Universitario (Anos 1237-1537)', 'location': 'Santiago', 'publisher': 'Consello da Cultura Galega', 'page': '268'}
        ),
#        (
#            """'''1929''', {{w|Kurt Tucholsky}}, ''[[s:de:Das Lächeln der Mona Lisa (Sammelband)|Das Lächeln der Mona Lisa (Sammelband)]]'', [[w:Rowohlt|Ernst Rowohlt Verlag]], page 138:""",
#            ('year', 'author', 'italics::link', 'link', 'page'),
#            {'_source': 'book', 'year': '1929', 'author': '{{w|Kurt Tucholsky}}', 'title': '[[s:de:Das Lächeln der Mona Lisa (Sammelband)|Das Lächeln der Mona Lisa (Sammelband)]]', 'publisher': '[[w:Rowohlt|Ernst Rowohlt Verlag]]', 'page': '138'}
#        ),
        (
            # '''Year'''.
             """'''1931'''. George Saintsbury, ''A Consideration of Thackeray'', chapter V.""",
            ('year', 'author', 'italics', 'chapter'),
            {'_source': 'book', 'year': '1931', 'author': 'George Saintsbury', 'title': 'A Consideration of Thackeray', 'chapter': 'V'}
        ),
        (
            """'''1897''', Florence Marryat, ''The Blood of the Vampire'', Ch. xiv:""",
            ('year', 'author', 'italics', 'chapter'),
            {'_source': 'book', 'year': '1897', 'author': 'Florence Marryat', 'title': 'The Blood of the Vampire', 'chapter': 'xiv'}
        ),
        (
            """'''1976''', {{w|Angela Carter}}, ‘My Father's House’, in ''Shaking a Leg'', Vintage 2013, p. 19:""",
            ('year', 'author', 'fancy_quote', 'italics', 'publisher', 'year2', 'page'),
            {'_source': 'book', 'year': '1976', 'author': '{{w|Angela Carter}}', 'chapter': "My Father's House", 'title': 'Shaking a Leg', 'publisher': 'Vintage', 'year_published': '2013', 'page': '19'}
        ),
        (
            """'''1933''', {{w|James Hilton (novelist)|James Hilton}}, ''{{w|Lost Horizon}}'', New York: Pocket Books, 1939, Chapter Three, p. 59,<sup>[https://archive.org/details/isbn_0671664271]</sup>""",
            ('year', 'author', 'italics', 'location', 'publisher', 'year2', 'chapter', 'page', 'url'),
            {'_source': 'book', 'year': '1933', 'author': '{{w|James Hilton (novelist)|James Hilton}}', 'title': '{{w|Lost Horizon}}', 'location': 'New York', 'publisher': 'Pocket Books', 'year_published': '1939', 'chapter': '3', 'page': '59', 'url': 'https://archive.org/details/isbn_0671664271'}
        ),
        (
            """'''2010''', Erich-Norbert Detroy, Frank M. Scheelen, ''Jeder Kunde hat seinen Preis: So verhandeln Sie individuell und verkaufen erfolgreicher'' (ISBN: 3802924258), page 49:""",
            ('year', 'author', 'italics', 'paren::isbn', 'page'),
            {'_source': 'book', 'year': '2010', 'author': 'Erich-Norbert Detroy; Frank M. Scheelen', 'title': 'Jeder Kunde hat seinen Preis: So verhandeln Sie individuell und verkaufen erfolgreicher', 'isbn': '3802924258', 'page': '49'}
        ),
#        (
#            """'''2005''', [[w:Plato|Plato]], ''Sophist''. Translation by Lesley Brown. [[w:Stephanus pagination|234a]].""",
#            ('year', 'author', 'italics', 'translator', 'link', 'link::text')
#            ('year', 'author', 'italics', 'translator', 'page'),
#            {'_source': 'book', 'year': '2005', 'author': '[[w:Plato|Plato]]', 'title': 'Sophist', 'translator': 'Lesley Brown', 'page': '234a'}
#        ),
        (
            # BAD DATE, messes everything else up
            # TODO: Author shouldn't allow numbers?
            """'''1998''' May 37, "barbara trumpinski" (username), "[http://groups.google.com/group/alt.med.fibromyalgia/msg/62a64f0a538e48c0?q=ABEND kitten is '''ABEND''']", in {{monospace|alt.med.fibromyalgia}}, ''Usenet'':""",
            ('year', 'author', 'double_quotes', 'paren', 'double_quotes::url', 'double_quotes::url::text', 'newsgroup'),
            None
        ),
        (
            """'''1850''' Charles Dickens - Oliver Twist""",
            ('year', 'author', 'unhandled<Oliver Twist>'),
            None
        ),
        (
            """'''2016''', {{w|Alan Moore}}, ''Jerusalem'', Liveright 2016, page 180:""",
            ('year', 'author', 'italics::location', 'publisher', 'year2', 'page'),
            None
#            ('year', 'author', 'italics', 'publisher', 'year2', 'page'),
#            {'_source': 'book', 'year': '2016', 'author': '{{w|Alan Moore}}', 'title': 'Jerusalem', 'publisher': 'Liveright', 'page': '180'}
        ),
        (
            """'''2012''', Peter L. Duren, ''Invitation to Classical Analysis'', {{w|American Mathematical Society}}, [https://books.google.com.au/books?id=Jyov-EMgbC0C&pg=PA180&dq=%22Abel+sum%22%7C%22Abel+sums%22&hl=en&sa=X&ved=0ahUKEwjRq-_wiv7WAhVIErwKHTCgBakQ6AEIfTAP#v=onepage&q=%22Abel%20sum%22%7C%22Abel%20sums%22&f=false page 180],""",
            ('year', 'author', 'italics', 'publisher', 'url', 'url::page'),
            {'_source': 'book', 'year': '2012', 'author': 'Peter L. Duren', 'title': 'Invitation to Classical Analysis', 'publisher': '{{w|American Mathematical Society}}', 'pageurl': 'https://books.google.com.au/books?id=Jyov-EMgbC0C&pg=PA180&dq=%22Abel+sum%22%7C%22Abel+sums%22&hl=en&sa=X&ved=0ahUKEwjRq-_wiv7WAhVIErwKHTCgBakQ6AEIfTAP#v=onepage&q=%22Abel%20sum%22%7C%22Abel%20sums%22&f=false', 'page': '180'}
        ),
        (
            """'''1867''', {{w|Thomas Carlyle}}, ''Shooting Niagara: and After?'' London: Chapman and Hall, Chapter{{nbsp}}10, p.{{nbsp}}53,<sup>[https://archive.org/details/shootingniagaraa00carluoft/page/53/mode/1up?q=Acherontic]</sup>""",
            ('year', 'author', 'italics', 'location', 'publisher', 'chapter', 'page', 'url'),
            {'_source': 'book', 'year': '1867', 'author': '{{w|Thomas Carlyle}}', 'title': 'Shooting Niagara: and After?', 'location': 'London', 'publisher': 'Chapman and Hall', 'chapter': '10', 'page': '53', 'url': 'https://archive.org/details/shootingniagaraa00carluoft/page/53/mode/1up?q=Acherontic'}
        ),
        (
            """'''1925''', {{w|Ford Madox Ford}}, ''No More Parades'', Penguin 2012 (''Parade's End''), p. 397:""",
            ('year', 'author', 'italics', 'publisher', 'year2', 'paren::italics', 'page'),
            {'_source': 'book', 'year': '1925', 'author': '{{w|Ford Madox Ford}}', 'title': 'No More Parades', 'publisher': 'Penguin', 'year_published': '2012', 'series': "Parade's End", 'page': '397'}
        ),
        (
            """'''1968''' {{w|Kurt Vonnegut}}, ''Welcome to the Monkey House'', Delacorte Press, page xiv:""",
            ('year', 'author', 'italics', 'publisher', 'page'),
            {'_source': 'book', 'year': '1968', 'author': '{{w|Kurt Vonnegut}}', 'title': 'Welcome to the Monkey House', 'publisher': 'Delacorte Press', 'page': 'xiv'}
        ),
        (
            """'''2013''', Johan C. Thom, ''The Pythagorean Akousmata and Early Pythagoreanism'', Gabriele Cornelli, Richard McKirahan, Constantinos Macris (editors), ''On Pythagoreanism'', Walter de Gruyter, [https://books.google.com.au/books?id=1HLnBQAAQBAJ&pg=PA79&dq=%22Androcydes%22&hl=en&sa=X&ved=0ahUKEwjy4IGHmfXgAhUQAXIKHQy3DQ8Q6AEIPzAF#v=onepage&q=%22Androcydes%22&f=false page 79],""",
            ('year', 'author', 'italics', 'editor', 'italics2', 'publisher', 'url', 'url::page'),
            {'_source': 'book', 'year': '2013', 'author': 'Johan C. Thom', 'chapter': 'The Pythagorean Akousmata and Early Pythagoreanism', 'editors': 'Gabriele Cornelli; Richard McKirahan; Constantinos Macris', 'title': 'On Pythagoreanism', 'publisher': 'Walter de Gruyter', 'pageurl': 'https://books.google.com.au/books?id=1HLnBQAAQBAJ&pg=PA79&dq=%22Androcydes%22&hl=en&sa=X&ved=0ahUKEwjy4IGHmfXgAhUQAXIKHQy3DQ8Q6AEIPzAF#v=onepage&q=%22Androcydes%22&f=false', 'page': '79'}
        ),
        (
            """'''1434''', M. González Garcés (ed.), ''Historia de La Coruña. Edad Media''. A Coruña: Caixa Galicia, page 609:""",
            ('year', 'editor', 'italics', 'location', 'publisher', 'page'),
            {'_source': 'book', 'year': '1434', 'editor': 'M. González Garcés', 'title': 'Historia de La Coruña. Edad Media', 'location': 'A Coruña', 'publisher': 'Caixa Galicia', 'page': '609'}
        ),
        (
            """'''1943''', {{w|Mary Norton (author)|Mary Norton}}, ''The Magic Bed-Knob'', New York: Hyperion, Chapter 8,<sup>[https://archive.org/details/magicbedknoborho00nort]</sup>""",
            ('year', 'author', 'italics', 'location', 'publisher', 'chapter', 'url'),
            {'_source': 'book', 'year': '1943', 'author': '{{w|Mary Norton (author)|Mary Norton}}', 'title': 'The Magic Bed-Knob', 'location': 'New York', 'publisher': 'Hyperion', 'chapter': '8', 'url': 'https://archive.org/details/magicbedknoborho00nort'}
        ),
        (
            """'''1969''', {{w|Margaret Atwood}}, ''{{w|The Edible Woman}}'', New York: Popular Library, 1976, Chapter{{nbsp}}19, p.{{nbsp}}168,<sup>[https://archive.org/details/ediblewomana00atwo]</sup>""",
            ('year', 'author', 'italics', 'location', 'publisher', 'year2', 'chapter', 'page', 'url'),
            {'_source': 'book', 'year': '1969', 'author': '{{w|Margaret Atwood}}', 'title': '{{w|The Edible Woman}}', 'location': 'New York', 'publisher': 'Popular Library', 'year_published': '1976', 'chapter': '19', 'page': '168', 'url': 'https://archive.org/details/ediblewomana00atwo'}
        ),
        (
            """'''1903''', Alice M. Hayes and Matthew Horace Hayes, ''The Horsewoman: A Practical Guide to Side-Saddle Riding,'' London: Hurst and Blackett, p.{{nbsp}}96,<sup>[https://archive.org/details/horsewomanpracti00hayerich/page/96/mode/1up?q=%22apron+skirt%22]</sup>""",
            ('year', 'author', 'italics', 'location', 'publisher', 'page', 'url'),
            {'_source': 'book', 'year': '1903', 'author': 'Alice M. Hayes; Matthew Horace Hayes', 'title': 'The Horsewoman: A Practical Guide to Side-Saddle Riding', 'location': 'London', 'publisher': 'Hurst and Blackett', 'page': '96', 'url': 'https://archive.org/details/horsewomanpracti00hayerich/page/96/mode/1up?q=%22apron+skirt%22'}
        ),
        (
            """'''1954''', {{w|C. S. Lewis}}, ''{{w|The Horse and His Boy}}'', Collins, 1998, Chapter 1,""",
            ('year', 'author', 'italics', 'publisher', 'year2', 'chapter'),
            {'_source': 'book', 'year': '1954', 'author': '{{w|C. S. Lewis}}', 'title': '{{w|The Horse and His Boy}}', 'publisher': 'Collins', 'year_published': '1998', 'chapter': '1'}
        ),
        (
            """'''1977''', {{w|Alistair Horne}}, ''A Savage War of Peace'', New York Review Books 2006, p. 236:""",
            ('year', 'author', 'italics', 'publisher', 'year2', 'page'),
            {'_source': 'book', 'year': '1977', 'author': '{{w|Alistair Horne}}', 'title': 'A Savage War of Peace', 'publisher': 'New York Review Books', 'year_published': '2006', 'page': '236'}
        ),
#        (
#            """'''1877''', Antonio Ive, ''Canti popolari istriani: raccolti a Rovigno'', volume 5, Ermanno Loescher, page 68:""",
#            ('year', 'author', 'italics', 'volume', 'publisher', 'page'),
#            {'_source': 'book', 'year': '1877', 'author': 'Antonio Ive', 'title': 'Canti popolari istriani: raccolti a Rovigno', 'volume': '5', 'publisher': 'Ermanno Loescher', 'page': '68'}
#        ),
        (
            """'''1916''', {{w|Charles Wharton Stork}}, “Sea Song” in ''Sea and Bay: A Poem of New England'', New York: John Lane, p. 71,<sup>[https://archive.org/details/seaandbayapoemn00storgoog]</sup>""",
            ('year', 'author', 'fancy_double_quotes', 'italics', 'location', 'publisher', 'page', 'url'),
            {'_source': 'book', 'year': '1916', 'author': '{{w|Charles Wharton Stork}}', 'chapter': 'Sea Song', 'title': 'Sea and Bay: A Poem of New England', 'location': 'New York', 'publisher': 'John Lane', 'page': '71', 'url': 'https://archive.org/details/seaandbayapoemn00storgoog'}
        ),
        (
            """'''2014''', George Kenny, ''Gaawiin Mawisiiwag Anishinaabeg: Indians Don't Cry'', p.7:""",
            ('year', 'author', 'italics', 'page'),
            {'_source': 'book', 'year': '2014', 'author': 'George Kenny', 'title': "Gaawiin Mawisiiwag Anishinaabeg: Indians Don't Cry", 'page': '7'}
        ),
        (
            """'''1395''', Antonio López Ferreiro (ed.), ''Galicia Histórica. Colección diplomática''. Santiago: Tipografía Galaica, page 156:""",
            ('year', 'editor', 'italics', 'location', 'publisher', 'page'),
            {'_source': 'book', 'year': '1395', 'editor': 'Antonio López Ferreiro', 'title': 'Galicia Histórica. Colección diplomática', 'location': 'Santiago', 'publisher': 'Tipografía Galaica', 'page': '156'}
        ),
        (
            """'''2013''', Johan C. Thom, ''The Pythagorean Akousmata and Early Pythagoreanism'', Gabriele Cornelli, Richard McKirahan, Constantinos Macris (editors), ''On Pythagoreanism'', Walter de Gruyter, [https://books.google.com.au/books?id=1HLnBQAAQBAJ&pg=PA79&dq=%22Androcydes%22&hl=en&sa=X&ved=0ahUKEwjy4IGHmfXgAhUQAXIKHQy3DQ8Q6AEIPzAF#v=onepage&q=%22Androcydes%22&f=false page 79],""",
            ('year', 'author', 'italics', 'editor', 'italics2', 'publisher', 'url', 'url::page'),
            {'_source': 'book', 'year': '2013', 'author': 'Johan C. Thom', 'chapter': 'The Pythagorean Akousmata and Early Pythagoreanism', 'editors': 'Gabriele Cornelli; Richard McKirahan; Constantinos Macris', 'title': 'On Pythagoreanism', 'publisher': 'Walter de Gruyter', 'pageurl': 'https://books.google.com.au/books?id=1HLnBQAAQBAJ&pg=PA79&dq=%22Androcydes%22&hl=en&sa=X&ved=0ahUKEwjy4IGHmfXgAhUQAXIKHQy3DQ8Q6AEIPzAF#v=onepage&q=%22Androcydes%22&f=false', 'page': '79'}
        ),
        (
            """'''2010''', Erich-Norbert Detroy, Frank M. Scheelen, ''Jeder Kunde hat seinen Preis: So verhandeln Sie individuell und verkaufen erfolgreicher'' (ISBN: 3802924258), page 49:""",
            ('year', 'author', 'italics', 'paren::isbn', 'page'),
            {'_source': 'book', 'year': '2010', 'author': 'Erich-Norbert Detroy; Frank M. Scheelen', 'title': 'Jeder Kunde hat seinen Preis: So verhandeln Sie individuell und verkaufen erfolgreicher', 'isbn': '3802924258', 'page': '49'}
        ),

    ]:
        print("__")
        print(text)
        parsed = fixer.parser.get_parsed(text)
        print(parsed)
        fingerprint = fixer.get_fingerprint(parsed)
        print(fingerprint)
        assert fingerprint == expected_fingerprint

        parsed = fixer.parser.get_parsed(text)
        res = fixer.convert_parsed_to_params(parsed)
        print(res)
        assert res == expected_params

def test_get_params_song():

    for text, expected_fingerprint, expected_params in [
#        (
        (
            """'''1958''' [[w:Ritchie Valens|Ritchie Valens]] ''Donna'' ( a song) :""",
            ('year', 'author', 'italics', 'classifier'),
            {'_source': 'song', 'year': '1958', 'author': '[[w:Ritchie Valens|Ritchie Valens]]', 'title': 'Donna'}
        ),
    ]:

        print("__")
        print(text)
        parsed = fixer.parser.get_parsed(text)
        print(parsed)
        fingerprint = fixer.get_fingerprint(parsed)
        print(fingerprint)
        assert fingerprint == expected_fingerprint

        parsed = fixer.parser.get_parsed(text)
        res = fixer.convert_parsed_to_params(parsed)
        print(res)
        assert res == expected_params



def test_get_params_journal():

    for text, expected_fingerprint, expected_params in [
        #( """ """, "", "" ),
        (
            """'''2003''', November 17, ''The New Yorker'': "Connolly is an instinctive disturber of the peace, an enemy of blandness &mdash; of the beigists.""",
            ('date', 'italics::journal', 'unhandled<"Connolly is an instinctive disturber of the peace, an enemy of blandness - of the beigists>'),
            None
        ),
        (
            # Vol VI, no XXXII
            """'''1864''' "The Adventures of a Lady in Search of a Horse", ''London Society'' Vol VI, no XXXII (July 1864) [http://books.google.com/books?id=_NscAQAAIAAJ&dq=heepishly&pg=PA5#v=onepage&q=heepishly&f=false p. 5]""",
            ('year', 'double_quotes', 'italics::journal', 'section'),
            {'_source': 'journal', 'year': '1864', 'title': 'The Adventures of a Lady in Search of a Horse', 'journal': 'London Society', 'section': 'Vol VI, no XXXII (July 1864) [http://books.google.com/books?id=_NscAQAAIAAJ&dq=heepishly&pg=PA5#v=onepage&q=heepishly&f=false p. 5]'}

        ),
        (
            """'''2018''', July 5, {{w|Paul Krugman}}, [https://www.nytimes.com/2018/07/05/opinion/more-on-a-job-guarantee-wonkish.html “More on a Job Guarantee (Wonkish)”], ''The New York Times'':""",
            ('date', 'author', 'fancy_double_quotes::url', 'fancy_double_quotes::url::text', 'italics::journal'),
            {'_source': 'journal', 'date': 'July 5 2018', 'author': '{{w|Paul Krugman}}', 'titleurl': 'https://www.nytimes.com/2018/07/05/opinion/more-on-a-job-guarantee-wonkish.html', 'title': 'More on a Job Guarantee (Wonkish)', 'journal': 'The New York Times'}
        ),
        (
            """'''2021''', Julia Huang, ''[https://web.archive.org/web/20210814023137/https://www.pharmaceuticalonline.com/doc/what-is-a-cbe-filing-what-is-a-pas-what-s-the-difference-between-anda-and-nda-0001 What Is A CBE 30 Filing? What Is A PAS? What's The Difference Between ANDA And NDA?]'', "Pharmaceutical Online":""",
            ('year', 'author', 'italics::url', 'italics::url::text', 'double_quotes::journal'),
            {'_source': 'journal', 'year': '2021', 'author': 'Julia Huang', 'titleurl': 'https://web.archive.org/web/20210814023137/https://www.pharmaceuticalonline.com/doc/what-is-a-cbe-filing-what-is-a-pas-what-s-the-difference-between-anda-and-nda-0001', 'title': "What Is A CBE 30 Filing? What Is A PAS? What's The Difference Between ANDA And NDA?", 'journal': 'Pharmaceutical Online'}
        ),
#        (
#            """'''1992''', "[timarit.is/view_page_init.jsp?issId=269791&pageId=3833037&lang=da Usuni kipigaa]", ''Atuagagdliutit''""",
#            ('year', 'double_quotes::brackets', 'italics::journal'),
#            {'_source': 'journal', 'year': '1992', 'title': '[timarit.is/view_page_init.jsp?issId=269791&pageId=3833037&lang=da Usuni kipigaa]', 'journal': 'Atuagagdliutit'}
#        ),
        (
            """'''1992''', "[http://timarit.is/view_page_init.jsp?issId=269857&pageId=3834041&lang=da Meeqqakka]", ''Atuagagdliutit/Grønlandsposten''""",
            ('year', 'double_quotes::url', 'double_quotes::url::text', 'italics::journal'),
            {'_source': 'journal', 'year': '1992', 'titleurl': 'http://timarit.is/view_page_init.jsp?issId=269857&pageId=3834041&lang=da', 'title': 'Meeqqakka', 'journal': 'Atuagagdliutit/Grønlandsposten'}
        ),
        (
            """'''2015''' January 22, Daniel Gahn, "[https://www.abendzeitung-muenchen.de/inhalt.gaztro-zuckersuesse-suenden.f838d2ab-6fe6-4550-a392-80ef26a7eba6.html Zuckersüße Sünden]", in the ''Abendzeitung München'':""",
            ('date', 'author', 'double_quotes::url', 'double_quotes::url::text', 'italics::journal'),
            {'_source': 'journal', 'date': 'January 22 2015', 'author': 'Daniel Gahn', 'titleurl': 'https://www.abendzeitung-muenchen.de/inhalt.gaztro-zuckersuesse-suenden.f838d2ab-6fe6-4550-a392-80ef26a7eba6.html', 'title': 'Zuckersüße Sünden', 'journal': 'Abendzeitung München'}
        ),
        (
            """'''2009''', Dominik Bardow, [https://www.freitag.de/autoren/dominik-bardow/die-schizophrenie-der-zahlschranke “Die Schizophrenie der Zahlschranke,”] ''{{w|der Freitag}}'', 22 December 2009:""",
            ('year', 'author', 'fancy_double_quotes::url', 'fancy_double_quotes::url::text', 'italics::journal', 'date'),
            {'_source': 'journal', 'date': '22 December 2009', 'author': 'Dominik Bardow', 'titleurl': 'https://www.freitag.de/autoren/dominik-bardow/die-schizophrenie-der-zahlschranke', 'title': 'Die Schizophrenie der Zahlschranke', 'journal': '{{w|der Freitag}}'}
        ),
        (
            """'''1836''', ‘Legends of Blarney Castle’, ''The Knickerbocker'', volume VIII:""",
            ('year', 'fancy_quote', 'italics::journal', 'volume'),
            {'_source': 'journal', 'year': '1836', 'title': 'Legends of Blarney Castle', 'journal': 'The Knickerbocker', 'volume': 'VIII'}
        ),
        (
            """'''2002''', “Interim force armour activities” in ''Armed Forces journal international'', v 139:""",
            ('year', 'fancy_double_quotes', 'italics::journal', 'volume'),
            {'_source': 'journal', 'year': '2002', 'title': 'Interim force armour activities', 'journal': 'Armed Forces journal international', 'volume': '139'}
        ),
#        (
#            """'''2014''', Lily Lieberman, "[http://issuu.com/timespub/docs/02132014 Techies and Trekkies Unite at Geek's Night Out]", ''College Times'', Volume 13, Issue 12, 13 February 2014 - 26 February 2014, page 19:""",
#            ('year', 'author', 'double_quotes::url', 'double_quotes::url::text', 'italics', 'volume', 'issue', 'date', 'date2', 'page'),
#            ""
#        ),
        (
            # no author, strip {{nowrap}}
            """'''2009''', "Is the era of free news over?", ''The Observer'', {{nowrap|10 May:}}""",
            ('year', 'double_quotes', 'italics::journal', 'date'),
            {'_source': 'journal', 'date': '10 May 2009', 'title': 'Is the era of free news over?', 'journal': 'The Observer'}
        ),
        (
            # Day Month Year
            """'''2012''', Adam Gopnik, "Vive La France", ''The New Yorker'', 7 May 2012:""",
            ('year', 'author', 'double_quotes', 'italics::journal', 'date'),
            {'_source': 'journal', 'date': '7 May 2012', 'author': 'Adam Gopnik', 'title': 'Vive La France', 'journal': 'The New Yorker'}
        ),
        (
            """'''1918''', Paul Haupt, "English 'coop' == Assyrian 'Quppu'," ''Modern Language Notes'', vol. 33, no. 7, p. 434,""",
            ('year', 'author', 'double_quotes', 'italics::journal', 'volume', 'number', 'page'),
            {'_source': 'journal', 'year': '1918', 'author': 'Paul Haupt', 'title': "English 'coop' == Assyrian 'Quppu'", 'journal': 'Modern Language Notes', 'volume': '33', 'number': '7', 'page': '434'}
        ),
        (
            """'''1857''', William Chambers, Robert Chambers, "Something about bells", ''Chambers's Journal'', vol. 28, no. 207, [http://books.google.co.uk/books?id=1nhUAAAAYAAJ&pg=PA398#v=onepage&q&f=true page 398].""",
            ('year', 'author', 'double_quotes', 'italics::journal', 'volume', 'number', 'url', 'url::page'),
            {'_source': 'journal', 'year': '1857', 'author': 'William Chambers; Robert Chambers', 'title': 'Something about bells', 'journal': "Chambers's Journal", 'volume': '28', 'number': '207', 'pageurl': 'http://books.google.co.uk/books?id=1nhUAAAAYAAJ&pg=PA398#v=onepage&q&f=true', 'page': '398'}
        ),
        (
            """'''2012''', {{w|Gillian Tindall}}, "The Alleged Lunatics' Friend Society", ''Literary Review'', 403:""",
            ('year', 'author', 'double_quotes', 'italics::journal', 'section'),
            {'_source': 'journal', 'year': '2012', 'author': '{{w|Gillian Tindall}}', 'title': "The Alleged Lunatics' Friend Society", 'journal': 'Literary Review', 'section': '403'}
        ),
#        (
#            """'''1682''', {{w|John Dryden}}, ''The Medal,'' Edinburgh, “Epistle to the Whigs,”<sup>[http://name.umdl.umich.edu/A36648.0001.001]</sup>""",
#            ('year', 'author', 'italics', 'location', 'fancy_double_quotes', 'url'),
#            {'_source': 'book', 'year': '1682', 'author': '{{w|John Dryden}}', 'title': 'The Medal', 'location': 'Edinburgh', 'chapter': 'Epistle to the Whigs', 'url': 'http://name.umdl.umich.edu/A36648.0001.001'}
#        ),
        (
            """'''2023''' Jane Doe, ''A Book'' Chapter: 66, (page 1) Volume XXII [picture caption] http://foo.bar""",
            ('year', 'author', 'italics', 'section', 'url'),
            {'_source': 'text', 'year': '2023', 'author': 'Jane Doe', 'title': 'A Book', 'section': 'Chapter: 66, page 1 Volume XXII [picture caption]', 'url': 'http://foo.bar'}
        ),
        (
            """'''2003''', ''Cincinnati Magazine'' (volume 36, number 5, page 26)""",
            ('year', 'italics::journal', 'paren::volume', 'paren::number', 'paren::page'),
            {'_source': 'journal', 'year': '2003', 'journal': 'Cincinnati Magazine', 'volume': '36', 'number': '5', 'page': '26'}
        ),
        # TODO: strip '' in link text?
#        (
#            """'''2007''' December 12, Howard Fineman, "Starting From Scratch", [[w:Newsweek|''Newsweek'']],""",
#            ('date', 'author', 'double_quotes', 'link', 'link::italics::journal'),
#            {'_source': 'journal', 'date': 'December 12 2007', 'author': 'Howard Fineman', 'title': 'Starting From Scratch', 'journal': "[[w:Newsweek|''Newsweek'']]"}
#        ),
        (
            """'''2004''', Karen Horsens, in: ''Kristeligt Dagblad'', 2004-08-02 / https://www.kristeligt-dagblad.dk/ordet/tag-jer-i-agt-de-falske-profeter...""",
            ('year', 'author', 'italics::journal', 'date', 'url'),
            {'_source': 'journal', 'date': 'Feb 2 2004', 'author': 'Karen Horsens', 'journal': 'Kristeligt Dagblad', 'url': 'https://www.kristeligt-dagblad.dk/ordet/tag-jer-i-agt-de-falske-profeter'}
        ),

        (
            """'''1979''', ''New West'', volume 4, part 1, page 128:""",
            ('year', 'italics::journal', 'section'),
            {'_source': 'journal', 'year': '1979', 'journal': 'New West', 'section': 'volume 4, part 1, page 128'},
        ),
        (
            # ''et al.''. and chapter is url
            """'''2018''', C Ustan ''et al.''. "[https://onlinelibrary.wiley.com/doi/pdf/10.1002/cam4.1733 Core-binding factor acute myeloid leukemia with t(8;21): Risk  factors and a novel scoring system (I-CBFit)]", ''Cancer Medicine''.""",
            ('year', 'author', 'double_quotes::url', 'double_quotes::url::text', 'italics::journal'),
            {'_source': 'journal', 'year': '2018', 'author': 'C Ustan; et al', 'titleurl': 'https://onlinelibrary.wiley.com/doi/pdf/10.1002/cam4.1733', 'title': 'Core-binding factor acute myeloid leukemia with t(8;21): Risk factors and a novel scoring system (I-CBFit)', 'journal': 'Cancer Medicine'}
        ),

        (
            """'''2022''', Shaakirrah Sanders, ''[https://www.scotusblog.com/2022/01/court-rejects-door-opening-as-a-sixth-amendment-confrontation-clause-exception/ Court rejects “door opening” as a Sixth Amendment confrontation-clause exception]'', in: SCOTUSblog, 2022-01-20""",
            ('year', 'author', 'italics::url', 'italics::url::text', 'journal', 'date'),
            {'_source': 'journal', 'date': 'Jan 20 2022', 'author': 'Shaakirrah Sanders', 'titleurl': 'https://www.scotusblog.com/2022/01/court-rejects-door-opening-as-a-sixth-amendment-confrontation-clause-exception/', 'title': 'Court rejects “door opening” as a Sixth Amendment confrontation-clause exception', 'journal': 'SCOTUSblog'}
        ),
        (
            """'''2022''', Matteo Wong, ''[https://www.theatlantic.com/technology/archive/2022/12/avatar-2-movie-navi-constructed-language/672616/ Hollywood’s Love Affair With Fictional Languages]'', in: The Atlantic, December 31 2022""",
            ('year', 'author', 'italics::url', 'italics::url::text', 'journal', 'date'),
            {'_source': 'journal', 'date': 'December 31 2022', 'author': 'Matteo Wong', 'titleurl': 'https://www.theatlantic.com/technology/archive/2022/12/avatar-2-movie-navi-constructed-language/672616/', 'title': 'Hollywood’s Love Affair With Fictional Languages', 'journal': 'The Atlantic'}
        ),
        (
            """'''1999''', Buddy Seigal, "[https://web.archive.org/web/20140826030806/http://www.ocweekly.com/1999-08-26/music/even-old-englishmen-still-get-wood/ Even Old Englishmen Still Get Wood]," ''OC Weekly'', 26 Aug. (retrieved 16 June 2009):""",
            ('year', 'author', 'double_quotes::url', 'double_quotes::url::text', 'italics::journal', 'date', 'paren::date_retrieved'),
            {'_source': 'journal', 'date': '26 Aug 1999', 'author': 'Buddy Seigal', 'titleurl': 'https://web.archive.org/web/20140826030806/http://www.ocweekly.com/1999-08-26/music/even-old-englishmen-still-get-wood/', 'title': 'Even Old Englishmen Still Get Wood', 'journal': 'OC Weekly', 'accessdate': '16 June 2009'}
        ),

#        (
#            """'''2009''', John Metzler, "[http://www.worldtribune.com/worldtribune/WTARC/2009/mz0630_07_31.asp High stakes for democracy (and terrorism) as Afghans prepare to vote ]," ''World Tribune'' (US), 7 August (retrieved 15 Sep 2010):""",
#            ('year', 'author', 'double_quotes::url', 'double_quotes::url::text', 'italics', 'paren::location', 'date', 'paren::date_retrieved')
#            ('year', 'author', 'double_quotes::url', 'double_quotes::url::text', 'italics::journal', 'paren::location', 'date', 'paren::date_retrieved'),
#            {'_source': 'journal', 'date': '7 August 2009', 'author': 'John Metzler', 'titleurl': 'http://www.worldtribune.com/worldtribune/WTARC/2009/mz0630_07_31.asp', 'title': 'High stakes for democracy (and terrorism) as Afghans prepare to vote', 'journal': 'World Tribune', 'location': 'US', 'accessdate': '15 Sep 2010'}
#        ),
#        (
#            # mismatched dates
#            """'''2011''' Feb 21, "[http://www.dailymail.co.uk/news/article-1359019/Bankers-revive-strip-club-Spearmint-Rhino-bumper-bonuses.html Bankers revive strip club Spearmint Rhino with bumper bonuses]," ''Daily Mail'' (UK) <small>(24 July 2011)</small>:""",
#            ('date', 'double_quotes::url', 'double_quotes::url::text', 'italics', 'paren::location', 'paren::date')
#            ('date', 'double_quotes::url', 'double_quotes::url::text', 'italics::journal', 'paren::location', 'paren::date'),
            # TODO: fail because dates don't match
#            {'_source': 'journal', 'date': '24 July 2011', 'titleurl': 'http://www.dailymail.co.uk/news/article-1359019/Bankers-revive-strip-club-Spearmint-Rhino-bumper-bonuses.html', 'title': 'Bankers revive strip club Spearmint Rhino with bumper bonuses', 'journal': 'Daily Mail', 'location': 'UK'}
#        ),
        (
            """'''1987''', Kelly Lawrence, ''The Gone Shots'', Franklin Watts, US, [http://books.google.com.au/books?id=wcw2PjYZKx8C&q=%22uey%22%7C%22ueys%22+corner&dq=%22uey%22%7C%22ueys%22+corner&hl=en&sa=X&ei=7MaoUNThOPCVmQWprIDQBA&redir_esc=y page 280],""",
            ('year', 'author', 'italics', 'publisher', 'location', 'url', 'url::page'),
            {'_source': 'book', 'year': '1987', 'author': 'Kelly Lawrence', 'title': 'The Gone Shots', 'publisher': 'Franklin Watts', 'location': 'US', 'pageurl': 'http://books.google.com.au/books?id=wcw2PjYZKx8C&q=%22uey%22%7C%22ueys%22+corner&dq=%22uey%22%7C%22ueys%22+corner&hl=en&sa=X&ei=7MaoUNThOPCVmQWprIDQBA&redir_esc=y', 'page': '280'}
        ),
        (
            """'''2004''', Hannibal King in the film ''Blade: Trinity'':""",
            ('year', 'author', 'unhandled<in the film>', 'italics'),
            None
        ),
        (
            """ '''1818''', Gentleman's Magazine and Historical Review:""",
            ('year', 'journal'),
            {'_source': 'journal', 'year': '1818', 'journal': "Gentleman's Magazine and Historical Review"}
        ),
        (
            """'''1956''', Farm and Home News - Volumes 8-9:""",
            ('year', 'unhandled<Farm and>', 'journal', 'volumes'),
            None
        ),
        (
            """'''2010''', ''[[w:Der Spiegel|Der Spiegel]]'', issue [http://www.spiegel.de/spiegel/print/index-2010-49.html 49/2010], page 80:""",
            ('year', 'italics::journal', 'section'),
            {'_source': 'journal', 'year': '2010', 'journal': '[[w:Der Spiegel|Der Spiegel]]', 'section': 'issue [http://www.spiegel.de/spiegel/print/index-2010-49.html 49/2010], page 80'}
#            ('year', 'italics::link', 'italics::link::journal', 'unhandled<issue>', 'url', 'url::text', 'page'),
#            ('year', 'italics::journal', 'unhandled<issue>', 'url', 'url::text', 'page'),
#            {'_source': 'journal', 'year': '2010', 'journal': '[[w:Der Spiegel|Der Spiegel]]', 'url': 'http://www.spiegel.de/spiegel/print/index-2010-49.html', 'title': '49/2010', 'page': '80'}
#            {'_source': 'journal', 'year': '2010', 'journal': '[[w:Der Spiegel|Der Spiegel]]', 'url': 'http://www.spiegel.de/spiegel/print/index-2010-49.html', 'issue': '49/2010', 'page': '80'}
        ),
        (
            """'''1974''', "[http://news.google.ca/newspapers?id=mWkqAAAAIBAJ&sjid=xVUEAAAAIBAJ&pg=4318,6028745&dq=did-a-number-on&hl=en Sports: Full-time Franco Busts A Couple, Rushes For 141]," ''Pittsburgh Press'', 29 Oct., p. 26 (retrieved 20 Aug. 2010):""",
            ('year', 'double_quotes::url', 'double_quotes::url::text', 'italics::journal', 'date', 'page', 'paren::date_retrieved'),
            {'_source': 'journal', 'date': '29 Oct 1974', 'titleurl': 'http://news.google.ca/newspapers?id=mWkqAAAAIBAJ&sjid=xVUEAAAAIBAJ&pg=4318,6028745&dq=did-a-number-on&hl=en', 'title': 'Sports: Full-time Franco Busts A Couple, Rushes For 141', 'journal': 'Pittsburgh Press', 'page': '26', 'accessdate': '20 Aug 2010'}
        ),
        (
            """'''1970''', "[https://web.archive.org/web/20130822174940/http://www.time.com/time/magazine/article/0,9171,909210,00.html Alive and Well]," ''Time'', 18 May:""",
            ('year', 'double_quotes::url', 'double_quotes::url::text', 'italics::journal', 'date'),
            {'_source': 'journal', 'date': '18 May 1970', 'titleurl': 'https://web.archive.org/web/20130822174940/http://www.time.com/time/magazine/article/0,9171,909210,00.html', 'title': 'Alive and Well', 'journal': 'Time'}
        ),
        (
            # publisher comic strip not idea
            """'''1934''', {{w|George Herriman}}, ''{{w|Krazy Kat}}'', Tuesday, April 17 comic strip ({{ISBN|978-1-63140-408-5}}, p. 112):""",
            ('year', 'author', 'italics', 'date', 'unhandled<comic strip>', 'paren::isbn', 'paren::page'),

            None
            #{'_source': 'journal', 'date': 'April 17 1934', 'author': '{{w|George Herriman}}', 'journal': '{{w|Krazy Kat}}', 'publisher': 'comic strip', 'isbn': '978-1-63140-408-5', 'page': '112'}
        ),
        (
            """'''2008''' July 31, [[w:Richard Zoglin|Richard Zoglin]], "[https://web.archive.org/web/20080807052344/http://www.time.com/time/magazine/article/0,9171,1828301,00.html A New Dawn for ''Hair'']," ''Time''""",
            ('date', 'author', 'double_quotes::url', 'double_quotes::url::text', 'italics::journal'),
            {'_source': 'journal', 'date': 'July 31 2008', 'author': '[[w:Richard Zoglin|Richard Zoglin]]', 'titleurl': 'https://web.archive.org/web/20080807052344/http://www.time.com/time/magazine/article/0,9171,1828301,00.html', 'title': "A New Dawn for ''Hair''", 'journal': 'Time'}
        ),
        (
            """'''2007''', "[http://www.thestar.com/article/193001 Editorial: Immigration targets go beyond numbers]," ''Toronto Star'', 18 May (retrieved 8 Sep. 2008):""",
            ('year', 'double_quotes::url', 'double_quotes::url::text', 'italics::journal', 'date', 'paren::date_retrieved'),
            {'_source': 'journal', 'date': '18 May 2007', 'titleurl': 'http://www.thestar.com/article/193001', 'title': 'Editorial: Immigration targets go beyond numbers', 'journal': 'Toronto Star', 'accessdate': '8 Sep 2008'}
        ),
        (
            """'''2005''' Sept. 18, [[w:Richard Corliss|Richard Corliss]], "[https://web.archive.org/web/20130716111613/http://www.time.com/time/magazine/article/0,9171,1106325,00.html Movies: Sticking to Their Guns]," ''Time'':""",
            ('date', 'author', 'double_quotes::url', 'double_quotes::url::text', 'italics::journal'),
            {'_source': 'journal', 'date': 'Sept 18 2005', 'author': '[[w:Richard Corliss|Richard Corliss]]', 'titleurl': 'https://web.archive.org/web/20130716111613/http://www.time.com/time/magazine/article/0,9171,1106325,00.html', 'title': 'Movies: Sticking to Their Guns', 'journal': 'Time'}
        ),
        (
            """'''2012''', ''The Guardian'', 28 January:""",
            ('year', 'italics::journal', 'date'),
            {'_source': 'journal', 'date': '28 January 2012', 'journal': 'The Guardian'}
        ),

        (
            """ '''2006''', ''{{w|Geek Monthly}}'', Issues 1-4, [https://books.google.com.au/books?id=iQHsAAAAMAAJ&q=%22urban+exploration%22&dq=%22urban+exploration%22&hl=en&sa=X&redir_esc=y page 1980]""",
            ('year', 'italics::journal', 'issues', 'url', 'url::page'),
            {'_source': 'journal', 'year': '2006', 'journal': '{{w|Geek Monthly}}', 'issue': '1-4', 'pageurl': 'https://books.google.com.au/books?id=iQHsAAAAMAAJ&q=%22urban+exploration%22&dq=%22urban+exploration%22&hl=en&sa=X&redir_esc=y', 'page': '1980'}
        ),
#        (
#            """'''1987''' {{w|Newsweek}} December 7, 1987, page 44""",
#            ('year', 'journal', 'date', 'page'),
#            {'_source': 'journal', 'date': 'December 7 1987', 'journal': '{{w|Newsweek}}', 'page': '44'}
#        ),
        (
            """'''2007''', Houston Chronicle (6/17/2007)""",
            ('year', 'journal', 'paren::date'),
            {'_source': 'journal', 'date': 'Jun 17 2007', 'journal': 'Houston Chronicle'}
        ),
        (
            """'''1969''', Field & Stream - Apr 1969:""",
            ('year', 'journal', 'month', 'year2'),
            {'_source': 'journal', 'year': '1969', 'journal': 'Field & Stream', 'month': 'Apr'}
        ),
        (
            """'''2012''', ''The Guardian'', 28 January:""",
            ('year', 'italics::journal', 'date'),
            {'_source': 'journal', 'date': '28 January 2012', 'journal': 'The Guardian'}
        ),
 #      ( """'''1985''', J. Derrick McClure, “The Pinkerton Syndrome”, in ''[[w:Chapman (magazine)|Chapman: Scotland's Quality Literary Magazine]]'', Edinburgh: Chapman Magazine and Publications, <small>{{w|OCLC}} [http://www.worldcat.org/oclc/55590049 55590049]</small>, pages 2–8; reprinted in ''Scots and Its Literature'' (Varieties of English around the World, General Series; 14), Amsterdam; Philadelphia, Pa., {{w|John Benjamins Publishing Company}}, 1996, <small>[[w:International Standard Book Number|ISBN]] [[Special:BookSources/9789027248725|978-90-272-4872-5]]</small>, pages 57–58:""",
 #           ('year', 'author', 'fancy_double_quotes', 'unhandled<in>', 'italics::link', 'location', 'unhandled<Chapman Magazine and Publications', 'oclc', 'pages', 'unhandled<reprinted in>', 'italics', 'paren', 'location2', 'location3', 'publisher', 'year2', 'link', 'unhandled<[[Special:BookSources>', 'isbn', 'pages2')
 #          ""
 #      ),
        ( """'''2005''', Rosalind Ryan, ''The Guardian'', 9 August:""",
            ('year', 'author', 'italics::journal', 'date'),
            {'_source': 'journal', 'date': '9 August 2005', 'author': 'Rosalind Ryan', 'journal': 'The Guardian'}
        ),
        (
            """'''1925''' September, ''Popular Science'', page 80:""",
            ('year', 'month', 'italics::journal', 'page'),
            {'_source': 'journal', 'year': '1925', 'month': 'September', 'journal': 'Popular Science', 'page': '80'}
        ),
        (
            "'''1995''', ''Charter'' (volume 66, issues 1-5, page 34)""",
            ('year', 'italics::journal', 'paren::volume', 'paren::issues', 'paren::page'),
            {'_source': 'journal', 'year': '1995', 'journal': 'Charter', 'volume': '66', 'issue': '1-5', 'page': '34'}
        ),
        (
            """'''2003''', ''Film Review: Special'' (issues 43-48, page 31)""",
            ('year', 'italics::journal', 'paren::issues', 'paren::page'),
            {'_source': 'journal', 'year': '2003', 'journal': 'Film Review: Special', 'issue': '43-48', 'page': '31'}
        ),
        (
            """'''2013''', Luke Harding and Uki Goni, ''Argentina urges UK to hand back Falklands and 'end colonialism'' (in ''The Guardian'', 3 January 2013)[http://www.guardian.co.uk/uk/2013/jan/02/argentina-britain-hand-back-falklands]""",
            ('year', 'author', 'italics', 'paren::italics::journal', 'paren::date', 'url'),
            {'_source': 'journal', 'date': '3 January 2013', 'author': 'Luke Harding; Uki Goni', 'title': "Argentina urges UK to hand back Falklands and 'end colonialism", 'journal': 'The Guardian', 'url': 'http://www.guardian.co.uk/uk/2013/jan/02/argentina-britain-hand-back-falklands'}
        ),
        (
            """'''2021''' April 24, David McWilliams, [https://www.irishtimes.com/opinion/david-mcwilliams-a-30-year-economic-supercycle-ended-this-week-1.4544720 "A 30-year economic supercycle ended this week"] ''The Irish Times'':""",
            ('date', 'author', 'double_quotes::url', 'double_quotes::url::text', 'italics::journal'),
#            ('date', 'author', 'url', 'url::double_quotes', 'italics::journal'),
            {'_source': 'journal', 'date': 'April 24 2021', 'author': 'David McWilliams', 'titleurl': 'https://www.irishtimes.com/opinion/david-mcwilliams-a-30-year-economic-supercycle-ended-this-week-1.4544720', 'title': 'A 30-year economic supercycle ended this week', 'journal': 'The Irish Times'}
        ),
        (
            """'''1982''', ''Michigan Natural Resources Magazine'', volumes 51-52, page 77:""",
            ('year', 'italics::journal', 'volumes', 'page'),
            {'_source': 'journal', 'year': '1982', 'journal': 'Michigan Natural Resources Magazine', 'volume': '51-52', 'page': '77'}
        ),
        (
            """'''2005''' September 7, ''Birmingham Post'', p. 9:""",
            ('date', 'italics::journal', 'page'),
            {'_source': 'journal', 'date': 'September 7 2005', 'journal': 'Birmingham Post', 'page': '9'}
        ),
    ]:
        print("__")
        print(text)
        parsed = fixer.parser.get_parsed(text)
        print(parsed)
        fingerprint = fixer.get_fingerprint(parsed)
        print(fingerprint)
        assert fingerprint == expected_fingerprint

        parsed = fixer.parser.get_parsed(text)
        res = fixer.convert_parsed_to_params(parsed)
        print(res)
        assert res == expected_params

def test_get_params_newsgroup():

    for text, expected_fingerprint, expected_params in [
        #( """ """, "", "" ),
        (
            """'''2000''', 2:1, ''[//groups.google.com/d/msg/comp.sys.mac.advocacy/4GAI4Vw0b8I/7OqqIXt-w4UJ Re: Malloy digest]'', comp.os.ms-windows.nt.advocacy, Usenet,""",
            ('year', 'author', 'italics::url', 'italics::url::text', 'newsgroup'),
            {'_source': 'newsgroup', 'year': '2000', 'author': '2:1', 'titleurl': '//groups.google.com/d/msg/comp.sys.mac.advocacy/4GAI4Vw0b8I/7OqqIXt-w4UJ', 'title': 'Re: Malloy digest', 'newsgroup': 'comp.os.ms-windows.nt.advocacy'}
        ),
        (
            """'''2003''' July 6, "Tom B" <d16842@aol.com>, "Re: Group Member Committee Agenda", ''rec.skydiving'', Usenet,""",
            ('date', 'author', 'double_quotes', 'newsgroup'),
            {'_source': 'newsgroup', 'date': 'July 6 2003', 'author': '"Tom B" <d16842@aol.com>', 'title': 'Re: Group Member Committee Agenda', 'newsgroup': 'rec.skydiving'}
        ),
        (
            """'''2006''' August 10, Dr Peter Young <pnyoung@ormail.co.uk>, "Leftpondian circumlocution.", ''alt.possessive.its.has.no.apostrophe'', Usenet,""",
            ('date', 'author', 'double_quotes', 'newsgroup'),
            {'_source': 'newsgroup', 'date': 'August 10 2006', 'author': 'Dr Peter Young <pnyoung@ormail.co.uk>', 'title': 'Leftpondian circumlocution.', 'newsgroup': 'alt.possessive.its.has.no.apostrophe'}
        ),
        (
            """'''1994''' January 5, "Lydia M. Uribe" (username), "[http://groups.google.com/group/alt.pub.coffeehouse.amethyst/msg/4b40a74111c14fe7?q=ABEND Paul Saunders could use some cheering up....] ", in {{monospace|alt.pub.coffeehouse.amethyst}}, ''Usenet'':""",
            ('date', 'author', 'double_quotes::url', 'double_quotes::url::text', 'newsgroup'),
            {'_source': 'newsgroup', 'date': 'January 5 1994', 'author': 'Lydia M. Uribe', 'url': 'http://groups.google.com/group/alt.pub.coffeehouse.amethyst/msg/4b40a74111c14fe7?q=ABEND', 'title': 'Paul Saunders could use some cheering up....', 'newsgroup': 'alt.pub.coffeehouse.amethyst'}
        ),
        (
            """'''1986''' Apr 15: Barry Shein, ''Re: job control'', {{monospace|net.unix-wizards}}, [http://groups.google.com/group/net.unix-wizards/msg/81f43d80b742972d?dmode=source]""",
            ('date', 'author', 'italics', 'newsgroup', 'url'),
            {'_source': 'newsgroup', 'date': 'Apr 15 1986', 'author': 'Barry Shein', 'title': 'Re: job control', 'newsgroup': 'net.unix-wizards', 'url': 'http://groups.google.com/group/net.unix-wizards/msg/81f43d80b742972d?dmode=source'}
        ),
        (
            """'''2014''' January 13, TC10K (username), ''Re: Best Places to eat in Orlando?'', in {{monospace|rec.roller-coaster}}, ''Usenet'':""",
            ('date', 'author', 'italics', 'newsgroup'),
            {'_source': 'newsgroup', 'date': 'January 13 2014', 'author': 'TC10K', 'title': 'Re: Best Places to eat in Orlando?', 'newsgroup': 'rec.roller-coaster'}
        ),
        (
            """'''2009''' February 4, "j01" (username), "[http://groups.google.com/group/aus.legal/msg/a03d631834f518d0?q=au auDa deleting '''.au''' without warning]", in {{monospace|aus.legal}}, ''Usenet'':""",
            ('date', 'author', 'double_quotes::url', 'double_quotes::url::text', 'newsgroup'),
            {'_source': 'newsgroup', 'date': 'February 4 2009', 'author': 'j01', 'url': 'http://groups.google.com/group/aus.legal/msg/a03d631834f518d0?q=au', 'title': "auDa deleting '''.au''' without warning", 'newsgroup': 'aus.legal'}
        ),
        (
            """'''2007''' June 12, "bugzilla-daemon@mozilla.org", "superreview requested: [Bug 383542] Odd text selection behavior with new textframe", in {{monospace|mozilla.dev.super-review}}, ''Usenet'':""",
            ('date', 'author', 'double_quotes', 'newsgroup'),
            {'_source': 'newsgroup', 'date': 'June 12 2007', 'author': 'bugzilla-daemon@mozilla.org', 'title': 'superreview requested: [Bug 383542] Odd text selection behavior with new textframe', 'newsgroup': 'mozilla.dev.super-review'}
        ),
        (
            """'''1990''' May 25: Jonathan Buss, ''Watanabe vs Buss, moves 15-17'', {{monospace|rec.games.go}}, [http://groups.google.com/group/rec.games.go/msg/71a8c96919059843?dmode=source]""",
            ('date', 'author', 'italics', 'newsgroup', 'url'),
            {'_source': 'newsgroup', 'date': 'May 25 1990', 'author': 'Jonathan Buss', 'title': 'Watanabe vs Buss, moves 15-17', 'newsgroup': 'rec.games.go', 'url': 'http://groups.google.com/group/rec.games.go/msg/71a8c96919059843?dmode=source'}
        ),
        (
            """'''2015''' January 7, "Kevrob" (username), ''Re: SF influence spreads to real world'', in {{monospace|rec.arts.sf.written}}, ''Usenet'':""",
            ('date', 'author', 'italics', 'newsgroup'),
            {'_source': 'newsgroup', 'date': 'January 7 2015', 'author': 'Kevrob', 'title': 'Re: SF influence spreads to real world', 'newsgroup': 'rec.arts.sf.written'}
        ),
        (
            """'''2000''' February 22, "Peter Alfke" (username), "German Education", in {{monospace|soc.culture.german}}, ''Usenet'':""",
            ('date', 'author', 'double_quotes', 'newsgroup'),
            {'_source': 'newsgroup', 'date': 'February 22 2000', 'author': 'Peter Alfke', 'title': 'German Education', 'newsgroup': 'soc.culture.german'}
        ),
        (
            """'''1997''', "h75h70", ''ZShell anyone?'' (on newsgroup ''rec.games.programmer'')""",
            ('year', 'double_quotes', 'italics', 'paren::newsgroup'),
            {'_source': 'newsgroup', 'year': '1997', 'author': 'h75h70', 'title': 'ZShell anyone?', 'newsgroup': 'rec.games.programmer'}
        ),
        (
            """'''2002''', "Philomena", ''Nominet WHOIS'' (discussion on Internet newsgroup ''alt.internet.providers.uk'')""",
            ('year', 'double_quotes', 'italics', 'paren::newsgroup'),
            {'_source': 'newsgroup', 'year': '2002', 'author': 'Philomena', 'title': 'Nominet WHOIS', 'newsgroup': 'alt.internet.providers.uk'}
        ),
        (
            """'''2004''' Susan Cohen, ''Re: Palestines stuggle for Nationalism'', in {{monospace|soc.culture.palestine}}, ''Usenet'':""",
            ('year', 'author', 'italics', 'newsgroup'),
            {'_source': 'newsgroup', 'year': '2004', 'author': 'Susan Cohen', 'title': 'Re: Palestines stuggle for Nationalism', 'newsgroup': 'soc.culture.palestine'}
        ),
        (
            """'''2006''' June 27, John Schilling, “David Drake - Leary and the RCN”, {{monospace|rec.arts.sf.written}}, ''Usenet''""",
            ('date', 'author', 'fancy_double_quotes', 'newsgroup'),
            {'_source': 'newsgroup', 'date': 'June 27 2006', 'author': 'John Schilling', 'title': 'David Drake - Leary and the RCN', 'newsgroup': 'rec.arts.sf.written'}
        ),

    ]:
        print("__")
        print(text)
        parsed = fixer.parser.get_parsed(text)
        print(parsed)
        fingerprint = fixer.get_fingerprint(parsed)
        print(fingerprint)
        assert fingerprint == expected_fingerprint


        parsed = fixer.parser.get_parsed(text)
        res = fixer.convert_parsed_to_params(parsed)
        print(res)
        assert res == expected_params

def test_get_params_others():

    for text, expected_fingerprint, expected_params in [
        #( """ """, "", "" ),
        (
            # tranlating Author & al.
            """'''1898''', Hobart Charles Porter translating Eduard Strasburger & al. ''A Text-book of Botany'', 109:""",
            ('year', 'translator', 'author', 'italics', 'section'),
            {'_source': 'text', 'year': '1898', 'translator': 'Hobart Charles Porter', 'author': 'Eduard Strasburger; et al', 'title': 'A Text-book of Botany', 'section': '109'}
        ),
        (
            # author & al. pages roman-roman
            """'''2006''', Barry A. Kosmin & al., ''Religion in a Free Market'', [http://books.google.com/books?id=eK4ccdPm9T4C&pg=PR16 pages xvi–xvii]:""",
            ('year', 'author', 'italics', 'url', 'url::pages'),
            {'_source': 'text', 'year': '2006', 'author': 'Barry A. Kosmin; et al', 'title': 'Religion in a Free Market', 'pageurl': 'http://books.google.com/books?id=eK4ccdPm9T4C&pg=PR16', 'pages': 'xvi-xvii'}
        ),
        (
            """'''1987''', "Armageddon Now!", ''{{w|Classic X-Men}}'' #15""",
            ('year', 'double_quotes', 'italics', 'section'),
            {'_source': 'text', 'year': '1987', 'chapter': 'Armageddon Now!', 'title': '{{w|Classic X-Men}}', 'section': '#15'}
        ),
        (
            """'''1898''', {{w|George Bernard Shaw}}, ''{{w|The Perfect Wagnerite}},'' “Forgotten ere finished,”[http://www.gutenberg.org/files/1487/1487-h/1487-h.htm]""",
            ('year', 'author', 'italics', 'fancy_double_quotes', 'url'),
            {'_source': 'text', 'year': '1898', 'author': '{{w|George Bernard Shaw}}', 'title': '{{w|The Perfect Wagnerite}}', 'chapter': 'Forgotten ere finished', 'url': 'http://www.gutenberg.org/files/1487/1487-h/1487-h.htm'}
        ),
        (
            """'''1602''', ''La Santa Biblia (antigua versión de Casiodoro de Reina)'', rev., ''Génesis 26:8'':""",
            ('year', 'italics', 'italics2'),
            {'_source': 'text', 'year': '1602', 'chapter': 'Génesis 26:8', 'title': 'La Santa Biblia (antigua versión de Casiodoro de Reina)'}
        ),
        (
            """'''2010''' January, David Brakke, “[http://www.jstor.org/stable/40390061 A New Fragment of Athanasius’s Thirty-Ninth '''''Festal''' Letter'': Heresy, Apocrypha, and the Canon]” in the ''{{w|Harvard Theological Review}}'', volume CIII, № 1, page 47:""",
            ('year', 'month', 'author', 'fancy_double_quotes::url', 'fancy_double_quotes::url::text', 'italics::journal', 'section'),
            {'_source': 'journal', 'year': '2010', 'month': 'January', 'author': 'David Brakke', 'titleurl': 'http://www.jstor.org/stable/40390061', 'title': "A New Fragment of Athanasius’s Thirty-Ninth '''''Festal''' Letter'': Heresy, Apocrypha, and the Canon", 'journal': '{{w|Harvard Theological Review}}', 'section': 'volume CIII, № 1, page 47'}
        ),
        (
            """'''1930:''' ''[http://www.bisharat.net/Documents/poal30.htm Practical Orthography of African Languages]''""",
            ('year', 'italics::url', 'italics::url::text'),
            {'_source': 'text', 'year': '1930', 'url': 'http://www.bisharat.net/Documents/poal30.htm', 'title': 'Practical Orthography of African Languages'}
        ),
        (
            """'''1776''', {{w|Thomas Paine}}, ''{{w|Common Sense (pamphlet)|Common Sense}}'', Philadelphia, [http://name.umdl.umich.edu/004831091.0001.000 “Of Monarchy and Hereditary Succession”], p. 13:""",
            ('year', 'author', 'italics', 'location', 'fancy_double_quotes::url', 'fancy_double_quotes::url::text', 'page'),
            {'_source': 'book', 'year': '1776', 'author': '{{w|Thomas Paine}}', 'title': '{{w|Common Sense (pamphlet)|Common Sense}}', 'location': 'Philadelphia', 'chapterurl': 'http://name.umdl.umich.edu/004831091.0001.000', 'chapter': 'Of Monarchy and Hereditary Succession', 'page': '13'}
        ),
        (
            """ '''1920:''' Edward J. Martin, ''[http://books.google.com/books?vid=0h8T4QJ5xpq5S7qeauL&id=LVUp08zqnCAC&pg=PA263&lpg=PA263&dq=jacketed&as_brr=1 The Traffic Library: Principles of Classification]''""",
            ('year', 'author', 'italics::url', 'italics::url::text'),
            {'_source': 'text', 'year': '1920', 'author': 'Edward J. Martin', 'url': 'http://books.google.com/books?vid=0h8T4QJ5xpq5S7qeauL&id=LVUp08zqnCAC&pg=PA263&lpg=PA263&dq=jacketed&as_brr=1', 'title': 'The Traffic Library: Principles of Classification'}
        ),
        (
            # Should be "PAGE" not "SECTION"
            """'''2006''', Stacey DeMarco, ''Witch in the Bedroom: Proven Sensual Magic'', Llewellyn Publications, Minnesota, [page 33]""",
            ('year', 'author', 'italics', 'publisher', 'location', 'brackets::page'),
            {'_source': 'book', 'year': '2006', 'author': 'Stacey DeMarco', 'title': 'Witch in the Bedroom: Proven Sensual Magic', 'publisher': 'Llewellyn Publications', 'location': 'Minnesota', 'page': '33'}
        ),
        (
            """'''1999''' April, Matt Groening, “Episode Two: The Series Has Landed”, ''Futurama'', season 1, episode 2, opening title""",
            ('year', 'month', 'author', 'fancy_double_quotes', 'italics', 'section'),
            {'_source': 'text', 'year': '1999', 'month': 'April', 'author': 'Matt Groening', 'chapter': 'Episode Two: The Series Has Landed', 'title': 'Futurama', 'section': 'season 1, episode 2, opening title'}
        ),
        (
            """'''1949''', G. Karsten. ‘Eenvorme, Informe, Yefforme’, ''De Speelwagen'' 10, no. 4: 307.""",
            ('year', 'author', 'fancy_quote', 'italics', 'section'),
            {'_source': 'text', 'year': '1949', 'author': 'G. Karsten', 'chapter': 'Eenvorme, Informe, Yefforme', 'title': 'De Speelwagen', 'section': '10, no. 4: 307'}
        ),
        (
            """'''1647''', {{w|John Fletcher}}, ''A Wife for a Month'', Act V, scene i:""",
            ('year', 'author', 'italics', 'section'),
            {'_source': 'text', 'year': '1647', 'author': '{{w|John Fletcher}}', 'title': 'A Wife for a Month', 'section': 'Act V, scene i'}
        ),
        (
            """'''1990''', {{w|Andrew Davies}}, {{w|Michael Dobbs}}, ''[[w:House of Cards (UK TV show)|House of Cards]]'', Season 1, Episode 4""",
            ('year', 'author', 'italics', 'section'),
            {'_source': 'text', 'year': '1990', 'author': '{{w|Andrew Davies}}; {{w|Michael Dobbs}}', 'title': '[[w:House of Cards (UK TV show)|House of Cards]]', 'section': 'Season 1, Episode 4'}

        ),
        #(
        #    """'''1571''', ''[[w:Alonso de Molina|Alonso de Molina]]'', ''[[w:Vocabulario en lengua castellana y mexicana y mexicana y castellana|Vocabulario en lengua castellana y mexicana y mexicana y castellana]]'', f. 117v. col. 2.""",
        #    "",
        #    ""
        #),
        #(
        #    """'''1571''', ''Idem'', ''[[w:Vocabulario en lengua castellana y mexicana y mexicana y castellana|Vocabulario en lengua castellana y mexicana y mexicana y castellana]]'', 105r. col. 2.""",
        #    ('year', 'author', 'italics::link', 'italics::link::text', 'section'),
        #    {'_source': 'book', 'year': '1571', 'author': '[[w:Alonso de Molina|Alonso de Molina]]', 'title': '[[w:Vocabulario en lengua castellana y mexicana y mexicana y castellana|Vocabulario en lengua castellana y mexicana y mexicana y castellana]]', 'section': '105r. col. 2'}
        #),
        #(
        #    """'''1571:''' [[w:Alonso de Molina|Alonso de Molina]], ''[[w:Vocabulario en lengua castellana y mexicana y mexicana y castellana|Vocabulario en lengua castellana y mexicana y mexicana y castellana]]'', f. 22r. col. 1.""",
        #    ('year', 'author', 'italics::link', 'italics::link::text', 'section'),
        #    {'_source': 'book', 'year': '1571', 'author': '[[w:Alonso de Molina|Alonso de Molina]]', 'title': '[[w:Vocabulario en lengua castellana y mexicana y mexicana y castellana|Vocabulario en lengua castellana y mexicana y mexicana y castellana]]', 'section': 'f. 22r. col. 1'}
        #),
#        (
#            """'''1989''' Piers Paul Read - A Season in the West""",
#            ('year', 'author', 'unhandled<A Season in the West>'),
#            {'_source': 'text', 'year': '1989', 'author': 'Piers Paul Read', 'title': 'A Season in the West'}
#        ),
        (
            # ISBN before title
            """'''2008''', Yolanda McVey, {{ISBN|9781585715787}}, ''Love's Secrets'':""",
            ('year', 'author', 'isbn', 'italics'),
            {'_source': 'text', 'year': '2008', 'author': 'Yolanda McVey', 'isbn': '9781585715787', 'title': "Love's Secrets"}
        ),
        (
            # No publisher, no page
            """'''2015''', Christopher J Gallagher, MD, ''Pure and Simple: Anesthesia Writtens Review IV Questions, Answers, Explanations 501-1000'' ({{ISBN|9781483431178}}):""",
            ('year', 'author', 'italics', 'paren::isbn'),
            {'_source': 'text', 'year': '2015', 'author': 'Christopher J Gallagher, MD', 'title': 'Pure and Simple: Anesthesia Writtens Review IV Questions, Answers, Explanations 501-1000', 'isbn': '9781483431178'}
        ),
        (
            """'''2003''', Paz Verdades M. Santos, ''Hagkus: Twentieth-Century Bikol Women Writers'' ({{ISBN |9789715554428}})""",
            ('year', 'author', 'italics', 'paren::isbn'),
            {'_source': 'text', 'year': '2003', 'author': 'Paz Verdades M. Santos', 'title': 'Hagkus: Twentieth-Century Bikol Women Writers', 'isbn': '9789715554428'}
        ),
        (
            # No author
            """'''2008''', ''Household Economy Approach'' ({{ISBN|9781841871196}}), page 3:""",
            ('year', 'italics', 'paren::isbn', 'page'),
            {'_source': 'text', 'year': '2008', 'title': 'Household Economy Approach', 'page': '3', 'isbn': '9781841871196'}
        ),
        (
            """'''2011''', Deepika Phukan, translating {{w|Arupa Patangia Kalita}}, ''The Story of Felanee'':""",
            ('year', 'translator', 'author', 'italics'),
            {'_source': 'text', 'year': '2011', 'author': '{{w|Arupa Patangia Kalita}}', 'translator': 'Deepika Phukan', 'title': 'The Story of Felanee'}

        ),
        (
            # {{C.E.}} after year, page=1,392
            """'''1704''' {{C.E.}}, ''Philoſophical tranſactions, Giving ſome Account of the Preſent Undertakings, Studies and Labours of the Ingenious, In many Conſiderable Parts of the World'', volume XXIII, [http://books.google.co.uk/books?id=j2LH2ErAT34C&pg=RA3-PA1392&dq=%22are%C3%A6%22&lr=&num=100&as_brr=0&ei=42YtS4PKDJzyzQSk3dCtBA&cd=41#v=onepage&q=%22are%C3%A6%22&f=false page 1,392]:""",
            ('year', 'italics', 'volume', 'url', 'url::page'),
            {'_source': 'text', 'year': '1704', 'title': 'Philoſophical tranſactions, Giving ſome Account of the Preſent Undertakings, Studies and Labours of the Ingenious, In many Conſiderable Parts of the World', 'volume': 'XXIII', 'pageurl': 'http://books.google.co.uk/books?id=j2LH2ErAT34C&pg=RA3-PA1392&dq=%22are%C3%A6%22&lr=&num=100&as_brr=0&ei=42YtS4PKDJzyzQSk3dCtBA&cd=41#v=onepage&q=%22are%C3%A6%22&f=false', 'page': '1392'}
#            {'_source': 'text', 'year': '1704', 'title': 'Philoſophical tranſactions, Giving ſome Account of the Preſent Undertakings, Studies and Labours of the Ingenious, In many Conſiderable Parts of the World', 'volume': 'XXIII', 'url': 'http://books.google.co.uk/books?id=j2LH2ErAT34C&pg=RA3-PA1392&dq=%22are%C3%A6%22&lr=&num=100&as_brr=0&ei=42YtS4PKDJzyzQSk3dCtBA&cd=41#v=onepage&q=%22are%C3%A6%22&f=false', 'pages': '1,392'}
        ),



        (
            # Simple
             """'''2013''', {{w|Kacey Musgraves}}, "My House":""",
             ('year', 'author', 'double_quotes'),
             {'_source': 'text', 'year': '2013', 'author': '{{w|Kacey Musgraves}}', 'title': 'My House'}
        ),
        (
            # No closing "
            """'''1942''', IH Wagman, JE Gullberg, "The Relationship between Monochromatic Light and Pupil Diameter. The Low Intensity Visibility Curve as Measured by Pupillary Measurements. ''American Journal of Physiology'', 137: 769-778""",
            ('year', 'author', 'unhandled<"The Relationship between Monochromatic Light and Pupil Diameter. The Low Intensity Visibility Curve as Measured by Pupillary Measurements>', 'italics::journal', 'section'),
            None
        ),
        (
            """'''2010''', Erich-Norbert Detroy, Frank M. Scheelen, ''Jeder Kunde hat seinen Preis: So verhandeln Sie individuell und verkaufen erfolgreicher'' (ISBN: 3802924258), page 49:""",
            ('year', 'author', 'italics', 'paren::isbn', 'page'),
            {'_source': 'book', 'year': '2010', 'author': 'Erich-Norbert Detroy; Frank M. Scheelen', 'title': 'Jeder Kunde hat seinen Preis: So verhandeln Sie individuell und verkaufen erfolgreicher', 'isbn': '3802924258', 'page': '49'}
        ),
        (
            """'''2009''', [https://books.google.com/books?id=El5Xm120CWwC&pg=PA226&dq=jiboney&hl=en&sa=X&ei=qIidVfOEI8iHsAXkk7zwBQ&ved=0CC0Q6AEwAzgK ''Puff''] by John Flaherty""",
            ('year', 'italics::url', 'italics::url::text', 'author'),
#            ('year', 'url', 'url::italics', 'author'),
            {'_source': 'text', 'year': '2009', 'url': 'https://books.google.com/books?id=El5Xm120CWwC&pg=PA226&dq=jiboney&hl=en&sa=X&ei=qIidVfOEI8iHsAXkk7zwBQ&ved=0CC0Q6AEwAzgK', 'title': 'Puff', 'author': 'John Flaherty'}

        ),
        (
            """'''2008''', Thomas W. Young - ''The Speed of Heat: An Airlift Wing at War in Iraq and Afghanistan ''""",
            ('year', 'author', 'italics'),
            {'_source': 'text', 'year': '2008', 'author': 'Thomas W. Young', 'title': 'The Speed of Heat: An Airlift Wing at War in Iraq and Afghanistan'}
        ),
        ( """'''2005''', Rosalind Ryan, ''The Guardian'', 9 August:""",
            ('year', 'author', 'italics::journal', 'date'),
            {'_source': 'journal', 'date': '9 August 2005', 'author': 'Rosalind Ryan', 'journal': 'The Guardian'}
        ),
        (
            """'''1962''', Hans Sperber, Travis Trittschuh & Hans Sperber, ''American Political Terms''""",
            ('year', 'author', 'italics'),
            {'_source': 'text', 'year': '1962', 'author': 'Hans Sperber; Travis Trittschuh; Hans Sperber', 'title': 'American Political Terms'}
        ),
        (
            """'''2006''', Michael R. Waters with Mark Long and William Dickens, ''Lone Star Stalag: German Prisoners of War at Camp Hearne''""",
            ('year', 'author', 'italics'),
            {'_source': 'text', 'year': '2006', 'author': 'Michael R. Waters; Mark Long; William Dickens', 'title': 'Lone Star Stalag: German Prisoners of War at Camp Hearne'}
        ),
        (
            """'''1599''' CE: William Shakespeare, ''The Tragedy of Julius Caesar''""",
            ('year', 'author', 'italics'),
            {'_source': 'text', 'year': '1599', 'author': 'William Shakespeare', 'title': 'The Tragedy of Julius Caesar'}
        ),
        (
            """'''2001''', Lex Roth, [http://www.actioun-letzebuergesch.lu/files/klack/076.pdf Eng Klack for eis Sprooch]:""",
            ('year', 'author', 'url', 'url::text'),
            {'_source': 'text', 'year': '2001', 'author': 'Lex Roth', 'url': 'http://www.actioun-letzebuergesch.lu/files/klack/076.pdf', 'title': 'Eng Klack for eis Sprooch'}
        ),
        (
            # BAD DATE, messes everything else up
            # TODO: Author shouldn't allow numbers?
            """'''1998''' May 37, "barbara trumpinski" (username), "[http://groups.google.com/group/alt.med.fibromyalgia/msg/62a64f0a538e48c0?q=ABEND kitten is '''ABEND''']", in {{monospace|alt.med.fibromyalgia}}, ''Usenet'':""",
            ('year', 'author', 'double_quotes', 'paren', 'double_quotes::url', 'double_quotes::url::text', 'newsgroup'),
            None
        ),
        (
            """'''1986''' Apr 15: Barry Shein, ''Re: job control'', {{monospace|net.unix-wizards}}, [http://groups.google.com/group/net.unix-wizards/msg/81f43d80b742972d?dmode=source]""",
            ('date', 'author', 'italics', 'newsgroup', 'url'),
            {'_source': 'newsgroup', 'date': 'Apr 15 1986', 'author': 'Barry Shein', 'title': 'Re: job control', 'newsgroup': 'net.unix-wizards', 'url': 'http://groups.google.com/group/net.unix-wizards/msg/81f43d80b742972d?dmode=source'}
        ),
        (
            """'''2014''' January 13, TC10K (username), ''Re: Best Places to eat in Orlando?'', in {{monospace|rec.roller-coaster}}, ''Usenet'':""",
            ('date', 'author', 'italics', 'newsgroup'),
            {'_source': 'newsgroup', 'date': 'January 13 2014', 'author': 'TC10K', 'title': 'Re: Best Places to eat in Orlando?', 'newsgroup': 'rec.roller-coaster'}
        ),
        (
            """'''1850''' Charles Dickens - Oliver Twist""",
            ('year', 'author', 'unhandled<Oliver Twist>'),
            None
        ),
        (
            """'''2009''' February 4, "j01" (username), "[http://groups.google.com/group/aus.legal/msg/a03d631834f518d0?q=au auDa deleting '''.au''' without warning]", in {{monospace|aus.legal}}, ''Usenet'':""",
            ('date', 'author', 'double_quotes::url', 'double_quotes::url::text', 'newsgroup'),
            {'_source': 'newsgroup', 'date': 'February 4 2009', 'author': 'j01', 'url': 'http://groups.google.com/group/aus.legal/msg/a03d631834f518d0?q=au', 'title': "auDa deleting '''.au''' without warning", 'newsgroup': 'aus.legal'}
        ),
        (
            """'''2007''' June 12, "bugzilla-daemon@mozilla.org", "superreview requested: [Bug 383542] Odd text selection behavior with new textframe", in {{monospace|mozilla.dev.super-review}}, ''Usenet'':""",
            ('date', 'author', 'double_quotes', 'newsgroup'),
            {'_source': 'newsgroup', 'date': 'June 12 2007', 'author': 'bugzilla-daemon@mozilla.org', 'title': 'superreview requested: [Bug 383542] Odd text selection behavior with new textframe', 'newsgroup': 'mozilla.dev.super-review'}
        ),
        (
            """'''1925''' September, ''Popular Science'', page 80:""",
            ('year', 'month', 'italics::journal', 'page'),
            {'_source': 'journal', 'year': '1925', 'month': 'September', 'journal': 'Popular Science', 'page': '80'}
        ),
        (
            """'''1990''' May 25: Jonathan Buss, ''Watanabe vs Buss, moves 15-17'', {{monospace|rec.games.go}}, [http://groups.google.com/group/rec.games.go/msg/71a8c96919059843?dmode=source]""",
            ('date', 'author', 'italics', 'newsgroup', 'url'),
            {'_source': 'newsgroup', 'date': 'May 25 1990', 'author': 'Jonathan Buss', 'title': 'Watanabe vs Buss, moves 15-17', 'newsgroup': 'rec.games.go', 'url': 'http://groups.google.com/group/rec.games.go/msg/71a8c96919059843?dmode=source'}
        ),
        (
            """'''2015''' January 7, "Kevrob" (username), ''Re: SF influence spreads to real world'', in {{monospace|rec.arts.sf.written}}, ''Usenet'':""",
            ('date', 'author', 'italics', 'newsgroup'),
            {'_source': 'newsgroup', 'date': 'January 7 2015', 'author': 'Kevrob', 'title': 'Re: SF influence spreads to real world', 'newsgroup': 'rec.arts.sf.written'}
        ),
        (
            """'''2000''' February 22, "Peter Alfke" (username), "German Education", in {{monospace|soc.culture.german}}, ''Usenet'':""",
            ('date', 'author', 'double_quotes', 'newsgroup'),
            {'_source': 'newsgroup', 'date': 'February 22 2000', 'author': 'Peter Alfke', 'title': 'German Education', 'newsgroup': 'soc.culture.german'}
        ),
        (
            """'''1997''', "h75h70", ''ZShell anyone?'' (on newsgroup ''rec.games.programmer'')""",
            ('year', 'double_quotes', 'italics', 'paren::newsgroup'),
            {'_source': 'newsgroup', 'year': '1997', 'author': 'h75h70', 'title': 'ZShell anyone?', 'newsgroup': 'rec.games.programmer'}
        ),
        (
            """'''2002''', "Philomena", ''Nominet WHOIS'' (discussion on Internet newsgroup ''alt.internet.providers.uk'')""",
            ('year', 'double_quotes', 'italics', 'paren::newsgroup'),
            {'_source': 'newsgroup', 'year': '2002', 'author': 'Philomena', 'title': 'Nominet WHOIS', 'newsgroup': 'alt.internet.providers.uk'}
        ),
#        (
#            """'''2016''', [https://web.archive.org/web/20171030003034/https://learningenglish.voanews.com/a/lets-learn-english-lesson-8-are-you-busy/3253185.html VOA Learning English] (public domain)""",
#            ('year', 'url', 'url::text', 'paren'),
#            {'_source': 'web', 'year': '2016', 'url': 'https://web.archive.org/web/20171030003034/https://learningenglish.voanews.com/a/lets-learn-english-lesson-8-are-you-busy/3253185.html', 'site': 'VOA Learning English'}
#        ),
        (
            """'''1996''', ''The Bangladesh Journal of American Studies'' (volumes 9-10, page 71)""",
            ('year', 'italics::journal', 'paren::volumes', 'paren::page'),
            {'_source': 'journal', 'year': '1996', 'journal': 'The Bangladesh Journal of American Studies', 'volume': '9-10', 'page': '71'}
        ),
        (
            "'''1995''', ''Charter'' (volume 66, issues 1-5, page 34)""",
            ('year', 'italics::journal', 'paren::volume', 'paren::issues', 'paren::page'),
            {'_source': 'journal', 'year': '1995', 'journal': 'Charter', 'volume': '66', 'issue': '1-5', 'page': '34'}
        ),
        (
            """'''2003''', ''Film Review: Special'' (issues 43-48, page 31)""",
            ('year', 'italics::journal', 'paren::issues', 'paren::page'),
            {'_source': 'journal', 'year': '2003', 'journal': 'Film Review: Special', 'issue': '43-48', 'page': '31'}
        ),
        (
            """'''1982''', ''Michigan Natural Resources Magazine'', volumes 51-52, page 77:""",
            ('year', 'italics::journal', 'volumes', 'page'),
            {'_source': 'journal', 'year': '1982', 'journal': 'Michigan Natural Resources Magazine', 'volume': '51-52', 'page': '77'}
        ),
        (
            """'''2005''' September 7, ''Birmingham Post'', p. 9:""",
            ('date', 'italics::journal', 'page'),
            {'_source': 'journal', 'date': 'September 7 2005', 'journal': 'Birmingham Post', 'page': '9'}
        ),
        (
            """'''2004''' Susan Cohen, ''Re: Palestines stuggle for Nationalism'', in {{monospace|soc.culture.palestine}}, ''Usenet'':""",
            ('year', 'author', 'italics', 'newsgroup'),
            {'_source': 'newsgroup', 'year': '2004', 'author': 'Susan Cohen', 'title': 'Re: Palestines stuggle for Nationalism', 'newsgroup': 'soc.culture.palestine'}
        ),
        (
            """'''2006''' June 27, John Schilling, “David Drake - Leary and the RCN”, {{monospace|rec.arts.sf.written}}, ''Usenet''""",
            ('date', 'author', 'fancy_double_quotes', 'newsgroup'),
            {'_source': 'newsgroup', 'date': 'June 27 2006', 'author': 'John Schilling', 'title': 'David Drake - Leary and the RCN', 'newsgroup': 'rec.arts.sf.written'}
        ),

#        (
#            # ('year', 'author', 'italics', 'location', 'publisher', 'part', 'chapter', 'page', 'url')
#            """'''1911''', {{w|D. H. Lawrence}}, ''{{w|The White Peacock}},'' London: Heinemann, Part{{nbsp}}2, Chapter{{nbsp}}2, p.{{nbsp}}233,<sup>[https://archive.org/details/whitepeacock00lawr/page/233/mode/1up?q=afloat]</sup>""",
#            "X"
#        ),

    ]:
        print("__")
        print(text)
        parsed = fixer.parser.get_parsed(text)
        print(parsed)
        fingerprint = fixer.get_fingerprint(parsed)
        print(fingerprint)
        assert fingerprint == expected_fingerprint


        parsed = fixer.parser.get_parsed(text)
        res = fixer.convert_parsed_to_params(parsed)
        print(res)
        assert res == expected_params

def test_entry():
    # TODO: fix this
    return

    text = """\
==German==

===Noun===
#* '''2014''', Dr. Aneesa Khan, ''Spice Doctor'', Author House ({{ISBN|9781496993014}}), page 37:#
#*: line 1
#*: line 2
#*:: trans1
#*:: trans2
"""

    expected = """\
==German==

===Noun===
#* {{quote-book|de|year=2014|author=Dr. Aneesa Khan|title=Spice Doctor|page=37|publisher=Author House|isbn=9781496993014
|passage=line 1<br>line 2
|translation=trans1<br>trans2}}\
"""

    res = fixer.process(text, "test", [])
    print([res])
    assert res == expected


def test_entry_too_many_depths():

    text = """\
==Quechua==

===Etymology===
{{rfe|qu}}

===Noun===
{{head|qu|noun}}

# [[noise]]
#* '''2012''', ''Languages of the Amazon'' {{ISBN|0199593566}}:
#*: ancha-p ancha-p-ña-m '''buulla'''-kta-lula-n kada tuta-m
#*:: too.much-GEN too.much-GEN-NOW-DIR.EV noise-ACC make-3p each night-DIR.EV
#*::: He really makes to much '''noise''' ... every night. (I [have direct knowledge of this, in that] hear it.)\
"""
    res = fixer.process(text, "test", [])
    assert res == text

def test_get_passage():

    text = """\
#*: line1
#*: line2\
"""
    expected = "line1<br>line2"

    passage, translation = fixer.get_passage(text.splitlines())
    print(passage)
    assert passage == expected
    assert translation == ""


def test_get_passage_with_translation():

    text = """\
#*: {{quote|de|blah|transblah}}
"""
    expected = ('blah', 'transblah')

    res = fixer.get_passage(text.splitlines())
    print(res)
    assert res == expected


def test_use_quote_after_unparsable():

    text = """\
==English==

===Noun===
{{es-noun}}

# [[test]]
#* '''2021''', {{w|Rickie Lee Jones}}, ''Last Chance Texaco'', Grive Press 2022, p. 93:
#*: You never waited until the train stopped to get off. The railroad '''bulls''' were waiting at the stops searching for freeloaders.\
"""
    res = fixer.process(text, "test", [])
    assert res == text


