import re
import sys

from autodooz.utils import nest_aware_split, nest_aware_resplit
from .names import *

allowed_lowercase_regex = r"^(" + "|".join(map(re.escape, allowed_lowercase_prefix)) + ")[A-Z]"

class NameLabeler():

    def __init__(self, allow_filename=None, debug=False):
        self.debug = debug
        self.state = {}
        self.stack = []

        self.allowed_names = set()
        if allow_filename:
            with open(allow_filename) as infile:
                self.allowed_names = {line.strip().lower() for line in infile if line.strip()}

    def dprint(self, *args, **kwargs):
        if self.debug:
            print(args, kwargs, file=sys.stderr)

    def is_allowed_lowercase_name(self, word):
        if word.lower() in allowed_lowercase_names:
            return True

        if re.match(allowed_lowercase_regex, word):
            return True

        return False

    @staticmethod
    def links_to_text(text):
        """ replaces '{{w|foo}}' with 'foo' and {{w|foo|bar}} with 'bar' """

        pattern = r"""(?x)
            (
                {{
                (w)\|
                (?P<params1>.*?)
                }}
            )
            |
            (
                \[\[
                (:)?
                (w|W|Wikipedia|s:[^|]*)[|:]
                (?P<params2>.*?)
                \]\]
            )
        """

        def replacer(m):
            param_string = m.group('params1') if m.group('params1') else m.group('params2')
            params = param_string.split("|")
            if len(params) == 1:
                return params[0].strip()
            elif len(params) == 2:
                return params[1].strip()
            else:
                return m.group(0)

        return re.sub(pattern, replacer, text)

        for start, alt_start, stop in [
            ("{{w|",  "{{", "}}"),
            ("[[w:",  "[[", "]]"),
            ("[[w|",  "[[", "]]"),
            ("[[W:",  "[[", "]]"),
            ("[[Wikipedia:",  "[[", "]]"),
            ("[[:w:", "[[", "]]"),
            ("[[s:Author:", "[[", "]]"),
            ]:

            if text.count(stop) != 1 or text.count(alt_start) != 1:
                continue

            try:
                start_pos = text.index(start)
                stop_pos = text.index(stop)
            except ValueError:
                continue

            if stop_pos < start_pos:
                continue

            params = text[start_pos+len(start):stop_pos].split("|")
            link_text =  params[0].strip() if len(params) == 1 else params[1].strip()
            text = text[:start_pos] + link_text + text[stop_pos+len(stop):]

        return text


    def is_valid_name(self, text, skip_case_checks=False):

        if not text:
            return False

        text = self.links_to_text(text)

        if text.lower() in self.allowed_names:
            self.dprint("allowed name", text)
            return True

        if len(text) < 5:
            self.dprint("disallowed name, too short", text)
            return False

        if text[0] in " ,.;:-" or text[-1] in " ,;:-":
            self.dprint("disallowed name, starts or ends with delimiter", text)
            return False

        if text.count("-") > 1:
            self.dprint("disallowed name, multiple hyphens", text)
            return False

        if text.count(",") > 1:
            self.dprint("disallowed name, multiple commas", text)
            return False

        if text.count('"') != text.count('"'):
            self.dprint("disallowed name, unbalanced quote", text)
            return False

        if text.count("(") != text.count(")"):
            self.dprint("disallowed name, unbalanced paren", text)
            return False

        if text.count("{{") != text.count("}}"):
            self.dprint("disallowed name, unbalanced curly brackets", text)
            return False

        if text.count("[") != text.count("]"):
            self.dprint("disallowed name, unbalanced square brackets", text)
            return False

        if text.count("[[") != text.count("]]"):
            self.dprint("disallowed name, unbalanced double square brackets", text)
            return False

        # Single word names must match allowlist
        words = [w for w in re.split(r"[,.\s]+", text) if w]
        if len(words) == 1:
            self.dprint("disallowed name, single word", text)
            return False

        # Four or more long names fails
        if len(list(word for word in words if len(word) > 3)) > 3:
            self.dprint("disallowed name, many words", text)
            return False

        if any(word.lower() in disallowed_name_words for word in words):
            self.dprint("disallowed name, disallowed name part", text)
            return False

        if any(word.endswith("'s") for word in words):
            self.dprint("disallowed name, ends 's", text)
            return False

        bad_items = [r'''[:ə"“”()<>\d]''', "''", r"\.com"]
        pattern = "(" +  "|".join(bad_items) + ")"
        if re.search(pattern, text):
            self.dprint("disallowed name, disallowed characters", text)
            return False


        if skip_case_checks:
            return True

        if any(len(word) in [2] and not word.isupper() and word.lower() not in allowed_short_name_words for word in words):
            self.dprint("disallowed name, short word not in allowlist", text)
            return False

        if any(re.match(r"[^A-Z]\[", word) for word in words):
            self.dprint("disallowed name, contains [ not preceeded by uppercase letter")
            return False

        # First word in name must be uppercase
        if not words[0][0].isupper():
            self.dprint("disallowed name, first name not uppercase", text)
            return False

        # Last word in name must be uppercase
        if not words[-1][0].isupper() and not self.is_allowed_lowercase_name(words[-1]):
            self.dprint("disallowed name, final name not uppercase", text)
            return False

        # All non-uppercase words must match allowlist
        for word in words:
            if word[0].islower() and not self.is_allowed_lowercase_name(word):
                self.dprint("disallowed name, lowercase name part", text)
                return False

        return True

    def split_names(self, text):

        """ Split text on name boundaries, with awareness of wiki templates, brackets, and special handling
        for variations of "et al"

        returns a list of (name, separator)
        """
        sep_options = [";", " -"]

        # if the text starts out "Last, First", don't split on commas
        if not re.match(r"\w+, \w+", text):
            sep_options.insert(0, ",")

        # Check for available separators
        for separator in sep_options:
            if separator in text:
                break

        # nest_aware_resplit only works predictably with a single capture group
        sep1_pattern = fr"\s*{separator}\s*"

        secondary_separators = [r"\s[/·&]\s", r"\band\b", r"\bwith\b"]
        sep2_pattern = "(" + "|".join(fr"\s*{x}\s*" for x in secondary_separators) + ")"

        suffix_pattern = r"""(?x)
            (?P<suffix>(M\.D\.|M\.D\.|senior|Jr|MD|PhD|MSW|JD|II|III|IV|Sr|esq)
                \.*
                (\s*\(.*?\))?             # include anything in parenthesis following the suffix as a label
                (\s*\[.*?\])?             # include anything in square brackets following the suffix as a label
            )
            (?P<sep>\s*)
            (?P<post>.*?)
            $
            """

        name_seps = []
        _parts = []
        for name, sep in nest_aware_resplit(sep1_pattern, text, [("{{","}}"), ("[","]"), ("(", ")")]):


        # TODO: Split on separator, then split on extra_separators
#        for name, sep in nest_aware_resplit(r"(\s+-\s+|\s*\bwith\b\s*|\s*&\s*|\s*\band\b\s*|\s*[" + sep_chars + r"]\s*)", text, [("{{","}}"), ("[","]"), ("(", ")")]):

            # Check for trailing comma
            m = re.search("(.*?)([, ]+)$", name)
            if m:
                name = m.group(1)
                sep = m.group(2) + sep

            has_et_al = False

            if not name.strip():
                continue


            m = re.match(suffix_pattern, name, re.IGNORECASE)
            if m:
                if not name_seps:
                    return []

                suffix = m.group('suffix')
                new_sep = m.group('sep')
                post = m.group('post')

                # TODO: if post starts with (, allow it to be part of the suffix

                # The suffix is only a suffix if it ends the string (no post text) or if it is followed
                # by a secondary separator
                # This lets us correctly match both "John Doe, M.D. and Jane Doe" and "John Doe, M.D. Jane Doe"

                prev_name, prev_sep = name_seps[-1]
                # End of list, just merge and finish
                if not post:
                    name_seps[-1] = (prev_name + prev_sep + suffix, new_sep + sep)
                    continue

                # If there's no separator, it's not a suffix (eg Sr. and Racha vs Sriracha)
                # suffix, separator, and trailing text, continue processing trailing text
                if sep and re.match(sep2_pattern, post):
                    name_seps[-1] = (prev_name + prev_sep + suffix, new_sep)
                    name = post

                # No separator or no trailing text, don't process as a suffix


            secondary_splits = list(nest_aware_resplit(sep2_pattern, name, [("{{","}}"), ("[","]"), ("(", ")")]))

            # Only split on secondary if both parts contain spaces
            # or if both parts don't contain spaces
            # to allow entries like "Jane and John Doe"
            if all(" " in n for n,s in secondary_splits if n) or all(" " not in n for n,s in secondary_splits):
                for name2, sep2 in secondary_splits:
                    if sep2 == "":
                        sep2 = sep
                    name_seps.append((name2, sep2))
            else:
                name_seps.append((name, sep))

            #_parts.append((orig_name,separator, len(names)))


#            # Detect and split "et al"
#            new_name = re.sub(r"(''|\b)(et\s+|&\s*)al(ii|\.)?('')?([., ]|$)", "<<<SPLIT>>>", name)
#            #new_name = re.sub(r"(''|\b)(et|&) al((ii|\.)''(.)?|[.,]|$)", "<<<SPLIT>>>", name)
#            if new_name == name:
#                self.dprint("NO MATCH", name)
#            name = new_name



#            for split_name in re.split("(<<<SPLIT>>>)", name):
#                if split_name == "<<<SPLIT>>>":
#                    names.append("et al")
#                else:
#                    split_name = split_name.strip()
#                    if split_name:
#                        names.append(split_name)

        return name_seps

    _classify_commands = {
        "(authors)": "<author",
        "(English author)": "!author",
        "(original author)": "!author",
        "(author)": "!author",
        "(aut.)": "!author",
        "(auth)": "!author",
        "(auth.)": "!author",

        "(translator)": "!translator",
        "(attributed translator)": "!translator",
        "(tr)": "!translator",
        "(tr.)": "!translator",
        "(tr)": "!translator",
        "(tr.)": "!translator",
        "(trans.)": "!translator",
        "(translation)": "!translator",
        "(transl)": "!translator",
        "(transl.)": "!translator",
        "(translators)": "<translator",
        "(trs)": "<translator",
        "(trs.)": "<translator",

        "(editors)": "<editor",
        "(translation editors)": "<editor",
        "(eds)": "<editor",
        "(eds.)": "<editor",
        "(editor)": "!editor",
        "(ed)": "!editor",
        "(Ed.)": "!editor",
        "(ed.)": "!editor",
        "(ed.)": "!editor",
        "(compiler)": "!editor",

        "(publisher)": "!publisher",
#        "(writer)": "!author",
#        "(lyrics)": "!author",
#        "(illustrator): "!illustrator",
#        "(illust.)": "!illustrator",


        "edited by": ">editor",
        "ed.": "!editor",
        "eds.": "<editor",
        "editors": "<editor",

        "translator": "!translator",
        "translators": "<translator",
        "translator:": ">translator",
        "translating": "<translator",
        "translated by": ">translator",
        "tr. by": ">translator",
        "trans. by": ">translator",
#        "trans.": ">translator",

#        "author": "!author", ?


    }
    # allow () and []
    _classify_commands |= { k.replace("(", "[").replace(")","]"):v for k,v in _classify_commands.items() }
    _classify_regex = "(" + "|".join(map(re.escape, _classify_commands)) + ")"


    def _run_command(self, command_line):

        """
        <CMD>[VALUE]

        CMD can be:
          ~ (unset _explicit. if value is provided, set _default to value)
          + (push value to stack)
          < (apply value to all stack items. unset _explicit)
          ! (apply value to top stack item. apply _default or _explicit to any remaining stack items. unset _explicit)
          > (apply _explicit or _default to everything on the stack. set _explicit to value)
          0 (apply _explicit or _default to everything on the stack. unset _explicit)
        """

        cmd = command_line[0]
        value = command_line[1:].strip()

        self.dprint("CMD", cmd, value, self.stack, self.state)

        # TODO: set validate_all=False to skip validation of first author name and explicitly labeled names
        def _label_items(items, label=None, validate_all=True):
            if not items:
                return True

            is_explicit=True
            if not label:
                if "__explicit" in self.state:
                    label = self.state.get("__explicit")
                    self.state["__explicit_used"] = True
                else:
                    label = self.state.get("__default")
                    is_explicit=False

            if not label:
                self.dprint("no _default or _explicit label available")
                return

            if label in self.state:
                self.dprint("duplicate label", label, items, self.state)


            allow_first = is_explicit and not validate_all

            while items and (allow_first or self.is_valid_name(items[0])):
                allow_first = False
                name = items.pop(0)
                if label not in self.state:
                    self.state[label] = []
                self.state[label].append(name)

            if items:
                label = "_invalid"
                if label not in self.state:
                    self.state[label] = []
                self.state[label] += items

            return True


        def _unset_explicit():
            if "__explicit" in self.state:
                if "__explicit_used" not in self.state:
                    self.dprint("Explicit value has not been not applied")
                    return
                del self.state["__explicit"]
                del self.state["__explicit_used"]
            return True

        def _set_default(value):
            self.state["__default"] = value
            return True

        def _set_explicit(value):
            if not _unset_explicit():
                return
            self.state["__explicit"] = value
            return True

        if cmd == "~":
            _unset_explicit()
            if value:
                _set_default(value)
            return True

        if cmd == "+":
            item = value
            self.stack.append(item)
            return True

        if cmd == "<":
            items = self.stack.copy()
            del self.stack[:]
            if not _label_items(items, value, validate_all=True):
                return
            _unset_explicit()
            return True

        if cmd == "!":
            if not self.stack:
                return
            items = [self.stack.pop()]

            if self.stack:
                stack_items = self.stack.copy()
                del self.stack[:]
                if not _label_items(stack_items):
                    return

            if not _label_items(items, value):
                return

            _unset_explicit()
            return True

        if cmd == ">":
            if self.stack:
                items = self.stack.copy()
                del self.stack[:]
                if not _label_items(items):
                    return

            _set_explicit(value)
            return True

        if cmd == "0":
            if self.stack:
                items = self.stack.copy()
                del self.stack[:]
                if not _label_items(items):
                    return
            _unset_explicit()
            return True

        raise ValueError("unhandled label command", command_line)


    def classify_names(self, text, init_command):

        """
        ["John Doe (author)", "Jane Doe (translator)", "Ed One", "Ed Two (eds.)"] => {"author": ["John Doe"], "translator": ["Jane Doe"], "editor": ["Ed One", "Ed Two"]}

        each "Name" gets pushed to a stack
        (label) acts as a command, the () are optional
        NOTE: "translating" is an alias for "translators"
        if label is singular, apply the label to last item on the stack and then apply "author" to all stack items
        if label is plural, apply the label to all items on the stack
        """

        self.state = {}
        self.stack = []


        # If the text matches a specifically allowed name, return that
        maybe_allowed, sep = re.match(r"(.*?)([,.;:\- ]*)$", text).groups()
        if maybe_allowed.lower() in self.allowed_names:
            name_seps = [(maybe_allowed, sep)]
            post_text = ""

        else:
            # If the text doesn't match an allowed name, only search names until the first "." divider
            # Break on ". " unless it's like J.D. or Mr.
            pattern = r"(.*)(?<![A-Z])(?<!Jr|Dr|Ms|Mr|Sr|et)(?<!Miss)(?<!Mrs|Sra|Sgt|Pvt|etc)(\.\s.*)"
            m = re.match(pattern, text)
            if m:
                text = m.group(1)
                post_text = m.group(2)
            else:
                post_text = ""

            name_seps = self.split_names(text)
            if not name_seps:
                return

        # Splits returns a list of (name, separator)
        # The name may be further split if it contains embedded commands
        # such like "edited by John Doe" would be split into "edited by", "john doe"
        #
        # If the token "john doe" generates an error, we want to be able to re-build
        # the original text starting from the name that generated an error
        #
        # In order to achieve this, all tokens passed to the VM are stored with the
        # correspoding index of name they came from. If a token is flagged as invalid
        # by the VM, we can then find the index of the name that failed, re-run
        # the VM with only the preceeding names, and then rebuild the "invalid_text"
        # from the following names and separators

        self.dprint("NAMES", name_seps)

        command_idxs = self._make_commands(name_seps, init_command)
        self._run_classifier(command_idxs)
        if not self.state or any(k.startswith("__") for k in self.state.keys()):
            return

        invalid = self.state.get("_invalid")
        if not invalid:
            return self.state, post_text

        self.dprint("INVALID TEXT FOUND, stripping and re-running")

        # If names were rejected as invalid,
        # re-generate the original text starting from the first invalid name
        found = False
        invalid_command = f"+{invalid[0]}"
        for command, idx in command_idxs:
            if command == invalid_command:
                found = True
                break
        if not found:
            raise ValueError(f"cannot find token in list", invalid_command, command_idxs)

        # If it failed on the first command, there's nothing to re-run
        if not idx:
            return


        prev_sep = name_seps[idx-1][1]
        name_seps[idx-1] = (name_seps[idx-1][0], "")

        invalid_text = prev_sep + "".join(sum(map(list, name_seps[idx:]), [])) + post_text
        print("INVALID", invalid_text, name_seps)

        # And re-run the processor with only the valid names
        command_idxs = self._make_commands(name_seps[:idx], init_command)
        self._run_classifier(command_idxs)
        if not self.state or any(k.startswith("__") for k in self.state.keys()):
            self.dprint("BAD VM STATE", self.state)
            return
        if "_invalid" in self.state:

            self.dprint("STILL INVALID")
            # TODO: We could try stripping a value each time until nothing or success
            return

            print("__")
            print([name_text])
            print(invalid_text)
            print(command_idxs)
            raise ValueError("still invalid after removing bad command at index", idx)

        return self.state, invalid_text


    def _make_commands(self, commands, init_command):

        # List of (name, names_idx)
        # Needed for mapping names that get split into names/commands
        # ie ["Name One", "Jane Doe translating John Doe"] will split into "Jane Doe", "!translator", "John Doe"
        # and pre_commands will contain [("Name One", 0), ("Jane Doe", 1), ("John Doe", 1)]
        pre_commands = [(init_command, None)] if init_command else []

        for idx, text_sep in enumerate(commands):
            text, _ = text_sep

            for token, alias in nest_aware_resplit(self._classify_regex, text, [("{{","}}"), ("[[","]]")], re.IGNORECASE):
                if token:
                    pre_commands.append(("+" + token.strip(), idx))

                if alias:
                    command = self._classify_commands[alias]
                    pre_commands.append((command, idx))

        return pre_commands


    def _run_classifier(self, command_idxs):
        self.state = {}
        self.stack = []

        for command, _ in command_idxs:
            if not self._run_command(command):
                return
            if "_invalid" in self.state:
                self.stack = []
                break

        if self.stack:
            if not self._run_command(f"0"):
                return

        if "__default" in self.state:
            del self.state["__default"]

        self.dprint("RUN COMPLETE", self.state)

