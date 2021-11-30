# -*- coding: utf-8 -*-
#
# Copyright (c) nexB Inc. and others.
# SPDX-License-Identifier: Apache-2.0
#
# Visit https://aboutcode.org and https://github.com/nexB/univers for support and download.

import json
import os
import re
import unittest

from univers.version_range import VersionRange
from unittest.case import expectedFailure


def create_test_function(
    description,
    vers,
    canonical_vers,
    is_invalid,
    scheme,
    constraints,
    test_func_prefix="test_vers_",
    **kwargs
):
    """
    Return a new (test function, test_name) where the test_function closed on
    test arguments. If is_error is True the tests are expected to raise an
    Exception.
    """
    if is_invalid:

        def test_vers(self):
            try:
                VersionRange.from_string(vers)
                self.fail("Should raise a ValueError")
            except ValueError:
                pass

            try:
                VersionRange.from_string(canonical_vers)
                self.fail("Should raise a ValueError")
            except ValueError:
                pass

    else:

        def test_vers(self):
            # parsing the test canonical `vers` then re-building a `vers` from these
            # parsed components should return the test canonical `vers`
            cano = VersionRange.from_string(vers)
            assert canonical_vers == cano.to_string()

            # parsing the test `vers` should return the components parsed from the
            # test canonical `vers`
            parsed = VersionRange.from_string(canonical_vers)
            assert str(cano) == str(parsed)

            # parsing the test `vers` then re-building a `vers` from these parsed
            # components should return the test canonical `vers`
            assert canonical_vers == parsed.to_string()

            # building a `vers` from the test ranges should return the test
            # canonical `vers`
            built = VersionRange(scheme, constraints)
            assert canonical_vers == built.to_string()

    # create a good function name for use in test discovery
    if not description:
        description = vers
    if is_invalid:
        test_func_prefix += "is_invalid_"
    test_name = python_safe_name(test_func_prefix + description)
    test_vers.__name__ = test_name
    test_vers.funcname = test_name
    return test_vers, test_name


def python_safe_name(s):
    """
    Return a name derived from string `s` safe to use as a Python function name.

    For example:
    >>> s = "not `\\a /`good` -safe name ??"
    >>> assert python_safe_name(s) == 'not_good_safe_name'
    """
    no_punctuation = re.compile(r"[\W_]", re.MULTILINE).sub
    s = s.lower()
    s = no_punctuation(" ", s)
    s = "_".join(s.split())
    return s


class VersTest(unittest.TestCase):
    pass


def build_tests(clazz=VersTest, test_file="test-suite-data.json"):
    """
    Dynamically build test methods for each vers test found in the `test_file`
    JSON file and attach a test method to the `clazz` class.
    """
    test_data_dir = os.path.join(os.path.dirname(__file__), "data")
    test_file = os.path.join(test_data_dir, test_file)

    with open(test_file) as tf:
        tests_data = json.load(tf)
    for items in tests_data:
        test_func, test_name = create_test_function(**items)
        # TODO: remove once implemented
        test_func = expectedFailure(test_func)
        # attach that method to the class
        setattr(clazz, test_name, test_func)


# build_tests()
