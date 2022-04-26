# Copyright (c) .NET Foundation. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
# URL: https://github.com/NuGet/NuGet.Client
# Ported to Python from the C# NuGet test suite and significantly modified

import unittest

import pytest


class VersionRangeFloatParsingTests(unittest.TestCase):
    def test_VersionRangeFloatParsing_Prerelease(self):

        range = VersionRange("1.0.0-*")

        assert range.MinVersion.IsPrerelease

    @pytest.mark.parametrize(
        [],
        [
            ("1.0.0-*", "1.0.0-0"),
            ("1.0.0-0*", "1.0.0-0"),
            ("1.0.0--*", "1.0.0--"),
            ("1.0.0-a-*", "1.0.0-a-"),
            ("1.0.0-a.*", "1.0.0-a.0"),
            ("1.*-*", "1.0.0-0"),
            ("1.0.*-0*", "1.0.0-0"),
            ("1.0.*--*", "1.0.0--"),
            ("1.0.*-a-*", "1.0.0-a-"),
            ("1.0.*-a.*", "1.0.0-a.0"),
        ],
    )
    def test_VersionRangeFloatParsing_PrereleaseWithNumericOnlyLabelVerifyMinVersion(
        self, rangeString, expected
    ):

        range = VersionRange(rangeString)

        assert range.MinVersion.to_string() == expected

    @pytest.mark.parametrize(
        [],
        [
            ("1.0.0-0"),
            ("1.0.0-100"),
            ("1.0.0-0.0.0.0"),
            ("1.0.0-0+0-0"),
        ],
    )
    def test_VersionRangeFloatParsing_PrereleaseWithNumericOnlyLabelVerifySatisfies(self, version):

        range = VersionRange("1.0.0-*")

        assert range.Satisfies(NuGetVersion(version))

    @pytest.mark.parametrize(
        [],
        [
            ("1.0.0-a*", "1.0.0-a.0"),
            ("1.0.0-a*", "1.0.0-a-0"),
            ("1.0.0-a*", "1.0.0-a"),
            ("1.0.*-a*", "1.0.0-a"),
            ("1.*-a*", "1.0.0-a"),
            ("*-a*", "1.0.0-a"),
        ],
    )
    def test_VersionRangeFloatParsing_VerifySatisfiesForFloatingRange(self, rangeString, version):

        range = VersionRange(rangeString)

        assert range.Satisfies(NuGetVersion(version))

    @pytest.mark.parametrize(
        [],
        [
            ("1.0.0-*", "0", ""),
            ("1.0.0-a*", "a", "a"),
            ("1.0.0-a-*", "a-", "a-"),
            ("1.0.0-a.*", "a.0", "a."),
            ("1.0.0-0*", "0", "0"),
            ("1.0.*-0*", "0", "0"),
            ("1.*-0*", "0", "0"),
            ("*-0*", "0", "0"),
            ("1.0.*-*", "0", ""),
            ("1.*-*", "0", ""),
            ("*-*", "0", ""),
            ("1.0.*-a*", "a", "a"),
            ("1.*-a*", "a", "a"),
            ("*-a*", "a", "a"),
            ("1.0.*-a-*", "a-", "a-"),
            ("1.*-a-*", "a-", "a-"),
            ("*-a-*", "a-", "a-"),
            ("1.0.*-a.*", "a.0", "a."),
            ("1.*-a.*", "a.0", "a."),
            ("*-a.*", "a.0", "a."),
        ],
    )
    def test_VersionRangeFloatParsing_VerifyReleaseLabels(
        self, rangeString, versionLabel, originalLabel
    ):

        range = VersionRange(rangeString)

        assert range.Float.MinVersion.Release == versionLabel
        assert range.Float.OriginalReleasePrefix == originalLabel

    @pytest.mark.parametrize(
        [],
        [
            ("1.0.0"),
            ("[1.0.0]"),
            ("(0.0.0, )"),
            ("[1.0.0, )"),
            ("[1.0.0, 2.0.0)"),
        ],
    )
    def test_VersionRangeFloatParsing_NoFloat(self, rangeString):

        range = VersionRange(rangeString)

        versions = [NuGetVersion("1.0.0"), NuGetVersion("1.1.0")]

        assert range.FindBestMatch(versions).to_string() == "1.0.0"

    def test_VersionRangeFloatParsing_FloatPrerelease(self):

        range = VersionRange("1.0.0-*")

        versions = [NuGetVersion("1.0.0-alpha"), NuGetVersion("1.0.0-beta")]
        assert range.FindBestMatch(versions).to_string() == "1.0.0-beta"

    def test_VersionRangeFloatParsing_FloatPrereleaseMatchVersion(self):

        range = VersionRange("1.0.0-*")

        versions = [
            NuGetVersion("1.0.0-beta"),
            NuGetVersion("1.0.1-omega"),
        ]

        assert range.FindBestMatch(versions).to_string() == "1.0.0-beta"

    def test_VersionRangeFloatParsing_FloatPrereleasePrefix(self):

        range = VersionRange("1.0.0-beta.*")

        versions = [
            NuGetVersion("1.0.0-beta.1"),
            NuGetVersion("1.0.0-beta.2"),
            NuGetVersion("1.0.0-omega.3"),
        ]
        assert range.FindBestMatch(versions).to_string() == "1.0.0-beta.2"

    def test_VersionRangeFloatParsing_FloatPrereleasePrefixSemVerLabelMix(self):

        range = VersionRange("1.0.0-beta.*")

        versions = [
            NuGetVersion("1.0.0-beta.1"),
            NuGetVersion("1.0.0-beta.2"),
            NuGetVersion("1.0.0-beta.a"),
        ]

        assert range.FindBestMatch(versions).to_string() == "1.0.0-beta.a"

    @pytest.mark.parametrize(
        [],
        [
            ("[]"),
            ("[*]"),
            ("[1.0.0, 1.1.*)"),
            ("[1.0.0, 2.0.*)"),
            ("(, 2.*.*)"),
            ("<1.0.*"),
            ("<=1.0.*"),
            ("1.0.0<"),
            ("1.0.0~"),
            ("~1.*.*"),
            ("~*"),
            ("~"),
            ("^"),
            ("^*"),
            (">=*"),
            ("1.*.0"),
            ("1.*.0-beta-*"),
            ("1.*.0-beta"),
            ("1.0.0.0.*"),
            ("=1.0.*"),
            ("1.0.0+*"),
            ("1.0.**"),
            ("1.0.*-*bla"),
            ("1.0.*-*bla+*"),
            ("**"),
            ("1.0.0-preview.*+blabla"),
            ("1.0.*--"),
            ("1.0.*-alpha*+"),
            ("1.0.*-"),
        ],
    )
    def test_VersionRangeFloatParsing_Invalid(self, rangeString):

        range = None
        assert not VersionRange(rangeString, range)

    @pytest.mark.parametrize(
        [],
        [
            ("*"),
            ("1.*"),
            ("1.0.*"),
            ("1.0.0.*"),
            ("1.0.0.0-beta"),
            ("1.0.0.0-beta*"),
            ("1.0.0"),
            ("1.0"),
            ("[1.0.*, )"),
            ("[1.0.0-beta.*, 2.0.0)"),
            ("1.0.0-beta.*"),
            ("1.0.0-beta-*"),
            ("1.0.*-bla*"),
            ("1.0.*-*"),
            ("1.0.*-preview.1.*"),
            ("1.0.*-preview.1*"),
            ("1.0.0--"),
            ("1.0.0-bla*"),
            ("1.0.*--*"),
            ("1.0.0--*"),
        ],
    )
    def test_VersionRangeFloatParsing_Valid(self, rangeString):

        range = None
        assert VersionRange(rangeString, range)

    @pytest.mark.parametrize(
        [],
        [
            ("1.0.0", "[1.0.0, )"),
            ("1.0.*", "[1.0.0, )"),
            ("[1.0.*, )", "[1.0.0, )"),
            ("[1.*, )", "[1.0.0, )"),
            ("[1.*, 2.0)", "[1.0.0, 2.0.0)"),
            ("*", "[0.0.0, )"),
        ],
    )
    def test_VersionRangeFloatParsing_LegacyEquivalent(self, rangeString, legacyString):

        range = None
        assert VersionRange(rangeString, range)

        assert range.ToLegacyString() == legacyString

    @pytest.mark.parametrize(
        [],
        [
            ("1.0.0-beta*"),
            ("1.0.0-beta.*"),
            ("1.0.0-beta-*"),
        ],
    )
    def test_VersionRangeFloatParsing_CorrectFloatRange(self, rangeString):

        range = None
        assert VersionRange(rangeString, range)

        assert range.Float.to_string() == rangeString

    @pytest.mark.parametrize(
        [],
        [
            ("1.0.0;2.0.0", "*", "2.0.0"),
            ("1.0.0;2.0.0", "0.*", "1.0.0"),
            ("1.0.0;2.0.0", "[*, )", "2.0.0"),
            ("1.0.0;2.0.0;3.0.0", "(1.0.*, )", "2.0.0"),
            ("1.0.0;2.0.0;3.0.0", "(1.0.*, 2.0.0)", None),
            ("1.1.0;1.2.0-rc.1;1.2.0-rc.2;2.0.0;3.0.0-beta.1", "*", "2.0.0"),
            ("1.1.0;1.2.0-rc.1;1.2.0-rc.2;2.0.0;3.0.0-beta.1", "1.*", "1.1.0"),
            ("1.1.0;1.2.0-rc.1;1.2.0-rc.2;2.0.0;3.0.0-beta.1", "1.2.0-*", "1.2.0-rc.2"),
            ("1.1.0;1.2.0-rc.1;1.2.0-rc.2;2.0.0;3.0.0-beta.1", "*-*", "3.0.0-beta.1"),
            ("1.1.0;1.2.0-rc.1;1.2.0-rc.2;2.0.0;3.0.0-beta.1", "1.*-*", "1.2.0-rc.2"),
            ("1.1.0;1.2.0-rc.1;1.2.0-rc.2;2.0.0;3.0.0-beta.1", "*-rc.*", "2.0.0"),
            ("1.1.0;1.2.0-rc.1;1.2.0-rc.2;1.2.0-rc1;2.0.0;3.0.0-beta.1", "1.*-rc*", "1.2.0-rc1"),
            ("1.1.0;1.2.0-rc.1;1.2.0-rc.2;1.2.0-rc1;1.10.0;2.0.0;3.0.0-beta.1", "1.1*-*", "1.10.0"),
        ],
    )
    def test_VersionRangeFloatParsing_FindsBestMatch(
        self, availableVersions, declaredRange, expectedVersion
    ):

        range = VersionRange(declaredRange)

        versions = []
        for version in availableVersions.Split(";"):

            versions.append(NuGetVersion(version))

        assert range.FindBestMatch(versions).to_string() == expectedVersion
