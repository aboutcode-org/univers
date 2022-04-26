# Copyright (c) .NET Foundation. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
# URL: https://github.com/NuGet/NuGet.Client
# Ported to Python from the C# NuGet test suite and significantly modified

import unittest

import pytest


class VersionComparerTests(unittest.TestCase):
    @pytest.mark.parametrize(
        [],
        [
            ("1.0.0", "1.0.0"),
            ("1.0.0-BETA", "1.0.0-beta"),
            ("1.0.0-BETA+AA", "1.0.0-beta+aa"),
            ("1.0.0-BETA.X.y.5.77.0+AA", "1.0.0-beta.x.y.5.77.0+aa"),
            ("1.0.0", "1.0.0+beta"),
        ],
    )
    def test_VersionComparisonDefaultEqual(self, version1, version2):

        match = Equals(VersionComparer.Default, version1, version2)

        assert match

    @pytest.mark.parametrize(
        [],
        [
            ("1.0", "1.0.0.0"),
            ("1.0+test", "1.0.0.0"),
            ("1.0.0.1-1.2.A", "1.0.0.1-1.2.a+A"),
            ("1.0.01", "1.0.1.0"),
        ],
    )
    def test_VersionComparisonDefaultEqualWithNuGetVersion(self, version1, version2):

        match = EqualsWithNuGetVersion(VersionComparer.Default, version1, version2)

        assert match

    @pytest.mark.parametrize(
        [],
        [
            ("1.0", "1.0.0.1"),
            ("1.0+test", "1.0.0.1"),
            ("1.0.0.1-1.2.A", "1.0.0.1-1.2.a.A+A"),
            ("1.0.01", "1.0.1.2"),
        ],
    )
    def test_VersionComparisonDefaultNotEqualWithNuGetVersion(self, version1, version2):

        match = EqualsWithNuGetVersion(VersionComparer.Default, version1, version2)

        assert not match

    @pytest.mark.parametrize(
        [],
        [
            ("0.0.0", "1.0.0"),
            ("1.1.0", "1.0.0"),
            ("1.0.1", "1.0.0"),
            ("1.0.0-BETA", "1.0.0-beta2"),
            ("1.0.0+AA", "1.0.0-beta+aa"),
            ("1.0.0-BETA+AA", "1.0.0-beta"),
            ("1.0.0-BETA.X.y.5.77.0+AA", "1.0.0-beta.x.y.5.79.0+aa"),
        ],
    )
    def test_VersionComparisonDefaultNotEqual(self, version1, version2):

        assert not Equals(version1, version2)
