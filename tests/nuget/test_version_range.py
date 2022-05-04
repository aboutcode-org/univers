# Copyright (c) .NET Foundation. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
# URL: https://github.com/NuGet/NuGet.Client
# Ported to Python from the C# NuGet test suite and significantly modified

import pytest

from univers import nuget
from univers.version_range import NugetVersionRange

"""
These tests need to be enable and fixed to pass.
"""

pytestmark = pytest.mark.skipif(True, reason="NuGet ranges tests need to be ported to Univers.")


# FIXME: these are correctly processed by NuGet
@pytest.mark.parametrize(
    "versionString, expected",
    [
        ("[1.0.0, ", "vers:nuget/>=1.0.0"),
        ("(1.0.0, ", "vers:nuget/>1.0.0"),
        ("1.0.0", "vers:nuget/>=1.0.0"),
        ("(1.0.0, 2.0.0", "vers:nuget/>1.0.0|<2.0.0"),
        ("(, 2.0.0", "vers:nuget/<2.0.0"),
        ("[, 2.0.0", "vers:nuget/<2.0.0"),
        ("[1.0.0, 2.0.0", "vers:nuget/>=1.0.0|<2.0.0"),
        ("1.0.0-beta*", "vers:nuget/>=1.0.0-beta"),
        ("[1.0.0-beta*, 2.0.0", "vers:nuget/>=1.0.0-beta|<2.0.0"),
    ],
)
def test_VersionRange_are_invalid(versionString, expected):
    with pytest.raises(Exception):
        vrange = NugetVersionRange.from_native(versionString)
        assert str(vrange) == expected


@pytest.mark.parametrize(
    "versionString, expected",
    [
        ("[1.0.0]", "vers:nuget/1.0.0"),
        ("[1.0.0, ]", "vers:nuget/>=1.0.0"),
        ("(1.0.0, ]", "vers:nuget/>1.0.0"),
        ("[1.0.0, 2.0.0]", "vers:nuget/>=1.0.0|<=2.0.0"),
        ("(1.0.0, 2.0.0]", "vers:nuget/>1.0.0|<=2.0.0"),
        ("(, 2.0.0]", "vers:nuget/<=2.0.0"),
        ("[, 2.0.0]", "vers:nuget/<=2.0.0"),
        ("[1.0.0-beta.1, 2.0.0-alpha.2]", "vers:nuget/>=1.0.0-beta.1|<=2.0.0-alpha.2"),
        # note that Nuget was ignoring builds for ranges
        ("[1.0.0+beta.1, 2.0.0+alpha.2]", "vers:nuget/>=1.0.0+beta.1|<=2.0.0+alpha.2"),
        ("[1.0, 2.0]", "vers:nuget/>=1.0|<=2.0"),
    ],
)
def test_VersionRange_PrettyPrintTests(versionString, expected):
    vrange = NugetVersionRange.from_native(versionString)
    assert str(vrange) == expected


@pytest.mark.parametrize(
    "rangeString, versionString, expected",
    [
        ("1.0.0", "1.0.1-beta", False),
        ("1.0.0", "1.0.1", True),
        ("1.0.0-*", "1.0.0-beta", True),
        ("1.0.0-beta.*", "1.0.0-beta.1", True),
        ("1.0.0-beta-*", "1.0.0-beta-01", True),
        ("1.0.0-beta-*", "2.0.0-beta", True),
        ("1.0.*", "1.0.0-beta", False),
        ("1.*", "1.0.0-beta", False),
        ("*", "1.0.0-beta", False),
        ("[1.0.0, 2.0.0]", "1.5.0-beta", False),
        ("[1.0.0, 2.0.0-beta]", "1.5.0-beta", True),
        ("[1.0.0-beta, 2.0.0]", "1.5.0-beta", True),
        ("[1.0.0-beta, 2.0.0]", "3.5.0-beta", False),
        ("[1.0.0-beta, 2.0.0]", "0.5.0-beta", False),
        ("[1.0.0-beta, 2.0.0)", "2.0.0", False),
        ("[1.0.0-beta, 2.0.0)", "2.0.0-beta", True),
        ("[1.0.*, 2.0.0-beta]", "2.0.0-beta", True),
    ],
)
def test_VersionRange_IsBetter_Prerelease(rangeString, versionString, expected):
    vrange = NugetVersionRange.from_native(rangeString)
    considering = nuget.Version.from_string(versionString)
    result = vrange.IsBetter(current=None, considering=considering)
    assert result == expected


def test_VersionRange_MetadataIsIgnored_Satisfy():
    noMetadata = NugetVersionRange.from_native("[1.0.0, 2.0.0]")
    lowerMetadata = NugetVersionRange.from_native("[1.0.0+A, 2.0.0]")
    upperMetadata = NugetVersionRange.from_native("[1.0.0, 2.0.0+A]")
    bothMetadata = NugetVersionRange.from_native("[1.0.0+A, 2.0.0+A]")

    versionNoMetadata = nuget.Version.from_string("1.0.0")
    versionMetadata = nuget.Version.from_string("1.0.0+B")

    assert noMetadata.Satisfies(versionNoMetadata)
    assert noMetadata.Satisfies(versionMetadata)
    assert lowerMetadata.Satisfies(versionNoMetadata)
    assert lowerMetadata.Satisfies(versionMetadata)
    assert upperMetadata.Satisfies(versionNoMetadata)
    assert upperMetadata.Satisfies(versionMetadata)
    assert bothMetadata.Satisfies(versionNoMetadata)
    assert bothMetadata.Satisfies(versionMetadata)


def test_VersionRange_MetadataIsIgnored_Equality():
    noMetadata = NugetVersionRange.from_native("[1.0.0, 2.0.0]")
    lowerMetadata = NugetVersionRange.from_native("[1.0.0+A, 2.0.0]")
    upperMetadata = NugetVersionRange.from_native("[1.0.0, 2.0.0+A]")
    bothMetadata = NugetVersionRange.from_native("[1.0.0+A, 2.0.0+A]")

    assert noMetadata.Equals(lowerMetadata)
    assert lowerMetadata.Equals(upperMetadata)
    assert upperMetadata.Equals(bothMetadata)
    assert bothMetadata.Equals(noMetadata)


def test_VersionRange_MetadataIsIgnored_FormatRemovesMetadata():
    bothMetadata = NugetVersionRange.from_native("[1.0.0+A, 2.0.0+A]")

    assert bothMetadata.to_string() == "[1.0.0, 2.0.0]"
    assert bothMetadata.to_string() == "[1.0.0, 2.0.0]"
    assert bothMetadata.ToLegacyString() == "[1.0.0, 2.0.0]"


def test_VersionRange_FloatAllStable_ReturnsCorrectPrints():
    bothMetadata = NugetVersionRange.from_native("*")

    assert bothMetadata.to_string() == "[*, )"
    assert bothMetadata.to_string() == "[*, )"
    assert bothMetadata.ToLegacyString() == "[0.0.0, )"
    # Note that this matches version strings generated by other version ranges such as 0.*, 0.0.*


def test_VersionRange_AllSpecialCases_NormalizeSame():
    assert NugetVersionRange.All.to_string() == "(, )"
    # pragma warning disable CS0618 # Type or member is obsolete
    assert NugetVersionRange.AllFloating.to_string() == "(, )"
    assert NugetVersionRange.AllStable.to_string() == "(, )"
    assert NugetVersionRange.AllStableFloating.to_string() == "(, )"


def test_VersionRange_MetadataIsIgnored_FormatRemovesMetadata_Short():
    bothMetadata = NugetVersionRange.from_native("[1.0.0+A, )")
    assert bothMetadata.ToLegacyShortString() == "1.0.0"


def test_VersionRange_MetadataIsIgnored_FormatRemovesMetadata_PrettyPrint():
    bothMetadata = NugetVersionRange.from_native("[1.0.0+A, )")
    assert bothMetadata.PrettyPrint() == "(>= 1.0.0)"


@pytest.mark.parametrize(
    "snapshot, expected",
    [
        ("1.0.0", "1.0.0"),
        ("1.0.0-beta", "1.0.0-beta"),
        ("1.0.0-*", "1.0.0"),
        ("2.0.0-*", "2.0.0"),
        ("1.0.0-rc1-*", "1.0.0-rc1"),
        ("1.0.0-5.1.*", "1.0.0-5.1"),
        ("1.0.0-5.1.0-*", "1.0.0-5.1.0"),
        ("1.0.*", "1.0.0"),
        ("1.*", "1.0.0"),
        ("*", "0.0.0"),
    ],
)
def test_VersionRange_VerifyNonSnapshotVersion(snapshot, expected):
    vrange = NugetVersionRange.from_native(snapshot)
    updated = vrange.ToNonSnapshotRange()
    assert updated.ToLegacyShortString() == expected


@pytest.mark.parametrize(
    "s",
    [
        ("[1.0.0]"),
        ("[1.0.0, 2.0.0]"),
        ("1.0.0"),
        ("1.0.0-beta"),
        ("(1.0.0-beta, 2.0.0-alpha)"),
        ("(1.0.0-beta, 2.0.0)"),
        ("(1.0.0, 2.0.0-alpha)"),
        ("1.0.0-beta-*"),
        ("[1.0.0-beta-*, ]"),
    ],
)
def test_VersionRange_IncludePrerelease(s):
    vrange = NugetVersionRange.from_native(s)
    assert vrange.IsFloating == vrange.IsFloating
    assert vrange.Float == vrange.Float
    assert vrange.to_string() == vrange.to_string()


def test_ParseVersionRangeSingleDigit():
    versionInfo = NugetVersionRange.from_native("[1,3)")
    assert versionInfo.MinVersion.to_string() == "1.0.0"
    assert versionInfo.IsMinInclusive
    assert versionInfo.MaxVersion.to_string() == "3.0.0"
    assert not versionInfo.IsMaxInclusive


def test_VersionRange_Exact():
    versionInfo = NugetVersionRange.from_native(
        nuget.Version.from_string(4, 3, 0), True, nuget.Version.from_string(4, 3, 0), True
    )
    assert versionInfo.Satisfies(nuget.Version.from_string("4.3.0"))


@pytest.mark.parametrize(
    "shortVersionSpec, longVersionSpec",
    [
        ("0", "0.0"),
        ("1", "1.0.0"),
        ("02", "2.0.0.0"),
        ("123.456", "123.456.0.0"),
        ("[2021,)", "[2021.0.0.0,)"),
        ("[,2021)", "[,2021.0.0.0)"),
    ],
)
def test_VersionRange_MissingVersionComponents_DefaultToZero(shortVersionSpec, longVersionSpec):
    versionRange1 = NugetVersionRange.from_native(shortVersionSpec)
    versionRange2 = NugetVersionRange.from_native(longVersionSpec)
    assert versionRange1 == versionRange2


@pytest.mark.parametrize(
    "spec, version",
    [
        ("1.0.0", "0.0.0"),
        ("[1.0.0, 2.0.0]", "2.0.1"),
        ("[1.0.0, 2.0.0]", "0.0.0"),
        ("[1.0.0, 2.0.0]", "3.0.0"),
        ("[1.0.0-beta+meta, 2.0.0-beta+meta]", "1.0.0-alpha"),
        ("[1.0.0-beta+meta, 2.0.0-beta+meta]", "1.0.0-alpha+meta"),
        ("[1.0.0-beta+meta, 2.0.0-beta+meta]", "2.0.0-rc"),
        ("[1.0.0-beta+meta, 2.0.0-beta+meta]", "2.0.0+meta"),
        ("(1.0.0-beta+meta, 2.0.0-beta+meta)", "2.0.0-beta+meta"),
        ("(, 2.0.0-beta+meta)", "2.0.0-beta+meta"),
    ],
)
def test_ParseVersionRangeDoesNotSatisfy(spec, version):
    versionInfo = NugetVersionRange.from_native(spec)
    middleVersion = nuget.Version.from_string(version)

    assert not versionInfo.Satisfies(middleVersion)
    assert not versionInfo.Satisfies(middleVersion, VersionComparison.Default)
    assert not versionInfo.Satisfies(middleVersion, VersionComparer.Default)
    assert not versionInfo.Satisfies(middleVersion, VersionComparison.VersionRelease)
    assert not versionInfo.Satisfies(middleVersion, VersionComparer.VersionRelease)
    assert not versionInfo.Satisfies(middleVersion, VersionComparison.VersionReleaseMetadata)
    assert not versionInfo.Satisfies(middleVersion, VersionComparer.VersionReleaseMetadata)


@pytest.mark.parametrize(
    "spec, version",
    [
        ("1.0.0", "2.0.0"),
        ("[1.0.0, 2.0.0]", "2.0.0"),
        ("(2.0.0,)", "2.1.0"),
        ("[2.0.0]", "2.0.0"),
        ("(,2.0.0]", "2.0.0"),
        ("(,2.0.0]", "1.0.0"),
        ("[2.0.0, )", "2.0.0"),
        ("1.0.0", "1.0.0"),
        ("[1.0.0]", "1.0.0"),
        ("[1.0.0, 1.0.0]", "1.0.0"),
        ("[1.0.0, 2.0.0]", "1.0.0"),
        ("[1.0.0-beta+meta, 2.0.0-beta+meta]", "1.0.0"),
        ("[1.0.0-beta+meta, 2.0.0-beta+meta]", "1.0.0-beta+meta"),
        ("[1.0.0-beta+meta, 2.0.0-beta+meta]", "2.0.0-beta"),
        ("[1.0.0-beta+meta, 2.0.0-beta+meta]", "1.0.0+meta"),
        ("(1.0.0-beta+meta, 2.0.0-beta+meta)", "1.0.0"),
        ("(1.0.0-beta+meta, 2.0.0-beta+meta)", "2.0.0-alpha+meta"),
        ("(1.0.0-beta+meta, 2.0.0-beta+meta)", "2.0.0-alpha"),
        ("(, 2.0.0-beta+meta)", "2.0.0-alpha"),
    ],
)
def test_ParseVersionRangeSatisfies(spec, version):
    versionInfo = NugetVersionRange.from_native(spec)
    middleVersion = nuget.Version.from_string(version)

    assert versionInfo.Satisfies(middleVersion)
    assert versionInfo.Satisfies(middleVersion, VersionComparison.Default)
    assert versionInfo.Satisfies(middleVersion, VersionComparer.VersionRelease)


@pytest.mark.parametrize(
    "minString, maxString, minInc, maxInc",
    [
        ("1.0.0", "2.0.0", True, True),
        ("1.0.0", "1.0.1", False, False),
        ("1.0.0-beta+0", "2.0.0", False, True),
        ("1.0.0-beta+0", "2.0.0+99", False, False),
        ("1.0.0-beta+0", "2.0.0+99", True, True),
        ("1.0.0", "2.0.0+99", True, True),
    ],
)
def test_ParseVersionRangeParts(minString, maxString, minInc, maxInc):
    minver = nuget.Version.from_string(minString)
    maxver = nuget.Version.from_string(maxString)

    versionInfo = NugetVersionRange.from_native(minver, minInc, maxver, maxInc)

    assert VersionComparer.Default == minver, versionInfo.MinVersion
    assert VersionComparer.Default == maxver, versionInfo.MaxVersion
    assert versionInfo.IsMinInclusive == minInc
    assert versionInfo.IsMaxInclusive == maxInc


@pytest.mark.parametrize(
    "minString, maxString, minInc, maxInc",
    [
        ("1.0.0", "2.0.0", True, True),
        ("1.0.0", "1.0.1", False, False),
        ("1.0.0-beta+0", "2.0.0", False, True),
        ("1.0.0-beta+0", "2.0.0+99", False, False),
        ("1.0.0-beta+0", "2.0.0+99", True, True),
        ("1.0.0", "2.0.0+99", True, True),
    ],
)
def test_ParseVersionRangeto_stringReParse(minString, maxString, minInc, maxInc):

    minver = nuget.Version.from_string(minString)
    maxver = nuget.Version.from_string(maxString)

    original = NugetVersionRange.from_native(minver, minInc, maxver, maxInc)
    versionInfo = NugetVersionRange.from_native(original.to_string())

    assert VersionComparer.Default == minver, versionInfo.MinVersion
    assert VersionComparer.Default == maxver, versionInfo.MaxVersion
    assert versionInfo.IsMinInclusive == minInc
    assert versionInfo.IsMaxInclusive == maxInc


@pytest.mark.parametrize(
    "version, expected",
    [
        ("1.2.0", "1.2.0"),
        ("1.2.3", "1.2.3"),
        ("1.2.3-beta", "1.2.3-beta"),
        ("1.2.3-beta+900", "1.2.3-beta"),
        ("1.2.3-beta.2.4.55.X+900", "1.2.3-beta.2.4.55.X"),
        ("1.2.3-0+900", "1.2.3-0"),
        ("[1.2.0]", "[1.2.0]"),
        ("[1.2.3]", "[1.2.3]"),
        ("[1.2.3-beta]", "[1.2.3-beta]"),
        ("[1.2.3-beta+900]", "[1.2.3-beta]"),
        ("[1.2.3-beta.2.4.55.X+900]", "[1.2.3-beta.2.4.55.X]"),
        ("[1.2.3-0+90]", "[1.2.3-0]"),
        ("(, 1.2.0]", "(, 1.2.0]"),
        ("(, 1.2.3]", "(, 1.2.3]"),
        ("(, 1.2.3-beta]", "(, 1.2.3-beta]"),
        ("(, 1.2.3-beta+900]", "(, 1.2.3-beta]"),
        ("(, 1.2.3-beta.2.4.55.X+900]", "(, 1.2.3-beta.2.4.55.X]"),
        ("(, 1.2.3-0+900]", "(, 1.2.3-0]"),
    ],
)
def test_ParseVersionRangeto_stringShortHand(version, expected):
    versionInfo = NugetVersionRange.from_native(version)
    assert VersionRangeFormatter() == expected, versionInfo.to_string("S")


@pytest.mark.parametrize(
    "version, expected",
    [
        ("1.2.0", "[1.2.0, )"),
        ("1.2.3-beta.2.4.55.X+900", "[1.2.3-beta.2.4.55.X, )"),
    ],
)
def test_ParseVersionRangeto_string(version, expected):
    versionInfo = NugetVersionRange.from_native(version)
    assert versionInfo.to_string() == expected


def test_ParseVersionRangeSimpleVersionNoBrackets():
    versionInfo = NugetVersionRange.from_native("1.2")
    assert versionInfo.MinVersion.to_string() == "1.2"
    assert versionInfo.IsMinInclusive
    assert versionInfo.MaxVersion == None
    assert not versionInfo.IsMaxInclusive


def test_ParseVersionRangeSimpleVersionNoBracketsExtraSpaces():
    versionInfo = NugetVersionRange.from_native("  1  .   2  ")
    assert versionInfo.MinVersion.to_string() == "1.2"
    assert versionInfo.IsMinInclusive
    assert versionInfo.MaxVersion == None
    assert not versionInfo.IsMaxInclusive


def test_ParseVersionRangeMaxOnlyInclusive():
    versionInfo = NugetVersionRange.from_native("(,1.2]")
    assert versionInfo.MinVersion == None
    assert not versionInfo.IsMinInclusive
    assert versionInfo.MaxVersion.to_string() == "1.2"
    assert versionInfo.IsMaxInclusive


def test_ParseVersionRangeMaxOnlyExclusive():
    versionInfo = NugetVersionRange.from_native("(,1.2)")
    assert versionInfo.MinVersion == None
    assert not versionInfo.IsMinInclusive
    assert versionInfo.MaxVersion.to_string() == "1.2"
    assert not versionInfo.IsMaxInclusive


def test_ParseVersionRangeExactVersion():
    versionInfo = NugetVersionRange.from_native("[1.2]")
    assert versionInfo.MinVersion.to_string() == "1.2"
    assert versionInfo.IsMinInclusive
    assert versionInfo.MaxVersion.to_string() == "1.2"
    assert versionInfo.IsMaxInclusive


def test_ParseVersionRangeMinOnlyExclusive():
    versionInfo = NugetVersionRange.from_native("(1.2,)")
    assert versionInfo.MinVersion.to_string() == "1.2"
    assert not versionInfo.IsMinInclusive
    assert versionInfo.MaxVersion == None
    assert not versionInfo.IsMaxInclusive


def test_ParseVersionRangeExclusiveExclusive():
    versionInfo = NugetVersionRange.from_native("(1.2,2.3)")
    assert versionInfo.MinVersion.to_string() == "1.2"
    assert not versionInfo.IsMinInclusive
    assert versionInfo.MaxVersion.to_string() == "2.3"
    assert not versionInfo.IsMaxInclusive


def test_ParseVersionRangeExclusiveInclusive():
    versionInfo = NugetVersionRange.from_native("(1.2,2.3]")
    assert versionInfo.MinVersion.to_string() == "1.2"
    assert not versionInfo.IsMinInclusive
    assert versionInfo.MaxVersion.to_string() == "2.3"
    assert versionInfo.IsMaxInclusive


def test_ParseVersionRangeInclusiveExclusive():
    versionInfo = NugetVersionRange.from_native("[1.2,2.3)")
    assert versionInfo.MinVersion.to_string() == "1.2"
    assert versionInfo.IsMinInclusive
    assert versionInfo.MaxVersion.to_string() == "2.3"
    assert not versionInfo.IsMaxInclusive


def test_ParseVersionRangeInclusiveInclusive():
    versionInfo = NugetVersionRange.from_native("[1.2,2.3]")
    assert versionInfo.MinVersion.to_string() == "1.2"
    assert versionInfo.IsMinInclusive
    assert versionInfo.MaxVersion.to_string() == "2.3"
    assert versionInfo.IsMaxInclusive


def test_ParseVersionRangeInclusiveInclusiveExtraSpaces():
    versionInfo = NugetVersionRange.from_native("   [  1 .2   , 2  .3   ]  ")
    assert versionInfo.MinVersion.to_string() == "1.2"
    assert versionInfo.IsMinInclusive
    assert versionInfo.MaxVersion.to_string() == "2.3"
    assert versionInfo.IsMaxInclusive


@pytest.mark.parametrize(
    "vrange",
    [
        ("*"),
        ("1.*"),
        ("1.0.0"),
        (" 1.0.0"),
        ("[1.0.0]"),
        ("[1.0.0] "),
        ("[1.0.0, 2.0.0)"),
    ],
)
def test_ParsedVersionRangeHasOriginalString(vrange):

    versionInfo = NugetVersionRange.from_native(vrange)

    assert versionInfo.OriginalString == vrange


def test_ParseVersionToNormalizedVersion():

    versionString = "(1.0,1.2]"

    assert NugetVersionRange.from_native(versionString).to_string() == "(1.0.0, 1.2.0]"


@pytest.mark.parametrize(
    "vrange",
    [
        ("1.2.0"),
        ("1.2.3"),
        ("1.2.3-beta"),
        ("1.2.3-beta+900"),
        ("1.2.3-beta.2.4.55.X+900"),
        ("1.2.3-0+900"),
        ("[1.2.0]"),
        ("[1.2.3]"),
        ("[1.2.3-beta]"),
        ("[1.2.3-beta+900]"),
        ("[1.2.3-beta.2.4.55.X+900]"),
        ("[1.2.3-0+900]"),
        ("(, 1.2.0)"),
        ("(, 1.2.3)"),
        ("(, 1.2.3-beta)"),
        ("(, 1.2.3-beta+900)"),
        ("(, 1.2.3-beta.2.4.55.X+900)"),
        ("(, 1.2.3-0+900)"),
    ],
)
def test_StringFormatNullProvider(vrange):

    versionRange = NugetVersionRange.from_native(vrange)
    actual = string.Format("0", versionRange)
    expected = versionRange.to_string()

    assert actual == expected


@pytest.mark.parametrize(
    "vrange",
    [
        ("1.2.0"),
        ("1.2.3"),
        ("1.2.3-beta"),
        ("1.2.3-beta+900"),
        ("1.2.3-beta.2.4.55.X+900"),
        ("1.2.3-0+900"),
        ("[1.2.0]"),
        ("[1.2.3]"),
        ("[1.2.3-beta]"),
        ("[1.2.3-beta+900]"),
        ("[1.2.3-beta.2.4.55.X+900]"),
        ("[1.2.3-0+90]"),
        ("(, 1.2.0]"),
        ("(, 1.2.3]"),
        ("(, 1.2.3-beta]"),
        ("(, 1.2.3-beta+900]"),
        ("(, 1.2.3-beta.2.4.55.X+900]"),
        ("(, 1.2.3-0+900]"),
    ],
)
def test_StringFormatNullProvider2(vrange):

    versionRange = NugetVersionRange.from_native(vrange)
    actual = string.Format(CultureInfo.InvariantCulture, "0", versionRange)
    expected = versionRange.to_string()

    assert actual == expected


@pytest.mark.parametrize(
    "versionString, minver, incMin, maxver, incMax",
    [
        ("(1.2.3.4, 3.2)", "1.2.3.4", False, "3.2", False),
        ("(1.2.3.4, 3.2]", "1.2.3.4", False, "3.2", True),
        ("[1.2, 3.2.5)", "1.2", True, "3.2.5", False),
        ("[2.3.7, 3.2.4.5]", "2.3.7", True, "3.2.4.5", True),
        ("(, 3.2.4.5]", None, False, "3.2.4.5", True),
        ("(1.6, ]", "1.6", False, None, True),
        ("[2.7]", "2.7", True, "2.7", True),
    ],
)
def test_ParseVersionParsesTokensVersionsCorrectly(versionString, minver, incMin, maxver, incMax):

    versionRange = NugetVersionRange.from_native(
        None if minver == None else nuget.Version.from_string(minver),
        incMin,
        None if maxver == None else nuget.Version.from_string(maxver),
        incMax,
    )

    actual = NugetVersionRange.from_native(versionString)

    assert actual.IsMinInclusive == versionRange.IsMinInclusive
    assert actual.IsMaxInclusive == versionRange.IsMaxInclusive
    assert actual.MinVersion == versionRange.MinVersion
    assert actual.MaxVersion == versionRange.MaxVersion


@pytest.mark.parametrize(
    "versionString1, versionString2, isEquals",
    [
        ("1.0.0", "1.0.*", False),
        ("[1.0.0,)", "[1.0.*, )", False),
        ("1.1.*", "1.0.*", False),
    ],
)
def test_VersionRange_Equals(versionString1, versionString2, isEquals):
    range1 = NugetVersionRange.from_native(versionString1)
    range2 = NugetVersionRange.from_native(versionString2)
    assert range1.Equals(range2) == isEquals


def test_VersionRange_to_stringRevPrefix():
    vrange = NugetVersionRange.from_native("1.1.1.*-*")
    assert vrange.to_string() == "[1.1.1.*-*, )"


def test_VersionRange_to_stringPatchPrefix():
    vrange = NugetVersionRange.from_native("1.1.*-*")
    assert vrange.to_string() == "[1.1.*-*, )"


def test_VersionRange_to_stringMinorPrefix():
    vrange = NugetVersionRange.from_native("1.*-*")
    assert vrange.to_string() == "[1.*-*, )"


def test_VersionRange_to_stringAbsoluteLatest():
    vrange = NugetVersionRange.from_native("*-*")
    assert vrange.to_string() == "[*-*, )"
    assert vrange.MinVersion.to_string() == "0.0.0-0"
    assert vrange.Float.MinVersion.to_string() == "0.0.0-0"
    assert vrange.Float.FloatBehavior == NuGetVersionFloatBehavior.AbsoluteLatest


def test_VersionRange_to_stringPrereleaseMajor():
    vrange = NugetVersionRange.from_native("*-rc.*")
    assert vrange.to_string() == "[*-rc.*, )"
    assert vrange.MinVersion.to_string() == "0.0.0-rc.0"
    assert vrange.Float.MinVersion.to_string() == "0.0.0-rc.0"
    assert vrange.Float.FloatBehavior == NuGetVersionFloatBehavior.PrereleaseMajor


def test_FindBestMatch_FloatingPrereleaseRevision_OutsideOfRange():
    vrange = NugetVersionRange.from_native("[1.0.0.*-*, 2.0.0)")

    versions = [
        nuget.Version.from_string("0.1.0"),
        nuget.Version.from_string("2.0.0"),
        nuget.Version.from_string("2.2.0"),
        nuget.Version.from_string("3.0.0"),
    ]

    assert not vrange.FindBestMatch(versions)


def test_FindBestMatch_FloatingPrereleaseRevision_NotMatchingPrefix_OutsideOfRange():
    vrange = NugetVersionRange.from_native("[1.0.0.*-beta*, 2.0.0)")

    versions = [
        nuget.Version.from_string("0.1.0"),
        nuget.Version.from_string("1.0.0-alpha.2"),
        nuget.Version.from_string("2.0.0"),
        nuget.Version.from_string("2.2.0"),
        nuget.Version.from_string("3.0.0"),
    ]

    assert not vrange.FindBestMatch(versions)


def test_FindBestMatch_FloatingPrereleaseRevision_OutsideOfRange_Lower():

    vrange = NugetVersionRange.from_native("[1.1.1.*-*, 2.0.0)")

    versions = [
        nuget.Version.from_string("0.1.0"),
        nuget.Version.from_string("0.8.0"),
        nuget.Version.from_string("0.9.0"),
        nuget.Version.from_string("1.0.0"),
    ]

    assert not vrange.FindBestMatch(versions)


def test_FindBestMatch_FloatingPrereleaseRevision_OutsideOfRange_Higher():

    vrange = NugetVersionRange.from_native("[1.1.1.*-*, 2.0.0)")

    versions = [
        nuget.Version.from_string("2.0.0"),
        nuget.Version.from_string("3.1.0"),
    ]

    assert not vrange.FindBestMatch(versions)


def test_FindBestMatch_FloatingPrereleaseRevision_OnlyMatching():

    vrange = NugetVersionRange.from_native("[1.0.1.*-alpha*, 2.0.0)")

    versions = [
        nuget.Version.from_string("0.1.0"),
        nuget.Version.from_string("1.0.1-alpha.2"),
        nuget.Version.from_string("2.0.0"),
        nuget.Version.from_string("2.2.0"),
        nuget.Version.from_string("3.0.0"),
    ]

    assert vrange.FindBestMatch(versions).to_string() == "1.0.1-alpha.2"


def test_FindBestMatch_FloatingPrereleaseRevision_BestMatching():

    vrange = NugetVersionRange.from_native("[1.0.1.*-alpha*, 2.0.0)")

    versions = [
        nuget.Version.from_string("0.1.0"),
        nuget.Version.from_string("1.0.0-alpha.2"),
        nuget.Version.from_string("1.0.1.9-alpha.1"),
        nuget.Version.from_string("1.1.0-alpha.1"),
        nuget.Version.from_string("2.0.0"),
        nuget.Version.from_string("2.2.0"),
        nuget.Version.from_string("3.0.0"),
    ]

    assert vrange.FindBestMatch(versions).to_string() == "1.0.1.9-alpha.1"


def test_FindBestMatch_FloatingPrereleaseRevision_BestMatchingStable():

    vrange = NugetVersionRange.from_native("[1.0.1.*-alpha*, 2.0.0)")

    versions = [
        nuget.Version.from_string("0.1.0"),
        nuget.Version.from_string("1.0.0-alpha.2"),
        nuget.Version.from_string("1.0.1.9"),
        nuget.Version.from_string("1.0.9-alpha.1"),
        nuget.Version.from_string("1.1.0-alpha.1"),
        nuget.Version.from_string("2.0.0"),
        nuget.Version.from_string("2.2.0"),
        nuget.Version.from_string("3.0.0"),
    ]

    assert vrange.FindBestMatch(versions).to_string() == "1.0.1.9"


def test_FindBestMatch_FloatingPrereleaseRevision_BestMatchingFloating():

    vrange = NugetVersionRange.from_native("[1.0.1.*-alpha*, 2.0.0)")

    versions = [
        nuget.Version.from_string("0.1.0"),
        nuget.Version.from_string("1.0.0-alpha.2"),
        nuget.Version.from_string("1.0.1.8"),
        nuget.Version.from_string("1.0.1.9-alpha.1"),
        nuget.Version.from_string("1.1.0-alpha.1"),
        nuget.Version.from_string("2.0.0"),
        nuget.Version.from_string("2.2.0"),
        nuget.Version.from_string("3.0.0"),
    ]

    assert vrange.FindBestMatch(versions).to_string() == "1.0.1.9-alpha.1"


def test_FindBestMatch_FloatingPrereleasePatch_OutsideOfRange():

    vrange = NugetVersionRange.from_native("[1.0.*-*, 2.0.0)")

    versions = [
        nuget.Version.from_string("0.1.0"),
        nuget.Version.from_string("2.0.0"),
        nuget.Version.from_string("2.2.0"),
        nuget.Version.from_string("3.0.0"),
    ]

    assert not vrange.FindBestMatch(versions)


def test_FindBestMatch_FloatingPrereleasePatch_NotMatchingPrefix_OutsideOfRange():

    vrange = NugetVersionRange.from_native("[1.0.*-beta*, 2.0.0)")

    versions = [
        nuget.Version.from_string("0.1.0"),
        nuget.Version.from_string("1.0.0-alpha.2"),
        nuget.Version.from_string("2.0.0"),
        nuget.Version.from_string("2.2.0"),
        nuget.Version.from_string("3.0.0"),
    ]

    assert not vrange.FindBestMatch(versions)


def test_FindBestMatch_FloatingPrereleasePatch_OutsideOfRange_Lower():

    vrange = NugetVersionRange.from_native("[1.1.*-*, 2.0.0)")

    versions = [
        nuget.Version.from_string("0.1.0"),
        nuget.Version.from_string("0.8.0"),
        nuget.Version.from_string("0.9.0"),
        nuget.Version.from_string("1.0.0"),
    ]

    assert not vrange.FindBestMatch(versions)


def test_FindBestMatch_FloatingPrereleasePatch_OutsideOfRange_Higher():

    vrange = NugetVersionRange.from_native("[1.1.*-*, 2.0.0)")

    versions = [
        nuget.Version.from_string("2.0.0"),
        nuget.Version.from_string("3.1.0"),
    ]
    assert not vrange.FindBestMatch(versions)


def test_FindBestMatch_FloatingPrereleasePatch_OnlyMatching():

    vrange = NugetVersionRange.from_native("[1.0.*-alpha*, 2.0.0)")

    versions = [
        nuget.Version.from_string("0.1.0"),
        nuget.Version.from_string("1.0.0-alpha.2"),
        nuget.Version.from_string("2.0.0"),
        nuget.Version.from_string("2.2.0"),
        nuget.Version.from_string("3.0.0"),
    ]

    assert vrange.FindBestMatch(versions).to_string() == "1.0.0-alpha.2"


def test_FindBestMatch_FloatingPrereleasePatch_BestMatching():

    vrange = NugetVersionRange.from_native("[1.0.*-alpha*, 2.0.0)")

    versions = [
        nuget.Version.from_string("0.1.0"),
        nuget.Version.from_string("1.0.0-alpha.2"),
        nuget.Version.from_string("1.0.9-alpha.1"),
        nuget.Version.from_string("1.1.0-alpha.1"),
        nuget.Version.from_string("2.0.0"),
        nuget.Version.from_string("2.2.0"),
        nuget.Version.from_string("3.0.0"),
    ]

    assert vrange.FindBestMatch(versions).to_string() == "1.0.9-alpha.1"


def test_FindBestMatch_FloatingPrereleasePatch_BestMatchingStable():

    vrange = NugetVersionRange.from_native("[1.0.*-alpha*, 2.0.0)")

    versions = [
        nuget.Version.from_string("0.1.0"),
        nuget.Version.from_string("1.0.0-alpha.2"),
        nuget.Version.from_string("1.0.9-alpha.1"),
        nuget.Version.from_string("1.0.9"),
        nuget.Version.from_string("1.1.0-alpha.1"),
        nuget.Version.from_string("2.0.0"),
        nuget.Version.from_string("2.2.0"),
        nuget.Version.from_string("3.0.0"),
    ]

    assert vrange.FindBestMatch(versions).to_string() == "1.0.9"


def test_FindBestMatch_FloatingPrereleasePatch_BestMatchingPrerelease():

    vrange = NugetVersionRange.from_native("[1.0.*-alpha*, 2.0.0)")

    versions = [
        nuget.Version.from_string("0.1.0"),
        nuget.Version.from_string("1.0.0-alpha.2"),
        nuget.Version.from_string("1.0.8"),
        nuget.Version.from_string("1.0.9-alpha.1"),
        nuget.Version.from_string("1.1.0-alpha.1"),
        nuget.Version.from_string("2.0.0"),
        nuget.Version.from_string("2.2.0"),
        nuget.Version.from_string("3.0.0"),
    ]

    assert vrange.FindBestMatch(versions).to_string() == "1.0.9-alpha.1"


def test_FindBestMatch_FloatingPrereleaseMinor_NotMatchingPrefix_OutsideOfRange():

    vrange = NugetVersionRange.from_native("[1.*-beta*, 2.0.0)")

    versions = [
        nuget.Version.from_string("0.1.0"),
        nuget.Version.from_string("1.0.0-alpha.2"),
        nuget.Version.from_string("2.0.0"),
        nuget.Version.from_string("2.2.0"),
        nuget.Version.from_string("3.0.0"),
    ]

    assert not vrange.FindBestMatch(versions)


def test_FindBestMatch_FloatingPrereleaseMinor_OutsideOfRange_Lower():

    vrange = NugetVersionRange.from_native("[1.*-*, 2.0.0)")

    versions = [
        nuget.Version.from_string("0.1.0"),
        nuget.Version.from_string("0.8.0"),
        nuget.Version.from_string("0.9.0"),
    ]

    assert not vrange.FindBestMatch(versions)


def test_FindBestMatch_FloatingPrereleaseMinor_OutsideOfRange_Higher():

    vrange = NugetVersionRange.from_native("[1.*-*, 2.0.0)")

    versions = [
        nuget.Version.from_string("2.0.0"),
        nuget.Version.from_string("3.1.0"),
    ]

    assert not vrange.FindBestMatch(versions)


def test_FindBestMatch_FloatingPrereleaseMinor_OnlyMatching():

    vrange = NugetVersionRange.from_native("[1.*-alpha*, 2.0.0)")

    versions = [
        nuget.Version.from_string("0.1.0"),
        nuget.Version.from_string("1.0.0-alpha.2"),
        nuget.Version.from_string("2.0.0"),
        nuget.Version.from_string("2.2.0"),
        nuget.Version.from_string("3.0.0"),
    ]

    assert vrange.FindBestMatch(versions).to_string() == "1.0.0-alpha.2"


def test_FindBestMatch_FloatingPrereleaseMinor_BestMatching():

    vrange = NugetVersionRange.from_native("[1.*-alpha*, 2.0.0)")

    versions = [
        nuget.Version.from_string("0.1.0"),
        nuget.Version.from_string("1.0.0-alpha.2"),
        nuget.Version.from_string("1.0.9-alpha.1"),
        nuget.Version.from_string("1.1.0-alpha.1"),
        nuget.Version.from_string("2.0.0"),
        nuget.Version.from_string("2.2.0"),
        nuget.Version.from_string("3.0.0"),
    ]

    assert vrange.FindBestMatch(versions).to_string() == "1.1.0-alpha.1"


def test_FindBestMatch_FloatingPrereleaseMinor_BestMatchingStable():

    vrange = NugetVersionRange.from_native("[1.*-alpha*, 2.0.0)")

    versions = [
        nuget.Version.from_string("0.1.0"),
        nuget.Version.from_string("1.0.0-alpha.2"),
        nuget.Version.from_string("1.0.9-alpha.1"),
        nuget.Version.from_string("1.1.0-alpha.1"),
        nuget.Version.from_string("1.10.1"),
        nuget.Version.from_string("2.0.0"),
        nuget.Version.from_string("2.2.0"),
        nuget.Version.from_string("3.0.0"),
    ]

    assert vrange.FindBestMatch(versions).to_string() == "1.10.1"


def test_FindBestMatch_FloatingPrereleaseMinor_BestMatchingPrerelease():

    vrange = NugetVersionRange.from_native("[1.*-alpha*, 2.0.0)")

    versions = [
        nuget.Version.from_string("0.1.0"),
        nuget.Version.from_string("1.0.0-alpha.2"),
        nuget.Version.from_string("1.0.9-alpha.1"),
        nuget.Version.from_string("1.1.0-alpha.1"),
        nuget.Version.from_string("1.10.1"),
        nuget.Version.from_string("1.99.1-alpha1"),
        nuget.Version.from_string("2.0.0"),
        nuget.Version.from_string("2.2.0"),
        nuget.Version.from_string("3.0.0"),
    ]

    assert vrange.FindBestMatch(versions).to_string() == "1.99.1-alpha1"


def test_FindBestMatch_PrereleaseRevision_RangeOpen():

    vrange = NugetVersionRange.from_native("[1.0.0.*-*, )")

    versions = [
        nuget.Version.from_string("0.1.0"),
        nuget.Version.from_string("0.2.0"),
        nuget.Version.from_string("1.0.0-alpha.2"),
        nuget.Version.from_string("1.0.0.1-alpha.1"),
        nuget.Version.from_string("1.0.1-alpha.1"),
        nuget.Version.from_string("101.0.0"),
    ]

    assert vrange.FindBestMatch(versions).to_string() == "1.0.0.1-alpha.1"


def test_FindBestMatch_PrereleasePatch_RangeOpen():

    vrange = NugetVersionRange.from_native("[1.0.*-*, )")

    versions = [
        nuget.Version.from_string("0.1.0"),
        nuget.Version.from_string("0.2.0"),
        nuget.Version.from_string("1.0.0-alpha.2"),
        nuget.Version.from_string("1.0.1-beta.2"),
    ]

    assert vrange.FindBestMatch(versions).to_string() == "1.0.1-beta.2"


def test_FindBestMatch_PrereleaseMinor_RangeOpen():

    vrange = NugetVersionRange.from_native("[1.*-*, )")

    versions = [
        nuget.Version.from_string("0.1.0"),
        nuget.Version.from_string("0.2.0"),
        nuget.Version.from_string("1.0.0-alpha.2"),
        nuget.Version.from_string("1.9.0-alpha.2"),
        nuget.Version.from_string("2.0.0-alpha.2"),
        nuget.Version.from_string("101.0.0"),
    ]

    assert vrange.FindBestMatch(versions).to_string() == "1.9.0-alpha.2"


def test_FindBestMatch_PrereleaseMinor_IgnoresPartialPrereleaseMatches():

    vrange = NugetVersionRange.from_native("[1.*-alpha*, )")

    versions = [
        nuget.Version.from_string("0.1.0"),
        nuget.Version.from_string("0.2.0"),
        nuget.Version.from_string("1.0.0-alpha.2"),
        nuget.Version.from_string("1.9.0"),
        nuget.Version.from_string("1.20.0-alph.3"),
        nuget.Version.from_string("101.0.0"),
    ]

    assert vrange.FindBestMatch(versions).to_string() == "1.9.0"


def test_FindBestMatch_PrereleaseMinor_NotMatching_SelectsFirstInRange():

    vrange = NugetVersionRange.from_native("[1.*-alpha*, )")

    versions = [
        nuget.Version.from_string("0.1.0"),
        nuget.Version.from_string("0.2.0"),
        nuget.Version.from_string("1.0.0-alph3.2"),
        nuget.Version.from_string("1.20.0-alph.3"),
        nuget.Version.from_string("101.0.0"),
    ]
    assert vrange.FindBestMatch(versions).to_string() == "1.20.0-alph.3"


def test_FindBestMatch_PrereleaseMajor_IgnoresPartialPrereleaseMatches():

    vrange = NugetVersionRange.from_native("[*-alpha*, )")

    versions = [
        nuget.Version.from_string("0.1.0"),
        nuget.Version.from_string("0.2.0"),
        nuget.Version.from_string("1.0.0-alpha.2"),
        nuget.Version.from_string("1.9.0"),
        nuget.Version.from_string("1.20.0-alph.3"),
    ]

    assert vrange.FindBestMatch(versions).to_string() == "1.9.0"


def test_FindBestMatch_PrereleaseMajor_NotMatching_SelectsFirstInRange():

    vrange = NugetVersionRange.from_native("[*-rc*, )")

    versions = [
        nuget.Version.from_string("0.1.0-beta"),
        nuget.Version.from_string("1.0.0-alpha.2"),
        nuget.Version.from_string("1.9.0-alpha.2"),
        nuget.Version.from_string("2.0.0-alpha.2"),
    ]
    assert vrange.FindBestMatch(versions).to_string() == "0.1.0-beta"


def test_FindBestMatch_PrereleaseMajor_BestMatching():

    vrange = NugetVersionRange.from_native("*-rc*")

    versions = [
        nuget.Version.from_string("1.1.0"),
        nuget.Version.from_string("1.2.0-rc.1"),
        nuget.Version.from_string("1.2.0-rc.2"),
        nuget.Version.from_string("1.2.0-rc1"),
        nuget.Version.from_string("2.0.0"),
        nuget.Version.from_string("3.0.0-beta.1"),
    ]

    assert vrange.FindBestMatch(versions).to_string() == "2.0.0"


def test_FindBestMatch_FloatingPrereleaseRevision_WithPartialMatch():

    vrange = NugetVersionRange.from_native("[1.1.1.1*-*, 2.0.0)")

    versions = [
        nuget.Version.from_string("1.1.1.10"),
        nuget.Version.from_string("3.1.0"),
    ]
    assert vrange.FindBestMatch(versions).to_string() == "1.1.1.10"


def test_FindBestMatch_FloatingRevision_WithPartialMatch():

    vrange = NugetVersionRange.from_native("[1.1.1.1*, 2.0.0)")

    versions = [
        nuget.Version.from_string("1.1.1.10"),
        nuget.Version.from_string("3.1.0"),
    ]

    assert vrange.FindBestMatch(versions).to_string() == "1.1.1.10"


def test_FindBestMatch_FloatingPrereleasePatch_WithPartialMatch():

    vrange = NugetVersionRange.from_native("[1.1.1*-*, 2.0.0)")

    versions = [
        nuget.Version.from_string("1.1.10"),
        nuget.Version.from_string("3.1.0"),
    ]

    assert vrange.FindBestMatch(versions).to_string() == "1.1.10"


def test_FindBestMatch_FloatingPatch_WithPartialMatch():

    vrange = NugetVersionRange.from_native("[1.1.1*, 2.0.0)")

    versions = [
        nuget.Version.from_string("1.1.10"),
        nuget.Version.from_string("3.1.0"),
    ]
    assert vrange.FindBestMatch(versions).to_string() == "1.1.10"


def test_FindBestMatch_FloatingPrereleaseMinor_WithPartialMatch():

    vrange = NugetVersionRange.from_native("[1.1*-*, 2.0.0)")

    versions = [
        nuget.Version.from_string("1.10.1"),
        nuget.Version.from_string("3.1.0"),
    ]

    assert vrange.FindBestMatch(versions).to_string() == "1.10.1"


def test_FindBestMatch_FloatingMinor_WithPartialMatch():

    vrange = NugetVersionRange.from_native("[1.1*, 2.0.0)")

    versions = [
        nuget.Version.from_string("1.10.1"),
        nuget.Version.from_string("3.1.0"),
    ]

    assert vrange.FindBestMatch(versions).to_string() == "1.10.1"


def test_FindBestMatch_FloatingPrerelease_WithExtraDashes():

    vrange = NugetVersionRange.from_native("[1.0.0--*, 2.0.0)")

    versions = [
        nuget.Version.from_string("1.0.0--alpha"),
        nuget.Version.from_string("1.0.0--beta"),
        nuget.Version.from_string("3.1.0"),
    ]

    assert vrange.FindBestMatch(versions).to_string() == "1.0.0--beta"


def test_FindBestMatch_FloatingPrereleaseMinor_WithExtraDashes():

    vrange = NugetVersionRange.from_native("[1.*--*, 2.0.0)")

    versions = [
        nuget.Version.from_string("1.0.0--alpha"),
        nuget.Version.from_string("1.0.0--beta"),
        nuget.Version.from_string("1.9.0--beta"),
        nuget.Version.from_string("3.1.0"),
    ]

    assert vrange.FindBestMatch(versions).to_string() == "1.9.0--beta"


@pytest.mark.parametrize(
    "vrange",
    [
        ("[1.1.4, 1.1.2)"),
        ("[1.1.4, 1.1.2]"),
        ("(1.1.4, 1.1.2)"),
        ("(1.1.4, 1.1.2]"),
        ("[1.0.0, 1.0.0)"),
        ("(1.0.0, 1.0.0]"),
        ("(1.0, 1.0.0]"),
        ("(*, *]"),
        ("[1.0.0-beta, 1.0.0-beta+900)"),
        ("(1.0.0-beta+600, 1.0.0-beta]"),
        ("(1.0)"),
        ("(1.0.0)"),
        ("[2.0.0)"),
        ("(2.0.0]"),
    ],
)
def test_Parse_Illogical_VersionRange_Throws(vrange):
    with pytest.assertraise(Exception):
        NugetVersionRange.from_native(vrange)
        assert exception.Message == "'vrange' is not a valid version string."
