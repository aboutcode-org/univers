# SPDX-License-Identifier: Apache-2.0
#
# Visit https://aboutcode.org and https://github.com/aboutcode-org/univers for support and download.

import re


class IntdotVersion:
    """
    intdot version.

    The regex pattern for the intdot version is any number (>0) of integers separated by dots, followed by an arbitrary number of other characters, e.g., 1.2.3.5543, 123.234-prerelease, 1.2.3alpha
    """

    VERSION_PATTERN = r"^(\d+(\.\d+)*)(.*)$"

    def __init__(self, version):
        if not self.is_valid(version):
            raise InvalidVersionError(version)

        version = str(version).strip()
        self.original = version

    def __eq__(self, other):
        return self.original == other.original

    def __lt__(self, other):
        return self.__cmp__(other) < 0

    def __le__(self, other):
        return self.__cmp__(other) <= 0

    def __gt__(self, other):
        return self.__cmp__(other) > 0

    def __ge__(self, other):
        return self.__cmp__(other) >= 0

    @classmethod
    def is_valid(cls, string):
        return re.compile(IntdotVersion.VERSION_PATTERN).match(string)

    def extract_numeric_labels(self, version):
        """
        Check if the version matches the pattern; if it matches, extract the first group (identified by parentheses) which is the numeric part of the version
        """
        match = re.match(IntdotVersion.VERSION_PATTERN, version)

        if match:
            version_labels = match.group(1)
            return version_labels
        else:
            raise InvalidVersionError(version)

    def __cmp__(self, other):
        """
        Compare this version with ``other`` returning -1, 0, or 1 if the
        other version is larger, the same, or smaller than this
        one.
        """
        if isinstance(other, str):
            other = IntdotVersion(other)

        if not isinstance(other, IntdotVersion):
            raise InvalidVersionError

        if self.original == other.original:
            return 0

        lhlabels = self.extract_numeric_labels(self.original)
        rhlabels = self.extract_numeric_labels(other.original)

        if lhlabels == rhlabels:
            return 0

        lhsize = len(lhlabels)
        rhsize = len(rhlabels)

        if lhsize > rhsize:
            limit = lhsize
        else:
            limit = rhsize

        limit -= 1

        i = 0

        while i <= limit:
            try:
                lhs = lhlabels[i]
            except IndexError:
                lhs = 0

            try:
                rhs = rhlabels[i]
            except IndexError:
                rhs = 0

            i += 1

            if lhs == rhs:
                continue

            if int(lhs) > int(rhs):
                return 1
            if int(lhs) < int(rhs):
                return -1
        return 0


class InvalidVersionError(ValueError):
    pass
