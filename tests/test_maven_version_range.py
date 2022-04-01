#
# Copyright (c) nexB Inc. and others.
# SPDX-License-Identifier: Apache-2.0
#
# Visit https://aboutcode.org and https://github.com/nexB/univers for support and download.

from univers.version_range import MavenVersionRange
from univers.version_constraint import VersionConstraint
from univers.versions import MavenVersion


def test_maven_version_range_from_native_with_lower_inclusive():
    version_range = MavenVersionRange.from_native("[1.0.0,2.0.0)")
    assert version_range == MavenVersionRange(
        constraints=(
            VersionConstraint(comparator=">=", version=MavenVersion(string="1.0.0")),
            VersionConstraint(comparator="<", version=MavenVersion(string="2.0.0")),
        )
    )


def test_maven_version_range_from_native_with_nothing_inclusive():
    version_range = MavenVersionRange.from_native(" ( 1.0.0 , 2.1.4 ) ")
    assert version_range == MavenVersionRange(
        constraints=(
            VersionConstraint(comparator=">", version=MavenVersion(string="1.0.0")),
            VersionConstraint(comparator="<", version=MavenVersion(string="2.1.4")),
        )
    )


def test_maven_version_range_from_native_for_pinned_version():
    version_range = MavenVersionRange.from_native("[1.0.0]")
    assert version_range == MavenVersionRange(
        constraints=(VersionConstraint(comparator="=", version=MavenVersion(string="1.0.0")),)
    )


def test_maven_version_range_from_native_for_illformed_version():
    try:
        MavenVersionRange.from_native("(1.0.0]")
        assert False, "should have raised an exception"
    except ValueError:
        assert True


def test_maven_version_range_from_native_str_representation():
    version_range = MavenVersionRange.from_native("[1.0.0,5.1)")
    assert str(version_range) == "vers:maven/>=1.0.0|<5.1"


def test_maven_version_range_from_native_for_multiple_version_ranges():
    version_range = MavenVersionRange.from_native("[2.0,2.3.1] , [2.4.0,2.12.2) , [2.13.0,2.15.0)")
    assert version_range == MavenVersionRange(
        constraints=(
            VersionConstraint(comparator=">=", version=MavenVersion(string="2.0")),
            VersionConstraint(comparator="<=", version=MavenVersion(string="2.3.1")),
            VersionConstraint(comparator=">=", version=MavenVersion(string="2.4.0")),
            VersionConstraint(comparator="<", version=MavenVersion(string="2.12.2")),
            VersionConstraint(comparator=">=", version=MavenVersion(string="2.13.0")),
            VersionConstraint(comparator="<", version=MavenVersion(string="2.15.0")),
        )
    )


def test_maven_version_range_from_native_for_multiple_pinned_versions_and_a_range():
    version_range = MavenVersionRange.from_native("[2.0] , [2.4.0] , [2.13.0,2.15.0)")
    assert version_range == MavenVersionRange(
        constraints=(
            VersionConstraint(comparator="=", version=MavenVersion(string="2.0")),
            VersionConstraint(comparator="=", version=MavenVersion(string="2.4.0")),
            VersionConstraint(comparator=">=", version=MavenVersion(string="2.13.0")),
            VersionConstraint(comparator="<", version=MavenVersion(string="2.15.0")),
        )
    )
