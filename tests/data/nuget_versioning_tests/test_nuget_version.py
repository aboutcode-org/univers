# Copyright (c) .NET Foundation. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
# URL: https:#github/github.com/NuGet/NuGet.Client
# Ported to Python from the C# NuGet test suite an significantly modified

import unittest

import pytest

from univers.nuget import NuGetVersion

SemanticVersion = NuGetVersion


class Version:
    pass


class NuGetVersioningTest(unittest.TestCase):
    @pytest.mark.parametrize(
        "version_string",
        [
            "1.0.0",
            "0.0.1",
            "1.2.3",
            "1.2.3-alpha",
            "1.2.3-X.y.3+Meta-2",
            "1.2.3-X.yZ.3.234.243.3242342+METADATA",
            "1.2.3-X.y3+0",
            "1.2.3-X+0",
            "1.2.3+0",
            "1.2.3-0",
        ],
    )
    def test_NuGetVersionParseStrict(self, version_string):
        semver = NuGetVersion.from_string(version_string, semver=True)
        assert version_string == str(semver)

    @pytest.mark.parametrize(
        ("version", "version_value_string", "special_value", "metadata"),
        [
            ("1.0.0", "1.0.0.0", "", ""),
            ("2.3-alpha", "2.3.0.0", "alpha", ""),
            ("3.4.0.3-RC-3", "3.4.0.3", "RC-3", ""),
            ("1.0.0-beta.x.y.5.79.0+aa", "1.0.0.0", "beta.x.y.5.79.0", "aa"),
            ("1.0.0-beta.x.y.5.79.0+AA", "1.0.0.0", "beta.x.y.5.79.0", "AA"),
        ],
    )
    def test_StringConstructorParsesValuesCorrectly(
        self, version, version_value_string, special_value, metadata
    ):
        versionValue = Version(version_value_string)
        semanticVersion = NuGetVersion(version)
        assert versionValue == semanticVersion.Version
        assert special_value == semanticVersion.Release
        assert metadata == semanticVersion.Metadata

    @pytest.mark.parametrize(
        "version_string",
        [
            ("1beta"),
            ("1.2Av^c"),
            ("1.2.."),
            ("1.2.3.4.5"),
            ("1.2.3.Beta"),
            ("1.2.3.4This version is full of awesomeness!!"),
            ("So.is.this"),
            ("1.34.2Alpha"),
            ("1.34.2Release Candidate"),
            ("1.4.7-"),
            ("1.4.7-*"),
            ("1.4.7+*"),
            ("1.4.7-AA.01^"),
            ("1.4.7-AA.0A^"),
            ("1.4.7-A^A"),
            ("1.4.7+AA.01^"),
        ],
    )
    def test_ParseThrowsIfStringIsNotAValidsemver(self, version_string):
        with pytest.raises(Exception):
            NuGetVersion.from_string(version_string, semver=True)

    @pytest.mark.parametrize(
        ("version_string", "expected_string"),
        [
            ("1.022", "1.22.0.0"),
            ("23.2.3", "23.2.3.0"),
            ("1.3.42.10133", "1.3.42.10133"),
        ],
    )
    def test_ParseReadsLegacyStyleVersionNumbers(self, version_string, expected_string):
        expected = NuGetVersion(Version(expected_string), "")

        actual = NuGetVersion(version_string)

        assert expected.Version == actual.Version
        assert expected.Release == actual.Release

    @pytest.mark.parametrize(
        ("version_string", "expected_string", "release_string"),
        [
            ("1.022-Beta", "1.22.0.0", "Beta"),
            ("23.2.3-Alpha", "23.2.3.0", "Alpha"),
            ("1.3.42.10133-PreRelease", "1.3.42.10133", "PreRelease"),
            ("1.3.42.200930-RC-2", "1.3.42.200930", "RC-2"),
        ],
    )
    def test_ParseReadssemverAndHybridsemverVersionNumbers(
        self, version_string, expected_string, release_string
    ):
        expected = NuGetVersion(Version(expected_string), release_string)

        actual = NuGetVersion(version_string)

        assert expected.Version == actual.Version
        assert expected.Release == actual.Release

    @pytest.mark.parametrize(
        ("version_string", "expected_string", "release_string"),
        [
            ("  1.022-Beta", "1.22.0.0", "Beta"),
            ("23.2.3-Alpha  ", "23.2.3.0", "Alpha"),
            ("    1.3.42.10133-PreRelease  ", "1.3.42.10133", "PreRelease"),
        ],
    )
    def test_ParseIgnoresLeadingAndTrailingWhitespace(
        self, version_string, expected_string, release_string
    ):
        expected = NuGetVersion(Version(expected_string), release_string)

        actual = NuGetVersion(version_string)

        assert expected.Version == actual.Version
        assert expected.Release == actual.Release

    @pytest.mark.parametrize(
        (
            "version_a",
            "version_b",
        ),
        [
            ("1.0", "1.0.1"),
            ("1.23", "1.231"),
            ("1.4.5.6", "1.45.6"),
            ("1.4.5.6", "1.4.5.60"),
            ("1.01", "1.10"),
            ("1.01-alpha", "1.10-beta"),
            ("1.01.0-RC-1", "1.10.0-rc-2"),
            ("1.01-RC-1", "1.01"),
            ("1.01", "1.2-preview"),
        ],
    )
    def test_semverLessThanAndGreaterThanOperatorsWorks(self, version_a, version_b):
        itemA = NuGetVersion(version_a)
        itemB = NuGetVersion(version_b)

        assert itemA < itemB
        assert itemA <= itemB
        assert itemB > itemA
        assert itemB >= itemA
        assert itemA != itemB

    def test_EqualsIsTrueForEmptyRevision(
        self,
    ):
        assert NuGetVersion("1.0.0.0").Equals(SemanticVersion("1.0.0"))
        assert SemanticVersion("1.0.0").Equals(NuGetVersion("1.0.0.0"))

    @pytest.mark.parametrize(
        (
            "version_a",
            "version_b",
        ),
        [
            ("1.0", "1.0.0.0"),
            ("1.23.01", "1.23.1"),
            ("1.45.6", "1.45.6.0"),
            ("1.45.6-Alpha", "1.45.6-Alpha"),
            ("1.6.2-BeTa", "1.6.02-beta"),
            ("22.3.07     ", "22.3.07"),
            ("1.0", "1.0.0.0+beta"),
            ("1.0.0.0+beta.2", "1.0.0.0+beta.1"),
        ],
    )
    def test_semverEqualsOperatorWorks(self, version_a, version_b):
        itemA = NuGetVersion(version_a)
        itemB = NuGetVersion(version_b)

        assert itemA == itemB
        assert itemA <= itemB
        assert itemB == itemA
        assert itemB >= itemA

    @pytest.mark.parametrize(
        "version",
        [
            ("1.0"),
            ("1.0.0"),
            ("1.0.0.0"),
            ("1.0-alpha"),
            ("1.0.0-b"),
            ("3.0.1.2"),
            ("2.1.4.3-pre-1"),
        ],
    )
    def test_to_stringReturnsOriginalValueForNonsemver2(self, version):
        semver = NuGetVersion(version)
        assert version == semver.to_string()

    @pytest.mark.parametrize(
        ("version", "expected", "full"),
        [
            ("1.0+A", "1.0.0", "1.0.0+A"),
            ("1.0-1.1", "1.0.0-1.1", "1.0.0-1.1"),
            ("1.0-1.1+B.B", "1.0.0-1.1", "1.0.0-1.1+B.B"),
            ("1.0.0009.01-1.1+A", "1.0.9.1-1.1", "1.0.9.1-1.1+A"),
        ],
    )
    def test_to_stringReturnsNormalizedForsemver2(self, version, expected, full):
        semver = NuGetVersion(version)
        assert expected == semver.to_string()
        assert full == semver.to_string()

    @pytest.mark.parametrize(
        ("version_string", "special_version", "expected"),
        [
            ("1.0", None, "1.0"),
            ("1.0.3.120", "", "1.0.3.120"),
            ("1.0.3.120", "alpha", "1.0.3.120-alpha"),
            ("1.0.3.120", "rc-2", "1.0.3.120-rc-2"),
        ],
    )
    def test_to_stringConstructedFromversion_andspecial_versionConstructor(
        self, version_string, special_version, expected
    ):
        version = Version(version_string)
        semver = NuGetVersion(version, special_version)
        assert expected == semver.to_string()

    @pytest.mark.parametrize(
        "version",
        [
            ("01.42.0"),
            ("01.0"),
            ("01.42.0-alpha"),
            ("01.42.0-alpha.1"),
            ("01.42.0-alpha+metadata"),
            ("01.42.0+metadata"),
        ],
    )
    def test_NuGetVersionKeepsoriginal_version_string(self, version):
        nuver = NuGetVersion(version)
        assert str(nuver) == version

    @pytest.mark.parametrize(
        ("version_string", "expected"),
        [
            ("1.0", "1.0"),
            ("1.0.3.120", "1.0.3.120"),
            ("1.0.3.120-alpha", "1.0.3.120-alpha"),
            ("1.0.3.120-rc-2", "1.0.3.120-rc-2"),
        ],
    )
    def test_to_stringFromStringFormat(self, version_string, expected):
        semver = NuGetVersion.from_string(version_string, semver=True)
        assert semver.to_string() == expected

    def test_TryParseStrictParsesStrictVersion(
        self,
    ):
        version_string = "1.3.2-CTP-2-Refresh-Alpha"
        version = NuGetVersion.from_string(version_string, semver=True)
        assert version
        assert Version("1.3.2.0") == version.Version
        assert "CTP-2-Refresh-Alpha" == version.Release

    @pytest.mark.parametrize(
        "version_string",
        [
            (""),
            ("NotAVersion"),
            ("1"),
            ("1.0"),
            ("v1.0.0"),
            ("1.0.3.120"),
        ],
    )
    def test_TryParseReturnsFalseWhenUnableToParseString(self, version_string):
        version = NuGetVersion.from_string(version_string, semver=True)
        assert not version
