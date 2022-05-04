# Copyright (c) .NET Foundation. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
# URL: https://github.com/NuGet/NuGet.Client
# Ported to Python from the C# NuGet test suite and significantly modified

import pytest

from univers import nuget


@pytest.mark.parametrize(
    "version",
    [
        ("2"),
        ("2.0"),
        ("2.0.0"),
        ("2.0.0.0"),
    ],
)
def test_VersionLength(version):
    semVer = nuget.Version.from_string(version)
    assert semVer.to_string() == "2.0.0"


@pytest.mark.parametrize(
    ("version", "expected"),
    [
        ("1.0.0-Beta", "1.0.0-beta"),
        ("1.0.0-Beta.2", "1.0.0-beta.2"),
        ("1.0.0+MetaOnly", "1.0.0+MetaOnly"),
        ("1.0.0", "1.0.0"),
        ("1.0.0-Beta+Meta", "1.0.0-beta+Meta"),
        ("1.0.0-RC.X+MetaAA", "1.0.0-rc.x+MetaAA"),
        ("1.0.0-RC.X.35.A.3455+Meta-A-B-C", "1.0.0-rc.x.35.a.3455+Meta-A-B-C"),
    ],
)
def test_FullVersionParsing(version, expected):
    version = nuget.Version.from_string(version)
    assert str(version) == expected


@pytest.mark.parametrize(
    ["expected", "version"],
    [
        ("beta", "1.0.0-Beta"),
        ("beta", "1.0.0-Beta+Meta"),
        ("rc.x", "1.0.0-RC.X+Meta"),
        ("rc.x.35.a.3455", "1.0.0-RC.X.35.A.3455+Meta"),
    ],
)
def test_SpecialVersionParsing(expected, version):
    version = nuget.Version.from_string(version)
    assert version.prerelease == expected


@pytest.mark.parametrize(
    "expected, version",
    [
        ("", "1.0.0-Beta"),
        ("Meta", "1.0.0-Beta+Meta"),
        ("MetaAA", "1.0.0-RC.X+MetaAA"),
        ("Meta-A-B-C", "1.0.0-RC.X.35.A.3455+Meta-A-B-C"),
    ],
)
def test_MetadataParsing(expected, version):
    version = nuget.Version.from_string(version)
    assert version.build == expected


@pytest.mark.parametrize(
    "expected, version",
    [
        (False, "1.0.0-Beta"),
        (False, "1.0.0-Beta.2"),
        (True, "1.0.0+MetaOnly"),
        (False, "1.0.0"),
        (True, "1.0.0-Beta+Meta"),
        (True, "1.0.0-RC.X+MetaAA"),
        (True, "1.0.0-RC.X.35.A.3455+Meta-A-B-C"),
    ],
)
def test_HasMetadataParsing(expected, version):
    version = nuget.Version.from_string(version)
    assert bool(version.build) == expected


@pytest.mark.parametrize(
    "major, minor, patch, version",
    [
        (0, 0, 0, "0.0.0"),
        (1, 0, 0, "1.0.0"),
        (3, 5, 1, "3.5.1"),
        (234, 234234, 1111, "234.234234.1111"),
        (3, 5, 1, "3.5.1+Meta"),
        (3, 5, 1, "3.5.1-x.y.z+AA"),
    ],
)
def test_VersionParsing(major, minor, patch, version):
    version = nuget.Version.from_string(version)
    assert version.major == major
    assert version.minor == minor
    assert version.patch == patch
