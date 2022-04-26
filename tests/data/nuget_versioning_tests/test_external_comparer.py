# Copyright (c) .NET Foundation. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
# URL: https://github.com/NuGet/NuGet.Client
# Ported to Python from the C# NuGet test suite and significantly modified

import unittest

import pytest


class ExternalComparerTests(unittest.TestCase):
    @pytest.mark.parametrize(
        ["verSpec", "ver"],
        [
            ("(2.3.1-RC+srv01-a5c5ff9, 2.3.1-RC+srv02-dbf5ec0)", "2.3.1-RC+srv03-d9375a6"),
            ("(2.3.1-RC+srv01-a5c5ff9, 2.3.1-RC+srv02-dbf5ec0)", "2.3.1-RC+srv04-0ed1eb0"),
            ("(2.3.1-RC+srv01-a5c5ff9, 2.3.1-RC+srv02-dbf5ec0)", "2.3.1-RC+srv04-cc5438c"),
        ],
    )
    def test_NuGetVersionRangeWithGitCommit(self, verSpec, ver):
        versionInfo = VersionRange(verSpec)
        version = NuGetVersion(ver)
        comparer = GitMetadataComparer()

        result = versionInfo.Satisfies(version, comparer)

        assert result

    @pytest.mark.parametrize(
        ["verSpec", "ver"],
        [
            ("(2.3.1-RC+srv02-dbf5ec0, )", "2.3.1-RC+srv03-d9375a6"),
            ("(2.3.1-RC+srv02-dbf5ec0, )", "2.3.1-RC+srv04-0ed1eb0"),
            ("(2.3.1-RC+srv02-dbf5ec0, )", "2.3.1-RC+srv04-cc5438c"),
            ("[2.3.1-RC+srv02-dbf5ec0, )", "2.3.1-RC+srv00-a5c5ff9"),
        ],
    )
    def test_NuGetVersionRangeWithGitCommitNotInRange(self, verSpec, ver):
        versionInfo = VersionRange(verSpec)
        version = NuGetVersion(ver)
        comparer = GitMetadataComparer()

        result = versionInfo.Satisfies(version, comparer)

        assert not result

    @pytest.mark.parametrize(
        ["version1", "version2"],
        [
            ("2.3.1.0-RC+srv03-d9375a6", "2.3.1-RC+srv04-d9375a6"),
            ("2.3.1.0-RC+srv04-d9375a6", "2.3.1-RC+srv01-d9375a6"),
        ],
    )
    def test_MixedVersionCompare(self, version1, version2):
        semVer1 = NuGetVersion(version1)
        semVer2 = NuGetVersion(version2)
        comparer = GitMetadataComparer()

        result = comparer.Compare(semVer1, semVer2)

        assert result == 0

    @pytest.mark.parametrize(
        ["version1", "version2"],
        [
            ("2.3.1.1-RC+srv03-d9375a6", "2.3.1-RC+srv04-d9375a6"),
            ("2.3.1.0-RC+srv04-d9375a6", "2.3.1-RC.2+srv01-d9375a6"),
        ],
    )
    def test_MixedVersionCompareNotEqual(self, version1, version2):
        semVer1 = NuGetVersion(version1)
        semVer2 = NuGetVersion(version2)
        comparer = GitMetadataComparer()

        result = comparer.Compare(semVer1, semVer2) == 0

        assert not result

    @pytest.mark.parametrize(
        ["version1", "version2"],
        [
            ("2.3.1-RC+srv03-d9375a6", "2.3.1-RC+srv04-d9375a6"),
            ("2.3.1-RC+srv04-d9375a6", "2.3.1-RC+srv01-d9375a6"),
        ],
    )
    def test_DictionaryWithGitCommit(self, version1, version2):
        semVer1 = NuGetVersion(version1)
        semVer2 = NuGetVersion(version2)
        comparer = GitMetadataComparer()
        gitHash = set(comparer)

        gitHash.Add(semVer1)

        assert gitHash.Contains(semVer2)
