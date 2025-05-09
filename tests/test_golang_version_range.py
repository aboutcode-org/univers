# Copyright (c) nexB Inc. and others.
# SPDX-License-Identifier: Apache-2.0
#
# Visit https://aboutcode.org and https://github.com/aboutcode-org/univers for support and download.

from univers.version_constraint import VersionConstraint
from univers.version_range import GolangVersionRange
from univers.versions import GolangVersion


def test_golang_exact_version():
    version_range = GolangVersionRange.from_native("v1.2.3")
    assert version_range == GolangVersionRange(
        constraints=(VersionConstraint(comparator="=", version=GolangVersion(string="v1.2.3")),)
    )


def test_golang_greater_than():
    version_range = GolangVersionRange.from_native(">v1.2.3")
    assert version_range == GolangVersionRange(
        constraints=(VersionConstraint(comparator=">", version=GolangVersion(string="v1.2.3")),)
    )


def test_golang_greater_than_or_equal():
    version_range = GolangVersionRange.from_native(">=v1.2.3")
    assert version_range == GolangVersionRange(
        constraints=(VersionConstraint(comparator=">=", version=GolangVersion(string="v1.2.3")),)
    )


def test_golang_less_than():
    version_range = GolangVersionRange.from_native("<v1.2.3")
    assert version_range == GolangVersionRange(
        constraints=(VersionConstraint(comparator="<", version=GolangVersion(string="v1.2.3")),)
    )


def test_golang_less_than_or_equal():
    version_range = GolangVersionRange.from_native("<=v1.2.3")
    assert version_range == GolangVersionRange(
        constraints=(VersionConstraint(comparator="<=", version=GolangVersion(string="v1.2.3")),)
    )


def test_golang_version_range_with_multiple_constraints():
    version_range = GolangVersionRange.from_native(">=v1.2.3, <v2.0.0")
    assert version_range == GolangVersionRange(
        constraints=(
            VersionConstraint(comparator=">=", version=GolangVersion(string="v1.2.3")),
            VersionConstraint(comparator="<", version=GolangVersion(string="v2.0.0")),
        )
    )


def test_golang_version_with_prerelease():
    version_range = GolangVersionRange.from_native("v1.2.3-beta.1")
    assert version_range == GolangVersionRange(
        constraints=(
            VersionConstraint(comparator="=", version=GolangVersion(string="v1.2.3-beta.1")),
        )
    )


def test_golang_range_string_representation():
    version_range = GolangVersionRange.from_native(">=v1.2.3, <v2.0.0")
    assert str(version_range) == "vers:golang/>=1.2.3|<2.0.0"


def test_golang_version_range_with_pre_and_build():
    version_range = GolangVersionRange.from_native("v1.2.3-alpha+build123")
    assert version_range == GolangVersionRange(
        constraints=(
            VersionConstraint(
                comparator="=", version=GolangVersion(string="v1.2.3-alpha+build123")
            ),
        )
    )


def test_golang_version_with_major_zero():
    version_range = GolangVersionRange.from_native("v0.1.5")
    assert version_range == GolangVersionRange(
        constraints=(VersionConstraint(comparator="=", version=GolangVersion(string="v0.1.5")),)
    )


def test_golang_version_with_only_major():
    version_range = GolangVersionRange.from_native("v1")
    assert version_range == GolangVersionRange(
        constraints=(VersionConstraint(comparator="=", version=GolangVersion(string="v1")),)
    )


def test_golang_version_with_upper_case():
    version_range = GolangVersionRange.from_native("V1.2.3")
    assert version_range == GolangVersionRange(
        constraints=(VersionConstraint(comparator="=", version=GolangVersion(string="v1.2.3")),)
    )
