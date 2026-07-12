#
# Copyright (c) 2019 JFrog LTD
# SPDX-License-Identifier: MIT
#
# Visit https://aboutcode.org and https://github.com/aboutcode-org/univers for support and download.

import json
from pathlib import Path

import pytest

from univers.versions import ConanVersion

from . import SchemaDrivenVersTest

TEST_DATA = Path(__file__).parent / "data" / "schema" / "conan_version_cmp.json"


class ConanVersionComparison(SchemaDrivenVersTest):
    def equality(self):
        """Compare version1 and version2 are equal."""
        return ConanVersion(self.input_version1) == ConanVersion(self.input_version2)

    def comparison(self):
        """Sort version1 and version2 and return them in the correct order."""
        sorts = sorted(
            [
                ConanVersion(self.input_version1),
                ConanVersion(self.input_version2),
            ]
        )
        return [sorts[0].string, sorts[1].string]


@pytest.mark.parametrize("test_case", json.load(open(TEST_DATA)))
def test_conan_version_comparison(test_case):
    avc = ConanVersionComparison.from_data(data=test_case)
    avc.assert_result()


def test_comparison_with_integer():
    v1 = ConanVersion("13.0")
    # Issue: https://github.com/conan-io/conan/issues/12907
    assert v1 > ConanVersion("5")
    assert v1 >= ConanVersion("5")
    assert v1 < ConanVersion("20")
    assert v1 <= ConanVersion("20")
    assert v1 == ConanVersion("13")
    assert v1 != ConanVersion("14")


def test_elem_comparison():
    v1 = ConanVersion("1.2.3b.4-pre.1.2b+build.1.1b")
    major = v1.major
    assert major < 2
    assert major < "2"
    assert major == 1
    assert major != 3
    assert major > 0
    assert str(major) == "1"
    patch = v1.patch
    assert patch < 4
    assert patch > 2
    assert patch < "3c"
    assert patch > "3a"
    assert patch == "3b"
    micro = v1.micro
    assert micro > 3
    assert micro < 5
    assert micro == 4
