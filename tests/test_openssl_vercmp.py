#
# Copyright (c) nexB Inc. and others.
# SPDX-License-Identifier: Apache-2.0
#
# Visit https://aboutcode.org and https://github.com/nexB/univers for support and download.

import operator

import pytest
from univers.versions import LegacyOpensslVersion
from univers.versions import OpensslVersion
from univers.versions import SemverVersion


def compare(version1, comparator, version2):
    """
    Compare version1 and version2 with comparator
    and return True if comparison is valid, False otherwise
    """
    operator_comparator = {
        "<": operator.lt,
        ">": operator.gt,
        "<=": operator.le,
        ">=": operator.ge,
        "==": operator.eq,
        "!=": operator.ne,
    }
    compare = operator_comparator[comparator]
    return compare(version1, version2)


@pytest.mark.parametrize(
    "version1, comparator, version2, expected",
    [
        ("1.0.0e", ">", "1.0.0r", False),
        ("1.0.0e", "<", "1.0.0r", True),
        ("1.0.0e", ">=", "1.0.0r", False),
        ("1.0.0e", "<=", "1.0.0r", True),
        ("1.0.0e", "==", "1.0.0r", False),
        ("1.0.0e", "!=", "1.0.0r", True),
        ("1.0.1f", ">", "1.0.1m", False),
        ("1.0.1f", "<", "1.0.1m", True),
        ("1.0.1f", ">=", "1.0.1m", False),
        ("1.0.1f", "<=", "1.0.1m", True),
        ("1.0.1f", "==", "1.0.1m", False),
        ("1.0.1f", "!=", "1.0.1m", True),
        ("1.0.1g", ">", "1.0.2a", False),
        ("1.0.1g", "<", "1.0.2a", True),
        ("1.0.1g", ">=", "1.0.2a", False),
        ("1.0.1g", "<=", "1.0.2a", True),
        ("1.0.1g", "==", "1.0.2a", False),
        ("1.0.1g", "!=", "1.0.2a", True),
        ("1.0.1h", ">", "0.9.8", True),
        ("1.0.1h", "<", "0.9.8", False),
        ("1.0.1h", ">=", "0.9.8", True),
        ("1.0.1h", "<=", "0.9.8", False),
        ("1.0.1h", "==", "0.9.8", False),
        ("1.0.1h", "!=", "0.9.8", True),
        ("1.0.1h", ">", "0.9.8a", True),
        ("1.0.1h", "<", "0.9.8a", False),
        ("1.0.1h", ">=", "0.9.8a", True),
        ("1.0.1h", "<=", "0.9.8a", False),
        ("1.0.1h", "==", "0.9.8a", False),
        ("1.0.1h", "!=", "0.9.8a", True),
        ("0.9.8lt", ">", "0.9.8ztl", False),
        ("0.9.8lt", "<", "0.9.8ztl", True),
        ("0.9.8lt", ">=", "0.9.8ztl", False),
        ("0.9.8lt", "<=", "0.9.8ztl", True),
        ("0.9.8lt", "==", "0.9.8ztl", False),
        ("0.9.8lt", "!=", "0.9.8ztl", True),
        ("1.1.1ag", ">", "1.1.1ag", False),
        ("1.1.1ag", "<", "1.1.1ag", False),
        ("1.1.1ag", ">=", "1.1.1ag", True),
        ("1.1.1ag", "<=", "1.1.1ag", True),
        ("1.1.1ag", "==", "1.1.1ag", True),
        ("1.1.1ag", "!=", "1.1.1ag", False),
    ],
)
def test_old_old_comparison(version1, comparator, version2, expected):
    old1 = OpensslVersion(version1)
    old2 = OpensslVersion(version2)
    assert compare(old1, comparator, old2) is expected


@pytest.mark.parametrize(
    "version1, comparator, version2, expected",
    [
        ("3.0.0", ">", "1.1.1z", True),
        ("3.0.0", "<", "1.1.1z", False),
        ("3.0.0", ">=", "1.1.1z", True),
        ("3.0.0", "<=", "1.1.1z", False),
        ("3.0.0", "==", "1.1.1z", False),
        ("3.0.0", "!=", "1.1.1z", True),
        ("3.1.0", ">", "1.0.1m", True),
        ("3.1.0", "<", "1.0.1m", False),
        ("3.1.0", ">=", "1.0.1m", True),
        ("3.1.0", "<=", "1.0.1m", False),
        ("3.1.0", "==", "1.0.1m", False),
        ("3.1.0", "!=", "1.0.1m", True),
        ("3.0.3", ">", "1.0.2a", True),
        ("3.0.3", "<", "1.0.2a", False),
        ("3.0.3", ">=", "1.0.2a", True),
        ("3.0.3", "<=", "1.0.2a", False),
        ("3.0.3", "==", "1.0.2a", False),
        ("3.0.3", "!=", "1.0.2a", True),
        ("3.0.1", ">", "0.9.8ztl", True),
        ("3.0.1", "<", "0.9.8ztl", False),
        ("3.0.1", ">=", "0.9.8ztl", True),
        ("3.0.1", "<=", "0.9.8ztl", False),
        ("3.0.1", "==", "0.9.8ztl", False),
        ("3.0.1", "!=", "0.9.8ztl", True),
        ("4.1.11", ">", "1.1.1ag", True),
        ("4.1.11", "<", "1.1.1ag", False),
        ("4.1.11", ">=", "1.1.1ag", True),
        ("4.1.11", "<=", "1.1.1ag", False),
        ("4.1.11", "==", "1.1.1ag", False),
        ("4.1.11", "!=", "1.1.1ag", True),
    ],
)
def test_new_old_comparison(version1, comparator, version2, expected):
    new = OpensslVersion(version1)
    old = OpensslVersion(version2)
    assert compare(new, comparator, old) is expected


@pytest.mark.parametrize(
    "version1, comparator, version2, expected",
    [
        ("1.1.1z", ">", "3.0.0", False),
        ("1.1.1z", "<", "3.0.0", True),
        ("1.1.1z", ">=", "3.0.0", False),
        ("1.1.1z", "<=", "3.0.0", True),
        ("1.1.1z", "==", "3.0.0", False),
        ("1.1.1z", "!=", "3.0.0", True),
        ("1.0.1m", ">", "3.1.0", False),
        ("1.0.1m", "<", "3.1.0", True),
        ("1.0.1m", ">=", "3.1.0", False),
        ("1.0.1m", "<=", "3.1.0", True),
        ("1.0.1m", "==", "3.1.0", False),
        ("1.0.1m", "!=", "3.1.0", True),
        ("1.0.2a", ">", "3.0.3", False),
        ("1.0.2a", "<", "3.0.3", True),
        ("1.0.2a", ">=", "3.0.3", False),
        ("1.0.2a", "<=", "3.0.3", True),
        ("1.0.2a", "==", "3.0.3", False),
        ("1.0.2a", "!=", "3.0.3", True),
        ("0.9.8ztl", ">", "3.0.1", False),
        ("0.9.8ztl", "<", "3.0.1", True),
        ("0.9.8ztl", ">=", "3.0.1", False),
        ("0.9.8ztl", "<=", "3.0.1", True),
        ("0.9.8ztl", "==", "3.0.1", False),
        ("0.9.8ztl", "!=", "3.0.1", True),
        ("1.1.1ag", ">", "4.1.11", False),
        ("1.1.1ag", "<", "4.1.11", True),
        ("1.1.1ag", ">=", "4.1.11", False),
        ("1.1.1ag", "<=", "4.1.11", True),
        ("1.1.1ag", "==", "4.1.11", False),
        ("1.1.1ag", "!=", "4.1.11", True),
    ],
)
def test_old_new_comparison(version1, comparator, version2, expected):
    old = OpensslVersion(version1)
    new = OpensslVersion(version2)
    assert compare(old, comparator, new) is expected


@pytest.mark.parametrize(
    "version1, comparator, version2, expected",
    [
        ("3.0.0", ">", "3.0.0", False),
        ("3.0.0", "<", "3.0.0", False),
        ("3.0.0", ">=", "3.0.0", True),
        ("3.0.0", "<=", "3.0.0", True),
        ("3.0.0", "==", "3.0.0", True),
        ("3.0.0", "!=", "3.0.0", False),
        ("3.1.0", ">", "3.0.2", True),
        ("3.1.0", "<", "3.0.2", False),
        ("3.1.0", ">=", "3.0.2", True),
        ("3.1.0", "<=", "3.0.2", False),
        ("3.1.0", "==", "3.0.2", False),
        ("3.1.0", "!=", "3.0.2", True),
        ("3.0.3", ">", "4.0.2", False),
        ("3.0.3", "<", "4.0.2", True),
        ("3.0.3", ">=", "4.0.2", False),
        ("3.0.3", "<=", "4.0.2", True),
        ("3.0.3", "==", "4.0.2", False),
        ("3.0.3", "!=", "4.0.2", True),
        ("3.0.1", ">", "3.0.2", False),
        ("3.0.1", "<", "3.0.2", True),
        ("3.0.1", ">=", "3.0.2", False),
        ("3.0.1", "<=", "3.0.2", True),
        ("3.0.1", "==", "3.0.2", False),
        ("3.0.1", "!=", "3.0.2", True),
        ("4.1.11", ">", "4.2.0", False),
        ("4.1.11", "<", "4.2.0", True),
        ("4.1.11", ">=", "4.2.0", False),
        ("4.1.11", "<=", "4.2.0", True),
        ("4.1.11", "==", "4.2.0", False),
        ("4.1.11", "!=", "4.2.0", True),
    ],
)
def test_new_new_comparison(version1, comparator, version2, expected):
    new1 = OpensslVersion(version1)
    new2 = OpensslVersion(version2)
    assert compare(new1, comparator, new2) is expected


@pytest.mark.parametrize(
    "version1, comparator, version2, expected",
    [
        ("3.2.3", ">", "1.0.0r", "TypeError"),
        ("3.2.3", "<", "1.0.0r", "TypeError"),
        ("3.2.3", ">=", "1.0.0r", "TypeError"),
        ("3.2.3", "<=", "1.0.0r", "TypeError"),
        ("3.2.3", "==", "1.0.0r", False),
        ("3.2.3", "!=", "1.0.0r", True),
        ("1.0.1f", ">", "1.0.1m", "TypeError"),
        ("1.0.1f", "<", "1.0.1m", "TypeError"),
        ("1.0.1f", ">=", "1.0.1m", "TypeError"),
        ("1.0.1f", "<=", "1.0.1m", "TypeError"),
        ("1.0.1f", "==", "1.0.1m", False),
        ("1.0.1f", "!=", "1.0.1m", True),
        ("1.0.1g", ">", "1.0.2a", "TypeError"),
        ("1.0.1g", "<", "1.0.2a", "TypeError"),
        ("1.0.1g", ">=", "1.0.2a", "TypeError"),
        ("1.0.1g", "<=", "1.0.2a", "TypeError"),
        ("1.0.1g", "==", "1.0.2a", False),
        ("1.0.1g", "!=", "1.0.2a", True),
        ("3.0.0", ">", "0.9.8", "TypeError"),
        ("3.0.0", "<", "0.9.8", "TypeError"),
        ("3.0.0", ">=", "0.9.8", "TypeError"),
        ("3.0.0", "<=", "0.9.8", "TypeError"),
        ("3.0.0", "==", "0.9.8", False),
        ("3.0.0", "!=", "0.9.8", True),
        ("3.0.0", ">", "0.9.8a", "TypeError"),
        ("3.0.0", "<", "0.9.8a", "TypeError"),
        ("3.0.0", ">=", "0.9.8a", "TypeError"),
        ("3.0.0", "<=", "0.9.8a", "TypeError"),
        ("3.0.0", "==", "0.9.8a", False),
        ("3.0.0", "!=", "0.9.8a", True),
        ("0.9.8lt", ">", "0.9.8ztl", "TypeError"),
        ("0.9.8lt", "<", "0.9.8ztl", "TypeError"),
        ("0.9.8lt", ">=", "0.9.8ztl", "TypeError"),
        ("0.9.8lt", "<=", "0.9.8ztl", "TypeError"),
        ("0.9.8lt", "==", "0.9.8ztl", False),
        ("0.9.8lt", "!=", "0.9.8ztl", True),
        ("0.9.1", ">", "0.9.1", "TypeError"),
        ("0.9.1", "<", "0.9.1", "TypeError"),
        ("0.9.1", ">=", "0.9.1", "TypeError"),
        ("0.9.1", "<=", "0.9.1", "TypeError"),
        ("0.9.1", "==", "0.9.1", False),
        ("0.9.1", "!=", "0.9.1", True),
    ],
)
def test_openssl_legacy_comparison(version1, comparator, version2, expected):
    openssl = OpensslVersion(version1)
    legacy = LegacyOpensslVersion(version2)
    try:
        result = compare(openssl, comparator, legacy)
    except TypeError:
        result = "TypeError"
    assert result is expected


@pytest.mark.parametrize(
    "version1, comparator, version2, expected",
    [
        ("3.2.3", ">", "1.0.0r", "TypeError"),
        ("3.2.3", "<", "1.0.0r", "TypeError"),
        ("3.2.3", ">=", "1.0.0r", "TypeError"),
        ("3.2.3", "<=", "1.0.0r", "TypeError"),
        ("3.2.3", "==", "1.0.0r", False),
        ("3.2.3", "!=", "1.0.0r", True),
        ("1.0.1f", ">", "1.0.1m", "TypeError"),
        ("1.0.1f", "<", "1.0.1m", "TypeError"),
        ("1.0.1f", ">=", "1.0.1m", "TypeError"),
        ("1.0.1f", "<=", "1.0.1m", "TypeError"),
        ("1.0.1f", "==", "1.0.1m", False),
        ("1.0.1f", "!=", "1.0.1m", True),
        ("1.0.1g", ">", "1.0.2a", "TypeError"),
        ("1.0.1g", "<", "1.0.2a", "TypeError"),
        ("1.0.1g", ">=", "1.0.2a", "TypeError"),
        ("1.0.1g", "<=", "1.0.2a", "TypeError"),
        ("1.0.1g", "==", "1.0.2a", False),
        ("1.0.1g", "!=", "1.0.2a", True),
        ("3.0.0", ">", "0.9.8", "TypeError"),
        ("3.0.0", "<", "0.9.8", "TypeError"),
        ("3.0.0", ">=", "0.9.8", "TypeError"),
        ("3.0.0", "<=", "0.9.8", "TypeError"),
        ("3.0.0", "==", "0.9.8", False),
        ("3.0.0", "!=", "0.9.8", True),
        ("3.0.0", ">", "0.9.8a", "TypeError"),
        ("3.0.0", "<", "0.9.8a", "TypeError"),
        ("3.0.0", ">=", "0.9.8a", "TypeError"),
        ("3.0.0", "<=", "0.9.8a", "TypeError"),
        ("3.0.0", "==", "0.9.8a", False),
        ("3.0.0", "!=", "0.9.8a", True),
        ("0.9.8lt", ">", "0.9.8ztl", "TypeError"),
        ("0.9.8lt", "<", "0.9.8ztl", "TypeError"),
        ("0.9.8lt", ">=", "0.9.8ztl", "TypeError"),
        ("0.9.8lt", "<=", "0.9.8ztl", "TypeError"),
        ("0.9.8lt", "==", "0.9.8ztl", False),
        ("0.9.8lt", "!=", "0.9.8ztl", True),
        ("0.9.1", ">", "0.9.1", "TypeError"),
        ("0.9.1", "<", "0.9.1", "TypeError"),
        ("0.9.1", ">=", "0.9.1", "TypeError"),
        ("0.9.1", "<=", "0.9.1", "TypeError"),
        ("0.9.1", "==", "0.9.1", False),
        ("0.9.1", "!=", "0.9.1", True),
    ],
)
def test_openssl_semver_comparison(version1, comparator, version2, expected):
    openssl = OpensslVersion(version1)
    semver = SemverVersion(version2)
    try:
        result = compare(openssl, comparator, semver)
    except TypeError:
        result = "TypeError"
    assert result is expected
