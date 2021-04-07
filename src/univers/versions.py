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

import attr
from functools import total_ordering
from packaging import version as pypi_version

import semantic_version

from univers.utils import remove_spaces
from univers.debian import Version as _DebianVersion
from univers.maven import Version as _MavenVersion
from univers.rpm import vercmp


class InvalidVersion(ValueError):
    pass


class BaseVersion:
    # each version value should be comparable e.g. implement functools.total_ordering

    scheme = attr.ib()
    value = attr.ib()
    version_string = attr.ib()

    def validate(self):
        """
        Validate that the version is valid for its scheme
        """
        raise NotImplementedError

    def __str__(self):
        return f"{self.scheme}:{self.version_string}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__} <{self.__str__()}>"


@total_ordering
@attr.s(frozen=True, init=False, order=False, eq=False, hash=True, repr=False)
class PYPIVersion(BaseVersion):
    scheme = "pypi"

    def __init__(self, version_string):
        # TODO the `pypi_version.Version` class's constructor also does the same validation
        # but it has a fallback option by creating an object of pypi_version.LegacyVersion class.
        # Avoid the double validation and the fallback.

        self.validate(version_string)
        object.__setattr__(self, "value", pypi_version.Version(version_string))
        object.__setattr__(self, "version_string", version_string)

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


@attr.s(frozen=True, init=False, order=False, eq=False, hash=True, repr=False)
@total_ordering
class SemverVersion(BaseVersion):
    scheme = "semver"

    def __init__(self, version_string):
        version_string = version_string.lower()
        version_string = version_string.lstrip("v")
        object.__setattr__(self, "value", semantic_version.Version.coerce(version_string))
        object.__setattr__(self, "version_string", version_string)

    @staticmethod
    def validate(version_string):
        pass

    def __eq__(self, other):
        # TBD: Should this verify the type of `other`
        return self.value.__eq__(other.value)

    def __lt__(self, other):
        return self.value.__lt__(other.value)


@total_ordering
@attr.s(frozen=True, init=False, order=False, eq=False, hash=True, repr=False)
class DebianVersion(BaseVersion):
    scheme = "debian"

    def __init__(self, version_string):
        version_string = remove_spaces(version_string)
        object.__setattr__(self, "value", _DebianVersion.from_string(version_string))
        object.__setattr__(self, "version_string", version_string)

    @staticmethod
    def validate(version_string):
        pass

    def __eq__(self, other):
        return self.value.__eq__(other.value)

    def __lt__(self, other):
        return self.value.__lt__(other.value)


@total_ordering
@attr.s(frozen=True, init=False, order=False, eq=False, hash=True, repr=False)
class MavenVersion(BaseVersion):
    scheme = "maven"

    def __init__(self, version_string):
        version_string = remove_spaces(version_string)
        object.__setattr__(self, "value", _MavenVersion(version_string))
        object.__setattr__(self, "version_string", version_string)

    @staticmethod
    def validate(version_string):
        # Defined for compatibility
        pass

    def __eq__(self, other):
        return self.value.__eq__(other.value)

    def __lt__(self, other):
        return self.value.__lt__(other.value)


# See https://docs.microsoft.com/en-us/nuget/concepts/package-versioning
@total_ordering
@attr.s(frozen=True, init=False, order=False, eq=False, hash=True, repr=False)
class NugetVersion(SemverVersion):
    scheme = "nuget"
    pass


@total_ordering
@attr.s(frozen=True, init=False, order=False, eq=False, hash=True, repr=False)
class RPMVersion(BaseVersion):
    scheme = "rpm"

    def __init__(self, version_string):
        version_string = remove_spaces(version_string)
        self.validate(version_string)
        object.__setattr__(self, "value", version_string)
        object.__setattr__(self, "version_string", version_string)

    @staticmethod
    def validate(version_string):
        pass

    def __eq__(self, other):
        result = vercmp(self.value, other.value)
        return result == 0

    def __lt__(self, other):
        result = vercmp(self.value, other.value)
        return result == -1


# TODO : Should these be upper case global constants ?

version_class_by_scheme = {
    "generic": GenericVersion,
    "semver": SemverVersion,
    "debian": DebianVersion,
    "pypi": PYPIVersion,
    "maven": MavenVersion,
    "nuget": NugetVersion,
    "rpm": RPMVersion,
}

# TODO: This is messed up
version_class_by_package_type = {
    "deb": DebianVersion,
    "pypi": PYPIVersion,
    "maven": MavenVersion,
    "nuget": NugetVersion,
    "composer": SemverVersion,
    "npm": SemverVersion,
    "gem": SemverVersion,
    "rpm": RPMVersion,
    "golang": SemverVersion,
    "generic": SemverVersion,
    "apache": SemverVersion,
    "hex": SemverVersion,
    "cargo": SemverVersion,
    "mozilla": SemverVersion,
    "github": SemverVersion,
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
