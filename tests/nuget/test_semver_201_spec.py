# Copyright (c) .NET Foundation. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
# URL: https://github.com/NuGet/NuGet.Client
# Ported to Python from the C# NuGet test suite and significantly modified

import pytest

from univers.utils import cmp
from univers.versions import SemverVersion as SemanticVersion


# A normal version number MUST take the form X.Y.Z
@pytest.mark.parametrize(
    ["version", "expected"],
    [
        ("1", False),
        ("1.2", False),
        ("1.2.3", True),
        ("10.2.3", True),
        ("13234.223.32222", True),
        ("1.2.3.4", False),
        ("1.2. 3", False),
        ("1. 2.3", False),
        ("X.2.3", False),
        ("1.2.Z", False),
        ("X.Y.Z", False),
    ],
)
def test_SemVerVersionMustBe3Parts(version, expected):
    semVer = None
    valid = SemanticVersion(version, semVer)
    assert valid == expected

# X, Y, and Z are non-negative integers
@pytest.mark.parametrize(
    ["versionString"],
    [
        ("-1.2.3",),
        ("1.-2.3",),
        ("1.2.-3",),
    ],
)
def test_SemVerVersionNegativeNumbers(versionString):
    semVer = None
    valid = SemanticVersion(versionString, semVer)
    assert not valid

# X, Y, and Z MUST NOT contain leading zeroes
@pytest.mark.parametrize(
    "versionString",
    [
        ("01.2.3",),
        ("1.02.3",),
        ("1.2.03",),
        ("00.2.3",),
        ("1.2.0030",),
    ],
)
def test_SemVerVersionLeadingZeros(versionString):
    semVer = None
    valid = SemanticVersion(versionString, semVer)
    assert not valid

# Major version zero (0.y.z) is for initial development
@pytest.mark.parametrize(
    "versionString",
    [
        ("0.1.2",),
        ("1.0.0",),
        ("0.0.0",),
    ],
)
def test_SemVerVersionValidZeros(versionString):
    semVer = None
    valid = SemanticVersion(versionString, semVer)
    assert valid

# valid release labels
@pytest.mark.parametrize(
    "versionString",
    [
        ("0.1.2-Alpha",),
        ("0.1.2-Alpha.2.34.5.453.345.345.345.345.A.B.bbbbbbb.Csdfdfdf",),
        ("0.1.2-Alpha-2-5Bdd",),
        ("0.1.2--",),
        ("0.1.2--B-C-",),
        ("0.1.2--B2.-.C.-A0-",),
        ("0.1.2+NoReleaseLabel",),
    ],
)
def test_SemVerVersionValidReleaseLabels(versionString):
    semVer = None
    valid = SemanticVersion(versionString, semVer)
    assert valid

# Release label identifiers MUST NOT be empty
@pytest.mark.parametrize(
    "versionString",
    [
        ("0.1.2-Alpha..2"),
        ("0.1.2-Alpha."),
        ("0.1.2-.AA"),
        ("0.1.2-"),
    ],
)
def test_SemVerVersionInvalidReleaseId(versionString):
    semVer = None
    valid = SemanticVersion(versionString, semVer)
    assert not valid

# Identifiers MUST comprise only ASCII alphanumerics and hyphen [0-9A-Za-z-]
@pytest.mark.parametrize(
    "versionString",
    [
        ("0.1.2-alp=ha"),
        ("0.1.2-alp┐jj"),
        ("0.1.2-a&444"),
        ("0.1.2-a.&.444"),
    ],
)
def test_SemVerVersionInvalidReleaseLabelChars(versionString):
    semVer = None
    valid = SemanticVersion(versionString, semVer)
    assert not valid

# Numeric identifiers MUST NOT include leading zeroes
@pytest.mark.parametrize(
    "versionString",
    [
        ("0.1.2-02"),
        ("0.1.2-2.02"),
        ("0.1.2-2.A.02"),
        ("0.1.2-02.A"),
    ],
)
def test_SemVerVersionReleaseLabelZeros(versionString):
    semVer = None
    valid = SemanticVersion(versionString, semVer)
    assert not valid

# Numeric identifiers MUST NOT include leading zeroes
@pytest.mark.parametrize(
    "versionString",
    [
        ("0.1.2-02A"),
        ("0.1.2-2.02B"),
        ("0.1.2-2.A.02-"),
        ("0.1.2-A02.A"),
    ],
)
def test_SemVerVersionReleaseLabelValidZeros(versionString):
    semVer = None
    valid = SemanticVersion(versionString, semVer)
    assert valid

# Identifiers MUST comprise only ASCII alphanumerics and hyphen [0-9A-Za-z-]
@pytest.mark.parametrize(
    "versionString",
    [
        ("0.1.2+02A"),
        ("0.1.2+A"),
        ("0.1.2+20349244.233.344.0"),
        ("0.1.2+203-49244.23-3.34-4.0-.-.-"),
        ("0.1.2+AAaaaaAAAaaaa"),
        ("0.1.2+-"),
        ("0.1.2+----.-.-.-"),
        ("0.1.2----+----"),
    ],
)
def test_SemVerVersionMetadataValidChars(versionString):
    semVer = None
    valid = SemanticVersion(versionString, semVer)
    assert valid

# Identifiers MUST comprise only ASCII alphanumerics and hyphen [0-9A-Za-z-]
@pytest.mark.parametrize(
    "versionString",
    [
        ("0.1.2+ÄÄ"),
        ("0.1.2+22.2ÄÄ"),
        ("0.1.2+2+A"),
    ],
)
def test_SemVerVersionMetadataInvalidChars(versionString):
    semVer = None
    valid = SemanticVersion(versionString, semVer)
    assert not valid

# Identifiers MUST NOT be empty
@pytest.mark.parametrize(
    "versionString",
    [
        ("0.1.2+02A."),
        ("0.1.2+02..A"),
        ("0.1.2+"),
    ],
)
def test_SemVerVersionMetadataNonEmptyParts(versionString):
    semVer = None
    valid = SemanticVersion(versionString, semVer)
    assert not valid

# Leading zeros are fine for metadata
@pytest.mark.parametrize(
    "versionString",
    [
        ("0.1.2+02.02-02"),
        ("0.1.2+02"),
        ("0.1.2+02A"),
        ("0.1.2+000000"),
    ],
)
def test_SemVerVersionMetadataLeadingZeros(versionString):
    semVer = None
    valid = SemanticVersion(versionString, semVer)
    assert valid

@pytest.mark.parametrize(
    "versionString",
    [
        ("0.1.2+AA-02A"),
        ("0.1.2+A.-A-02A"),
    ],
)
def test_SemVerVersionMetadataOrder(versionString):
    semver = SemanticVersion(versionString)
    assert not semver.IsPrerelease

# Precedence is determined by the first difference when comparing each
# of these identifiers from left to right as follows: Major, minor, and
# patch versions are always compared numerically
@pytest.mark.parametrize(
    ["lower", "higher"],
    [
        ("1.2.3", "1.2.4"),
        ("1.2.3", "2.0.0"),
        ("9.9.9", "10.1.1"),
    ],
)
def test_SemVerSortVersion(lower, higher):
    lowerSemVer = SemanticVersion(lower)
    higherSemVer = SemanticVersion(higher)
    assert cmp(lowerSemVer, higherSemVer) < 0

# a pre-release version has lower precedence than a normal version
@pytest.mark.parametrize(
    ["lower", "higher"],
    [
        ("1.2.3-alpha", "1.2.3"),
    ],
)
def test_SemVerSortRelease(lower, higher):
    lowerSemVer = SemanticVersion(lower)
    higherSemVer = SemanticVersion(higher)
    assert cmp(lowerSemVer, higherSemVer) < 0

# identifiers consisting of only digits are compared numerically
@pytest.mark.parametrize(
    ["lower", "higher"],
    [
        ("1.2.3-2", "1.2.3-3"),
        ("1.2.3-1.9", "1.2.3-1.50"),
    ],
)
def test_SemVerSortReleaseNumeric(lower, higher):
    lowerSemVer = SemanticVersion(lower)
    higherSemVer = SemanticVersion(higher)
    assert cmp(lowerSemVer, higherSemVer) < 0

# identifiers with letters or hyphens are compared lexically in ASCII sort order
@pytest.mark.parametrize(
    ["lower", "higher"],
    [
        ("1.2.3-2A", "1.2.3-3A"),
        ("1.2.3-1.50A", "1.2.3-1.9A"),
    ],
)
def test_SemVerSortReleaseAlpha(lower, higher):
    lowerSemVer = SemanticVersion(lower)
    higherSemVer = SemanticVersion(higher)
    assert cmp(lowerSemVer, higherSemVer) < 0

# Numeric identifiers always have lower precedence than non-numeric identifiers
@pytest.mark.parametrize(
    ["lower", "higher"],
    [
        ("1.2.3-999999", "1.2.3-Z"),
        ("1.2.3-A.999999", "1.2.3-A.56-2"),
    ],
)
def test_SemVerSortNumericAlpha(lower, higher):
    lowerSemVer = SemanticVersion(lower)
    higherSemVer = SemanticVersion(higher)
    assert cmp(lowerSemVer, higherSemVer) < 0

# A larger set of pre-release fields has a higher precedence than a smaller set
@pytest.mark.parametrize(
    ["lower", "higher"],
    [
        ("1.2.3-a", "1.2.3-a.2"),
        ("1.2.3-a.2.3.4", "1.2.3-a.2.3.4.5"),
    ],
)
def test_SemVerSortReleaseLabelCount(lower, higher):
    lowerSemVer = SemanticVersion(lower)
    higherSemVer = SemanticVersion(higher)
    assert cmp(lowerSemVer, higherSemVer) < 0

# ignore release label casing
@pytest.mark.parametrize(
    ["a", "b"],
    [
        ("1.2.3-a", "1.2.3-A"),
        ("1.2.3-A-b2-C", "1.2.3-a-B2-c"),
    ],
)
def test_SemVerSortIgnoreReleaseCasing(a, b):
    semVerA = SemanticVersion(a)
    semVerB = SemanticVersion(b)
    assert semVerA == semVerB
