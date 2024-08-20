#
# Copyright (c) nexB Inc. and others.
# SPDX-License-Identifier: Apache-2.0
#
# Visit https://aboutcode.org and https://github.com/aboutcode-org/univers for support and download.

from univers.version_constraint import VersionConstraint
from univers.versions import AlpineLinuxVersion
from univers.versions import ArchLinuxVersion
from univers.versions import ComposerVersion
from univers.versions import DebianVersion
from univers.versions import EnhancedSemanticVersion
from univers.versions import GentooVersion
from univers.versions import GolangVersion
from univers.versions import MavenVersion
from univers.versions import NginxVersion
from univers.versions import NugetVersion
from univers.versions import PypiVersion
from univers.versions import RpmVersion
from univers.versions import RubygemsVersion
from univers.versions import SemverVersion
from univers.versions import Version


def test_version():
    assert Version("1.2.3") == Version("1.2.3")
    assert Version("1.2.3") != Version("1.2.4")
    assert Version.is_valid("1.2.3")
    assert not Version.is_valid(None)
    assert Version.normalize("v1.2.3") == "1.2.3"
    assert Version("1.2.3").satisfies(VersionConstraint(comparator=">=", version=Version("1.2.3")))


def test_pypi_version():
    assert PypiVersion("1.2.3") == PypiVersion("1.2.3")
    assert PypiVersion("1.2.3") != PypiVersion("1.2.4")
    assert PypiVersion("1") == PypiVersion("1.0")
    assert PypiVersion.is_valid("1.2.3")
    assert not PypiVersion.is_valid("1.2.3a-1-a")
    assert PypiVersion.normalize("v1.2.3") == "1.2.3"
    assert PypiVersion("1").satisfies(
        VersionConstraint(comparator=">=", version=PypiVersion("1.0.0"))
    )
    assert PypiVersion("2.4") == PypiVersion("2.4.0")
    assert PypiVersion("2.5") > PypiVersion("2.4.0")
    assert PypiVersion("2.5") != PypiVersion("2.4.0")
    assert PypiVersion("2.4") < PypiVersion("2.5.0")
    assert PypiVersion("2.6") >= PypiVersion("2.5.0")
    assert PypiVersion("2.3") <= PypiVersion("2.5.0")
    assert PypiVersion("2.6") >= PypiVersion("2.6.0")
    assert PypiVersion("2.5") <= PypiVersion("2.5.0")


def test_enhanced_semantic_version():
    assert EnhancedSemanticVersion("1.2.3-pre.1+build.1") != EnhancedSemanticVersion(
        "1.2.3-pre.1+build.0"
    )
    assert EnhancedSemanticVersion("1.2.3-pre.1+build.1") > EnhancedSemanticVersion(
        "1.2.3-pre.1+build.0"
    )
    assert (
        EnhancedSemanticVersion("1.2.3-pre.1+build.1").precedence_key
        != EnhancedSemanticVersion("1.2.3-pre.1+build.0").precedence_key
    )


def test_semver_version():
    assert SemverVersion.is_valid("1.2.3")
    assert SemverVersion.is_valid("1.2.3-pre.1+build.1")
    version = SemverVersion("1.2.3-pre.1+build.1")
    assert version.major == 1
    assert version.minor == 2
    assert version.patch == 3
    assert version.prerelease == ("pre", "1")
    assert version.build == ("build", "1")
    assert version.next_major() == SemverVersion("2.0.0")
    assert version.next_minor() == SemverVersion("1.3.0")
    assert version.next_patch() == SemverVersion("1.2.3")
    assert SemverVersion("1.2.3").next_patch() == SemverVersion("1.2.4")
    assert version.satisfies(
        VersionConstraint(comparator=">=", version=SemverVersion("1.2.3-pre.1+build.1"))
    )
    assert SemverVersion("1.0.0") == SemverVersion("1.0")
    assert SemverVersion("1.2.3+42") != SemverVersion("1.2.3+23")
    assert SemverVersion("1.2.3+42") > SemverVersion("1.2.3+23")


def test_nginx_version():
    assert NginxVersion("1.2").is_stable
    assert NginxVersion("1.2.3").is_stable
    assert not NginxVersion("1.3.0").is_stable
    assert NginxVersion("1.0.0") == NginxVersion("1")
    assert NginxVersion("1.0.0") == NginxVersion("1.0")
    assert NginxVersion("1.0.0") == NginxVersion("1.0.0")
    assert NginxVersion("1.0") > NginxVersion("0.3.0")
    assert NginxVersion("0.1.0") < NginxVersion("0.3.0")
    assert NginxVersion("0.1") != NginxVersion("0.1.1")
    assert NginxVersion("0.1.1") >= NginxVersion("0.1")
    assert NginxVersion("0.1.1") >= NginxVersion("0.1.1")
    assert NginxVersion("0.1.1") <= NginxVersion("0.1.1")
    assert NginxVersion("0.1.1") <= NginxVersion("0.1.2")


def test_rubygems_version():
    assert RubygemsVersion("1.2.0") == RubygemsVersion("1.2")
    assert RubygemsVersion.is_valid("1.2ab")
    assert RubygemsVersion.is_valid("1.2.3.a.b.c.d")
    assert not RubygemsVersion.is_valid("aa")
    assert RubygemsVersion("1.3.0") == RubygemsVersion("1.3")
    assert RubygemsVersion("1.3.0") <= RubygemsVersion("1.3")
    assert RubygemsVersion("1.1.3") <= RubygemsVersion("1.3")
    assert RubygemsVersion("1.4.pre") >= RubygemsVersion("1.3")
    assert RubygemsVersion("1.4.pre") != RubygemsVersion("1.4")


def test_arch_linux_version():
    assert ArchLinuxVersion("1.2.3-1") == ArchLinuxVersion("1.2.3-1")
    assert ArchLinuxVersion("1.2.3-1") != ArchLinuxVersion("1.2.3-2")
    assert ArchLinuxVersion("1.2.3-1") > ArchLinuxVersion("1.2.3-0")
    assert ArchLinuxVersion("1.2.3-1") < ArchLinuxVersion("1.2.3-2")
    assert ArchLinuxVersion("1.2.3-1") >= ArchLinuxVersion("1.2.3-1")
    assert ArchLinuxVersion("1.2.3-1") <= ArchLinuxVersion("1.2.3-1")


def test_debian_version():
    assert DebianVersion("1.2.3-1") == DebianVersion("1.2.3-1")
    assert not DebianVersion.is_valid("n")
    assert DebianVersion.is_valid("1.2.3-1")
    assert DebianVersion("1.2.3-1") == DebianVersion("1.2.3-1")
    assert DebianVersion("1.2.3-1") != DebianVersion("1.2.3-2")
    assert DebianVersion("1.2.3-1") > DebianVersion("1.2.3-0")
    assert DebianVersion("1.2.3-1") < DebianVersion("1.2.3-2")
    assert DebianVersion("1.2.3-1") >= DebianVersion("1.2.3-1")
    assert DebianVersion("1.2.3-1") <= DebianVersion("1.2.3-1")


def test_maven_version():
    assert MavenVersion("1.2.3") == MavenVersion("1.2.3")
    assert MavenVersion("1.2.3") != MavenVersion("1.2.4")
    assert MavenVersion("1") == MavenVersion("1.0")
    assert MavenVersion.is_valid("1.2.3")
    assert MavenVersion("1.2.3") == MavenVersion("1.2.3")
    assert MavenVersion("1.2.3") != MavenVersion("1.2.4")
    assert MavenVersion("1.2.3") > MavenVersion("1.2.2")
    assert MavenVersion("1.2.3") < MavenVersion("1.2.4")
    assert MavenVersion("1.2.3") >= MavenVersion("1.2.3")
    assert MavenVersion("1.2.3") <= MavenVersion("1.2.3")


def test_nuget_version():
    assert NugetVersion("1.2.3") == NugetVersion("1.2.3")
    assert NugetVersion("1.2.3") != NugetVersion("1.2.4")
    assert NugetVersion("1") == NugetVersion("1.0")
    assert NugetVersion.is_valid("1.2.3")
    assert not NugetVersion.is_valid("1.2.3a-1-a")


def test_rpm_version():
    assert RpmVersion("1.2.3-1") == RpmVersion("1.2.3-1")
    assert RpmVersion("1.2.3-1") != RpmVersion("1.2.3-2")
    assert RpmVersion("1.2.3-1") > RpmVersion("1.2.3-0")
    assert RpmVersion("1.2.3-1") < RpmVersion("1.2.3-2")
    assert RpmVersion("1.2.3-1") >= RpmVersion("1.2.3-1")
    assert RpmVersion("1.2.3-1") <= RpmVersion("1.2.3-1")


def test_gentoo_version():
    assert GentooVersion("1.2.3") == GentooVersion("1.2.3")
    assert GentooVersion("1.2.3") != GentooVersion("1.2.4")
    assert GentooVersion.is_valid("1.2.3")
    assert not GentooVersion.is_valid("1.2.3a-1-a")


def test_alpine_linux_version():
    assert AlpineLinuxVersion("1.2.3-r1") == AlpineLinuxVersion("1.2.3-r1")
    assert AlpineLinuxVersion("1.2.3-r1") != AlpineLinuxVersion("1.2.3-r2")
    assert AlpineLinuxVersion("1.2.3-r1") > AlpineLinuxVersion("1.2.3-r0")
    assert AlpineLinuxVersion("1.2.3-r1") < AlpineLinuxVersion("1.2.3-r2")
    assert AlpineLinuxVersion("1.2.3-r1") >= AlpineLinuxVersion("1.2.3-r1")
    assert AlpineLinuxVersion("1.2.3-r1") <= AlpineLinuxVersion("1.2.3-r1")
    assert AlpineLinuxVersion.is_valid("1.2.3-r1")
    assert not AlpineLinuxVersion.is_valid("007")


def test_composer_version():
    assert ComposerVersion("1.2.3") == ComposerVersion("1.2.3")
    assert ComposerVersion("1.2.3") != ComposerVersion("1.2.4")
    assert ComposerVersion("1") == ComposerVersion("1.0")
    assert ComposerVersion("v1.0") == ComposerVersion("1.0")
    assert ComposerVersion.is_valid("1.2.3")
    assert ComposerVersion.is_valid("1.2.3a-1-a")
    assert ComposerVersion("1.0.0") == ComposerVersion("v1")
    assert ComposerVersion("1.0.0") == ComposerVersion("v1.0")
    assert ComposerVersion("1.0.0") == ComposerVersion("v1.0.0")
    assert ComposerVersion("v1.0") > ComposerVersion("v0.3.0")
    assert ComposerVersion("v0.1.0") < ComposerVersion("v0.3.0")
    assert ComposerVersion("v0.1") != ComposerVersion("v0.1.1")
    assert ComposerVersion("v0.1.1") >= ComposerVersion("v0.1")
    assert ComposerVersion("v0.1.1") >= ComposerVersion("v0.1.1")
    assert ComposerVersion("v0.1.1") <= ComposerVersion("v0.1.1")
    assert ComposerVersion("v0.1.1") <= ComposerVersion("v0.1.2")


def test_golang_version():
    assert GolangVersion("1.2.3") == GolangVersion("1.2.3")
    assert GolangVersion("1.2.3") != GolangVersion("1.2.4")
    assert GolangVersion("1") == GolangVersion("1.0")
    assert GolangVersion("v1.0") == GolangVersion("1.0")
    assert GolangVersion.is_valid("1.2.3")
    assert GolangVersion.is_valid("1.2.3a-1-a")
    assert GolangVersion("1.0.0") == GolangVersion("v1")
    assert GolangVersion("1.0.0") == GolangVersion("v1.0")
    assert GolangVersion("1.0.0") == GolangVersion("v1.0.0")
    assert GolangVersion("v1.0") > GolangVersion("v0.3.0")
    assert GolangVersion("v0.1.0") < GolangVersion("v0.3.0")
    assert GolangVersion("v0.1") != GolangVersion("v0.1.1")
    assert GolangVersion("v0.1.1") >= GolangVersion("v0.1")
    assert GolangVersion("v0.1.1") >= GolangVersion("v0.1.1")
    assert GolangVersion("v0.1.1") <= GolangVersion("v0.1.1")
    assert GolangVersion("v0.1.1") <= GolangVersion("v0.1.2")
