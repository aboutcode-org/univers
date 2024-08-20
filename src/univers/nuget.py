# SPDX-License-Identifier: Apache-2.0
# Nuget version utility originally from:
# https://raw.githubusercontent.com/google/osv/f5647ad2f746685b08debfba0293e442f2fb9945/lib/osv/nuget.py
# Copyright 2022 Google LLC
# modified by nexB and others for integration in the Univers library
#
# Visit https://aboutcode.org and https://github.com/aboutcode-org/univers for support and download.

import functools
import re

import semver

_PAD_WIDTH = 8
_FAKE_PRE_WIDTH = 16


def _strip_leading_v(version):
    """Strip leading v from the version, if any."""
    # Versions starting with "v" aren't valid SemVer, but we handle them just in
    # case.
    if version.startswith("v"):
        return version[1:]

    return version


def _remove_leading_zero(component):
    """Remove leading zeros from a component."""
    if component[0] == ".":
        return "." + str(int(component[1:]))

    return str(int(component))


def coerce(version):
    """Coerce a potentially invalid semver into valid semver."""
    version = _strip_leading_v(version)
    version_pattern = re.compile(r"^(\d+)(\.\d+)?(\.\d+)?(.*)$")
    match = version_pattern.match(version)
    if not match:
        return version

    return (
        _remove_leading_zero(match.group(1))
        + _remove_leading_zero(match.group(2) or ".0")
        + _remove_leading_zero(match.group(3) or ".0")
        + match.group(4)
    )


def is_valid(version):
    """Returns whether or not the version is a valid semver."""
    return semver.VersionInfo.isvalid(_strip_leading_v(version))


def parse(version):
    """Parse a SemVer."""
    return semver.VersionInfo.parse(coerce(version))


def normalize(version):
    """Normalize semver version for indexing (to allow for lexical
    sorting/filtering)."""
    version = parse(version)

    # Precedence rules: https://semver.org/#spec-item-11

    # 1. Precedence MUST be calculated by separating the version into major,
    # minor, patch and pre-release identifiers in that order (Build metadata does
    # not figure into precedence).
    #
    # Normalization: Per spec build metadata is ignored.

    # 2. Precedence is determined by the first difference when comparing each of
    # these identifiers from left to right as follows: Major, minor, and patch
    # versions are always compared numerically.
    #
    # Normalization: Pad the components with '0' to allow for lexical ordering of
    # numbers.
    core_parts = "{}.{}.{}".format(
        str(version.major).rjust(_PAD_WIDTH, "0"),
        str(version.minor).rjust(_PAD_WIDTH, "0"),
        str(version.patch).rjust(_PAD_WIDTH, "0"),
    )

    # 3. When major, minor, and patch are equal, a pre-release version has lower
    # precedence than a normal version:
    #
    # Normalization: Attach a very long fake prerelease version that is most
    # likely to come after any real prelease version.
    if not version.prerelease:
        pre = "z" * _FAKE_PRE_WIDTH
        return f"{core_parts}-{pre}"

    # 4. Precedence for two pre-release versions with the same major, minor, and
    # patch version MUST be determined by comparing each dot separated identifier
    # from left to right until a difference is found as follows:
    #
    # Normalization: Pad the components.
    pre_components = []
    for component in version.prerelease.split("."):
        # 3. Numeric identifiers always have lower precedence than non-numeric
        # identifiers.
        #
        # Normalization: Pad numeric components with '0', and prefix alphanumeric
        # with a single '1' (to ensure they always come after).
        if component.isdigit():
            # 1. Identifiers consisting of only digits are compared numerically.
            pre_components.append(component.rjust(_PAD_WIDTH, "0"))
        else:
            # 2. Identifiers with letters or hyphens are compared lexically in ASCII
            # sort order.
            pre_components.append("1" + component)

    # 4. A larger set of pre-release fields has a higher precedence than a smaller
    # set, if all of the preceding identifiers are equal.
    #
    # Consistent with lexical sorting after normalization.

    pre = ".".join(pre_components)
    return f"{core_parts}-{pre}"


def _extract_revision(str_version):
    """
    Extract revision from ``str_version`` and return a tuple of:
        (dotted version string without revision, revision integer).
    The revision is the 4th numeric dotted component of a NuGet version.
    """
    # e.g. '1.0.0.0-prerelease'
    # note: each match group contains its leading dot.
    pattern = re.compile(r"^(\d+)(\.\d+)(\.\d+)(\.\d+)(.*)")
    match = pattern.match(str_version)
    if not match:
        return str_version, 0

    return (
        "".join((match.group(1), match.group(2), match.group(3), match.group(5))),
        int(match.group(4)[1:]),
    )


class InvalidNuGetVersion(Exception):
    pass


@functools.total_ordering
class Version:
    """NuGet version."""

    def __init__(self, base_semver, revision=0):
        self._base_semver = base_semver
        if self._base_semver.prerelease:
            # TODO: why lowercasing this and not the build and why here and now?
            self._base_semver = self._base_semver.replace(prerelease=base_semver.prerelease.lower())
        self._revision = revision or 0
        self._original_version = None

    def __eq__(self, other):
        return (
            isinstance(other, Version)
            and self._base_semver == other._base_semver
            and self._revision == other._revision
        )

    def __lt__(self, other):
        if not isinstance(other, Version):
            return NotImplemented
        if self._base_semver.replace(prerelease="") == other._base_semver.replace(prerelease=""):
            # If the first three components are the same, compare the revision.
            if self._revision != other._revision:
                return self._revision < other._revision

        # Revision is the same, so ignore it for comparison purposes.
        return self._base_semver < other._base_semver

    def __hash__(self):
        return hash(
            (
                self._base_semver.to_tuple(),
                self._revision,
            )
        )

    @classmethod
    def from_string(cls, str_version):
        if not str_version:
            return

        str_version = str_version.strip()
        if " " in str_version:
            raise InvalidNuGetVersion(f"version cannot contain spaces: {str_version}")

        if not any(c.isdigit() for c in str_version):
            raise InvalidNuGetVersion(f"version does not contain any digit: {str_version}")

        original = str_version
        str_version = coerce(str_version)
        str_version, revision = _extract_revision(str_version)
        vers = Version(base_semver=parse(str_version), revision=revision)
        vers._original_version = original
        return vers

    def __repr__(self):
        return f"Version<{self.to_string()}>"

    def to_string(self, with_empty_revision=False, include_prerelease=True, include_build=True):
        major = self.major or "0"
        minor = self.minor or "0"
        patch = self.patch or "0"

        if with_empty_revision:
            revision = self.revision and f".{self.revision}" or ".0"
        else:
            revision = self.revision and f".{self.revision}" or ""

        if include_prerelease:
            prerelease = self.prerelease and f"-{self.prerelease}" or ""
        else:
            prerelease = ""
        if include_build:
            build = self.build and f"+{self.build}" or ""
        else:
            build = ""

        return f"{major}.{minor}.{patch}{revision}{prerelease}{build}"

    def __str__(self):
        return self.to_string(
            with_empty_revision=False, include_prerelease=True, include_build=True
        )

    @property
    def base_version(self):
        """
        Return the base version dotted string composed of the four numerical
        segments including revision and ignoring prerelease and build.
        """
        return self.to_string(
            with_empty_revision=True, include_prerelease=False, include_build=False
        )

    @property
    def major(self):
        return self._base_semver.major

    @property
    def minor(self):
        return self._base_semver.minor

    @property
    def patch(self):
        return self._base_semver.patch

    @property
    def revision(self):
        return self._revision

    @property
    def prerelease(self):
        return self._base_semver.prerelease and self._base_semver.prerelease or ""

    @property
    def build(self):
        return self._base_semver.build and self._base_semver.build or ""
