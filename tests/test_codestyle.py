#
# Copyright (c) nexB Inc. and others.
# SPDX-License-Identifier: Apache-2.0
#
# Visit https://aboutcode.org and https://github.com/nexB/univers for support and download.

import subprocess
import unittest


class BaseTests(unittest.TestCase):
    def test_codestyle(self):
        args = "black --check -l 100 setup.py src tests"
        try:
            subprocess.check_output(args.split())
        except subprocess.CalledProcessError as e:
            print("===========================================================")
            print(e.output)
            print("===========================================================")
            raise Exception(
                "Black style check failed; please format the code using:\n"
                "  python -m black -l 100 setup.py src tests",
                e.output,
            ) from e

        args = "isort --check-only src tests setup.py"
        try:
            subprocess.check_output(args.split())
        except Exception as e:
            print("===========================================================")
            print(e.output)
            print("===========================================================")
            raise Exception(
                "Unsorted imports, please sort your imports using isort. "
                "Alternatively, run ``isort src tests setup.py``",
                e.output,
            ) from e
