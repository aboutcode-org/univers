#
# Copyright (c) nexB Inc. and others.
# SPDX-License-Identifier: Apache-2.0
#
# Visit https://aboutcode.org and https://github.com/nexB/univers for support and download.

import pytest

from univers import versions


def test_version_comparison_for_semver_edge_case():
    assert versions.SemverVersion("1.0.0") == versions.SemverVersion("1.0")
    assert versions.SemverVersion("1.2.3+42") != versions.SemverVersion("1.2.3+23")
    assert versions.SemverVersion("1.2.3+42") > versions.SemverVersion("1.2.3+23")


def test_version_comparison_for_golang_edge_case():
    assert versions.GolangVersion("1.0.0") == versions.GolangVersion("v1")
    assert versions.GolangVersion("1.0.0") == versions.GolangVersion("v1.0")
    assert versions.GolangVersion("1.0.0") == versions.GolangVersion("v1.0.0")
    assert versions.GolangVersion("v1.0") > versions.GolangVersion("v0.3.0")
    assert versions.GolangVersion("v0.1.0") < versions.GolangVersion("v0.3.0")
    assert versions.GolangVersion("v0.1") != versions.GolangVersion("v0.1.1")
    assert versions.GolangVersion("v0.1.1") >= versions.GolangVersion("v0.1")
    assert versions.GolangVersion("v0.1.1") >= versions.GolangVersion("v0.1.1")
    assert versions.GolangVersion("v0.1.1") <= versions.GolangVersion("v0.1.1")
    assert versions.GolangVersion("v0.1.1") <= versions.GolangVersion("v0.1.2")


def test_version_comparison_for_pypi_edge_case():
    assert versions.PypiVersion("2.4") == versions.PypiVersion("2.4.0")
    assert versions.PypiVersion("2.5") > versions.PypiVersion("2.4.0")
    assert versions.PypiVersion("2.5") != versions.PypiVersion("2.4.0")
    assert versions.PypiVersion("2.4") < versions.PypiVersion("2.5.0")
    assert versions.PypiVersion("2.6") >= versions.PypiVersion("2.5.0")
    assert versions.PypiVersion("2.3") <= versions.PypiVersion("2.5.0")
    assert versions.PypiVersion("2.6") >= versions.PypiVersion("2.6.0")
    assert versions.PypiVersion("2.5") <= versions.PypiVersion("2.5.0")


def test_version_comparison_for_golang_edge_case():
    assert versions.ComposerVersion("1.0.0") == versions.ComposerVersion("v1")
    assert versions.ComposerVersion("1.0.0") == versions.ComposerVersion("v1.0")
    assert versions.ComposerVersion("1.0.0") == versions.ComposerVersion("v1.0.0")
    assert versions.ComposerVersion("v1.0") > versions.ComposerVersion("v0.3.0")
    assert versions.ComposerVersion("v0.1.0") < versions.ComposerVersion("v0.3.0")
    assert versions.ComposerVersion("v0.1") != versions.ComposerVersion("v0.1.1")
    assert versions.ComposerVersion("v0.1.1") >= versions.ComposerVersion("v0.1")
    assert versions.ComposerVersion("v0.1.1") >= versions.ComposerVersion("v0.1.1")
    assert versions.ComposerVersion("v0.1.1") <= versions.ComposerVersion("v0.1.1")
    assert versions.ComposerVersion("v0.1.1") <= versions.ComposerVersion("v0.1.2")


def test_version_comparison_for_nginx_edge_case():
    assert versions.NginxVersion("1.0.0") == versions.NginxVersion("1")
    assert versions.NginxVersion("1.0.0") == versions.NginxVersion("1.0")
    assert versions.NginxVersion("1.0.0") == versions.NginxVersion("1.0.0")
    assert versions.NginxVersion("1.0") > versions.NginxVersion("0.3.0")
    assert versions.NginxVersion("0.1.0") < versions.NginxVersion("0.3.0")
    assert versions.NginxVersion("0.1") != versions.NginxVersion("0.1.1")
    assert versions.NginxVersion("0.1.1") >= versions.NginxVersion("0.1")
    assert versions.NginxVersion("0.1.1") >= versions.NginxVersion("0.1.1")
    assert versions.NginxVersion("0.1.1") <= versions.NginxVersion("0.1.1")
    assert versions.NginxVersion("0.1.1") <= versions.NginxVersion("0.1.2")


def test_version_comparison_for_gem_edge_case():
    assert versions.RubygemsVersion("1.3.0") == versions.RubygemsVersion("1.3")
    assert versions.RubygemsVersion("1.3.0") <= versions.RubygemsVersion("1.3")
    assert versions.RubygemsVersion("1.1.3") <= versions.RubygemsVersion("1.3")
    assert versions.RubygemsVersion("1.4.pre") >= versions.RubygemsVersion("1.3")
    assert versions.RubygemsVersion("1.4.pre") != versions.RubygemsVersion("1.4")


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
