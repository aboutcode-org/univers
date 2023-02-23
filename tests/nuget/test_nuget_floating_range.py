# Copyright (c) .NET Foundation. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
# URL: https://github.com/NuGet/NuGet.Client
# Ported to Python from the C# NuGet test suite and significantly modified

import pytest

from univers.version_range import NugetVersionRange as VersionRange
from univers.versions import NugetVersion as NuGetVersion

"""
NuGet Float ranges are not yet supported in Univers.

See https://docs.microsoft.com/en-us/nuget/concepts/package-versioning#version-ranges

    "When using the PackageReference format, NuGet also supports using a floating 
    notation, *, for Major, Minor, Patch, and pre-release suffix parts of the
    number. Floating versions are not supported with the packages.config format.
    When a floating version is specified, the rule is to resolve to the highest
    existent version that matches the version description. Examples of floating
    versions and the resolutions are below."

For example:

<!-- Accepts any 6.x.y version.
     Will resolve to the highest acceptable stable version.-->
<PackageReference Include="ExamplePackage" Version="6.*" />
"""

pytestmark = pytest.mark.skipif(True, reason="NuGet Float ranges are not yet supported in Univers.")


def test_FloatRange_OutsideOfRange():
    vrange = VersionRange("[1.0.*, 2.0.0)")

    versions = [
        NuGetVersion("0.1.0"),
        NuGetVersion("1.0.0-alpha.2"),
        NuGetVersion("2.0.0"),
        NuGetVersion("2.2.0"),
        NuGetVersion("3.0.0"),
    ]

    assert not vrange.FindBestMatch(versions)


def test_FloatRange_OutsideOfRangeLower():
    vrange = VersionRange("[1.0.*, 2.0.0)")
    versions = [NuGetVersion("0.1.0"), NuGetVersion("0.2.0"), NuGetVersion("1.0.0-alpha.2")]
    assert not vrange.FindBestMatch(versions)


def test_FloatRange_OutsideOfRangeHigher():
    vrange = VersionRange("[1.0.*, 2.0.0)")

    versions = [
        NuGetVersion("2.0.0"),
        NuGetVersion("2.0.0-alpha.2"),
        NuGetVersion("3.1.0"),
    ]

    assert not vrange.FindBestMatch(versions)


def test_FloatRange_OutsideOfRangeOpen():
    vrange = VersionRange("[1.0.*, )")
    versions = [NuGetVersion("0.1.0"), NuGetVersion("0.2.0"), NuGetVersion("1.0.0-alpha.2")]
    assert not vrange.FindBestMatch(versions)


def test_FloatRange_RangeOpen():
    vrange = VersionRange("[1.0.*, )")

    versions = [
        NuGetVersion("0.1.0"),
        NuGetVersion("0.2.0"),
        NuGetVersion("1.0.0-alpha.2"),
        NuGetVersion("101.0.0"),
    ]

    assert vrange.FindBestMatch(versions).to_string() == "101.0.0"


def test_FloatRange_ParsePrerelease():
    vrange = FloatRange("1.0.0-*")
    assert vrange.Satisfies(NuGetVersion("1.0.0-alpha"))
    assert vrange.Satisfies(NuGetVersion("1.0.0-beta"))
    assert vrange.Satisfies(NuGetVersion("1.0.0"))
    assert not vrange.Satisfies(NuGetVersion("1.0.1-alpha"))
    assert not vrange.Satisfies(NuGetVersion("1.0.1"))


def test_FloatingRange_FloatNone():
    vrange = FloatRange("1.0.0")
    assert vrange.MinVersion.to_string() == "1.0.0"
    assert vrange.FloatBehavior == NuGetVersionFloatBehavior


def test_FloatingRange_FloatPre():
    vrange = FloatRange("1.0.0-*")

    assert vrange.MinVersion.to_string() == "1.0.0-0"
    assert vrange.FloatBehavior == NuGetVersionFloatBehavior.Prerelease


def test_FloatingRange_FloatPrePrefix():
    vrange = FloatRange("1.0.0-alpha-*")
    assert vrange.MinVersion.to_string() == "1.0.0-alpha-"
    assert vrange.FloatBehavior == NuGetVersionFloatBehavior.Prerelease


def test_FloatingRange_FloatRev():
    vrange = FloatRange("1.0.0.*")
    assert vrange.MinVersion.to_string() == "1.0.0"
    assert vrange.FloatBehavior == NuGetVersionFloatBehavior.Revision


def test_FloatingRange_FloatPatch():
    vrange = FloatRange("1.0.*")
    assert vrange.MinVersion.to_string() == "1.0.0"
    assert vrange.FloatBehavior == NuGetVersionFloatBehavior.Patch


def test_FloatingRange_FloatMinor():
    vrange = FloatRange("1.*")
    assert vrange.MinVersion.to_string() == "1.0.0"
    assert vrange.FloatBehavior == NuGetVersionFloatBehavior.Minor


def test_FloatingRange_FloatMajor():
    vrange = FloatRange("*")
    assert vrange.MinVersion.to_string() == "0.0.0"
    assert vrange.FloatBehavior == NuGetVersionFloatBehavior.Major


def test_FloatingRange_FloatNoneBest():
    vrange = VersionRange("1.0.0")

    versions = [
        NuGetVersion("1.0.0"),
        NuGetVersion("1.0.1"),
        NuGetVersion("2.0.0"),
    ]

    assert vrange.FindBestMatch(versions).to_string() == "1.0.0"


def test_FloatingRange_FloatMinorBest():

    vrange = VersionRange("1.*")

    versions = [
        NuGetVersion("0.1.0"),
        NuGetVersion("1.0.0"),
        NuGetVersion("1.2.0"),
        NuGetVersion("2.0.0"),
    ]

    assert vrange.FindBestMatch(versions).to_string() == "1.2.0"


def test_FloatingRange_FloatMinorPrefixNotFoundBest():

    vrange = VersionRange("1.*")

    versions = [
        NuGetVersion("0.1.0"),
        NuGetVersion("2.0.0"),
        NuGetVersion("2.5.0"),
        NuGetVersion("3.3.0"),
    ]

    # take the nearest when the prefix is not matched
    assert vrange.FindBestMatch(versions).to_string() == "2.0.0"


def test_FloatingRange_FloatAllBest():

    vrange = VersionRange("*")

    versions = [
        NuGetVersion("0.1.0"),
        NuGetVersion("2.0.0"),
        NuGetVersion("2.5.0"),
        NuGetVersion("3.3.0"),
    ]

    assert vrange.FindBestMatch(versions).to_string() == "3.3.0"


def test_FloatingRange_FloatPrereleaseBest():

    vrange = VersionRange("1.0.0-*")

    versions = [
        NuGetVersion("0.1.0-alpha"),
        NuGetVersion("1.0.0-alpha01"),
        NuGetVersion("1.0.0-alpha02"),
        NuGetVersion("2.0.0-beta"),
        NuGetVersion("2.0.1"),
    ]

    assert vrange.FindBestMatch(versions).to_string() == "1.0.0-alpha02"


def test_FloatingRange_FloatPrereleaseNotFoundBest():

    vrange = VersionRange("1.0.0-*")

    versions = [
        NuGetVersion("0.1.0-alpha"),
        NuGetVersion("1.0.1-alpha01"),
        NuGetVersion("1.0.1-alpha02"),
        NuGetVersion("2.0.0-beta"),
        NuGetVersion("2.0.1"),
    ]

    assert vrange.FindBestMatch(versions).to_string() == "1.0.1-alpha01"


def test_FloatingRange_FloatPrereleasePartialBest():

    vrange = VersionRange("1.0.0-alpha*")

    versions = [
        NuGetVersion("0.1.0-alpha"),
        NuGetVersion("1.0.0-alpha01"),
        NuGetVersion("1.0.0-alpha02"),
        NuGetVersion("2.0.0-beta"),
        NuGetVersion("2.0.1"),
    ]

    assert vrange.FindBestMatch(versions).to_string() == "1.0.0-alpha02"


def test_FloatingRange_to_stringPre():

    vrange = VersionRange("1.0.0-*")

    assert vrange.to_string() == "[1.0.0-*, )"


def test_FloatingRange_to_stringPrePrefix():

    vrange = VersionRange("1.0.0-alpha.*")

    assert vrange.to_string() == "[1.0.0-alpha.*, )"


def test_FloatingRange_to_stringRev():

    vrange = VersionRange("1.0.0.*")

    assert vrange.to_string() == "[1.0.0.*, )"


def test_FloatingRange_to_stringPatch():

    vrange = VersionRange("1.0.*")

    assert vrange.to_string() == "[1.0.*, )"


def test_FloatingRange_to_stringMinor():

    vrange = VersionRange("1.*")

    assert vrange.to_string() == "[1.*, )"


@pytest.mark.parametrize(
    "floatVersionString",
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
def test_FloatingRange_TryParse_Invalid(floatVersionString):
    valid = FloatRange.from_string(floatVersionString)
    assert not valid


@pytest.mark.parametrize(
    "floatVersionString",
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
def test_FloatingRange_Parse_Valid(floatVersionString):

    vrange = FloatRange(floatVersionString)
    assert vrange


@pytest.mark.parametrize(
    "floatVersionString",
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
def test_FloatingRange_Parse_Invalid(floatVersionString):

    vrange = FloatRange(floatVersionString)

    assert not vrange


@pytest.mark.parametrize(
    "floatVersionString",
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
def test_FloatingRange_TryParse_Valid(floatVersionString):
    valid = FloatRange.from_string(floatVersionString)
    assert valid
    assert vrange


def test_FloatingRange_FloatPrereleaseRev():
    vrange = FloatRange("1.0.0.*-*")
    assert vrange.MinVersion.to_string() == "1.0.0-0"
    assert vrange.FloatBehavior == NuGetVersionFloatBehavior.PrereleaseRevision


def test_FloatingRange_FloatPrereleasePatch():

    vrange = FloatRange("1.0.*-*")

    assert vrange.MinVersion.to_string() == "1.0.0-0"
    assert vrange.FloatBehavior == NuGetVersionFloatBehavior.PrereleasePatch


def test_FloatingRange_FloatPrereleaseMinor():
    vrange = FloatRange("1.*-*")
    assert vrange.MinVersion.to_string() == "1.0.0-0"
    assert vrange.FloatBehavior == NuGetVersionFloatBehavior.PrereleaseMinor


def test_FloatingRange_FloatMajorPrerelease():
    vrange = FloatRange("*-rc.*")
    assert vrange.MinVersion.to_string() == "0.0.0-rc.0"
    assert vrange.FloatBehavior == NuGetVersionFloatBehavior.PrereleaseMajor


def test_FloatingRange_FloatAbsoluteLatest():
    vrange = FloatRange("*-*")
    assert vrange.MinVersion.to_string() == "0.0.0-0"
    assert vrange.FloatBehavior == NuGetVersionFloatBehavior.AbsoluteLatest


@pytest.mark.parametrize(
    "versionRange, normalizedMinVersion",
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
def test_FloatRange_ParsesCorrectMinVersion(versionRange, normalizedMinVersion):
    vrange = FloatRange(versionRange)
    assert vrange.MinVersion.to_string() == normalizedMinVersion
