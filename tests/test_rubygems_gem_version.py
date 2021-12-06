
#
# Copyright (c) Chad Fowler, Rich Kilmer, Jim Weirich and others.
# Portions copyright (c) Engine Yard and Andre ArkoFacebook, Inc. and its affiliates.
#
# SPDX-License-Identifier: MIT
#
# Originally from https://github.com/rubygems/rubygems

from univers.gem import GemVersion


def assert_equal(expected, result):
    assert result == expected


def assert_bumped_version_equal(expected, unbumped):
  # Assert that bumping the +unbumped+ version yields the +expected+.

  assert_version_equal(expected, GemVersion(unbumped).bump())


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


def test_eql_eh():
  assert_version_eql("1.2", "1.2")
  refute_version_eql("1.2", "1.2.0")
  refute_version_eql("1.2", "1.3")
  refute_version_eql("1.2.b1", "1.2.b.1")


def test_equals2():
  assert_version_equal("1.2", "1.2")
  refute_version_equal("1.2", "1.3")
  assert_version_equal("1.2.b1", "1.2.b.1")


  # REVISIT: consider removing as too impl-bound
def test_hash():
  assert  GemVersion("1.2").hash == GemVersion("1.2").hash
  assert GemVersion("1.2").hash != GemVersion("1.3").hash
  assert GemVersion("1.2").hash == GemVersion("1.2.0").hash
  assert GemVersion("1.2.pre.1").hash == GemVersion("1.2.0.pre.1.0").hash


def test_initialize():
  for good in ["1.0", "1.0 ", " 1.0 ", "1.0\n", "\n1.0\n", "1.0"]:
    assert_version_equal("1.0", good)

  assert_version_equal("1", 1)


def test_initialize_invalid():
  invalid_versions = [
    "junk",
    "1.0\n2.0"
    "1..2",
    "1.2\ 3.4",
  ]

  # DON'T TOUCH THIS WITHOUT CHECKING CVE-2013-4287
  invalid_versions += ["2.3422222.222.222222222.22222.ads0as.dasd0.ddd2222.2.qd3e."]

  for invalid in invalid_versions:
    try:
      GemVersion(invalid)
      raise Exception("exception not raised")
    except ValueError:
      pass


def test_empty_version():
  for empty in ["", "   ", " "]:
    assert_equal("0", GemVersion(empty).version)


def test_prerelease():
  assert_prerelease("1.2.0.a")
  assert_prerelease("2.9.b")
  assert_prerelease("22.1.50.0.d")
  assert_prerelease("1.2.d.42")

  assert_prerelease('1.A')

  assert_prerelease('1-1')
  assert_prerelease('1-a')

  refute_prerelease("1.2.0")
  refute_prerelease("2.9")
  refute_prerelease("22.1.50.0")


def test_release():
  assert_release_equal("1.2.0", "1.2.0.a")
  assert_release_equal("1.1", "1.1.rc10")
  assert_release_equal("1.9.3", "1.9.3.alpha.5")
  assert_release_equal("1.9.3", "1.9.3")


def test_spaceship():

  def cmp(a, b):
      return a.__cmp__(b)

  # Ruby spaceship  <=>  is the same as Python legacy cmp()
  assert_equal(0, cmp(GemVersion("1.0")       , GemVersion("1.0.0")))
  assert_equal(1, cmp(GemVersion("1.0")       , GemVersion("1.0.a")))
  assert_equal(1, cmp(GemVersion("1.8.2")     , GemVersion("0.0.0")))
  assert_equal(1, cmp(GemVersion("1.8.2")     , GemVersion("1.8.2.a")))
  assert_equal(1, cmp(GemVersion("1.8.2.b")   , GemVersion("1.8.2.a")))
  assert_equal(-1, cmp(GemVersion("1.8.2.a") , GemVersion("1.8.2")))
  assert_equal(1, cmp(GemVersion("1.8.2.a10") , GemVersion("1.8.2.a9")))
  assert_equal(0, cmp(GemVersion("")          , GemVersion("0")))

  assert_equal(0, cmp(GemVersion("0.beta.1")  , GemVersion("0.0.beta.1")))
  assert_equal(-1, cmp(GemVersion("0.0.beta")  , GemVersion("0.0.beta.1")))
  assert_equal(-1, cmp(GemVersion("0.0.beta")  , GemVersion("0.beta.1")))

  assert_equal(-1, cmp(GemVersion("5.a") , GemVersion("5.0.0.rc2")))
  assert_equal(1, cmp(GemVersion("5.x") , GemVersion("5.0.0.rc2")))

  assert_nil(cmp(GemVersion("1.0") , "whatever"))


def test_approximate_recommendation():
  assert_approximate_equal("~> 1.0", "1")
  assert_approximate_satisfies_itself("1")

  assert_approximate_equal("~> 1.0", "1.0")
  assert_approximate_satisfies_itself("1.0")

  assert_approximate_equal("~> 1.2", "1.2")
  assert_approximate_satisfies_itself("1.2")

  assert_approximate_equal("~> 1.2", "1.2.0")
  assert_approximate_satisfies_itself("1.2.0")

  assert_approximate_equal("~> 1.2", "1.2.3")
  assert_approximate_satisfies_itself("1.2.3")

  assert_approximate_equal("~> 1.2.a", "1.2.3.a.4")
  assert_approximate_satisfies_itself("1.2.3.a.4")

  assert_approximate_equal("~> 1.9.a", "1.9.0.dev")
  assert_approximate_satisfies_itself("1.9.0.dev")


def test_to_s():
  assert GemVersion("5.2.4").to_string() == "5.2.4"


def test_semver():
  assert_less_than("1.0.0-alpha", "1.0.0-alpha.1")
  assert_less_than("1.0.0-alpha.1", "1.0.0-beta.2")
  assert_less_than("1.0.0-beta.2", "1.0.0-beta.11")
  assert_less_than("1.0.0-beta.11", "1.0.0-rc.1")
  assert_less_than("1.0.0-rc1", "1.0.0")
  assert_less_than("1.0.0-1", "1")


def test_segments():
  # modifying the segments of a version should not affect the segments of the cached version object
  ver = GemVersion('9.8.7')
  secondseg = ver.segments[2]
  secondseg += 1

  refute_version_equal("9.8.8", "9.8.7")
  assert_equal([9, 8, 7], GemVersion("9.8.7").segments)


def test_canonical_segments():
  assert_equal([1], GemVersion("1.0.0").canonical_segments)
  assert_equal([1, "a", 1], GemVersion("1.0.0.a.1.0").canonical_segments)
  assert_equal([1, 2, 3, "pre", 1], GemVersion("1.2.3-1").canonical_segments)


def test_frozen_version():
  ver = GemVersion('1.test')
  assert_less_than(ver, GemVersion('1'))
  assert_version_equal(GemVersion('1'), v.release)
  assert_version_equal(GemVersion('2'), v.bump)


def assert_prerelease(version):
  # Asserts that +version+ is a prerelease.
  assert GemVersion(version).prerelease(), "#{version} is a prerelease"


def assert_approximate_equal(expected, version):
  # Assert that +expected+ is the "approximate" recommendation for +version+.
  assert GemVersion(version).approximate_recommendation() == expected


def assert_approximate_satisfies_itself(version):
  # Assert that the "approximate" recommendation for +version+ satisfies +version+.
  gem_version = GemVersion(version)
  req = GemRequirement(gem_version.approximate_recommendation())
  assert req.satisfied_by(gem_version)


def assert_release_equal(release, version):
  # Assert that +release+ is the correct non-prerelease +version+.
  assert_version_equal(release, GemVersion(version).release)


def assert_version_equal(expected, actual):
  # Assert that two versions are equal. Handles strings or
  # Gem::Version instances.
  assert GemVersion(expected) == GemVersion(actual)


def assert_version_eql(first, second):
  # Assert that two versions are eql?. Checks both directions.
  first, second = GemVersion(first), GemVersion(second)
  assert first == second, "#{first} is eql? #{second}"
  assert second == first, "#{second} is eql? #{first}"


def assert_less_than(left, right):
  assert GemVersion(left) < GemVersion(right)


def refute_prerelease(version):
  # Refute the assumption that +version+ is a prerelease.
  assert not GemVersion(version).prerelease()


def refute_version_eql(first, second):
  # Refute the assumption that two versions are eql?. Checks both
  # directions.
  first = GemVersion(first)
  second = GemVersion(second)
  assert first != second
  assert second != first


def refute_version_equal(unexpected, actual):
  # Refute the assumption that the two versions are equal?.
  assert GemVersion(unexpected) != GemVersion(actual)
