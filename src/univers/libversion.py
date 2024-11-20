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
            start = 0
            end = len(s)
            keyword_type = LibversionVersion.classify_keyword(s)

            if keyword_type == KEYWORD_PRE_RELEASE:
                metaorder = METAORDER_PRE_RELEASE
            elif keyword_type == KEYWORD_POST_RELEASE:
                metaorder = METAORDER_POST_RELEASE
            else:
                metaorder = METAORDER_PRE_RELEASE

            return s, start, end, metaorder
        else:
            s = s.lstrip("0")
            start = 0
            end = len(s)

            if start == end:
                metaorder = METAORDER_ZERO
            else:
                metaorder = METAORDER_NONZERO

            return s, start, end, metaorder

    @staticmethod
    def get_next_version_component(s):
        components = re.split(r"[^a-zA-Z0-9]+", s)

        for component in components:
            yield LibversionVersion.parse_token_to_component(component)

    def compare_components(self, other):
        min_len = min(len(self.components), len(other.components))

        for i in range(min_len):
            c1 = self.components[i]
            c2 = other.components[i]

            # Compare metaorder
            if c1[3] < c2[3]:
                return -1
            elif c1[3] > c2[3]:
                return 1

            # Compare if components are empty
            c1_is_empty = c1[1] == c1[2]
            c2_is_empty = c2[1] == c2[2]

            if c1_is_empty and c2_is_empty:
                return 0
            elif c1_is_empty:
                return -1
            elif c2_is_empty:
                return 1

            # Compare if components are alpha or numeric
            c1_is_alpha = c1[0][c1[1]].isalpha()
            c2_is_alpha = c2[0][c2[1]].isalpha()

            if c1_is_alpha and c2_is_alpha:
                if c1[0][c1[1]].lower() < c2[0][c2[1]].lower():
                    return -1
                elif c1[0][c1[1]].lower() > c2[0][c2[1]].lower():
                    return 1
            elif c1_is_alpha:
                return -1
            elif c2_is_alpha:
                return 1

            # Numeric comparison
            c1_value = int(c1[0][c1[1] : c1[2]])
            c2_value = int(c2[0][c2[1] : c2[2]])

            if c1_value < c2_value:
                return -1
            elif c1_value > c2_value:
                return 1

        # All components compared are equal, check for more components
        if len(self.components) < len(other.components):
            return -1
        elif len(self.components) > len(other.components):
            return 1
        else:
            return 0
