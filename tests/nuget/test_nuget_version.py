# Copyright (c) .NET Foundation. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
# URL: https:#github/github.com/NuGet/NuGet.Client
# Ported to Python from the C# NuGet test suite an significantly modified

import pytest

from univers import nuget


@pytest.mark.parametrize(
    ("version_string", "expected"),
    [
        ("1.0.0", "1.0.0"),
        ("0.0.1", "0.0.1"),
        ("1.2.3", "1.2.3"),
        ("1.2.3-alpha", "1.2.3-alpha"),
        ("1.2.3-X.y.3+Meta-2", "1.2.3-x.y.3+Meta-2"),
        ("1.2.3-X.yZ.3.234.243.3242342+METADATA", "1.2.3-x.yz.3.234.243.3242342+METADATA"),
        ("1.2.3-X.y3+0", "1.2.3-x.y3+0"),
        ("1.2.3-X+0", "1.2.3-x+0"),
        ("1.2.3+0", "1.2.3+0"),
        ("1.2.3-0", "1.2.3-0"),
    ],
)
def test_NuGetVersionParseStrict_and_normalize_case(version_string, expected):
    semver = nuget.Version.from_string(version_string)
    assert str(semver) == expected


@pytest.mark.parametrize(
    ("version", "base_version", "prerelease", "build"),
    [
        ("1.0.0", "1.0.0.0", "", ""),
        ("2.3-alpha", "2.3.0.0", "alpha", ""),
        ("3.4.0.3-RC-3", "3.4.0.3", "RC-3", ""),
        ("1.0.0-beta.x.y.5.79.0+aa", "1.0.0.0", "beta.x.y.5.79.0", "aa"),
        ("1.0.0-beta.x.y.5.79.0+AA", "1.0.0.0", "beta.x.y.5.79.0", "AA"),
    ],
)
def test_StringConstructorParsesValuesCorrectly(version, base_version, prerelease, build):
    vers = nuget.Version.from_string(version)
    assert vers.base_version == base_version
    assert vers.prerelease == prerelease.lower()
    assert vers.build == build


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
        ("NotAVersion"),
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
def test_ParseThrowsIfStringIsNotAValidsemver(version_string):
    with pytest.raises(Exception):
        nuget.Version.from_string(version_string)


@pytest.mark.parametrize(
    ("version_string", "expected_string"),
    [
        ("1.022", "1.22.0.0"),
        ("23.2.3", "23.2.3.0"),
        ("1.3.42.10133", "1.3.42.10133"),
    ],
)
def test_ParseReadsLegacyStyleVersionNumbers(version_string, expected_string):
    actual = nuget.Version.from_string(version_string)
    assert actual.base_version == expected_string


@pytest.mark.parametrize(
    ("version", "base_version", "prerelease"),
    [
        ("1.022-Beta", "1.22.0.0", "Beta"),
        ("23.2.3-Alpha", "23.2.3.0", "Alpha"),
        ("1.3.42.10133-PreRelease", "1.3.42.10133", "PreRelease"),
        ("1.3.42.200930-RC-2", "1.3.42.200930", "RC-2"),
    ],
)
def test_ParseReadssemverAndHybridsemverVersionNumbers(
    version,
    base_version,
    prerelease,
):
    vers = nuget.Version.from_string(version)
    assert vers.base_version == base_version
    assert vers.prerelease == prerelease.lower()


@pytest.mark.parametrize(
    ("version", "base_version", "prerelease"),
    [
        ("  1.022-Beta", "1.22.0.0", "Beta"),
        ("23.2.3-Alpha  ", "23.2.3.0", "Alpha"),
        ("    1.3.42.10133-PreRelease  ", "1.3.42.10133", "PreRelease"),
    ],
)
def test_ParseIgnoresLeadingAndTrailingWhitespace(
    version,
    base_version,
    prerelease,
):
    vers = nuget.Version.from_string(version)
    assert vers.base_version == base_version
    assert vers.prerelease == prerelease.lower()


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
def test_semverLessThanAndGreaterThanOperatorsWorks(version_a, version_b):
    itemA = nuget.Version.from_string(version_a)
    itemB = nuget.Version.from_string(version_b)

    assert itemA < itemB
    assert itemA <= itemB
    assert itemB > itemA
    assert itemB >= itemA
    assert itemA != itemB


def test_EqualsIsTrueForEmptyRevision():
    assert nuget.Version.from_string("1.0.0.0") == nuget.Version.from_string("1.0.0")
    assert nuget.Version.from_string("1.0.0") == nuget.Version.from_string("1.0.0.0")


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
def test_semverEqualsOperatorWorks(version_a, version_b):
    itemA = nuget.Version.from_string(version_a)
    itemB = nuget.Version.from_string(version_b)

    assert itemA == itemB
    assert itemA <= itemB
    assert itemB == itemA
    assert itemB >= itemA


@pytest.mark.parametrize(
    ("version", "expected"),
    [
        ("1.0", "1.0.0"),
        ("1.0.0", "1.0.0"),
        ("1.0.0.0", "1.0.0"),
        ("1.0-alpha", "1.0.0-alpha"),
        ("1.0.0-b", "1.0.0-b"),
        ("3.0.1.2", "3.0.1.2"),
        ("2.1.4.3-pre-1", "2.1.4.3-pre-1"),
    ],
)
def test_to_stringReturnsOriginalValueForNonsemver2(version, expected):
    vers = nuget.Version.from_string(version)
    assert vers.to_string() == expected


@pytest.mark.parametrize(
    ("version", "base_with_prerelease", "full"),
    [
        ("1.0+A", "1.0.0", "1.0.0+A"),
        ("1.0-1.1", "1.0.0-1.1", "1.0.0-1.1"),
        ("1.0-1.1+B.B", "1.0.0-1.1", "1.0.0-1.1+B.B"),
        ("1.0.0009.01-1.1+A", "1.0.9.1-1.1", "1.0.9.1-1.1+A"),
    ],
)
def test_to_stringReturnsNormalizedForsemver2(version, base_with_prerelease, full):
    version = nuget.Version.from_string(version)
    assert (
        version.to_string(with_empty_revision=False, include_prerelease=True, include_build=False)
        == base_with_prerelease
    )
    assert (
        version.to_string(with_empty_revision=False, include_prerelease=True, include_build=True)
        == full
    )


@pytest.mark.parametrize(
    ("base_version", "prerelease", "version"),
    [
        ("1.0", "", "1.0"),
        ("1.0.3.120", "", "1.0.3.120"),
        ("1.0.3.120", "alpha", "1.0.3.120-alpha"),
        ("1.0.3.120", "rc-2", "1.0.3.120-rc-2"),
    ],
)
def test_to_stringConstructedFromversion_andspecial_versionConstructor(
    base_version, prerelease, version
):
    version = nuget.Version.from_string(version)
    assert nuget.Version.from_string(version.base_version) == nuget.Version.from_string(
        base_version
    )
    assert version.prerelease == prerelease


@pytest.mark.parametrize(
    ("version", "expected"),
    [
        ("01.42.0", "1.42.0"),
        ("01.0", "1.0.0"),
        ("01.42.0-alpha", "1.42.0-alpha"),
        ("01.42.0-alpha.1", "1.42.0-alpha.1"),
        ("01.42.0-alpha+metadata", "1.42.0-alpha+metadata"),
        ("01.42.0+metadata", "1.42.0+metadata"),
    ],
)
def test_NuGetVersionKeepsoriginal_version_string(version, expected):
    nuver = nuget.Version.from_string(version)
    assert nuver._original_version == version
    assert str(nuver) == expected


@pytest.mark.parametrize(
    ("version", "expected"),
    [
        ("1.0", "1.0.0"),
        ("1.0.3.120", "1.0.3.120"),
        ("1.0.3.120-alpha", "1.0.3.120-alpha"),
        ("1.0.3.120-rc-2", "1.0.3.120-rc-2"),
    ],
)
def test_to_stringFromStringFormat(version, expected):
    version = nuget.Version.from_string(version)
    assert version.to_string() == expected


def test_TryParseStrictParsesStrictVersion():
    version_string = "1.3.2-CTP-2-Refresh-Alpha"
    version = nuget.Version.from_string(version_string)
    assert version
    no_prerel = nuget.Version.from_string("1.3.2.0")
    assert version.base_version == no_prerel.to_string(with_empty_revision=True)
    assert version.prerelease == "CTP-2-Refresh-Alpha".lower()


def test_TryParseReturnsFalseWhenUnableToParseString():
    assert not nuget.Version.from_string("")


@pytest.mark.parametrize(
    ("version", "expected"),
    [
        ("1", "1.0.0.0"),
        ("1.0", "1.0.0.0"),
        ("v1.0.0", "1.0.0.0"),
        ("1.0.3.120", "1.0.3.120"),
    ],
)
def test_Can_Parse_various_String(version, expected):
    version = nuget.Version.from_string(version)
    assert version.base_version == expected
