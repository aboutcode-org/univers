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

from universal_versions.utils import remove_spaces
from universal_versions.version_range import VersionRange
from universal_versions.versions import parse_version


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

        return cls.from_scheme_version_spec_string(cls, scheme, version_range_expressions)

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
            range = VersionRange(version_range, scheme)
            ranges.append(range)

        vs = cls()
        vs.ranges = ranges
        vs.scheme = scheme
        return vs

    def __str__(self):
        """
        Return the canonical representation.
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
