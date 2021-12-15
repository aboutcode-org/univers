#
# Copyright (c) nexB Inc. and others.
# SPDX-License-Identifier: Apache-2.0
#
# Visit https://aboutcode.org and https://github.com/nexB/univers for support and download.

import attr
import semantic_version
from packaging.specifiers import SpecifierSet
from semantic_version.base import AllOf
from semantic_version.base import AnyOf

from univers import gem
from univers import versions
from univers.utils import remove_spaces
from univers.version_constraint import VersionConstraint
from univers.version_constraint import contains_version


@attr.s(frozen=True, order=False, eq=True, hash=True)
class VersionRange:
    """
    Base version range class. Subclasses must provide implememt.
    A VersionRange represents a list of constraints on the versions "timeline"
    of a package.
    """

    # Versioning scheme. By convention this is the same as the Package URL
    # package type since this "defines" most commonly the versioning scheme of a
    # package, such as "npm" (whose scheme is defined in the "node-semver" npm
    # package. This could be something else though and a purl may be accompanied
    # by a version range for another scheme; for example, a
    # ``pkg:github/foo/bar`` purl could be accompanied by a a ``vers:npm/12.3``
    # range. Subclasses MUST provide this.
    scheme = None

    # Version subclass to use with this versioning scheme, such as
    # PypiVersion. Subclasses MUST provide this.
    version_class = None

    # A list of lists of VersionConstraint where the outer list is an "OR" of
    # the innner lists that are each "ANDs" of atomic constraints
    constraints = attr.ib(type=list, default=attr.Factory(list))

    def __attrs_post_init__(self, *args, **kwargs):
        self.constraints.sort()

    @classmethod
    def from_native(cls, string):
        """
        Return a VersionRange built from a scheme-specific, native version range
        ``string``. Subclasses must implement.
        """
        return NotImplementedError

    def to_native(self):
        """
        Return a native range string for this VersionRange. Subclasses must
        implement.
        """
        return NotImplementedError

    @classmethod
    def from_string(cls, vers, dedupe=False, validate=False):
        """
        Return a VersionRange built from a ``vers`` version range spec string,
        such as "vers:npm/1.2.3,>=2.0.0"
        """
        vers = remove_spaces(vers)

        uri_scheme, _, scheme_range_spec = vers.partition(":")
        uri_scheme = uri_scheme.lower()

        if uri_scheme != "vers":
            raise ValueError(f"{vers!r} must start with the 'vers:' URI scheme.")

        versioning_scheme, _, constraints = scheme_range_spec.partition("/")
        versioning_scheme = versioning_scheme.lower()
        range_class = RANGE_CLASS_BY_SCHEMES.get(versioning_scheme)
        if not range_class:
            raise ValueError(
                f"{vers!r} has an unknown versioning scheme: " f"{versioning_scheme!r}.",
            )

        constraints = constraints.strip()
        if not constraints:
            raise ValueError(f"{vers!r} specifies no version range constraints.")

        if constraints.startswith("*"):
            if constraints != "*":
                raise ValueError(f"{vers!r} contains an invalid '*' constraint.")
            return range_class([VersionConstraint.from_string("*")])

        parsed_constraints = []

        constraints = constraints.strip("|")
        for const in constraints.split("|"):
            constraint = VersionConstraint.from_string(
                string=const,
                version_class=range_class.version_class,
            )
            parsed_constraints.append(constraint)

        parsed_constraints.sort()
        if dedupe:
            parsed_constraints = VersionConstraint.dedupe(parsed_constraints)
        if validate:
            VersionConstraint.validate(parsed_constraints)

        return range_class(parsed_constraints)

    def __str__(self):
        constraints = "|".join(str(c) for c in sorted(self.constraints))
        return f"vers:{self.scheme}/{constraints}"

    to_string = __str__

    def to_dict(self):
        constraints = [c.to_dict() for c in self.constraints]
        return dict(scheme=self.scheme, constraints=constraints)

    def __contains__(self, version):
        """
        Return True if this VersionRange contains the ``version`` Version
        object. A version is contained in a VersionRange if it satisfies its
        constraints according to ``vers`` rules.
        """
        if not isinstance(version, self.version_class):
            raise TypeError(
                f"{version!r} is not of expected type: {self.version_class!r}",
            )
        return contains_version(version, self.constraints)

    contains = __contains__

    def __eq__(self, other):
        return (
            self.scheme == other.scheme
            and self.version_class == other.version_class
            and self.constraints == other.constraints
        )


class NpmVersionRange(VersionRange):
    scheme = "npm"
    version_class = versions.SemverVersion

    vers_by_native_comparators = {
        "==": "=",
        "<=": "<=",
        ">=": ">=",
        "<": "<",
        ">": ">",
    }

    @classmethod
    def from_native(cls, string):
        """
        Return a VersionRange built from an npm "node-semver" range ``string``.
        """
        # FIXME: code is entirely duplicated with the GemVersionRange

        # an NpmSpec handles parsing of both the semver versions and node-semver
        # ranges at once
        spec = semantic_version.NpmSpec(string)

        clause = spec.clause.simplify()
        assert isinstance(clause, (AnyOf, AllOf))
        anyof_constraints = []
        if isinstance(clause, AnyOf):
            for allof_clause in clause.clauses:
                anyof_constraints.append(get_allof_constraints(cls, allof_clause))
        elif isinstance(clause, AllOf):
            alloc = get_allof_constraints(cls, clause)
            anyof_constraints.append(alloc)
        else:
            raise ValueError(f"Unknown clause type: {spec!r}")

        return cls(constraints=anyof_constraints)


def get_allof_constraints(cls, clause):
    """
    Return a list of VersionConstraint given an AllOf ``clause``.
    """
    assert isinstance(clause, AllOf)
    allof_constraints = []
    for constraint in clause.clauses:
        comparator = cls.vers_by_native_comparators[constraint.operator]
        version = cls.version_class(str(constraint.target))
        constraint = VersionConstraint(comparator=comparator, version=version)
        allof_constraints.append(constraint)
    return allof_constraints


class GemVersionRange(VersionRange):
    """
    A version range implementation for Rubygems.

    gem need its own versioning scheme as this is not semver.
    See https//github.com/nexB/univers/issues/5
    See https://github.com/ruby/ruby/blob/415671a28273e5bfbe9aa00a0e386f025720ac23/lib/rubygems/requirement.rb
    See https//semver.org/spec/v2.0.0.html#spec-item-11
    See https//snyk.io/blog/differences-in-version-handling-gems-and-npm/
    See https://github.com/npm/node-semver/issues/112
    """

    scheme = "gem"
    version_class = versions.RubygemsVersion

    vers_by_native_comparators = {
        "=": "=",
        "!=": "!=",
        "<=": "<=",
        ">=": ">=",
        "<": "<",
        ">": ">",
    }

    @classmethod
    def from_native(cls, string):
        """
        Return a VersionRange built from a Rubygem version range ``string``.

        Gem version semantics are different from semver: there can be commonly
        more than three segments and the operators are also different.
        """

        gr = gem.GemRequirement.from_string(string).simplify()

        constraints = []
        for gc in gr.constraints:
            version = cls.version_class(str(gc.version))
            op = cls.vers_by_native_comparators[gc.op]
            vc = VersionConstraint(comparator=op, version=version)
            constraints.append(vc)

        return cls(constraints=constraints)


class DebianVersionRange(VersionRange):
    scheme = "deb"
    version_class = versions.DebianVersion


class PypiVersionRange(VersionRange):
    """
    PyPI PEP 440 version range.

    For example:
    >>> from univers.versions import PypiVersion
    >>> constraints = [
    ...    VersionConstraint(version=PypiVersion("2")),
    ...    VersionConstraint(comparator=">=", version=PypiVersion("3")),
    ...    VersionConstraint(comparator="<", version=PypiVersion("4")),
    ...    VersionConstraint(version=PypiVersion("5")),
    ... ]
    >>> range = PypiVersionRange(constraints=constraints)
    >>> assert str(range) == "vers:pypi/2|>=3|<4|5"
    """

    scheme = "pypi"
    version_class = versions.PypiVersion

    vers_by_native_comparators = {
        # 01.01.01 is equal 1.1.1 e.g., with version normalization
        "==": "=",
        "!=": "!=",
        "<=": "<=",
        ">=": ">=",
        "<": "<",
        ">": ">",
        "~=": None,
        # 01.01.01 is NOT equal to 1.1.1 using === which is strict string equality
        "===": None,
    }

    @classmethod
    def from_native(cls, string):
        """
        Return a VersionRange built from a PyPI PEP440 version specifiers ``string``.
        """
        # TODO: there is a complication with environment markers that are not yet supported

        # TODO: handle ~= and === operators
        specifiers = SpecifierSet(string)

        # In PyPI all constraints apply
        constraints = []

        for spec in specifiers:
            operator = spec.operator
            version = spec.version
            assert isinstance(version, cls.version_class)
            comparator = cls.vers_by_native_comparators[operator]
            constraint = VersionConstraint(comparator=comparator, version=version)
            constraints.append(constraint)

        return cls(constraints=constraints)


class MavenVersionRange(VersionRange):
    """
    Maven version range as documented at
    https://maven.apache.org/enforcer/enforcer-rules/versionRanges.html
    """

    scheme = "maven"
    version_class = versions.MavenVersion


class NugetVersionRange(VersionRange):
    scheme = "nuget"
    version_class = versions.NugetVersion


class ComposerVersionRange(VersionRange):
    # TODO composer may need its own scheme see https//github.com/nexB/univers/issues/5
    # and https//getcomposer.org/doc/articles/versions.md
    scheme = "composer"
    version_class = versions.SemverVersion


class RpmVersionRange(VersionRange):
    # https://twiki.cern.ch/twiki/bin/view/Main/RPMAndDebVersioning
    scheme = "rpm"
    version_class = versions.RpmVersion


class GolangVersionRange(VersionRange):
    scheme = "golang"
    version_class = versions.SemverVersion


class GenericVersionRange(VersionRange):
    scheme = "generic"
    version_class = versions.SemverVersion
    # apache is not semver at large. And in particular we may have schemes that
    # are package name-specific


class ApacheVersionRange(VersionRange):
    scheme = "apache"
    version_class = versions.SemverVersion


class HexVersionRange(VersionRange):
    scheme = "hex"
    version_class = versions.SemverVersion


class CargoVersionRange(VersionRange):
    scheme = "cargo"
    version_class = versions.SemverVersion


class MozillaVersionRange(VersionRange):
    scheme = "mozilla"
    version_class = versions.SemverVersion


class GitHubVersionRange(VersionRange):
    scheme = "github"
    version_class = versions.SemverVersion


class EbuildVersionRange(VersionRange):
    scheme = "ebuild"
    version_class = versions.GentooVersion


class ArchLinuxVersionRange(VersionRange):
    scheme = "archlinux"
    version_class = versions.ArchLinuxVersion


class NginxVersionRange(VersionRange):
    """
    Nginx versioning is semver for version and their own syntax for ranges as
    used in their security advisories.

    The documentation on these ranges is minimal. See these for details:
    - https://mailman.nginx.org/pipermail/nginx/2021-September/061039.html
    - https://nginx.org/en/security_advisories.html
    - https://serverfault.com/questions/715049/what-s-the-difference-between-the-mainline-and-stable-branches-of-nginx

    In particular for versions:
    - the versions are semver.

    - versions can be in the one "mainline" branch or one of many "stable" branches.

    - for versions in the "mainline" branch, (e.g., development) the minor
      segment is an odd number.

    - versions in the "stable" branch, (e.g., a release branch) the minor
      segment is an even number. Installation are typically made from branch and
      its versions.

      For example: in 0.6.18 the 6 e.g., semver "minor" segment is either odd or even
      - odd (as with "7") means this is the "mainline" branch
      - even (as with "4") means this is in a "stable" branch

    And for ranges, we have these notations:

    - dash ranges: 0.6.18-1.20.0 where start and end are included in the range

    - comma ranges: 1.21.0+, 1.20.1+ where any of the condition applies

    - plus suffixes: 1.21.0+ where this or any later version in the branch applies
      Therefore:
      - 1.21.0+ would expand to >=1.21.0 because 21 is odd and this is the
        mainline branch

      - 1.22.0+ would expand to >=1.22.0,<1.23.0 because 22 is even and this is
        one of the stable branches

    There are two special version range values:
      - "all" means all versions.
      - "none" means no version and therefore no version range. It is used only
        in one advisory for CVE-2009-4487 and triggers an error.

    Some vulnerable ranges are only for Windows builds but the range syntax is
    the same. This could be resolved with a specific purl qualifier.
    These are prefixed by the string "nginx/Window".
    """

    scheme = "nginx"
    version_class = versions.SemverVersion

    vers_by_native_comparators = {
        "==": "=",
        "<=": "<=",
        ">=": ">=",
        "<": "<",
        ">": ">",
    }

    @classmethod
    def from_native(cls, string):
        """
        Return a VersionRange built from an nginx range ``string``.

        For example:
        >>> result = NginxVersionRange.from_native("1.5.10")
        >>> assert str(result) == "vers:nginx/1.5.10", str(result)

        >>> result = NginxVersionRange.from_native("0.7.52-0.8.39")
        >>> assert str(result) == "vers:nginx/>=0.7.52|<=0.8.39", str(result)

        >>> result = NginxVersionRange.from_native("1.1.4-1.2.8, 1.3.9-1.4.0")
        >>> assert str(result) == "vers:nginx/>=1.1.4|<=1.2.8|>=1.3.9|<=1.4.0", str(result)

        >>> result = NginxVersionRange.from_native("0.8.40+, 0.7.66+")
        >>> assert str(result) == "vers:nginx/>=0.7.66|>=0.8.40|<0.9.0", str(result)

        >>> result = NginxVersionRange.from_native("1.5.0+, 1.4.1+")
        >>> assert str(result) == "vers:nginx/>=1.4.1|<1.5.0|>=1.5.0", str(result)

        >>> result = NginxVersionRange.from_native("all")
        >>> assert str(result) == "vers:nginx/*", str(result)

        >>> try:
        ...     NginxVersionRange.from_native("none")
        ... except ValueError:
        ...     pass
        """
        cleaned = remove_spaces(string).lower()
        if cleaned == "all":
            return cls(constraints=[VersionConstraint(comparator="*")])

        constraints = []

        for clauses in cleaned.split(","):

            if "-" in clauses:
                # dash range
                start, _, end = clauses.partition("-")
                start_version = semantic_version.Version.coerce(start)
                end_version = semantic_version.Version.coerce(end)
                vstart = VersionConstraint(comparator=">=", version=start_version)
                vend = VersionConstraint(comparator="<=", version=end_version)
                constraints.extend([vstart, vend])

            elif "+" in clauses:
                # suffixed version
                vs = clauses.rstrip("+")
                version = semantic_version.Version.coerce(vs)
                is_stable = is_even(version.minor)

                if is_stable:
                    # we have a start and end in stable ranges
                    start_version = semantic_version.Version.coerce(vs)
                    end_version = start_version.next_minor()
                    vstart = VersionConstraint(comparator=">=", version=start_version)
                    vend = VersionConstraint(comparator="<", version=end_version)
                    constraints.extend([vstart, vend])
                else:
                    # mainline branch ranges are resolved to a singel constraint
                    version = semantic_version.Version.coerce(vs)
                    constraint = VersionConstraint(comparator=">=", version=version)
                    constraints.append(constraint)

            else:
                # plain single version
                version = semantic_version.Version.coerce(clauses)
                constraint = VersionConstraint(comparator="=", version=version)
                constraints.append(constraint)

        return cls(constraints=constraints)


def is_even(s):
    """
    Return True if the string "s" is an even number and False if this is an odd
    number. For example:

    >>> is_even(4)
    True
    >>> is_even(123)
    False
    >>> is_even(0)
    True
    """
    return (int(s) % 2) == 0


RANGE_CLASS_BY_SCHEMES = {
    "npm": NpmVersionRange,
    "deb": DebianVersionRange,
    "pypi": PypiVersionRange,
    "maven": MavenVersionRange,
    "nuget": NugetVersionRange,
    "composer": ComposerVersionRange,
    "gem": GemVersionRange,
    "rpm": RpmVersionRange,
    "golang": GolangVersionRange,
    "generic": GenericVersionRange,
    "apache": ApacheVersionRange,
    "hex": HexVersionRange,
    "cargo": CargoVersionRange,
    "mozilla": MozillaVersionRange,
    "github": GitHubVersionRange,
    "ebuild": EbuildVersionRange,
    "archlinux": ArchLinuxVersionRange,
    "nginx": NginxVersionRange,
}
