#
# Copyright (c) nexB Inc. and others.
# SPDX-License-Identifier: Apache-2.0
#
# Visit https://aboutcode.org and https://github.com/aboutcode-org/univers for support and download.


import pytest

from univers.versions import AutoconfVersion
from univers.versions import InvalidVersion

def test_basic_comparison():
    # For Autoconfig 1.21.4 > 1.21.3
    assert AutoconfVersion("1.21.4") == AutoconfVersion("1.21.4")
    assert AutoconfVersion("1.21.4") > AutoconfVersion("1.21.3")
    assert AutoconfVersion("1.21.3") < AutoconfVersion("1.21.4")

def test_length_comparison():
    # For Autoconfig 3.15 < 3.15.6
    assert AutoconfVersion("3.15") < AutoconfVersion("3.15.6")
    assert AutoconfVersion("3.15.6") > AutoconfVersion("3.15")

def test_different_separators():
    # "-"" , "_" , "."" all should be treated as same
    assert AutoconfVersion("1-21-4") == AutoconfVersion("1_21_4") == AutoconfVersion("1.21.4")
    assert AutoconfVersion("1-21-4") > AutoconfVersion("1.21.3")

def test_empty_string():
    # Empty string should be considerd as version 0
    assert AutoconfVersion("").value == (0,)

def test_invalid_version():
    # Invalid strings should raise InvalidVersion
    with pytest.raises(InvalidVersion):
        AutoconfVersion("Invalid_version")

