#
# SPDX-License-Identifier: MIT
#
# Visit https://aboutcode.org and https://github.com/aboutcode-org/univers for support and download.

import re
from datetime import datetime
from datetime import timedelta
from datetime import timezone


class DatetimeVersion:
    """
    datetime version.

    The timestamp must be RFC3339-compliant, i.e., a subset of ISO8601, where the date AND time are always specified. Therefore, we cannot use an ISO-parser directly, but have to check for compliance with the RFC format via a regex.
    """

    VERSION_PATTERN = re.compile(
        r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
    )
    _TIME_TZ_RE = re.compile(
        r"^(?P<h>\d{2}):(?P<M>\d{2}):(?P<s>\d{2})(?:\.(?P<f>\d+))?(?P<tz>Z|[+-]\d{2}:\d{2})$"
    )

    def __init__(self, version):
        version = str(version).strip()
        if not self.is_valid(version):
            raise InvalidVersionError(version)

        # save the original
        self.original = version

        # normalize Z to +00:00 to make tz parsing uniform
        if version.endswith("Z"):
            version = version[:-1] + "+00:00"

        # split into date and time+tz parts
        date_part, time_tz_part = version.split("T", 1)

        # parse the date-only portion first using fromisoformat
        # (datetime.fromisoformat accepts date-only strings)
        try:
            dt = datetime.fromisoformat(date_part)
        except ValueError:
            raise InvalidVersionError(version)

        # parse time and timezone with regex
        m = self._TIME_TZ_RE.fullmatch(time_tz_part)
        if not m:
            raise InvalidVersionError(version)

        hour = int(m.group("h"))
        minute = int(m.group("M"))
        second = int(m.group("s"))
        frac = m.group("f") or ""
        # ensure microseconds length is exactly 6 (truncate or pad), because datetime requires that
        if frac:
            micro = int((frac[:6]).ljust(6, "0"))
        else:
            micro = 0

        leap_second = second == 60
        if leap_second:
            # we can't handle second=60, so we use 59 and add one second later
            second = 59

        tz_text = m.group("tz")
        sign = 1 if tz_text[0] == "+" else -1
        tzh = int(tz_text[1:3])
        tzm = int(tz_text[4:6])
        offset = sign * (tzh * 3600 + tzm * 60)
        tzinfo = timezone(timedelta(seconds=offset))

        # construct aware datetime for the exact instant
        dt = datetime(
            year=dt.year,
            month=dt.month,
            day=dt.day,
            hour=hour,
            minute=minute,
            second=second,
            microsecond=micro,
            tzinfo=tzinfo,
        )

        if leap_second:
            dt = dt + timedelta(seconds=1)

        # canonicalize to UTC for comparisons/hashing
        self.parsed_stamp = dt.astimezone(timezone.utc)

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
