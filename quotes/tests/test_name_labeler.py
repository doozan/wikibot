from autodooz.quotes.name_labeler import NameLabeler
fixer = NameLabeler(debug=True)


def test_is_valid_name():

    assert fixer.is_valid_name("John Smith") == True
    assert fixer.is_valid_name("John Smith, Jr.") == True
    assert fixer.is_valid_name("Dr. John Smith, Jr.") == True
    assert fixer.is_valid_name("Smith, Johnny D.") == True
    assert fixer.is_valid_name("J[ohn] Smith") == True
    assert fixer.is_valid_name("DJ Smith") == True
    assert fixer.is_valid_name("D.J. Smith") == True

    assert fixer.is_valid_name("D. J. Smith") == True
    assert fixer.is_valid_name("J. Smith") == True

    assert fixer.is_valid_name("D.J. Smith, Jr") == True

    assert fixer.is_valid_name("James Holbort Smith") == True
    assert fixer.is_valid_name("james Holbort Smith") == False
    assert fixer.is_valid_name("James Holbort smith") == False

    assert fixer.is_valid_name("James Holbort, Smith") == True
    assert fixer.is_valid_name("James, Holbort, Smith") == False
    assert fixer.is_valid_name('John "Johnny D" Smith') == False
    assert fixer.is_valid_name("John Smith Inc") == False

def test_split_names():

    res = fixer.split_names("J.D. Doe, Jr., John Doe, Dr. Jane Doe (translator), Ed One, Ed Two (eds.)")
    print(res)
    assert [x[0] for x in res] == ['J.D. Doe, Jr.', 'John Doe', 'Dr. Jane Doe (translator)', 'Ed One', 'Ed Two (eds.)']

    res = fixer.split_names("J.D. Doe, Jr., MD, John Doe, Dr. Jane Doe (translator), Ed One, Ed Two (eds.)")
    print(res)
    assert [x[0] for x in res] == ['J.D. Doe, Jr., MD', 'John Doe', 'Dr. Jane Doe (translator)', 'Ed One', 'Ed Two (eds.)']

#    ([('J.D. Doe', ', '), (',', 'Jr.'), (', ,MD', ', '), (',', 'John Doe'), (', ', ','), ('Dr. Jane Doe (translator)', ', '), (',', 'Ed One'), (', ', ','), ('Ed Two (eds.)', '')], [])

#    print(orig)
#    assert orig == [('J.D. Doe', ',', 0), (' Jr.', ',', 1), (' MD', ',', 1), (' John Doe', ',', 1), (' Dr. Jane Doe (translator)', ',', 2), (' Ed One', ',', 3), (' Ed Two (eds.)', '', 4)]


    res = fixer.split_names("John Doe, Jr. (author), Dr. Jane Doe (translator), Ed One, Ed Two (eds.)")
    assert [x[0] for x in res] == ['John Doe, Jr. (author)', 'Dr. Jane Doe (translator)', 'Ed One', 'Ed Two (eds.)']

    res = fixer.split_names("John Doe and Jane Doe")
    assert [x[0] for x in res] == ['John Doe', 'Jane Doe']

    res = fixer.split_names("John Doe & Jane Doe")
    assert [x[0] for x in res] == ['John Doe', 'Jane Doe']

    res = fixer.split_names("John and Jane Doe")
    assert [x[0] for x in res] == ['John and Jane Doe']

    res = fixer.split_names("Doe and Doe")
    assert [x[0] for x in res] == ['Doe', 'Doe']

    res = fixer.split_names("[[w:William F. Buckley, Jr. (author)|William F. Buckley]], John Doe, Jr., [[w:George Byron, 6th Baron Byron|Lord Byron]]")
    assert [x[0] for x in res] == ['[[w:William F. Buckley, Jr. (author)|William F. Buckley]]', 'John Doe, Jr.', '[[w:George Byron, 6th Baron Byron|Lord Byron]]']

#    text="Muhammad Khalid Masud et al - Dispensing Justice in Islam: Qadis and Their Judgements"
#    res = fixer.split_names(text)
#    assert [x[0] for x in res] == ['Muhammad Khalid Masud', 'et al', '- Dispensing Justice in Islam: Qadis', 'Their Judgements']

def test_classify_names():

    res = fixer.classify_names("A. Doe, ", "~author")
    print(res)
    assert res == ({'author': ['A. Doe']}, '')

    res = fixer.classify_names("John Doe, Jr., Jane Doe (translator), Ed Foo, Ed Bar (eds.)", "~author")
    print(res)
    assert res == ({"author": ["John Doe, Jr."], "translator": ["Jane Doe"], "editor": ["Ed Foo", "Ed Bar"]}, "")

    res = fixer.classify_names("translated by John Doe, Jr. and Jane Doe, Ed Foo (editor)", "~author")
    print(res)
    assert res == ({'translator': ['John Doe, Jr.', 'Jane Doe'], 'editor': ['Ed Foo']}, "")

    res = fixer.classify_names("M. Lucas Álvarez & P. Lucas Domínguez (eds.)", "~author")
    print(res)
    assert res == ({'editor': ['M. Lucas Álvarez', 'P. Lucas Domínguez']}, '')



    res = fixer.classify_names("Edgar Allan Poe, translated by Edwin Grobe", "~author")
    print(res)
    assert res == ({'author': ['Edgar Allan Poe'], 'translator': ['Edwin Grobe']}, '')

    # Fail if conflicting labels
    res = fixer.classify_names("translated by John Doe, Jr. (editor)", "~author")
    print(res)
    assert res == None


    # Fail if conflicting multi-labels
    res = fixer.classify_names("translated by John Doe, Jr. and Jane Doe, Ed One (editors)", "~author")
    print(res)
    assert res == None


    res = fixer.classify_names("David Squire et al", "~editor")
    print(res)
    assert res == None
#    assert res == ({'editor': ['David Squire', 'et al']}, "")

#    res = fixer.classify_names("Lewis B. Ware ''et al.''", "~editor")
#    print(res)
#    assert res == ({'editor': ['Lewis B. Ware', 'et al']}, "")

#    res = fixer.classify_names("John Doe ''et al.'' Jane Doe", "~author")
#    print(res)
#    assert res == ({'author': ['John Doe', 'et al', 'Jane Doe']}, "")

    res = fixer.classify_names("John Doe, This is not a valid name.", "~author")
    print(res)
    assert res == ({'author': ['John Doe']}, ', This is not a valid name.')

    res = fixer.classify_names("This is not a valid name, John Doe", "~author")
    print(res)
    assert res == None

    # Explicit labels apply unconditionally to the first name and then to each valid name afterwards
#    res = fixer.classify_names("edited by This is not a valid name, John Doe", "~author")
#    print(res)
#    assert res == ({'editor': ['This is not a valid name', 'John Doe']}, "")

    # Explicit labels apply unconditionally to the first name and then to each valid name afterwards
#    res = fixer.classify_names("edited by This is not a valid name, John Doe, Also not valid", "~author")
#    print(res)
#    assert res == ({'editor': ['This is not a valid name', 'John Doe']}, "Also not valid")


    # Explicit labels apply unconditionally to the first name and then to each valid name afterwards
#    res = fixer.classify_names("edited by John Doe, This is not a valid name", "~author")
#    print(res)
#    assert res == ({'editor': ['John Doe']}, 'This is not a valid name')

    # Retroactively labelled names must all pass validation
    res = fixer.classify_names("Jane Doe, John Doe (editors)", "~author")
    print(res)
    assert res == ({'editor': ['Jane Doe', 'John Doe']}, "")

    # Retroactively labelled names must all pass validation
    res = fixer.classify_names("This is not a valid name, John Doe (editors)", "~author")
    print(res)
    assert res == None

    res = fixer.classify_names('{{w|Y Beibl cyssegr-lan}}, Genesis 28:15:', "~author")
    print(res)
    assert res == None

    # parse et al and variations
#    res = fixer.classify_names("Jane Doe et al.", "~author")
#    assert res == ({'author': ['Jane Doe', 'et al']}, '')#
#    res = fixer.classify_names("Jane Doe, et al.", "~author")
#    assert res == ({'author': ['Jane Doe', 'et al']}, '')
#    res = fixer.classify_names("Jane Doe, et alii, invalid-name", "~author")
#    assert res == ({'author': ['Jane Doe', 'et al']}, 'invalid-name')

    # Invalid name followed by et al gets restored properly
    res = fixer.classify_names("Jane Doe, invalid-name, et alii, another-invalid-name", "~author")
    assert res == ({'author': ['Jane Doe']}, ', invalid-name, et alii, another-invalid-name')

#    res = fixer.classify_names("Jane Doe, et alii", "~author")
#    assert res == ({'author': ['Jane Doe', 'et al']}, '')

#    res = fixer.classify_names("Jane Doe, et alias", "~author")
#    print(res)
#    assert res == ({'author': ['Jane Doe']}, ' et alias')

#    res = fixer.classify_names("Jane Doe, & al.", "~author")
#    assert res == ({'author': ['Jane Doe', 'et al']}, '')
#    res = fixer.classify_names("Jane Doe, [[et al]].", "~author")
#    assert res == ({'author': ['Jane Doe', 'et al']}, '')


    res = fixer.classify_names("Judith Lynn Sebesta (editor and translator), Jeffrey M. Duban (translator)", "~author")
    assert res == None

    res = fixer.classify_names("Dr. John Smith", "~author")
    assert res == ({'author': ['Dr. John Smith']}, '')


    res = fixer.classify_names("John Gaspar Scheuchzer translating Engelbert Kaempfer", "~author")
    assert res == ({'translator': ['John Gaspar Scheuchzer'], 'author': ['Engelbert Kaempfer']}, '')
    res = fixer.classify_names("John Gaspar Scheuchzer translating Engelbert Kaempfer's", "~author")
    assert res == None


    # If this name is not in allowed names, it will split on the comma
    text = "Smith Wilkins, Mary Jane"
    assert text.lower() not in fixer.allowed_names
    res = fixer.classify_names(text, "~author")
    assert res == ({'author': ['Smith Wilkins', 'Mary Jane']}, '')

    # But if it is in allowed names, it should pass through exactly
    fixer.allowed_names.add(text.lower())
    res = fixer.classify_names(text, "~author")
    print(res)
    assert res == ({'author': ['Smith Wilkins, Mary Jane']}, '')


    # if splitting on secondary "and" fails, fail the entire primary section
    res = fixer.classify_names("Connie Green, Religious Diversity and Children's Literature", "~author")
    assert res == ({'author': ['Connie Green']}, "Religious Diversity and Children's Literature")


def test_links_to_text():
    assert fixer.links_to_text("abc {{w|foo}} def") == "abc foo def"
    assert fixer.links_to_text("abc {{w|foo|bar}} def") == "abc bar def"
    assert fixer.links_to_text("abc [[w:foo]]") == "abc foo"
    assert fixer.links_to_text("[[w:foo|bar]] def") == "bar def"
    assert fixer.links_to_text("[[:w:foo]]") == "foo"
    assert fixer.links_to_text("abc [[:w:foo|bar]] def") == "abc bar def"
