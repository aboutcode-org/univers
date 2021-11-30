#
# Copyright (c) nexB Inc. and others.
# SPDX-License-Identifier: Apache-2.0
#
# Visit https://aboutcode.org and https://github.com/nexB/univers for support and download.

import pytest

from univers import versions
from univers.version_constraint import VersionConstraint


@pytest.mark.parametrize(
    "version, spec, expected",
    [
        ("2.7", "<=3.4", True),
        ("2.7.1", "<=3.4", True),
        ("2.7.1rc1", "<=3.4", True),
        ("2.7.15", "<=3.4", True),
        ("2.7.15rc1", "<=3.4", True),
        ("2.7", ">=3.4", False),
        ("2.7.1", ">=3.4", False),
        ("2.7.1rc1", ">=3.4", False),
        ("2.7.15", ">=3.4", False),
        ("2.7.15rc1", ">=3.4", False),
        ("0.0.0", ">=1.0.0", False),
        ("1.2.3", ">=1.0.0", True),
        ("1.2.3b1", ">=1.0.0", True),
        ("1.0.1b1", ">=1.0.0", True),
        ("1.0.0b1", ">=1.0.0", False),
        ("1.0.0b1", ">=1.0.0b1", True),
    ],
)
def test_pypi_comparison(version, spec, expected):
    version = versions.PypiVersion(version)
    constraint = VersionConstraint.from_string(
        string=spec,
        version_class=versions.PypiVersion,
    )
    assert (version in constraint) is expected


@pytest.mark.parametrize(
    "version, spec, expected",
    [
        ("2.7.1", "<=3.4.3", True),
        ("1.1.0", ">1.0.0", True),
        ("2.0.0", "<=2.0.0", True),
        ("1.9999.9999", "<=2.0.0", True),
        ("0.2.9", "<=2.0.0", True),
        ("1.9999.9999", "<2.0.0", True),
        ("0.1.1-alpha", ">=0.1.1-beta", False),
        ("1.0.0+20130313144700", "=1.0.0+9999999999", False),
    ],
)
def test_semver_comparison(version, spec, expected):
    version = versions.SemverVersion(version)
    constraint = VersionConstraint.from_string(
        string=spec,
        version_class=versions.SemverVersion,
    )
    assert (version in constraint) is expected
