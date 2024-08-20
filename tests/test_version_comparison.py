#
# Copyright (c) nexB Inc. and others.
# SPDX-License-Identifier: Apache-2.0
#
# Visit https://aboutcode.org and https://github.com/aboutcode-org/univers for support and download.

import pytest

from univers import versions


@pytest.mark.parametrize(
    "version_class",
    [
        versions.SemverVersion,
        versions.GolangVersion,
        versions.PypiVersion,
        versions.GenericVersion,
        versions.ComposerVersion,
        versions.NginxVersion,
        versions.ArchLinuxVersion,
        versions.DebianVersion,
        versions.RpmVersion,
        versions.MavenVersion,
        versions.NugetVersion,
        versions.GentooVersion,
        versions.OpensslVersion,
        versions.LegacyOpensslVersion,
        versions.AlpineLinuxVersion,
    ],
)
def test_version_comparators_are_working(version_class):
    assert version_class("1.0.0") == version_class("1.0.0")
    assert version_class("1.0.0") != version_class("1.0.1")
    assert version_class("1.0.0") < version_class("1.0.1")
    assert version_class("1.0.1") > version_class("1.0.0")
    assert version_class("1.0.0") <= version_class("1.0.1")
    assert version_class("1.0.1") >= version_class("1.0.0")
    assert version_class("1.0.0") <= version_class("1.0.0")
    assert version_class("1.0.0") >= version_class("1.0.0")
