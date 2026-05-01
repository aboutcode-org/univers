#
# Copyright (c) nexB Inc. and others.
# SPDX-License-Identifier: Apache-2.0
#
# Visit https://aboutcode.org and https://github.com/aboutcode-org/univers for support and download.

import json
from pathlib import Path

import pytest

from univers.versions import AlpineLinuxVersion
from univers.versions import InvalidVersion

from . import SchemaDrivenVersTest

TEST_DATA = Path(__file__).parent / "data" / "schema" / "alpine_version_cmp.json"


class AlpineVersionComparison(SchemaDrivenVersTest):
    def equality(self):
        """Compare version1 and version2 are equal."""
        return AlpineLinuxVersion(self.input_version1) == AlpineLinuxVersion(self.input_version2)

    def comparison(self):
        """Sort version1 and version2 and return them in the correct order."""
        sorts = sorted(
            [
                AlpineLinuxVersion(self.input_version1),
                AlpineLinuxVersion(self.input_version2),
            ]
        )
        return [sorts[0].string, sorts[1].string]


@pytest.mark.parametrize("test_case", json.load(open(TEST_DATA)))
def test_alpine_vers_cmp2(test_case):
    avc = AlpineVersionComparison.from_data(data=test_case)
    avc.assert_result()


@pytest.mark.parametrize(
    ("version", "expected_value"),
    [
        # dot immediately before revision marker (issue #59)
        ("0.12.5.-r0", "0.12.5-r0"),
        # dot instead of dash before revision number (issue #59)
        ("0.8.21.r2", "0.8.21-r2"),
        # dash as numeric version-component separator (issue #59)
        ("1.11-20-r0", "1.11.20-r0"),
        ("57-1-r2", "57.1-r2"),
        # single letter + digit suffix, e.g. OpenSSH portable releases (issue #59)
        ("1.9.5p2-r0", "1.9.5_p2-r0"),
        ("3.3.3p1-r3", "3.3.3_p1-r3"),
        ("6.6.2p1-r0", "6.6.2_p1-r0"),
        ("6.6.4p1-r1", "6.6.4_p1-r1"),
        ("6.7.1p1-r1", "6.7.1_p1-r1"),
        # _git snapshot suffix mapped to _alpha for comparison (issue #59)
        ("5.15.3_git20200401-r0", "5.15.3_alpha20200401-r0"),
        ("5.15.3_git20210510-r0", "5.15.3_alpha20210510-r0"),
    ],
)
def test_alpine_extended_version_formats(version, expected_value):
    """Versions with Alpine-specific patterns must parse and normalise correctly."""
    v = AlpineLinuxVersion(version)
    assert v.value == expected_value


@pytest.mark.parametrize(
    ("smaller", "larger"),
    [
        # portable-release ordering: p1 < p2
        ("1.9.5p1-r0", "1.9.5p2-r0"),
        # git snapshot is a pre-release, comes before the stable release
        ("5.15.3_git20200401-r0", "5.15.3-r0"),
        # earlier git snapshot < later git snapshot
        ("5.15.3_git20200401-r0", "5.15.3_git20210510-r0"),
        # dash-separated version component ordering
        ("1.11-20-r0", "1.11-21-r0"),
        ("57-1-r2", "57-2-r0"),
        # dot-r vs normal version
        ("0.8.21.r2", "0.8.22-r0"),
    ],
)
def test_alpine_extended_version_comparison(smaller, larger):
    """Extended Alpine version formats must compare in the correct order."""
    v1 = AlpineLinuxVersion(smaller)
    v2 = AlpineLinuxVersion(larger)
    assert v1 < v2


@pytest.mark.parametrize(
    "test_case",
    [
        # these are the tests are not supported yet
        # when we start supporting these version,
        # they will be moved back to main test suite
        ("2.10.1", ">", "02.08.01b"),
        ("02.08.01b", "<", "4.77"),
        ("23_foo", ">", "4_beta"),
        ("1.06-r6", "<", "006"),
        ("006", ">", "1.0.0"),
        ("2.10.1", ">", "02.08.01b"),
        ("02.08.01b", "<", "4.77"),
        ("2.2.3-r2", "<", "013"),
        ("013", "<", "014-r1"),
        ("014-r1", ">", "1.3.1-r1"),
        ("3.0.0-r2", "<", "021109-r3"),
        ("021109-r3", "<", "20060512"),
        ("0.9.28.1", "<", "087-r1"),
        ("087-r1", "<", "103"),
        # invalid. do string sort
        ("1.0", "<", "1.0bc"),
    ],
)
def test_invalid_alpine_vers_cmp(test_case):
    v1, _, v2 = test_case
    with pytest.raises(InvalidVersion):
        AlpineLinuxVersion(v1)
        AlpineLinuxVersion(v2)
