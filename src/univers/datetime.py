#
# SPDX-License-Identifier: MIT
#
# Visit https://aboutcode.org and https://github.com/aboutcode-org/univers for support and download.

import re
from datetime import datetime
from datetime import timezone


class DatetimeVersion:
    """
    datetime version.

    The timestamp must be RFC3339-compliant, i.e., a subset of ISO8601, where the date AND time are always specified. Therefore, we cannot use an ISO-parser directly, but have to check for compliance with the RFC format via a regex.
    """

    VERSION_PATTERN = re.compile(
        r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
    )

    def __init__(self, version):
        version = str(version).strip()
        if not self.is_valid(version):
            raise InvalidVersionError(version)

        # fromisoformat doesn't accept the "Z" suffix prior to 3.11, so we normalize it:
        if version.endswith("Z"):
            version = version[:-1] + "+00:00"

        self.original = version
        self.parsed_stamp = datetime.fromisoformat(version).astimezone(timezone.utc)

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
        return bool(cls.VERSION_PATTERN.fullmatch(string))


class InvalidVersionError(ValueError):
    pass
