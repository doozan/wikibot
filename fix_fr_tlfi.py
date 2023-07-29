import enwiktionary_sectionparser as sectionparser

def fr_add_tlfi(text, title, summary, options):

    if "==French==" not in text:
        return text

    if "{{R:fr:TLFi" in text or "{{R:TLFi" in text:
        return text

    entry = sectionparser.parse(text, title)
    if not entry:
        return text

    all_french = entry.filter_sections(matches="French", recursive=False)
    if not all_french:
        return text

    french = all_french[0]

    # If further reading section already exists, add link as first item
    all_further_reading = french.filter_sections(matches="Further reading")
    if all_further_reading:
        further_reading = all_further_reading[0]
        further_reading.content_wikilines.insert(0, "* {{R:fr:TLFi}}")

    # Otherwise, create and insert or append the new section
    else:
        further_reading = sectionparser.Section(entry, 3, "References")
        further_reading.content_wikilines.append("* {{R:fr:TLFi}}")

        anagrams = french.filter_sections(matches="Anagrams", recursive=False)
        if anagrams:
            target_pos = french._children.index_of(anagrams[0])
            french._children.insert(target_pos, anagrams)
        else:
            french._children.append(further_reading)

    if summary is not None:
        summary.append("French: added missing TLFi link")

    return str(entry)
