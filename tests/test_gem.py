# Copyright (c) Center for Information Technology, http://coi.gov.pl
# SPDX-License-Identifier: Apache-2.0
# this has been significantly modified from the original
#
# Visit https://aboutcode.org and https://github.com/nexB/univers for support and download.

# notes: This has been substantially modified and enhanced from the original
# puppeteer code to extract the Ruby version hanlding code.

import pytest
from univers.gem import GemVersion
from univers.gem import GemRequirement


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
