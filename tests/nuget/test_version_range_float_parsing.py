# Copyright (c) .NET Foundation. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
# URL: https://github.com/NuGet/NuGet.Client
# Ported to Python from the C# NuGet test suite and significantly modified

import pytest

from univers import nuget
from univers.version_range import NugetVersionRange as VersionRange


def test_VersionRangeFloatParsing_Prerelease():
    vrange = VersionRange("1.0.0-*")
    assert vrange.MinVersion.IsPrerelease


@pytest.mark.parametrize(
    "rangeString, expected",
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
    rangeString, expected
):
    vrange = VersionRange(rangeString)
    assert vrange.MinVersion.to_string() == expected


@pytest.mark.parametrize(
    "version",
    [
        ("1.0.0-0"),
        ("1.0.0-100"),
        ("1.0.0-0.0.0.0"),
        ("1.0.0-0+0-0"),
    ],
)
def test_VersionRangeFloatParsing_PrereleaseWithNumericOnlyLabelVerifySatisfies(version):
    vrange = VersionRange("1.0.0-*")
    assert vrange.Satisfies(nuget.Version(version))


@pytest.mark.parametrize(
    "rangeString, version",
    [
        ("1.0.0-a*", "1.0.0-a.0"),
        ("1.0.0-a*", "1.0.0-a-0"),
        ("1.0.0-a*", "1.0.0-a"),
        ("1.0.*-a*", "1.0.0-a"),
        ("1.*-a*", "1.0.0-a"),
        ("*-a*", "1.0.0-a"),
    ],
)
def test_VersionRangeFloatParsing_VerifySatisfiesForFloatingRange(rangeString, version):
    vrange = VersionRange(rangeString)
    assert vrange.Satisfies(nuget.Version(version))


@pytest.mark.parametrize(
    "rangeString, versionLabel, originalLabel",
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
    rangeString, versionLabel, originalLabel
):
    vrange = VersionRange(rangeString)
    assert vrange.Float.MinVersion.Release == versionLabel
    assert vrange.Float.OriginalReleasePrefix == originalLabel


@pytest.mark.parametrize(
    "rangeString",
    [
        ("1.0.0"),
        ("[1.0.0]"),
        ("(0.0.0, )"),
        ("[1.0.0, )"),
        ("[1.0.0, 2.0.0)"),
    ],
)
def test_VersionRangeFloatParsing_NoFloat(rangeString):
    vrange = VersionRange(rangeString)
    versions = [nuget.Version("1.0.0"), nuget.Version("1.1.0")]
    assert vrange.FindBestMatch(versions).to_string() == "1.0.0"


def test_VersionRangeFloatParsing_FloatPrerelease():
    vrange = VersionRange("1.0.0-*")
    versions = [nuget.Version("1.0.0-alpha"), nuget.Version("1.0.0-beta")]
    assert vrange.FindBestMatch(versions).to_string() == "1.0.0-beta"


def test_VersionRangeFloatParsing_FloatPrereleaseMatchVersion():
    vrange = VersionRange("1.0.0-*")
    versions = [
        nuget.Version("1.0.0-beta"),
        nuget.Version("1.0.1-omega"),
    ]
    assert vrange.FindBestMatch(versions).to_string() == "1.0.0-beta"


def test_VersionRangeFloatParsing_FloatPrereleasePrefix():
    vrange = VersionRange("1.0.0-beta.*")
    versions = [
        nuget.Version("1.0.0-beta.1"),
        nuget.Version("1.0.0-beta.2"),
        nuget.Version("1.0.0-omega.3"),
    ]
    assert vrange.FindBestMatch(versions).to_string() == "1.0.0-beta.2"


def test_VersionRangeFloatParsing_FloatPrereleasePrefixSemVerLabelMix():
    vrange = VersionRange("1.0.0-beta.*")
    versions = [
        nuget.Version("1.0.0-beta.1"),
        nuget.Version("1.0.0-beta.2"),
        nuget.Version("1.0.0-beta.a"),
    ]
    assert vrange.FindBestMatch(versions).to_string() == "1.0.0-beta.a"


@pytest.mark.parametrize(
    "rangeString",
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
def test_VersionRangeFloatParsing_Invalid(rangeString):
    vrange = None
    assert not VersionRange(rangeString, vrange)


@pytest.mark.parametrize(
    "rangeString",
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
def test_VersionRangeFloatParsing_Valid(rangeString):
    vrange = None
    assert VersionRange(rangeString, vrange)


@pytest.mark.parametrize(
    "rangeString, legacyString",
    [
        ("1.0.0", "[1.0.0, )"),
        ("1.0.*", "[1.0.0, )"),
        ("[1.0.*, )", "[1.0.0, )"),
        ("[1.*, )", "[1.0.0, )"),
        ("[1.*, 2.0)", "[1.0.0, 2.0.0)"),
        ("*", "[0.0.0, )"),
    ],
)
def test_VersionRangeFloatParsing_LegacyEquivalent(rangeString, legacyString):
    vrange = None
    assert VersionRange(rangeString, vrange)
    assert vrange.ToLegacyString() == legacyString


@pytest.mark.parametrize(
    "rangeString",
    [
        ("1.0.0-beta*"),
        ("1.0.0-beta.*"),
        ("1.0.0-beta-*"),
    ],
)
def test_VersionRangeFloatParsing_CorrectFloatRange(rangeString):
    vrange = None
    assert VersionRange(rangeString, vrange)
    assert vrange.Float.to_string() == rangeString


@pytest.mark.parametrize(
    "availableVersions, declaredRange, expectedVersion",
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
    availableVersions, declaredRange, expectedVersion
):
    vrange = VersionRange(declaredRange)
    versions = []
    for version in availableVersions.Split(";"):
        versions.append(nuget.Version(version))

    assert vrange.FindBestMatch(versions).to_string() == expectedVersion
