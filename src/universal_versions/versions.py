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
from universal_versions.debian_version.version import Version as _DebianVersion


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


@total_ordering
class SemverVersion(BaseVersion):
    scheme = "semver"

    def __init__(self, version_string):
        # self.validate(version_string)
        version_string = version_string.lower()
        version_string = version_string.lstrip("v")
        self.value = semantic_version.Version.coerce(version_string)

    @staticmethod
    def validate(version_string):
        pass

    def __eq__(self, other):
        # TBD: Should this verify the type of `other`
        return self.value.__eq__(other.value)

    def __lt__(self, other):
        return self.value.__lt__(other.value)


@total_ordering
class DebianVersion(BaseVersion):
    scheme = "debian"

    def __init__(self,  version_string):
        version_string = remove_spaces(version_string)
        self.value = _DebianVersion.from_string(version_string)

    @staticmethod
    def validate(version_string):
        pass

    def __eq__(self, other):
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


# See https://docs.microsoft.com/en-us/nuget/concepts/package-versioning
class NugetVersion(SemverVersion):
    scheme = "nuget"
    pass


# TODO : Should these be upper case global constants ?

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
