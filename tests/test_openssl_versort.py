#
# Copyright (c) nexB Inc. and others.
# SPDX-License-Identifier: Apache-2.0
#
# Visit https://aboutcode.org and https://github.com/nexB/univers for support and download.

from pathlib import Path

from commoncode import testcase
from tests import util_tests
from univers.versions import OpensslVersion


class TestOpenssl(testcase.FileBasedTesting):
    test_data_dir = str(Path(__file__).resolve().parent / "data" / "openssl")

    def test_openssl_version_sort(self):
        versions_file = self.get_test_loc("openssl_all_versions.txt")
        with open(versions_file) as f:
            all_openssl_versions = f.readlines()
        results = [OpensslVersion(x.strip()) for x in all_openssl_versions]
        results.sort()
        results = [version_to_dict(x) for x in results]
        expected_file = self.get_test_loc("openssl_versort_expected.json", must_exist=False)
        util_tests.check_results_against_json(results, expected_file)


def version_to_dict(version):
    return {
        "string": version.string,
        "normalized_string": version.normalized_string,
        "value": str(version.value),
    }
