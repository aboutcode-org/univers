#
# Copyright (c) nexB Inc. and others.
# SPDX-License-Identifier: Apache-2.0
#
# Visit https://aboutcode.org and https://github.com/nexB/ for support and download.

import subprocess
import unittest


class BaseTests(unittest.TestCase):
    def test_codestyle(self):
        args = "python -m black --check -l 100 *.py etc/ src/ tests/ docs"
        try:
            subprocess.check_output(args.split())
        except Exception as e:
            raise Exception(
                "Black style check failed; please format the code using:\n"
                "  python -m black -l 100 *.py etc/ src/ tests/ docs"
            ) from e
