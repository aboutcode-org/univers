#
# Copyright (c) 2015 SAS Institute, Inc
#

"""
Versioning of artifacts
"""

import itertools

from .errors import RestrictionParseError
from .errors import VersionRangeParseError


EXCLUSIVE_CLOSE = ')'
EXCLUSIVE_OPEN = '('
INCLUSIVE_CLOSE = ']'
INCLUSIVE_OPEN = '['

# Known qualifiers, oldest to newest
QUALIFIERS = ["alpha", "beta", "milestone", "rc", "snapshot", "", "sp"]

# Well defined aliases
ALIASES = {
    "ga": "",
    "final": "",
    "cr": "rc",
}


class Restriction(object):
    """Describes a restriction in versioning
    """
    def __init__(self, lower_bound, lower_bound_inclusive, upper_bound,
                 upper_bound_inclusive):
        """Create a restriction

        :param lower_bound: the lowest version acceptable
        :type lower_bound: artifactory.versioning.Version
        :param lower_bound_inclusive: restriction includes the lower bound
        :type lower_bound_inclusive: bool
        :param upper_bound: the highest version acceptable
        :type upper_bound: artifactory.versioning.Version
        :param upper_bound_inclusive: restriction includes the upper bound
        :type upper_bound_inclusive: bool
        """
        self.lower_bound = lower_bound
        self.lower_bound_inclusive = lower_bound_inclusive
        self.upper_bound = upper_bound
        self.upper_bound_inclusive = upper_bound_inclusive

    def __contains__(self, version):
        """Return true if version is contained within the restriction

        version must be greater than the lower bound (or equal to it if the
        lower bound is inclusive) and less than the upper bount ( or equal to it
        if the upper bound is inclusive).
        """
        if self.lower_bound:
            if self.lower_bound == version and not self.lower_bound_inclusive:
                return False

            if self.lower_bound > version:
                return False

        if self.upper_bound:
            if self.upper_bound == version and not self.upper_bound_inclusive:
                return False

            if self.upper_bound < version:
                return False

        return True

    def __lt__(self, other):
        if self is other:
            return False

        if not isinstance(other, Restriction):
            return False

        if self.lower_bound < other.lower_bound:
            return True

        if self.lower_bound_inclusive < other.lower_bound_inclusive:
            return True

        if self.upper_bound < other.upper_bound:
            return True

        if self.upper_bound_inclusive < other.upper_bound_inclusive:
            return True

        return False

    def __ne__(self, other):
        return self < other or other < self

    def __eq__(self, other):
        return not self != other

    def __gt__(self, other):
        return other < self

    def __ge__(self, other):
        return not (self < other)

    def __le__(self, other):
        return not (self > other)

    def __hash__(self):
        result = 13
        if self.lower_bound:
            result += hash(self.lower_bound)
        else:
            result += 1

        result *= 1 if self.lower_bound_inclusive else 2

        if self.upper_bound:
            result -= hash(self.upper_bound)
        else:
            result -= 3

        result += 2 if self.upper_bound_inclusive else 3

        return result

    def __str__(self):
        s = ""
        s += '[' if self.lower_bound_inclusive else '('
        if self.lower_bound:
            s += str(self.lower_bound)
        s += ','

        if self.upper_bound:
            s += str(self.upper_bound)
        s += ']' if self.lower_bound_inclusive else ')'

        return s

    def __repr__(self):
        return "<%s.%s(%r, %r, %r, %r)>" % (
            self.__module__,
            "Restriction",
            self.lower_bound,
            self.lower_bound_inclusive,
            self.upper_bound,
            self.upper_bound_inclusive,
            )

    @staticmethod
    def fromstring(spec):
        """Generate a Restriction from a string
        """
        lower_bound_inclusive = spec[0] == INCLUSIVE_OPEN
        upper_bound_inclusive = spec[-1] == INCLUSIVE_CLOSE

        _spec = spec[1:-1].strip()
        if ',' in _spec:
            lower_bound, upper_bound = _spec.split(',')
            if lower_bound == upper_bound:
                raise RestrictionParseError(
                    "Range cannot have identical boundaries: %s" % spec)

            lower_version = Version(lower_bound) if lower_bound else None
            upper_version = Version(upper_bound) if upper_bound else None

            if lower_version and upper_version and upper_version < lower_version:
                raise RestrictionParseError(
                    "Range defies version ordering: %s" % spec)

            restriction = Restriction(lower_version, lower_bound_inclusive,
                                      upper_version, upper_bound_inclusive)
        else:
            # single version restriction
            if not lower_bound_inclusive or not upper_bound_inclusive:
                raise RestrictionParseError(
                    "Single version must be surrounded by []: %s"
                                   % spec)
            version = Version(_spec)
            restriction = Restriction(version, lower_bound_inclusive,
                                      version, upper_bound_inclusive)

        return restriction


class VersionRange(object):
    """Version range specification

    Valid ranges are comma separated range specifications
    """
    def __init__(self, version, restrictions):
        self.version = version
        self.restrictions = restrictions

    def __contains__(self, version):
        return any((version in r) for r in self.restrictions)

    def __lt__(self, other):
        if self is other:
            return False

        if not isinstance(other, VersionRange):
            return False

        return (
            self.version < other.version
            and self.restrictions < other.restrictions
            )

    def __ne__(self, other):
        return self < other or other < self

    def __eq__(self, other):
        return not self != other

    def __gt__(self, other):
        return other < self

    def __ge__(self, other):
        return not (self < other)

    def __le__(self, other):
        return not (self > other)

    def __hash__(self):
        result = 7
        result = 31 * result + (hash(self.version) if self.version else 0)
        result = 31 * result + (hash(self.restrictions) if self.restrictions
                                else 0)
        return result

    def __str__(self):
        if self.version:
            return str(self.version)
        else:
            return ','.join(str(r) for r in self.restrictions)

    def __repr__(self):
        return "<%s.%s(%r, %r)>" % (self.__module__, "VersionRange",
                                    self.version, self.restrictions)

    def _intersection(self, l1, l2):
        """Return the intersection of l1 and l2

        :param l1 list of restrictions
        :type l1 [Restriction, ...]
        :param l2 list of restrictions
        :type l2 [Restriction, ...]
        :return Intersection of l1 and l2
        :rtype [Restriction, ...]
        """
        raise NotImplementedError

    @staticmethod
    def fromstring(spec):
        """Create a VersionRange from a string specification

        :param spec string representation of a version or version range
        :type spec str
        :return a new VersionRange
        :rtype VersionRange
        :raises RuntimeError if the range is invalid in some way
        """
        if not spec:
            return None
        _spec = spec[:]

        restrictions = []
        version = None
        lower_bound = None
        upper_bound = None
        while (_spec.startswith(EXCLUSIVE_OPEN)
               or _spec.startswith(INCLUSIVE_OPEN)):
            exclusive_close = _spec.find(EXCLUSIVE_CLOSE)
            inclusive_close = _spec.find(INCLUSIVE_CLOSE)

            close = inclusive_close
            if inclusive_close < 0 or 0 <= exclusive_close < inclusive_close:
                # close is exclusive
                close = exclusive_close

            if close < 0:
                raise VersionRangeParseError("Unbounded range: %s" % spec)

            restriction = Restriction.fromstring(_spec[0:close+1])

            if lower_bound is None:
                lower_bound = restriction.lower_bound

            if upper_bound is not None:
                if restriction.lower_bound is None \
                        or restriction.lower_bound < upper_bound:
                    raise VersionRangeParseError("Ranges overlap: %s" % spec)
            restrictions.append(restriction)
            upper_bound = restriction.upper_bound

            _spec = _spec[close+1:]
            if _spec and _spec.startswith(','):
                # pop off leading comma
                _spec = _spec[1:]

        if _spec:
            if restrictions:
                raise VersionRangeParseError(
                    "Only fully-qualified sets allowed in multiple set"
                    " scenario: %s" % spec)
            else:
                version = Version(_spec)
                # add the "everything" restriction
                restrictions.append(Restriction(None, False, None, False))

        return VersionRange(version, restrictions)

    @staticmethod
    def from_version(version):
        return VersionRange(version, [])

    def restrict(self, version_range):
        """Retruns a new VersionRange that is a restriction of this
        and the specified version range.

        Prefers this version over the specified version range

        :param version_range the version range that will restrict this range
        :type version_range VersionRange
        :return intersection of this version range and the specified one
        :rypte VersionRange
        """
        raise NotImplementedError

    def match_version(self, versions):
        matched = None
        for version in sorted(versions, reverse=True):
            if version in self:
                matched = version
                break
        return matched


class Version(object):
    """Maven version objecjt
    """
    def __init__(self, version):
        self._unparsed = None
        self._parsed = None
        self.fromstring(version)

    def __cmp__(self, other):
        if self is other:
            return 0

        if not isinstance(other, Version):
            return 1

        return self._compare(self._parsed, other._parsed)

    def __hash__(self):
        result = 1229
        result = 1223 * result + self.major
        result = 1223 * result + self.minor
        result = 1223 * result + self.tiny
        result = 1223 * result + self.build

        if self.qualifier:
            result = 1223 * result + hash(self.qualifier)

        return result

    def __repr__(self):
        return "<%s.%s(%r)>" % (self.__module__, "Version", self._unparsed)

    def __str__(self):
        return self._unparsed

    def _compare(self, this, other):
        if isinstance(this, int):
            return self._int_compare(this, other)
        elif isinstance(this, str):
            return self._string_compare(this, other)
        elif isinstance(this, list):
            return self._list_compare(this, other)
        else:
            raise RuntimeError("Unkown type for t: %r" % this)

    def _int_compare(self, this, other):
        if isinstance(other, int):
            return this - other
        elif isinstance(other, (str, list)):
            return 1
        elif other is None:
            return this
        else:
            raise RuntimeError("other is of invalid type: %s" % type(other))

    def _list_compare(self, l, other):
        if other is None:
            if len(l) == 0:
                return 0
            return self._compare(l[0], other)
        if isinstance(other, int):
            return -1
        elif isinstance(other, str):
            return 1
        elif isinstance(other, list):
            for left, right in itertools.izip_longest(l, other):
                if left is None:
                    if right is None:
                        result = 0
                    else:
                        result = -1 * self._compare(right, left)
                else:
                    result = self._compare(left, right)
                if result != 0:
                    return result
            else:
                return 0
        else:
            raise RuntimeError("other is of invalid type: %s" % type(other))

    def _new_list(self, l):
        """Create a new sublist, append it to the current list and return the
        sublist

        :param list l: list to add a sublist to
        :return: the sublist
        :rtype: list
        """
        l = self._normalize(l)
        sublist = []
        l.append(sublist)
        return sublist

    def _normalize(self, l):
        for item in l[::-1]:
            if not item:
                l.remove(item)
            elif not isinstance(item, list):
                break
        return l

    def _string_compare(self, s, other):
        """Compare string item `s` to `other`

        :param str s: string item to compare
        :param other: other item to compare
        :type other: int, str, list or None
        """
        if other is None:
            return self._string_compare(s, "")

        if isinstance(other, (int, list)):
            return -1
        elif isinstance(other, str):
            s_value = self._string_value(s)
            other_value = self._string_value(other)
            if s_value < other_value:
                return -1
            elif s_value == other_value:
                return 0
            else:
                return 1
        else:
            raise RuntimeError("other is of invalid type: %s" % type(other))

    def _parse_buffer(self, buf, followed_by_digit=False):
        """Parse the string buf to determine if it is string or an int

        :param str buf: string to parse
        :param bool followed_by_digit: s is followed by a digit, eg. 'a1'
        :return: integer or string value of buf
        :rtype: int or str
        """
        if buf.isdigit():
            buf = int(buf)
        elif followed_by_digit and len(buf) == 1:
            if buf == 'a':
                buf = 'alpha'
            elif buf == 'b':
                buf = 'beta'
            elif buf == 'm':
                buf = 'milestone'

        return ALIASES.get(buf, buf)

    def _string_value(self, s):
        """Convert a string into a comparable value.

        If the string is a known qualifier, or an alias of a known qualifier,
        then return its index in the QUALIFIERS list. Otherwise return a string
        of the length of the QUALIFIERS list - s, eg. 7-foo

        :param str s: string to convert into value
        :return: value of string `s`
        :rtype: str
        """
        if s in QUALIFIERS:
            return str(QUALIFIERS.index(s) + 1)

        return "%d-%s" % (len(QUALIFIERS), s)

    def fromstring(self, version):
        """Parse a maven version

        The version string is examined one character at a time.

        There's a buffer containing the current text - all characters are
        appended, except for '.' and '-'. When it's stated 'append buffer to
        list', the buffer is first converted to an int if that's possible,
        otherwise left alone as a string. It will only be appended if it's
        length is not 0.

        * If a '.' is encountered, the current buffer is appended to the current
          list, either as a int (if it's a number) or a string.
        * If a '-' is encountered, do the same as when a '.' is encountered,
          then create a new sublist, append it to the current list and replace
          the current list with the new sub-list.
        * If the last character was a digit:
            * and the current one is too, append it to the buffer.
            * otherwise append the current buffer to the list, reset the buffer
              with the current char as content
        * if the last character was NOT a digit:
            * if the current character is also NOT a digit, append it to the
              buffer
            * if it is a digit, append buffer to list, set buffers content to
              the digit
        * finally, append the buffer to the list
        """
        self._unparsed = version
        self._parsed = current_list = []
        buf = str(version.strip()).lower()
        start = 0
        is_digit = False
        for idx, ch in enumerate(buf):
            if ch == '.':
                if idx == start:
                    current_list.append(0)
                else:
                    current_list.append(self._parse_buffer(buf[start:idx]))
                start = idx + 1
            elif ch == '-':
                if idx == start:
                    current_list.append(0)
                else:
                    current_list.append(self._parse_buffer(buf[start:idx]))
                start = idx + 1
                current_list = self._new_list(current_list)
            elif ch.isdigit():
                if not is_digit and idx > start:
                    current_list.append(self._parse_buffer(buf[start:idx], True))
                    current_list = self._new_list(current_list)
                    start = idx
                is_digit = True
            else:
                if is_digit and idx > start:
                    current_list.append(self._parse_buffer(buf[start:idx]))
                    current_list = self._new_list(current_list)
                    start = idx
                is_digit = False
        else:
            if len(buf) > start:
                current_list.append(self._parse_buffer(buf[start:]))
        current_list = self._normalize(current_list)
        self._parsed = self._normalize(self._parsed)
