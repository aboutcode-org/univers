# Copyright (c) .NET Foundation. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
# URL: https://github.com/NuGet/NuGet.Client
# Ported to Python from the C# NuGet test suite and significantly modified

import unittest

import pytest


class VersionRangeTests(unittest.TestCase):
    @pytest.mark.parametrize(
        [],
        [
            ("1.0.0", "(>= 1.0.0)"),
            ("[1.0.0]", "(= 1.0.0)"),
            ("[1.0.0, ]", "(>= 1.0.0)"),
            ("[1.0.0, )", "(>= 1.0.0)"),
            ("(1.0.0, )", "(> 1.0.0)"),
            ("(1.0.0, ]", "(> 1.0.0)"),
            ("(1.0.0, 2.0.0)", "(> 1.0.0& < 2.0.0)"),
            ("[1.0.0, 2.0.0]", "(>= 1.0.0& <= 2.0.0)"),
            ("[1.0.0, 2.0.0)", "(>= 1.0.0& < 2.0.0)"),
            ("(1.0.0, 2.0.0]", "(> 1.0.0& <= 2.0.0)"),
            ("(, 2.0.0]", "(<= 2.0.0)"),
            ("(, 2.0.0)", "(< 2.0.0)"),
            ("[, 2.0.0)", "(< 2.0.0)"),
            ("[, 2.0.0]", "(<= 2.0.0)"),
            ("1.0.0-beta*", "(>= 1.0.0-beta)"),
            ("[1.0.0-beta*, 2.0.0)", "(>= 1.0.0-beta& < 2.0.0)"),
            ("[1.0.0-beta.1, 2.0.0-alpha.2]", "(>= 1.0.0-beta.1& <= 2.0.0-alpha.2)"),
            ("[1.0.0+beta.1, 2.0.0+alpha.2]", "(>= 1.0.0& <= 2.0.0)"),
            ("[1.0, 2.0]", "(>= 1.0.0& <= 2.0.0)"),
        ],
    )
    def test_VersionRange_PrettyPrintTests(self, versionString, expected):

        formatter = VersionRangeFormatter()
        range = VersionRange(versionString)

        s = string.Format(formatter, "0:P", range)
        s2 = range.to_string("P", formatter)
        s3 = range.PrettyPrint()

        assert s == expected
        assert s2 == expected
        assert s3 == expected

    @pytest.mark.parametrize(
        [],
        [
            ("1.0.0", False ),
            ("1.*", False ),
            ("*", False ),
            ("[*, )", True),
            ("[1.*, ]", False ),
            ("[1.*, 2.0.0)", True),
            ("(, )", True),
        ],
    )
    def test_VersionRange_NormalizationRoundTripsTest(
        self, versionString, isOriginalStringNormalized
    ):

        originalParsedRange = VersionRange(versionString)

        normalizedRangeRepresentation = originalParsedRange.to_string()

        roundTrippedRange = VersionRange(normalizedRangeRepresentation)

        assert roundTrippedRange == originalParsedRange
        assert roundTrippedRange.to_string() == originalParsedRange.to_string()
        if isOriginalStringNormalized:

            assert versionString == originalParsedRange.to_string()

        else:

            Assert.NotEqual(originalParsedRange.to_string(), versionString)

    def test_VersionRange_PrettyPrintAllRange(self):

        formatter = VersionRangeFormatter()
        range = VersionRange.All

        s = string.Format(formatter, "0:P", range)
        s2 = range.to_string("P", formatter)
        s3 = range.PrettyPrint()

        assert s == ""
        assert s2 == ""
        assert s3 == ""

    @pytest.mark.parametrize(
        [],
        [
            ("1.0.0", "1.0.1-beta", False ),
            ("1.0.0", "1.0.1", True),
            ("1.0.0-*", "1.0.0-beta", True),
            ("1.0.0-beta.*", "1.0.0-beta.1", True),
            ("1.0.0-beta-*", "1.0.0-beta-01", True),
            ("1.0.0-beta-*", "2.0.0-beta", True),
            ("1.0.*", "1.0.0-beta", False ),
            ("1.*", "1.0.0-beta", False ),
            ("*", "1.0.0-beta", False ),
            ("[1.0.0, 2.0.0]", "1.5.0-beta", False ),
            ("[1.0.0, 2.0.0-beta]", "1.5.0-beta", True),
            ("[1.0.0-beta, 2.0.0]", "1.5.0-beta", True),
            ("[1.0.0-beta, 2.0.0]", "3.5.0-beta", False ),
            ("[1.0.0-beta, 2.0.0]", "0.5.0-beta", False ),
            ("[1.0.0-beta, 2.0.0)", "2.0.0", False ),
            ("[1.0.0-beta, 2.0.0)", "2.0.0-beta", True),
            ("[1.0.*, 2.0.0-beta]", "2.0.0-beta", True),
        ],
    )
    def test_VersionRange_IsBetter_Prerelease(self, rangeString, versionString, expected):

        range = VersionRange(rangeString)
        considering = NuGetVersion(versionString)

        result = range.IsBetter(current=None, considering=considering)

        assert result == expected

    def test_VersionRange_MetadataIsIgnored_Satisfy(self):

        noMetadata = VersionRange("[1.0.0, 2.0.0]")
        lowerMetadata = VersionRange("[1.0.0+A, 2.0.0]")
        upperMetadata = VersionRange("[1.0.0, 2.0.0+A]")
        bothMetadata = VersionRange("[1.0.0+A, 2.0.0+A]")

        versionNoMetadata = NuGetVersion("1.0.0")
        versionMetadata = NuGetVersion("1.0.0+B")

        assert noMetadata.Satisfies(versionNoMetadata)
        assert noMetadata.Satisfies(versionMetadata)
        assert lowerMetadata.Satisfies(versionNoMetadata)
        assert lowerMetadata.Satisfies(versionMetadata)
        assert upperMetadata.Satisfies(versionNoMetadata)
        assert upperMetadata.Satisfies(versionMetadata)
        assert bothMetadata.Satisfies(versionNoMetadata)
        assert bothMetadata.Satisfies(versionMetadata)

    def test_VersionRange_MetadataIsIgnored_Equality(self):

        noMetadata = VersionRange("[1.0.0, 2.0.0]")
        lowerMetadata = VersionRange("[1.0.0+A, 2.0.0]")
        upperMetadata = VersionRange("[1.0.0, 2.0.0+A]")
        bothMetadata = VersionRange("[1.0.0+A, 2.0.0+A]")

        assert noMetadata.Equals(lowerMetadata)
        assert lowerMetadata.Equals(upperMetadata)
        assert upperMetadata.Equals(bothMetadata)
        assert bothMetadata.Equals(noMetadata)

    def test_VersionRange_MetadataIsIgnored_FormatRemovesMetadata(self):

        bothMetadata = VersionRange("[1.0.0+A, 2.0.0+A]")

        assert bothMetadata.to_string() == "[1.0.0, 2.0.0]"
        assert bothMetadata.to_string() == "[1.0.0, 2.0.0]"
        assert bothMetadata.ToLegacyString() == "[1.0.0, 2.0.0]"

    def test_VersionRange_FloatAllStable_ReturnsCorrectPrints(self):

        bothMetadata = VersionRange("*")

        assert bothMetadata.to_string() == "[*, )"
        assert bothMetadata.to_string() == "[*, )"
        assert bothMetadata.ToLegacyString() == "[0.0.0, )"
        # Note that this matches version strings generated by other version ranges such as 0.*, 0.0.*

    def test_VersionRange_AllSpecialCases_NormalizeSame(self):

        assert VersionRange.All.to_string() == "(, )"
        # pragma warning disable CS0618 # Type or member is obsolete
        assert VersionRange.AllFloating.to_string() == "(, )"
        assert VersionRange.AllStable.to_string() == "(, )"
        assert VersionRange.AllStableFloating.to_string() == "(, )"

    # pragma warning restore CS0618 # Type or member is obsolete

    def test_VersionRange_MetadataIsIgnored_FormatRemovesMetadata_Short(self):

        bothMetadata = VersionRange("[1.0.0+A, )")

        assert bothMetadata.ToLegacyShortString() == "1.0.0"

    def test_VersionRange_MetadataIsIgnored_FormatRemovesMetadata_PrettyPrint(self):

        bothMetadata = VersionRange("[1.0.0+A, )")

        assert bothMetadata.PrettyPrint() == "(>= 1.0.0)"

    @pytest.mark.parametrize(
        [],
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
    def test_VersionRange_VerifyNonSnapshotVersion(self, snapshot, expected):

        range = VersionRange(snapshot)

        updated = range.ToNonSnapshotRange()

        assert updated.ToLegacyShortString() == expected

    @pytest.mark.parametrize(
        [],
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
    def test_VersionRange_IncludePrerelease(self, s):

        range = VersionRange(s)

        assert range.IsFloating == range.IsFloating
        assert range.Float == range.Float
        assert range.to_string() == range.to_string()

    def test_ParseVersionRangeSingleDigit(self):

        versionInfo = VersionRange("[1,3)")
        assert versionInfo.MinVersion.to_string() == "1.0.0"
        assert versionInfo.IsMinInclusive
        assert versionInfo.MaxVersion.to_string() == "3.0.0"
        assert not versionInfo.IsMaxInclusive

    def test_VersionRange_Exact(self):

        versionInfo = VersionRange(NuGetVersion(4, 3, 0), True, NuGetVersion(4, 3, 0), True)

        assert versionInfo.Satisfies(NuGetVersion("4.3.0"))

    @pytest.mark.parametrize(
        [],
        [
            ("0", "0.0"),
            ("1", "1.0.0"),
            ("02", "2.0.0.0"),
            ("123.456", "123.456.0.0"),
            ("[2021,)", "[2021.0.0.0,)"),
            ("[,2021)", "[,2021.0.0.0)"),
        ],
    )
    def test_VersionRange_MissingVersionComponents_DefaultToZero(
        self, shortVersionSpec, longVersionSpec
    ):

        versionRange1 = VersionRange(shortVersionSpec)
        versionRange2 = VersionRange(longVersionSpec)

        assert versionRange1 == versionRange2

    @pytest.mark.parametrize(
        [],
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
    def test_ParseVersionRangeDoesNotSatisfy(self, spec, version):

        versionInfo = VersionRange(spec)
        middleVersion = NuGetVersion(version)

        assert not versionInfo.Satisfies(middleVersion)
        assert not versionInfo.Satisfies(middleVersion, VersionComparison.Default)
        assert not versionInfo.Satisfies(middleVersion, VersionComparer.Default)
        assert not versionInfo.Satisfies(middleVersion, VersionComparison.VersionRelease)
        assert not versionInfo.Satisfies(middleVersion, VersionComparer.VersionRelease)
        assert not versionInfo.Satisfies(middleVersion, VersionComparison.VersionReleaseMetadata)
        assert not versionInfo.Satisfies(middleVersion, VersionComparer.VersionReleaseMetadata)

    @pytest.mark.parametrize(
        [],
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
    def test_ParseVersionRangeSatisfies(self, spec, version):

        versionInfo = VersionRange(spec)
        middleVersion = NuGetVersion(version)

        assert versionInfo.Satisfies(middleVersion)
        assert versionInfo.Satisfies(middleVersion, VersionComparison.Default)
        assert versionInfo.Satisfies(middleVersion, VersionComparer.VersionRelease)

    @pytest.mark.parametrize(
        [],
        [
            ("1.0.0", "2.0.0", True, True),
            ("1.0.0", "1.0.1", False , False ),
            ("1.0.0-beta+0", "2.0.0", False , True),
            ("1.0.0-beta+0", "2.0.0+99", False , False ),
            ("1.0.0-beta+0", "2.0.0+99", True, True),
            ("1.0.0", "2.0.0+99", True, True),
        ],
    )
    def test_ParseVersionRangeParts(self, minString, maxString, minInc, maxInc):

        min = NuGetVersion(minString)
        max = NuGetVersion(maxString)

        versionInfo = VersionRange(min, minInc, max, maxInc)

        assert VersionComparer.Default == min, versionInfo.MinVersion
        assert VersionComparer.Default == max, versionInfo.MaxVersion
        assert versionInfo.IsMinInclusive == minInc
        assert versionInfo.IsMaxInclusive == maxInc

    @pytest.mark.parametrize(
        [],
        [
            ("1.0.0", "2.0.0", True, True),
            ("1.0.0", "1.0.1", False , False ),
            ("1.0.0-beta+0", "2.0.0", False , True),
            ("1.0.0-beta+0", "2.0.0+99", False , False ),
            ("1.0.0-beta+0", "2.0.0+99", True, True),
            ("1.0.0", "2.0.0+99", True, True),
        ],
    )
    def test_ParseVersionRangeto_stringReParse(self, minString, maxString, minInc, maxInc):

        min = NuGetVersion(minString)
        max = NuGetVersion(maxString)

        original = VersionRange(min, minInc, max, maxInc)
        versionInfo = VersionRange(original.to_string())

        assert VersionComparer.Default == min, versionInfo.MinVersion
        assert VersionComparer.Default == max, versionInfo.MaxVersion
        assert versionInfo.IsMinInclusive == minInc
        assert versionInfo.IsMaxInclusive == maxInc

    @pytest.mark.parametrize(
        [],
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
    def test_ParseVersionRangeto_stringShortHand(self, version, expected):

        versionInfo = VersionRange(version)

        assert VersionRangeFormatter() == expected, versionInfo.to_string("S")

    @pytest.mark.parametrize(
        [],
        [
            ("1.2.0", "[1.2.0, )"),
            ("1.2.3-beta.2.4.55.X+900", "[1.2.3-beta.2.4.55.X, )"),
        ],
    )
    def test_ParseVersionRangeto_string(self, version, expected):

        versionInfo = VersionRange(version)

        assert versionInfo.to_string() == expected

    def test_ParseVersionRangeSimpleVersionNoBrackets(self):

        versionInfo = VersionRange("1.2")

        assert versionInfo.MinVersion.to_string() == "1.2"
        assert versionInfo.IsMinInclusive
        assert versionInfo.MaxVersion == None
        assert not versionInfo.IsMaxInclusive

    def test_ParseVersionRangeSimpleVersionNoBracketsExtraSpaces(self):

        versionInfo = VersionRange("  1  .   2  ")

        assert versionInfo.MinVersion.to_string() == "1.2"
        assert versionInfo.IsMinInclusive
        assert versionInfo.MaxVersion == None
        assert not versionInfo.IsMaxInclusive

    def test_ParseVersionRangeMaxOnlyInclusive(self):

        versionInfo = VersionRange("(,1.2]")

        assert versionInfo.MinVersion == None
        assert not versionInfo.IsMinInclusive
        assert versionInfo.MaxVersion.to_string() == "1.2"
        assert versionInfo.IsMaxInclusive

    def test_ParseVersionRangeMaxOnlyExclusive(self):

        versionInfo = VersionRange("(,1.2)")
        assert versionInfo.MinVersion == None
        assert not versionInfo.IsMinInclusive
        assert versionInfo.MaxVersion.to_string() == "1.2"
        assert not versionInfo.IsMaxInclusive

    def test_ParseVersionRangeExactVersion(self):

        versionInfo = VersionRange("[1.2]")

        assert versionInfo.MinVersion.to_string() == "1.2"
        assert versionInfo.IsMinInclusive
        assert versionInfo.MaxVersion.to_string() == "1.2"
        assert versionInfo.IsMaxInclusive

    def test_ParseVersionRangeMinOnlyExclusive(self):

        versionInfo = VersionRange("(1.2,)")

        assert versionInfo.MinVersion.to_string() == "1.2"
        assert not versionInfo.IsMinInclusive
        assert versionInfo.MaxVersion == None
        assert not versionInfo.IsMaxInclusive

    def test_ParseVersionRangeExclusiveExclusive(self):

        versionInfo = VersionRange("(1.2,2.3)")

        assert versionInfo.MinVersion.to_string() == "1.2"
        assert not versionInfo.IsMinInclusive
        assert versionInfo.MaxVersion.to_string() == "2.3"
        assert not versionInfo.IsMaxInclusive

    def test_ParseVersionRangeExclusiveInclusive(self):

        versionInfo = VersionRange("(1.2,2.3]")

        assert versionInfo.MinVersion.to_string() == "1.2"
        assert not versionInfo.IsMinInclusive
        assert versionInfo.MaxVersion.to_string() == "2.3"
        assert versionInfo.IsMaxInclusive

    def test_ParseVersionRangeInclusiveExclusive(self):

        versionInfo = VersionRange("[1.2,2.3)")
        assert versionInfo.MinVersion.to_string() == "1.2"
        assert versionInfo.IsMinInclusive
        assert versionInfo.MaxVersion.to_string() == "2.3"
        assert not versionInfo.IsMaxInclusive

    def test_ParseVersionRangeInclusiveInclusive(self):

        versionInfo = VersionRange("[1.2,2.3]")

        assert versionInfo.MinVersion.to_string() == "1.2"
        assert versionInfo.IsMinInclusive
        assert versionInfo.MaxVersion.to_string() == "2.3"
        assert versionInfo.IsMaxInclusive

    def test_ParseVersionRangeInclusiveInclusiveExtraSpaces(self):

        versionInfo = VersionRange("   [  1 .2   , 2  .3   ]  ")

        assert versionInfo.MinVersion.to_string() == "1.2"
        assert versionInfo.IsMinInclusive
        assert versionInfo.MaxVersion.to_string() == "2.3"
        assert versionInfo.IsMaxInclusive

    @pytest.mark.parametrize(
        [],
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
    def test_ParsedVersionRangeHasOriginalString(self, range):

        versionInfo = VersionRange(range)

        assert versionInfo.OriginalString == range

    def test_ParseVersionToNormalizedVersion(self):

        versionString = "(1.0,1.2]"

        assert VersionRange(versionString).to_string() == "(1.0.0, 1.2.0]"

    @pytest.mark.parametrize(
        [],
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
    def test_StringFormatNullProvider(self, range):

        versionRange = VersionRange(range)
        actual = string.Format("0", versionRange)
        expected = versionRange.to_string()

        assert actual == expected

    @pytest.mark.parametrize(
        [],
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
    def test_StringFormatNullProvider2(self, range):

        versionRange = VersionRange(range)
        actual = string.Format(CultureInfo.InvariantCulture, "0", versionRange)
        expected = versionRange.to_string()

        assert actual == expected

    @pytest.mark.parametrize(
        [],
        [
            ("(1.2.3.4, 3.2)", "1.2.3.4", False , "3.2", False ),
            ("(1.2.3.4, 3.2]", "1.2.3.4", False , "3.2", True),
            ("[1.2, 3.2.5)", "1.2", True, "3.2.5", False ),
            ("[2.3.7, 3.2.4.5]", "2.3.7", True, "3.2.4.5", True),
            ("(, 3.2.4.5]", None, False , "3.2.4.5", True),
            ("(1.6, ]", "1.6", False , None, True),
            ("[2.7]", "2.7", True, "2.7", True),
        ],
    )
    def test_ParseVersionParsesTokensVersionsCorrectly(
        self, versionString, min, incMin, max, incMax
    ):

        versionRange = VersionRange(
            None if min == None else NuGetVersion(min),
            incMin,
            None if max == None else NuGetVersion(max),
            incMax,
        )

        actual = VersionRange(versionString)

        assert actual.IsMinInclusive == versionRange.IsMinInclusive
        assert actual.IsMaxInclusive == versionRange.IsMaxInclusive
        assert actual.MinVersion == versionRange.MinVersion
        assert actual.MaxVersion == versionRange.MaxVersion

    @pytest.mark.parametrize(
        [],
        [
            ("1.0.0", "1.0.*", False ),
            ("[1.0.0,)", "[1.0.*, )", False ),
            ("1.1.*", "1.0.*", False ),
        ],
    )
    def test_VersionRange_Equals(self, versionString1, versionString2, isEquals):

        range1 = VersionRange(versionString1)
        range2 = VersionRange(versionString2)

        assert range1.Equals(range2) == isEquals

    def test_VersionRange_to_stringRevPrefix(self):

        range = VersionRange("1.1.1.*-*")

        assert range.to_string() == "[1.1.1.*-*, )"

    def test_VersionRange_to_stringPatchPrefix(self):

        range = VersionRange("1.1.*-*")

        assert range.to_string() == "[1.1.*-*, )"

    def test_VersionRange_to_stringMinorPrefix(self):

        range = VersionRange("1.*-*")

        assert range.to_string() == "[1.*-*, )"

    def test_VersionRange_to_stringAbsoluteLatest(self):

        range = VersionRange("*-*")

        assert range.to_string() == "[*-*, )"
        assert range.MinVersion.to_string() == "0.0.0-0"
        assert range.Float.MinVersion.to_string() == "0.0.0-0"
        assert range.Float.FloatBehavior == NuGetVersionFloatBehavior.AbsoluteLatest

    def test_VersionRange_to_stringPrereleaseMajor(self):

        range = VersionRange("*-rc.*")

        assert range.to_string() == "[*-rc.*, )"
        assert range.MinVersion.to_string() == "0.0.0-rc.0"
        assert range.Float.MinVersion.to_string() == "0.0.0-rc.0"
        assert range.Float.FloatBehavior == NuGetVersionFloatBehavior.PrereleaseMajor

    def test_FindBestMatch_FloatingPrereleaseRevision_OutsideOfRange(self):

        range = VersionRange("[1.0.0.*-*, 2.0.0)")

        versions = [
            NuGetVersion("0.1.0"),
            NuGetVersion("2.0.0"),
            NuGetVersion("2.2.0"),
            NuGetVersion("3.0.0"),
        ]

        assert not range.FindBestMatch(versions)

    def test_FindBestMatch_FloatingPrereleaseRevision_NotMatchingPrefix_OutsideOfRange(self):

        range = VersionRange("[1.0.0.*-beta*, 2.0.0)")

        versions = [
            NuGetVersion("0.1.0"),
            NuGetVersion("1.0.0-alpha.2"),
            NuGetVersion("2.0.0"),
            NuGetVersion("2.2.0"),
            NuGetVersion("3.0.0"),
        ]

        assert not range.FindBestMatch(versions)

    def test_FindBestMatch_FloatingPrereleaseRevision_OutsideOfRange_Lower(self):

        range = VersionRange("[1.1.1.*-*, 2.0.0)")

        versions = [
            NuGetVersion("0.1.0"),
            NuGetVersion("0.8.0"),
            NuGetVersion("0.9.0"),
            NuGetVersion("1.0.0"),
        ]

        assert not range.FindBestMatch(versions)

    def test_FindBestMatch_FloatingPrereleaseRevision_OutsideOfRange_Higher(self):

        range = VersionRange("[1.1.1.*-*, 2.0.0)")

        versions = [
            NuGetVersion("2.0.0"),
            NuGetVersion("3.1.0"),
        ]

        assert not range.FindBestMatch(versions)

    def test_FindBestMatch_FloatingPrereleaseRevision_OnlyMatching(self):

        range = VersionRange("[1.0.1.*-alpha*, 2.0.0)")

        versions = [
            NuGetVersion("0.1.0"),
            NuGetVersion("1.0.1-alpha.2"),
            NuGetVersion("2.0.0"),
            NuGetVersion("2.2.0"),
            NuGetVersion("3.0.0"),
        ]

        assert range.FindBestMatch(versions).to_string() == "1.0.1-alpha.2"

    def test_FindBestMatch_FloatingPrereleaseRevision_BestMatching(self):

        range = VersionRange("[1.0.1.*-alpha*, 2.0.0)")

        versions = [
            NuGetVersion("0.1.0"),
            NuGetVersion("1.0.0-alpha.2"),
            NuGetVersion("1.0.1.9-alpha.1"),
            NuGetVersion("1.1.0-alpha.1"),
            NuGetVersion("2.0.0"),
            NuGetVersion("2.2.0"),
            NuGetVersion("3.0.0"),
        ]

        assert range.FindBestMatch(versions).to_string() == "1.0.1.9-alpha.1"

    def test_FindBestMatch_FloatingPrereleaseRevision_BestMatchingStable(self):

        range = VersionRange("[1.0.1.*-alpha*, 2.0.0)")

        versions = [
            NuGetVersion("0.1.0"),
            NuGetVersion("1.0.0-alpha.2"),
            NuGetVersion("1.0.1.9"),
            NuGetVersion("1.0.9-alpha.1"),
            NuGetVersion("1.1.0-alpha.1"),
            NuGetVersion("2.0.0"),
            NuGetVersion("2.2.0"),
            NuGetVersion("3.0.0"),
        ]

        assert range.FindBestMatch(versions).to_string() == "1.0.1.9"

    def test_FindBestMatch_FloatingPrereleaseRevision_BestMatchingFloating(self):

        range = VersionRange("[1.0.1.*-alpha*, 2.0.0)")

        versions = [
            NuGetVersion("0.1.0"),
            NuGetVersion("1.0.0-alpha.2"),
            NuGetVersion("1.0.1.8"),
            NuGetVersion("1.0.1.9-alpha.1"),
            NuGetVersion("1.1.0-alpha.1"),
            NuGetVersion("2.0.0"),
            NuGetVersion("2.2.0"),
            NuGetVersion("3.0.0"),
        ]

        assert range.FindBestMatch(versions).to_string() == "1.0.1.9-alpha.1"

    def test_FindBestMatch_FloatingPrereleasePatch_OutsideOfRange(self):

        range = VersionRange("[1.0.*-*, 2.0.0)")

        versions = [
            NuGetVersion("0.1.0"),
            NuGetVersion("2.0.0"),
            NuGetVersion("2.2.0"),
            NuGetVersion("3.0.0"),
        ]

        assert not range.FindBestMatch(versions)

    def test_FindBestMatch_FloatingPrereleasePatch_NotMatchingPrefix_OutsideOfRange(self):

        range = VersionRange("[1.0.*-beta*, 2.0.0)")

        versions = [
            NuGetVersion("0.1.0"),
            NuGetVersion("1.0.0-alpha.2"),
            NuGetVersion("2.0.0"),
            NuGetVersion("2.2.0"),
            NuGetVersion("3.0.0"),
        ]

        assert not range.FindBestMatch(versions)

    def test_FindBestMatch_FloatingPrereleasePatch_OutsideOfRange_Lower(self):

        range = VersionRange("[1.1.*-*, 2.0.0)")

        versions = [
            NuGetVersion("0.1.0"),
            NuGetVersion("0.8.0"),
            NuGetVersion("0.9.0"),
            NuGetVersion("1.0.0"),
        ]

        assert not range.FindBestMatch(versions)

    def test_FindBestMatch_FloatingPrereleasePatch_OutsideOfRange_Higher(self):

        range = VersionRange("[1.1.*-*, 2.0.0)")

        versions = [
            NuGetVersion("2.0.0"),
            NuGetVersion("3.1.0"),
        ]
        assert not range.FindBestMatch(versions)

    def test_FindBestMatch_FloatingPrereleasePatch_OnlyMatching(self):

        range = VersionRange("[1.0.*-alpha*, 2.0.0)")

        versions = [
            NuGetVersion("0.1.0"),
            NuGetVersion("1.0.0-alpha.2"),
            NuGetVersion("2.0.0"),
            NuGetVersion("2.2.0"),
            NuGetVersion("3.0.0"),
        ]

        assert range.FindBestMatch(versions).to_string() == "1.0.0-alpha.2"

    def test_FindBestMatch_FloatingPrereleasePatch_BestMatching(self):

        range = VersionRange("[1.0.*-alpha*, 2.0.0)")

        versions = [
            NuGetVersion("0.1.0"),
            NuGetVersion("1.0.0-alpha.2"),
            NuGetVersion("1.0.9-alpha.1"),
            NuGetVersion("1.1.0-alpha.1"),
            NuGetVersion("2.0.0"),
            NuGetVersion("2.2.0"),
            NuGetVersion("3.0.0"),
        ]

        assert range.FindBestMatch(versions).to_string() == "1.0.9-alpha.1"

    def test_FindBestMatch_FloatingPrereleasePatch_BestMatchingStable(self):

        range = VersionRange("[1.0.*-alpha*, 2.0.0)")

        versions = [
            NuGetVersion("0.1.0"),
            NuGetVersion("1.0.0-alpha.2"),
            NuGetVersion("1.0.9-alpha.1"),
            NuGetVersion("1.0.9"),
            NuGetVersion("1.1.0-alpha.1"),
            NuGetVersion("2.0.0"),
            NuGetVersion("2.2.0"),
            NuGetVersion("3.0.0"),
        ]

        assert range.FindBestMatch(versions).to_string() == "1.0.9"

    def test_FindBestMatch_FloatingPrereleasePatch_BestMatchingPrerelease(self):

        range = VersionRange("[1.0.*-alpha*, 2.0.0)")

        versions = [
            NuGetVersion("0.1.0"),
            NuGetVersion("1.0.0-alpha.2"),
            NuGetVersion("1.0.8"),
            NuGetVersion("1.0.9-alpha.1"),
            NuGetVersion("1.1.0-alpha.1"),
            NuGetVersion("2.0.0"),
            NuGetVersion("2.2.0"),
            NuGetVersion("3.0.0"),
        ]

        assert range.FindBestMatch(versions).to_string() == "1.0.9-alpha.1"

    def test_FindBestMatch_FloatingPrereleaseMinor_NotMatchingPrefix_OutsideOfRange(self):

        range = VersionRange("[1.*-beta*, 2.0.0)")

        versions = [
            NuGetVersion("0.1.0"),
            NuGetVersion("1.0.0-alpha.2"),
            NuGetVersion("2.0.0"),
            NuGetVersion("2.2.0"),
            NuGetVersion("3.0.0"),
        ]

        assert not range.FindBestMatch(versions)

    def test_FindBestMatch_FloatingPrereleaseMinor_OutsideOfRange_Lower(self):

        range = VersionRange("[1.*-*, 2.0.0)")

        versions = [
            NuGetVersion("0.1.0"),
            NuGetVersion("0.8.0"),
            NuGetVersion("0.9.0"),
        ]

        assert not range.FindBestMatch(versions)

    def test_FindBestMatch_FloatingPrereleaseMinor_OutsideOfRange_Higher(self):

        range = VersionRange("[1.*-*, 2.0.0)")

        versions = [
            NuGetVersion("2.0.0"),
            NuGetVersion("3.1.0"),
        ]

        assert not range.FindBestMatch(versions)

    def test_FindBestMatch_FloatingPrereleaseMinor_OnlyMatching(self):

        range = VersionRange("[1.*-alpha*, 2.0.0)")

        versions = [
            NuGetVersion("0.1.0"),
            NuGetVersion("1.0.0-alpha.2"),
            NuGetVersion("2.0.0"),
            NuGetVersion("2.2.0"),
            NuGetVersion("3.0.0"),
        ]

        assert range.FindBestMatch(versions).to_string() == "1.0.0-alpha.2"

    def test_FindBestMatch_FloatingPrereleaseMinor_BestMatching(self):

        range = VersionRange("[1.*-alpha*, 2.0.0)")

        versions = [
            NuGetVersion("0.1.0"),
            NuGetVersion("1.0.0-alpha.2"),
            NuGetVersion("1.0.9-alpha.1"),
            NuGetVersion("1.1.0-alpha.1"),
            NuGetVersion("2.0.0"),
            NuGetVersion("2.2.0"),
            NuGetVersion("3.0.0"),
        ]

        assert range.FindBestMatch(versions).to_string() == "1.1.0-alpha.1"

    def test_FindBestMatch_FloatingPrereleaseMinor_BestMatchingStable(self):

        range = VersionRange("[1.*-alpha*, 2.0.0)")

        versions = [
            NuGetVersion("0.1.0"),
            NuGetVersion("1.0.0-alpha.2"),
            NuGetVersion("1.0.9-alpha.1"),
            NuGetVersion("1.1.0-alpha.1"),
            NuGetVersion("1.10.1"),
            NuGetVersion("2.0.0"),
            NuGetVersion("2.2.0"),
            NuGetVersion("3.0.0"),
        ]

        assert range.FindBestMatch(versions).to_string() == "1.10.1"

    def test_FindBestMatch_FloatingPrereleaseMinor_BestMatchingPrerelease(self):

        range = VersionRange("[1.*-alpha*, 2.0.0)")

        versions = [
            NuGetVersion("0.1.0"),
            NuGetVersion("1.0.0-alpha.2"),
            NuGetVersion("1.0.9-alpha.1"),
            NuGetVersion("1.1.0-alpha.1"),
            NuGetVersion("1.10.1"),
            NuGetVersion("1.99.1-alpha1"),
            NuGetVersion("2.0.0"),
            NuGetVersion("2.2.0"),
            NuGetVersion("3.0.0"),
        ]

        assert range.FindBestMatch(versions).to_string() == "1.99.1-alpha1"

    def test_FindBestMatch_PrereleaseRevision_RangeOpen(self):

        range = VersionRange("[1.0.0.*-*, )")

        versions = [
            NuGetVersion("0.1.0"),
            NuGetVersion("0.2.0"),
            NuGetVersion("1.0.0-alpha.2"),
            NuGetVersion("1.0.0.1-alpha.1"),
            NuGetVersion("1.0.1-alpha.1"),
            NuGetVersion("101.0.0"),
        ]

        assert range.FindBestMatch(versions).to_string() == "1.0.0.1-alpha.1"

    def test_FindBestMatch_PrereleasePatch_RangeOpen(self):

        range = VersionRange("[1.0.*-*, )")

        versions = [
            NuGetVersion("0.1.0"),
            NuGetVersion("0.2.0"),
            NuGetVersion("1.0.0-alpha.2"),
            NuGetVersion("1.0.1-beta.2"),
        ]

        assert range.FindBestMatch(versions).to_string() == "1.0.1-beta.2"

    def test_FindBestMatch_PrereleaseMinor_RangeOpen(self):

        range = VersionRange("[1.*-*, )")

        versions = [
            NuGetVersion("0.1.0"),
            NuGetVersion("0.2.0"),
            NuGetVersion("1.0.0-alpha.2"),
            NuGetVersion("1.9.0-alpha.2"),
            NuGetVersion("2.0.0-alpha.2"),
            NuGetVersion("101.0.0"),
        ]

        assert range.FindBestMatch(versions).to_string() == "1.9.0-alpha.2"

    def test_FindBestMatch_PrereleaseMinor_IgnoresPartialPrereleaseMatches(self):

        range = VersionRange("[1.*-alpha*, )")

        versions = [
            NuGetVersion("0.1.0"),
            NuGetVersion("0.2.0"),
            NuGetVersion("1.0.0-alpha.2"),
            NuGetVersion("1.9.0"),
            NuGetVersion("1.20.0-alph.3"),
            NuGetVersion("101.0.0"),
        ]

        assert range.FindBestMatch(versions).to_string() == "1.9.0"

    def test_FindBestMatch_PrereleaseMinor_NotMatching_SelectsFirstInRange(self):

        range = VersionRange("[1.*-alpha*, )")

        versions = [
            NuGetVersion("0.1.0"),
            NuGetVersion("0.2.0"),
            NuGetVersion("1.0.0-alph3.2"),
            NuGetVersion("1.20.0-alph.3"),
            NuGetVersion("101.0.0"),
        ]
        assert range.FindBestMatch(versions).to_string() == "1.20.0-alph.3"

    def test_FindBestMatch_PrereleaseMajor_IgnoresPartialPrereleaseMatches(self):

        range = VersionRange("[*-alpha*, )")

        versions = [
            NuGetVersion("0.1.0"),
            NuGetVersion("0.2.0"),
            NuGetVersion("1.0.0-alpha.2"),
            NuGetVersion("1.9.0"),
            NuGetVersion("1.20.0-alph.3"),
        ]

        assert range.FindBestMatch(versions).to_string() == "1.9.0"

    def test_FindBestMatch_PrereleaseMajor_NotMatching_SelectsFirstInRange(self):

        range = VersionRange("[*-rc*, )")

        versions = [
            NuGetVersion("0.1.0-beta"),
            NuGetVersion("1.0.0-alpha.2"),
            NuGetVersion("1.9.0-alpha.2"),
            NuGetVersion("2.0.0-alpha.2"),
        ]
        assert range.FindBestMatch(versions).to_string() == "0.1.0-beta"

    def test_FindBestMatch_PrereleaseMajor_BestMatching(self):

        range = VersionRange("*-rc*")

        versions = [
            NuGetVersion("1.1.0"),
            NuGetVersion("1.2.0-rc.1"),
            NuGetVersion("1.2.0-rc.2"),
            NuGetVersion("1.2.0-rc1"),
            NuGetVersion("2.0.0"),
            NuGetVersion("3.0.0-beta.1"),
        ]

        assert range.FindBestMatch(versions).to_string() == "2.0.0"

    def test_FindBestMatch_FloatingPrereleaseRevision_WithPartialMatch(self):

        range = VersionRange("[1.1.1.1*-*, 2.0.0)")

        versions = [
            NuGetVersion("1.1.1.10"),
            NuGetVersion("3.1.0"),
        ]
        assert range.FindBestMatch(versions).to_string() == "1.1.1.10"

    def test_FindBestMatch_FloatingRevision_WithPartialMatch(self):

        range = VersionRange("[1.1.1.1*, 2.0.0)")

        versions = [
            NuGetVersion("1.1.1.10"),
            NuGetVersion("3.1.0"),
        ]

        assert range.FindBestMatch(versions).to_string() == "1.1.1.10"

    def test_FindBestMatch_FloatingPrereleasePatch_WithPartialMatch(self):

        range = VersionRange("[1.1.1*-*, 2.0.0)")

        versions = [
            NuGetVersion("1.1.10"),
            NuGetVersion("3.1.0"),
        ]

        assert range.FindBestMatch(versions).to_string() == "1.1.10"

    def test_FindBestMatch_FloatingPatch_WithPartialMatch(self):

        range = VersionRange("[1.1.1*, 2.0.0)")

        versions = [
            NuGetVersion("1.1.10"),
            NuGetVersion("3.1.0"),
        ]
        assert range.FindBestMatch(versions).to_string() == "1.1.10"

    def test_FindBestMatch_FloatingPrereleaseMinor_WithPartialMatch(self):

        range = VersionRange("[1.1*-*, 2.0.0)")

        versions = [
            NuGetVersion("1.10.1"),
            NuGetVersion("3.1.0"),
        ]

        assert range.FindBestMatch(versions).to_string() == "1.10.1"

    def test_FindBestMatch_FloatingMinor_WithPartialMatch(self):

        range = VersionRange("[1.1*, 2.0.0)")

        versions = [
            NuGetVersion("1.10.1"),
            NuGetVersion("3.1.0"),
        ]

        assert range.FindBestMatch(versions).to_string() == "1.10.1"

    def test_FindBestMatch_FloatingPrerelease_WithExtraDashes(self):

        range = VersionRange("[1.0.0--*, 2.0.0)")

        versions = [
            NuGetVersion("1.0.0--alpha"),
            NuGetVersion("1.0.0--beta"),
            NuGetVersion("3.1.0"),
        ]

        assert range.FindBestMatch(versions).to_string() == "1.0.0--beta"

    def test_FindBestMatch_FloatingPrereleaseMinor_WithExtraDashes(self):

        range = VersionRange("[1.*--*, 2.0.0)")

        versions = [
            NuGetVersion("1.0.0--alpha"),
            NuGetVersion("1.0.0--beta"),
            NuGetVersion("1.9.0--beta"),
            NuGetVersion("3.1.0"),
        ]

        assert range.FindBestMatch(versions).to_string() == "1.9.0--beta"

    @pytest.mark.parametrize(
        [],
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
    def test_Parse_Illogical_VersionRange_Throws(self, range):
        with pytest.assertraise(Exception):
            VersionRange(range)
            assert exception.Message == "'range' is not a valid version string."
