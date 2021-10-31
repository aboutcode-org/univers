# Copyright (c) 2009-2020 by Pacman Development Team
# Copyright (c) 2008 by Dan McGee <dan@archlinux.org>
# SPDX-License-Identifier: Apache-2.0
# this has been significantly modified from the original

from univers.versions import ArchVersion


def test_same_length():
    assert ArchVersion("1.5.0") == ArchVersion("1.5.0")
    assert ArchVersion("1.5.1") > ArchVersion("1.5.0")


def test_mixed_length():
    assert ArchVersion("1.5.1") > ArchVersion("1.5")


def test_with_pkgrel_same_length():
    assert ArchVersion("1.5.0-1") == ArchVersion("1.5.0-1")
    assert ArchVersion("1.5.0-1") < ArchVersion("1.5.0-2")
    assert ArchVersion("1.5.0-1") < ArchVersion("1.5.1-1")
    assert ArchVersion("1.5.0-2") < ArchVersion("1.5.1-1")


def test_alpha_dotted_versions():
    assert ArchVersion("1.5.a") > ArchVersion("1.5")
    assert ArchVersion("1.5.b") > ArchVersion("1.5.a")
    assert ArchVersion("1.5.1") > ArchVersion("1.5.b")


def test_with_epoch():
    assert ArchVersion("0:1.0") == ArchVersion("0:1.0")
    assert ArchVersion("0:1.0") < ArchVersion("0:1.1")
    assert ArchVersion("1:1.0") > ArchVersion("0:1.0")
    assert ArchVersion("1:1.0") > ArchVersion("0:1.1")
    assert ArchVersion("1:1.0") < ArchVersion("2:1.1")


def test_with_epoch_mixed_pkgrel():
    assert ArchVersion("1:1.0") > ArchVersion("0:1.0-1")
    assert ArchVersion("1:1.0-1") > ArchVersion("0:1.1-1")


def test_with_only_one_version_with_epoch():
    assert ArchVersion("0:1.0") == ArchVersion("1.0")
    assert ArchVersion("0:1.0") < ArchVersion("1.1")
    assert ArchVersion("0:1.1") > ArchVersion("1.0")
    assert ArchVersion("1:1.0") > ArchVersion("1.0")
    assert ArchVersion("1:1.0") > ArchVersion("1.1")
    assert ArchVersion("1:1.1") > ArchVersion("1.1")


def test_alpha_dot_and_dashes():
    assert ArchVersion("1.5.b-1") == ArchVersion("1.5.b")
    assert ArchVersion("1.5-1") < ArchVersion("1.5.b")


# def test_same_content_different_separators():
#     assert ArchVersion("2.0") == ArchVersion("2_0")
#     assert ArchVersion("2.0_a") == ArchVersion("2_0.a")
#     assert ArchVersion("2.0a ") < ArchVersion("2.0.a")
#     assert ArchVersion("2___a") == ArchVersion("2_a")


def test_with_pkgrel_mixed_length():
    assert ArchVersion("1.5-1") < ArchVersion("1.5.1-1")
    assert ArchVersion("1.5-2") < ArchVersion("1.5.1-1")
    assert ArchVersion("1.5-2") < ArchVersion("1.5.1-2")


def test_with_mixed_pkgrel_inclusion():
    assert ArchVersion("1.5") == ArchVersion("1.5-1")
    assert ArchVersion("1.5-1") == ArchVersion("1.5")
    assert ArchVersion("1.1-1") == ArchVersion("1.1")
    assert ArchVersion("1.0-1") < ArchVersion("1.1")
    assert ArchVersion("1.1-1") > ArchVersion("1.0")


def test_alphanumeric_versions():
    assert ArchVersion("1.5b-1") < ArchVersion("1.5-1")
    assert ArchVersion("1.5b  ") < ArchVersion("1.5  ")
    assert ArchVersion("1.5b-1") < ArchVersion("1.5  ")
    assert ArchVersion("1.5b  ") < ArchVersion("1.5.1")


def test_manpage_cases():
    assert ArchVersion("1.0a") < ArchVersion("1.0alpha")
    assert ArchVersion("1.0alpha") < ArchVersion("1.0b")
    assert ArchVersion("1.0b") < ArchVersion("1.0beta")
    assert ArchVersion("1.0beta") < ArchVersion("1.0rc")
    assert ArchVersion("1.0rc") < ArchVersion("1.0")
