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

import operator
import re
from functools import total_ordering
from packaging import version as pypi_version
from semver import version as semver_version
import semver


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


@total_ordering
class SemverVersion:
    scheme = "semver"

    def __init__(self, version_string):
        self.validate(version_string)
        self.value = semver_version.Version.parse(version_string)

    @staticmethod
    def validate(version_string):
        match = semver_version.Version._REGEX.search(version_string)
        if not match:
            raise InvalidVersion(f"Invalid version: '{version_string}'")

    def __eq__(self, other):
        # TBD: Should this verify the type of `other`
        return self.value.__eq__(other.value)

    def __lt__(self, other):
        return self.value.__lt__(other.value)


version_class_by_scheme = {
    "generic": GenericVersion,
    "semver": SemverVersion,
    "debian": DebianVersion,
    "pypi": PYPIVersion,
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
