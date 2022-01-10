#
# Copyright (c) Chad Fowler, Rich Kilmer, Jim Weirich and others.
# Portions copyright (c) Engine Yard and Andre ArkoFacebook, Inc. and its affiliates.
#
# SPDX-License-Identifier: MIT
#
# Originally from https://github.com/rubygems/rubygems

from univers.gem import GemRequirement


def test_satisfied_by():

    assert not GemRequirement("!= 1").satisfied_by("1")
    assert GemRequirement("!= 1").satisfied_by("2")

    assert not GemRequirement("!= 1", "= 2").satisfied_by("1")
    assert GemRequirement("!= 1", "= 2").satisfied_by("2")

    assert not GemRequirement("!= 1", "> 1").satisfied_by("1")
    assert GemRequirement("!= 1", "> 1").satisfied_by("2")

    assert not GemRequirement("!= 1", ">= 1").satisfied_by("1")
    assert GemRequirement("!= 1", ">= 1").satisfied_by("2")

    assert not GemRequirement("= 1", ">= 0.1", "<= 1.1").satisfied_by("0.2")
    assert GemRequirement("= 1", ">= 0.1", "<= 1.1").satisfied_by("1")
    assert not GemRequirement("= 1", ">= 0.1", "<= 1.1").satisfied_by("3")

    assert GemRequirement("= 1", ">= 1", "<= 1").satisfied_by("1")
    assert not GemRequirement("= 1", ">= 1", "<= 1").satisfied_by("2")
    assert not GemRequirement("= 1", ">= 1", "<= 1").satisfied_by("0.1")

    assert GemRequirement("= 1", "~> 1").satisfied_by("1")
    assert not GemRequirement("= 1", "~> 1").satisfied_by("1.1")

    assert GemRequirement(">= 0.z", "= 0").satisfied_by("0")
    assert not GemRequirement(">= 0.z", "= 0").satisfied_by("1")
    assert not GemRequirement(">= 0.z", "= 0").satisfied_by("0.1")
    assert not GemRequirement(">= 0.z", "= 0").satisfied_by("0.z")

    assert GemRequirement(">= 0").satisfied_by("1")
    assert GemRequirement(">= 0").satisfied_by("2")
    assert GemRequirement(">= 0").satisfied_by("0")

    assert not GemRequirement(">= 1.0.0", "< 2.0.0").satisfied_by("3")
    assert GemRequirement(">= 1.0.0", "< 2.0.0").satisfied_by("1.5.1")

    assert GemRequirement("~> 1").satisfied_by("1")
    assert GemRequirement("~> 1").satisfied_by("1.1")
    assert not GemRequirement("~> 1").satisfied_by("2")

    assert not GemRequirement("~> 2.0", "~> 2.1").satisfied_by("1")
    assert GemRequirement("~> 2.0", "~> 2.1").satisfied_by("2.1.2")

    assert not GemRequirement(">= 4.1.0", "< 5.0", "= 5.2.1").satisfied_by("1")
    assert not GemRequirement(">= 4.1.0", "< 5.0", "= 5.2.1").satisfied_by("5.2.1")
    assert not GemRequirement(
        "< 5.0",
        "< 5.3",
        "< 6.0",
        "< 6",
        "= 5.2.0",
        "> 2",
        ">= 3.0",
        ">= 3.1",
        ">= 3.2",
        ">= 4.0.0",
        ">= 4.1.0",
        ">= 4.2.0",
        ">= 4.2",
        ">= 4",
    ).satisfied_by("5.2.0")
    assert not GemRequirement("!= 1", "< 2", "> 2").satisfied_by("1")
    assert not GemRequirement("!= 1", "<= 1", ">= 1").satisfied_by("1")
    assert not GemRequirement("< 2", "> 2").satisfied_by("1")
    assert not GemRequirement("< 2", "> 2", "= 2").satisfied_by("1")
    assert not GemRequirement("= 1", "!= 1").satisfied_by("1")
    assert not GemRequirement("= 1", "= 2").satisfied_by("1")
    assert not GemRequirement("= 1", "~> 2").satisfied_by("1")
    assert not GemRequirement(">= 0", "<= 0.a").satisfied_by("1")
    assert not GemRequirement("~> 2.0", "~> 3").satisfied_by("1")
