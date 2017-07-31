import re

from six import iterkeys, itervalues
from typing import Callable, Sequence, MutableSequence

from puppeter.domain import default


class GemVersion:
    VERSION_PATTERN = '[0-9]+(?:\.[0-9a-zA-Z]+)*(-[0-9A-Za-z-]+(\.[0-9A-Za-z-]+)*)?'
    ANCHORED_VERSION_PATTERN = re.compile('^\s*({VERSION_PATTERN})?\s*$'.format(VERSION_PATTERN=VERSION_PATTERN))

    def __init__(self, version):
        # If version is an empty string convert it to 0
        version = 0 if re.compile('^\s*$').match(str(version)) else version

        self.__version = str(version).strip().replace('-', '.pre.')
        self.__segments = None
        self.__bump = None
        self.__release = None

    def bump(self):
        if not self.__bump:
            segments = self.segments()
            while any(map(lambda s: isinstance(s, str), segments)):
                segments.pop()
            if len(segments) > 1:
                segments.pop()
            segments[-1] = segments[-1] + 1
            segments = list(map(lambda r: str(r), segments))
            self.__bump = GemVersion('.'.join(segments))

        return self.__bump

    def release(self):
        if not self.__release:
            segments = self.segments()
            while any(map(lambda s: isinstance(s, str), segments)):
                segments.pop()
            segments = list(map(lambda r: str(r), segments))
            self.__release = GemVersion('.'.join(segments))

        return self.__release

    def segments(self):
        # type: () -> MutableSequence[int|str]
        return list(self.__get_segments())

    def __cmp__(self, other):
        # type: (GemVersion) -> int
        if self.__version == other.__version:
            return 0
        lhsegments = self.__get_segments()
        rhsegments = other.__get_segments()

        lhsize = len(lhsegments)
        rhsize = len(rhsegments)
        limit = (lhsize if lhsize > rhsize else rhsize) - 1

        i = 0

        while i <= limit:
            lhs = default(lambda: lhsegments[i], IndexError, 0)
            rhs = default(lambda: rhsegments[i], IndexError, 0)
            i += 1

            if lhs == rhs:
                continue
            if isinstance(lhs, str) and isinstance(rhs, int):
                return -1
            if isinstance(lhs, int) and isinstance(rhs, str):
                return 1

            return lhs - rhs
        return 0

    def __lt__(self, other):
        return self.__cmp__(other) < 0

    def __le__(self, other):
        return self.__cmp__(other) <= 0

    def __eq__(self, other):
        return self.__cmp__(other) == 0

    def __repr__(self):
        return 'GemVersion({segments})'.format(segments=self.segments())

    def __get_segments(self):
        # type: () -> Sequence[int|str]
        if not self.__segments:
            rex = re.compile('[0-9]+|[a-z]+', re.IGNORECASE)
            d_rex = re.compile('^\d+$')
            self.__segments = tuple(map(lambda s: int(s) if d_rex.match(s) else s, rex.findall(self.__version)))
        return self.__segments


class GemRequirement:
    OPS = {
        '=': lambda v, r: v == r,
        '!=': lambda v, r: v != r,
        '>': lambda v, r: v > r,
        '<': lambda v, r: v < r,
        '>=': lambda v, r: v >= r,
        '<=': lambda v, r: v <= r,
        '~>': lambda v, r: v >= r and v.release() < r.bump()
    }

    PATTERN_RAW = "\\s*({quoted})?\\s*({VERSION_PATTERN})\\s*".format(
        quoted='|'.join(tuple(map(lambda k: re.escape(k), iterkeys(OPS)))),
        VERSION_PATTERN=GemVersion.VERSION_PATTERN
    )

    # A regular expression that matches a requirement
    PATTERN = re.compile('^{PATTERN_RAW}$'.format(PATTERN_RAW=PATTERN_RAW))

    ##
    # The default requirement matches any version

    DEFAULT_REQUIREMENT = tuple(['>=', GemVersion(0)])

    class BadRequirementError(AttributeError):
        pass

    def __init__(self, *requirements):
        # type: (str) -> None
        if len(requirements) == 0:
            self.__requirements = tuple([GemRequirement.DEFAULT_REQUIREMENT])
        else:
            self.__requirements = tuple(map(lambda req: GemRequirement.parse(req), requirements))

    @classmethod
    def parse(cls, requirement):
        if isinstance(requirement, GemVersion):
            return tuple(['=', requirement])

        match = cls.PATTERN.match(str(requirement))
        if not match:
            raise cls.BadRequirementError('Illformed requirement [{inspect}]'.format(inspect=repr(requirement)))

        if match.group(1) == '>=' and match.group(2) == '0':
            return cls.DEFAULT_REQUIREMENT
        else:
            op = match.group(1) if match.group(1) else '='
            return tuple([op, GemVersion(match.group(2))])

    def satified_by(self, version):
        gemver = version if isinstance(version, GemVersion) else GemVersion(version)
        operation = self.__test_rv(gemver)
        return all(map(operation, self.__requirements))

    @classmethod
    def __test_rv(cls, version):
        # type: (GemVersion) -> Callable[[str, GemVersion], bool]
        def __testing(req):
            op, rv = req
            callable = cls.__get_operation(op)
            return callable(version, rv)
        return __testing

    @classmethod
    def __get_operation(cls, op):
        # type: (str) -> Callable[[GemVersion, GemVersion], bool]
        try:
            return cls.OPS[op]
        except KeyError:
            return cls.OPS['=']
