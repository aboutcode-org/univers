# Copyright (c) .NET Foundation. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
# URL: https://github.com/NuGet/NuGet.Client
# Ported to Python from the C# NuGet test suite and significantly modified

import pytest

from univers.version_range import NugetVersionRange

"""
Univers range semantics are different and therefore we only test parsing here.
"""


# FIXME: these may be valid Nuget ranges
@pytest.mark.parametrize(
    "vrange",
    [
        "(, )",
        "(0.0.0, 0.0.0)",
        "(2.0.0, 2.0.0)",
        "(3.0.0, 3.0.0)",
    ],
)
def test_InvalidRange(vrange):
    with pytest.raises(Exception):
        NugetVersionRange.from_native(vrange)


@pytest.mark.parametrize(
    "superSet, subSet",
    [
        ("[1.0.0, )", "[1.0.0, )"),
        ("[1.0.0, )", "[1.0.1, )"),
        ("[1.0.0-alpha, )", "[1.0.0, )"),
        ("[1.0.0]", "[1.0.0]"),
        ("[1.0.0, 2.0.0]", "(1.1.0, 1.5.0)"),
        ("(0.0.0, )", "[1.0.0, )"),
        ("(1.0.0-alpha, 2.0.0]", "[2.0.0]"),
        ("(1.0.0-alpha, 2.0.0]", "(2.0.0, 2.0.1)"),
    ],
)
def test_VersionRangeSet_SubSetTest(superSet, subSet):
    superSetRange = NugetVersionRange.from_native(superSet)
    subSetRange = NugetVersionRange.from_native(subSet)


#     assert subSetRange.IsSubSetOrEqualTo(superSetRange)


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
        ("(1.0.0-alpha, 2.0.0]", "(3.0.0, 3.0.1)"),
        # ("(3.0.0, 3.0.0)", "[3.0.0]"),
    ],
)
def test_VersionRangeSet_SubSetTestNeg(superSet, subSet):
    superSetRange = NugetVersionRange.from_native(superSet)
    subSetRange = NugetVersionRange.from_native(subSet)


#     assert not subSetRange.IsSubSetOrEqualTo(superSetRange)


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
        #         ("(, )", "[1.0.0, 1.5.0)", "[, ]"),
        #         ("(, )", "[1.0.0, 1.5.0)", "(, )"),
        ("(, )", "[1.0.0-alpha, )", "(, 2.0.0-beta]"),
        (
            "[0.0.0-alpha-1, 9000.0.0.1]",
            "[0.0.0-alpha-1, 0.0.0-alpha-2]",
            "[10.0.0.0, 9000.0.0.1]",
        ),
    ],
)
def test_VersionRangeSet_CombineTwoRanges(expected, rangeA, rangeB):
    a = NugetVersionRange.from_native(rangeA)
    b = NugetVersionRange.from_native(rangeB)


#     ranges = [a, b]
#     combined = NugetVersionRange.Combine(ranges)
#
#     rangesRev = [b, a]
#     combinedRev = NugetVersionRange.Combine(rangesRev)
#
#     assert combined.to_string() == expected
#
#     # Verify the order has no effect
#     assert combinedRev.to_string() == expected


def test_VersionRangeSet_CombineSingleRangeList():
    a = NugetVersionRange.from_native("[1.0.0, )")


#     ranges = [a]
#     combined = NugetVersionRange.Combine(ranges)
#     assert combined.to_string() == a.to_string()


def test_VersionRangeSet_RemoveEmptyRanges():
    ranges = [
        # these are empty ranges
        #         NugetVersionRange.from_native("(5.0.0, 5.0.0)"),
        #         NugetVersionRange.from_native("(3.0.0-alpha, 3.0.0-alpha)"),
        NugetVersionRange.from_native("[1.0.0, 2.0.0]"),
    ]


#
#     combined = NugetVersionRange.Combine(ranges)
#     assert combined.to_string() == "[1.0.0, 2.0.0]"


def test_VersionRangeSet_CombineMultipleRanges():
    ranges = [
        NugetVersionRange.from_native("[1.0.0]"),
        NugetVersionRange.from_native("[2.0.0]"),
        NugetVersionRange.from_native("[3.0.0]"),
        NugetVersionRange.from_native("[4.0.0-beta-1]"),
        NugetVersionRange.from_native("[5.0.1-rc4]"),
    ]


#     combined = NugetVersionRange.Combine(ranges)
#     ranges.Reverse()
#     assert combined.to_string() == "[1.0.0, 5.0.1-rc4]"


def test_VersionRangeSet_CommonSubSet_SingleRangeList():
    a = NugetVersionRange.from_native("[1.0.0, )")


#     ranges = [a]
#     combined = NugetVersionRange.CommonSubSet(ranges)
#     assert combined.to_string() == a.to_string()


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
        # ("[1.0.0, 1.5.0)", "[1.0.0, 1.5.0)", "[, ]"),
        ("(0.0.0, 0.0.0)", "[1.0.0]", "[2.0.0]"),
    ],
)
def test_VersionRangeSet_CommonSubSet(expected, rangeA, rangeB):
    a = NugetVersionRange.from_native(rangeA)
    b = NugetVersionRange.from_native(rangeB)


#     ranges = [a, b]
#     combined = NugetVersionRange.CommonSubSet(ranges)
#     rangesRev = [b, a]
#     combinedRev = NugetVersionRange.CommonSubSet(rangesRev)
#     assert combined.to_string() == expected
#     # Verify the order has no effect
#     assert combinedRev.to_string() == expected


def test_VersionRangeSet_CommonSubSetInMultipleRanges():
    ranges = [
        NugetVersionRange.from_native("[1.0.0, 5.0.0)"),
        NugetVersionRange.from_native("[2.0.0, 6.0.0]"),
        NugetVersionRange.from_native("[4.0.0, 5.0.0]"),
    ]


#     combined = NugetVersionRange.CommonSubSet(ranges)
#     assert combined.to_string() == "[4.0.0, 5.0.0)"
