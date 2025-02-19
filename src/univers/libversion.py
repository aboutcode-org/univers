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
METAORDER_ZERO = 1
METAORDER_NONZERO = 2
METAORDER_PRE_RELEASE = 3
METAORDER_POST_RELEASE = 4
METAORDER_LETTER_SUFFIX = 5
METAORDER_UPPER_BOUND = 6


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
    def parse_token_to_component(s):
        if s.isalpha():
            keyword_type = LibversionVersion.classify_keyword(s)
            metaorder = METAORDER_PRE_RELEASE if keyword_type == KEYWORD_PRE_RELEASE else METAORDER_POST_RELEASE
            return s, metaorder
        else:
            s = s.lstrip("0")
            metaorder = METAORDER_ZERO if s == "" else METAORDER_NONZERO
            return s, metaorder

    @staticmethod
    def get_next_version_component(s):
        components = re.split(r"[^a-zA-Z0-9]+", s)
        for component in components:
            yield LibversionVersion.parse_token_to_component(component)

    def compare_components(self, other):
        max_len = max(len(self.components), len(other.components))

        for i in range(max_len):
            """
            Get current components or pad with zero
            """
            c1 = self.components[i] if i < len(self.components) else ("0", METAORDER_ZERO)
            c2 = other.components[i] if i < len(other.components) else ("0", METAORDER_ZERO)

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
                if c1[0].lower() < c2[0].lower():
                    return -1
                elif c1[0].lower() > c2[0].lower():
                    return 1
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