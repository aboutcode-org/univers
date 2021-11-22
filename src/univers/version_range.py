#
# Copyright (c) nexB Inc. and others.
# SPDX-License-Identifier: Apache-2.0
#
# Visit https://aboutcode.org and https://github.com/nexB/univers for support and download.

import attr
from packaging.specifiers import SpecifierSet
from semantic_version import NpmSpec
from semantic_version.base import AllOf
from semantic_version.base import AnyOf

from univers import versions
from univers.utils import remove_spaces
from univers.version_constraint import VersionConstraint


@attr.s(frozen=True, order=False, eq=True, hash=True)
class VersionRange:
    """
    Base version range class. Subclasses must provide implememt.
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
        VersionConstraint.sort(self.constraints)

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
    def from_string(cls, vers):
        """
        Return a VersionRange built from a ``vers`` version range spec string,
        such as "vers:npm/1.2.3,>=2.0.0"
        """
        vers = remove_spaces(vers)

        uri_scheme, _, scheme_range_spec = vers.partition(":")
        if not uri_scheme == "vers":
            raise ValueError(f"{vers!r} must start with the 'vers:' URI scheme.")

        versioning_scheme, _, constraints = scheme_range_spec.partition("/")
        range_class = RANGE_CLASS_BY_SCHEMES.get(versioning_scheme)
        if not range_class:
            raise ValueError(
                f"{vers!r} has an unknown versioning scheme: " f"{versioning_scheme!r}.",
            )

        if not constraints:
            raise ValueError(f"{vers!r} specifies no version range constraints.")

        # parse_constraints
        version_constraints = []
        for or_constraints in constraints.split("|"):
            and_constraints = []
            for constraint in or_constraints.split(","):
                constraint = VersionConstraint.from_string(
                    string=constraint,
                    version_class=range_class.version_class,
                )
                and_constraints.append(constraint)
            version_constraints.append(and_constraints)

        return range_class(version_constraints)

    def __str__(self):
        constraints = VersionConstraint.to_constraints_string(self.constraints)
        return f"vers:{self.scheme}/{constraints}"

    to_string = __str__

    def to_dict(self):
        VersionConstraint.validate(self.constraints)

        constraints = []
        for inner_constraints in self.constraints:
            constraints.append([c.to_dict() for c in inner_constraints])
        return dict(scheme=self.scheme, constraints=constraints)

    def __contains__(self, version):
        """
        Return True if this VersionRange contains the ``version`` Version
        object. A version is contained in a VersionRange if it satisfies its
        constraints this way:

        - at least one of its ``constraints`` nested inner list of
          VersionConstraint should be satisfied

        - a nested inner list of VersionConstraint is satisfied if all of its
          VersionConstraints are satisfied, e.g., the ``version`` is contained in
          all of the version ranges described by the constraint.

        - a VersionConstraint is "satisfied" if the ``version`` Version is "in"
          this VersionConstraint. Conversely, the ``version`` satisfies a constraint.
        """
        if not isinstance(version, self.version_class):
            raise TypeError(
                f"{version!r} is not of expected type: {self.version_class!r}",
            )
        for inner_constraints in self.constraints:
            if version.satisfies_all(inner_constraints):
                return True
        return False

    contains = __contains__

    @classmethod
    def join(cls, constraints):
        """
        Return a string representing the provided ``constraints`` nested
        sequence of VersionConstraint objects such that the outer sequence
        VersionConstraints are joined with an "OR" e.g., a "vers" pipe "|" and
        the inner sequences of VersionConstraint are each joined with an "AND"
        e.g., a "vers" coma ",".
        """
        cls.validate(constraints)
        or_constraints = []
        for inner_constraints in constraints:
            and_constraints = ",".join(str(c) for c in sorted(inner_constraints))
            or_constraints.append(and_constraints)
        return "|".join(or_constraints)

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
        spec = NpmSpec(string)

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
    # gem need its own scheme see https//github.com/nexB/univers/issues/5
    # See https://github.com/ruby/ruby/blob/415671a28273e5bfbe9aa00a0e386f025720ac23/lib/rubygems/requirement.rb
    # See https//semver.org/spec/v2.0.0.html#spec-item-11
    # See https//snyk.io/blog/differences-in-version-handling-gems-and-npm/
    # See https://github.com/npm/node-semver/issues/112

    scheme = "gem"
    version_class = versions.RubyVersion

    vers_by_native_comparators = {
        "==": "=",
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
        """
        # TODO: Gem version semantics are different from semver:
        # there can be commonly more than 3 segments
        # the operators are also different.

        # replace Rubygem ~> pessimistic operator by node-semver equivalent
        string = string.replace("~>", "~")
        spec = NpmSpec(string)

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


class DebianVersionRange(VersionRange):
    scheme = "deb"
    version_class = versions.DebianVersion


class PypiVersionRange(VersionRange):
    scheme = "pypi"
    version_class = versions.PypiVersion

    vers_by_native_comparators = {
        "==": "=",
        "!=": "!=",
        "<=": "<=",
        ">=": ">=",
        "<": "<",
        ">": ">",
        "~=": None,
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
        allof_constraints = []
        constraints = [allof_constraints]

        for spec in specifiers:
            operator = spec.operator
            version = spec.version
            assert isinstance(version, cls.version_class)
            comparator = cls.vers_by_native_comparators[operator]
            constraint = VersionConstraint(comparator=comparator, version=version)
            allof_constraints.append(constraint)

        return cls(constraints=constraints)


class MavenVersionRange(VersionRange):
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
    scheme = "nginx"
    version_class = None


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
