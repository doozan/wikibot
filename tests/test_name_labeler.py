from autodooz.name_labeler import NameLabeler
fixer = NameLabeler(debug=True)


def notest_split_names():

    res = fixer.split_names("J.D. Doe, Jr., MD, John Doe, Dr. Jane Doe (translator), Ed One, Ed Two (eds.)")
    print(res)
    assert res == ['J.D. Doe, Jr., MD', 'John Doe', 'Dr. Jane Doe (translator)', 'Ed One', 'Ed Two (eds.)']

#    ([('J.D. Doe', ', '), (',', 'Jr.'), (', ,MD', ', '), (',', 'John Doe'), (', ', ','), ('Dr. Jane Doe (translator)', ', '), (',', 'Ed One'), (', ', ','), ('Ed Two (eds.)', '')], [])

    print(orig)
    assert orig == [('J.D. Doe', ',', 0), (' Jr.', ',', 1), (' MD', ',', 1), (' John Doe', ',', 1), (' Dr. Jane Doe (translator)', ',', 2), (' Ed One', ',', 3), (' Ed Two (eds.)', '', 4)]


    res, orig = fixer.split_names("John Doe, Jr. (author), Dr. Jane Doe (translator), Ed One, Ed Two (eds.)")
    print(res)
    assert res == ['John Doe, Jr. (author)', 'Dr. Jane Doe (translator)', 'Ed One', 'Ed Two (eds.)']
    print(orig)
    assert orig == [('John Doe', ',', 0), (' Jr. (author)', ',', 1), (' Dr. Jane Doe (translator)', ',', 1), (' Ed One', ',', 2), (' Ed Two (eds.)', '', 3)]


    res, orig = fixer.split_names("[[w:William F. Buckley, Jr. (author)|William F. Buckley]], John Doe, Jr., [[w:George Byron, 6th Baron Byron|Lord Byron]]")
    print(res)
    assert res == ['[[w:William F. Buckley, Jr. (author)|William F. Buckley]]', 'John Doe, Jr.', '[[w:George Byron, 6th Baron Byron|Lord Byron]]']
    print(orig)
    assert orig == [('[[w:William F. Buckley, Jr. (author)|William F. Buckley]]', ',', 0), (' John Doe', ',', 1), (' Jr.', ',', 2), (' [[w:George Byron, 6th Baron Byron|Lord Byron]]', '', 2)]

    text="Muhammad Khalid Masud et al - Dispensing Justice in Islam: Qadis and Their Judgements"
    res, orig = fixer.split_names(text)
    print(res)
    assert res == ['Muhammad Khalid Masud', 'et al', '- Dispensing Justice in Islam: Qadis', 'Their Judgements']
    print(orig)
    assert orig == [('[[w:William F. Buckley, Jr. (author)|William F. Buckley]]', ',', 0), (' John Doe', ',', 1), (' Jr.', ',', 2), (' [[w:George Byron, 6th Baron Byron|Lord Byron]]', '', 2)]


def test_classify_names():

    res = fixer.classify_names("John Doe, Jr., Jane Doe (translator), Ed One, Ed Two (eds.)", "~author")
    print(res)
    assert res == ({"author": ["John Doe, Jr."], "translator": ["Jane Doe"], "editor": ["Ed One", "Ed Two"]}, "")

    res = fixer.classify_names("translated by John Doe, Jr. and Jane Doe, Ed One (editor)", "~author")
    print(res)
    assert res == ({'translator': ['John Doe, Jr.', 'Jane Doe'], 'editor': ['Ed One']}, "")


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
    assert res == ({'author': ['John Doe']}, 'This is not a valid name.')

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
    assert res == ({'author': ['{{w|Y Beibl cyssegr-lan}}']}, 'Genesis 28:15:')

    # parse et al and variations
#    res = fixer.classify_names("Jane Doe et al.", "~author")
#    assert res == ({'author': ['Jane Doe', 'et al']}, '')#
#    res = fixer.classify_names("Jane Doe, et al.", "~author")
#    assert res == ({'author': ['Jane Doe', 'et al']}, '')
#    res = fixer.classify_names("Jane Doe, et alii, invalid-name", "~author")
#    assert res == ({'author': ['Jane Doe', 'et al']}, 'invalid-name')

    # Invalid name followed by et al gets restored properly
    res = fixer.classify_names("Jane Doe, invalid-name, et alii, another-invalid-name", "~author")
    assert res == ({'author': ['Jane Doe']}, 'invalid-name, et alii, another-invalid-name')

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


