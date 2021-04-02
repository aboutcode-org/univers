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

from univers.version_specifier import VersionSpecifier


class TestVersionSpecifier(TestCase):
    def test_from_version_spec_string(self):
        spec_string = "pypi:0.0.2,0.0.6,0.0.0,0.0.1,0.0.4,0.0.5,0.0.3"
        version_spec = VersionSpecifier.from_version_spec_string(spec_string)

        assert len(version_spec.ranges) == 7
        assert all(["pypi" == vrange.version.scheme for vrange in version_spec.ranges])

    def test_resolving_pessimsitic_operator(self):
        version_range_string = "~>2.0.8"
        version_spec = VersionSpecifier.from_scheme_version_spec_string(
            "semver", version_range_string
        )
        assert len(version_spec.ranges) == 2
