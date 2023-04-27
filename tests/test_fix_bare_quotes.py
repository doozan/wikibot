from autodooz.fix_bare_quotes import QuoteFixer
#from ..fix_bare_quotes import QuoteFixer
fixer = QuoteFixer(debug=True)
parse_details = fixer.parse_details

def test_parse_details():

    text = """'''2007''', William D. Popkin, ''Evolution of the Judicial Opinion: Institutional and Individual Styles'', NYU Press ({{ISBN|9780814767498}}), page 104:"""
    expected = {'year': '2007', 'author': 'William D. Popkin', "title": 'Evolution of the Judicial Opinion: Institutional and Individual Styles', "publisher": "NYU Press", "isbn": "9780814767498", "page": "104"}

    res = parse_details(text)
    print(res)
    assert res == expected


    # No publisher
    text = """'''2017''', Rebecca Tuhus-Dubrow, ''Personal Stereo'' ({{ISBN|1501322834}}), page 45:"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '2017', 'author': 'Rebecca Tuhus-Dubrow', 'title': 'Personal Stereo', 'isbn': '1501322834', 'page': '45'}

    # Multi authors
    text = """'''2015''', Thomas J. Gradel, Dick Simpson, ''Corrupt Illinois: Patronage, Cronyism, and Criminality'', University of Illinois Press ({{ISBN|9780252097034}}), page 117:"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '2015', 'author': 'Thomas J. Gradel', 'author2': 'Dick Simpson', 'title': 'Corrupt Illinois: Patronage, Cronyism, and Criminality', 'publisher': 'University of Illinois Press', 'isbn': '9780252097034', 'page': '117'}

    # Author with , Jr.
    text = """'''2010''', E. San Juan, Jr., ''SUTRANG KAYUMANGGI'', Lulu.com {{ISBN|9780557274277}}, page 24"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '2010', 'author': 'E. San Juan, Jr.', 'title': 'SUTRANG KAYUMANGGI', 'publisher': 'Lulu.com', 'isbn': '9780557274277', 'page': '24'}


    text = """'''1998''', Anton Pavlovich Chekhov, Ronald Hingley, ''Five Plays'', Oxford University Press, USA ({{ISBN|9780192834126}}), page 148:"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '1998', 'author': 'Anton Pavlovich Chekhov', 'author2': 'Ronald Hingley', 'title': 'Five Plays', 'publisher': 'Oxford University Press, USA', 'isbn': '9780192834126', 'page': '148'}

    # No publisher, no page
    text= """'''2015''', Christopher J Gallagher, MD, ''Pure and Simple: Anesthesia Writtens Review IV Questions, Answers, Explanations 501-1000'' ({{ISBN|9781483431178}}):"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '2015', 'author': 'Christopher J Gallagher, MD', 'title': 'Pure and Simple: Anesthesia Writtens Review IV Questions, Answers, Explanations 501-1000', 'isbn': '9781483431178'}

    # No publisher, no page
    text= """'''2013''', Larry Munson, Tony Barnhart, ''From Herschel to a Hobnail Boot: The Life and Times of Larry Munson'', Triumph Books ({{ISBN|9781623686826}}), page 52:"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '2013', 'author': 'Larry Munson', 'author2': 'Tony Barnhart', 'title': 'From Herschel to a Hobnail Boot: The Life and Times of Larry Munson', 'publisher': 'Triumph Books', 'isbn': '9781623686826', 'page': '52'}


    text = """'''2013''', Robert Miraldi, ''Seymour Hersh'', Potomac Books, Inc. ({{ISBN|9781612344751}}), page 187:"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '2013', 'author': 'Robert Miraldi', 'title': 'Seymour Hersh', 'publisher': 'Potomac Books, Inc.', 'isbn': '9781612344751', 'page': '187'}


    # Publisher followed by "," page abbreviated
    text = """'''2016''', Justin O. Schmidt, ''The Sting of the Wild'', Johns Hopkins University Press, {{ISBN|978-1-4214-1928-2}}, p. 55"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '2016', 'author': 'Justin O. Schmidt', 'title': 'The Sting of the Wild', 'publisher': 'Johns Hopkins University Press', 'isbn': '978-1-4214-1928-2', 'page': '55'}


    # google books link, page in link
    text = """'''2006''', W. Stanley Taft Jr. and James W. Mayer, ''The Science of Paintings'', {{ISBN|9780387217413}}, [https://books.google.ca/books?id=nobhBwAAQBAJ&pg=PA9&dq=%22deattributions%22&hl=en&sa=X&redir_esc=y#v=onepage&q=%22deattributions%22&f=false p. 9 (Google preview)]:"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '2006', 'author': 'W. Stanley Taft Jr.', 'author2': 'James W. Mayer', 'title': 'The Science of Paintings', 'isbn': '9780387217413', 'pageurl': 'https://books.google.ca/books?id=nobhBwAAQBAJ&pg=PA9&dq=%22deattributions%22&hl=en&sa=X&redir_esc=y#v=onepage&q=%22deattributions%22&f=false', 'page': '9'}

    # google link, chapter in link
    text = """'''2010''', Rachel Cohn, ''Very Lefreak'', Random House, {{ISBN|9780375895524}}, [http://books.google.com/books?id=B7jw88zb_jEC&pg=PT19&dq=Wikipediaing chapter 3]:"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '2010', 'author': 'Rachel Cohn', 'title': 'Very Lefreak', 'publisher': 'Random House', 'isbn': '9780375895524', 'chapterurl': 'http://books.google.com/books?id=B7jw88zb_jEC&pg=PT19&dq=Wikipediaing', 'chapter': '3'}

    # gbooks for page
    text = """'''2001''', Rudi Bekkers, ''Mobile Telecommunications Standards: GSM, UMTS, TETRA, and ERMES'', Artech House ({{ISBN|9781580532501}}), page {{gbooks|PrG2URuUfioC|250|patent|pool}}:"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '2001', 'author': 'Rudi Bekkers', 'title': 'Mobile Telecommunications Standards: GSM, UMTS, TETRA, and ERMES', 'publisher': 'Artech House', 'isbn': '9781580532501', 'page': '{{gbooks|PrG2URuUfioC|250|patent|pool}}'}

    # roman numerals
    text = """'''2004''', Rob Shein, ''Zero-Day Exploit: Countdown to Darkness'', Syngress ({{ISBN|9780080543925}}), page [https://books.google.de/books?id=ddGYYKnja1UC&lpg=PR21&dq=%22zero-day%20exploit%22&pg=PR21#v=onepage&q=%22zero-day%20exploit%22&f=false xxi]:"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '2004', 'author': 'Rob Shein', 'title': 'Zero-Day Exploit: Countdown to Darkness', 'pageurl': 'https://books.google.de/books?id=ddGYYKnja1UC&lpg=PR21&dq=%22zero-day%20exploit%22&pg=PR21#v=onepage&q=%22zero-day%20exploit%22&f=false', 'page': 'xxi', 'publisher': 'Syngress', 'isbn': '9780080543925'}

    # p.230
    text ="""'''1994''', R. Jeffrey Ringer, ''Queer Words, Queer Images: Communication and Construction of Homosexuality'' {{ISBN|0814774415}}, p.230"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '1994', 'author': 'R. Jeffrey Ringer', 'title': 'Queer Words, Queer Images: Communication and Construction of Homosexuality', 'isbn': '0814774415', 'page': '230'}

    # p&nbsp;66
    text="""'''2003''', Gillian Cloke, ''This Female Man of God: Women and Spiritual Power in the Patristic Age, 350–450 AD'', Routledge, {{ISBN|9781134868254}}, [https://books.google.com/books?id=KCGIAgAAQBAJ&lpg=PA66&dq=%22inchastity%22&pg=PA66#v=onepage&q=%22inchastity%22&f=false p.&nbsp;66]:"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '2003', 'author': 'Gillian Cloke', 'title': 'This Female Man of God: Women and Spiritual Power in the Patristic Age, 350–450 AD', 'publisher': 'Routledge', 'isbn': '9781134868254', 'pageurl': 'https://books.google.com/books?id=KCGIAgAAQBAJ&lpg=PA66&dq=%22inchastity%22&pg=PA66#v=onepage&q=%22inchastity%22&f=false', 'page': '66'}

    # translator
    text = """'''2013''', Charles Dickens (tr. by Hans Jørgen Birkmose), ''Oliver Twist'', Klim ({{ISBN|9788771292855}})#"""
    res = parse_details(text)
    print(res)
#    assert res == {'year': '2013', 'translator': 'Hans Jørgen Birkmose', 'author': 'Charles Dickens', 'title': 'Oliver Twist', 'publisher': 'Klim', 'isbn': '9788771292855'}


    # no publisher, period after title, colon after author
    text="""'''1993''' Oscar Hijuelos: ''The Fourteen Sisters of Emilio Montez O'Brien''. {{ISBN|0-14-023028-9}} page 75:"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '1993', 'author': 'Oscar Hijuelos', 'title': "The Fourteen Sisters of Emilio Montez O'Brien", 'isbn': '0-14-023028-9', 'page': '75'}

    # colon after author
    text="""'''1996''' Sherman Alexie: ''Indian Killer'' {{ISBN|0-87113-652-X}} page 102:"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '1996', 'author': 'Sherman Alexie', 'title': 'Indian Killer', 'isbn': '0-87113-652-X', 'page': '102'}


    # Title URL
    text="""'''2006''', Henrik Ibsen, trans. by Odd Tangerud, ''[http://www.gutenberg.org/files/20162/20162-h/20162-h.htm La kolonoj de la socio]'', {{ISBN|82-91707-52-9}}"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '2006', 'translator': 'Odd Tangerud', 'author': 'Henrik Ibsen', 'url': 'http://www.gutenberg.org/files/20162/20162-h/20162-h.htm', 'title': 'La kolonoj de la socio', 'isbn': '82-91707-52-9'}

    # Semicolon separator for authors
    text="""'''2013''', Judy Faust; Punch Faust, ''The MOTs File: Memories, Observations, and Thoughts'', AuthorHouse {{ISBN|9781491827123}}, page 88"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '2013', 'author': 'Judy Faust', 'author2': 'Punch Faust', 'title': 'The MOTs File: Memories, Observations, and Thoughts', 'publisher': 'AuthorHouse', 'isbn': '9781491827123', 'page': '88'}


    # Translator first
    text="""'''2012''', Judit Szántó (translator), {{w|Kathy Reichs}}, ''Csont és bőr'', Ulpius-ház {{ISBN|978 963 254 598 1}}, chapter 11, page 169:"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '2012', 'translator': 'Judit Szántó', 'author': '{{w|Kathy Reichs}}', 'title': 'Csont és bőr', 'publisher': 'Ulpius-ház', 'isbn': '9789632545981', 'chapter': '11', 'page': '169'}



    # Publisher after page
    text="""'''1992''', {{w|Samuel Beckett}}, ''{{w|Dream of Fair to Middling Women}}'', p. 71. John Calder {{ISBN|978-0714542133}}:"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '1992', 'author': '{{w|Samuel Beckett}}', 'title': '{{w|Dream of Fair to Middling Women}}', 'page': '71', 'publisher': 'John Calder', 'isbn': '978-0714542133'}


    # Parenthesis around publisher, isbn
    text="""'''1995''', Gill Van Hasselt, ''Childbirth: Your Choices for Managing Pain'' (Taylor Pub, {{ISBN|9780878339020}}):"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '1995', 'author': 'Gill Van Hasselt', 'title': 'Childbirth: Your Choices for Managing Pain', 'publisher': 'Taylor Pub', 'isbn': '9780878339020'}

    # sup tags
    text="""'''1998''', [[w:Frank M. Robinson|Frank M. Robinson]] and Lawrence Davidson, ''Pulp Culture: The Art of Fiction Magazines'',<sup >[http://books.google.com/books?id=mhYfL6Dn5g8C ]</sup> Collectors Press, Inc., {{ISBN|1-888054-12-3}}, page 103"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '1998', 'author': '[[w:Frank M. Robinson|Frank M. Robinson]]', 'author2': 'Lawrence Davidson', 'title': 'Pulp Culture: The Art of Fiction Magazines', 'pageurl': 'http://books.google.com/books?id=mhYfL6Dn5g8C', 'page': '103', 'publisher': 'Collectors Press, Inc.', 'isbn': '1-888054-12-3'}

    # page before ISBN
    text="""'''2011''', Steve Urick, ''Practical Christian Living'', p. 214 ({{ISBN|978-1-4520-8297-4}}):"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '2011', 'author': 'Steve Urick', 'title': 'Practical Christian Living', 'page': '214', 'isbn': '978-1-4520-8297-4'}

    # publisher is link
    text="""'''1996''', Marc Parent, ''Turning Stones'', [[w:Harcourt Brace & Company|Harcourt Brace & Company]], {{ISBN|0151002045}}, page 93,"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '1996', 'author': 'Marc Parent', 'title': 'Turning Stones', 'page': '93', 'publisher': '[[w:Harcourt Brace & Company|Harcourt Brace & Company]]', 'isbn': '0151002045'}

    # ISBN last
    text="""'''2006''' Kelly Pyrek, ''Forensic Nursing'', page 514, {{ISBN|084933540X}}."""
    res = parse_details(text)
    print(res)
    assert res == {'year': '2006', 'author': 'Kelly Pyrek', 'title': 'Forensic Nursing', 'page': '514', 'isbn': '084933540X'}

    # Volume
    text="""'''2008''', John L. Capinera, ''Encyclopedia of Entomology'' {{ISBN|1402062427}}, volume 4, page 3326:"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '2008', 'author': 'John L. Capinera', 'title': 'Encyclopedia of Entomology', 'volume': '4', 'page': '3326', 'isbn': '1402062427'}

    text ="""'''2003''', Paz Verdades M. Santos, ''Hagkus: Twentieth-Century Bikol Women Writers'' ({{ISBN |9789715554428}})"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '2003', 'author': 'Paz Verdades M. Santos', 'title': 'Hagkus: Twentieth-Century Bikol Women Writers', 'isbn': '9789715554428'}

    # Published year
    text = """'''1936''', {{w|George Weller}}, ''Clutch and Differential'', Ayer, 1970, {{ISBN|0836936590}}, page 196,"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '1936', 'author': '{{w|George Weller}}', 'title': 'Clutch and Differential', 'page': '196', 'publisher': 'Ayer', 'year_published': '1970', 'isbn': '0836936590'}


    # Published year same as year
    text="""'''2007''', David J. Wishart, ''Encyclopedia of the Great Plains Indians'', University of Nebraska Press (2007), {{ISBN|0-8032-9862-5}}, [http://books.google.ca/books?id=646oX4hA8EkC&lpg=PA32&dq=%22quilled%22&pg=PA32#v=onepage&q=%22quilled%22&f=false page 32]:"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '2007', 'author': 'David J. Wishart', 'title': 'Encyclopedia of the Great Plains Indians', 'pageurl': 'http://books.google.ca/books?id=646oX4hA8EkC&lpg=PA32&dq=%22quilled%22&pg=PA32#v=onepage&q=%22quilled%22&f=false', 'page': '32', 'publisher': 'University of Nebraska Press', 'isbn': '0-8032-9862-5'}

    # publisher followed by year
    text="""'''2007''' Rachel M. Harper: ''Brass Ankle Blues''. Simon&Schuster 2007. {{ISBN|0743296583}} page 88:"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '2007', 'author': 'Rachel M. Harper', 'title': 'Brass Ankle Blues', 'page': '88', 'publisher': 'Simon&Schuster', 'isbn': '0743296583'}

    # reprint
    text="""'''1971''', Peter Brown, ''The World of Late Antiquity: AD 150—750'', Thames & Hudson LTD (2013 reprint), {{ISBN|0393958035}}, page 54."""
    res = parse_details(text)
    print(res)
    assert res == {'year': '1971', 'author': 'Peter Brown', 'title': 'The World of Late Antiquity: AD 150—750', 'page': '54', 'publisher': 'Thames & Hudson LTD', 'year_published': '2013', 'isbn': '0393958035'}

    # No publisher, date
    text="""'''1958''', [[w:John Kenneth Galbraith|John Kenneth Galbraith]], ''The Affluent Society'' (1998 edition), {{ISBN|9780395925003}}, [http://books.google.ca/books?id=IfH010hvIqcC&printsec=frontcover&source=gbs_ge_summary_r&cad=0#v=onepage&q=niggardly&f=false p. 186]:"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '1958', 'author': '[[w:John Kenneth Galbraith|John Kenneth Galbraith]]', 'title': 'The Affluent Society', 'pageurl': 'http://books.google.ca/books?id=IfH010hvIqcC&printsec=frontcover&source=gbs_ge_summary_r&cad=0#v=onepage&q=niggardly&f=false', 'page': '186', 'year_published': '1998', 'isbn': '9780395925003'}

    # illustrated edition
    text="""'''2001''', [[w:Yann Martel|Yann Martel]], ''Life of Pi'' (illustrated 2007 edition), {{ISBN|9780156035811}}, [http://books.google.ca/books?id=RmkhNOzuV5YC&pg=PA186&dq=%22calendar+day%22+subject:%22fiction%22&hl=en&sa=X&ei=ChOEU8PrEMiT8QHQxoC4Bw&ved=0CCwQ6AEwADgK#v=onepage&q=%22calendar%20day%22%20subject%3A%22fiction%22&f=false p. 186 (Google preview)]:"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '2001', 'author': '[[w:Yann Martel|Yann Martel]]', 'title': 'Life of Pi', 'pageurl': 'http://books.google.ca/books?id=RmkhNOzuV5YC&pg=PA186&dq=%22calendar+day%22+subject:%22fiction%22&hl=en&sa=X&ei=ChOEU8PrEMiT8QHQxoC4Bw&ved=0CCwQ6AEwADgK#v=onepage&q=%22calendar%20day%22%20subject%3A%22fiction%22&f=false', 'page': '186', 'year_published': '2007', 'isbn': '9780156035811'}

    # No author
    text="""'''2008''', ''Household Economy Approach'' ({{ISBN|9781841871196}}), page 3:"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '2008', 'title': 'Household Economy Approach', 'page': '3', 'isbn': '9781841871196'}

    # Publisher location
    text="""'''1978''', Marguerite V. Burke, ''The Ukrainian Canadians'', Toronto: Van Nostrand Reinhold, {{ISBN|0442298633}}, p 48:"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '1978', 'author': 'Marguerite V. Burke', 'title': 'The Ukrainian Canadians', 'page': '48', 'publisher': 'Van Nostrand Reinhold', 'location': 'Toronto', 'isbn': '0442298633'}

    # Publisher location
    text="""'''2008''', David Squire et al, ''The First-Time Garden Specialist'' ({{ISBN|1845379268}}), page 12:"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '2008', 'author': 'David Squire', 'author2': 'et al', 'title': 'The First-Time Garden Specialist', 'page': '12', 'isbn': '1845379268'}


    # ''et al.''
    text="""'''1988''', Lewis B. Ware ''et al.'', ''Low-Intensity Conflict in the Third World,'' Air Univ. Press, {{ISBN|978-1585660223}}, p. 139:"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '1988', 'author': 'Lewis B. Ware', 'author2': 'et al', 'title': 'Low-Intensity Conflict in the Third World', 'page': '139', 'publisher': 'Air Univ. Press', 'isbn': '978-1585660223'}

    # ''et al.'' multiple authors
    text="""'''2019''', Pierre Terjanian, Andrea Bayer, et al., ''The Last Knight: The Art, Armor, and Ambition of Maximilian I'', Metropolitan Museum of Art ({{ISBN|9781588396747}}), page 96:"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '2019', 'author': 'Pierre Terjanian', 'author2': 'Andrea Bayer', 'author3': 'et al', 'title': 'The Last Knight: The Art, Armor, and Ambition of Maximilian I', 'page': '96', 'publisher': 'Metropolitan Museum of Art', 'isbn': '9781588396747'}


    # ''et alii''
    text="""'''1964''': Nikolay Rimsky-Korsakov ''et alii'', ''Principles of orchestration: with musical examples drawn from his own works'', [http://books.google.co.uk/books?id=erS-2XR-kPUC&pg=PA112&dq=crescendi&ei=58nkSeaJIYyykASju4yfDQ page 112] ([http://store.doverpublications.com/0486212661.html DoverPublications.com]; {{ISBN|0486212661}}"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '1964', 'author': 'Nikolay Rimsky-Korsakov', 'author2': 'et al', 'title': 'Principles of orchestration: with musical examples drawn from his own works', 'pageurl': 'http://books.google.co.uk/books?id=erS-2XR-kPUC&pg=PA112&dq=crescendi&ei=58nkSeaJIYyykASju4yfDQ', 'page': '112', 'publisher': '[http://store.doverpublications.com/0486212661.html DoverPublications.com]', 'isbn': '0486212661'}


    # ''et al.''. and chapter is url
    text="""'''2018''', C Ustan ''et al.''. "[https://onlinelibrary.wiley.com/doi/pdf/10.1002/cam4.1733 Core-binding factor acute myeloid leukemia with t(8;21): Risk  factors and a novel scoring system (I-CBFit)]", ''Cancer Medicine''."""
    res = parse_details(text)
    print(res)
    assert res == {'year': '2018', 'author': 'C Ustan', 'author2': 'et al', 'chapter': 'Core-binding factor acute myeloid leukemia with t(8;21): Risk  factors and a novel scoring system (I-CBFit)', 'chapterurl': 'https://onlinelibrary.wiley.com/doi/pdf/10.1002/cam4.1733', 'title': 'Cancer Medicine'}


    # (editors)
    text="""'''2005''', John Schaeffer, Doug Pratt (editors), ''Appendix'', ''Gaiam Real Goods Solar Living Sourcebook'', [http://books.google.com.au/books?id=im-No5TYyy8C&pg=PA517&dq=%22awg%22&hl=en&sa=X&ei=k5wEUbnbB8OhkQXZtoEY&redir_esc=y#v=onepage&q=%22awg%22&f=false page 517],"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '2005', 'editors': 'John Schaeffer; Doug Pratt', 'title': 'Appendix: Gaiam Real Goods Solar Living Sourcebook', 'pageurl': 'http://books.google.com.au/books?id=im-No5TYyy8C&pg=PA517&dq=%22awg%22&hl=en&sa=X&ei=k5wEUbnbB8OhkQXZtoEY&redir_esc=y#v=onepage&q=%22awg%22&f=false', 'page': '517'}


    # editors, author
    text="""'''1995''', Solomon Feferman, John W. Dawson, Jr., Warren Goldfarb, Charlers Parsons, Robert N. Solovay (editors), {{w|Kurt Gödel}}, ''Kurt Gödel: Collected Works: Volume III'', {{w|Oxford University Press}}, [https://books.google.com.au/books?id=gDzbuUwma5MC&pg=PA419&dq=%22Hausdorff+gap%22%7C%22Hausdorff+gaps%22&hl=en&newbks=1&newbks_redir=0&sa=X&ved=2ahUKEwjo-o7D9OT7AhVQJUQIHaSlBIgQ6AF6BAhXEAI#v=onepage&q=%22Hausdorff%20gap%22%7C%22Hausdorff%20gaps%22&f=false page 419]"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '1995', 'author': '{{w|Kurt Gödel}}', 'editors': 'Solomon Feferman; John W. Dawson, Jr.; Warren Goldfarb; Charlers Parsons; Robert N. Solovay', 'title': 'Kurt Gödel: Collected Works: Volume III', 'pageurl': 'https://books.google.com.au/books?id=gDzbuUwma5MC&pg=PA419&dq=%22Hausdorff+gap%22%7C%22Hausdorff+gaps%22&hl=en&newbks=1&newbks_redir=0&sa=X&ved=2ahUKEwjo-o7D9OT7AhVQJUQIHaSlBIgQ6AF6BAhXEAI#v=onepage&q=%22Hausdorff%20gap%22%7C%22Hausdorff%20gaps%22&f=false', 'page': '419', 'publisher': '{{w|Oxford University Press}}'}


    # translator
    text="""'''1865''', [[w:Homer|Homer]] and [[w:Edward Smith-Stanley, 14th Earl of Derby|Edward Smith-Stanley, 14th Earl of Derby]] (translator), ''[[w:Iliad|Iliad]]'', volume 1, [http://books.google.co.uk/books?id=EEYbAAAAYAAJ&pg=PP14&dq=%22Heph%C3%A6stus%22&ei=PWSiSru7DYmGzATwjoCBCA#v=onepage&q=%22Heph%C3%A6stus%22&f=false page viii]:"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '1865', 'author': '[[w:Homer|Homer]]', 'translator': '[[w:Edward Smith-Stanley, 14th Earl of Derby|Edward Smith-Stanley, 14th Earl of Derby]]', 'title': '[[w:Iliad|Iliad]]', 'volume': '1', 'pageurl': 'http://books.google.co.uk/books?id=EEYbAAAAYAAJ&pg=PP14&dq=%22Heph%C3%A6stus%22&ei=PWSiSru7DYmGzATwjoCBCA#v=onepage&q=%22Heph%C3%A6stus%22&f=false', 'page': 'viii'}

    # unnumbered page
    text = """'''2018''', Adrian Besley, ''BTS: Icons of K-Pop'', [https://books.google.com/books?id=QcxmDwAAQBAJ&pg=PT170&dq=%22army+are+clever%22 unnumbered page]:"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '2018', 'author': 'Adrian Besley', 'title': 'BTS: Icons of K-Pop', 'pageurl': 'https://books.google.com/books?id=QcxmDwAAQBAJ&pg=PT170&dq=%22army+are+clever%22', 'page': 'unnumbered'}

    # '''Year'''.
    text = """'''1931'''. George Saintsbury, ''A Consideration of Thackeray'', chapter V."""
    res = parse_details(text)
    assert res == {'year': '1931', 'author': 'George Saintsbury', 'title': 'A Consideration of Thackeray', 'chapter': 'V'}

    # publisher followed by ed.
    text = """'''1940''', [[w:Carson McCullers|Carson McCullers]], ''[[w:The Heart Is a Lonely Hunter|The Heart Is a Lonely Hunter]]'', 2004 Houghton Mifflin ed., {{ISBN|0618526412}}, page 306,"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '1940', 'author': '[[w:Carson McCullers|Carson McCullers]]', 'title': '[[w:The Heart Is a Lonely Hunter|The Heart Is a Lonely Hunter]]', 'page': '306', 'publisher': 'Houghton Mifflin', 'year_published': '2004', 'isbn': '0618526412'}

    # Numbered edition
    text = """'''2007''', John Howells, Don Merwin, ''Choose Mexico for Retirement'', 10th edition {{ISBN|0762753544}}, page 49:"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '2007', 'author': 'John Howells', 'author2': 'Don Merwin', 'title': 'Choose Mexico for Retirement', 'edition': '10th', 'page': '49', 'isbn': '0762753544'}

    # Numbered edition
    text = """'''2007''', John Merryman, Rogelio Pérez-Perdomo, ''The Civil Law Tradition'', 3rd edition {{ISBN|0804768331}}, page 107:"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '2007', 'author': 'John Merryman', 'author2': 'Rogelio Pérez-Perdomo', 'title': 'The Civil Law Tradition', 'edition': '3rd', 'page': '107', 'isbn': '0804768331'}

    # 1975 Dover Edition
    text="""'''1945''', Neva L. Boyd, ''Handbook of Recreational Games'', 1975 [[w:Dover Publications|Dover]] edition, {{ISBN|0486232042}}, [http://books.google.com/books?id=12qZwZpIwCIC&pg=PA16&dq=candlelight p.16]:"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '1945', 'author': 'Neva L. Boyd', 'title': 'Handbook of Recreational Games', 'pageurl': 'http://books.google.com/books?id=12qZwZpIwCIC&pg=PA16&dq=candlelight', 'page': '16', 'publisher': '[[w:Dover Publications|Dover]]', 'year_published': '1975', 'isbn': '0486232042'}


    # Multiple pages
    text = """'''2013''', Terry Pratchett, ''Raising Steam'', Doubleday, {{ISBN|978-0-857-52227-6}}, pages 345–346:"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '2013', 'author': 'Terry Pratchett', 'title': 'Raising Steam', 'pages': '345–346', 'publisher': 'Doubleday', 'isbn': '978-0-857-52227-6'}


    # Pages in link text
    text = """'''2006''', {{w|Alexander McCall Smith}}, ''Love Over Scotland'', Random House Digital (2007), {{ISBN|978-0-307-27598-1}}, [http://books.google.com/books?id=_SLjwNeumpoC&pg=PA242&dq=third-person pages 243-4]:"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '2006', 'author': '{{w|Alexander McCall Smith}}', 'title': 'Love Over Scotland', 'pageurl': 'http://books.google.com/books?id=_SLjwNeumpoC&pg=PA242&dq=third-person', 'pages': '243-4', 'publisher': 'Random House Digital', 'year_published': '2007', 'isbn': '978-0-307-27598-1'}

    # Strip (novel) from unparsed text
    text = """'''1959''', [[w:James Michener|James Michener]], ''[[w:Hawaii (novel)|Hawaii]]'' (novel),<sup >[http://books.google.com/books?id=1QHYAAAAMAAJ ]</sup> Fawcett Crest (1986), {{ISBN|9780449213353}}, page 737:"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '1959', 'author': '[[w:James Michener|James Michener]]', 'title': '[[w:Hawaii (novel)|Hawaii]]', 'pageurl': 'http://books.google.com/books?id=1QHYAAAAMAAJ', 'page': '737', 'publisher': 'Fawcett Crest', 'year_published': '1986', 'isbn': '9780449213353'}


    # Strip (novel) from unparsed text
    text = """'''2003''', Karin Slaughter, ''A Faint Cold Fear'' (novel), HarperCollins, {{ISBN|978-0-688-17458-3}}, [http://books.google.com/books?id=n8yT5KxPzNAC&pg=PA169&dq=rolling page 169]:"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '2003', 'author': 'Karin Slaughter', 'title': 'A Faint Cold Fear', 'pageurl': 'http://books.google.com/books?id=n8yT5KxPzNAC&pg=PA169&dq=rolling', 'page': '169', 'publisher': 'HarperCollins', 'isbn': '978-0-688-17458-3'}

    # Travellers edition generated wrong publisher
    text="""'''1999''', Mark Warren, ''Mark Warren's Atlas of Australian Surfing'', traveller's edition 1999, {{ISBN|0-7322-6731-5}}, page 103"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '1999', 'author': 'Mark Warren', 'title': "Mark Warren's Atlas of Australian Surfing", 'edition': "traveller's", 'page': '103', 'isbn': '0-7322-6731-5'}

    text = """'''1999''', K. Zakrzewska, R. Lavery, "Modelling DNA-protein interactions", in ''Computational Molecular Biology'' (edited by J. Leszczynski; {{ISBN|008052964X}}:"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '1999', 'editor': 'J. Leszczynski', 'author': 'K. Zakrzewska', 'author2': 'R. Lavery', 'chapter': 'Modelling DNA-protein interactions', 'title': 'Computational Molecular Biology', 'isbn': '008052964X'}

    # Editor prefixed
    text="""'''2008''', ''The New Black Lace Book of Women's Sexual Fantasies'' (ed. Mitzi Szereto), Black Lace (2008), {{ISBN|9780352341723}}, [http://books.google.com/books?id=XI7MR8XZSh8C&pg=PA38&dq=%22alphas%22#v=onepage&q=%22alphas%22&f=false page 38]"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '2008', 'editor': 'Mitzi Szereto', 'title': "The New Black Lace Book of Women's Sexual Fantasies", 'pageurl': 'http://books.google.com/books?id=XI7MR8XZSh8C&pg=PA38&dq=%22alphas%22#v=onepage&q=%22alphas%22&f=false', 'page': '38', 'publisher': 'Black Lace', 'isbn': '9780352341723'}

    # Pages
    text = """'''1999''', Peter McPhee, ''Runner'', {{ISBN|1550286749}}, pp. 37{{ndash}}8:"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '1999', 'author': 'Peter McPhee', 'title': 'Runner', 'pages': '37{{ndash}}8', 'isbn': '1550286749'}

    # pages
    text = """'''1991''', Katie Hafner & [[w:John Markoff|John Markoff]], ''Cyberpunk: Outlaws and Hackers on the Computer Frontier'' (1995 revised edition), Simon and Schuster, {{ISBN|0684818620}}, pp. 255-256:"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '1991', 'author': 'Katie Hafner', 'author2': '[[w:John Markoff|John Markoff]]', 'title': 'Cyberpunk: Outlaws and Hackers on the Computer Frontier', 'edition': 'revised', 'pages': '255-256', 'publisher': 'Simon and Schuster', 'isbn': '0684818620'}

    # Chapter title
    text = """'''2008''', Ian Black, "An earthquake hits Newcastle" in ''Geordies vs Mackems & Mackems vs Geordies'', Black & White Publishing {{ISBN|9781845028619}}, page 97"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '2008', 'author': 'Ian Black', 'chapter': 'An earthquake hits Newcastle', 'title': 'Geordies vs Mackems & Mackems vs Geordies', 'page': '97', 'publisher': 'Black & White Publishing', 'isbn': '9781845028619'}

    # Chapter title
    text = """'''2009''', Cate Robertson, "Half-Crown Doxy", in ''Bitten: Dark Erotic Stories'' (ed. Susie Bright), Chronicle Books (2009), {{ISBN|9780811864251}}, [http://books.google.com/books?id=GWFpxR443xEC&pg=PA126&dq=%22his+grundle%22#v=onepage&q=%22his%20grundle%22&f=false page 126]:"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '2009', 'editor': 'Susie Bright', 'author': 'Cate Robertson', 'chapter': 'Half-Crown Doxy', 'title': 'Bitten: Dark Erotic Stories', 'pageurl': 'http://books.google.com/books?id=GWFpxR443xEC&pg=PA126&dq=%22his+grundle%22#v=onepage&q=%22his%20grundle%22&f=false', 'page': '126', 'publisher': 'Chronicle Books', 'isbn': '9780811864251'}

    # Chapter title in ''
    text = """'''2002''' Dave Margoshes, ''Faith, Hope, Charity'', in ''Purity of Absence'', Dundurn Press Ltd., {{ISBN|0888784198}}, page 106:"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '2002', 'author': 'Dave Margoshes', 'chapter': 'Faith, Hope, Charity', 'title': 'Purity of Absence', 'page': '106', 'publisher': 'Dundurn Press Ltd.', 'isbn': '0888784198'}

    # Sub-title
    text = """'''2006''', Timothy M. Gay, ''Tris Speaker'', ''The Rough-and-Tumble Life of a Baseball Legend'', U of Nebraska Press, {{ISBN|0803222068}}, page 37:"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '2006', 'author': 'Timothy M. Gay', 'title': 'Tris Speaker: The Rough-and-Tumble Life of a Baseball Legend', 'page': '37', 'publisher': 'U of Nebraska Press', 'isbn': '0803222068'}

    # Pages in link text
    text = """'''2009''', Steve Scott, ''Insiders - Outsiders'', {{ISBN|9781907172205}}, [http://books.google.ca/books?id=LKaOUC90pKUC&pg=PA37&dq=%22ashamed+me%22&hl=en&sa=X&ei=uPlIUqWICfPb4AOc34CACQ&ved=0CDoQ6AEwAjgK#v=snippet&q=%22ashamed%20me%22&f=false pp. 36-37 (Google preview)]:"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '2009', 'author': 'Steve Scott', 'title': 'Insiders - Outsiders', 'pageurl': 'http://books.google.ca/books?id=LKaOUC90pKUC&pg=PA37&dq=%22ashamed+me%22&hl=en&sa=X&ei=uPlIUqWICfPb4AOc34CACQ&ved=0CDoQ6AEwAjgK#v=snippet&q=%22ashamed%20me%22&f=false', 'pages': '36-37', 'isbn': '9781907172205'}

    # multi ISBN
    text = """'''2008''': Martin Walters, ''Chinese Wildlife: A Visitor’s Guide'', [http://books.google.co.uk/books?id=yIqTV8t_ElAC&pg=PA25&dq=%22Chinese+grapefruit%22&ei=nJNLSv60J42mM7HXzK4K page 25] ([https://web.archive.org/web/20090917020647/http://www.bradt-travelguides.com/details.asp?prodid=177 Bradt Travel Guides]; {{ISBN|1841622206}}, 9781841622200)"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '2008', 'author': 'Martin Walters', 'title': 'Chinese Wildlife: A Visitor’s Guide', 'pageurl': 'http://books.google.co.uk/books?id=yIqTV8t_ElAC&pg=PA25&dq=%22Chinese+grapefruit%22&ei=nJNLSv60J42mM7HXzK4K', 'page': '25', 'publisher': '[https://web.archive.org/web/20090917020647/http://www.bradt-travelguides.com/details.asp?prodid=177 Bradt Travel Guides]', 'isbn': '1841622206', 'isbn2': '9781841622200'}

    # x, y, and z authors
    text = """'''2001''', Delys Bird, Robert Dixon, and Christopher Lee, ''Authority and Influence'', [http://books.google.co.uk/books?id=DABZAAAAMAAJ&q=ambilaevous&dq=ambilaevous&ei=QiuSSImiGIHAigHKibD6DA&pgis=1 page 54] (University of Queensland Press; {{ISBN|0702232033}}, 9780702232039)"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '2001', 'author': 'Delys Bird', 'author2': 'Robert Dixon', 'author3': 'Christopher Lee', 'title': 'Authority and Influence', 'pageurl': 'http://books.google.co.uk/books?id=DABZAAAAMAAJ&q=ambilaevous&dq=ambilaevous&ei=QiuSSImiGIHAigHKibD6DA&pgis=1', 'page': '54', 'publisher': 'University of Queensland Press', 'isbn': '0702232033', 'isbn2': '9780702232039'}

    # Multiple editors
    text = """'''2014''', Cornel Sandvoss & Laura Kearns, "From Interpretive Communities to Interpretive Fairs: Ordinary Fandom, Textual Selection and Digital Media", in ''The Ashgate Research Companion to Fan Cultures'' (eds. Stijn Reijnders, Koos Zwaan, & Linda Duits), Ashgate (2014), {{ISBN|9781409455622}}, [https://books.google.com/books?id=sfTiBAAAQBAJ&pg=PA93&dq=%22aca-fans%22 page 93]:"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '2014', 'editor': 'Stijn Reijnders; Koos Zwaan; Linda Duits', 'author': 'Cornel Sandvoss', 'author2': 'Laura Kearns', 'chapter': 'From Interpretive Communities to Interpretive Fairs: Ordinary Fandom, Textual Selection and Digital Media', 'title': 'The Ashgate Research Companion to Fan Cultures', 'pageurl': 'https://books.google.com/books?id=sfTiBAAAQBAJ&pg=PA93&dq=%22aca-fans%22', 'page': '93', 'publisher': 'Ashgate', 'isbn': '9781409455622'}

    # '''''
    text = """'''2014''', Larisa Kharakhinova, ''Heart-to-heart letters: to MrRight from '''CCCP''''', Litres {{ISBN|9785457226449}}, page 22"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '2014', 'author': 'Larisa Kharakhinova', 'title': "Heart-to-heart letters: to MrRight from '''CCCP'''", 'page': '22', 'publisher': 'Litres', 'isbn': '9785457226449'}

    # OCLC instad of ISBN
    text = """'''1847''': Charles Sealsfield, ''Rambleton: A Romance of Fashionable Life in New-York during the Great Speculation of 1836'' {{OCLC|12337689}}, page 127"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '1847', 'author': 'Charles Sealsfield', 'title': 'Rambleton: A Romance of Fashionable Life in New-York during the Great Speculation of 1836', 'page': '127', 'oclc': '12337689'}


    text="""'''1857''', William Chambers, Robert Chambers, "Something about bells", ''Chambers's Journal'', vol. 28, no. 207, [http://books.google.co.uk/books?id=1nhUAAAAYAAJ&pg=PA398#v=onepage&q&f=true page 398]."""
    res = parse_details(text)
    print(res)
    assert res == {'year': '1857', 'author': 'William Chambers', 'author2': 'Robert Chambers', 'chapter': 'Something about bells', 'title': "Chambers's Journal", 'volume': '28', 'number': '207', 'pageurl': 'http://books.google.co.uk/books?id=1nhUAAAAYAAJ&pg=PA398#v=onepage&q&f=true', 'page': '398'}

    text="""'''1918''', Paul Haupt, "English 'coop' == Assyrian 'Quppu'," ''Modern Language Notes'', vol. 33, no. 7, p. 434,"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '1918', 'author': 'Paul Haupt', 'chapter': "English 'coop' == Assyrian 'Quppu'", 'title': 'Modern Language Notes', 'volume': '33', 'number': '7', 'page': '434'}

    text="""'''2017''', Masaki Kohana ''et al.'', "A Topic Trend on P2P Based Social Media", in ''Advances in Network-Based Information Systems: The 20th International Conference on Network-Based Information Systems (NBiS-2017)'' (eds Leonard Barolli, Makoto Takizawa, & Tomoya Enokido), [https://www.google.com/books/edition/Advances_in_Network_Based_Information_Sy/W3syDwAAQBAJ?hl=en&gbpv=1&dq=%22instance%22+mastodon&pg=PA1140&printsec=frontcover page 1140]"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '2017', 'editor': 'Leonard Barolli; Makoto Takizawa; Tomoya Enokido', 'author': 'Masaki Kohana', 'author2': 'et al', 'chapter': 'A Topic Trend on P2P Based Social Media', 'title': 'Advances in Network-Based Information Systems: The 20th International Conference on Network-Based Information Systems (NBiS-2017)', 'pageurl': 'https://www.google.com/books/edition/Advances_in_Network_Based_Information_Sy/W3syDwAAQBAJ?hl=en&gbpv=1&dq=%22instance%22+mastodon&pg=PA1140&printsec=frontcover', 'page': '1140'}

    text="""'''1937''', [[w:Zora Neale Hurston|Zora Neale Hurston]], ''Their Eyes Were Watching God'', Harper (2000), page 107:"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '1937', 'author': '[[w:Zora Neale Hurston|Zora Neale Hurston]]', 'title': 'Their Eyes Were Watching God', 'page': '107', 'publisher': 'Harper', 'year_published': '2000'}

#    text="""'''1910''', Patrick Weston Joyce, ''[[s:English as we speak it in Ireland|English as we speak it in Ireland]]'', [[s:English as we speak it in Ireland/IV|chapter 5]]"""
#    res = parse_details(text)
#    print(res)
#    assert res == {'year': '1910', 'author': 'Patrick Weston Joyce', 'title': '[[s:English as we speak it in Ireland|English as we speak it in Ireland]]', 'chapter': '[[s:English as we speak it in Ireland/IV|chapter 5]]'}


    # Publisher not in () with no ISBN
    text="""'''2000''', Paul Wilkes, ''And They Shall Be My People: An American Rabbi and His Congregation'', Grove Press, p. 135:"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '2000', 'author': 'Paul Wilkes', 'title': 'And They Shall Be My People: An American Rabbi and His Congregation', 'page': '135', 'publisher': 'Grove Press'}


    text="""'''1875''', Arthur Crump, ''The Theory of Stock Exchange Speculation'' (page 28)"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '1875', 'author': 'Arthur Crump', 'title': 'The Theory of Stock Exchange Speculation', 'page': '28'}

    # Trailing date
    #'''2022''', Adela Suliman, "[https://www.washingtonpost.com/sports/2022/07/20/quidditch-quadball-name-change-jk-rowling/ Quidditch is now quadball, distancing game from J.K. Rowling, league says]", ''The Washington Post'', 20 July 2022:
    #'''2023''', Munza Mushtaq, ''[https://www.csmonitor.com/World/Making-a-difference/2023/0106/In-Sri-Lanka-Pastor-Moses-shows-the-power-of-a-free-lunch In Sri Lanka, Pastor Moses shows the power of a free lunch]'', in: The Christian Science Monitor, January 6 2023



    text="""'''1990''', {{w|Andrew Davies}}, {{w|Michael Dobbs}}, ''[[w:House of Cards (UK TV show)|House of Cards]]'', Season 1, Episode 4"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '1990', 'author': '{{w|Andrew Davies}}', 'author2': '{{w|Michael Dobbs}}', 'title': '[[w:House of Cards (UK TV show)|House of Cards]]', 'season': '1', 'episode': '4'}


    # Month Year
#    text="""'''2012''', Adam Mathew, "Mass Effect 3", ''PlayStation Magazine'' (Australia), April 2012, [https://archive.org/details/Official_AUS_Playstation_Magazine_Issue_067_2012_04_Derwent_Howard_Publishing_AU/page/60/mode/2up?q=me3 page 60]:"""
#    res = parse_details(text)
#    print(res)
#    assert res == {'year': '2012', 'author': 'Adam Mathew', 'chapter': 'Mass Effect 3', 'title': 'PlayStation Magazine', 'month': 'April', 'url': 'https://archive.org/details/Official_AUS_Playstation_Magazine_Issue_067_2012_04_Derwent_Howard_Publishing_AU/page/60/mode/2up?q=me3', 'page': '60'}


    # Day Month Year
    text="""'''2012''', Adam Gopnik, "Vive La France", ''The New Yorker'', 7 May 2012:"""
    res = parse_details(text)
    print(res)
    assert res == {'author': 'Adam Gopnik', 'chapter': 'Vive La France', 'title': 'The New Yorker', 'date': '7 May 2012'}

    # Month Day Year
    text="""'''2012''', Adam Gopnik, "Vive La France", ''The New Yorker'', May 7 2012:"""
    res = parse_details(text)
    print(res)
    assert res == {'author': 'Adam Gopnik', 'chapter': 'Vive La France', 'title': 'The New Yorker', 'date': 'May 7 2012'}

    # Vol VI, no XXXII
    text="""'''1864''' "The Adventures of a Lady in Search of a Horse", ''London Society'' Vol VI, no XXXII (July 1864) [http://books.google.com/books?id=_NscAQAAIAAJ&dq=heepishly&pg=PA5#v=onepage&q=heepishly&f=false p. 5]"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '1864', 'chapter': 'The Adventures of a Lady in Search of a Horse', 'title': 'London Society', 'volume': 'VI', 'number': 'XXXII', 'month': 'July', 'pageurl': 'http://books.google.com/books?id=_NscAQAAIAAJ&dq=heepishly&pg=PA5#v=onepage&q=heepishly&f=false', 'page': '5'}

    # Simple
    text = """'''2013''', {{w|Kacey Musgraves}}, "My House":"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '2013', 'author': '{{w|Kacey Musgraves}}', 'title': 'My House'}


    text = """'''2008''' July 31, [[w:Richard Zoglin|Richard Zoglin]], "[https://web.archive.org/web/20080807052344/http://www.time.com/time/magazine/article/0,9171,1828301,00.html A New Dawn for ''Hair'']," ''Time''"""
    res = parse_details(text)
    print(res)
    assert res == {'date': 'July 31 2008', 'author': '[[w:Richard Zoglin|Richard Zoglin]]', 'chapter': "A New Dawn for ''Hair''", 'chapterurl': 'https://web.archive.org/web/20080807052344/http://www.time.com/time/magazine/article/0,9171,1828301,00.html', 'title': 'Time'}



def test_parse_details2():


    text="""'''2007''', Eli Maor, ''The Pythagorean Theorem: A 4,000-year History'', {{w|Princeton University Press}}, [https://books.google.com.au/books?id=Z5VoBGy3AoAC&pg=PA1&dq=%22Fermat%27s+Last+Theorem%22&hl=en&sa=X&ved=0ahUKEwiSltz2xMnWAhUMzLwKHcAiBiY4ZBDoAQhcMAk#v=onepage&q=%22Fermat's%20Last%20Theorem%22&f=false page 1],"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '2007', 'author': 'Eli Maor', 'title': 'The Pythagorean Theorem: A 4,000-year History', 'pageurl': "https://books.google.com.au/books?id=Z5VoBGy3AoAC&pg=PA1&dq=%22Fermat%27s+Last+Theorem%22&hl=en&sa=X&ved=0ahUKEwiSltz2xMnWAhUMzLwKHcAiBiY4ZBDoAQhcMAk#v=onepage&q=%22Fermat's%20Last%20Theorem%22&f=false", 'page': '1', 'publisher': '{{w|Princeton University Press}}'}

    text = """'''1955''', {{w|W. H. Auden}}, “Lakes” in ''Selected Poetry of W. H. Auden'', New York: Modern Library, 1959, p.{{nbsp}}149,<sup>[https://openlibrary.org/ia/selectedpoetry00whau]</sup>"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '1955', 'author': '{{w|W. H. Auden}}', 'chapter': 'Lakes', 'title': 'Selected Poetry of W. H. Auden', 'url': 'https://openlibrary.org/ia/selectedpoetry00whau', 'page': '149', 'publisher': 'Modern Library', 'year_published': '1959', 'location': 'New York'}


    text = """'''2011''', Deepika Phukan, translating {{w|Arupa Patangia Kalita}}, ''The Story of Felanee'':"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '2011', 'author': '{{w|Arupa Patangia Kalita}}', 'translator': 'Deepika Phukan', 'title': 'The Story of Felanee'}


    # author & al. pages roman-roman
    text = """'''2006''', Barry A. Kosmin & al., ''Religion in a Free Market'', [http://books.google.com/books?id=eK4ccdPm9T4C&pg=PR16 pages xvi–xvii]:"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '2006', 'author': 'Barry A. Kosmin', 'author2': 'et al', 'title': 'Religion in a Free Market', 'pageurl': 'http://books.google.com/books?id=eK4ccdPm9T4C&pg=PR16', 'pages': 'xvi–xvii'}


    text = """'''1974''', "[http://news.google.ca/newspapers?id=mWkqAAAAIBAJ&sjid=xVUEAAAAIBAJ&pg=4318,6028745&dq=did-a-number-on&hl=en Sports: Full-time Franco Busts A Couple, Rushes For 141]," ''Pittsburgh Press'', 29 Oct., p. 26 (retrieved 20 Aug. 2010):"""
    res = parse_details(text)
    print(res)
    assert res == {'date': '29 Oct 1974', 'chapter': 'Sports: Full-time Franco Busts A Couple, Rushes For 141', 'chapterurl': 'http://news.google.ca/newspapers?id=mWkqAAAAIBAJ&sjid=xVUEAAAAIBAJ&pg=4318,6028745&dq=did-a-number-on&hl=en', 'title': 'Pittsburgh Press', 'accessdate': '20 Aug. 2010', 'page': '26'}

    text ="""'''1970''', "[https://web.archive.org/web/20130822174940/http://www.time.com/time/magazine/article/0,9171,909210,00.html Alive and Well]," ''Time'', 18 May:"""
    res = parse_details(text)
    print(res)
    assert res == {'date': '18 May 1970', 'chapter': 'Alive and Well', 'chapterurl': 'https://web.archive.org/web/20130822174940/http://www.time.com/time/magazine/article/0,9171,909210,00.html', 'title': 'Time'}


    text="""'''1999''', Buddy Seigal, "[https://web.archive.org/web/20140826030806/http://www.ocweekly.com/1999-08-26/music/even-old-englishmen-still-get-wood/ Even Old Englishmen Still Get Wood]," ''OC Weekly'', 26 Aug. (retrieved 16 June 2009):"""
    res = parse_details(text)
    print(res)
    assert res == {'date': '26 Aug 1999', 'author': 'Buddy Seigal', 'chapter': 'Even Old Englishmen Still Get Wood', 'chapterurl': 'https://web.archive.org/web/20140826030806/http://www.ocweekly.com/1999-08-26/music/even-old-englishmen-still-get-wood/', 'title': 'OC Weekly', 'accessdate': '16 June 2009'}


    text="""'''2009''', John Metzler, "[http://www.worldtribune.com/worldtribune/WTARC/2009/mz0630_07_31.asp High stakes for democracy (and terrorism) as Afghans prepare to vote ]," ''World Tribune'' (US), 7 August (retrieved 15 Sep 2010):"""
    res = parse_details(text)
    print(res)
    assert res == {'date': '7 August 2009', 'author': 'John Metzler', 'chapter': 'High stakes for democracy (and terrorism) as Afghans prepare to vote', 'chapterurl': 'http://www.worldtribune.com/worldtribune/WTARC/2009/mz0630_07_31.asp', 'title': 'World Tribune', 'accessdate': '15 Sep 2010', 'location': 'US'}

    text="""'''2003''', ''Cincinnati Magazine'' (volume 36, number 5, page 26)"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '2003', 'title': 'Cincinnati Magazine', 'volume': '36', 'number': '5', 'page': '26'}


    # Start-End for issue number
    text="""'''2004''' September-October, ''American Cowboy'', volume 11, number 2, page 53:"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '2004', 'issue': 'September-October', 'title': 'American Cowboy', 'volume': '11', 'number': '2', 'page': '53'}


    # no author, strip {{nowrap}}
    text="""'''2009''', "Is the era of free news over?", ''The Observer'', {{nowrap|10 May:}}"""
    res = parse_details(text)
    print(res)
    assert res == {'date': '10 May 2009', 'chapter': 'Is the era of free news over?', 'title': 'The Observer'}


    # {{C.E.}} after year, page=1,392
    text="""'''1704''' {{C.E.}}, ''Philoſophical tranſactions, Giving ſome Account of the Preſent Undertakings, Studies and Labours of the Ingenious, In many Conſiderable Parts of the World'', volume XXIII, [http://books.google.co.uk/books?id=j2LH2ErAT34C&pg=RA3-PA1392&dq=%22are%C3%A6%22&lr=&num=100&as_brr=0&ei=42YtS4PKDJzyzQSk3dCtBA&cd=41#v=onepage&q=%22are%C3%A6%22&f=false page 1,392]:"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '1704', 'title': 'Philoſophical tranſactions, Giving ſome Account of the Preſent Undertakings, Studies and Labours of the Ingenious, In many Conſiderable Parts of the World', 'volume': 'XXIII', 'pageurl': 'http://books.google.co.uk/books?id=j2LH2ErAT34C&pg=RA3-PA1392&dq=%22are%C3%A6%22&lr=&num=100&as_brr=0&ei=42YtS4PKDJzyzQSk3dCtBA&cd=41#v=onepage&q=%22are%C3%A6%22&f=false', 'page': '1,392'}


    # Lines
    text="""'''1850''' [[w:Dante Gabriel Rossetti|Dante Gabriel Rossetti]], ''The Blessed Damozel'', lines 103-108"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '1850', 'author': '[[w:Dante Gabriel Rossetti|Dante Gabriel Rossetti]]', 'title': 'The Blessed Damozel', 'lines': '103-108'}

    # Line
    text="""'''1798''', [[w:William Cowper|William Cowper]], ''On Receipt of My Mother's Picture'', [https://web.archive.org/web/20090228072946/http://rpo.library.utoronto.ca/poem/564.html line 60]"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '1798', 'author': '[[w:William Cowper|William Cowper]]', 'title': "On Receipt of My Mother's Picture", 'line': '60', 'url': 'https://web.archive.org/web/20090228072946/http://rpo.library.utoronto.ca/poem/564.html'}





    # publisher comic strip not idea
    text = """'''1934''', {{w|George Herriman}}, ''{{w|Krazy Kat}}'', Tuesday, April 17 comic strip ({{ISBN|978-1-63140-408-5}}, p. 112):"""
    res = parse_details(text)
    print(res)
    assert res == {'date': 'April 17 1934', 'author': '{{w|George Herriman}}', 'title': '{{w|Krazy Kat}}', 'page': '112', 'publisher': 'comic strip', 'isbn': '978-1-63140-408-5'}


    text="""'''2006''', Michael R. Waters with Mark Long and William Dickens, ''Lone Star Stalag: German Prisoners of War at Camp Hearne''"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '2006', 'author': 'Michael R. Waters', 'author2': 'Mark Long', 'author3': 'William Dickens', 'title': 'Lone Star Stalag: German Prisoners of War at Camp Hearne'}


    # and
    text="""'''2015''', Simon Carnell and Erica Segre, translating {{w|Carlo Rovelli}}, ''Seven Brief Lessons on Physics'', Penguin 2016, p. 44:"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '2015', 'translators': 'Simon Carnell; Erica Segre', 'author': '{{w|Carlo Rovelli}}', 'title': 'Seven Brief Lessons on Physics', 'page': '44', 'publisher': 'Penguin', 'year_published': '2016'}

    text="""'''1962''', Hans Sperber, Travis Trittschuh & Hans Sperber, ''American Political Terms''"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '1962', 'author': 'Hans Sperber', 'author2': 'Travis Trittschuh', 'author3': 'Hans Sperber', 'title': 'American Political Terms'}


    text="""'''1977''', Olga Kuthanová, translating Jan Hanzák & Jiří Formánek, ''The Illustrated Encyclopedia of Birds'', London 1992, p. 177:"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '1977', 'translator': 'Olga Kuthanová', 'author': 'Jan Hanzák', 'author2': 'Jiří Formánek', 'title': 'The Illustrated Encyclopedia of Birds', 'page': '177', 'location': 'London', 'year_published': '1992'}

    text="""'''1775''', María Francisca Isla y Losada, ''Romance''"""
    res = parse_details(text)
    print(res)
    assert res ==  {'author': 'María Francisca Isla y Losada', 'title': 'Romance', 'year': '1775'}

def test_parse_details3():

    text="""'''1925''', {{w|Ford Madox Ford}}, ''No More Parades'', Penguin 2012 (''Parade's End''), p. 294:"""
    res = parse_details(text)
    print(res)
    assert res ==  None

    text="""'''1892''', Carl Deite translating William Theodore Brannt as ''A Practical Treatise on the Manufacture of Perfumery'', p. 230"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '1892', 'translator': 'Carl Deite', 'author': 'William Theodore Brannt', 'title': 'A Practical Treatise on the Manufacture of Perfumery', 'page': '230'}

    text="""'''1727''', John Gaspar Scheuchzer translating Engelbert Kaempfer's ''History of Japan'', Vol. I, p. 287:"""
    res = parse_details(text)
    print(res)
    assert res ==  {'year': '1727', 'translator': 'John Gaspar Scheuchzer', 'author': 'Engelbert Kaempfer', 'title': 'History of Japan', 'volume': 'I', 'page': '287'}

    text="""'''1989''', Richard Winston & al. translating [[w:Carl Jung|Carl Jung]] & al. as ''Memories, Dreams, Reflections'', p. 108:"""
    res = parse_details(text)
    print(res)
    assert res ==  {'year': '1989', 'translators': 'Richard Winston; et al', 'author': '[[w:Carl Jung|Carl Jung]]', 'author2': 'et al', 'title': 'Memories, Dreams, Reflections', 'page': '108'}


    # TODO: Extract and process the URL links individually
    # Then try to identify the URL class from the text
    #
    # [“"']*(URL)[”"']*

    text="""'''2007''', Tim Pooley, “The Uneasy Interface”, in Yuji Kawaguchi et al. (editors), ''Corpus-Based Perspectives in Linguistics'', John Benjamins Publishing Company, {{ISBN|978-90-272-3318-9}}, [http://books.google.com/books?id=0qrZwAZSQq4C&pg=PA175&dq=Torontarians page 175]:"""
    res = parse_details(text)
    print(res)
#    assert res ==  "X"

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


def test_parse_details_unhandled():


    # tranlating Author & al.
    text="""'''1898''', Hobart Charles Porter translating Eduard Strasburger & al. ''A Text-book of Botany'', 109:"""
    res = parse_details(text)
    print(res)
    assert res == None

    # Fail if published date newer than citation date (usually used in journals, not needed here in a book citation)
    text="""'''1772''', {{w|Frances Burney}}, ''Journals & Letters'', Penguin 2001, 30 May:"""
    res = parse_details(text)
    print(res)
    assert res == None # {'year': '1772', 'author': '{{w|Frances Burney}}', 'title': 'Journals & Letters', 'year_published': '2001', 'date_published': '30 May 2001', 'publisher': 'Penguin'}



    # Extra title, unhandled
    text="""'''2010''', S. Suzanne Nielsen, ed, ''Food Analysis, fourth edition'', {{ISBN|978-1-4419-1477-4}}, Chapter 12, "Traditional Methods for Mineral Analysis", page 213"""
    res = parse_details(text)
    print(res)
    assert res == None

    # Part, not yet handled
    text="""'''2002''', John Maynard, ''Aborigines and the ‘Sport of Kings’: Aboriginal Jockeys in Australian Racing History'', Aboriginal Studies Press (2013), {{ISBN|9781922059543}}, part II, {{gbooks|4erLAgAAQBAJ|96|streeted}}:"""
    res = parse_details(text)
    print(res)
    assert res == None


    # Publisher in parenthesis, not handled - other items can be in parethensis
    text="""'''2010''' Frank Buchmann-Moller ''Someone to Watch Over Me: The Life and Music of Ben Webster'' (University of Michigan Press) {{ISBN|0472025988}} p.57"""
    res = parse_details(text)
    print(res)
    assert res == None

    # Multiple URLS
    text="""'''2009''', Roger Ebert, ''Roger Ebert's Movie Yearbook 2010'',<sup >[http://books.google.com/books?id=-1aM7D_ymdAC ][http://www.amazon.com/Roger-Eberts-Movie-Yearbook-2010/dp/B003STCR2E ]</sup> Andrews McMeel Publishing, {{ISBN|978-0-7407-8536-8}}, page 363:"""
    res = parse_details(text)
    print(res)
    assert res == None

    # ''et al.'' in editor
    text = """'''1842''', [[w:Solomon Ludwig Steinheim|Solomon Ludwig Steinheim]], "On the Perennial and the Ephemeral in Judaism" in ''The Jewish Philosophy Reader'' (2000), edited by Daniel H. Frank ''et al.'', {{ISBN|9780415168601}}, [http://books.google.ca/books?id=_UbNP_Y0edQC&dq=platitudinize+OR+platitudinizes+OR+platitudinized&q=%22platitudinized%2C%3A#v=snippet&q=%22platitudinized%2C%3A&f=false p. 402]:"""
    res = parse_details(text)
    print(res)
    assert res == None


    # bad publisher
    text="""'''1964''', {{w|J. D. Salinger}} (author), Judit Gyepes (translator), ''Zabhegyező'' [''{{w|The Catcher in the Rye}}''], Budapest: Európa Könyvkiadó (1998), {{ISBN|9630764024}}, chapter 11, page 95:"""
    res = parse_details(text)
    print(res)
    assert res == None

    # ISBN before title
    text="""'''2008''', Yolanda McVey, {{ISBN|9781585715787}}, ''Love's Secrets'':"""
    res = parse_details(text)
    print(res)
    assert res == None


    # crap after author
    text="""'''2004''', John P. Frayne and Madeleine Marchaterre, “Notes” to ''The Collected Works of W. B. Yeats, Volume IX: Early Articles and Reviews'', Scribner, {{ISBN|0-684-80730-0}}, [http://books.google.com/books?id=61IX00wwuYYC&pg=PA553&dq=in-memoriam page 553]:"""
    res = parse_details(text)
    print(res)
    assert res == None

    text="""'''2013''', [[w:Tom Hanks|Tom Hanks]], introduction to ''Two Sides of the Moon: Our Story of the Cold War Space Race'' by Alexei Leonov and David Scott, Open Road Media {{ISBN|9781480448742}}"""
    res = parse_details(text)
    print(res)
    assert res == None

    # crap after author
    text="""'''2004''', John P. Frayne and Madeleine Marchaterre, “Notes” to ''The Collected Works of W. B. Yeats, Volume IX: Early Articles and Reviews'', Scribner, {{ISBN|0-684-80730-0}}, [http://books.google.com/books?id=61IX00wwuYYC&pg=PA553&dq=in-memoriam page 553]:"""
    res = parse_details(text)
    print(res)
    assert res == None

    text == """#* '''2006''', Irvine Welsh, Federico Corriente Basús transl., ''Porno'', Anagrama ({{ISBN|9788433938565}})"""
    res = parse_details(text)
    print(res)
    assert res == None




    # Translator, extra junk
    text="""'''1974''': [[w:Plato|Plato]] (author) and Desmond Lee (translator), ''[[w:The Republic (Plato)|The Republic]]'' (2nd edition, revised; Penguin Classics; {{ISBN|0140440488}}, Translator’s Introduction, pages 51 and 53:"""
    res = parse_details(text)
    print(res)
    assert res == None

    # Volume info, no publisher
    text="""'''2006''', Renaat Declerck, Susan Reed, Bert Cappelle, ''The Grammar of the English Verb Phrase'', vol. 1, ''The Grammar of the English Tense System'', {{ISBN|9783110185898}}, page 6:"""
    res = parse_details(text)
    print(res)
    assert res == None


    text = """'''2010''', L. A. Banks, &quot;Dog Tired (of the Drama!)&quot;, in ''Blood Lite II: Overbite'' (ed. Kevin J. Anderson), Gallery Books (2010), {{ISBN|9781439187654}}, [http://books.google.com/books?id=5ckoF81np3sC&amp;pg=PA121&amp;dq=%22beta%22+%22alpha+males%22 page 121]:"""
    res = parse_details(text)
    print(res)
    assert res == None

    text = """'''1756''', {{w|Thomas Thistlewood}}, diary, quoted in '''2001''', Glyne A. Griffith, ''Caribbean Cultural Identities'', Bucknell University Press ({{ISBN|9780838754757}}), page 38:"""
    res = parse_details(text)
    print(res)
    assert res == None

    text = """'''1986''', Anthony Burgess, ''Homage to Qwert Yuiop'' (published as ''But Do Blondes Prefer Gentlemen?'' in USA)"""
    res = parse_details(text)
    print(res)
    assert res == None

    text="""'''1979''', ''New West'', volume 4, part 1, page 128:"""
    res = parse_details(text)
    print(res)
    assert res == None

    text="""'''2016''', "The Veracity Elasticity", season 10, episode 7 of ''{{w|The Big Bang Theory}}''"""
    res = parse_details(text)
    print(res)
    assert res == None

    # TODO: in: should signal that the following is a journal title
    text = """'''2022''', Shaakirrah Sanders, ''[https://www.scotusblog.com/2022/01/court-rejects-door-opening-as-a-sixth-amendment-confrontation-clause-exception/ Court rejects “door opening” as a Sixth Amendment confrontation-clause exception]'', in: SCOTUSblog, 2022-01-20"""
    res = parse_details(text)
    print(res)
    assert res == None

    # Fail on bad name
    text="""'''1885''', Joseph Parker,T''he people's Bible: discourses upon Holy Scripture'', volume 16, page 83"""
    res = parse_details(text)
    print(res)
    assert res == None

    # Fail on mismatched dates
    text = """'''2011''' Feb 21, "[http://www.dailymail.co.uk/news/article-1359019/Bankers-revive-strip-club-Spearmint-Rhino-bumper-bonuses.html Bankers revive strip club Spearmint Rhino with bumper bonuses]," ''Daily Mail'' (UK) <small>(24 July 2011)</small>:"""
    res = parse_details(text)
    print(res)
    assert res == None



    # Multi chapter, should be journal
    text="""'''1935''', {{w|Arthur Leo Zagat}}, ''Girl of the Goat God'', in ''Dime Mystery Magazine'', November 1935, Chapter IV, [http://gutenberg.net.au/ebooks13/1304651h.html]"""
    res = parse_details(text)
    print(res)
    assert res == None

    text="""'''2022''', Matteo Wong, ''[https://www.theatlantic.com/technology/archive/2022/12/avatar-2-movie-navi-constructed-language/672616/ Hollywood’s Love Affair With Fictional Languages]'', in: The Atlantic, December 31 2022"""
    res = parse_details(text)
    print(res)
    assert res == None

    # "in" and fancy quotes
    text="""'''1633''', {{w|John Donne}}, “The Indifferent” in ''Poems'', London: John Marriot, p. 200,<sup>[http://name.umdl.umich.edu/A69225.0001.001]</sup>"""
    res = parse_details(text)
    print(res)
    assert res == None

    


def test_entry():

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


def test_get_leading_chapter_title():

    assert fixer.get_leading_chapter_title('"foo bar", blah') == ("foo bar", "blah")
    assert fixer.get_leading_chapter_title(" ''foo bar'' in blah") == ("foo bar", "blah")
    assert fixer.get_leading_chapter_title(" ''foo bar'', in: blah") == ("foo bar", "blah")
    assert fixer.get_leading_chapter_title(" ''foo bar'' blah") == ("", " ''foo bar'' blah")
    assert fixer.get_leading_chapter_title("''Homage to Qwert Yuiop'' (published as ''But Do Blondes Prefer Gentlemen?'' in USA)") == ("", "''Homage to Qwert Yuiop'' (published as ''But Do Blondes Prefer Gentlemen?'' in USA)")

    text = """\
''[https://www.theatlantic.com/technology/archive/2022/12/avatar-2-movie-navi-constructed-language/672616/ Hollywood’s Love Affair With Fictional Languages]'', in: The Atlantic, December 31 2022\
"""
    expected = ('[https://www.theatlantic.com/technology/archive/2022/12/avatar-2-movie-navi-constructed-language/672616/ Hollywood’s Love Affair With Fictional Languages]', 'The Atlantic, December 31 2022')

    res = fixer.get_leading_chapter_title(text)
    print(res)
    assert res == expected


def test_season_episode():

    assert fixer.get_season_episode('s01e12') == ("01", "12", " ")
    assert fixer.get_season_episode('x s01e12 x') == ("01", "12", "x x")
    assert fixer.get_season_episode('xs01e12') == ("", "", "xs01e12")
    assert fixer.get_season_episode('s01e12x') == ("", "", "s01e12x")


def test_split_names():

    res = list(fixer.split_names("John Doe, Jr., John Doe, Dr. Jane Doe (translator), Ed One, Ed Two (eds.)"))
    print(res)
    assert res == ['John Doe, Jr.', 'John Doe', 'Dr. Jane Doe (translator)', 'Ed One', 'Ed Two (eds.)']

    res = list(fixer.split_names("John Doe, Jr. (author), Dr. Jane Doe (translator), Ed One, Ed Two (eds.)"))
    print(res)
    assert res == ['John Doe, Jr. (author)', 'Dr. Jane Doe (translator)', 'Ed One', 'Ed Two (eds.)']

    res = list(fixer.split_names("[[w:William F. Buckley, Jr. (author)|William F. Buckley]], John Doe, Jr., [[w:George Byron, 6th Baron Byron|Lord Byron]]"))
    print(res)
    assert res == ['[[w:William F. Buckley, Jr. (author)|William F. Buckley]]', 'John Doe, Jr.', '[[w:George Byron, 6th Baron Byron|Lord Byron]]']



def test_classify_names():

    names = fixer.split_names("John Doe, Jr., Jane Doe (translator), Ed One, Ed Two (eds.)")
    assert names == ['John Doe, Jr.', 'Jane Doe (translator)', 'Ed One', 'Ed Two (eds.)']
    res = fixer.classify_names(names)
    print(res)
    assert res == {"author": ["John Doe, Jr."], "translator": ["Jane Doe"], "editor": ["Ed One", "Ed Two"]}


    names = fixer.split_names("David Squire et al")
    res = fixer.classify_names(names)
    print(res)
    assert res == {'author': ['David Squire', 'et al']}

    names = fixer.split_names("Lewis B. Ware ''et al.''")
    res = fixer.classify_names(names)
    print(res)
    assert res == {'author': ['Lewis B. Ware', 'et al']}


def test_get_date():

    assert fixer.get_date('Test, 12 July, 2012 abcd') == ('2012', 'July', -12, 'Test, abcd')
    assert fixer.get_date('Test, July 12, 2012 abcd') == ('2012', 'July', 12, 'Test, abcd')
    assert fixer.get_date('Test, 12 Jul, 2012 abcd') == ('2012', 'Jul', -12, 'Test, abcd')
    assert fixer.get_date('Test, Jul 12, 2012 abcd') == ('2012', 'Jul', 12, 'Test, abcd')

    assert fixer.get_date('x2012-02-02x') == (None, None, None, 'x2012-02-02x')
    assert fixer.get_date('Test 2012-02-02') == ('2012', 'Feb', 2, 'Test  ')
    assert fixer.get_date('Test, 2012-2-2 abcd') == ('2012', 'Feb', 2, 'Test,  abcd')
    assert fixer.get_date('Test, 2012-12-02 abcd') == ('2012', 'Dec', 2, 'Test,  abcd')
    assert fixer.get_date('Test, 2012-12-31 abcd') == ('2012', 'Dec', 31, 'Test,  abcd')
    assert fixer.get_date('Test, 2012-02-31 abcd') == (None, None, None, 'Test, 2012-02-31 abcd')

    assert fixer.get_date('16 Jan 2016') == ('2016', 'Jan', -16, ' ')
    assert fixer.get_date('22 Sept 2017') == ('2017', 'Sept', -22, ' ')
    assert fixer.get_date('8 Sept. 2009') == ('2009', 'Sept', -8, ' ')

    assert fixer.get_date('Sun 8 Sept. 2009') == ('2009', 'Sept', -8, ' ')
    assert fixer.get_date('Sunday, 8 Sept. 2009') == ('2009', 'Sept', -8, ' ')
    assert fixer.get_date('Tues 8 Sept. 2009') == ('2009', 'Sept', -8, ' ')

    assert fixer.get_date("Penguin 2001, May 30") == ('2001', 'May', 30, 'Penguin  ')
    assert fixer.get_date("Penguin 2001, 30 May") == ('2001', 'May', -30, 'Penguin  ')

    assert fixer.get_date("Penguin 20 Jan 08") == ('2008', 'Jan', -20, 'Penguin ')

def test_get_leading_issue():
    assert fixer.get_leading_issue("Spring-Fall. Blah") == ('Spring-Fall', 'Blah')
    assert fixer.get_leading_issue("Oct-Nov. Blah") == ('Oct-Nov', 'Blah')
    assert fixer.get_leading_issue("Winter. Blah") == ('Winter', 'Blah')

def test_strip_wrapper_templates():
    assert fixer.strip_wrapper_templates("ABC", ["temp1", "temp2"]) == "ABC"
    assert fixer.strip_wrapper_templates("{{temp1|ABC}}", ["temp1"]) == "ABC"
    assert fixer.strip_wrapper_templates("{{temp1|ABC}}", ["ABC", "temp1"]) == "ABC"
    assert fixer.strip_wrapper_templates("AB{{temp1|blah}}CD {{temp2|X}} X{{temp1| x }}X {{temp1|{{temp2|ABC}}}}", ["temp1", "temp2"]) == \
            "ABblahCD X X x X ABC"


def notest_all():

    import re
    import sys

    valid = 0
    invalid = 0
    with open("errors") as infile:
        start = False
        for line in infile:
            line = line.strip()
            if not line:
                continue

            if not start:
                if line == "===unparsable_line===":
                    start=True
                continue

            m = re.match(r": \[\[(.*?)]] <nowiki>(.*?)</nowiki>", line)
            if not m:
                continue
            page = m.group(1)
            text = m.group(2)

            text = text.lstrip("#:* ").strip()
            res = parse_details(text)
            if res:
                print(line)
                valid += 1
            else:
                invalid += 1
#                if res and "publisher" in res:
#                    print(res["publisher"])
#                authors = [v for k,v in res.items() if k.startswith("author")]
#                for author in authors:
#                    print(author)
                #print(line)
#                if len(authors)>1 or any(len(a) > 20 or len(a.split(" ")) > 2 for a in authors):
#                    print("         ", authors, "<<<<<<<<<<<<<")
#                else:
#                    print("         ", authors)
#                print("")

    print("Valid", valid, file=sys.stderr)
    print("Invalid", invalid, file=sys.stderr)

if __name__ == "__main__":
    notest_all()



