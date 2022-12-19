from ..fix_bare_quotes import QuoteFixer
parse_details = QuoteFixer.parse_details

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
    assert res == {'year': '2013', 'translator': 'Hans Jørgen Birkmose', 'author': 'Charles Dickens', 'title': 'Oliver Twist', 'publisher': 'Klim', 'isbn': '9788771292855'}


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


    text="""'''2006''', Henrik Ibsen, trans. by Odd Tangerud, ''[http://www.gutenberg.org/files/20162/20162-h/20162-h.htm La kolonoj de la socio]'', {{ISBN|82-91707-52-9}}"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '2006', 'translator': 'Odd Tangerud', 'author': 'Henrik Ibsen', 'title': '[http://www.gutenberg.org/files/20162/20162-h/20162-h.htm La kolonoj de la socio]', 'isbn': '82-91707-52-9'}

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

    # ISBN before title
    text="""'''2008''', Yolanda McVey, {{ISBN|9781585715787}}, ''Love's Secrets'':"""
    res = parse_details(text)
    print(res)
    assert res == None

    # Volume
    text="""'''2008''', John L. Capinera, ''Encyclopedia of Entomology'' {{ISBN|1402062427}}, volume 4, page 3326:"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '2008', 'author': 'John L. Capinera', 'title': 'Encyclopedia of Entomology', 'volume': '4', 'page': '3326', 'isbn': '1402062427'}

    # bad publisher
    text="""'''1964''', {{w|J. D. Salinger}} (author), Judit Gyepes (translator), ''Zabhegyező'' [''{{w|The Catcher in the Rye}}''], Budapest: Európa Könyvkiadó (1998), {{ISBN|9630764024}}, chapter 11, page 95:"""
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

    # Publisher in parenthesis, not handled - other items can be in parethensis
    text="""'''2010''' Frank Buchmann-Moller ''Someone to Watch Over Me: The Life and Music of Ben Webster'' (University of Michigan Press) {{ISBN|0472025988}} p.57"""
    res = parse_details(text)
    print(res)
    assert res == None

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

    # Multiple URLS
    text="""'''2009''', Roger Ebert, ''Roger Ebert's Movie Yearbook 2010'',<sup >[http://books.google.com/books?id=-1aM7D_ymdAC ][http://www.amazon.com/Roger-Eberts-Movie-Yearbook-2010/dp/B003STCR2E ]</sup> Andrews McMeel Publishing, {{ISBN|978-0-7407-8536-8}}, page 363:"""
    res = parse_details(text)
    print(res)
    assert res == None

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
    assert res == {'year': '1988', 'author': 'Lewis B. Ware', 'author2': 'et al', 'title': 'Low-Intensity Conflict in the Third World,', 'page': '139', 'publisher': 'Air Univ. Press', 'isbn': '978-1585660223'}

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


    # publisher followed by ed.
    text = """'''1940''', [[w:Carson McCullers|Carson McCullers]], ''[[w:The Heart Is a Lonely Hunter|The Heart Is a Lonely Hunter]]'', 2004 Houghton Mifflin ed., {{ISBN|0618526412}}, page 306,"""
    res = parse_details(text)
    print(res)
    assert res == {'year': '1940', 'author': '[[w:Carson McCullers|Carson McCullers]]', 'title': '[[w:The Heart Is a Lonely Hunter|The Heart Is a Lonely Hunter]]', 'page': '306', 'publisher': 'Houghton Mifflin', 'year_published': '2004', 'isbn': '0618526412'}


    # ''et al.'' in editor
    text = """'''1842''', [[w:Solomon Ludwig Steinheim|Solomon Ludwig Steinheim]], "On the Perennial and the Ephemeral in Judaism" in ''The Jewish Philosophy Reader'' (2000), edited by Daniel H. Frank ''et al.'', {{ISBN|9780415168601}}, [http://books.google.ca/books?id=_UbNP_Y0edQC&dq=platitudinize+OR+platitudinizes+OR+platitudinized&q=%22platitudinized%2C%3A#v=snippet&q=%22platitudinized%2C%3A&f=false p. 402]:"""
    res = parse_details(text)
    print(res)
    assert res == None

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

    # Unhandled
    text = """'''1934''', {{w|George Herriman}}, ''{{w|Krazy Kat}}'', Tuesday, April 17 comic strip ({{ISBN|978-1-63140-408-5}}, p. 112):"""
    res = parse_details(text)
    assert res == None

    text = """'''2010''', L. A. Banks, &quot;Dog Tired (of the Drama!)&quot;, in ''Blood Lite II: Overbite'' (ed. Kevin J. Anderson), Gallery Books (2010), {{ISBN|9781439187654}}, [http://books.google.com/books?id=5ckoF81np3sC&amp;pg=PA121&amp;dq=%22beta%22+%22alpha+males%22 page 121]:"""
    res = parse_details(text)
    assert res == None

    text = """'''1756''', {{w|Thomas Thistlewood}}, diary, quoted in '''2001''', Glyne A. Griffith, ''Caribbean Cultural Identities'', Bucknell University Press ({{ISBN|9780838754757}}), page 38:"""
    res = parse_details(text)
    assert res == None


def test_entry():

    text = """
#* '''2014''', Dr. Aneesa Khan, ''Spice Doctor'', Author House ({{ISBN|9781496993014}}), page 37:#
#*: Marinade: 4 tbsp tomato puree
#*: 3 tbsp lemon juice
#*: 1 tsp crushed garlic
#*: {{...}}
#*: 1 tsp turmeric powder
#*: 1⁄2 tsp '''elachi''' powder
#*: 1⁄2 tsp pepper
"""

def notest_all():

    with open("isbn.txt") as infile:
        for line in infile:
            page, line = line.split("\t")
            line = line.lstrip("#:* ").strip()
            res = parse_details(line)
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

    assert 0
