# Copyright (c) .NET Foundation. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
# URL: https://github.com/NuGet/NuGet.Client
# Ported to Python from the C# NuGet test suite and significantly modified

import pytest

from univers import nuget


@pytest.mark.parametrize(
    "version1, version2",
    [
        ("1.0.0", "1.0.0"),
        ("1.0.0-BETA", "1.0.0-beta"),
        ("1.0.0-BETA+AA", "1.0.0-beta+aa"),
        ("1.0.0-BETA.X.y.5.77.0+AA", "1.0.0-beta.x.y.5.77.0+aa"),
        ("1.0.0", "1.0.0+beta"),
    ],
)
def test_VersionComparisonDefaultEqual(version1, version2):
    assert nuget.Version.from_string(version1) == nuget.Version.from_string(version2)


@pytest.mark.parametrize(
    "version1, version2",
    [
        ("1.0", "1.0.0.0"),
        ("1.0+test", "1.0.0.0"),
        ("1.0.0.1-1.2.A", "1.0.0.1-1.2.a+A"),
        ("1.0.01", "1.0.1.0"),
    ],
)
def test_VersionComparisonDefaultEqualWithNuGetVersion(version1, version2):
    assert nuget.Version.from_string(version1) == nuget.Version.from_string(version2)


@pytest.mark.parametrize(
    "version1, version2",
    [
        ("1.0", "1.0.0.1"),
        ("1.0+test", "1.0.0.1"),
        ("1.0.0.1-1.2.A", "1.0.0.1-1.2.a.A+A"),
        ("1.0.01", "1.0.1.2"),
    ],
)
def test_VersionComparisonDefaultNotEqualWithNuGetVersion(version1, version2):
    assert nuget.Version.from_string(version1) != nuget.Version.from_string(version2)


@pytest.mark.parametrize(
    "version1, version2",
    [
        ("0.0.0", "1.0.0"),
        ("1.1.0", "1.0.0"),
        ("1.0.1", "1.0.0"),
        ("1.0.0-BETA", "1.0.0-beta2"),
        ("1.0.0+AA", "1.0.0-beta+aa"),
        ("1.0.0-BETA.X.y.5.77.0+AA", "1.0.0-beta.x.y.5.79.0+aa"),
    ],
)
def test_VersionComparisonDefaultNotEqual(version1, version2):
    assert nuget.Version.from_string(version1) != nuget.Version.from_string(version2)


# FIXME: Semver considers these two the same, but this one NuGet test treated them as different
@pytest.mark.parametrize(
    "version1, version2",
    [
        ("1.0.0-BETA+AA", "1.0.0-beta"),
    ],
)
def test_VersionComparisonDefaultNotEqual2(version1, version2):
    assert nuget.Version.from_string(version1) == nuget.Version.from_string(version2)
