#
# Copyright (c) nexB Inc. and others.
# SPDX-License-Identifier: Apache-2.0
#
# Visit https://aboutcode.org and https://github.com/nexB/univers for support and download.

from unittest import TestCase

from univers.normalized_range import NormalizedVersionRanges
from univers.version_constraint import VersionConstraint
from univers.version_range import PypiVersionRange
from univers.version_range import VersionRange
from univers.versions import PypiVersion

all_versions_pypi = [
    "1.1.3",
    "1.1.4",
    "1.10",
    "1.10.1",
    "1.10.2",
    "1.10.3",
    "1.10.4",
    "1.10.5",
    "1.10.6",
    "1.10.7",
    "1.10.8",
    "1.10a1",
    "1.10b1",
    "1.10rc1",
    "1.11",
    "1.11.1",
    "1.11.10",
    "1.11.11",
    "1.11.12",
    "1.11.13",
    "1.11.14",
    "1.11.15",
    "1.11.16",
    "1.11.17",
    "1.11.18",
    "1.11.2",
    "1.11.20",
    "1.11.21",
    "1.11.22",
    "1.11.23",
    "1.11.24",
    "1.11.25",
    "1.11.26",
    "1.11.27",
    "1.11.28",
    "1.11.29",
    "1.11.3",
    "1.11.4",
    "1.11.5",
    "1.11.6",
    "1.11.7",
    "1.11.8",
    "1.11.9",
    "1.11a1",
    "1.11b1",
    "1.11rc1",
    "1.2",
    "1.2.1",
    "1.2.2",
    "1.2.3",
    "1.2.4",
    "1.2.5",
    "1.2.6",
    "1.2.7",
    "1.3",
    "1.3.1",
    "1.3.2",
    "1.3.3",
    "1.3.4",
    "1.3.5",
    "1.3.6",
    "1.3.7",
    "1.4",
    "1.4.1",
    "1.4.10",
    "1.4.11",
    "1.4.12",
    "1.4.13",
    "1.4.14",
    "1.4.15",
    "1.4.16",
    "1.4.17",
    "1.4.18",
    "1.4.19",
    "1.4.2",
    "1.4.20",
    "1.4.21",
    "1.4.22",
    "1.4.3",
    "1.4.4",
    "1.4.5",
    "1.4.6",
    "1.4.7",
    "1.4.8",
    "1.4.9",
    "1.5",
    "1.5.1",
    "1.5.10",
    "1.5.11",
    "1.5.12",
    "1.5.2",
    "1.5.3",
    "1.5.4",
    "1.5.5",
    "1.5.6",
    "1.5.7",
    "1.5.8",
    "1.5.9",
    "1.6",
    "1.6.1",
    "1.6.10",
    "1.6.11",
    "1.6.2",
    "1.6.3",
    "1.6.4",
    "1.6.5",
    "1.6.6",
    "1.6.7",
    "1.6.8",
    "1.6.9",
    "1.7",
    "1.7.1",
    "1.7.10",
    "1.7.11",
    "1.7.2",
    "1.7.3",
    "1.7.4",
    "1.7.5",
    "1.7.6",
    "1.7.7",
    "1.7.8",
    "1.7.9",
    "1.8",
    "1.8.1",
    "1.8.10",
    "1.8.11",
    "1.8.12",
    "1.8.13",
    "1.8.14",
    "1.8.15",
    "1.8.16",
    "1.8.17",
    "1.8.18",
    "1.8.19",
    "1.8.2",
    "1.8.3",
    "1.8.4",
    "1.8.5",
    "1.8.6",
    "1.8.7",
    "1.8.8",
    "1.8.9",
    "1.8a1",
    "1.8b1",
    "1.8b2",
    "1.8c1",
    "1.9",
    "1.9.1",
    "1.9.10",
    "1.9.11",
    "1.9.12",
    "1.9.13",
    "1.9.2",
    "1.9.3",
    "1.9.4",
    "1.9.5",
    "1.9.6",
    "1.9.7",
    "1.9.8",
    "1.9.9",
    "1.9a1",
    "1.9b1",
    "1.9rc1",
    "1.9rc2",
    "2.0",
    "2.0.1",
    "2.0.10",
    "2.0.12",
    "2.0.13",
    "2.0.2",
    "2.0.3",
    "2.0.4",
    "2.0.5",
    "2.0.6",
    "2.0.7",
    "2.0.8",
    "2.0.9",
    "2.0a1",
    "2.0b1",
    "2.0rc1",
    "2.1",
    "2.1.1",
    "2.1.10",
    "2.1.11",
    "2.1.12",
    "2.1.13",
    "2.1.14",
    "2.1.15",
    "2.1.2",
    "2.1.3",
    "2.1.4",
    "2.1.5",
    "2.1.7",
    "2.1.8",
    "2.1.9",
    "2.1a1",
    "2.1b1",
    "2.1rc1",
    "2.2",
    "2.2.1",
    "2.2.10",
    "2.2.11",
    "2.2.12",
    "2.2.13",
    "2.2.14",
    "2.2.15",
    "2.2.16",
    "2.2.17",
    "2.2.18",
    "2.2.19",
    "2.2.2",
    "2.2.20",
    "2.2.21",
    "2.2.22",
    "2.2.23",
    "2.2.24",
    "2.2.25",
    "2.2.26",
    "2.2.27",
    "2.2.28",
    "2.2.3",
    "2.2.4",
    "2.2.5",
    "2.2.6",
    "2.2.7",
    "2.2.8",
    "2.2.9",
    "2.2a1",
    "2.2b1",
    "2.2rc1",
    "3.0",
    "3.0.1",
    "3.0.10",
    "3.0.11",
    "3.0.12",
    "3.0.13",
    "3.0.14",
    "3.0.2",
    "3.0.3",
    "3.0.4",
    "3.0.5",
    "3.0.6",
    "3.0.7",
    "3.0.8",
    "3.0.9",
    "3.0a1",
    "3.0b1",
    "3.0rc1",
    "3.1",
    "3.1.1",
    "3.1.10",
    "3.1.11",
    "3.1.12",
    "3.1.13",
    "3.1.14",
    "3.1.2",
    "3.1.3",
    "3.1.4",
    "3.1.5",
    "3.1.6",
    "3.1.7",
    "3.1.8",
    "3.1.9",
    "3.1a1",
    "3.1b1",
    "3.1rc1",
    "3.2",
    "3.2.1",
    "3.2.10",
    "3.2.11",
    "3.2.12",
    "3.2.13",
    "3.2.14",
    "3.2.15",
    "3.2.16",
    "3.2.17",
    "3.2.18",
    "3.2.2",
    "3.2.3",
    "3.2.4",
    "3.2.5",
    "3.2.6",
    "3.2.7",
    "3.2.8",
    "3.2.9",
    "3.2a1",
    "3.2b1",
    "3.2rc1",
    "4.0",
    "4.0.1",
    "4.0.10",
    "4.0.2",
    "4.0.3",
    "4.0.4",
    "4.0.5",
    "4.0.6",
    "4.0.7",
    "4.0.8",
    "4.0.9",
    "4.0a1",
    "4.0b1",
    "4.0rc1",
    "4.1",
    "4.1.1",
    "4.1.2",
    "4.1.3",
    "4.1.4",
    "4.1.5",
    "4.1.6",
    "4.1.7",
    "4.1a1",
    "4.1b1",
    "4.1rc1",
    "4.2a1",
    "4.2b1",
]


class TestNormalizedVersionRanges(TestCase):
    purl_type_pypi = "pypi"

    def test_NormalizedVersionRanges_from_github_type1(self):
        range_expression = "> 1.11rc1"

        normalized_range = NormalizedVersionRanges.from_github(
            range_expression=range_expression,
            purl_type=self.purl_type_pypi,
            all_versions=all_versions_pypi,
        )

        expected = NormalizedVersionRanges(
            version_ranges=[
                PypiVersionRange(
                    constraints=(
                        VersionConstraint(comparator=">=", version=PypiVersion(string="1.11")),
                        VersionConstraint(comparator="<=", version=PypiVersion(string="4.2b1")),
                    )
                )
            ]
        )
        assert normalized_range == expected

    def test_NormalizedVersionRanges_from_github_type2(self):
        range_expression = ">= 3.2.2, < 4.0.2"
        purl_type = "pypi"

        normalized_range = NormalizedVersionRanges.from_github(
            range_expression=range_expression,
            purl_type=self.purl_type_pypi,
            all_versions=all_versions_pypi,
        )

        expected = NormalizedVersionRanges(
            version_ranges=[
                PypiVersionRange(
                    constraints=(
                        VersionConstraint(comparator=">=", version=PypiVersion(string="3.2.2")),
                        VersionConstraint(comparator="<=", version=PypiVersion(string="4.0.1")),
                    )
                )
            ]
        )
        assert normalized_range == expected

    def test_NormalizedVersionRanges_from_github_type3(self):
        range_expression = [">= 3.2.2, < 4.0.2", ">1.4.9, < 1.11rc1"]

        normalized_range = NormalizedVersionRanges.from_github(
            range_expression=range_expression,
            purl_type=self.purl_type_pypi,
            all_versions=all_versions_pypi,
        )

        expected = NormalizedVersionRanges(
            version_ranges=[
                PypiVersionRange(
                    constraints=(
                        VersionConstraint(comparator=">=", version=PypiVersion(string="1.4.10")),
                        VersionConstraint(comparator="<=", version=PypiVersion(string="1.11b1")),
                    )
                ),
                PypiVersionRange(
                    constraints=(
                        VersionConstraint(comparator=">=", version=PypiVersion(string="3.2.2")),
                        VersionConstraint(comparator="<=", version=PypiVersion(string="4.0.1")),
                    )
                ),
            ]
        )
        assert normalized_range == expected

    def test_NormalizedVersionRanges_from_snyk_type1(self):
        range_expression = " >= 3.0.1, < 4.0.2"

        normalized_range = NormalizedVersionRanges.from_snyk(
            range_expression=range_expression,
            purl_type=self.purl_type_pypi,
            all_versions=all_versions_pypi,
        )

        expected = NormalizedVersionRanges(
            version_ranges=[
                PypiVersionRange(
                    constraints=(
                        VersionConstraint(comparator=">=", version=PypiVersion(string="3.0.1")),
                        VersionConstraint(comparator="<=", version=PypiVersion(string="4.0.1")),
                    )
                )
            ]
        )
        assert normalized_range == expected

    def test_NormalizedVersionRanges_from_snyk_type2(self):
        range_expression = "[3.0.1,4.0.2)"

        normalized_range = NormalizedVersionRanges.from_snyk(
            range_expression=range_expression,
            purl_type=self.purl_type_pypi,
            all_versions=all_versions_pypi,
        )

        expected = NormalizedVersionRanges(
            version_ranges=[
                PypiVersionRange(
                    constraints=(
                        VersionConstraint(comparator=">=", version=PypiVersion(string="3.0.1")),
                        VersionConstraint(comparator="<=", version=PypiVersion(string="4.0.1")),
                    )
                )
            ]
        )
        assert normalized_range == expected

    def test_NormalizedVersionRanges_from_snyk_type3(self):
        range_expression = ["[3.0.1,4.0.2)", " >= 3.0.1, < 4.0.2"]

        normalized_range = NormalizedVersionRanges.from_snyk(
            range_expression=range_expression,
            purl_type=self.purl_type_pypi,
            all_versions=all_versions_pypi,
        )

        expected = NormalizedVersionRanges(
            version_ranges=[
                PypiVersionRange(
                    constraints=(
                        VersionConstraint(comparator=">=", version=PypiVersion(string="3.0.1")),
                        VersionConstraint(comparator="<=", version=PypiVersion(string="4.0.1")),
                    )
                )
            ]
        )
        assert normalized_range == expected

    def test_NormalizedVersionRanges_from_gitlab_type1(self):
        range_expression = "[1.4,2.1rc1),[3.2,4.0rc1)"

        normalized_range = NormalizedVersionRanges.from_gitlab(
            range_expression=range_expression,
            purl_type=self.purl_type_pypi,
            all_versions=all_versions_pypi,
        )

        expected = NormalizedVersionRanges(
            version_ranges=[
                PypiVersionRange(
                    constraints=(
                        VersionConstraint(comparator=">=", version=PypiVersion(string="1.4")),
                        VersionConstraint(comparator="<=", version=PypiVersion(string="2.1b1")),
                    )
                ),
                PypiVersionRange(
                    constraints=(
                        VersionConstraint(comparator=">=", version=PypiVersion(string="3.2")),
                        VersionConstraint(comparator="<=", version=PypiVersion(string="4.0b1")),
                    )
                ),
            ]
        )
        assert normalized_range == expected

    def test_NormalizedVersionRanges_from_gitlab_type2(self):
        range_expression = ">=4.0,<4.2b1||>=1.2,<2.1"

        normalized_range = NormalizedVersionRanges.from_gitlab(
            range_expression=range_expression,
            purl_type=self.purl_type_pypi,
            all_versions=all_versions_pypi,
        )

        expected = NormalizedVersionRanges(
            version_ranges=[
                PypiVersionRange(
                    constraints=(
                        VersionConstraint(comparator=">=", version=PypiVersion(string="1.2")),
                        VersionConstraint(comparator="<=", version=PypiVersion(string="2.1rc1")),
                    )
                ),
                PypiVersionRange(
                    constraints=(
                        VersionConstraint(comparator=">=", version=PypiVersion(string="4.0")),
                        VersionConstraint(comparator="<=", version=PypiVersion(string="4.2a1")),
                    )
                ),
            ]
        )
        assert normalized_range == expected

    def test_NormalizedVersionRanges_from_gitlab_type3(self):
        range_expression = ">=1.2 <2.1"

        normalized_range = NormalizedVersionRanges.from_gitlab(
            range_expression=range_expression,
            purl_type=self.purl_type_pypi,
            all_versions=all_versions_pypi,
        )

        expected = NormalizedVersionRanges(
            version_ranges=[
                PypiVersionRange(
                    constraints=(
                        VersionConstraint(comparator=">=", version=PypiVersion(string="1.2")),
                        VersionConstraint(comparator="<=", version=PypiVersion(string="2.1rc1")),
                    )
                ),
            ]
        )
        assert normalized_range == expected

    def test_NormalizedVersionRanges_from_gitlab_type4(self):
        range_expression = ">=1.5,<1.5.2"

        normalized_range = NormalizedVersionRanges.from_gitlab(
            range_expression=range_expression,
            purl_type=self.purl_type_pypi,
            all_versions=all_versions_pypi,
        )

        expected = NormalizedVersionRanges(
            version_ranges=[
                PypiVersionRange(
                    constraints=(
                        VersionConstraint(comparator=">=", version=PypiVersion(string="1.5")),
                        VersionConstraint(comparator="<=", version=PypiVersion(string="1.5.1")),
                    )
                )
            ]
        )
        assert normalized_range == expected

    def test_NormalizedVersionRanges_from_gitlab_type5(self):
        range_expression = [
            ">=1.2 <2.1",
            ">=4.0,<4.2b1||>=1.2,<2.1",
            "[1.4,2.1rc1),[3.2,4.0rc1)",
            ">=1.5,<1.5.2",
        ]

        normalized_range = NormalizedVersionRanges.from_gitlab(
            range_expression=range_expression,
            purl_type=self.purl_type_pypi,
            all_versions=all_versions_pypi,
        )

        expected = NormalizedVersionRanges(
            version_ranges=[
                PypiVersionRange(
                    constraints=(
                        VersionConstraint(comparator=">=", version=PypiVersion(string="1.2")),
                        VersionConstraint(comparator="<=", version=PypiVersion(string="2.1rc1")),
                    )
                ),
                PypiVersionRange(
                    constraints=(
                        VersionConstraint(comparator=">=", version=PypiVersion(string="3.2")),
                        VersionConstraint(comparator="<=", version=PypiVersion(string="4.0b1")),
                    )
                ),
                PypiVersionRange(
                    constraints=(
                        VersionConstraint(comparator=">=", version=PypiVersion(string="4.0")),
                        VersionConstraint(comparator="<=", version=PypiVersion(string="4.2a1")),
                    )
                ),
            ]
        )
        assert normalized_range == expected

    def test_NormalizedVersionRanges_from_discrete_for_DEPS(self):
        range_expression = [
            "2.0",
            "2.0rc1",
            "2.0rc1-py2.4-linux-i686",
            "2.0rc1-py2.4-linux-x86_64",
            "2.0rc1-py2.4-macosx-10.3-i386",
            "2.0rc1-py2.4-win32",
            "2.0rc1-py2.5-linux-i686",
            "2.0rc1-py2.5-linux-x86_64",
            "2.0rc1-py2.5-macosx-10.3-i386",
            "2.0rc1-py2.5-win32",
            "2.1-py2.4-win322.1-py2.5-win32",
            "2.1-py2.6-win32",
            " 2.1.0",
            "2.1.1",
            "2.1.1-py2.4-win32",
            "2.1.1-py2.5-win32",
            "2.1.1-py2.6-win32",
            "2.10.0 2.2.0",
            "2.2.1",
            "2.2.3",
            "2.2.11",
            "2.2.9",
        ]

        normalized_range = NormalizedVersionRanges.from_discrete(
            range_expression=range_expression,
            purl_type=self.purl_type_pypi,
            all_versions=all_versions_pypi,
        )

        expected = NormalizedVersionRanges(
            version_ranges=[
                PypiVersionRange(
                    constraints=(
                        VersionConstraint(comparator=">=", version=PypiVersion(string="2.0rc1")),
                        VersionConstraint(comparator="<=", version=PypiVersion(string="2.0")),
                    )
                ),
                PypiVersionRange(
                    constraints=(
                        VersionConstraint(comparator="=", version=PypiVersion(string="2.1.1")),
                    )
                ),
                PypiVersionRange(
                    constraints=(
                        VersionConstraint(comparator="=", version=PypiVersion(string="2.2.1")),
                    )
                ),
                PypiVersionRange(
                    constraints=(
                        VersionConstraint(comparator="=", version=PypiVersion(string="2.2.3")),
                    )
                ),
                PypiVersionRange(
                    constraints=(
                        VersionConstraint(comparator="=", version=PypiVersion(string="2.2.9")),
                    )
                ),
                PypiVersionRange(
                    constraints=(
                        VersionConstraint(comparator="=", version=PypiVersion(string="2.2.11")),
                    )
                ),
            ]
        )
        assert normalized_range == expected

    def test_NormalizedVersionRanges_from_discrete_for_VulnerableCode(self):
        range_expression = [
            "1.10",
            "1.10.1",
            "1.10.2",
            "1.10.3",
            "1.10.4",
            "1.10.5",
            "1.10.6",
            "1.10.7",
            "1.10.8",
            "1.10a1",
            "1.10b1",
            "1.10rc1",
            "1.11",
            "1.11.0",
            "1.11.1",
            "1.11.10",
            "1.11.11",
            "1.11.12",
            "1.11.13",
            "1.11.14",
            "1.11.15",
            "1.11.16",
            "1.11.17",
            "1.11.18",
            "1.11.2",
            "1.11.3",
            "1.11.4",
            "1.11.5",
            "1.11.6",
            "1.11.7",
            "1.11.8",
            "1.11.9",
            "1.11a1",
            "1.11b1",
            "1.11rc1",
            "1.1.3",
            "1.1.4",
            "1.2",
            "1.2.1",
            "1.2.2",
            "1.2.3",
            "1.2.4",
            "1.2.5",
            "1.2.6",
            "1.2.7",
            "1.3",
            "1.3.1",
            "1.3.2",
            "1.3.3",
            "1.3.4",
            "1.3.5",
            "1.3.6",
            "1.3.7",
            "1.4",
            "1.4.1",
            "1.4.10",
            "1.4.11",
            "1.4.12",
            "1.4.13",
            "1.4.14",
            "1.4.15",
            "1.4.16",
            "1.4.17",
            "1.4.18",
            "1.4.19",
            "1.4.2",
            "1.4.20",
            "1.4.21",
            "1.4.22",
            "1.4.3",
            "1.4.4",
            "1.4.5",
            "1.4.6",
            "1.4.7",
            "1.4.8",
            "1.4.9",
            "1.5",
            "1.5.1",
            "1.5.10",
            "1.5.11",
            "1.5.12",
            "1.5.2",
            "1.5.3",
            "1.5.4",
            "1.5.5",
            "1.5.6",
            "1.5.7",
            "1.5.8",
            "1.5.9",
            "1.6",
            "1.6.1",
            "1.6.10",
            "1.6.11",
            "1.6.2",
            "1.6.3",
            "1.6.4",
            "1.6.5",
            "1.6.6",
            "1.6.7",
            "1.6.8",
            "1.6.9",
            "1.7",
            "1.7.1",
            "1.7.10",
            "1.7.11",
            "1.7.2",
            "1.7.3",
            "1.7.4",
            "1.7.5",
            "1.7.6",
            "1.7.7",
            "1.7.8",
            "1.7.9",
            "1.8",
            "1.8.1",
            "1.8.10",
            "1.8.11",
            "1.8.12",
            "1.8.13",
            "1.8.14",
            "1.8.15",
            "1.8.16",
            "1.8.17",
            "1.8.18",
            "1.8.19",
            "1.8.2",
            "1.8.3",
            "1.8.4",
            "1.8.5",
            "1.8.6",
            "1.8.7",
            "1.8.8",
            "1.8.9",
            "1.8a1",
            "1.8b1",
            "1.8b2",
            "1.8c1",
            "1.9",
            "1.9.1",
            "1.9.10",
            "1.9.11",
            "1.9.12",
            "1.9.13",
            "1.9.2",
            "1.9.3",
            "1.9.4",
            "1.9.5",
            "1.9.6",
            "1.9.7",
            "1.9.8",
            "1.9.9",
            "1.9a1",
            "1.9b1",
            "1.9rc1",
            "1.9rc2",
            "2.0",
            "2.0.0",
            "2.0.1",
            "2.0.10",
            "2.0.2",
            "2.0.3",
            "2.0.4",
            "2.0.5",
            "2.0.6",
            "2.0.7",
            "2.0.8",
            "2.0.9",
            "2.1",
            "2.1.0",
            "2.1.1",
            "2.1.2",
            "2.1.3",
            "2.1.4",
            "2.1.5",
        ]

        normalized_range = NormalizedVersionRanges.from_discrete(
            range_expression=range_expression,
            purl_type=self.purl_type_pypi,
            all_versions=all_versions_pypi,
        )

        expected = NormalizedVersionRanges(
            version_ranges=[
                PypiVersionRange(
                    constraints=(
                        VersionConstraint(comparator=">=", version=PypiVersion(string="1.1.3")),
                        VersionConstraint(comparator="<=", version=PypiVersion(string="1.11.18")),
                    )
                ),
                PypiVersionRange(
                    constraints=(
                        VersionConstraint(comparator=">=", version=PypiVersion(string="2.0")),
                        VersionConstraint(comparator="<=", version=PypiVersion(string="2.0.10")),
                    )
                ),
                PypiVersionRange(
                    constraints=(
                        VersionConstraint(comparator=">=", version=PypiVersion(string="2.1")),
                        VersionConstraint(comparator="<=", version=PypiVersion(string="2.1.5")),
                    )
                ),
            ]
        )
        assert normalized_range == expected
        return normalized_range

    def test_NormalizedVersionRanges_from_discrete_for_OSV(self):
        range_expression = [
            "0",
            "1.0.1",
            "1.0.2",
            "1.0.3",
            "1.0.4",
            "1.1",
            "1.1.1",
            "1.1.2",
            "1.1.3",
            "1.1.4",
            "1.10",
            "1.10.1",
            "1.10.2",
            "1.10.3",
            "1.10.4",
            "1.10.5",
            "1.10.6",
            "1.10.7",
            "1.10.8",
            "1.10a1",
            "1.10b1",
            "1.10rc1",
            "1.11",
            "1.11.1",
            "1.11.10",
            "1.11.11",
            "1.11.12",
            "1.11.13",
            "1.11.14",
            "1.11.15",
            "1.11.16",
            "1.11.17",
            "1.11.18",
            "1.11.2",
            "1.11.20",
            "1.11.21",
            "1.11.22",
            "1.11.23",
            "1.11.24",
            "1.11.25",
            "1.11.26",
            "1.11.27",
            "1.11.28",
            "1.11.3",
            "1.11.4",
            "1.11.5",
            "1.11.6",
            "1.11.7",
            "1.11.8",
            "1.11.9",
            "1.11a1",
            "1.11b1",
            "1.11rc1",
            "1.2",
            "1.2.1",
            "1.2.2",
            "1.2.3",
            "1.2.4",
            "1.2.5",
            "1.2.6",
            "1.2.7",
            "1.3",
            "1.3.1",
            "1.3.2",
            "1.3.3",
            "1.3.4",
            "1.3.5",
            "1.3.6",
            "1.3.7",
            "1.4",
            "1.4.1",
            "1.4.10",
            "1.4.11",
            "1.4.12",
            "1.4.13",
            "1.4.14",
            "1.4.15",
            "1.4.16",
            "1.4.17",
            "1.4.18",
            "1.4.19",
            "1.4.2",
            "1.4.20",
            "1.4.21",
            "1.4.22",
            "1.4.3",
            "1.4.4",
            "1.4.5",
            "1.4.6",
            "1.4.7",
            "1.4.8",
            "1.4.9",
            "1.5",
            "1.5.1",
            "1.5.10",
            "1.5.11",
            "1.5.12",
            "1.5.2",
            "1.5.3",
            "1.5.4",
            "1.5.5",
            "1.5.6",
            "1.5.7",
            "1.5.8",
            "1.5.9",
            "1.6",
            "1.6.1",
            "1.6.10",
            "1.6.11",
            "1.6.2",
            "1.6.3",
            "1.6.4",
            "1.6.5",
            "1.6.6",
            "1.6.7",
            "1.6.8",
            "1.6.9",
            "1.7",
            "1.7.1",
            "1.7.10",
            "1.7.11",
            "1.7.2",
            "1.7.3",
            "1.7.4",
            "1.7.5",
            "1.7.6",
            "1.7.7",
            "1.7.8",
            "1.7.9",
            "1.8",
            "1.8.1",
            "1.8.10",
            "1.8.11",
            "1.8.12",
            "1.8.13",
            "1.8.14",
            "1.8.15",
            "1.8.16",
            "1.8.17",
            "1.8.18",
            "1.8.19",
            "1.8.2",
            "1.8.3",
            "1.8.4",
            "1.8.5",
            "1.8.6",
            "1.8.7",
            "1.8.8",
            "1.8.9",
            "1.8a1",
            "1.8b1",
            "1.8b2",
            "1.8c1",
            "1.9",
            "1.9.1",
            "1.9.10",
            "1.9.11",
            "1.9.12",
            "1.9.13",
            "1.9.2",
            "1.9.3",
            "1.9.4",
            "1.9.5",
            "1.9.6",
            "1.9.7",
            "1.9.8",
            "1.9.9",
            "1.9a1",
            "1.9b1",
            "1.9rc1",
            "1.9rc2",
        ]
        normalized_range = NormalizedVersionRanges.from_discrete(
            range_expression=range_expression,
            purl_type=self.purl_type_pypi,
            all_versions=all_versions_pypi,
        )

        expected = NormalizedVersionRanges(
            version_ranges=[
                PypiVersionRange(
                    constraints=(
                        VersionConstraint(comparator=">=", version=PypiVersion(string="1.1.3")),
                        VersionConstraint(comparator="<=", version=PypiVersion(string="1.11.28")),
                    )
                )
            ]
        )
        assert normalized_range == expected
