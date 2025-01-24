import enwiktionary_sectionparser as sectionparser
import re

def fr_add_tlfi(text, title, summary, options):

    if "==French==" not in text:
        return text

    if "{{R:fr:TLFi" in text:
        return text

    if "{{R:TLFi" in text:
        new_text = re.sub("({{)R:TLFi\s*([|}])", r"\1R:fr:TLFi\2", text)
        if new_text != text:
            if summary is not None:
                summary.append("renamed {{R:TLFi}} to {{R:fr:TLFi}}")
            return new_text

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

    # Otherwise, create and insert or append the new section
    else:
        further_reading = sectionparser.Section(entry, 3, "References")

        # References should be inserted before Anagrams if it exists
        anagrams = french.filter_sections(matches="Anagrams", recursive=False)
        if anagrams:
            target_pos = french._children.index(anagrams[0])
            french._children.insert(target_pos, further_reading)
        else:
            french._children.append(further_reading)

    further_reading.content_wikilines.insert(0, "* {{R:fr:TLFi}}")

    if summary is not None:
        summary.append("French: added missing TLFi link")

    return str(entry)
