import pytest

from univers.conan.version import ConanVersion

values = [
    ["1.0.0", 0, "2.0.0"],
    ["1.1.0", 0, "2.0.0"],
    ["1.1.1-pre", 0, "2.0.0"],
    ["1.1.1", 1, "1.2.0"],
    ["1.1.1", 2, "1.1.2"],
]


@pytest.mark.parametrize("version, index, result", values)
def test_version_bump(version, index, result):
    r = ConanVersion(version)
    bumped = r.bump(index)
    assert bumped == result
