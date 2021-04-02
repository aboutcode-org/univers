#
# Copyright (c) nexB Inc. and others.
# SPDX-License-Identifier: Apache-2.0
#
# Visit https://aboutcode.org and https://github.com/nexB/ for support and download.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from unittest import TestCase
from packaging import version

from univers import versions


class TestPYPIVersion(TestCase):
    def test_constructor(self):
        pypi_version = versions.PYPIVersion("2.4.5")
        assert pypi_version.value == version.Version("2.4.5")
        assert pypi_version.scheme == "pypi"

        self.assertRaises(versions.InvalidVersion, versions.PYPIVersion, "2.//////")

    # Comparision is already tested at https://github.com/pypa/packaging/blob/main/tests/test_version.py
