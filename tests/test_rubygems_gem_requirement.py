#
# Copyright (c) Chad Fowler, Rich Kilmer, Jim Weirich and others.
# Portions copyright (c) Engine Yard and Andre ArkoFacebook, Inc. and its affiliates.
#
# SPDX-License-Identifier: MIT
#
# Originally from https://github.com/rubygems/rubygems

from univers.gem import GemConstraint
from univers.gem import GemRequirement
from univers.gem import GemVersion
from univers.gem import InvalidRequirementError


def test_equals():
    refute_requirement_equal("= 1.2", "= 1.3")
    refute_requirement_equal("~> 1.3", "~> 1.3.0")
    assert_requirement_equal(["> 2", "~> 1.3", "~> 1.3.1"], ["~> 1.3.1", "~> 1.3", "> 2"])
    assert_requirement_equal(["> 2", "~> 1.3"], ["> 2.0", "~> 1.3"])


def test_initialize():
    assert_requirement_equal("= 2", "2")
    assert_requirement_equal("= 2", ["2"])
    assert_requirement_equal("= 2", GemVersion(2))
    assert_requirement_equal("2.0", "2")


def test_create():
    r = GemRequirement(">= 1", "< 2")
    assert r.constraints == (
        GemConstraint(">=", GemVersion(1)),
        GemConstraint("<", GemVersion(2)),
    )
    assert GemRequirement("= 1") == GemRequirement("= 1")
    assert GemRequirement(">= 1.2", "<= 1.3") == GemRequirement("<= 1.3", ">= 1.2")


def test_explicit_default_is_not_none():
    r = GemRequirement(">= 0")
    assert r


def test_basic_non_none():
    r = GemRequirement("= 1")
    assert r


def test_for_lockfile():
    assert GemRequirement("~> 1.0").for_lockfile() == " (~> 1.0)"
    assert GemRequirement(">= 1.0.1", "~> 1.0").for_lockfile() == " (~> 1.0, >= 1.0.1)"
    duped = GemRequirement("= 1.0", ["=", GemVersion("1.0")])
    assert duped.for_lockfile() == " (= 1.0)"


def test_parse():
    assert GemRequirement.parse("  1") == GemConstraint("=", GemVersion(1))
    assert GemRequirement.parse("= 1") == GemConstraint("=", GemVersion(1))
    assert GemRequirement.parse("> 1") == GemConstraint(">", GemVersion(1))
    assert GemRequirement.parse("=\n1") == GemConstraint("=", GemVersion(1))
    assert GemRequirement.parse("1.0") == GemConstraint("=", GemVersion(1))

    assert GemRequirement.parse(GemVersion("2")) == GemConstraint("=", GemVersion(2))


def test_parse_deduplication():
    assert GemRequirement.parse("~> 1") == GemConstraint("~>", GemVersion("1"))


def test_parse_bad():
    bads = [
        None,
        "",
        "! 1",
        "= junk",
        "1..2",
    ]
    for bad in bads:
        try:
            GemRequirement.parse(bad)
            raise Exception("exception not raised")
        except InvalidRequirementError:
            pass


def test_prerelease_eh():
    r = GemVersion("1")
    assert not r.prerelease()

    r = GemVersion("1.a")
    assert r.prerelease()

    r = GemVersion("1.x")
    assert r.prerelease()


def test_satisfied_by_eh_bang_equal():
    r = GemRequirement("!= 1.2")

    assert_satisfied_by("1.1", r)
    refute_satisfied_by("1.2", r)
    assert_satisfied_by("1.3", r)


def test_satisfied_by_eh_blank():
    r = GemRequirement("1.2")

    refute_satisfied_by("1.1", r)
    assert_satisfied_by("1.2", r)
    refute_satisfied_by("1.3", r)


def test_satisfied_by_eh_equal():
    r = GemRequirement("= 1.2")

    refute_satisfied_by("1.1", r)
    assert_satisfied_by("1.2", r)
    refute_satisfied_by("1.3", r)


def test_satisfied_by_eh_gt():
    r = GemRequirement("> 1.2")

    refute_satisfied_by("1.1", r)
    refute_satisfied_by("1.2", r)
    assert_satisfied_by("1.3", r)


def test_satisfied_by_eh_gte():
    r = GemRequirement(">= 1.2")

    refute_satisfied_by("1.1", r)
    assert_satisfied_by("1.2", r)
    assert_satisfied_by("1.3", r)


def test_satisfied_by_eh_list():
    r = GemRequirement("> 1.1", "< 1.3")

    refute_satisfied_by("1.1", r)
    assert_satisfied_by("1.2", r)
    refute_satisfied_by("1.3", r)


def test_satisfied_by_eh_lt():
    r = GemRequirement("< 1.2")

    assert_satisfied_by("1.1", r)
    refute_satisfied_by("1.2", r)
    refute_satisfied_by("1.3", r)


def test_satisfied_by_eh_lte():
    r = GemRequirement("<= 1.2")

    assert_satisfied_by("1.1", r)
    assert_satisfied_by("1.2", r)
    refute_satisfied_by("1.3", r)


def test_satisfied_by_eh_tilde_gt():
    r = GemRequirement("~> 1.2")

    refute_satisfied_by("1.1", r)
    assert_satisfied_by("1.2", r)
    assert_satisfied_by("1.3", r)


def test_satisfied_by_eh_tilde_gt_v0():
    r = GemRequirement("~> 0.0.1")

    refute_satisfied_by("0.1.1", r)
    assert_satisfied_by("0.0.2", r)
    assert_satisfied_by("0.0.1", r)


def test_satisfied_by_eh_good_problematic():
    assert_satisfied_by("0.0.1.0", "> 0.0.0.1")


def test_satisfied_by_eh_good():
    assert_satisfied_by("0.2.33", "= 0.2.33")
    assert_satisfied_by("0.2.34", "> 0.2.33")
    assert_satisfied_by("1.0", "= 1.0")
    assert_satisfied_by("1.0.0", "= 1.0")
    assert_satisfied_by("1.0", "= 1.0.0")
    assert_satisfied_by("1.0", "1.0")
    assert_satisfied_by("1.8.2", "> 1.8.0")
    assert_satisfied_by("1.112", "> 1.111")
    assert_satisfied_by("0.2", "> 0.0.0")
    assert_satisfied_by("0.0.0.0.0.2", "> 0.0.0")
    assert_satisfied_by("10.3.2", "> 9.3.2")
    assert_satisfied_by("1.0.0.0", "= 1.0")
    assert_satisfied_by("10.3.2", "!= 9.3.4")
    assert_satisfied_by("10.3.2", "> 9.3.2")
    assert_satisfied_by(" 9.3.2", ">= 9.3.2")
    assert_satisfied_by("9.3.2 ", ">= 9.3.2")
    assert_satisfied_by("", "= 0")
    assert_satisfied_by("", "< 0.1")
    assert_satisfied_by("  ", "< 0.1 ")
    assert_satisfied_by("", " <  0.1")
    assert_satisfied_by("  ", "> 0.a ")
    assert_satisfied_by("", " >  0.a")
    assert_satisfied_by("3.1", "< 3.2.rc1")

    assert_satisfied_by("3.2.0", "> 3.2.0.rc1")
    assert_satisfied_by("3.2.0.rc2", "> 3.2.0.rc1")

    assert_satisfied_by("3.0.rc2", "< 3.0")
    assert_satisfied_by("3.0.rc2", "< 3.0.0")
    assert_satisfied_by("3.0.rc2", "< 3.0.1")

    assert_satisfied_by("3.0.rc2", "> 0")

    assert_satisfied_by("5.0.0.rc2", "~> 5.a")
    refute_satisfied_by("5.0.0.rc2", "~> 5.x")

    assert_satisfied_by("5.0.0", "~> 5.a")
    assert_satisfied_by("5.0.0", "~> 5.x")


def test_illformed_requirements():
    bads = [">>> 1.3.5", "> blah"]
    for bad in bads:
        try:
            GemRequirement.parse(bad)
            raise Exception("exception not raised")
        except InvalidRequirementError:
            pass


def test_satisfied_by_eh_boxed():
    refute_satisfied_by("1.3", "~> 1.4")
    assert_satisfied_by("1.4", "~> 1.4")
    assert_satisfied_by("1.5", "~> 1.4")
    refute_satisfied_by("2.0", "~> 1.4")

    refute_satisfied_by("1.3", "~> 1.4.4")
    refute_satisfied_by("1.4", "~> 1.4.4")
    assert_satisfied_by("1.4.4", "~> 1.4.4")
    assert_satisfied_by("1.4.5", "~> 1.4.4")
    refute_satisfied_by("1.5", "~> 1.4.4")
    refute_satisfied_by("2.0", "~> 1.4.4")

    refute_satisfied_by("1.1.pre", "~> 1.0.0")
    refute_satisfied_by("1.1.pre", "~> 1.1")
    refute_satisfied_by("2.0.a", "~> 1.0")
    refute_satisfied_by("2.0.a", "~> 2.0")

    refute_satisfied_by("0.9", "~> 1")
    assert_satisfied_by("1.0", "~> 1")
    assert_satisfied_by("1.1", "~> 1")
    refute_satisfied_by("2.0", "~> 1")


def test_satisfied_by_eh_multiple():
    req = [">= 1.4", "<= 1.6", "!= 1.5"]

    refute_satisfied_by("1.3", req)
    assert_satisfied_by("1.4", req)
    refute_satisfied_by("1.5", req)
    assert_satisfied_by("1.6", req)
    refute_satisfied_by("1.7", req)
    refute_satisfied_by("2.0", req)


def test_satisfied_by_boxed():
    refute_satisfied_by("1.3", "~> 1.4")
    assert_satisfied_by("1.4", "~> 1.4")
    assert_satisfied_by("1.4.0", "~> 1.4")
    assert_satisfied_by("1.5", "~> 1.4")
    refute_satisfied_by("2.0", "~> 1.4")

    refute_satisfied_by("1.3", "~> 1.4.4")
    refute_satisfied_by("1.4", "~> 1.4.4")
    assert_satisfied_by("1.4.4", "~> 1.4.4")
    assert_satisfied_by("1.4.5", "~> 1.4.4")
    refute_satisfied_by("1.5", "~> 1.4.4")
    refute_satisfied_by("2.0", "~> 1.4.4")


def test_satisfied_by_explicitly_bounded():
    req = [">= 1.4.4", "< 1.5"]

    assert_satisfied_by("1.4.5", req)
    assert_satisfied_by("1.5.0.rc1", req)
    refute_satisfied_by("1.5.0", req)

    req = [">= 1.4.4", "< 1.5.a"]

    assert_satisfied_by("1.4.5", req)
    refute_satisfied_by("1.5.0.rc1", req)
    refute_satisfied_by("1.5.0", req)


def test_bad():
    refute_satisfied_by("", "> 0.1")
    refute_satisfied_by("1.2.3", "!= 1.2.3")
    refute_satisfied_by("1.2.003.0.0", "!= 1.02.3")
    refute_satisfied_by("4.5.6", "< 1.2.3")
    refute_satisfied_by("1.0", "> 1.1")
    refute_satisfied_by("", "= 0.1")
    refute_satisfied_by("1.1.1", "> 1.1.1")
    refute_satisfied_by("1.2", "= 1.1")
    refute_satisfied_by("1.40", "= 1.1")
    refute_satisfied_by("1.3", "= 1.40")
    refute_satisfied_by("9.3.3", "<= 9.3.2")
    refute_satisfied_by("9.3.1", ">= 9.3.2")
    refute_satisfied_by("9.3.03", "<= 9.3.2")
    refute_satisfied_by("1.0.0.1", "= 1.0")


def test_equal_with_multiple_versions():
    r1 = GemRequirement("1.0", "2.0")
    r2 = GemRequirement("2.0", "1.0")
    assert r1 == r2

    r1 = GemRequirement("1.0", "2.0", "3.0")
    r2 = GemRequirement("3.0", "1.0", "2.0")
    assert r1 == r2


def test_equivalent_requirements_are_equal():
    refute_requirement_equal("= 1.2", "= 1.3")
    refute_requirement_equal("= 1.3", "= 1.2")

    refute_requirement_equal("~> 1.3", "~> 1.3.0")
    refute_requirement_equal("~> 1.3.0", "~> 1.3")

    assert_requirement_equal(["> 2", "~> 1.3", "~> 1.3.1"], ["~> 1.3.1", "~> 1.3", "> 2"])

    assert_requirement_equal(["> 2", "~> 1.3"], ["> 2.0", "~> 1.3"])
    assert_requirement_equal(["> 2.0", "~> 1.3"], ["> 2", "~> 1.3"])

    assert_requirement_equal("= 1.0", "= 1.0.0")
    assert_requirement_equal("= 1.1", "= 1.1.0")
    assert_requirement_equal("= 1", "= 1.0.0")

    assert_requirement_equal("1.0", "1.0.0")
    assert_requirement_equal("1.1", "1.1.0")
    assert_requirement_equal("1", "1.0.0")


def assert_requirement_equal(expected, actual):
    # Assert that two requirements are equal. Handles GemRequirements,
    # strings, arrays, numbers, and versions.
    assert GemRequirement.create(actual) == GemRequirement.create(expected)


def refute_requirement_equal(unexpected, actual):
    # Refute the assumption that two requirements are equal.
    assert GemRequirement.create(actual) != GemRequirement.create(unexpected)
    assert GemRequirement.create(unexpected) != GemRequirement.create(actual)


def assert_satisfied_by(version, requirement):
    # Assert that +version+ satisfies +requirement+.
    if not isinstance(requirement, GemRequirement):
        requirement = GemRequirement.create(requirement)
    assert requirement.satisfied_by(GemVersion(version))


def refute_satisfied_by(version, requirement):
    # Refute the assumption that +version+ satisfies +requirement+.
    if not isinstance(requirement, GemRequirement):
        requirement = GemRequirement.create(requirement)
    assert not requirement.satisfied_by(GemVersion(version))
