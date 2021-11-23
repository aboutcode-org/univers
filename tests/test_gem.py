# Copyright 2017 Center for Information Technology
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

import pytest
from puppeter.domain.model.gemrequirement import GemVersion, GemRequirement


def test_gem_version_release():
    # given
    v = GemVersion("1.2.4.beta")

    # when
    released = v.release()

    # then
    assert GemVersion("1.2.4") == released


def test_gem_version_bump():
    # given
    v = GemVersion("1.2.4")

    # when
    bumped = v.bump()

    # then
    assert GemVersion("1.3.0") == bumped


def test_gem_version_compare():
    assert GemVersion("1.3.0") == GemVersion("1.3")
    assert GemVersion("1.3.0") <= GemVersion("1.3")
    assert GemVersion("1.1.3") <= GemVersion("1.3")
    assert GemVersion("1.4.pre") >= GemVersion("1.3")
    assert GemVersion("1.4.pre") != GemVersion("1.4")


@pytest.mark.parametrize(
    "requirement,version",
    [
        (["3.4"], "3.4.0"),
        (["~> 3.4"], "3.4.8"),
        ([">= 3.4"], "4.4.8"),
        ([">= 3.4", "<4"], "3.45.8"),
    ],
)
def test_gem_requirement(requirement, version):
    assert GemRequirement(*requirement).satified_by(version)


@pytest.mark.parametrize(
    "requirement,version", [([">= 3.4", "<4"], "4.1"), (["~> 3"], "4.1.0.pre")]
)
def test_gem_requirement_fails(requirement, version):
    assert GemRequirement(*requirement).satified_by(version) is False
