#
# Copyright (c) nexB Inc. and others.
# SPDX-License-Identifier: Apache-2.0
#
# Visit https://aboutcode.org and https://github.com/nexB/univers for support and download.

from functools import total_ordering

import attr
import semantic_version
from packaging import version as packaging_version

from univers import arch
from univers import debian
from univers import gem
from univers import gentoo
from univers import maven
from univers import rpm
from univers.utils import remove_spaces

"""
Version classes encapsulating the details of each version syntax.
For instance semver is a version syntax. Python and Debian use another syntax.

Each subclass primary responsibility to is be comparable and orderable
"""

# TODO: Add mozilla versions https://github.com/mozilla-releng/mozilla-version
# TODO: Add conda versions https://github.com/conda/conda/blob/master/conda/models/version.py
#       and https://docs.conda.io/projects/conda-build/en/latest/resources/package-spec.html#build-version-spec


class InvalidVersion(ValueError):
    pass


def is_valid_alpine_version(s):
    """
    Return True is the string `s` is a valid Alpine version.
    We do not support yet version strings that start with
    non-significant zeros.
    For example:
    >>> is_valid_alpine_version("006")
    False
    >>> is_valid_alpine_version("1.2.3")
    True
    >>> is_valid_alpine_version("02-r1")
    False
    """
    left, _, _ = s.partition(".")
    # hanlde the suffix case
    left, _, _ = left.partition("-")
    if not left.isdigit():
        return True
    i = int(left)
    return str(i) == left


@attr.s(frozen=True, order=False, hash=True)
class Version:
    """
    Base version mixin to subclass for each version syntax implementation.

    Each version subclass is:

    - immutable and hashable
    - comparable and orderable e.g., such as implementing all rich comparison
      operators or implementing functools.total_ordering. The default is to
      compare the value as-is.
    """

    # the original string used to build this Version
    string = attr.ib(type=str)

    # the normalized string for this Version, stored without spaces and
    # lowercased. Any leading v is removed too.
    normalized_string = attr.ib(type=str, default=None, repr=False)

    # a comparable scheme-specific version object constructed from the version string
    value = attr.ib(default=None, repr=False)

    def __attrs_post_init__(self):
        normalized_string = self.normalize(self.string)
        if not self.is_valid(normalized_string):
            raise InvalidVersion(f"{self.string!r} is not a valid {self.__class__!r}")

        # Set the normalized string as default value

        # Notes: setattr is used because this is an immutable frozen instance.
        # See https://www.attrs.org/en/stable/init.html?#post-init
        object.__setattr__(self, "normalized_string", normalized_string)
        value = self.build_value(normalized_string)
        object.__setattr__(self, "value", value)

    @classmethod
    def is_valid(cls, string):
        """
        Return True if the ``string`` is a valid version for its scheme or False
        if not valid. The empty string, None, False and 0 are considered invalid.
        Subclasses should implement this.
        """
        return bool(string)

    @classmethod
    def normalize(cls, string):
        """
        Return a normalized version string from ``string ``. Subclass can override.
        """
        # FIXME: Is removing spaces and strip v the right thing to do?
        return remove_spaces(string).rstrip("v ").strip()

    @classmethod
    def build_value(self, string):
        """
        Return a wrapped version "value" object for a version ``string``.
        Subclasses can override. The default is a no-op and returns the string
        as-is, and is called by default at init time with the computed
        normalized_string.
        """
        return string

    def satisfies(self, constraint):
        """
        Return True is this Version satisfies the ``constraint``
        VersionConstraint. Satisfying means that this version is "within" the
        ``constraint``.
        """
        return self in constraint

    def __str__(self):
        return str(self.value)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.value.__eq__(other.value)

    def __lt__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.value.__lt__(other.value)

    def __gt__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.value.__gt__(other.value)

    def __le__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.value.__le__(other.value)

    def __ge__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.value.__ge__(other.value)


@attr.s(frozen=True, order=False, hash=True)
class GenericVersion(Version):
    @classmethod
    def is_valid(cls, string):
        # generic implementation ...
        # TODO: Should use
        # https://github.com/repology/libversion/blob/master/doc/ALGORITHM.md#core-algorithm
        #  Version is split into separate all-alphabetic or all-numeric
        #  components.
        # All other characters are treated as separators. Empty components are
        # not generated.
        #   10.2alpha3..patch.4. → 10, 2, alpha, 3, patch, 4
        return super(GenericVersion, cls).is_valid(string)


@attr.s(frozen=True, order=False, eq=False, hash=True)
class PypiVersion(Version):
    """
    Python PEP 440 version as implemented in packaging with fallback to "legacy"
    """

    # TODO: ensure we deal with triple equal

    @classmethod
    def build_value(cls, string):
        """
        Return a packaging.version.LegacyVersion or packaging.version.Version
        """
        return packaging_version.Version(string)

    @classmethod
    def is_valid(cls, string):
        try:
            # Note: we consider only modern pep440 versions as valid. legacy
            # will fail validation for now.
            cls.build_value(string)
            return True
        except packaging_version.InvalidVersion:
            return False

        return False


@attr.s(frozen=True, order=False, eq=False, hash=True)
class SemverVersion(Version):
    """
    Strict semver v2.0 with 3 segments.
    """

    @classmethod
    def build_value(cls, string):
        return semantic_version.Version.coerce(string)

    @classmethod
    def is_valid(cls, string):
        try:
            cls.build_value(string)
            return True
        except ValueError:
            return False


@attr.s(frozen=True, order=False, eq=False, hash=True)
class RubygemsVersion(Version):
    """
    Rubygems encourages semver version but does not enforce it.
    Rubygems supports 4 or more segments in versions such
    as with https://rubygems.org/gems/rails/versions/5.0.0.1
    """

    @classmethod
    def build_value(cls, string):
        return gem.GemVersion(string)

    @classmethod
    def is_valid(cls, string):
        return gem.GemVersion.is_correct(string)


@attr.s(frozen=True, order=False, eq=False, hash=True)
class ArchLinuxVersion(Version):
    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return arch.vercmp(self.value, other.value) == 0

    def __lt__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return arch.vercmp(self.value, other.value) < 0

    def __gt__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return arch.vercmp(self.value, other.value) > 0

    def __le__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return arch.vercmp(self.value, other.value) <= 0

    def __ge__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return arch.vercmp(self.value, other.value) >= 0


@attr.s(frozen=True, order=False, eq=False, hash=True)
class DebianVersion(Version):
    @classmethod
    def build_value(cls, string):
        return debian.Version.from_string(string)

    @classmethod
    def is_valid(cls, string):
        return debian.Version.is_valid(string)


@attr.s(frozen=True, order=False, eq=False, hash=True)
class MavenVersion(Version):
    # See https://maven.apache.org/enforcer/enforcer-rules/versionRanges.html
    # https://github.com/apache/maven/tree/master/maven-artifact/src/main/java/org/apache/maven/artifact/versioning

    @classmethod
    def build_value(cls, string):
        return maven.Version(string)


@attr.s(frozen=True, order=False, eq=False, hash=True)
class NugetVersion(SemverVersion):
    # See https://docs.microsoft.com/en-us/nuget/concepts/package-versioning
    pass


@attr.s(frozen=True, order=False, eq=False, hash=True)
class RpmVersion(Version):
    """
    Represent an RPM version.

    For example::

    # 1:1.1.4|>=2.8.16|<=2.8.16-z
    """

    @classmethod
    def build_value(cls, string):
        return rpm.RpmVersion.from_string(string)


@total_ordering
@attr.s(frozen=True, order=False, eq=False, hash=True)
class GentooVersion(Version):
    @classmethod
    def is_valid(cls, string):
        return gentoo.is_valid(string)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return gentoo.vercmp(self.value, other.value) == 0

    def __lt__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return gentoo.vercmp(self.value, other.value) == -1


@attr.s(frozen=True, order=False, eq=False, hash=True)
class AlpineLinuxVersion(Version):
    @classmethod
    def is_valid(cls, string):
        return is_valid_alpine_version(string) and gentoo.is_valid(string)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return gentoo.vercmp(self.value, other.value) == 0

    def __lt__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return gentoo.vercmp(self.value, other.value) < 0

    def __gt__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return gentoo.vercmp(self.value, other.value) > 0


@attr.s(frozen=True, order=False, eq=False, hash=True)
class LegacyOpensslVersion(Version):
    """
    Represent an Legacy Openssl Version.

    For example::
    >>> LegacyOpensslVersion("1.0.1f")
    LegacyOpensslVersion(string='1.0.1f')
    >>> LegacyOpensslVersion("1.0.2ac")
    LegacyOpensslVersion(string='1.0.2ac')
    >>> LegacyOpensslVersion("1.0.2a")
    LegacyOpensslVersion(string='1.0.2a')
    >>> LegacyOpensslVersion("3.0.2")
    Traceback (most recent call last):
        ...
    univers.versions.InvalidVersion: '3.0.2' is not a valid <class 'univers.versions.LegacyOpensslVersion'>
    """

    @classmethod
    def is_valid(cls, string):
        return bool(cls.parse(string))

    @classmethod
    def parse(cls, string):
        """
        Return a four-tuple of (major, minor, build, patch) version segments where
        major, minor, build are integers and patch is a string possibly empty.
        Return False if this is not a valid LegacyOpensslVersion.

        For example::
        >>> LegacyOpensslVersion.parse("1.0.1f")
        (1, 0, 1, 'f')
        >>> LegacyOpensslVersion.parse("1.0.2ac")
        (1, 0, 2, 'ac')
        >>> LegacyOpensslVersion.parse("2.0.2az")
        False
        """

        # All known legacy base OpenSSL versions
        all_legacy_base = (
            "0.9.1",
            "0.9.2",
            "0.9.3",
            "0.9.4",
            "0.9.5",
            "0.9.6",
            "0.9.7",
            "0.9.8",
            "1.0.0",
            "1.0.1",
            "1.0.2",
            "1.1.0",
            "1.1.1",
        )
        if not string.startswith(all_legacy_base):
            return False

        segments = string.split(".")
        if not len(segments) == 3:
            return False
        major, minor, build = segments
        major = int(major)
        minor = int(minor)
        if build.isdigit():
            build = int(build)
            patch = ""
        else:
            patch = build[1:]
            build = int(build[0])
            if patch[0].isdigit():
                return False
        return major, minor, build, patch

    @classmethod
    def build_value(cls, string):
        return cls.parse(string)

    def __str__(self):
        return f"{self.value[0]}.{self.value[1]}.{self.value[2]}{self.value[3]}"


@attr.s(frozen=True, order=False, eq=False, hash=True)
class OpensslVersion(Version):
    """
    Internally tracks two types of openssl versions
        - LegacyOpensslVersion for versions before version 3.0.0 such as 1.0.1g
        - Semver for versions from 3.0.0 and up
    For example::
    >>> old = OpensslVersion("1.1.0f")
    >>> new = OpensslVersion("3.0.1")
    >>> assert old == OpensslVersion(string="1.1.0f")
    >>> assert new == OpensslVersion(string="3.0.1")
    >>> assert old.value == LegacyOpensslVersion(string="1.1.0f")
    >>> assert new.value == SemverVersion(string="3.0.1")
    >>> OpensslVersion("1.2.4fg")
    Traceback (most recent call last):
        ...
    univers.versions.InvalidVersion: '1.2.4fg' is not a valid <class 'univers.versions.OpensslVersion'>
    """

    @classmethod
    def is_valid(cls, string):
        return cls.is_valid_new(string) or cls.is_valid_legacy(string)

    @classmethod
    def build_value(cls, string):
        """
        Return a wrapped version "value" object depending on
        whether version is legacy or semver.
        """
        if cls.is_valid_legacy(string):
            return LegacyOpensslVersion(string)
        if cls.is_valid_new(string):
            return SemverVersion(string)

    @classmethod
    def is_valid_new(cls, string):
        """
        Check the validity of new Openssl Version.

        For example::
        >>> OpensslVersion.is_valid_new("1.0.1f")
        False
        >>> OpensslVersion.is_valid_new("3.0.0")
        True
        >>> OpensslVersion.is_valid_new("3.0.2")
        True
        """
        if SemverVersion.is_valid(string):
            sem = semantic_version.Version.coerce(string)
            return sem.major >= 3

    @classmethod
    def is_valid_legacy(cls, string):
        return LegacyOpensslVersion.is_valid(string)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        if not isinstance(other.value, self.value.__class__):
            return NotImplemented
        return self.value.__eq__(other.value)

    def __lt__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        if isinstance(other.value, self.value.__class__):
            return self.value.__lt__(other.value)
        # By construction legacy version is always behind Semver
        return isinstance(self.value, LegacyOpensslVersion)

    def __gt__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        if isinstance(other.value, self.value.__class__):
            return self.value.__gt__(other.value)
        # By construction semver version is always ahead of legacy
        return isinstance(self.value, SemverVersion)

    def __le__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        if isinstance(other.value, self.value.__class__):
            return self.value.__le__(other.value)
        # version value are of diff type, then legacy one is always behind semver
        return isinstance(self.value, LegacyOpensslVersion)

    def __ge__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        if isinstance(other.value, self.value.__class__):
            return self.value.__ge__(other.value)
        # version value are of diff type, then semver one is always ahead of legacy
        return isinstance(self.value, SemverVersion)
