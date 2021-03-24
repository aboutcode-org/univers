# Copyright (c) nexB Inc. and others.
# SPDX-License-Identifier: Apache-2.0
#
# Visit https://aboutcode.org and https://github.com/nexB/ for support and download.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from functools import total_ordering
from packaging import version as pypi_version

import semantic_version
from pymaven import Version as _MavenVersion

from universal_versions.utils import remove_spaces


class InvalidVersion(ValueError):
    pass


class BaseVersion:
    # each version value should be comparable e.g. implement functools.total_ordering

    scheme = None
    value = None

    def validate(self):
        """
        Validate that the version is valid for its scheme
        """
        raise NotImplementedError

    def __str__(self):
        return f"{self.scheme}:{self.value}"


@total_ordering
class PYPIVersion(BaseVersion):
    scheme = "pypi"

    def __init__(self, version_string):
        # TODO the `pypi_version.Version` class's constructor also does the same validation
        # but it has a fallback option by creating an object of pypi_version.LegacyVersion class.
        # Avoid the double validation and the fallback.

        self.validate(version_string)
        self.value = pypi_version.Version(version_string)

    @staticmethod
    def validate(version_string):
        match = pypi_version.Version._regex.search(version_string)
        if not match:
            raise InvalidVersion(f"Invalid version: '{version_string}'")

    def __eq__(self, other):
        # TBD: Should this verify the type of `other`
        return self.value.__eq__(other.value)

    def __lt__(self, other):
        return self.value.__lt__(other.value)


class GenericVersion:
    scheme = "generic"

    def validate(self):
        """
        Validate that the version is valid for its scheme
        """
        # generic implementation ...
        # use 1. of https://github.com/repology/libversion/blob/master/doc/ALGORITHM.md#core-algorithm
        #  Version is split into separate all-alphabetic or all-numeric components. All other characters are treated as separators. Empty components are not generated.
        #     10.2alpha3..patch.4. → 10, 2, alpha, 3, patch, 4


class DebianVersion(BaseVersion):
    scheme = "debian"

    def __init__(self, version_string):
        self.validate(version_string)
        self.value = version_string

    @staticmethod
    def validate(version_string):
        """
        Validate that the version is valid for its scheme
        """
        # debian implementation ...
        DebianVersion.get_epoch(version_string)

    @staticmethod
    def get_digits(revision_str):
        """Return a tuple of the first integer characters of a revision (which
        may be empty) and the remains."""
        # If the string is empty, return (0,'')
        if not revision_str:
            return 0, ""
        # get the index of the first non-digit
        for i, char in enumerate(revision_str):
            if not char.isdigit():
                if i == 0:
                    return 0, revision_str
                return int(revision_str[0:i]), revision_str[i:]
        # string is entirely digits
        return int(revision_str), ""

    @staticmethod
    def get_alphas(revision_str):
        """Return a tuple of the first non-digit characters of a revision (which
        may be empty) and the remaining characters."""
        # get the index of the first digit
        for i, char in enumerate(revision_str):
            if char.isdigit():
                if i == 0:
                    return "", revision_str
                return revision_str[0:i], revision_str[i:]
        # string is entirely alphas
        return revision_str, ""

    @staticmethod
    def listify(revision_str):
        """Split a revision string into a list of alternating between strings and
        numbers, padded on either end to always be "str, int, str, int..." and
        always be of even length.  This allows us to trivially implement the
        comparison algorithm described at section 5.6.12 in:
        https://www.debian.org/doc/debian-policy/ch-controlfields.html#version
        """
        result = []
        while revision_str:
            rev_1, remains = DebianVersion.get_alphas(revision_str)
            rev_2, remains = DebianVersion.get_digits(remains)
            result.extend([rev_1, rev_2])
            revision_str = remains
        return result

    @staticmethod
    def get_upstream(version_str):
        """Given a version string that could potentially contain both an upstream
        revision and a debian revision, return a tuple of both.  If there is no
        debian revision, return 0 as the second tuple element."""
        try:
            d_index = version_str.rindex("-")
        except ValueError:
            # no hyphens means no debian version, also valid.
            return version_str, "0"

        return version_str[0:d_index], version_str[d_index + 1 :]

    @staticmethod
    def get_epoch(version_str):
        """Parse the epoch out of a package version string.
        Return (epoch, version); epoch is zero if not found."""
        try:
            # there could be more than one colon,
            # but we only care about the first
            e_index = version_str.index(":")
        except ValueError:
            # no colons means no epoch; that's valid, man
            return 0, version_str

        try:
            epoch = int(version_str[0:e_index])
        except ValueError:
            raise ValueError(
                "Corrupt DebianVersion version %s: epochs can only be ints, and "
                "epochless versions cannot use the colon character." % version_str
            )

        return epoch, version_str[e_index + 1 :]

    @staticmethod
    def split_full_version(version_str):
        """Split a full version string into epoch, upstream version and
        debian revision.
        :param: version_str
        :returns: tuple"""
        epoch, full_ver = DebianVersion.get_epoch(version_str)
        upstream_rev, debian_rev = DebianVersion.get_upstream(full_ver)
        return epoch, upstream_rev, debian_rev

    @staticmethod
    def dstringcmp(a, b):
        """debian package version string section lexical sort algorithm
        "The lexical comparison is a comparison of ASCII values modified so
        that all the letters sort earlier than all the non-letters and so that
        a tilde sorts before anything, even the end of a part."
        """

        if a == b:
            return 0
        try:
            for i, char in enumerate(a):
                if char == b[i]:
                    continue
                # "a tilde sorts before anything, even the end of a part"
                # (emptyness)
                if char == "~":
                    return -1
                if b[i] == "~":
                    return 1
                # "all the letters sort earlier than all the non-letters"
                if char.isalpha() and not b[i].isalpha():
                    return -1
                if not char.isalpha() and b[i].isalpha():
                    return 1
                # otherwise lexical sort
                if ord(char) > ord(b[i]):
                    return 1
                if ord(char) < ord(b[i]):
                    return -1
        except IndexError:
            # a is longer than b but otherwise equal, hence greater
            # ...except for goddamn tildes
            if char == "~":
                return -1
            return 1
        # if we get here, a is shorter than b but otherwise equal, hence lesser
        # ...except for goddamn tildes
        if b[len(a)] == "~":
            return 1
        return -1

    @staticmethod
    def compare_revision_strings(rev1, rev2):
        """Compare two debian revision strings as described at
        https://www.debian.org/doc/debian-policy/ch-controlfields.html#version
        """
        # TODO(memory): this function now fails pylint R0912 too-many-branches
        if rev1 == rev2:
            return 0
        # listify pads results so that we will always be comparing ints to ints
        # and strings to strings (at least until we fall off the end of a list)
        list1 = DebianVersion.listify(rev1)
        list2 = DebianVersion.listify(rev2)
        if list1 == list2:
            return 0
        try:
            for i, item in enumerate(list1):
                # explicitly raise IndexError if we've fallen off the edge of list2
                if i >= len(list2):
                    raise IndexError
                # just in case
                if not isinstance(item, list2[i].__class__):
                    raise ValueError(
                        "Cannot compare %s to %s, something has gone horribly "
                        "awry." % (item, list2[i])
                    )
                # if the items are equal, next
                if item == list2[i]:
                    continue
                # numeric comparison
                if isinstance(item, int):
                    if item > list2[i]:
                        return 1
                    if item < list2[i]:
                        return -1
                else:
                    # string comparison
                    return DebianVersion.dstringcmp(item, list2[i])
        except IndexError:
            # rev1 is longer than rev2 but otherwise equal, hence greater
            # ...except for goddamn tildes
            if list1[len(list2)][0][0] == "~":
                return -1
            return 1
        # rev1 is shorter than rev2 but otherwise equal, hence lesser
        # ...except for goddamn tildes
        if list2[len(list1)][0][0] == "~":
            return 1
        return -1

    @staticmethod
    def compare_versions(ver1, ver2):
        """Function to compare two Debian package version strings,
        suitable for passing to list.sort() and friends."""
        if ver1 == ver2:
            return 0

        # note the string conversion: the debian policy here explicitly
        # specifies ASCII string comparisons, so if you are mad enough to
        # actually cram unicode characters into your package name, you are on
        # your own.
        epoch1, upstream1, debian1 = DebianVersion.split_full_version(str(ver1))
        epoch2, upstream2, debian2 = DebianVersion.split_full_version(str(ver2))

        # if epochs differ, immediately return the newer one
        if epoch1 < epoch2:
            return -1
        if epoch1 > epoch2:
            return 1

        # then, compare the upstream versions
        upstr_res = DebianVersion.compare_revision_strings(upstream1, upstream2)
        if upstr_res != 0:
            return upstr_res

        debian_res = DebianVersion.compare_revision_strings(debian1, debian2)
        if debian_res != 0:
            return debian_res

        # at this point, the versions are equal, but due to an interpolated
        # zero in either the epoch or the debian version
        return 0


@total_ordering
class SemverVersion(BaseVersion):
    scheme = "semver"

    def __init__(self, version_string):
        # self.validate(version_string)
        version_string = version_string.lstrip("v")
        self.value = semantic_version.Version(version_string)

    @staticmethod
    def validate(version_string):
        pass
        # try:
        #     semantic_version.validate(version_string)
        # except ValueError:
        #     raise ValueError(f"Invalid version {version_string}")

    def __eq__(self, other):
        # TBD: Should this verify the type of `other`
        return self.value.__eq__(other.value)

    def __lt__(self, other):
        return self.value.__lt__(other.value)


@total_ordering
class MavenVersion(BaseVersion):
    scheme = "maven"

    def __init__(self, version_string):
        version_string = remove_spaces(version_string)
        self.value = _MavenVersion(version_string)

    @staticmethod
    def validate(version_string):
        # Defined for compatibility
        pass

    def __eq__(self, other):
        return self.value.__eq__(other.value)

    def __lt__(self, other):
        return self.value.__lt__(other.value)


class NugetVersion(MavenVersion):
    scheme = "nuget"
    pass


version_class_by_scheme = {
    "generic": GenericVersion,
    "semver": SemverVersion,
    "debian": DebianVersion,
    "pypi": PYPIVersion,
    "maven": MavenVersion,
    "nuget": NugetVersion,
}

version_class_by_package_type = {
    "generic": GenericVersion,
    "deb": DebianVersion,
    "pypi": PYPIVersion,
    "maven": MavenVersion,
    "nuget": NugetVersion,
    "composer": SemverVersion,
    "npm": SemverVersion,
    "gem": SemverVersion,
}


def validate_scheme(scheme):
    if scheme not in version_class_by_scheme:
        raise ValueError(f"Invalid scheme {scheme}")


def parse_version(version):
    """
    Return a Version object from a scheme-prefixed string
    """
    if ":" in version:
        scheme, _, version = version.partition(":")
    else:
        scheme = "generic"

    cls = version_class_by_scheme[scheme]
    return cls(version)
