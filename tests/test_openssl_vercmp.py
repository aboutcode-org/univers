#
# Copyright (c) nexB Inc. and others.
# SPDX-License-Identifier: Apache-2.0
#
# Visit https://aboutcode.org and https://github.com/aboutcode-org/univers for support and download.

import json
import operator
from pathlib import Path

import pytest

from tests import SchemaDrivenVersTest
from univers.versions import LegacyOpensslVersion
from univers.versions import OpensslVersion
from univers.versions import SemverVersion

TEST_DATA = Path(__file__).parent / "data" / "schema" / "openssl_version_cmp.json"


class OpenSSLVersionComp(SchemaDrivenVersTest):
    def equality(self):
        """Compare version1 and version2 are equal."""
        return OpensslVersion(self.input_version1) == OpensslVersion(self.input_version2)

    def comparison(self):
        """Sort versions and return them in the correct order."""
        return [str(v) for v in sorted(map(OpensslVersion, self.input["versions"]))]


@pytest.mark.parametrize("test_case", json.load(open(TEST_DATA)))
def test_openssl_vers_cmp(test_case):
    avc = OpenSSLVersionComp.from_data(data=test_case)
    avc.assert_result()


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
