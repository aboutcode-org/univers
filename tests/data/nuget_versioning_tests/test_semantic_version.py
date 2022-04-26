# Copyright (c) .NET Foundation. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
# URL: https://github.com/NuGet/NuGet.Client
# Ported to Python from the C# NuGet test suite and significantly modified

import unittest

import pytest


class SemanticVersionTests(unittest.TestCase):
    @pytest.mark.parametrize(
        ["versionString"],
        [
            ("1.0.0"),
            ("0.0.1"),
            ("1.2.3"),
            ("1.2.3-alpha"),
            ("1.2.3-X.yZ.3.234.243.32423423.4.23423.4324.234.234.3242"),
            ("1.2.3-X.yZ.3.234.243.32423423.4.23423+METADATA"),
            ("1.2.3-X.y3+0"),
            ("1.2.3-X+0"),
            ("1.2.3+0"),
            ("1.2.3-0"),
        ],
    )
    def test_ParseSemanticVersionStrict(self, versionString):
        semVer = SemanticVersion(versionString)
        assert versionString == semVer.to_string()

    @pytest.mark.parametrize(
        ["versionString"],
        [
            ("1.2.3"),
            ("1.2.3+0"),
            ("1.2.3+321"),
            ("1.2.3+XYZ"),
        ],
    )
    def test_SemanticVersionStrictEquality(self, versionString):
        main = SemanticVersion("1.2.3")
        semVer = SemanticVersion(versionString)
        assert main == semVer

    @pytest.mark.parametrize(
        ["versionString"],
        [
            ("1.2.3-alpha"),
            ("1.2.3-alpha+0"),
            ("1.2.3-alpha+10"),
            ("1.2.3-alpha+beta"),
        ],
    )
    def test_SemanticVersionStrictEqualityPreRelease(self, versionString):
        main = SemanticVersion("1.2.3-alpha")
        semVer = SemanticVersion(versionString)
        assert main == semVer

    @pytest.mark.parametrize(
        ["versionString"],
        [
            ("2.7"),
            ("1.3.4.5"),
            ("1.3-alpha"),
            ("1.3 .4"),
            ("2.3.18.2-a"),
            ("1.2.3-A..B"),
            ("01.2.3"),
            ("1.02.3"),
            ("1.2.03"),
            (".2.03"),
            ("1.2."),
            ("1.2.3-a$b"),
            ("a.b.c"),
            ("1.2.3-00"),
            ("1.2.3-A.00.B"),
        ],
    )
    def test_TryParseStrictReturnsFalseIfVersionIsNotStrictSemVer(self, version):
        semanticVersion = SemanticVersion(version)
        assert not semanticVersion
