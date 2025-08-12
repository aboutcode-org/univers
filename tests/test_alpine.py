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

TEST_DATA = Path(__file__).parent / "data" / "schema" / "alpine_test.json"


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
