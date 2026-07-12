# Copyright 2022 Google LLC
# Copyright (c) .NET Foundation. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# pylint: disable=line-too-long
# Many tests are ported from
# https://github.com/NuGet/NuGet.Client/blob/dev/test/NuGet.Core.Tests/NuGet.Versioning.Test/VersionComparerTests.cs

import json
from pathlib import Path

import pytest

from tests import SchemaDrivenVersTest
from univers.nuget import Version
from univers.versions import NugetVersion

TEST_DATA = Path(__file__).parent / "data" / "schema" / "nuget_version_cmp.json"


class NugetVersionComp(SchemaDrivenVersTest):
    def equality(self):
        """Compare version1 and version2 are equal."""
        return NugetVersion(self.input_version1) == NugetVersion(self.input_version2)

    def comparison(self):
        """Sort versions and return them in the correct order."""
        return [str(v) for v in sorted(map(NugetVersion, self.input["versions"]))]


@pytest.mark.parametrize("test_case", json.load(open(TEST_DATA)))
def test_gentoo_vers_cmp(test_case):
    avc = NugetVersionComp.from_data(data=test_case)
    avc.assert_result()


def test_NugetVersion_hash():
    vers1 = NugetVersion("1.0.1+23")
    vers2 = NugetVersion("1.0.1+23")
    assert hash(vers1) == hash(vers2)


def test_nuget_semver_hash():
    vers1 = Version.from_string("51.0.0+2")
    vers2 = Version.from_string("51.0.0+2")
    assert hash(vers1) == hash(vers2)
