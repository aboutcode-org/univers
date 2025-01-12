#
# Copyright (c) nexB Inc. and others.
# SPDX-License-Identifier: Apache-2.0
#
# Visit https://aboutcode.org and https://github.com/aboutcode-org/univers for support and download.

from typing import List
from typing import Union

import attr
import semantic_version
from packaging.specifiers import InvalidSpecifier
from packaging.specifiers import SpecifierSet
from semantic_version.base import AllOf
from semantic_version.base import AnyOf

from univers import gem
from univers import maven
from univers import versions
from univers.conan.version_range import VersionRange as conan_version_range
from univers.utils import remove_spaces
from univers.version_constraint import VersionConstraint
from univers.version_constraint import contains_version


class InvalidVersionRange(Exception):
    """
    Error for scheme-specific version syntax is not supported or not valid
    """


INVERTED_COMPARATORS = {
    ">=": "<",
    "<=": ">",
    "!=": "=",
    "<": ">=",
    ">": "<=",
    "=": "!=",
}


@attr.s(frozen=True, order=False, eq=True, hash=True)
class VersionRange:
    """
    Base version range class. Subclasses must provide implement.
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

    # A tuple of VersionConstraint that are signposts on the versions
    # timeline
    constraints = attr.ib(type=tuple, default=attr.Factory(tuple))

    def __attrs_post_init__(self, *args, **kwargs):
        constraints = tuple(sorted(self.constraints))
        # Notes: setattr is used because this is an immutable frozen instance.
        # See https://www.attrs.org/en/stable/init.html?#post-init
        object.__setattr__(self, "constraints", constraints)

    @classmethod
    def from_native(cls, string):
        """
        Return a VersionRange built from a scheme-specific, native version range
        ``string``. Subclasses can implement.
        """
        return NotImplementedError

    @classmethod
    def from_natives(cls, strings):
        """
        Return a VersionRange built from a ``strings`` list of scheme-
        specific native version range strings. Subclasses can implement.
        """
        return NotImplementedError

    def to_native(self, *args, **kwargs):
        """
        Return a native range string for this VersionRange. Subclasses can
        implement. Optional ``args`` and ``kwargs`` allow subclass to require
        extra arguments (such as a package name that some scheme may require
        like for deb and rpm.)
        """
        return NotImplementedError

    @classmethod
    def from_string(cls, vers, simplify=False, validate=False):
        """
        Return a VersionRange built from a ``vers`` version range spec string,
        such as "vers:npm/1.2.3,>=2.0.0"
        """
        if not vers or not isinstance(vers, str) or not vers.strip():
            raise ValueError(
                f"{vers!r} is not a valid argument, a valid ``vers`` string argument is required."
            )

        # Spaces are not significant and removed in a canonical form.
        vers = remove_spaces(vers)

        # A version range specifier contains only printable ASCII letters, digits and
        # punctuation.
        is_ascii = len(vers) + 2 == len(ascii(vers))
        if not is_ascii:
            raise ValueError(f"Invalid non ASCII characters: {vers!r}")

        # The URI scheme and versioning scheme are always lowercase as in  ``vers:npm``.
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

        version_class = range_class.version_class

        constraints = remove_spaces(constraints)
        if not constraints:
            raise ValueError(f"{vers!r} specifies no version range constraints.")

        # There is only one star: "*" must only occur once and alone in a range,
        # without any other constraint or version.
        if constraints.startswith("*"):
            if constraints != "*":
                raise ValueError(f"{vers!r} contains an invalid '*' constraint.")
            return range_class(
                [VersionConstraint.from_string(string="*", version_class=version_class)]
            )

        parsed_constraints = []

        constraints = constraints.strip("|")
        for const in constraints.split("|"):
            constraint = VersionConstraint.from_string(
                string=const,
                version_class=version_class,
            )
            parsed_constraints.append(constraint)

        # Constraints are sorted by version**. The canonical ordering is the versions
        # order. The ordering of ``<version-constraint>`` is not significant otherwise
        # but this sort order is needed when check if a version is contained in a range.
        parsed_constraints.sort()

        if simplify:
            parsed_constraints = VersionConstraint.simplify(parsed_constraints)
        if validate:
            VersionConstraint.validate(parsed_constraints)

        return range_class(parsed_constraints)

    @classmethod
    def from_versions(cls, sequence):
        """
        Return a VersionRange built from a list of version strings,
        such as ["3.0.0", "1.0.1b", "3.0.2", "0.9.7a", "1.1.1ka"]
        """
        if not cls.scheme or not cls.version_class:
            return NotImplementedError

        constraints = []
        for version in sequence:
            version_obj = cls.version_class(version)
            constraint = VersionConstraint(comparator="=", version=version_obj)
            constraints.append(constraint)
        return cls(constraints=constraints)

    def is_star(self):
        return len(self.constraints) == 1 and self.constraints[0].is_star()

    def invert(self):
        """
        Return the inverse or complement of this VersionRange. For example, if this range is
        ">=1.0.0", the inverse is "<1.0.0".
        >>> str(VersionRange.from_string("vers:npm/>=1.0.0").invert())
        'vers:npm/<1.0.0'
        """
        inverted_constraints = []

        if self.is_star():
            # The inverse of "*" is an empty range.
            return None

        for constraint in self.constraints:
            inverted_constraints.append(constraint.invert())

        return self.__class__(constraints=inverted_constraints)

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

    def normalize(self, known_versions: List[str]):
        """
        Return a new VersionRange normalized and simplified using the universe of
        ``known_versions`` list of version strings.
        """
        versions = sorted([self.version_class(i) for i in known_versions])

        resolved = []
        contiguous = []
        for kv in versions:
            if self.__contains__(kv):
                contiguous.append(kv)
            elif contiguous:
                resolved.append(contiguous)
                contiguous = []

        if contiguous:
            resolved.append(contiguous)

        version_constraints = []
        for contiguous_segment in resolved:
            lower_bound = contiguous_segment[0]
            upper_bound = contiguous_segment[-1]
            if lower_bound == upper_bound:
                version_constraints.append(VersionConstraint(version=lower_bound))
            else:
                version_constraints.append(VersionConstraint(comparator=">=", version=lower_bound))
                version_constraints.append(VersionConstraint(comparator="<=", version=upper_bound))

        return self.__class__(constraints=version_constraints)


def from_cve_v4(data, scheme):
    """
    Return a VersionRange build from the provided CVE V4 API ``data`` using the
    provided versioning vers ``scheme``.
    """


def from_cve_v5(data, scheme):
    """
    Return a VersionRange build from the provided CVE V5 API ``data`` using the
    provided versioning vers ``scheme``.

    See https://github.com/CVEProject/cve-schema/tree/master/schema/v5.0
    ``data`` can be:
    - a mapping of collectionURL and versions:
        {"collectionURL": "some URL", "versions": [{"versionValue": "1.0"}]}

    """


def from_osv_v1(data, scheme):
    """
    Return a VersionRange build from the provided CVE V4 API data using the
    provided versioning vers ``scheme``.
    """


def get_allof_constraints(cls, clause):
    """
    Return a list of VersionConstraint given an AllOf ``clause``.
    """
    if not isinstance(clause, AllOf):
        raise ValueError(f"Unknown clause type: {clause!r}")
    allof_constraints = []
    for constraint in clause.clauses:
        comparator = cls.vers_by_native_comparators[constraint.operator]
        version = cls.version_class(str(constraint.target))
        constraint = VersionConstraint(comparator=comparator, version=version)
        allof_constraints.append(constraint)
    return allof_constraints


def get_npm_version_constraints_from_semver_npm_spec(string, cls):
    """
    Return a VersionConstraint for the provided ``string``.
    """
    spec = semantic_version.NpmSpec(string)
    clause = spec.clause.simplify()
    if isinstance(clause, (AnyOf, AllOf)):
        anyof_constraints = []
        if isinstance(clause, AnyOf):
            for allof_clause in clause.clauses:
                anyof_constraints.extend(get_allof_constraints(cls, allof_clause))
        elif isinstance(clause, AllOf):
            alloc = get_allof_constraints(cls, clause)
            anyof_constraints.extend(alloc)
        else:
            raise ValueError(f"Unknown clause type: {spec!r}")
    return anyof_constraints


class NpmVersionRange(VersionRange):
    scheme = "npm"
    version_class = versions.SemverVersion

    vers_by_native_comparators = {
        "==": "=",
        "<=": "<=",
        ">=": ">=",
        "<": "<",
        ">": ">",
        "=": "=",  # This is not a native node-semver comparator, but is used in the gitlab version range for npm packages.
    }

    @classmethod
    def from_native(cls, string):
        """
        Return a VersionRange built from an npm "node-semver" range ``string``.
        """
        # FIXME: code is entirely duplicated with the GemVersionRange

        # an NpmSpec handles parsing of both the semver versions and node-semver
        # ranges at once

        if string == "*":
            return cls(
                constraints=[
                    VersionConstraint.from_string(string="*", version_class=cls.version_class)
                ]
            )

        constraints = []
        vrc = cls.version_class
        # A constraint item can be a comparator or a version or a version with comparator
        # If it's empty continue
        # If it's in `vers_by_native_comparators`, append it with the comparator and continue
        # If it's a version, make version constraint from the version and use the comparator from the previous item and make comparator empty
        # If it's a version with comparator, use split_req to get version and comparator to form constraint and make comparator empty

        for range in string.split("||"):
            if " - " in range:
                constraints.extend(
                    get_npm_version_constraints_from_semver_npm_spec(string=range, cls=cls)
                )
                continue
            comparator = ""
            for constraint in range.split():
                cmp = "".join([comparator, constraint])
                if cmp in cls.vers_by_native_comparators:
                    comparator = cls.vers_by_native_comparators[cmp]
                    continue
                if comparator:
                    if constraint.endswith(".x"):
                        constraints.extend(
                            get_npm_version_constraints_from_semver_npm_spec(
                                string=constraint, cls=cls
                            )
                        )
                    else:
                        constraint = constraint.lstrip("vV")
                        constraints.append(
                            VersionConstraint(comparator=comparator, version=vrc(constraint))
                        )
                else:
                    # Handle caret range expression.
                    if constraint.startswith("^"):
                        base_version = vrc(constraint.lstrip("^"))
                        prerelease = base_version.value.prerelease
                        base_version.value.prerelease = ()
                        if base_version.major:
                            high = base_version.next_major()
                        elif base_version.minor:
                            high = base_version.next_minor()
                        else:
                            high = base_version.next_patch()
                        base_version.value.prerelease = prerelease
                        lower = base_version
                        constraints.extend(
                            [
                                VersionConstraint(comparator=">=", version=lower),
                                VersionConstraint(comparator="<", version=high),
                            ]
                        )
                    elif constraint.endswith(".x") or constraint.startswith("~"):
                        constraints.extend(
                            get_npm_version_constraints_from_semver_npm_spec(
                                string=constraint, cls=cls
                            )
                        )
                    else:
                        comparator, version_constraint = split_req(
                            string=constraint,
                            comparators=cls.vers_by_native_comparators,
                            default="=",
                        )
                        version_constraint = version_constraint.lstrip("vV")
                        constraints.append(
                            VersionConstraint(
                                comparator=comparator, version=vrc(version_constraint)
                            )
                        )
                comparator = ""
        return cls(constraints=constraints)


class ConanVersionRange(VersionRange):
    scheme = "conan"
    version_class = versions.ConanVersion

    @classmethod
    def from_native(cls, string):
        """
        Return a VersionRange built from a conan range ``string``.
        """
        condition_sets = conan_version_range(string).condition_sets
        constraints = []
        for conditions in condition_sets:
            for condition in conditions.conditions:
                comparator = condition.operator
                version = condition.version
                constraints.append(
                    VersionConstraint(
                        comparator=comparator, version=cls.version_class(str(version))
                    )
                )
        return cls(constraints=constraints)


class GemVersionRange(VersionRange):
    """
    A version range implementation for Rubygems.

    gem need its own versioning scheme as this is not semver.
    See https//github.com/aboutcode-org/univers/issues/5
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


def split_req(string, comparators, default=None, strip=""):
    """
    Return a tuple of (vers comparator, version) strings given an common version
    requirement``string`` such as "> 2.3" or "<= 2.3" using the ``comparators``
    mapping of {native comparator: vers comparator}. Strip the ``string`` from
    the provided leading of training characters in ``strip``.

    If there is none of the ``comparators`` found in ``string``:

    - Return the ``default`` vers comparator string if provided.
    - Otherwise, raise a ValueError for an unknown comparator.

    For example::

    >>> comps = {"=": "=", "<=": "<=", ">=": ">="}
    >>> assert split_req("= 2.3", comparators=comps) == ("=", "2.3",)
    >>> assert split_req("  <   =  2 . 3  ", comparators=comps) == ("<=", "2.3",)
    >>> assert split_req(">= 2.3", comparators=comps) == (">=", "2.3",)
    >>> assert split_req(">= 2.3", comparators=comps) == (">=", "2.3",)
    >>> assert split_req("<= 2.3", comparators=comps) == ("<=", "2.3",)
    >>> assert split_req("(< =  2.3 )", comparators=comps, strip=")(") == ("<=", "2.3",)

    With a default, we return the default comparator::

    >>> assert split_req("2.3,", comparators=comps, default="=", strip=",") == ("=", "2.3",)

    Otherwise, a ValuaeError::

    >>> try:
    ...     split_req("~2.3", comparators=comps, )
    ...     raise Exception("ValueError should be raised")
    ... except ValueError:
    ...     pass
    """
    constraint_string = remove_spaces(string).strip(strip)

    for native_comparator, vers_comparator in comparators.items():
        if constraint_string.startswith(native_comparator):
            version = constraint_string.lstrip(native_comparator)
            return vers_comparator, version

    if default:
        return default, constraint_string

    raise ValueError(f"Unknown comparator in version requirement: {string!r} ")


class DebianVersionRange(VersionRange):
    """
    Debian version ranges as seen in Debian manual for relationships:
    https://www.debian.org/doc/debian-policy/ch-relationships.html

    These are for defined one expression at a time. Multiple expressions each
    com with a package name. Therefore there is no "range string" per se, instead
    there is always a list of version constraints as an input. For instance::

        libc6 (>> 2.23), libc6 (<< 2.24)'

    Therefore native conversions are different.
    """

    scheme = "deb"
    version_class = versions.DebianVersion
    vers_by_native_comparators = {
        "=": "=",
        "<=": "<=",
        ">=": ">=",
        "<<": "<",
        ">>": ">",
        # legacy
        "<": "<",
        ">": ">",
    }

    @classmethod
    def split(cls, string):
        """
        Return a tuple of (vers comparator, version) strings given a Debian
        version relationship ``string`` such as ">>2.3" or "(<< 2.3)". Raise a
        ValueError for unknown comparators.

        For example::
        >>> assert DebianVersionRange.split("=2.3") == ("=", "2.3",)
        >>> assert DebianVersionRange.split("  <   =  2 . 3  ") == ("<=", "2.3",)
        >>> assert DebianVersionRange.split("(>=2.3)") == (">=", "2.3",)
        >>> assert DebianVersionRange.split(">=2.3") == (">=", "2.3",)
        >>> assert DebianVersionRange.split("<=2.3") == ("<=", "2.3",)
        >>> assert DebianVersionRange.split("<<2.3") == ("<", "2.3",)
        >>> assert DebianVersionRange.split(">>2.3") == (">", "2.3",)
        >>> assert DebianVersionRange.split(">2.3") == (">", "2.3",)
        >>> assert DebianVersionRange.split("<2.3") == ("<", "2.3",)
        >>> try:
        ...     DebianVersionRange.split("~2.3")
        ...     raise Exception("ValueError should be raised")
        ... except ValueError:
        ...     pass
        """
        return split_req(
            string=string,
            comparators=cls.vers_by_native_comparators,
            strip=")(",
        )

    @classmethod
    def build_constraint_from_string(cls, string):
        """
        Return a VersionConstraint built from a single Debian version
        relationship ``string``.

        >>> vr = DebianVersionRange.build_constraint_from_string("= 5.0")
        >>> assert str(vr) == "5.0"
        >>> vr = DebianVersionRange.build_constraint_from_string("(>> 2.23)")
        >>> assert str(vr) == ">2.23"
        >>> vr = DebianVersionRange.build_constraint_from_string("<= 2.24")
        >>> assert str(vr) == "<=2.24"
        """
        comparator, version = cls.split(string)
        version = cls.version_class(version)
        return VersionConstraint(comparator=comparator, version=version)

    @classmethod
    def from_native(cls, string):
        """
        Return a VersionRange built from a ``string`` single Debian
        version relationship string.

        For example::

        >>> vr = DebianVersionRange.from_native("(= 3.5.6)")
        >>> assert str(vr) == "vers:deb/3.5.6"
        """
        return cls(constraints=[cls.build_constraint_from_string(string)])

    @classmethod
    def from_natives(cls, strings):
        """
        Return a VersionRange built from a ``strings`` list of Debian
        version relationships or a single relationship string.

        For example::

        >>> vr = DebianVersionRange.from_natives("= 3.5.6")
        >>> assert str(vr) == "vers:deb/3.5.6"

        >>> rels = ["(>= 2.8.16)"]
        >>> vr = DebianVersionRange.from_natives(rels)
        >>> assert str(vr) == "vers:deb/>=2.8.16"

        >>> rels = [">= 1:1.1.4", "(>= 2.8.16)", "<= 2.8.16-z"]
        >>> vr = DebianVersionRange.from_natives(rels)
        >>> assert str(vr) == "vers:deb/>=2.8.16|<=2.8.16-z|>=1:1.1.4"

        >>> rels = ["(>= 2:4.13.1)", "(<= 2:4.13.1-0ubuntu0.16.04.1.1~)"]
        >>> vr = DebianVersionRange.from_natives(rels)
        >>> assert str(vr) == "vers:deb/>=2:4.13.1|<=2:4.13.1-0ubuntu0.16.04.1.1~"

        >>> rels = ["= 5.0", "(>> 2.23)", "< 2.24"]
        >>> vr = DebianVersionRange.from_natives(rels)
        >>> assert str(vr) == "vers:deb/>2.23|<2.24|5.0"

        >>> rels = ["(<< 3:1.1.25~)", "(>> 2:1.1.24~)"]
        >>> vr = DebianVersionRange.from_natives(rels)
        >>> assert str(vr) == "vers:deb/>2:1.1.24~|<3:1.1.25~"
        """

        if isinstance(strings, str):
            return cls.from_native(strings)
        constraints = [cls.build_constraint_from_string(rel) for rel in strings]
        return cls(constraints=constraints)


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
        # per https://www.python.org/dev/peps/pep-0440/#compatible-release
        # For a given release identifier V.N, the compatible release clause is
        # approximately equivalent to the pair of comparison clauses:
        # >= V.N, == V.*
        "~=": None,
        # 01.01.01 is NOT equal to 1.1.1 using === which is strict string
        # equality this is a rare and eventually non-suggested approach
        "===": None,
    }

    @classmethod
    def from_native(cls, string):
        """
        Return a VersionRange built from a PyPI PEP440 version specifiers ``string``.
        Raise an a univers.versions.InvalidVersion
        """
        # TODO: environment markers are yet supported
        # TODO: handle  .* version, ~= and === operators

        if ";" in string:
            raise InvalidVersionRange(f"Unsupported PyPI environment marker: {string!r}")

        unsupported_chars = ";\\/|{}()`?'\"\t\n "
        string = "".join(string.split(" "))

        if any(c in string for c in unsupported_chars):
            raise InvalidVersionRange(
                f"Unsupported character: {unsupported_chars!r} " f"in PyPI version: {string!r}"
            )

        try:
            specifiers = SpecifierSet(string)
        except InvalidSpecifier as e:
            raise InvalidVersionRange() from e

        # Note that in PyPI all constraints apply

        constraints = []
        unsupported_messages = []
        for spec in specifiers:
            operator = spec.operator
            version = spec.version

            if operator == "~=" or operator == "===":
                msg = f"Unsupported PyPI version constraint operator: {spec!r}"
                unsupported_messages.append(msg)

            if str(version).endswith(".*"):
                msg = f"Unsupported PyPI version: {spec!r}"
                unsupported_messages.append(msg)

            try:
                version = cls.version_class(version)
                comparator = cls.vers_by_native_comparators[operator]
                constraint = VersionConstraint(comparator=comparator, version=version)
                constraints.append(constraint)
            except:
                msg = f"Invalid PyPI version: {spec!r}"
                unsupported_messages.append(msg)

        if unsupported_messages:
            raise InvalidVersionRange(*unsupported_messages)

        return cls(constraints=constraints)


class MavenVersionRange(VersionRange):
    """
    Maven version range as documented at
    https://maven.apache.org/enforcer/enforcer-rules/versionRanges.html
    """

    scheme = "maven"
    version_class = versions.MavenVersion

    @classmethod
    def from_native(cls, string):
        """
        Return a VersionRange built from a Maven version specifier ``string``.
        """

        string = "".join(string.split(" "))

        restrictions = maven.VersionRange(string).restrictions
        constraints = []

        for restriction in restrictions:
            lower_bound = restriction.lower_bound
            upper_bound = restriction.upper_bound
            lower_inclusive = restriction.lower_bound_inclusive
            upper_inclusive = restriction.upper_bound_inclusive

            if lower_bound == upper_bound:
                constraints.append(
                    VersionConstraint(comparator="=", version=cls.version_class(str(lower_bound)))
                )
                continue

            if lower_bound:
                if lower_inclusive:
                    comparator = ">="
                else:
                    comparator = ">"
                constraints.append(
                    VersionConstraint(
                        comparator=comparator,
                        version=cls.version_class(str(lower_bound)),
                    )
                )

            if upper_bound:
                if upper_inclusive:
                    comparator = "<="
                else:
                    comparator = "<"
                constraints.append(
                    VersionConstraint(
                        comparator=comparator,
                        version=cls.version_class(str(upper_bound)),
                    )
                )

        return cls(constraints=constraints)

    @classmethod
    def from_natives(cls, strings):
        if isinstance(strings, str):
            return cls.from_native(strings)
        constraints = []
        for rel in strings:
            constraints.extend(cls.from_native(rel).constraints)
        return cls(constraints=constraints)


class NugetVersionRange(MavenVersionRange):
    """
    NuGet range as in:[3.10.1,4)
    """

    scheme = "nuget"
    version_class = versions.NugetVersion


class ComposerVersionRange(VersionRange):
    """
    Composer version range as documented at
    https://getcomposer.org/doc/articles/versions.md
    """

    scheme = "composer"
    version_class = versions.ComposerVersion

    vers_by_native_comparators = {
        "==": "=",
        "<=": "<=",
        ">=": ">=",
        "<": "<",
        ">": ">",
        "=": "=",  # This is not a native composer-semver comparator, but is used in the gitlab version range for composer packages.
    }

    @classmethod
    def from_native(cls, string):
        """
        Parse a Composer version range string into a version range object.
        """
        string = string.strip()

        if string.startswith("^"):
            base_version = string[1:]
            base_version_obj = cls.version_class(base_version)
            base_parts = base_version.split(".")
            if base_parts[0] == "0":
                upper_constraint = VersionConstraint(
                    comparator="<", version=cls.version_class(f"0.{int(base_parts[1]) + 1}.0")
                )
            else:
                upper_constraint = VersionConstraint(
                    comparator="<", version=cls.version_class(f"{int(base_parts[0]) + 1}.0.0")
                )
            lower_constraint = VersionConstraint(comparator=">=", version=base_version_obj)
            return cls(constraints=[lower_constraint, upper_constraint])

        if string.startswith("~"):
            base_version = string[1:]
            base_version_obj = cls.version_class(base_version)
            base_parts = base_version.split(".")

            if len(base_parts) == 3:
                upper_constraint = VersionConstraint(
                    comparator="<",
                    version=cls.version_class(f"{base_parts[0]}.{int(base_parts[1]) + 1}.0"),
                )
            else:
                upper_constraint = VersionConstraint(
                    comparator="<", version=cls.version_class(f"{int(base_parts[0]) + 1}.0.0")
                )

            lower_constraint = VersionConstraint(comparator=">=", version=base_version_obj)
            return cls(constraints=[lower_constraint, upper_constraint])

        if ".*" in string:
            base_version = string.replace(".*", ".0")
            base_version_obj = cls.version_class(base_version)
            base_parts = base_version.split(".")
            upper_constraint = VersionConstraint(
                comparator="<",
                version=cls.version_class(f"{base_parts[0]}.{int(base_parts[1]) + 1}.0"),
            )
            lower_constraint = VersionConstraint(comparator=">=", version=base_version_obj)
            return cls(constraints=[lower_constraint, upper_constraint])

        constraints = []

        segments = string.split("||")

        for segment in segments:
            if not any(op in string for op in cls.vers_by_native_comparators):
                segment = "==" + segment
            specifiers = SpecifierSet(segment)
            for spec in specifiers:
                operator = spec.operator
                version = spec.version
                version = cls.version_class(version)
                comparator = cls.vers_by_native_comparators.get(operator, "=")
                constraint = VersionConstraint(comparator=comparator, version=version)
                constraints.append(constraint)

        return cls(constraints=constraints)


class RpmVersionRange(VersionRange):
    # http://ftp.rpm.org/api/4.4.2.2/dependencies.html
    # http://ftp.rpm.org/max-rpm/s1-rpm-depend-manual-dependencies.html
    scheme = "rpm"
    version_class = versions.RpmVersion

    vers_by_native_comparators = {
        "=": "=",
        "<=": "<=",
        ">=": ">=",
        "<": "<",
        ">": ">",
        # seen in RPM code but never seen in the doc or in the wild so far
        "<>": "!=",
        # seen in a specfile parser code
        "!=": "!=",
        "==": "=",
    }

    @classmethod
    def build_constraint_from_string(cls, string):
        """
        Return a VersionConstraint built from a single RPM version
        relationship ``string``.

        >>> vr = RpmVersionRange.build_constraint_from_string("= 5.0")
        >>> assert str(vr) == "5.0", str(vr)
        >>> vr = RpmVersionRange.build_constraint_from_string("> 2.23,")
        >>> assert str(vr) == ">2.23", str(vr)
        >>> vr = RpmVersionRange.build_constraint_from_string("<= 2.24")
        >>> assert str(vr) == "<=2.24", str(vr)
        """
        comparator, version = split_req(
            string=string,
            comparators=cls.vers_by_native_comparators,
            strip=",",
        )
        version = cls.version_class(version)
        return VersionConstraint(comparator=comparator, version=version)

    @classmethod
    def from_native(cls, string):
        """
        Return a VersionRange built from a ``string`` single RPM
        version requirement string.

        For example::

        >>> vr = RpmVersionRange.from_native("= 3.5.6")
        >>> assert str(vr) == "vers:rpm/3.5.6", str(vr)
        """
        return cls(constraints=[cls.build_constraint_from_string(string)])

    @classmethod
    def from_natives(cls, strings):
        """
        Return a VersionRange built from a ``strings`` list of RPM
        version requirements or a single requirement string.

        For example::

        >>> vr = RpmVersionRange.from_natives("= 3.5.6")
        >>> assert str(vr) == "vers:rpm/3.5.6", str(vr)

        >>> reqs = [">= 2.8.16"]
        >>> vr = RpmVersionRange.from_natives(reqs)
        >>> assert str(vr) == "vers:rpm/>=2.8.16", str(vr)

        >>> reqs = [">= 1:1.1.4", ">= 2.8.16", "<= 2.8.16-z"]
        >>> vr = RpmVersionRange.from_natives(reqs)
        >>> assert str(vr) == "vers:rpm/>=2.8.16|<=2.8.16-z|>=1:1.1.4", str(vr)

        >>> reqs = ["= 5.0", "> 2.23,", "< 2.24"]
        >>> vr = RpmVersionRange.from_natives(reqs)
        >>> assert str(vr) == "vers:rpm/>2.23|<2.24|5.0", str(vr)
        """

        if isinstance(strings, str):
            return cls.from_native(strings)
        constraints = [cls.build_constraint_from_string(rel) for rel in strings]
        return cls(constraints=constraints)


class GolangVersionRange(VersionRange):
    """
    Go modules use strict semver with pseudo numbering for Git commits.
    https://go.dev/doc/modules/version-numbers
    """

    scheme = "golang"
    version_class = versions.GolangVersion

    vers_by_native_comparators = {
        "==": "=",
        "<=": "<=",
        ">=": ">=",
        "<": "<",
        ">": ">",
        "=": "=",  # This is not a native golang-semver comparator, but is used in the gitlab version range for go packages.
    }

    @classmethod
    def from_native(cls, string):
        """
        Parse a native GoLang version range into a set of constraints.
        """
        constraints = []

        segments = string.split("||")
        for segment in segments:

            if not any(op in string for op in cls.vers_by_native_comparators):
                segment = "==" + segment

            specifiers = SpecifierSet(segment)
            for spec in specifiers:
                operator = spec.operator
                version = spec.version
                version = cls.version_class(version)
                comparator = cls.vers_by_native_comparators.get(operator, "=")
                constraint = VersionConstraint(comparator=comparator, version=version)
                constraints.append(constraint)

        return cls(constraints=constraints)

    @classmethod
    def from_natives(cls, strings):
        if isinstance(strings, str):
            return cls.from_native(strings)
        constraints = []
        for rel in strings:
            constraints.extend(cls.from_native(rel).constraints)
        return cls(constraints=constraints)


class GenericVersionRange(VersionRange):
    scheme = "generic"
    version_class = versions.SemverVersion


class ApacheVersionRange(VersionRange):
    # apache is not semver at large. And in particular we may have schemes that
    # are package name-specific
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


class AlpineLinuxVersionRange(VersionRange):
    scheme = "alpine"
    version_class = versions.AlpineLinuxVersion


class ArchLinuxVersionRange(VersionRange):
    scheme = "alpm"
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
    version_class = versions.NginxVersion

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
            return cls(
                constraints=[VersionConstraint(comparator="*", version_class=cls.version_class)]
            )

        constraints = []

        for clauses in cleaned.split(","):

            if "-" in clauses:
                # dash range
                start, _, end = clauses.partition("-")
                start_version = cls.version_class(start)
                end_version = cls.version_class(end)
                vstart = VersionConstraint(comparator=">=", version=start_version)
                vend = VersionConstraint(comparator="<=", version=end_version)
                constraints.extend([vstart, vend])

            elif "+" in clauses:
                # suffixed version
                vs = clauses.rstrip("+")
                version = cls.version_class(vs)
                if version.is_stable:
                    # we have a start and end in stable ranges
                    start_version = cls.version_class(vs)
                    end_version = cls.version_class(str(start_version.next_minor()))
                    vstart = VersionConstraint(comparator=">=", version=start_version)
                    vend = VersionConstraint(comparator="<", version=end_version)
                    constraints.extend([vstart, vend])
                else:
                    # mainline branch ranges are resolved to a single constraint
                    version = cls.version_class(vs)
                    constraint = VersionConstraint(comparator=">=", version=version)
                    constraints.append(constraint)

            else:
                # plain single version
                version = cls.version_class(clauses)
                constraint = VersionConstraint(comparator="=", version=version)
                constraints.append(constraint)

        return cls(constraints=constraints)


class OpensslVersionRange(VersionRange):
    """
    Openssl version range.
    openssl doesn't use <,>,<= or >=
    For more see 'https://www.openssl.org/news/vulnerabilities.xml'

    For example::
    >>> from univers.versions import OpensslVersion
    >>> constraints = (
    ... VersionConstraint(version=OpensslVersion("1.0.1af")),
    ... VersionConstraint(comparator="=", version=OpensslVersion("3.0.1")),
    ... VersionConstraint(comparator="=", version=OpensslVersion("1.1.1nf")),
    ... )
    >>> range = OpensslVersionRange(constraints=constraints)
    >>> assert str(range) == 'vers:openssl/1.0.1af|1.1.1nf|3.0.1'
    """

    scheme = "openssl"
    version_class = versions.OpensslVersion

    @classmethod
    def from_native(cls, string):
        cleaned = remove_spaces(string).lower()
        constraints = []
        for version in cleaned.split(","):
            version_obj = cls.version_class(version)
            constraint = VersionConstraint(comparator="=", version=version_obj)
            constraints.append(constraint)
        return cls(constraints=constraints)


class MattermostVersionRange(VersionRange):
    scheme = "mattermost"
    version_class = versions.SemverVersion


def from_gitlab_native(gitlab_scheme, string):
    purl_scheme = gitlab_scheme
    if gitlab_scheme not in PURL_TYPE_BY_GITLAB_SCHEME.values():
        purl_scheme = PURL_TYPE_BY_GITLAB_SCHEME[gitlab_scheme]

    vrc = RANGE_CLASS_BY_SCHEMES[purl_scheme]
    supported_native_implementations = [
        ConanVersionRange,
        MavenVersionRange,
        NugetVersionRange,
    ]
    if vrc in supported_native_implementations:
        return vrc.from_native(string)
    constraint_items = []
    constraints = []

    split = " "
    if purl_scheme == "pypi":
        split = ","

    # GitLab advisory for composer uses both `,` and space for separating constraints.
    # https://gitlab.com/gitlab-org/security-products/gemnasium-db/-/blob/8ba4872b659cf5a306e0d47abdd0e428948bf41c/packagist/illuminate/cookie/GHSA-2867-6rrm-38gr.yml
    # https://gitlab.com/gitlab-org/security-products/gemnasium-db/-/blob/8ba4872b659cf5a306e0d47abdd0e428948bf41c/packagist/contao-components/mediaelement/CVE-2016-4567.yml
    if purl_scheme == "composer" and "," in string:
        split = ","

    pipe_separated_constraints = string.split("||")
    for pipe_separated_constraint in pipe_separated_constraints:
        space_seperated_constraints = pipe_separated_constraint.split(split)
        constraint_items.extend(space_seperated_constraints)
    comparator = ""
    # A constraint item can be a comparator or a version or a version with comparator
    # If it's empty continue
    # If it's in `vers_by_native_comparators`, append it with the comparator and continue
    # If it's a version, make version constraint from the version and use the comparator from the previous item and make comparator empty
    # If it's a version with comparator, use split_req to get version and comparator to form constraint and make comparator empty
    for constraint_item in constraint_items:
        if not constraint_item:
            continue
        if "".join([comparator, constraint_item]) in vrc.vers_by_native_comparators:
            comparator = "".join([comparator, constraint_item])
            comparator = vrc.vers_by_native_comparators[comparator]
            continue
        if comparator:
            constraints.append(
                VersionConstraint(comparator=comparator, version=vrc.version_class(constraint_item))
            )
        else:
            comparator, version_constraint = split_req(
                constraint_item, vrc.vers_by_native_comparators, default="="
            )
            constraints.append(
                VersionConstraint(
                    comparator=comparator, version=vrc.version_class(version_constraint)
                )
            )
        comparator = ""
    return vrc(constraints=constraints)


vers_by_github_native_comparators = {
    "=": "=",
    "!=": "!=",
    "<=": "<=",
    ">=": ">=",
    "<": "<",
    ">": ">",
}


def build_constraint_from_github_advisory_string(scheme: str, string: str):
    """
    Return a VersionConstraint built from a single github-native version
    relationship ``string``.

    >>> vr = build_constraint_from_github_advisory_string("gem","<= 2.24")
    >>> assert str(vr) == "<=2.24", str(vr)
    >>> vr = build_constraint_from_github_advisory_string("pypi","< 9.0")
    >>> assert str(vr) == "<9.0", str(vr)
    >>> vr = build_constraint_from_github_advisory_string("pypi","= 9.0")
    >>> assert str(vr) == "9.0", str(vr)
    """
    vrc = RANGE_CLASS_BY_SCHEMES[scheme]
    comparator, version = split_req(
        string=string,
        comparators=vers_by_github_native_comparators,
    )
    version = vrc.version_class(version)
    return VersionConstraint(comparator=comparator, version=version)


def build_range_from_github_advisory_constraint(scheme: str, string: Union[str, List]):
    """
    Github has a special syntax for version ranges.
    For example:
    Maven native version range looks like:
    ``[1.0.0,1.0.1)``
    Github native version range looks like:
    ``>= 1.0.0, < 1.0.1``

    Return a VersionRange built from a ``string`` single or multiple github-native
    version relationship string.

    For example::

    >>> vr = build_range_from_github_advisory_constraint("maven", ">= 2.13.0, < 2.16.0")
    >>> assert str(vr) == "vers:maven/>=2.13.0|<2.16.0"
    >>> vr = build_range_from_github_advisory_constraint("gem", ">= 2.13.0, < 2.16.0")
    >>> assert str(vr) == "vers:gem/>=2.13.0|<2.16.0"
    >>> vr = build_range_from_github_advisory_constraint("pypi","< 9.0")
    >>> assert str(vr) == "vers:pypi/<9.0"
    >>> vr = build_range_from_github_advisory_constraint("pypi","= 9.0")
    >>> assert str(vr) == "vers:pypi/9.0"
    """
    if isinstance(string, str):
        string = [string]

    constraints = []
    vrc = RANGE_CLASS_BY_SCHEMES[scheme]
    for item in string:
        constraint_strings = item.split(",")

        for constraint in constraint_strings:
            constraints.append(build_constraint_from_github_advisory_string(scheme, constraint))
    return vrc(constraints=constraints)


vers_by_snyk_native_comparators = {
    "==": "=",
    "=": "=",
    "!=": "!=",
    "<=": "<=",
    ">=": ">=",
    "<": "<",
    ">": ">",
}


def split_req_bracket_notation(string):
    """
    Return a tuple of (vers comparator, version) strings given an bracket notation
    version requirement ``string`` such as "(2.3" or "3.9]"

    For example::

    >>> assert split_req_bracket_notation(" 2.3 ]") == ("<=", "2.3")
    >>> assert split_req_bracket_notation("( 3.9") == (">", "3.9")
    """
    comparators_front = {"(": ">", "[": ">="}
    comparators_rear = {")": "<", "]": "<="}

    constraint_string = remove_spaces(string).strip()

    for native_comparator, vers_comparator in comparators_front.items():
        if constraint_string.startswith(native_comparator):
            version = constraint_string.lstrip(native_comparator)
            return vers_comparator, version

    for native_comparator, vers_comparator in comparators_rear.items():
        if constraint_string.endswith(native_comparator):
            version = constraint_string.rstrip(native_comparator)
            return vers_comparator, version

    raise ValueError(f"Unknown comparator in version requirement: {string!r} ")


def build_range_from_snyk_advisory_string(scheme: str, string: Union[str, List]):
    """
    Return a VersionRange built from a ``string`` single or multiple snyk
    version relationship string.
    Snyk version range looks like:
        ">=4.0.0, <4.0.10.16"
        ">=4.1.0 <4.4.15.7"
        "[3.0.0,3.1.25)"
        "(,9.21]"
        "[1.4.5,)"

    For example::

    >>> vr = build_range_from_snyk_advisory_string("pypi", ">=4.0.0, <4.0.10")
    >>> assert str(vr) == "vers:pypi/>=4.0.0|<4.0.10"
    >>> vr = build_range_from_snyk_advisory_string("golang", ">=9.6.0-rc1 <9.8.1-rc1")
    >>> assert str(vr) == "vers:golang/>=9.6.0-rc1|<9.8.1-rc1"
    >>> vr = build_range_from_snyk_advisory_string("pypi", "(,9.21]")
    >>> assert str(vr) == "vers:pypi/<=9.21"
    """
    version_constraints = []
    vrc = RANGE_CLASS_BY_SCHEMES[scheme]

    if isinstance(string, str):
        string = [string]

    for item in string:
        delimiter = "," if "," in item else " "
        if delimiter == ",":
            snyk_constraints = item.strip().replace(" ", "")
            constraints = snyk_constraints.split(",")
        else:
            snyk_constraints = item.strip()
            constraints = snyk_constraints.split(" ")

        for constraint in constraints:
            if any(comp in constraint for comp in "[]()"):
                comparator, version = split_req_bracket_notation(string=constraint)
            else:
                comparator, version = split_req(
                    string=constraint,
                    comparators=vers_by_snyk_native_comparators,
                )
            if comparator and version:
                version = vrc.version_class(version)
                version_constraints.append(
                    VersionConstraint(
                        comparator=comparator,
                        version=version,
                    )
                )
    return vrc(constraints=version_constraints)


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
    "alpm": ArchLinuxVersionRange,
    "nginx": NginxVersionRange,
    "openssl": OpensslVersionRange,
    "mattermost": MattermostVersionRange,
    "conan": ConanVersionRange,
}

PURL_TYPE_BY_GITLAB_SCHEME = {
    "gem": "gem",
    "go": "golang",
    "maven": "maven",
    "npm": "npm",
    "nuget": "nuget",
    "pypi": "pypi",
    "packagist": "composer",
    "conan": "conan",
}
