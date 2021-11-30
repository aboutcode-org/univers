# Copyright (c) 2009-2020 by Pacman Development Team
# Copyright (c) 2008 by Dan McGee <dan@archlinux.org>
# SPDX-License-Identifier: Apache-2.0
# this has been significantly modified from the original
#
# Visit https://aboutcode.org and https://github.com/nexB/univers for support and download.

from univers.versions import ArchLinuxVersion


def test_same_length():
    assert ArchLinuxVersion("1.5.0") == ArchLinuxVersion("1.5.0")
    assert ArchLinuxVersion("1.5.1") > ArchLinuxVersion("1.5.0")


def test_mixed_length():
    assert ArchLinuxVersion("1.5.1") > ArchLinuxVersion("1.5")


def test_with_pkgrel_same_length():
    assert ArchLinuxVersion("1.5.0-1") == ArchLinuxVersion("1.5.0-1")
    assert ArchLinuxVersion("1.5.0-1") < ArchLinuxVersion("1.5.0-2")
    assert ArchLinuxVersion("1.5.0-1") < ArchLinuxVersion("1.5.1-1")
    assert ArchLinuxVersion("1.5.0-2") < ArchLinuxVersion("1.5.1-1")


def test_alpha_dotted_versions():
    assert ArchLinuxVersion("1.5.a") > ArchLinuxVersion("1.5")
    assert ArchLinuxVersion("1.5.b") > ArchLinuxVersion("1.5.a")
    assert ArchLinuxVersion("1.5.1") > ArchLinuxVersion("1.5.b")


def test_with_epoch():
    assert ArchLinuxVersion("0:1.0") == ArchLinuxVersion("0:1.0")
    assert ArchLinuxVersion("0:1.0") < ArchLinuxVersion("0:1.1")
    assert ArchLinuxVersion("1:1.0") > ArchLinuxVersion("0:1.0")
    assert ArchLinuxVersion("1:1.0") > ArchLinuxVersion("0:1.1")
    assert ArchLinuxVersion("1:1.0") < ArchLinuxVersion("2:1.1")


def test_with_epoch_mixed_pkgrel():
    assert ArchLinuxVersion("1:1.0") > ArchLinuxVersion("0:1.0-1")
    assert ArchLinuxVersion("1:1.0-1") > ArchLinuxVersion("0:1.1-1")


def test_with_only_one_version_with_epoch():
    assert ArchLinuxVersion("0:1.0") == ArchLinuxVersion("1.0")
    assert ArchLinuxVersion("0:1.0") < ArchLinuxVersion("1.1")
    assert ArchLinuxVersion("0:1.1") > ArchLinuxVersion("1.0")
    assert ArchLinuxVersion("1:1.0") > ArchLinuxVersion("1.0")
    assert ArchLinuxVersion("1:1.0") > ArchLinuxVersion("1.1")
    assert ArchLinuxVersion("1:1.1") > ArchLinuxVersion("1.1")


def test_alpha_dot_and_dashes():
    assert ArchLinuxVersion("1.5.b-1") == ArchLinuxVersion("1.5.b")
    assert ArchLinuxVersion("1.5-1") < ArchLinuxVersion("1.5.b")


# def test_same_content_different_separators():
#     assert ArchLinuxVersion("2.0") == ArchLinuxVersion("2_0")
#     assert ArchLinuxVersion("2.0_a") == ArchLinuxVersion("2_0.a")
#     assert ArchLinuxVersion("2.0a ") < ArchLinuxVersion("2.0.a")
#     assert ArchLinuxVersion("2___a") == ArchLinuxVersion("2_a")


def test_with_pkgrel_mixed_length():
    assert ArchLinuxVersion("1.5-1") < ArchLinuxVersion("1.5.1-1")
    assert ArchLinuxVersion("1.5-2") < ArchLinuxVersion("1.5.1-1")
    assert ArchLinuxVersion("1.5-2") < ArchLinuxVersion("1.5.1-2")


def test_with_mixed_pkgrel_inclusion():
    assert ArchLinuxVersion("1.5") == ArchLinuxVersion("1.5-1")
    assert ArchLinuxVersion("1.5-1") == ArchLinuxVersion("1.5")
    assert ArchLinuxVersion("1.1-1") == ArchLinuxVersion("1.1")
    assert ArchLinuxVersion("1.0-1") < ArchLinuxVersion("1.1")
    assert ArchLinuxVersion("1.1-1") > ArchLinuxVersion("1.0")


def test_alphanumeric_versions():
    assert ArchLinuxVersion("1.5b-1") < ArchLinuxVersion("1.5-1")
    assert ArchLinuxVersion("1.5b  ") < ArchLinuxVersion("1.5  ")
    assert ArchLinuxVersion("1.5b-1") < ArchLinuxVersion("1.5  ")
    assert ArchLinuxVersion("1.5b  ") < ArchLinuxVersion("1.5.1")


def test_manpage_cases():
    assert ArchLinuxVersion("1.0a") < ArchLinuxVersion("1.0alpha")
    assert ArchLinuxVersion("1.0alpha") < ArchLinuxVersion("1.0b")
    assert ArchLinuxVersion("1.0b") < ArchLinuxVersion("1.0beta")
    assert ArchLinuxVersion("1.0beta") < ArchLinuxVersion("1.0rc")
    assert ArchLinuxVersion("1.0rc") < ArchLinuxVersion("1.0")
