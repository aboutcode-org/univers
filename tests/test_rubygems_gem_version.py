#
# Copyright (c) Chad Fowler, Rich Kilmer, Jim Weirich and others.
# Portions copyright (c) Engine Yard and Andre ArkoFacebook, Inc. and its affiliates.
#
# SPDX-License-Identifier: MIT
#
# Originally from https://github.com/rubygems/rubygems

from univers.gem import GemRequirement
from univers.gem import GemVersion
from univers.gem import InvalidVersionError


def assert_bumped_version_equal(expected, unbumped):
    # Assert that bumping the +unbumped+ version yields the +expected+.

    assert_version_eql(expected, GemVersion(unbumped).bump())


def test_bump():
    assert_bumped_version_equal("5.3", "5.2.4")


def test_bump_alpha():
    assert_bumped_version_equal("5.3", "5.2.4.a")


def test_bump_alphanumeric():
    assert_bumped_version_equal("5.3", "5.2.4.a10")


def test_bump_trailing_zeros():
    assert_bumped_version_equal("5.1", "5.0.0")


def test_bump_one_level():
    assert_bumped_version_equal("6", "5")


def test_eql_is_same():
    assert_version_eql("1.2", "1.2")
    assert_version_strict_equal("1.2", "1.2")

    refute_version_eql("1.2", "1.3")
    refute_version_strict_equal("1.2", "1.3")

    refute_version_strict_equal("1.2", "1.2.0")
    assert_version_eql("1.2", "1.2.0")

    assert_version_eql("1.2.b1", "1.2.b.1")
    refute_version_strict_equal("1.2.b1", "1.2.b.1")

    refute_version_strict_equal("1.2.pre.1", "1.2.0.pre.1.0")
    assert_version_eql("1.2.pre.1", "1.2.0.pre.1.0")


def test_initialize():
    for good in ["1.0", "1.0 ", " 1.0 ", "1.0\n", "\n1.0\n", "1.0"]:
        assert_version_eql("1.0", good)

    assert_version_eql("1", 1)


def test_initialize_invalid():
    invalid_versions = [
        "whatever",
        "junk",
        "1.0\n2.0" "1..2",
        "1.2\ 3.4",
    ]

    # DON'T TOUCH THIS WITHOUT CHECKING CVE-2013-4287
    invalid_versions += ["2.3422222.222.222222222.22222.ads0as.dasd0.ddd2222.2.qd3e."]

    for invalid in invalid_versions:
        try:
            GemVersion(invalid)
            raise Exception(f"exception not raised for: {invalid!r}")
        except InvalidVersionError:
            pass


def test_empty_version():
    assert GemVersion("").version == "0"
    assert GemVersion("  ").version == "0"
    assert GemVersion(" ").version == "0"


def test_prerelease():
    assert_prerelease("1.2.0.a")
    assert_prerelease("2.9.b")
    assert_prerelease("22.1.50.0.d")
    assert_prerelease("1.2.d.42")

    assert_prerelease("1.A")

    assert_prerelease("1-1")
    assert_prerelease("1-a")

    refute_prerelease("1.2.0")
    refute_prerelease("2.9")
    refute_prerelease("22.1.50.0")


def test_release():
    assert_release_equal("1.2.0", "1.2.0.a")
    assert_release_equal("1.1", "1.1.rc10")
    assert_release_equal("1.9.3", "1.9.3.alpha.5")
    assert_release_equal("1.9.3", "1.9.3")


def test_spaceship_cmp():
    def cmp(a, b):
        return a.__cmp__(b)

    # Ruby spaceship  <=>  is the same as Python legacy cmp()
    assert cmp(GemVersion("1.0"), GemVersion("1.0.0")) == 0
    assert cmp(GemVersion("1.0"), GemVersion("1.0.a")) == 1
    assert cmp(GemVersion("1.8.2"), GemVersion("0.0.0")) == 1
    assert cmp(GemVersion("1.8.2"), GemVersion("1.8.2.a")) == 1
    assert cmp(GemVersion("1.8.2.b"), GemVersion("1.8.2.a")) == 1
    assert cmp(GemVersion("1.8.2.a"), GemVersion("1.8.2")) == -1
    assert cmp(GemVersion("1.8.2.a10"), GemVersion("1.8.2.a9")) == 1
    assert cmp(GemVersion(""), GemVersion("0")) == 0
    assert cmp(GemVersion("0.beta.1"), GemVersion("0.0.beta.1")) == 0
    assert cmp(GemVersion("0.0.beta"), GemVersion("0.0.beta.1")) == -1
    assert cmp(GemVersion("0.0.beta"), GemVersion("0.beta.1")) == -1
    assert cmp(GemVersion("5.a"), GemVersion("5.0.0.rc2")) == -1
    assert cmp(GemVersion("5.x"), GemVersion("5.0.0.rc2")) == 1


def assert_version_satisfies_requirement(requirement, version):
    # Assert that +version+ satisfies the "approximate" ~> +requirement+.
    req = GemRequirement.create(requirement)
    ver = GemVersion(version)
    assert req.satisfied_by(ver)


def test_satisfies_requirement():
    assert_version_satisfies_requirement("~> 1.0", "1")
    assert_version_satisfies_requirement("~> 1.0", "1.0")
    assert_version_satisfies_requirement("~> 1.2", "1.2")
    assert_version_satisfies_requirement("~> 1.2", "1.2.0")
    assert_version_satisfies_requirement("~> 1.2", "1.2.3")
    assert_version_satisfies_requirement("~> 1.2.a", "1.2.3.a.4")
    assert_version_satisfies_requirement("~> 1.9.a", "1.9.0.dev")


def test_to_s():
    assert GemVersion("5.2.4").to_string() == "5.2.4"


def test_compare():
    assert GemVersion("0.0.1.0") > GemVersion("0.0.0.1")
    assert not GemVersion("0.0.1.0") < GemVersion("0.0.0.1")
    assert GemVersion("0.0.1.0") >= GemVersion("0.0.0.1")
    assert not GemVersion("0.0.1.0") <= GemVersion("0.0.0.1")


def test_semver():
    assert_less_than("1.0.0-alpha", "1.0.0-alpha.1")
    assert_less_than("1.0.0-alpha.1", "1.0.0-beta.2")
    assert_less_than("1.0.0-beta.2", "1.0.0-beta.11")
    assert_less_than("1.0.0-beta.11", "1.0.0-rc.1")
    assert_less_than("1.0.0-rc1", "1.0.0")
    assert_less_than("1.0.0-1", "1")


def test_segments():
    # modifying the segments of a version should not affect the segments of the cached version object
    ver = GemVersion("9.8.7")
    secondseg = ver.segments[2]
    secondseg += 1

    refute_version_eql("9.8.8", "9.8.7")
    assert GemVersion("9.8.7").segments == [9, 8, 7]


def test_split_segments():
    assert GemVersion("3.2.4-2").split_segments() == ([3, 2, 4], ["pre", 2])


def test_canonical_segments():
    assert GemVersion("1.0.0").canonical_segments == [1]
    assert GemVersion("1.0.0.a.1.0").canonical_segments == [1, "a", 1]
    assert GemVersion("1.2.3-1").canonical_segments == [1, 2, 3, "pre", 1]


def test_frozen_version():
    ver = GemVersion("1.test")
    assert_less_than(ver, GemVersion("1"))
    assert_version_eql(GemVersion("1"), ver.release())
    assert_version_eql(GemVersion("2"), ver.bump())


def assert_prerelease(version):
    # Asserts that +version+ is a prerelease.
    assert GemVersion(version).prerelease(), "#{version} is a prerelease"


def assert_release_equal(release, version):
    # Assert that +release+ is the correct non-prerelease +version+.
    assert_version_eql(release, GemVersion(version).release())


def assert_version_eql(first, second):
    # Assert that two versions are eql?. Checks both directions.
    first = GemVersion(first)
    second = GemVersion(second)
    assert first is not second
    assert first == second
    assert second == first


def refute_version_eql(first, second):
    # Refute the assumption that two versions are eql?. Checks both
    # directions.
    first = GemVersion(first)
    second = GemVersion(second)
    assert first is not second
    assert first != second
    assert second != first


def assert_version_strict_equal(first, second):
    # Assert that two versions are strictly equal
    first = GemVersion(first)
    second = GemVersion(second)
    assert first is not second
    assert first.equal_strictly(second)
    assert second.equal_strictly(first)


def refute_version_strict_equal(first, second):
    first = GemVersion(first)
    second = GemVersion(second)
    assert first is not second
    assert not first.equal_strictly(second)
    assert not second.equal_strictly(first)


def assert_less_than(left, right):
    assert GemVersion(left) < GemVersion(right)


def refute_prerelease(version):
    # Refute the assumption that +version+ is a prerelease.
    assert not GemVersion(version).prerelease()
