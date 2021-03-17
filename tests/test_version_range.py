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

import pytest

from version_range import VersionRange
from versions import version_class_by_scheme


@pytest.mark.parametrize(
    "scheme ,version, spec, result",
    [
        ("pypi", "2.7", "<=3.4", True),
        ("pypi", "2.7.1", "<=3.4", True),
        ("pypi", "2.7.1rc1", "<=3.4", True),
        ("pypi", "2.7.15", "<=3.4", True),
        ("pypi", "2.7.15rc1", "<=3.4", True),
        ("pypi", "2.7", ">=3.4", False),
        ("pypi", "2.7.1", ">=3.4", False),
        ("pypi", "2.7.1rc1", ">=3.4", False),
        ("pypi", "2.7.15", ">=3.4", False),
        ("pypi", "2.7.15rc1", ">=3.4", False),
        ("pypi", "0.0.0", ">=1.0.0", False),
        ("pypi", "1.2.3", ">=1.0.0", True),
        ("pypi", "1.2.3b1", ">=1.0.0", True),
        ("pypi", "1.0.1b1", ">=1.0.0", True),
        ("pypi", "1.0.0b1", ">=1.0.0", False),
        ("pypi", "1.0.0b1", ">=1.0.0b1", True),
    ],
)
def test_comparision(scheme, version, spec, result):
    version_class = version_class_by_scheme[scheme]
    version_object = version_class(version)
    assert (version_object in VersionRange(spec, scheme)) == result
