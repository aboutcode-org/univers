#
# Copyright (c) nexB Inc. and others.
# SPDX-License-Identifier: Apache-2.0
#
# Visit https://aboutcode.org and https://github.com/nexB/univers for support and download.

import operator
from typing import NamedTuple

import pytest
from univers.versions import AlpineLinuxVersion
from univers.versions import InvalidVersion


class AlpineVersionComparison(NamedTuple):
    """
    We have this class to drive the tests, where we compare
    `version1` and `version2` on the basis of the `comparator`
    """

    version1: str
    comparator: str
    version2: str

    @classmethod
    def from_string(cls, s: str):
        segments = s.split()

        assert len(segments) == 3
        return cls(*segments)

    def compare(self):
        """
        Compare version1 and version2 with comparator
        and return True if comparison is valid, False otherwise
        """
        v1 = AlpineLinuxVersion(self.version1)
        v2 = AlpineLinuxVersion(self.version2)
        COMPARATORS = {
            "<": operator.lt,
            ">": operator.gt,
            "=": operator.eq,
        }
        comparator = COMPARATORS[self.comparator]
        return comparator(v1, v2)


@pytest.mark.parametrize("test_case", open("./tests/data/alpine_test.txt").read().splitlines(False))
def test_alpine_vers_cmp(test_case):
    avc = AlpineVersionComparison.from_string(test_case)
    assert avc.compare()


@pytest.mark.parametrize(
    "test_case",
    [
        # these are the tests are not supported yet
        # when we start supporting these version,
        # they will be moved back to main test suite
        "2.10.1 > 02.08.01b",
        "02.08.01b < 4.77",
        "23_foo > 4_beta",
        "1.06-r6 < 006",
        "006 > 1.0.0",
        "2.10.1 > 02.08.01b",
        "02.08.01b < 4.77",
        "2.2.3-r2 < 013",
        "013 < 014-r1",
        "014-r1 > 1.3.1-r1",
        "3.0.0-r2 < 021109-r3",
        "021109-r3 < 20060512",
        "0.9.28.1 < 087-r1",
        "087-r1 < 103",
        # invalid. do string sort
        "1.0 < 1.0bc",
    ],
)
def test_invalid_alpine_vers_cmp(test_case):
    avc = AlpineVersionComparison.from_string(test_case)
    with pytest.raises(InvalidVersion):
        AlpineLinuxVersion(avc.version1)
        AlpineLinuxVersion(avc.version2)
