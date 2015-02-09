#
# Copyright (c) 2015 SAS Institute, Inc
#

"""
Versioning of artifacts
"""

import itertools


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
    def __init__(self, lowerBound, lowerBoundInclusive, upperBound,
                 upperBoundInclusive):
        """Create a restriction

        :param lowerBound: the lowest version acceptable
        :type lowerBound: artifactory.versioning.Version
        :param lowerBoundInclusive: restriction includes the lower bound
        :type lowerBoundInclusive: bool
        :param upperBound: the highest version acceptable
        :type upperBound: artifactory.versioning.Version
        :param upperBoundInclusive: restriction includes the upper bound
        :type upperBoundInclusive: bool
        """
        self.lowerBound = lowerBound
        self.lowerBoundInclusive = lowerBoundInclusive
        self.upperBound = upperBound
        self.upperBoundInclusive = upperBoundInclusive

    def __contains__(self, version):
        """Return true if version is contained within the restriction

        version must be greater than the lower bound (or equal to it if the
        lower bound is inclusive) and less than the upper bount ( or equal to it
        if the upper bound is inclusive).
        """
        if self.lowerBound:
            if self.lowerBound == version and not self.lowerBoundInclusive:
                return False

            if self.lowerBound > version:
                return False

        if self.upperBound:
            if self.upperBound == version and not self.upperBoundInclusive:
                return False

            if self.upperBound < version:
                return False

        return True

    def __lt__(self, other):
        if self is other:
            return False

        if not isinstance(other, Restriction):
            return False

        return (
            self.lowerBound < other.lowerBound
            or self.lowerBoundInclusive < other.lowerBoundInclusive
            or self.upperBound < other.upperBound
            or self.upperBoundInclusive < other.lowerBoundInclusive
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
        result = 13
        if self.lowerBound:
            result += hash(self.lowerBound)
        else:
            result += 1

        result *= 1 if self.lowerBoundInclusive else 2

        if self.upperBound:
            result -= hash(self.upperBound)
        else:
            result -= 3

        result += 2 if self.upperBoundInclusive else 3

        return result

    def __str__(self):
        s = ""
        s += '[' if self.lowerBoundInclusive else '('
        if self.lowerBound:
            s += str(self.lowerBound)
        s += ','

        if self.upperBound:
            s += str(self.upperBound)
        s += ']' if self.lowerBoundInclusive else ')'

        return s

    def __repr__(self):
        return "<%s.%s(%r, %r, %r, %r)>" % (
            self.__module__,
            "Restriction",
            self.lowerBound,
            self.lowerBoundInclusive,
            self.upperBound,
            self.upperBoundInclusive,
            )


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
    def _parseRestriction(spec):
        lowerBoundInclusive = spec.startswith('[')
        upperBoundInclusive = spec.endswith(']')

        _spec = spec[1:-1].strip()
        comma = _spec.find(',')
        if comma < 0:
            # single version restriction
            if not lowerBoundInclusive or not upperBoundInclusive:
                raise RuntimeError("Single version must be surrounded by []: %s"
                                   % spec)
            version = Version(_spec)
            restriction = Restriction(version, lowerBoundInclusive,
                                      version, upperBoundInclusive)
        else:
            lowerBound = _spec[:comma].strip()
            upperBound = _spec[comma+1:].strip()
            if lowerBound == upperBound:
                raise RuntimeError("Range cannot have identical boundaries: %s"
                                   % spec)
            lowerVersion = Version(lowerBound) if lowerBound else None
            upperVersion = Version(upperBound) if upperBound else None

            if lowerBound and upperBound and upperBound < lowerBound:
                raise RuntimeError("Range defies version ordering: %s" % spec)

            restriction = Restriction(lowerVersion, lowerBoundInclusive,
                                      upperVersion, upperBoundInclusive)

        return restriction

    def clone(self):
        restrictions = self.restrictions[:] if self.restrictions else []
        return VersionRange(self.version, restrictions)

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
        lowerBound = None
        upperBound = None
        while (_spec.startswith(EXCLUSIVE_OPEN)
               or _spec.startswith(INCLUSIVE_OPEN)):
            exclusiveClose = _spec.find(EXCLUSIVE_CLOSE)
            inclusiveClose = _spec.find(INCLUSIVE_CLOSE)

            close = inclusiveClose
            if inclusiveClose < 0 or exclusiveClose < inclusiveClose:
                # close is exclusive
                close = exclusiveClose

            if close < 0:
                raise RuntimeError("Unbounded range: %s" % spec)

            restriction = VersionRange._parseRestriction(_spec[0:close+1])

            if lowerBound is None:
                lowerBound = restriction.lowerBound

            if upperBound is not None:
                if restriction.lowerBound is None \
                        or restriction.lowerBound < upperBound:
                    raise RuntimeError("Ranges overlap: %s" % spec)
            restrictions.append(restriction)
            upperBound = restriction.upperBound

            _spec = _spec[close+1:]
            if _spec and _spec.startswith(','):
                # pop off leading comma
                _spec = _spec[1:]

        if _spec:
            if restrictions:
                raise RuntimeError("Only fully-qualified sets allowed in"
                                   " multiple set scenario: %s" % spec)
        else:
            version = Version(_spec)
            # add the "everything" restriction
            restrictions.add(Restriction(None, False, None, False))

        return Version(version, restrictions)

    @staticmethod
    def fromVersion(version):
        return VersionRange(version, [])

    def restrict(self, versionRange):
        """Retruns a new VersionRange that is a restriction of this
        and the specified version range.

        Prefers this version over the specified version range

        :param versionRange the version range that will restrict this range
        :type versionRange VersionRange
        :return intersection of this version range and the specified one
        :rypte VersionRange
        """
        raise NotImplementedError

    def matchVersion(self, versions):
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
        return self.unparsed

    def _compare(self, this, other):
        if isinstance(this, int):
            return self._intCompare(this, other)
        elif isinstance(this, str):
            return self._stringCompare(this, other)
        elif isinstance(this, list):
            return self._listCompare(this, other)
        else:
            raise RuntimeError("Unkown type for t: %r" % this)

    def _intCompare(self, this, other):
        if isinstance(other, int):
            return this - other
        elif isinstance(other, (str, list)):
            return 1
        elif other is None:
            return this
        else:
            raise RuntimeError("other is of invalid type: %s" % type(other))

    def _listCompare(self, l, other):
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

    def _newList(self, l):
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

    def _stringCompare(self, s, other):
        """Compare string item `s` to `other`

        :param str s: string item to compare
        :param other: other item to compare
        :type other: int, str, list or None
        """
        if other is None:
            return self._stringCompare(s, "")

        if isinstance(other, (int, list)):
            return -1
        elif isinstance(other, str):
            sValue = self._stringValue(s)
            otherValue = self._stringValue(other)
            if sValue < otherValue:
                return -1
            elif sValue == otherValue:
                return 0
            else:
                return 1
        else:
            raise RuntimeError("other is of invalid type: %s" % type(other))

    def _parseBuffer(self, buf, followedByDigit=False):
        """Parse the string buf to determine if it is string or an int

        :param str buf: string to parse
        :param bool followedByDigit: s is followed by a digit, eg. 'a1'
        :return: integer or string value of buf
        :rtype: int or str
        """
        if buf.isdigit():
            buf = int(buf)
        elif followedByDigit and len(buf) == 1:
            if buf == 'a':
                buf = 'alpha'
            elif buf == 'b':
                buf = 'beta'
            elif buf == 'm':
                buf = 'milestone'

        return ALIASES.get(buf, buf)

    def _stringValue(self, s):
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
        self._parsed = currentList = []
        buf = version.lower()
        start = 0
        isDigit = False
        for idx, ch in enumerate(buf):
            if ch == '.':
                if idx == start:
                    currentList.append(0)
                else:
                    currentList.append(self._parseBuffer(buf[start:idx]))
                start = idx + 1
            elif ch == '-':
                if idx == start:
                    currentList.append(0)
                else:
                    currentList.append(self._parseBuffer(buf[start:idx]))
                start = idx + 1
                currentList = self._newList(currentList)
            elif ch.isdigit():
                if not isDigit and idx > start:
                    currentList.append(self._parseBuffer(buf[start:idx], True))
                    currentList = self._newList(currentList)
                    start = idx
                isDigit = True
            else:
                if isDigit and idx > start:
                    currentList.append(self._parseBuffer(buf[start:idx]))
                    currentList = self._newList(currentList)
                    start = idx
                isDigit = False
        else:
            if len(buf) > start:
                currentList.append(self._parseBuffer(buf[start:]))
        currentList = self._normalize(currentList)
        self._parsed = self._normalize(self._parsed)
