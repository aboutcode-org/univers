import pytest

from univers.versions import DartVersion


def test_equal():
    assert DartVersion("1.2.3") == DartVersion("1.2.3")
    assert DartVersion("1.4.5-dev") == DartVersion("1.4.5-dev")

    # test cases from https://github.com/dart-lang/pub_semver/blob/master/test/version_test.dart
    assert DartVersion("01.2.3") == DartVersion("1.2.3")
    assert DartVersion("1.02.3") == DartVersion("1.2.3")
    assert DartVersion("1.2.03") == DartVersion("1.2.3")
    # assert DartVersion("1.2.3-01") == DartVersion("1.2.3-1")
    # assert DartVersion("1.2.3+01") == DartVersion("1.2.3+1")


def test_compare():
    versions = [
        "1.0.0-alpha",
        "1.0.0-alpha.1",
        "1.0.0-beta.2",
        "1.0.0-beta.11",
        "1.0.0-rc.1",
        "1.0.0-rc.1+build.1",
        "1.0.0",
        "1.0.0+0.3.7",
        "1.3.7+build",
        #'1.3.7+build.2.b8f12d7',
        "1.3.7+build.11.e0f985a",
        "2.0.0",
        "2.1.0",
        "2.2.0",
        "2.11.0",
        "2.11.1",
    ]

    for i in range(len(versions)):
        for j in range(len(versions)):
            a = DartVersion(versions[i])
            b = DartVersion(versions[j])
            assert (a < b) == (i < j)
            assert (a <= b) == (i <= j)
            assert (a > b) == (i > j)
            assert (a >= b) == (i >= j)
            assert (a == b) == (i == j)
            assert (a != b) == (i != j)


def test_next_major():
    assert DartVersion(DartVersion("1.2.3").next_major().string) == DartVersion("2.0.0")
    assert DartVersion(DartVersion("1.1.4").next_major().string) == DartVersion("2.0.0")
    assert DartVersion(DartVersion("2.0.0").next_major().string) == DartVersion("3.0.0")
    assert DartVersion(DartVersion("1.2.3-dev").next_major().string) == DartVersion(
        "2.0.0"
    )
    assert DartVersion(DartVersion("2.0.0-dev").next_major().string) == DartVersion(
        "2.0.0"
    )
    assert DartVersion(DartVersion("1.2.3+1").next_major().string) == DartVersion(
        "2.0.0"
    )


def test_next_minor():
    assert DartVersion(DartVersion("1.2.3").next_minor().string) == DartVersion("1.3.0")
    assert DartVersion(DartVersion("1.1.4").next_minor().string) == DartVersion("1.2.0")
    assert DartVersion(DartVersion("1.3.0").next_minor().string) == DartVersion("1.4.0")
    assert DartVersion(DartVersion("1.2.3-dev").next_minor().string) == DartVersion(
        "1.3.0"
    )
    # assert DartVersion(DartVersion("1.3.0-dev").next_minor().string) == DartVersion("1.4.0")
    assert DartVersion(DartVersion("1.2.3+1").next_minor().string) == DartVersion(
        "1.3.0"
    )


def test_next_patch():
    assert DartVersion(DartVersion("1.2.3").next_patch().string) == DartVersion("1.2.4")
    assert DartVersion(DartVersion("2.0.0").next_patch().string) == DartVersion("2.0.1")
    assert DartVersion(DartVersion("1.2.4-dev").next_patch().string) == DartVersion(
        "1.2.4"
    )
    assert DartVersion(DartVersion("1.2.3+2").next_patch().string) == DartVersion(
        "1.2.4"
    )
