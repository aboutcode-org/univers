# Copyright (c) .NET Foundation. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
# URL: https://github.com/NuGet/NuGet.Client
# Ported to Python from the C# NuGet test suite and significantly modified

import unittest

import pytest


class FloatingRangeTests:
    def test_FloatRange_OutsideOfRange(self):

        range = VersionRange("[1.0.*, 2.0.0)")

        versions = [
            NuGetVersion("0.1.0"),
            NuGetVersion("1.0.0-alpha.2"),
            NuGetVersion("2.0.0"),
            NuGetVersion("2.2.0"),
            NuGetVersion("3.0.0"),
        ]

        assert not range.FindBestMatch(versions)

    def test_FloatRange_OutsideOfRangeLower(self):

        range = VersionRange("[1.0.*, 2.0.0)")

        versions = [NuGetVersion("0.1.0"), NuGetVersion("0.2.0"), NuGetVersion("1.0.0-alpha.2")]

        assert not range.FindBestMatch(versions)

    def test_FloatRange_OutsideOfRangeHigher(self):

        range = VersionRange("[1.0.*, 2.0.0)")

        versions = [
            NuGetVersion("2.0.0"),
            NuGetVersion("2.0.0-alpha.2"),
            NuGetVersion("3.1.0"),
        ]

        assert not range.FindBestMatch(versions)

    def test_FloatRange_OutsideOfRangeOpen(self):

        range = VersionRange("[1.0.*, )")

        versions = [NuGetVersion("0.1.0"), NuGetVersion("0.2.0"), NuGetVersion("1.0.0-alpha.2")]

        assert not range.FindBestMatch(versions)

    def test_FloatRange_RangeOpen(self):

        range = VersionRange("[1.0.*, )")

        versions = [
            NuGetVersion("0.1.0"),
            NuGetVersion("0.2.0"),
            NuGetVersion("1.0.0-alpha.2"),
            NuGetVersion("101.0.0"),
        ]

        assert range.FindBestMatch(versions).to_string() == "101.0.0"

    def test_FloatRange_ParseBasic(self):

        range = FloatRange("1.0.0")

        assert range.MinVersion == range.MinVersion
        assert NuGetVersionFloatBehavior == range.FloatBehavior

    def test_FloatRange_ParsePrerelease(self):

        range = FloatRange("1.0.0-*")

        assert range.Satisfies(NuGetVersion("1.0.0-alpha"))
        assert range.Satisfies(NuGetVersion("1.0.0-beta"))
        assert range.Satisfies(NuGetVersion("1.0.0"))

        assert not range.Satisfies(NuGetVersion("1.0.1-alpha"))
        assert not range.Satisfies(NuGetVersion("1.0.1"))

    def test_FloatingRange_FloatNone(self):

        range = FloatRange("1.0.0")

        assert range.MinVersion.to_string() == "1.0.0"
        assert range.FloatBehavior == NuGetVersionFloatBehavior

    def test_FloatingRange_FloatPre(self):

        range = FloatRange("1.0.0-*")

        assert range.MinVersion.to_string() == "1.0.0-0"
        assert range.FloatBehavior == NuGetVersionFloatBehavior.Prerelease

    def test_FloatingRange_FloatPrePrefix(self):

        range = FloatRange("1.0.0-alpha-*")

        assert range.MinVersion.to_string() == "1.0.0-alpha-"
        assert range.FloatBehavior == NuGetVersionFloatBehavior.Prerelease

    def test_FloatingRange_FloatRev(self):

        range = FloatRange("1.0.0.*")

        assert range.MinVersion.to_string() == "1.0.0"
        assert range.FloatBehavior == NuGetVersionFloatBehavior.Revision

    def test_FloatingRange_FloatPatch(self):

        range = FloatRange("1.0.*")

        assert range.MinVersion.to_string() == "1.0.0"
        assert range.FloatBehavior == NuGetVersionFloatBehavior.Patch

    def test_FloatingRange_FloatMinor(self):

        range = FloatRange("1.*")

        assert range.MinVersion.to_string() == "1.0.0"
        assert range.FloatBehavior == NuGetVersionFloatBehavior.Minor

    def test_FloatingRange_FloatMajor(self):

        range = FloatRange("*")

        assert range.MinVersion.to_string() == "0.0.0"
        assert range.FloatBehavior == NuGetVersionFloatBehavior.Major

    def test_FloatingRange_FloatNoneBest(self):

        range = VersionRange("1.0.0")

        versions = [
            NuGetVersion("1.0.0"),
            NuGetVersion("1.0.1"),
            NuGetVersion("2.0.0"),
        ]

        assert range.FindBestMatch(versions).to_string() == "1.0.0"

    def test_FloatingRange_FloatMinorBest(self):

        range = VersionRange("1.*")

        versions = [
            NuGetVersion("0.1.0"),
            NuGetVersion("1.0.0"),
            NuGetVersion("1.2.0"),
            NuGetVersion("2.0.0"),
        ]

        assert range.FindBestMatch(versions).to_string() == "1.2.0"

    def test_FloatingRange_FloatMinorPrefixNotFoundBest(self):

        range = VersionRange("1.*")

        versions = [
            NuGetVersion("0.1.0"),
            NuGetVersion("2.0.0"),
            NuGetVersion("2.5.0"),
            NuGetVersion("3.3.0"),
        ]

        # take the nearest when the prefix is not matched
        assert range.FindBestMatch(versions).to_string() == "2.0.0"

    def test_FloatingRange_FloatAllBest(self):

        range = VersionRange("*")

        versions = [
            NuGetVersion("0.1.0"),
            NuGetVersion("2.0.0"),
            NuGetVersion("2.5.0"),
            NuGetVersion("3.3.0"),
        ]

        assert range.FindBestMatch(versions).to_string() == "3.3.0"

    def test_FloatingRange_FloatPrereleaseBest(self):

        range = VersionRange("1.0.0-*")

        versions = [
            NuGetVersion("0.1.0-alpha"),
            NuGetVersion("1.0.0-alpha01"),
            NuGetVersion("1.0.0-alpha02"),
            NuGetVersion("2.0.0-beta"),
            NuGetVersion("2.0.1"),
        ]

        assert range.FindBestMatch(versions).to_string() == "1.0.0-alpha02"

    def test_FloatingRange_FloatPrereleaseNotFoundBest(self):

        range = VersionRange("1.0.0-*")

        versions = [
            NuGetVersion("0.1.0-alpha"),
            NuGetVersion("1.0.1-alpha01"),
            NuGetVersion("1.0.1-alpha02"),
            NuGetVersion("2.0.0-beta"),
            NuGetVersion("2.0.1"),
        ]

        assert range.FindBestMatch(versions).to_string() == "1.0.1-alpha01"

    def test_FloatingRange_FloatPrereleasePartialBest(self):

        range = VersionRange("1.0.0-alpha*")

        versions = [
            NuGetVersion("0.1.0-alpha"),
            NuGetVersion("1.0.0-alpha01"),
            NuGetVersion("1.0.0-alpha02"),
            NuGetVersion("2.0.0-beta"),
            NuGetVersion("2.0.1"),
        ]

        assert range.FindBestMatch(versions).to_string() == "1.0.0-alpha02"

    def test_FloatingRange_to_stringPre(self):

        range = VersionRange("1.0.0-*")

        assert range.to_string() == "[1.0.0-*, )"

    def test_FloatingRange_to_stringPrePrefix(self):

        range = VersionRange("1.0.0-alpha.*")

        assert range.to_string() == "[1.0.0-alpha.*, )"

    def test_FloatingRange_to_stringRev(self):

        range = VersionRange("1.0.0.*")

        assert range.to_string() == "[1.0.0.*, )"

    def test_FloatingRange_to_stringPatch(self):

        range = VersionRange("1.0.*")

        assert range.to_string() == "[1.0.*, )"

    def test_FloatingRange_to_stringMinor(self):

        range = VersionRange("1.*")

        assert range.to_string() == "[1.*, )"

    @pytest.mark.parametrize(
        ["floatVersionString"],
        [
            ("1.0.0+*"),
            ("1.0.**"),
            ("1.*.0"),
            ("1.0.*-*bla"),
            ("1.0.*-*bla+*"),
            ("**"),
            ("1.0.0-preview.*+blabla"),
            ("1.0.*--"),
            ("1.0.*-alpha*+"),
            ("1.0.*-"),
            (None),
            (""),
        ],
    )
    def test_FloatingRange_TryParse_Invalid(self, floatVersionString):

        valid = FloatRange.from_string(floatVersionString)

        assert not valid
        assert not range

    @pytest.mark.parametrize(
        ["floatVersionString"],
        [
            ("1.0.0-preview.*"),
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
    def test_FloatingRange_Parse_Valid(self, floatVersionString):

        range = FloatRange(floatVersionString)
        assert range

    @pytest.mark.parametrize(
        ["floatVersionString"],
        [
            ("1.0.0+*"),
            ("1.0.**"),
            ("1.*.0"),
            ("1.0.*-*bla"),
            ("1.0.*-*bla+*"),
            ("**"),
            ("1.0.0-preview.*+blabla"),
            ("1.0.*--"),
            ("1.0.*-alpha*+"),
            ("1.0.*-"),
            (None),
            (""),
        ],
    )
    def test_FloatingRange_Parse_Invalid(self, floatVersionString):

        range = FloatRange(floatVersionString)

        assert not range

    @pytest.mark.parametrize(
        ["floatVersionString"],
        [
            ("1.0.0-preview.*"),
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
    def test_FloatingRange_TryParse_Valid(self, floatVersionString):

        valid = FloatRange.from_string(floatVersionString)

        assert valid
        assert range

    def test_FloatingRange_FloatPrereleaseRev(self):

        range = FloatRange("1.0.0.*-*")

        assert range.MinVersion.to_string() == "1.0.0-0"
        assert range.FloatBehavior == NuGetVersionFloatBehavior.PrereleaseRevision

    def test_FloatingRange_FloatPrereleasePatch(self):

        range = FloatRange("1.0.*-*")

        assert range.MinVersion.to_string() == "1.0.0-0"
        assert range.FloatBehavior == NuGetVersionFloatBehavior.PrereleasePatch

    def test_FloatingRange_FloatPrereleaseMinor(self):

        range = FloatRange("1.*-*")

        assert range.MinVersion.to_string() == "1.0.0-0"
        assert range.FloatBehavior == NuGetVersionFloatBehavior.PrereleaseMinor

    def test_FloatingRange_FloatMajorPrerelease(self):

        range = FloatRange("*-rc.*")

        assert range.MinVersion.to_string() == "0.0.0-rc.0"
        assert range.FloatBehavior == NuGetVersionFloatBehavior.PrereleaseMajor

    def test_FloatingRange_FloatAbsoluteLatest(self):

        range = FloatRange("*-*")

        assert range.MinVersion.to_string() == "0.0.0-0"
        assert range.FloatBehavior == NuGetVersionFloatBehavior.AbsoluteLatest

    @pytest.mark.parametrize(
        ["versionRange", "normalizedMinVersion"],
        [
            ("*", "0.0.0"),
            ("*-*", "0.0.0-0"),
            ("1.*", "1.0.0"),
            ("1.1.*", "1.1.0"),
            ("1.1.*-*", "1.1.0-0"),
            ("1.1.1-*", "1.1.1-0"),
            ("1.1.1-beta*", "1.1.1-beta"),
            ("1.1.1-1*", "1.1.1-1"),
            ("1.1.*-beta*", "1.1.0-beta"),
            ("1.1.*-1*", "1.1.0-1"),
            ("1.0.0-beta.1*", "1.0.0-beta.1"),
            ("1.0.*-beta.1*", "1.0.0-beta.1"),
            ("1.0.0-b-*", "1.0.0-b-"),
            ("1.0.*-b-*", "1.0.0-b-"),
            ("1.1.0-beta.*", "1.1.0-beta.0"),
            ("1.1.*-beta.*", "1.1.0-beta.0"),
            ("*-beta.*", "0.0.0-beta.0"),
        ],
    )
    def test_FloatRange_ParsesCorrectMinVersion(self, versionRange, normalizedMinVersion):
        range = FloatRange(versionRange)
        assert range.MinVersion.to_string() == normalizedMinVersion
