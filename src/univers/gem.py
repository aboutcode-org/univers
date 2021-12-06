# Copyright (c) Center for Information Technology, http://coi.gov.pl
# SPDX-License-Identifier: Apache-2.0
# this has been significantly modified from the original
#
# Visit https://aboutcode.org and https://github.com/nexB/univers for support and download.

# notes: This has been substantially modified and enhanced from the original
# puppeteer code to extract the Ruby version hanlding code.


import re
from collections import namedtuple


def default(x, e, y):
    try:
        return x()
    except e:
        return y


class GemVersion:
    VERSION_PATTERN = "[0-9]+(?:\.[0-9a-zA-Z]+)*(-[0-9A-Za-z-]+(\.[0-9A-Za-z-]+)*)?"
    ANCHORED_VERSION_PATTERN = re.compile(
        "^\s*({VERSION_PATTERN})?\s*$".format(VERSION_PATTERN=VERSION_PATTERN)
    )

    def __init__(self, version):

        self.original = version

        # If version is an empty string convert it to 0
        version = 0 if re.compile("^\s*$").match(str(version)) else version

        self.__version = str(version).strip().replace("-", ".pre.")
        self.__segments = None
        self.__bump = None
        self.__release = None

    def __str__(self):
        return self.original

    def bump(self):
        """
        Return a new GemVersion built from incrementing this GemVersion  last
        numeric segment.
        """
        if not self.__bump:
            segments = self.segments()
            while any(map(lambda s: isinstance(s, str), segments)):
                segments.pop()
            if len(segments) > 1:
                segments.pop()
            segments[-1] = segments[-1] + 1
            segments = list(map(lambda r: str(r), segments))
            self.__bump = GemVersion(".".join(segments))

        return self.__bump

    def release(self):
        """
        Return a new GemVersion composed only of release, numeric segments.
        """
        if not self.__release:
            segments = self.segments()
            while any(map(lambda s: isinstance(s, str), segments)):
                segments.pop()
            segments = list(map(lambda r: str(r), segments))
            self.__release = GemVersion(".".join(segments))

        return self.__release

    def segments(self):
        """
        Return a list of version segments.
        """
        return list(self.__get_segments())

    def __cmp__(self, other):
        """
        Compare the ``other`` GemVersion with this GemVersion according to the
        legacy "cmp()" function semantics. Return 0, 1, or -1.
        """
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
        return "GemVersion({segments})".format(segments=self.segments())

    def __get_segments(self):
        """
        Return a sequence of ints and strings segments parsed from the original
        version string.
        """
        # type: () -> Sequence[int|str]
        if not self.__segments:
            rex = re.compile("[0-9]+|[a-z]+", re.IGNORECASE)
            d_rex = re.compile("^\d+$")
            self.__segments = tuple(
                map(lambda s: int(s) if d_rex.match(s) else s, rex.findall(self.__version))
            )
        return self.__segments


GemConstraint = namedtuple("GemConstraint", ["op", "version"])
GemConstraint.to_string = lambda gc: f"{gc.op} {gc.version}"


def sorted_constraints(constraints):
    return sorted(constraints, key=lambda gc: gc.version)


class GemRequirement:
    """
    A gem requirement using the Gem notation.
    """

    OPS = {
        "=": lambda v, r: v == r,
        "!=": lambda v, r: v != r,
        ">": lambda v, r: v > r,
        "<": lambda v, r: v < r,
        ">=": lambda v, r: v >= r,
        "<=": lambda v, r: v <= r,
        "~>": lambda v, r: v >= r and v.release() < r.bump(),
    }

    PATTERN_RAW = "\\s*({quoted})?\\s*({VERSION_PATTERN})\\s*".format(
        quoted="|".join(tuple(map(lambda k: re.escape(k), iter(OPS)))),
        VERSION_PATTERN=GemVersion.VERSION_PATTERN,
    )

    # A regular expression that matches a requirement
    PATTERN = re.compile("^{PATTERN_RAW}$".format(PATTERN_RAW=PATTERN_RAW))

    # #
    # The default requirement matches any version

    DEFAULT_REQUIREMENT = tuple([">=", GemVersion(0)])

    class BadRequirementError(AttributeError):
        pass

    def __init__(self, *requirements):

        if not requirements:
            self.requirements = tuple([GemRequirement.DEFAULT_REQUIREMENT])

        else:
            self.requirements = tuple(map(GemRequirement.parse, requirements))

    def for_lockfile(self):
        """
        Return a string representing this list of requirements suitable for use
        in a lockfile.

        For example::
        >>> gr = GemRequirement(">= 1.0.1", "~> 1.0")
        >>> gf_flf = gr.for_lockfile()
        >>> assert gf_flf == " (~> 1.0, >= 1.0.1)", gf_flf
        """

        gcs = [GemConstraint(*r) for r in self.requirements]
        gcs = [gc.to_string() for gc in sorted_constraints(gcs)]
        reqss = ", ".join(gcs)
        return f" ({reqss})"

    @classmethod
    def create(cls, reqs):
        """
        Return a GemRequirement built from a single requirement string or a list
        of requirement strings.
        """
        if isinstance(reqs, list):
            return GemRequirement(*reqs)
        else:
            return GemRequirement(reqs)

    @classmethod
    def parse(cls, requirement):
        """
        Return a tuple of (operator string, GemVersion object) parsed from a
        saingle ``requirement`` string.
        """
        if isinstance(requirement, GemVersion):
            return tuple(["=", requirement])

        match = cls.PATTERN.match(str(requirement))
        if not match:
            raise cls.BadRequirementError(
                "Illformed requirement [{inspect}]".format(inspect=repr(requirement))
            )

        if match.group(1) == ">=" and match.group(2) == "0":
            return cls.DEFAULT_REQUIREMENT
        else:
            op = match.group(1) if match.group(1) else "="
            return tuple([op, GemVersion(match.group(2))])

    def satified_by(self, version):
        """
        Return True if the ``version`` GemVersion or string satisfied this
        requirement.
        """
        gemver = version if isinstance(version, GemVersion) else GemVersion(version)
        operation = self.__test_rv(gemver)
        return all(map(operation, self.requirements))

    @classmethod
    def __test_rv(cls, version):
        """
        Return a callable function that can check if a ``version`` satisfies the
        operation of a single (op, version) requirement.
        """

        # type: (GemVersion) -> Callable[[str, GemVersion], bool]
        def __testing(req):
            op, rv = req
            callble = cls.__get_operation(op)
            return callble(version, rv)

        return __testing

    @classmethod
    def __get_operation(cls, op):
        """
        Return a callable operator given an ``op`` operator string.
        """
        # type: (str) -> Callable[[GemVersion, GemVersion], bool]
        try:
            return cls.OPS[op]
        except KeyError:
            return cls.OPS["="]
