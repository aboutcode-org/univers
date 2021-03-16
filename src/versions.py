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

    def validate(self, version_string):
        match = version.Version._regex.search(version_string)
        if not match:
            raise InvalidVersion(f"Invalid version: '{version_string}'")

    def __eq__(self, other):
        # TBD: Should this verify the type of `other`
        return self.value.__eq__(other)

    def __lt__(self, other):
        return self.value.__lt__(other)


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
    "pypi": PYPIVersion
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
    range = ""


class VersionSpecifier:

    scheme = ""
    ranges = []

    @classmethod
    def from_version_spec_string(cls, value):
        """
        Return a VersionSpecifier built from a version spec string, prefixed by
        a scheme such as "semver:1.2.3,>=2.0.0"
        """
        raise NotImplementedError

    @classmethod
    def from_scheme_version_spec_string(cls, scheme, value):
        """
        Return a VersionSpecifier built from a scheme-specific version spec string and a scheme string.
        """
        raise NotImplementedError

    def __contains__(self, version):
        """
        Return True if this VersionSpecifier contains the ``version``
        Version object or scheme-prefixed version string. A version is contained
        in a VersionSpecifier if it satisfies all its Range.
        """
        if isinstance(version, str):
            version = parse_version(version)

        # .... magic happens here
        raise NotImplementedError

    def __str__(self):
        """
        Return this VersionSpecifier string using a canonical representation and our universal syntax.
        """
        # TODO: sort to make canonic
        ranges = ",".join(self.ranges)
        return f"{self.scheme}:{ranges}"
