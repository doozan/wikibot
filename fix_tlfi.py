from autodooz.sectionparser import SectionParser, Section

def fr_add_tlfi(text, title, summary, options):

    if "==French==" not in text:
        return text

    if "{{R:TLFi" in text:
        return text

    entry = SectionParser(text, title)
    all_french = entry.filter_sections(matches=lambda x: x.title == "French", recursive=False)
    if not all_french:
        return text

    french = all_french[0]

    # If further reading section already exists, add link as first item
    all_further_reading = french.filter_sections(matches=lambda x: x.title == "Further reading")
    if all_further_reading:
        further_reading = all_further_reading[0]
        further_reading._lines.insert(0, "* {{R:TLFi}}")
        return str(entry)

    # Otherwise, create and insert or append the new section
    further_reading = Section(entry, 3, "References")
    further_reading._lines.append("* {{R:TLFi}}")

    anagrams = french.filter_sections(matches=lambda x: x.title == "Anagrams", recursive=False)
    if anagrams:
        target_pos = french._children.index_of(anagrams[0])
        french._children.insert(target_pos, anagrams)
    else:
        french._children.append(further_reading)

    return str(entry)
