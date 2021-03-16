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

import re
from packaging import version
from functools import total_ordering


def remove_spaces(string):
    return string.replace(" ", "")


class BaseVersion:
    # each version value should be comparable e.g. implement functools.total_ordering

    scheme = None
    value = None

    def validate(self):
        """
        Validate that the version is valid for its scheme
        """
        raise NotImplementedError


@total_ordering
class PYPIVersion(BaseVersion):
    scheme = "pypi"

    def __init__(self, version_string):
        # TODO the `Version` class's constructor also does the same validation
        # but it has a fallback option by creating an object of version.LegacyVersion class.
        # Avoid the double validation and the fallback.

        self.validate(version_string)
        self.value = version.Version(version_string)

    @staticmethod
    def validate(version_string):
        match = version.Version._regex.search(version_string)
        if not match:
            raise InvalidVersion(f"Invalid version: '{version_string}'")

    def __eq__(self, other):
        # TBD: Should this verify the type of `other`
        return self.value.__eq__(other.value)

    def __lt__(self, other):
        return self.value.__lt__(other.value)


class InvalidVersion(ValueError):
    pass


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


class DebianVersion:
    scheme = "debian"

    def validate(self):
        """
        Validate that the version is valid for its scheme
        """
        # debian implementation ...


class SemverVersion:
    scheme = "semver"

    def validate(self):
        """
        Validate that the version is valid for its scheme
        """
        # node-semver implementation ...


versions_classes_by_scheme = {
    "generic": GenericVersion,
    "semver": SemverVersion,
    "debian": DebianVersion,
    "pypi": PYPIVersion,
    # ....
}


def parse_version(version):
    """
    Return a Version object from a scheme-prefixed string
    """
    if ":" in version:
        scheme, _, version = version.partition(":")
    else:
        scheme = "generic"

    cls = versions_classes_by_scheme[scheme]
    return cls(version)


class VersionRange:
    # one of <> >= =< or != or =
    operator = ""
    value = ""

    def __init__(self, version_range_string):
        version_range_string = remove_spaces(version_range_string)
        _, self.operator, self.value = self.partition_operator(version_range_string)
        self.validate()

    def validate(self):

        # self.operator will always have a valid value
        if not self.value:
            raise ValueError("Version range has no bounds")

    @staticmethod
    def partition_operator(version_range_string):

        if ">=" in version_range_string:
            return version_range_string.partition(">=")

        if "<=" in version_range_string:
            return version_range_string.partition("<=")

        if "!=" in version_range_string:
            return version_range_string.partition("!=")

        if "<" in version_range_string:
            return version_range_string.partition("<")

        if ">" in version_range_string:
            return version_range_string.partition(">")

        if "=" in version_range_string:
            return version_range_string.partition("=")

        return "", "=", version_range_string

    def __contains__(self, version):
        version_class = versions_classes_by_scheme[version.scheme]
        version_object = version_class(self.value)

        # TODO: this can be made more concise by using `eval`. Research whether that is safe
        if self.operator == ">=":
            return version >= version_object

        if self.operator == "<=":
            return version <= version_object

        if self.operator == "!=":
            return version != version_object

        if self.operator == "<":
            return version < version_object

        if self.operator == ">":
            return version > version_object

        return version == version_object

    def __str__(self):
        return f"{self.operator}{self.value}"


class VersionSpecifier:

    scheme = ""
    ranges = []

    @classmethod
    def from_version_spec_string(cls, version_spec_string):
        """
        Return a VersionSpecifier built from a version spec string, prefixed by
        a scheme such as "semver:1.2.3,>=2.0.0"
        """
        scheme, _, version_range_expressions = version_spec_string.partition(":")
        if not scheme:
            raise ValueError(f"{version_spec_string} is not prefixed by scheme")

        if not version_range_expressions:
            raise ValueError(f"{version_spec_string} contains no version range")

        return from_scheme_version_spec_string(scheme, version_range_expressions)

    @classmethod
    def from_scheme_version_spec_string(cls, scheme, value):
        """
        Return a VersionSpecifier built from a scheme-specific version spec string and a scheme string.
        """

        # TODO: Handle wildcards, carets, tilde here. Convert them into something sane
        value = remove_spaces(value)
        version_ranges = value.split(",")
        ranges = []
        for version_range in version_ranges:
            _, operator, value = VersionRange.partition_operator(version_range)
            version_class = versions_classes_by_scheme[scheme]
            version_class.validate(value)
            ranges.append(VersionRange(version_range))

        vs = cls()
        vs.ranges = ranges
        vs.scheme = scheme
        return vs

    def __str__(self):
        """
        Return this VersionSpecifier string using a canonical representation and our universal syntax.
        """
        # TODO: sort to make canonic
        ranges = ",".join(self.ranges)

        return f"{self.scheme}:{ranges}"

    def __contains__(self, version):
        """
        Return True if this VersionSpecifier contains the ``version``
        Version object or scheme-prefixed version string. A version is contained
        in a VersionSpecifier if it satisfies all its Range.
        """
        if isinstance(version, str):
            version = parse_version(version)

        return all([version in version_range for version_range in self.ranges])
