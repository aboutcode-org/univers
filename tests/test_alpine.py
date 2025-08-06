#
# Copyright (c) nexB Inc. and others.
# SPDX-License-Identifier: Apache-2.0
#
# Visit https://aboutcode.org and https://github.com/aboutcode-org/univers for support and download.

import operator
from typing import NamedTuple

import pytest

from univers.versions import AlpineLinuxVersion
from univers.versions import InvalidVersion
from typing import Optional
from typing import Union
import json

TEST_DATA = []


class AlpineVersionComparisonNew(NamedTuple):
    """
    We have this class to drive the tests, where we compare
    `version1` and `version2` on the basis of the `comparator`
    """

    test_type: str
    test_group: str
    input: dict
    expected_output: Union[list, bool]

    @classmethod
    def from_data(cls, data: dict):
        return cls(**data)

    @property
    def input_scheme(self):
        return self.input["input_scheme"]

    @property
    def input_version1(self):
        return self.input["versions"][0]

    @property
    def input_version2(self):
        return self.input["versions"][1]

    @property
    def expected_output_version1(self):
        return self.expected_output[0]

    @property
    def expected_output_version2(self):
        return self.expected_output[0]

    def compare(self):
        if self.test_type == "equality":
            self.equality()
        elif self.test_type == "comparison":
            self.comparison()
        else:
            raise Exception(f"Unknown test_type: {self.test_type}")

    def equality(self):
        """
        Compare version1 and version2 are equal
        """
        v1 = AlpineLinuxVersion(self.input_version1)
        v2 = AlpineLinuxVersion(self.input_version2)
        assert operator.eq(v1, v2)

    def comparison(self):
        """
        Sort version1 and version2 and return them in the correct order
        """
        v1 = AlpineLinuxVersion(self.input_version1)
        v2 = AlpineLinuxVersion(self.input_version2)
        sorts = sorted([v1, v2])
        results = [sorts[0].string, sorts[1].string]
        assert results == self.expected_output


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

    def compare_original(self):
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

    def compare_dump(self):
        """
        Compare version1 and version2 with comparator
        and return True if comparison is valid, False otherwise
        """
        if self.comparator == "=":
            test = {
                "test_group": "advanced",
                "test_type": "equality",
                "input": {
                    "input_scheme": "apk",
                    "versions": [self.version1, self.version2],
                },
                "expected_output": True,
            }

            TEST_DATA.append(test)

        elif self.comparator in ("><"):
            if self.comparator == ">":
                ver1 = self.version2
                ver2 = self.version1
            else:
                ver1 = self.version1
                ver2 = self.version2

            test = {
                "test_group": "advanced",
                "test_type": "comparison",
                "input": {
                    "input_scheme": "apk",
                    "versions": [self.version1, self.version2],
                },
                "expected_output": [ver1, ver2],
            }
            TEST_DATA.append(test)


@pytest.mark.parametrize("test_case", open("./tests/data/alpine_test.txt").read().splitlines(False))
def test_alpine_vers_cmp(test_case):
    # avc = AlpineVersionComparison.from_string(test_case)
    # avc.compare_dump()
    pass


@pytest.mark.parametrize("test_case", json.load(open("foo.json")))
def test_alpine_vers_cmp2(test_case):
    avc = AlpineVersionComparisonNew.from_data(data=test_case)
    avc.compare()


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

#
# def teardown_module(module):
#     import json
#     print("="*50)
#     with open("foo.json", "w") as o:
#         json.dump(TEST_DATA, o, indent=2)
#     print("="*50)
