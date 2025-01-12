# Copyright (c) nexB Inc. and others.
# SPDX-License-Identifier: Apache-2.0
#
# Visit https://aboutcode.org and https://github.com/aboutcode-org/univers for support and download.

from univers.version_constraint import VersionConstraint
from univers.version_range import ComposerVersionRange
from univers.versions import ComposerVersion


def test_composer_exact_version():
    version_range = ComposerVersionRange.from_native("1.3.2")
    assert version_range == ComposerVersionRange(
        constraints=(VersionConstraint(comparator="=", version=ComposerVersion(string="1.3.2")),)
    )


def test_composer_greater_than_or_equal():
    version_range = ComposerVersionRange.from_native(">=1.3.2")
    assert version_range == ComposerVersionRange(
        constraints=(VersionConstraint(comparator=">=", version=ComposerVersion(string="1.3.2")),)
    )


def test_composer_less_than():
    version_range = ComposerVersionRange.from_native("<1.3.2")
    assert version_range == ComposerVersionRange(
        constraints=(VersionConstraint(comparator="<", version=ComposerVersion(string="1.3.2")),)
    )


def test_composer_wildcard():
    version_range = ComposerVersionRange.from_native("1.3.*")
    assert version_range == ComposerVersionRange(
        constraints=(
            VersionConstraint(comparator=">=", version=ComposerVersion(string="1.3.0")),
            VersionConstraint(comparator="<", version=ComposerVersion(string="1.4.0")),
        )
    )


def test_composer_tilde_patch():
    version_range = ComposerVersionRange.from_native("~1.3.2")
    assert version_range == ComposerVersionRange(
        constraints=(
            VersionConstraint(comparator=">=", version=ComposerVersion(string="1.3.2")),
            VersionConstraint(comparator="<", version=ComposerVersion(string="1.4.0")),
        )
    )


def test_composer_tilde_minor():
    version_range = ComposerVersionRange.from_native("~1.3")
    assert version_range == ComposerVersionRange(
        constraints=(
            VersionConstraint(comparator=">=", version=ComposerVersion(string="1.3.0")),
            VersionConstraint(comparator="<", version=ComposerVersion(string="2.0.0")),
        )
    )


def test_composer_caret_patch():
    version_range = ComposerVersionRange.from_native("^1.3.2")
    assert version_range == ComposerVersionRange(
        constraints=(
            VersionConstraint(comparator=">=", version=ComposerVersion(string="1.3.2")),
            VersionConstraint(comparator="<", version=ComposerVersion(string="2.0.0")),
        )
    )


def test_composer_caret_zero_minor():
    version_range = ComposerVersionRange.from_native("^0.3.2")
    assert version_range == ComposerVersionRange(
        constraints=(
            VersionConstraint(comparator=">=", version=ComposerVersion(string="0.3.2")),
            VersionConstraint(comparator="<", version=ComposerVersion(string="0.4.0")),
        )
    )


def test_composer_range_with_multiple_constraints():
    version_range = ComposerVersionRange.from_native(">=1.2.3, <2.0.0")
    assert version_range == ComposerVersionRange(
        constraints=(
            VersionConstraint(comparator=">=", version=ComposerVersion(string="1.2.3")),
            VersionConstraint(comparator="<", version=ComposerVersion(string="2.0.0")),
        )
    )


def test_composer_range_with_or_constraints():
    version_range = ComposerVersionRange.from_native(">=1.0.0 || <2.0.0")
    assert version_range == ComposerVersionRange(
        constraints=(
            VersionConstraint(comparator=">=", version=ComposerVersion(string="1.0.0")),
            VersionConstraint(comparator="<", version=ComposerVersion(string="2.0.0")),
        )
    )


def test_composer_invalid_syntax():
    try:
        ComposerVersionRange.from_native(">1.0.0 <2.0.0")
        assert False, "Should have raised a ValueError"
    except ValueError:
        assert True


def test_composer_range_str_representation():
    version_range = ComposerVersionRange.from_native(">=1.0.0, <2.0.0")
    assert str(version_range) == "vers:composer/>=1.0.0|<2.0.0"
