# Copyright (c) .NET Foundation. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
# URL: https://github.com/NuGet/NuGet.Client
# Ported to Python from the C# NuGet test suite and significantly modified

import pytest

from univers.version_range import NugetVersionRange


@pytest.mark.parametrize(
    "superSet, subSet",
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
def test_VersionRangeSet_SubSetTest(superSet, subSet):
    superSetRange = NugetVersionRange(superSet)
    subSetRange = NugetVersionRange(subSet)
    assert subSetRange.IsSubSetOrEqualTo(superSetRange)


@pytest.mark.parametrize(
    "superSet, subSet",
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
def test_VersionRangeSet_SubSetTestNeg(superSet, subSet):
    superSetRange = NugetVersionRange(superSet)
    subSetRange = NugetVersionRange(subSet)
    assert not subSetRange.IsSubSetOrEqualTo(superSetRange)


@pytest.mark.parametrize(
    "expected, rangeA, rangeB",
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
def test_VersionRangeSet_CombineTwoRanges(expected, rangeA, rangeB):
    a = NugetVersionRange(rangeA)
    b = NugetVersionRange(rangeB)

    ranges = [a, b]
    combined = NugetVersionRange.Combine(ranges)

    rangesRev = [b, a]
    combinedRev = NugetVersionRange.Combine(rangesRev)

    assert combined.to_string() == expected

    # Verify the order has no effect
    assert combinedRev.to_string() == expected


def test_VersionRangeSet_CombineSingleRangeList():
    a = NugetVersionRange("[1.0.0, )")
    ranges = [a]
    combined = NugetVersionRange.Combine(ranges)
    assert combined.to_string() == a.to_string()


def test_VersionRangeSet_SpecialCaseRangeCombine_NonePlusOne():
    ranges = [NugetVersionRange, NugetVersionRange("[1.0.0]")]
    combined = NugetVersionRange.Combine(ranges)
    assert combined.to_string() == "[1.0.0, 1.0.0]"


def test_VersionRangeSet_RemoveEmptyRanges():
    ranges = [
        NugetVersionRange,
        NugetVersionRange("(5.0.0, 5.0.0)"),
        NugetVersionRange("(3.0.0-alpha, 3.0.0-alpha)"),
        NugetVersionRange("[1.0.0, 2.0.0]"),
    ]

    combined = NugetVersionRange.Combine(ranges)
    assert combined.to_string() == "[1.0.0, 2.0.0]"


def test_VersionRangeSet_CombineMultipleRanges():
    ranges = [
        NugetVersionRange("[1.0.0]"),
        NugetVersionRange("[2.0.0]"),
        NugetVersionRange("[3.0.0]"),
        NugetVersionRange("[4.0.0-beta-1]"),
        NugetVersionRange("[5.0.1-rc4]"),
    ]

    combined = NugetVersionRange.Combine(ranges)
    ranges.Reverse()
    assert combined.to_string() == "[1.0.0, 5.0.1-rc4]"


def test_VersionRangeSet_CommonSubSet_SingleRangeList():
    a = NugetVersionRange("[1.0.0, )")
    ranges = [a]
    combined = NugetVersionRange.CommonSubSet(ranges)
    assert combined.to_string() == a.to_string()


def test_VersionRangeSet_CommonSubSet_EmptyRangeList():
    ranges = []
    combined = NugetVersionRange.CommonSubSet(ranges)
    assert combined.to_string() == NugetVersionRange.to_string()


@pytest.mark.parametrize(
    "expected, rangeA, rangeB",
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
def test_VersionRangeSet_CommonSubSet(expected, rangeA, rangeB):
    a = NugetVersionRange(rangeA)
    b = NugetVersionRange(rangeB)
    ranges = [a, b]
    combined = NugetVersionRange.CommonSubSet(ranges)
    rangesRev = [b, a]
    combinedRev = NugetVersionRange.CommonSubSet(rangesRev)
    assert combined.to_string() == expected
    # Verify the order has no effect
    assert combinedRev.to_string() == expected


def test_VersionRangeSet_CommonSubSetInMultipleRanges():
    ranges = [
        NugetVersionRange("[1.0.0, 5.0.0)"),
        NugetVersionRange("[2.0.0, 6.0.0]"),
        NugetVersionRange("[4.0.0, 5.0.0]"),
    ]
    combined = NugetVersionRange.CommonSubSet(ranges)
    assert combined.to_string() == "[4.0.0, 5.0.0)"
