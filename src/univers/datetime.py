#
# SPDX-License-Identifier: MIT
#
# Visit https://aboutcode.org and https://github.com/aboutcode-org/univers for support and download.

import re

from dateutil.parser import isoparse


class DatetimeVersion:
    """
    datetime version.

    The timestamp must be RFC3339-compliant, i.e., a subset of ISO8601, where the date AND time are always specified. Therefore, we can use dateutil's ISO-parser but have to check for compliance with the RFC format first via a regex.
    """

    VERSION_PATTERN = re.compile(
        r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
    )

    def __init__(self, version):
        if not self.is_valid(version):
            raise InvalidVersionError(version)

        version = str(version).strip()
        self.original = version
        self.parsed_stamp = isoparse(version)

    def __eq__(self, other):
        return self.parsed_stamp == other.parsed_stamp

    def __lt__(self, other):
        return self.parsed_stamp < other.parsed_stamp

    def __le__(self, other):
        return self.parsed_stamp <= other.parsed_stamp

    def __gt__(self, other):
        return self.parsed_stamp > other.parsed_stamp

    def __ge__(self, other):
        return self.parsed_stamp >= other.parsed_stamp

    @classmethod
    def is_valid(cls, string):
        return cls.VERSION_PATTERN.match(string)


class InvalidVersionError(ValueError):
    pass
