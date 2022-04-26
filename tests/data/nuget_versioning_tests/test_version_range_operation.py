# Copyright (c) .NET Foundation. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
# URL: https://github.com/NuGet/NuGet.Client
# Ported to Python from the C# NuGet test suite and significantly modified

import unittest

import pytest


class VersionRangeSetTests(unittest.TestCase):
    @pytest.mark.parametrize(
        [],
        [
            ("[1.0.0, )", "[1.0.0, )"),
            ("[1.0.0, )", "[1.0.1, )"),
            ("[1.0.0-alpha, )", "[1.0.0, )"),
            ("[1.0.0]", "[1.0.0]"),
            ("[1.0.0, 2.0.0]", "(1.1.0, 1.5.0)"),
            ("(, )", "[1.0.0, )"),
            ("(0.0.0, )", "[1.0.0, )"),
            ("(0.0.0, 0.0.0)", "(0.0.0, 0.0.0)"),
            ("(1.0.0-alpha, 2.0.0]", "[2.0.0]"),
            ("(1.0.0-alpha, 2.0.0]", "(2.0.0, 2.0.0)"),
            ("(2.0.0, 2.0.0)", "(2.0.0, 2.0.0)"),
        ],
    )
    def test_VersionRangeSet_SubSetTest(self, superSet, subSet):

        superSetRange = VersionRange(superSet)
        subSetRange = VersionRange(subSet)

        assert subSetRange.IsSubSetOrEqualTo(superSetRange)

    @pytest.mark.parametrize(
        [],
        [
            ("[1.0.1, )", "[1.0.0, )"),
            ("[1.0.1, )", "[1.0.1-alpha, )"),
            ("[1.0.0, 2.0.0)", "[1.0.0, 2.0.0]"),
            ("[1.0.0, 2.0.0)", "[1.0.0-alpha, 2.0.0)"),
            ("[1.0.0, 2.0.0)", "[ , 2.0.0)"),
            ("(1.0.0, 2.0.0)", "[1.0.0, 2.0.0)"),
            ("(1.0.0, 2.0.0)", "[1.0.0]"),
            ("(1.0.0, 2.0.0)", "[1.0.0-beta]"),
            ("(1.0.0-alpha, 2.0.0]", "(3.0.0, 3.0.0)"),
            ("(3.0.0, 3.0.0)", "[3.0.0]"),
        ],
    )
    def test_VersionRangeSet_SubSetTestNeg(self, superSet, subSet):

        superSetRange = VersionRange(superSet)
        subSetRange = VersionRange(subSet)

        assert not subSetRange.IsSubSetOrEqualTo(superSetRange)

    @pytest.mark.parametrize(
        [],
        [
            ("[1.0.0, )", "[1.0.0, )", "[1.0.0, )"),
            ("(, 1.0.0)", "[0.0.0, 1.0.0)", "(, 1.0.0)"),
            ("[1.0.0, )", "[1.0.0, )", "(1.0.0, )"),
            ("[1.0.0-alpha, )", "[1.0.0-alpha, )", "[1.0.0, )"),
            ("[1.0.0, 2.0.0]", "[1.0.0]", "[2.0.0]"),
            ("[1.0.0, 2.0.0-beta-1]", "[1.0.0]", "[2.0.0-beta-1]"),
            ("[1.0.0, 3.0.0]", "[1.0.0, 2.0.0]", "[1.5.0, 3.0.0]"),
            ("(1.0.0, 3.0.0)", "(1.0.0, 2.0.0]", "[1.5.0, 3.0.0)"),
            ("[1.0.0, 2.0.0]", "(1.0.0, 2.0.0)", "[1.0.0, 2.0.0]"),
            ("[1.0.0, 2.0.0]", "[1.0.0, 1.5.0)", "(1.5.0, 2.0.0]"),
            ("(, )", "[1.0.0, 1.5.0)", "[, ]"),
            ("(, )", "[1.0.0, 1.5.0)", "(, )"),
            ("(, )", "[1.0.0-alpha, )", "(, 2.0.0-beta]"),
            (
                "[0.0.0-alpha-1, 9000.0.0.1]",
                "[0.0.0-alpha-1, 0.0.0-alpha-2]",
                "[10.0.0.0, 9000.0.0.1]",
            ),
        ],
    )
    def test_VersionRangeSet_CombineTwoRanges(self, expected, rangeA, rangeB):

        a = VersionRange(rangeA)
        b = VersionRange(rangeB)

        ranges = [a, b]
        combined = VersionRange.Combine(ranges)

        rangesRev = [b, a]
        combinedRev = VersionRange.Combine(rangesRev)

        assert combined.to_string() == expected

        # Verify the order has no effect
        assert combinedRev.to_string() == expected

    def test_VersionRangeSet_CombineSingleRangeList(self):

        a = VersionRange("[1.0.0, )")
        ranges = [a]

        combined = VersionRange.Combine(ranges)

        assert combined.to_string() == a.to_string()

    def test_VersionRangeSet_SpecialCaseRangeCombine_NonePlusOne(self):

        ranges = [VersionRange, VersionRange("[1.0.0]")]

        combined = VersionRange.Combine(ranges)

        assert combined.to_string() == "[1.0.0, 1.0.0]"

    def test_VersionRangeSet_RemoveEmptyRanges(self):

        ranges = [
            VersionRange,
            VersionRange("(5.0.0, 5.0.0)"),
            VersionRange("(3.0.0-alpha, 3.0.0-alpha)"),
            VersionRange("[1.0.0, 2.0.0]"),
        ]

        combined = VersionRange.Combine(ranges)

        assert combined.to_string() == "[1.0.0, 2.0.0]"

    def test_VersionRangeSet_CombineMultipleRanges(self):

        ranges = [
            VersionRange("[1.0.0]"),
            VersionRange("[2.0.0]"),
            VersionRange("[3.0.0]"),
            VersionRange("[4.0.0-beta-1]"),
            VersionRange("[5.0.1-rc4]"),
        ]

        combined = VersionRange.Combine(ranges)

        ranges.Reverse()

        assert combined.to_string() == "[1.0.0, 5.0.1-rc4]"

    def test_VersionRangeSet_CommonSubSet_SingleRangeList(self):

        a = VersionRange("[1.0.0, )")
        ranges = [a]

        combined = VersionRange.CommonSubSet(ranges)

        assert combined.to_string() == a.to_string()

    def test_VersionRangeSet_CommonSubSet_EmptyRangeList(self):

        ranges = []

        combined = VersionRange.CommonSubSet(ranges)

        assert combined.to_string() == VersionRange.to_string()

    @pytest.mark.parametrize(
        [],
        [
            ("[2.0.0, )", "[1.0.0, )", "[2.0.0, )"),
            ("[0.0.0, 1.0.0)", "[0.0.0, 2.0.0)", "(, 1.0.0)"),
            ("[2.0.0, 3.0.0]", "(1.0.0, 3.0.0]", "[2.0.0, 4.0.0)"),
            ("(0.0.0, 0.0.0)", "[1.0.0, 3.0.0]", "[4.0.0, 5.0.0)"),
            ("(2.0.0, 3.0.0]", "(2.0.0, 3.0.0]", "[2.0.0, 4.0.0)"),
            ("(0.0.0, 0.0.0)", "[1.0.0, 3.0.0)", "[3.0.0, 5.0.0)"),
            ("(0.0.0, 0.0.0)", "[1.0.0, 3.0.0)", "[4.0.0, 5.0.0)"),
            ("(1.5.0, 2.0.0]", "[1.0.0, 2.0.0]", "(1.5.0, 3.0.0]"),
            ("[1.0.0, 1.5.0)", "[1.0.0, 1.5.0)", "[, ]"),
            ("(0.0.0, 0.0.0)", "[1.0.0]", "[2.0.0]"),
        ],
    )
    def test_VersionRangeSet_CommonSubSet(self, expected, rangeA, rangeB):

        a = VersionRange(rangeA)
        b = VersionRange(rangeB)

        ranges = [a, b]
        combined = VersionRange.CommonSubSet(ranges)

        rangesRev = [b, a]
        combinedRev = VersionRange.CommonSubSet(rangesRev)

        assert combined.to_string() == expected

        # Verify the order has no effect
        assert combinedRev.to_string() == expected

    def test_VersionRangeSet_CommonSubSetInMultipleRanges(self):

        ranges = [
            VersionRange("[1.0.0, 5.0.0)"),
            VersionRange("[2.0.0, 6.0.0]"),
            VersionRange("[4.0.0, 5.0.0]"),
        ]

        combined = VersionRange.CommonSubSet(ranges)

        assert combined.to_string() == "[4.0.0, 5.0.0)"
