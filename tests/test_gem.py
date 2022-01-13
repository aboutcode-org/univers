# Copyright (c) Center for Information Technology, http://coi.gov.pl
# SPDX-License-Identifier: Apache-2.0
# this has been significantly modified from the original
#
# Visit https://aboutcode.org and https://github.com/nexB/univers for support and download.

# notes: This has been substantially modified and enhanced from the original
# puppeteer code to extract the Ruby version handling code.

from univers.gem import GemRequirement
from univers.gem import GemVersion


def test_gem_version_release():
    assert GemVersion("1.2.4.beta").release() == GemVersion("1.2.4")


def test_gem_version_bump():
    assert GemVersion("1.2.4").bump() == GemVersion("1.3.0")


def test_gem_version_compare():
    assert GemVersion("1.3.0") == GemVersion("1.3")
    assert GemVersion("1.3.0") <= GemVersion("1.3")
    assert GemVersion("1.1.3") <= GemVersion("1.3")
    assert GemVersion("1.4.pre") >= GemVersion("1.3")
    assert GemVersion("1.4.pre") != GemVersion("1.4")


def test_gem_requirement():
    assert GemRequirement("3.4").satisfied_by("3.4.0")
    assert GemRequirement("~> 3.4").satisfied_by("3.4.8")
    assert GemRequirement(">= 3.4").satisfied_by("4.4.8")
    assert GemRequirement(">= 3.4", "<4").satisfied_by("3.45.8")


def test_gem_requirement_fails1():
    assert GemRequirement(">= 3.4", "<4").satisfied_by("4.1") is False


def test_gem_requirement_fails2():
    assert GemRequirement("~> 3").satisfied_by("4.1.0.pre") is False
