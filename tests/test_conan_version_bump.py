#
# Copyright (c) 2019 JFrog LTD
# SPDX-License-Identifier: MIT
#
# Visit https://aboutcode.org and https://github.com/aboutcode-org/univers for support and download.

import pytest

from univers.versions import ConanVersion

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
