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
    semVer = nuget.Version(version)
    assert semVer.to_string() == "2.0.0"


@pytest.mark.parametrize(
    "version",
    [
        ("1.0.0-Beta"),
        ("1.0.0-Beta.2"),
        ("1.0.0+MetaOnly"),
        ("1.0.0"),
        ("1.0.0-Beta+Meta"),
        ("1.0.0-RC.X+MetaAA"),
        ("1.0.0-RC.X.35.A.3455+Meta-A-B-C"),
    ],
)
def test_FullVersionParsing(version):
    versions = Parse(version)
    for v in versions:
        assert v.to_string() == version


@pytest.mark.parametrize(
    "expected, version",
    [
        ("Beta", "1.0.0-Beta"),
        ("Beta", "1.0.0-Beta+Meta"),
        ("RC.X", "1.0.0-RC.X+Meta"),
        ("RC.X.35.A.3455", "1.0.0-RC.X.35.A.3455+Meta"),
    ],
)
def test_SpecialVersionParsing(expected, version):
    versions = Parse(version)
    for v in versions:
        assert v.Release == expected


@pytest.mark.parametrize(
    "expected, version",
    [
        ((""), "1.0.0+Metadata"),
        ((""), "1.0.0"),
        (("Beta"), "1.0.0-Beta"),
        (("Beta"), "1.0.0-Beta+Meta"),
        (("RC", "X"), "1.0.0-RC.X+Meta"),
        (("RC", "X", "35", "A", "3455"), "1.0.0-RC.X.35.A.3455+Meta"),
    ],
)
def test_ReleaseLabelParsing(expected, version):
    versions = Parse(version)
    for v in versions:
        assert v.ReleaseLabels == expected


@pytest.mark.parametrize(
    "expected, version",
    [
        (False, "1.0.0+Metadata"),
        (False, "1.0.0"),
        (True, "1.0.0-Beta"),
        (True, "1.0.0-Beta+Meta"),
        (True, "1.0.0-RC.X+Meta"),
        (True, "1.0.0-RC.X.35.A.3455+Meta"),
    ],
)
def test_IsPrereleaseParsing(expected, version):
    versions = Parse(version)
    for v in versions:
        assert v.IsPrerelease == expected


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
    versions = Parse(version)
    for v in versions:
        assert v.Metadata == expected


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
    versions = Parse(version)
    for v in versions:
        assert v.HasMetadata == expected


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
    versions = Parse(version)
    for v in versions:
        assert v.Major == major
        assert v.Minor == minor
        assert v.Patch == patch


def Parse(version):
    """
    All possible ways to parse a version from a string
    """
    # Parse
    versions = []
    versions.Add(nuget.Version(version))
    versions.Add(nuget.Version(version))

    # TryParse
    semVer = None
    nuget.Version(version, semVer)
    versions.Add(semVer)

    nuVer = None
    nuget.Version(version, nuVer)
    versions.Add(nuVer)

    # TryParseStrict
    nuVer = None
    nuget.Version.TryParseStrict(version, nuVer)
    versions.Add(nuVer)

    # Constructors
    normal = nuget.Version(version)

    versions.Add(normal)
    versions.Add(nuget.Version(nuget.Version(version)))

    return versions
