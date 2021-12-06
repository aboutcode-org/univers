#
# Copyright (c) Chad Fowler, Rich Kilmer, Jim Weirich and others.
# Portions copyright (c) Engine Yard and Andre ArkoFacebook, Inc. and its affiliates.
#
# SPDX-License-Identifier: MIT
#
# Originally from https://github.com/rubygems/rubygems


from univers.gem import GemRequirement


def test_is_empty():
    assert not GemRequirement("!= 1").is_empty()
    assert not GemRequirement("!= 1", "= 2").is_empty()
    assert not GemRequirement("!= 1", "> 1").is_empty()
    assert not GemRequirement("!= 1", ">= 1").is_empty()
    assert not GemRequirement("= 1", ">= 0.1", "<= 1.1").is_empty()
    assert not GemRequirement("= 1", ">= 1", "<= 1").is_empty()
    assert not GemRequirement("= 1", "~> 1").is_empty()
    assert not GemRequirement(">= 0.z", "= 0").is_empty()
    assert not GemRequirement(">= 0").is_empty()
    assert not GemRequirement(">= 1.0.0", "< 2.0.0").is_empty()
    assert not GemRequirement("~> 1").is_empty()
    assert not GemRequirement("~> 2.0", "~> 2.1").is_empty()
    assert GemRequirement(">= 4.1.0", "< 5.0", "= 5.2.1").is_empty()
    assert GemRequirement(
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
    ).is_empty()
    assert GemRequirement("!= 1", "< 2", "> 2").is_empty()
    assert GemRequirement("!= 1", "<= 1", ">= 1").is_empty()
    assert GemRequirement("< 2", "> 2").is_empty()
    assert GemRequirement("< 2", "> 2", "= 2").is_empty()
    assert GemRequirement("= 1", "!= 1").is_empty()
    assert GemRequirement("= 1", "= 2").is_empty()
    assert GemRequirement("= 1", "~> 2").is_empty()
    assert GemRequirement(">= 0", "<= 0.a").is_empty()
    assert GemRequirement("~> 2.0", "~> 3").is_empty()
