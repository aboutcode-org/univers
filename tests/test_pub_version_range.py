import pytest

from univers.version_range import InvalidVersionRange
from univers.version_range import PubVersionRange
from univers.versions import DartVersion

values = [
    # https://github.com/dart-lang/pub_semver/blob/master/test/version_range_test.dart
    # version must be greater than min
    [">1.2.3", [[]], ["1.3.3", "2.3.3"], ["1.2.2", "1.2.3"]],
    # version must be min or greater if includeMin
    [">=1.2.3", [[]], ["1.2.3", "1.3.3"], ["1.2.2"]],
    # pre-release versions of inclusive min are excluded
    # version must be less than max
    ["<2.3.4", [[]], ["2.3.3"], ["2.3.4", "2.4.3"]],
    # pre-release versions of non-pre-release max are excluded
    # pre-release versions of non-pre-release max are included if min is a pre-release of the same version
    # pre-release versions of pre-release max are included
    # version must be max or less if includeMax
    [">1.2.3 <=2.3.4", [[]], ["2.3.3", "2.3.4", "2.3.4-dev"], ["2.4.3"]],
    # has no min if one was not set
    ["<1.2.3", [[]], ["0.0.0"], ["1.2.3"]],
    # has no max if one was not set
    [">1.2.3", [[]], ["1.3.3", "999.3.3"], ["1.2.3"]],
]


@pytest.mark.parametrize("version_range, conditions, versions_in, versions_out", values)
def test_range(version_range, conditions, versions_in, versions_out):
    r = PubVersionRange.from_native(version_range)

    for v in versions_in:
        assert DartVersion(v) in r

    for v in versions_out:
        assert DartVersion(v) not in r
