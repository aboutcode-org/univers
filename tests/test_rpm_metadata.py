#!/usr/bin/env python3
# Copyright (c) Facebook, Inc. and its affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import unittest

from univers.rpm_metadata import RpmMetadata
from univers.rpm_metadata import _compare_values
from univers.rpm_metadata import compare_rpm_versions


class RpmMetadataTestCase(unittest.TestCase):
    def test_rpm_compare_versions(self):
        # name mismatch
        a = RpmMetadata("test-name1", 1, "2", "3")
        b = RpmMetadata("test-name2", 1, "2", "3")
        with self.assertRaises(ValueError):
            compare_rpm_versions(a, b)

        # Taste data was generated with:
        # rpmdev-vercmp <epoch1> <ver1> <release1> <epoch2> <ver2> <release2>
        # which also uses the same Python rpm lib.
        #
        # This number of test cases is excessive but does show how interesting
        # RPM version comparisons can be.
        test_evr_data = [
            # Non-alphanumeric (except ~) are ignored for equality
            ((1, "2", "3"), (1, "2", "3"), 0),  # 1:2-3 == 1:2-3
            ((1, ":2>", "3"), (1, "-2-", "3"), 0),  # 1::2>-3 == 1:-2--3
            ((1, "2", "3?"), (1, "2", "?3"), 0),  # 1:2-?3 == 1:2-3?
            # epoch takes precedence no matter what
            ((0, "2", "3"), (1, "2", "3"), -1),  # 0:2-3 < 1:2-3
            ((1, "1", "3"), (0, "2", "3"), 1),  # 1:1-3 > 0:2-3
            # version and release trigger the real comparison rules
            ((0, "1", "3"), (0, "2", "3"), -1),  # 0:1-3 < 0:2-3
            ((0, "~2", "3"), (0, "1", "3"), -1),  # 0:~2-3 < 0:1-3
            ((0, "~", "3"), (0, "1", "3"), -1),  # 0:~-3 < 0:1-3
            ((0, "1", "3"), (0, "~", "3"), 1),  # 0:1-3 > 0:~-3
            ((0, "^1", "3"), (0, "^", "3"), 1),  # 0:^1-3 > 0:^-3
            ((0, "^", "3"), (0, "^1", "3"), -1),  # 0:^-3 < 0:^1-3
            ((0, "0333", "b"), (0, "0033", "b"), 1),  # 0:0333-b > 0:0033-b
            ((0, "0033", "b"), (0, "0333", "b"), -1),  # 0:0033-b < 0:0333-b
            ((0, "3", "~~"), (0, "3", "~~~"), 1),  # 0:3-~~ > 0:3-~~~
            ((0, "3", "~~~"), (0, "3", "~~"), -1),  # 0:3-~~~ < 0:3-~~
            ((0, "3", "~~~"), (0, "3", "~~~"), 0),  # 0:3-~~~ == 0:3-~~~
            ((0, "a2aa", "b"), (0, "a2a", "b"), 1),  # 0:a2aa-b > 0:a2a-b
            ((0, "33", "b"), (0, "aaa", "b"), 1),  # 0:33-b > 0:aaa-b
        ]

        for evr1, evr2, expected in test_evr_data:
            a = RpmMetadata("test-name", *evr1)
            b = RpmMetadata("test-name", *evr2)
            self.assertEqual(
                compare_rpm_versions(a, b),
                expected,
                f"failed: {evr1}, {evr2}, {expected}",
            )

        # Test against some more canonical tests.  These are derived from
        # actual tests used for rpm itself.
        for ver1, ver2, expected in self._load_canonical_tests():
            self.assertEqual(
                _compare_values(ver1, ver2),
                expected,
                f"failed: {ver1}, {ver2}, {expected}",
            )
