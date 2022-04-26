# Copyright (c) .NET Foundation. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
# URL: https://github.com/NuGet/NuGet.Client
# Ported to Python from the C# NuGet test suite and significantly modified

import unittest

import pytest


class VersionParsingTests(unittest.TestCase):
    @pytest.mark.parametrize(
        [],
        [
            ("2"),
            ("2.0"),
            ("2.0.0"),
            ("2.0.0.0"),
        ],
    )
    def test_VersionLength(self, version):

        semVer = NuGetVersion(version)

        assert semVer.to_string() == "2.0.0"

    @pytest.mark.parametrize(
        [],
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
    def test_FullVersionParsing(self, version):
        versions = Parse(version)
        for v in versions:
            assert v.to_string() == version

    @pytest.mark.parametrize(
        [],
        [
            ("Beta", "1.0.0-Beta"),
            ("Beta", "1.0.0-Beta+Meta"),
            ("RC.X", "1.0.0-RC.X+Meta"),
            ("RC.X.35.A.3455", "1.0.0-RC.X.35.A.3455+Meta"),
        ],
    )
    def test_SpecialVersionParsing(self, expected, version):
        versions = Parse(version)
        for v in versions:
            assert v.Release == expected

    @pytest.mark.parametrize(
        [],
        [
            ("", "1.0.0+Metadata"),
            ("", "1.0.0"),
            ("Beta", "1.0.0-Beta"),
            ("Beta", "1.0.0-Beta+Meta"),
            ("RC", "X", "1.0.0-RC.X+Meta"),
            ("RC", "X", "35", "A", "3455", "1.0.0-RC.X.35.A.3455+Meta"),
        ],
    )
    def test_ReleaseLabelParsing(expected, version):
        versions = Parse(version)
        for v in versions:
            assert v.ReleaseLabels == expected

    @pytest.mark.parametrize(
        [],
        [
            (false, "1.0.0+Metadata"),
            (false, "1.0.0"),
            (true, "1.0.0-Beta"),
            (true, "1.0.0-Beta+Meta"),
            (true, "1.0.0-RC.X+Meta"),
            (true, "1.0.0-RC.X.35.A.3455+Meta"),
        ],
    )
    def test_IsPrereleaseParsing(expected, version):
        versions = Parse(version)
        for v in versions:
            assert v.IsPrerelease == expected

    @pytest.mark.parametrize(
        [],
        [
            ("", "1.0.0-Beta"),
            ("Meta", "1.0.0-Beta+Meta"),
            ("MetaAA", "1.0.0-RC.X+MetaAA"),
            ("Meta-A-B-C", "1.0.0-RC.X.35.A.3455+Meta-A-B-C"),
        ],
    )
    def test_MetadataParsing(self, expected, version):
        versions = Parse(version)
        for v in versions:
            assert v.Metadata == expected

    @pytest.mark.parametrize(
        [],
        [
            (false, "1.0.0-Beta"),
            (false, "1.0.0-Beta.2"),
            (true, "1.0.0+MetaOnly"),
            (false, "1.0.0"),
            (true, "1.0.0-Beta+Meta"),
            (true, "1.0.0-RC.X+MetaAA"),
            (true, "1.0.0-RC.X.35.A.3455+Meta-A-B-C"),
        ],
    )
    def test_HasMetadataParsing(expected, version):
        versions = Parse(version)
        for v in versions:
            assert v.HasMetadata == expected

    @pytest.mark.parametrize(
        [],
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


# All possible ways to parse a version from a string
def Parse(version):

    # Parse
    versions = []
    versions.Add(NuGetVersion(version))
    versions.Add(NuGetVersion(version))

    # TryParse
    semVer = None
    NuGetVersion(version, semVer)
    versions.Add(semVer)

    nuVer = None
    NuGetVersion(version, nuVer)
    versions.Add(nuVer)

    # TryParseStrict
    nuVer = None
    NuGetVersion.TryParseStrict(version, nuVer)
    versions.Add(nuVer)

    # Constructors
    normal = NuGetVersion(version)

    versions.Add(normal)
    versions.Add(NuGetVersion(NuGetVersion(version)))

    return versions
