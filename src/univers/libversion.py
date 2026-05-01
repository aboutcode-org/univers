# SPDX-License-Identifier: Apache-2.0
#
# Visit https://aboutcode.org and https://github.com/aboutcode-org/univers for support and download.

import re

PRE_RELEASE_KEYWORDS = ["alpha", "beta", "rc", "pre"]
POST_RELEASE_KEYWORDS = ["post", "patch", "pl", "errata"]

KEYWORD_UNKNOWN = 0
KEYWORD_PRE_RELEASE = 1
KEYWORD_POST_RELEASE = 2

METAORDER_LOWER_BOUND = 0
METAORDER_PRE_RELEASE = 1
METAORDER_ZERO = 2
METAORDER_POST_RELEASE = 3
METAORDER_NONZERO = 4
METAORDER_LETTER_SUFFIX = 5
METAORDER_UPPER_BOUND = 6

_TOKEN_RE = re.compile(r"[A-Za-z]+|[0-9]+")


class LibversionVersion:
    def __init__(self, version_string):
        self.version_string = version_string
        self.components = list(self.get_next_version_component(version_string))

    def __hash__(self):
        return hash(self.components)

    def __eq__(self, other):
        return self.compare_components(other) == 0

    def __lt__(self, other):
        return self.compare_components(other) < 0

    def __le__(self, other):
        return self.compare_components(other) <= 0

    def __gt__(self, other):
        return self.compare_components(other) > 0

    def __ge__(self, other):
        return self.compare_components(other) >= 0

    @staticmethod
    def classify_keyword(s):
        if s in PRE_RELEASE_KEYWORDS:
            return KEYWORD_PRE_RELEASE
        elif s in POST_RELEASE_KEYWORDS:
            return KEYWORD_POST_RELEASE
        else:
            return KEYWORD_UNKNOWN

    @staticmethod
    def get_next_version_component(s):
        tokens = list(_TOKEN_RE.finditer(s))
        token_count = len(tokens)
        parsed_tokens = []

        prev_end = None
        for token in tokens:
            start, end = token.span()
            delim_before = prev_end is not None and start > prev_end
            parsed_tokens.append(
                {
                    "value": token.group(0),
                    "is_alpha": token.group(0).isalpha(),
                    "delim_before": delim_before,
                    "start": start,
                    "end": end,
                }
            )
            prev_end = end

        for i, token in enumerate(parsed_tokens):
            next_token = parsed_tokens[i + 1] if i + 1 < token_count else None
            delim_after = next_token is not None and next_token["start"] > token["end"]

            if token["is_alpha"]:
                raw_value = token["value"]
                value = raw_value.lower()
                keyword_type = LibversionVersion.classify_keyword(value)

                is_letter_suffix = False
                if i > 0 and not token["delim_before"]:
                    prev_token = parsed_tokens[i - 1]
                    if not prev_token["is_alpha"]:
                        next_is_numeric_no_delim = (
                            next_token is not None
                            and not next_token["is_alpha"]
                            and not delim_after
                        )
                        if not next_is_numeric_no_delim:
                            is_letter_suffix = True

                if is_letter_suffix:
                    metaorder = METAORDER_LETTER_SUFFIX
                elif keyword_type == KEYWORD_POST_RELEASE:
                    metaorder = METAORDER_POST_RELEASE
                else:
                    metaorder = METAORDER_PRE_RELEASE

                yield value, metaorder
                continue

            value = token["value"].lstrip("0")
            metaorder = METAORDER_ZERO if value == "" else METAORDER_NONZERO
            yield value, metaorder

    def compare_components(self, other):
        max_len = max(len(self.components), len(other.components))

        for i in range(max_len):
            """
            Get current components or pad with zero
            """
            c1 = self.components[i] if i < len(self.components) else ("", METAORDER_ZERO)
            c2 = other.components[i] if i < len(other.components) else ("", METAORDER_ZERO)

            """
            Compare based on metaorder
            """
            if c1[1] < c2[1]:
                return -1
            elif c1[1] > c2[1]:
                return 1

            """
            Check based on empty components
            """
            c1_is_empty = c1[0] == ""
            c2_is_empty = c2[0] == ""

            if c1_is_empty and c2_is_empty:
                continue
            elif c1_is_empty:
                return -1
            elif c2_is_empty:
                return 1

            """
            Compare based on alphabet or numeric
            """ 
            c1_is_alpha = c1[0].isalpha()
            c2_is_alpha = c2[0].isalpha()

            if c1_is_alpha and c2_is_alpha:
                c1_letter = c1[0][0].lower() if c1[0] else ""
                c2_letter = c2[0][0].lower() if c2[0] else ""
                if c1_letter < c2_letter:
                    return -1
                elif c1_letter > c2_letter:
                    return 1
                continue
            elif c1_is_alpha:
                return -1
            elif c2_is_alpha:
                return 1

            """
            Compare based on numeric comparison
            """ 
            c1_value = int(c1[0]) if c1[0] else 0
            c2_value = int(c2[0]) if c2[0] else 0

            if c1_value < c2_value:
                return -1
            elif c1_value > c2_value:
                return 1

        return 0