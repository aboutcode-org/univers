# Copyright (c) Facebook, Inc. and its affiliates.
# SPDX-License-Identifier: MIT

import unittest

from univers.rpm import RpmVersion
from univers.rpm import compare_rpm_versions


class RpmMetadataTestCase(unittest.TestCase):
    def test_rpm_compare_versions(self):
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
            a = RpmVersion(*evr1)
            b = RpmVersion(*evr2)
            self.assertEqual(
                compare_rpm_versions(a, b),
                expected,
                f"failed: {evr1}, {evr2}, {expected}",
            )
