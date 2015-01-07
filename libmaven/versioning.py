"""
Versioning of artifacts
"""

EXCLUSIVE_CLOSE = ')'
EXCLUSIVE_OPEN = '('
INCLUSIVE_CLOSE = ']'
INCLUSIVE_OPEN = '['


class Restriction(object):
    """Describes a restriction in versioning
    """
    def __init__(self, lowerBound, lowerBoundInclusive, upperBound,
                 upperBoundInclusive):
        """Create a restriction

        @param lowerBound: the lowest version acceptable
        @type lowerBound: artifactory.versioning.Version
        @param lowerBoundInclusive: restriction includes the lower bound
        @type lowerBoundInclusive: bool
        @param upperBound: the highest version acceptable
        @type upperBound: artifactory.versioning.Version
        @param upperBoundInclusive: restriction includes the upper bound
        @type upperBoundInclusive: bool
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
        if this is other:
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
        return s < o or o < self

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

    def __ne__(self, other):
        return not (self == other)

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

        @param l1 list of restrictions
        @type l1 [Restriction, ...]
        @param l2 list of restrictions
        @type l2 [Restriction, ...]
        @return Intersection of l1 and l2
        @rtype [Restriction, ...]
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

        @param spec string representation of a version or version range
        @type spec str
        @return a new VersionRange
        @rtype VersionRange
        @raises RuntimeError if the range is invalid in some way
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

        @param versionRange the version range that will restrict this range
        @type versionRange VersionRange
        @return intersection of this version range and the specified one
        @rypte VersionRange
        """
        raise NotImplementedError

    def matchVersion(versions):
        mached = None
        for version in sorted(versions, reverse=True):
            if version in self:
                matched = version
                break
        return matched


class Version(object):
    """Maven version objecjt
    """
    def __init__(self, version):
        self.unparsed = version
        self.major = 0
        self.minor = 0
        self.tiny = 0
        self.qualifier = ''
        self.build = 0

        self.fromstring(version)

    def __lt__(self, other):
        return self.compareTo(other) < 0

    def __eq__(self, other):
        if self is other:
            return True

        if not isinstance(other, Version):
            return False

        return self.compareTo(other) == 0

    def __ne__(self, other):
        return not (self == other)

    def __le__(self, other):
        return self.compareTo(other) <= 0

    def __gt__(self, other):
        return self.compareTo(other) > 0

    def __ge__(self, other):
        return self.compareTo(other) >= 0

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
        return "<%s.%s(%r)>" % (self.__module__, "Version", self.unparsed)

    def __str__(self):
        return self.unparsed

    def compareTo(self, other):
        """Compare maven versions

        * numerical comparison of major version
        * numerical comparison of minor version
        * if revision does not exist, add ".0" for comparison purposes
        * numerical comparison of revision
        * if qualifier does not exist, it is newer than if it does
        * case-insensitive string comparison of qualifier
            * this ensures timestamps are correctly ordered, and SNAPSHOT is
              newer than an equivalent timestamp
            * this also ensures that beta comes after alpha, as does rc
        * if no qualifier, and build does not exist, add "-0" for comparison
          purposes
        * numerical comparison of build

        @param other: other version object to compare with
        @type other: Version
        @return: if this version is newer, a number greater than 0, else if this
            version is older, a number less than 0. 0 if the versions are the
            same
        @rtype: int
        """
        result = self.major - other.major
        if result == 0:
            result = self.minor - other.minor
        if result == 0:
            result = self.tiny - other.tiny
        if result == 0:
            if self.qualifier:
                if other.qualifier:
                    # if either qualifier starts with the other, the
                    # longer one is older
                    if (len(self.qualifier) > len(other.qualifier)
                            and qualifier.startswith(other.qualifier)):
                        result = -1
                    elif (len(self.qualifier) < len(other.qualifier)
                            and other.qualifier.startswith(self.qualifier)):
                        result = 1
                    else:
                        if self.qualifier.upper() < other.qualifier.upper():
                            result = -1
                        elif self.qualifier.upper() > other.query.upper():
                            result = 1
                else:
                    # other has no qualifier but we do, other is newer
                    result = -1
            elif other.qualifier:
                # other has a qualifier but we don't, we are newer
                result = 1
            else:
                # compare build
                result = self.build - other.build

        return result

    def fromstring(self, version):
        """Parse a maven version

        <major>.<minor>.<revision>[-<qualifier> | -<build>]

        if the version is not of this format, then the whole thing is considered
        a qualifier.
        """
        head, _, tail = version.partition('-')
        if tail:
            # we have a qualifier or build number
            if (len(tail) == 1 or not tail.startswith('0')):
                # tail may be a build number, try it and find out
                try:
                    self.build = int(tail)
                except ValueError:
                    # tail wasn't a build number
                    self.qualifier = tail
            else:
                # tail is a qualifier
                self.qualifier = tail

        badlyFormatted = False
        if not ('.' in head or head.startswith('0')):
            # may have only a major version
            try:
                self.major = int(head)
            except ValueError:
                badlyFormatted = True
        else:
            # parse head
            if '..' in head or head.startswith('.') or head.endswith('.'):
                badlyFormatted = True
            else:
                parts = head.split('.')
                try:
                    self.major = int(parts.pop(0))
                    if parts:
                        self.minor = int(parts.pop(0))
                    if parts:
                        self.tiny = int(parts.pop(0))
                    if parts:
                        badlyFormatted = True
                except ValueError:
                    badlyFormatted = True

            if badlyFormatted:
                self.major = 0
                self.minor = 0
                self.tiny = 0
                self.qualifier = version
                self.build = 0
