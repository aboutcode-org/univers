import pytest

from univers.version_range import CargoVersionRange
from univers.version_range import InvalidVersionRange
from univers.versions import CargoVersion

values = [
    # https://doc.rust-lang.org/cargo/reference/specifying-dependencies.html
    # caret
    ["^1.2.3", [[]], ["1.2.3"], []],
    # tilde
    ["~1.2.3", [[">=", "1.2.3"], ["<", "1.3.0"]], ["1.2.4"], ["2.0.1"]],
    ["~1.2", [[">=", "1.2.0"], ["<", "1.3.0"]], ["1.2.5"], ["1.3.1"]],
    [
        "~1",
        [[">=", "1.0.0"], ["<", "2.0.0"]],
        ["1.3.0", "1.8.1"],
        ["2.1.0", "2.2"],
    ],  # tilde increment the major
    # wildcard
    ["*", [[">=", "0.0.0"]], ["1.0.0", "2.0.0"], []],
    ["1.*", [], ["1.0.0"], ["2"]],
    ["1.2.*", [[">=", "1.2.0"], ["<", "1.3.0"]], ["1.2", "1.2.1"], ["2.1.0", "2.2"]],
    # https://github.com/dtolnay/semver/blob/master/tests/test_version_req.rs :
    # test_basic
    [
        "^1.0.0",
        [[]],
        ["1.0.0", "1.1.0", "1.0.1"],
        ["0.9.9", "0.10.0", "0.1.0", "1.0.0-pre", "1.0.1-pre"],
    ],
    # test_exact
    [
        "=1.0.0",
        [["=", "1.0.0"]],
        ["1.0.0"],
        ["1.0.1", "0.9.9", "0.10.0", "0.1.0", "1.0.0-pre"],
    ],
    ["=0.9.0", [["=", "0.9.0"]], ["0.9.0"], ["0.9.1", "1.9.0", "0.0.9", "0.9.0-pre"]],
    ["=0.0.2", [["=", "0.0.2"]], ["0.0.2"], ["0.0.1", "0.0.3", "0.0.2-pre"]],
    [
        "=0.1.0-beta2.a",
        [["=", "0.1.0-beta2.a"]],
        ["0.1.0-beta2.a"],
        ["0.9.1", "0.1.0", "0.1.1-beta2.a", "0.1.0-beta2"],
    ],
    # https://github.com/dtolnay/semver/blob/master/tests/test_version_req.rs#L73
    ["=0.1.0+meta", [["=", "0.1.0+meta"]], ["0.1.0", "0.1.0+meta", "0.1.0+any"], []],
    # test_greater_than
    [
        ">= 1.0.0",
        [[]],
        ["1.0.0", "2.0.0"],
        ["0.1.0", "0.0.1", "1.0.0-pre", "2.0.0-pre"],
    ],
    [
        ">= 2.1.0-alpha2",
        [[]],
        ["2.1.0-alpha2", "2.1.0-alpha3", "2.1.0", "3.0.0"],
        ["2.0.0", "2.1.0-alpha1", "2.0.0-alpha2", "3.0.0-alpha2"],
    ],
    # test_less_than
    [
        "<1.0.0",
        [[]],
        ["0.1.0", "0.0.1"],
        ["1.0.0", "1.0.0-beta", "1.0.1", "0.9.9-alpha"],
    ],
    [
        "<= 2.1.0-alpha2",
        [[]],
        ["2.1.0-alpha2", "2.1.0-alpha1", "2.0.0", "1.0.0"],
        ["2.1.0", "2.2.0-alpha1", "2.0.0-alpha2", "1.0.0-alpha2"],
    ],
    [
        ">1.0.0-alpha, <1.0.0",
        [[">", "2.1.0-alpha2"], ["<", "1.0.0"]],
        ["1.0.0-beta"],
        [],
    ],
    [">1.0.0-alpha, <1.0", [[">", "1.0.0-alpha"], ["<", "1.0"]], ["1.0.0-beta"], []],
    [">1.0.0-alpha, <1", [[">", "1.0.0-alpha"], ["<", "1"]], ["1.0.0-beta"], []],
    # test_multiple
    ["> 0.0.9, <= 2.5.3", [[]], ["0.0.10", "1.0.0", "2.5.3"], ["0.0.8", "2.5.4"]],
    ["^0.3.0, ^0.4.0", [[]], [], ["0.0.8", "0.3.0", "0.4.0"]],
    ["<=0.2.0, >=0.5.0", [[]], [], ["0.0.8", "0.3.0", "0.5.1"]],
    ["^0.1.0, ^0.1.4, ^0.1.6", [[]], ["0.1.6", "0.1.9"], ["0.1.0", "0.1.4", "0.2.0"]],
    [
        ">=0.5.1-alpha3, <0.6",
        [[[">", "0.5.1-alpha3"], ["=", "0.5.1-alpha3"], ["<", "0.6"]]],
        ["0.5.1-alpha3", "0.5.1-alpha4", "0.5.1-beta", "0.5.1", "0.5.5"],
        ["0.5.1-alpha1", "0.5.2-alpha3", "0.5.5-pre", "0.5.0-pre"],
    ],
    # test_tilde
    ["~1", [[]], ["1.0.0", "1.0.1", "1.1.1"], ["0.9.1", "2.9.0", "0.0.9"]],
    ["~1.2", [[]], ["1.2.0", "1.2.1"], ["1.1.1", "1.3.0", "0.0.9"]],
    ["~1.2.2", [[]], ["1.2.2", "1.2.4"], ["1.2.1", "1.9.0", "1.0.9", "2.0.1", "0.1.3"]],
    [
        "~1.2.3-beta.2",
        [[]],
        ["1.2.3", "1.2.4", "1.2.3-beta.2", "1.2.3-beta.4"],
        ["1.3.3", "1.1.4", "1.2.3-beta.1", "1.2.4-beta.2"],
    ],
    # test_caret
    [
        "^1",
        [[]],
        ["1.1.2", "1.1.0", "1.2.1", "1.0.1"],
        ["0.9.1", "2.9.0", "0.1.4", "1.0.0-beta1", "0.1.0-alpha", "1.0.1-pre"],
    ],
    ["^1.1", [[]], ["1.1.2", "1.1.0", "1.2.1"], ["0.9.1", "2.9.0", "1.0.1", "0.1.4"]],
    [
        "^1.1.2",
        [[]],
        ["1.1.2", "1.1.4", "1.2.1"],
        [
            "0.9.1",
            "2.9.0",
            "1.1.1",
            "0.0.1",
            "1.1.2-alpha1",
            "1.1.3-alpha1",
            "2.9.0-alpha1",
        ],
    ],
    [
        "^0.1.2",
        [[]],
        ["0.1.2", "0.1.4"],
        ["0.9.1", "2.9.0", "1.1.1", "0.0.1", "0.1.2-beta", "0.1.3-alpha", "0.2.0-pre"],
    ],
    [
        "^0.5.1-alpha3",
        [[]],
        [
            "0.5.1-alpha3",
            "0.5.1-alpha4",
            "0.5.1-beta",
            "0.5.1",
            "0.5.5",
        ],
        ["0.5.1-alpha1", "0.5.2-alpha3", "0.5.5-pre", "0.5.0-pre", "0.6.0"],
    ],
    ["^0.0.2", [[]], ["0.0.2"], ["0.9.1", "2.9.0", "1.1.1", "0.0.1", "0.1.4"]],
    ["^0.0", [[]], ["0.0.2", "0.0.0"], ["0.9.1", "2.9.0", "1.1.1", "0.0.1", "0.1.4"]],
    ["^0", [[]], ["0.9.1", "0.0.2", "0.0.0"], ["2.9.0", "1.1.1"]],
    [
        "^1.4.2-beta.5",
        [[]],
        ["1.4.2", "1.4.3", "1.4.2-beta.5", "1.4.2-beta.6", "1.4.2-c"],
        ["0.9.9", "2.0.0", "1.4.2-alpha", "1.4.2-beta.4", "1.4.3-beta.5"],
    ],
    # test_wildcard
    # https://github.com/dtolnay/semver/blob/master/tests/test_version_req.rs#L272
    ["*", [[]], ["0.9.1", "2.9.0", "0.0.9", "1.0.1", "1.1.1"], ["1.0.0-pre"]],
    ["1.*", [[]], ["1.2.0", "1.2.1", "1.1.1", "1.3.0"], ["0.0.9", "1.2.0-pre"]],
    [
        "1.2.*",
        [[]],
        ["1.2.0", "1.2.2", "1.2.4"],
        ["1.9.0", "1.0.9", "2.0.1", "0.1.3", "1.2.2-pre"],
    ],
    # test_pre
    ["=2.1.1-really.0", [[]], ["2.1.1-really.0"], []],
    # test_cargo3202
    ["0.*.*", [[]], ["0.5.0"], []],
]


error_list = [
    "> 0.1.0,",
    "> 0.3.0, ,",
    "1.2.3 - 2.3.4",
    "> 0.0.9 <= 2.5.3",
    "=1.2.3 || =2.3.4",
    "1.1 || =1.2.3",
    "6.* || 8.* || >= 10.*",
    ">= >= 0.0.2",
    ">== 0.0.2",
    "a.0.0",
    "1.0.0-",
    ">=",
    "*.1",
    "1.*.1",
    ">=1.*.1",
    "*, 0.20.0-any",
    "0.20.0-any, *" "0.20.0-any, *, 1.0",
]


@pytest.mark.parametrize("version_range, conditions, versions_in, versions_out", values)
def test_range(version_range, conditions, versions_in, versions_out):
    r = CargoVersionRange.from_native(version_range)
    # TODO test Version Constraints

    for v in versions_in:
        assert CargoVersion(v) in r

    for v in versions_out:
        assert CargoVersion(v) not in r


def test_error():
    for version_range in error_list:
        with pytest.raises(InvalidVersionRange):
            CargoVersionRange.from_native(version_range)