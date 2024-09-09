import pytest

from univers.versions import CargoVersion


def test_compare():
    """
    1.2.3  :=  >=1.2.3, <2.0.0
    1.2    :=  >=1.2.0, <2.0.0
    1      :=  >=1.0.0, <2.0.0
    0.2.3  :=  >=0.2.3, <0.3.0
    0.2    :=  >=0.2.0, <0.3.0
    0.0.3  :=  >=0.0.3, <0.0.4
    0.0    :=  >=0.0.0, <0.1.0
    0      :=  >=0.0.0, <1.0.0
    """

    assert CargoVersion("1.2.3") >= CargoVersion("1.2.3")
    assert CargoVersion("1.2.3") < CargoVersion("2.0.0")

    assert CargoVersion("1.2") >= CargoVersion("1.2.0")
    assert CargoVersion("1.2") < CargoVersion("2.0.0")

    assert CargoVersion("1") >= CargoVersion("1.0.0")
    assert CargoVersion("1") < CargoVersion("2.0.0")

    assert CargoVersion("0.2.3") >= CargoVersion("0.2.3")
    assert CargoVersion("0.2.3") < CargoVersion("0.3.0")

    assert CargoVersion("0.2") >= CargoVersion("0.2.0")
    assert CargoVersion("0.2") < CargoVersion("0.3.0")

    assert CargoVersion("0.0.3") >= CargoVersion("0.0.3")
    assert CargoVersion("0.0.3") < CargoVersion("0.0.4")

    assert CargoVersion("0.0") >= CargoVersion("0.0.0")
    assert CargoVersion("0.0") < CargoVersion("0.1.0")

    assert CargoVersion("0") >= CargoVersion("0.0.0")
    assert CargoVersion("0") < CargoVersion("1.0.0")


version_list = [
    ("1.2.3", 1, 2, 3, (), ()),
    ("1.2.3-alpha1", 1, 2, 3, ("alpha1",), ()),
    ("1.2.3+build5", 1, 2, 3, (), ("build5",)),
    ("1.2.3+5build", 1, 2, 3, (), ("5build",)),
    ("1.2.3-alpha1+build5", 1, 2, 3, ("alpha1",), ("build5",)),
    (
        "1.2.3-1.alpha1.9+build5.7.3aedf",
        1,
        2,
        3,
        (
            "1",
            "alpha1",
            "9",
        ),
        (
            "build5",
            "7",
            "3aedf",
        ),
    ),
    (
        "1.2.3-0a.alpha1.9+05build.7.3aedf",
        1,
        2,
        3,
        (
            "0a",
            "alpha1",
            "9",
        ),
        (
            "05build",
            "7",
            "3aedf",
        ),
    ),
    (
        "0.4.0-beta.1+0851523",
        0,
        4,
        0,
        (
            "beta",
            "1",
        ),
        ("0851523",),
    ),
    ("1.1.0-beta-10", 1, 1, 0, ("beta-10",), ()),
]


@pytest.mark.parametrize(
    "version, expected_major, expected_minor, expected_patch, expected_prerelease, expected_build",
    version_list,
)
def test_cargo(
    version, expected_major, expected_minor, expected_patch, expected_prerelease, expected_build
):
    # https://github.com/dtolnay/semver/blob/master/tests/test_version.rs :
    v1 = CargoVersion(version)
    assert v1.major == expected_major
    assert v1.minor == expected_minor
    assert v1.patch == expected_patch
    assert v1.prerelease == expected_prerelease
    assert v1.build == expected_build


def test_cargo1():
    assert CargoVersion("1.2.3") == CargoVersion("1.2.3")
    assert CargoVersion("1.2.3-alpha1") == CargoVersion("1.2.3-alpha1")
    assert CargoVersion("1.2.3+build.42") == CargoVersion("1.2.3+build.42")
    assert CargoVersion("1.2.3-alpha1+42") == CargoVersion("1.2.3-alpha1+42")
    assert CargoVersion("0.0.0") != CargoVersion("0.0.1")
    assert CargoVersion("0.0.0") != CargoVersion("0.1.0")
    assert CargoVersion("0.0.0") != CargoVersion("1.0.0")
    assert CargoVersion("1.2.3-alpha") != CargoVersion("1.2.3-beta")
    assert CargoVersion("1.2.3+23") != CargoVersion("1.2.3+42")

    assert CargoVersion("0.0.0") < CargoVersion("1.2.3-alpha2")
    assert CargoVersion("1.0.0") < CargoVersion("1.2.3-alpha2")
    assert CargoVersion("1.2.0") < CargoVersion("1.2.3-alpha2")
    assert CargoVersion("1.2.3-alpha1") < CargoVersion("1.2.3")
    assert CargoVersion("1.2.3-alpha1") < CargoVersion("1.2.3-alpha2")
    assert not (CargoVersion("1.2.3-alpha2") < CargoVersion("1.2.3-alpha2"))
    assert CargoVersion("1.2.3+23") < CargoVersion("1.2.3+42")

    assert CargoVersion("0.0.0") <= CargoVersion("1.2.3-alpha2")
    assert CargoVersion("1.0.0") <= CargoVersion("1.2.3-alpha2")
    assert CargoVersion("1.2.0") <= CargoVersion("1.2.3-alpha2")
    assert CargoVersion("1.2.3-alpha1") <= CargoVersion("1.2.3-alpha2")
    assert CargoVersion("1.2.3-alpha2") <= CargoVersion("1.2.3-alpha2")
    assert CargoVersion("1.2.3+23") <= CargoVersion("1.2.3+42")

    assert CargoVersion("1.2.3-alpha2") > CargoVersion("0.0.0")
    assert CargoVersion("1.2.3-alpha2") > CargoVersion("1.0.0")
    assert CargoVersion("1.2.3-alpha2") > CargoVersion("1.2.0")
    assert CargoVersion("1.2.3-alpha2") > CargoVersion("1.2.3-alpha1")
    assert CargoVersion("1.2.3") > CargoVersion("1.2.3-alpha2")
    assert not (CargoVersion("1.2.3-alpha2") > CargoVersion("1.2.3-alpha2"))
    assert not (CargoVersion("1.2.3+23") > CargoVersion("1.2.3+42"))

    assert CargoVersion("1.2.3-alpha2") >= CargoVersion("0.0.0")
    assert CargoVersion("1.2.3-alpha2") >= CargoVersion("1.0.0")
    assert CargoVersion("1.2.3-alpha2") >= CargoVersion("1.2.0")
    assert CargoVersion("1.2.3-alpha2") >= CargoVersion("1.2.3-alpha1")
    assert CargoVersion("1.2.3-alpha2") >= CargoVersion("1.2.3-alpha2")
    assert not (CargoVersion("1.2.3+23") >= CargoVersion("1.2.3+42"))
