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
