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


from semantic_version import Version

from univers.utils import remove_spaces
from univers.version_range import VersionRange
from univers.versions import parse_version


def normalized_caret_ranges(caret_version_range_string):
    """
    Helper which returns VersionRange objects from a string which contains ranges which use
    the caret operator. The scheme is 'semver'.

    Example:-
    >>> lower_bound, upper_bound = normalized_caret_ranges("^1.0.2")
    >>> expected_lower_bound = VersionRange(">=1.0.2", "semver")
    >>> expected_upper_bound = VersionRange("<2.0.0", "semver")
    >>> assert lower_bound == expected_lower_bound
    >>> assert upper_bound == expected_upper_bound
    """
    caret_version_range_string = remove_spaces(caret_version_range_string)
    try:
        _, version = caret_version_range_string.split("^")
    except ValueError:
        raise ValueError(f"The version range string {caret_version_range_string} is not valid.")
    lower_bound = version
    upper_bound = Version.coerce(version).next_major().__str__()

    return VersionRange(f">={lower_bound}", "semver"), VersionRange(f"<{upper_bound}", "semver")


def normalized_tilde_ranges(tilde_version_range_string):
    """
    Helper which returns VersionRange objects from a string which contains ranges which use
    the tilde operator. The scheme is 'semver'.

    Example:-
    >>> lower_bound, upper_bound = normalized_tilde_ranges("~1.0.2")
    >>> expected_lower_bound = VersionRange(">=1.0.2", "semver")
    >>> expected_upper_bound = VersionRange("<1.1.0", "semver")
    >>> assert lower_bound == expected_lower_bound
    >>> assert upper_bound == expected_upper_bound
    """
    tilde_version_range_string = remove_spaces(tilde_version_range_string)
    try:
        _, version = tilde_version_range_string.split("~")
    except ValueError:
        raise ValueError(f"The version range string {tilde_version_range_string} is not valid.")
    lower_bound = version
    upper_bound = Version.coerce(version).next_minor().__str__()

    return VersionRange(f">={lower_bound}", "semver"), VersionRange(f"<{upper_bound}", "semver")


def normalized_pessimistic_ranges(pessimistic_version_range_string):
    """
    Helper which returns VersionRange objects from a string which contains ranges which use
    a pessimistic operator. The scheme is 'semver' since only ruby style semver supports
    this operator.

    Example:- '~>2.0.8' will get resolved into VersionRange objects of '>=2.0.8' and '<2.1.0'
    """
    pessimistic_version_range_string = remove_spaces(pessimistic_version_range_string)
    try:
        _, version = pessimistic_version_range_string.split("~>")
    except ValueError:
        raise ValueError(
            f"The version range string {pessimistic_version_range_string} is not valid"
        )

    lower_bound = version
    upper_bound = Version.coerce(version).next_minor().__str__()

    return VersionRange(f">={lower_bound}", "semver"), VersionRange(f"<{upper_bound}", "semver")


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

        return cls.from_scheme_version_spec_string(scheme, version_range_expressions)

    @classmethod
    def from_scheme_version_spec_string(cls, scheme, value):
        """
        Return a VersionSpecifier built from a scheme-specific version spec string and a scheme string.
        """

        value = remove_spaces(value)
        version_ranges = value.split(",")
        ranges = []
        for version_range in version_ranges:
            if scheme == "semver":
                if "~>" in version_range:
                    ranges.extend(normalized_pessimistic_ranges(version_range))
                    continue

                if "~" in version_range:
                    ranges.extend(normalized_tilde_ranges(version_range))
                    continue

                if "^" in version_range:
                    ranges.extend(normalized_caret_ranges(version_range))
                    continue

            rng = VersionRange(version_range, scheme)
            ranges.append(rng)

        ranges.sort(key=lambda rng: (rng.operator, rng.version))

        vs = cls()
        vs.ranges = ranges
        vs.scheme = scheme
        return vs

    def __str__(self):
        """
        Return the canonical representation.
        """

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

    def __eq__(self, other):
        return (self.ranges, self.scheme) == (other.ranges, other.scheme)
