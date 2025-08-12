#
# Copyright (c) nexB Inc. and others.
# SPDX-License-Identifier: Apache-2.0
#
# Visit https://aboutcode.org and https://github.com/aboutcode-org/univers for support and download.

from typing import NamedTuple
from typing import Union


class SchemaDrivenVersTest(NamedTuple):
    test_type: str
    test_group: str
    input: dict
    expected_output: Union[list, bool]

    @classmethod
    def from_data(cls, data: dict):
        return cls(**data)

    def assert_result(self):
        assert self.result == self.expected_output

    @property
    def result(self):
        if self.test_type == "equality":
            return self.equality()
        elif self.test_type == "comparison":
            return self.comparison()
        elif self.test_type == "containment":
            return self.containment()
        elif self.test_type == "roundtrip":
            return self.roundtrip()
        elif self.test_type == "from_native":
            return self.from_native()

        raise Exception(f"Unknown test_type: {self.test_type}")

    def equality(self):
        raise NotImplementedError

    def comparison(self):
        raise NotImplementedError

    def containment(self):
        raise NotImplementedError

    def roundtrip(self):
        raise NotImplementedError

    def from_native(self):
        raise NotImplementedError

    @property
    def input_scheme(self):
        return self.input["input_scheme"]

    @property
    def input_native_range(self):
        return self.input["native_range"]

    @property
    def input_version1(self):
        return self.input["versions"][0]

    @property
    def input_version2(self):
        return self.input["versions"][1]


def get_test_data_comp(scheme, versions, output):
    return {
        "test_group": "advanced",
        "test_type": "comparison",
        "input": {
            "input_scheme": scheme,
            "versions": versions,
        },
        "expected_output": output,
    }


def get_test_data_eq(scheme, versions, output):
    return {
        "test_group": "advanced",
        "test_type": "equality",
        "input": {
            "input_scheme": scheme,
            "versions": versions,
        },
        "expected_output": output,
    }


def get_test_data_containment(vers, version, output):
    return {
        "test_group": "advanced",
        "test_type": "containment",
        "input": {
            "vers": vers,
            "version": version,
        },
        "expected_output": output,
    }


def get_test_data_roundtrip(vers, output):
    return {
        "test_group": "advanced",
        "test_type": "roundtrip",
        "input": {
            "vers": vers,
        },
        "expected_output": output,
    }


def get_test_data_from_native(native_range, schema, output):
    return {
        "test_group": "advanced",
        "test_type": "from_native",
        "input": {
            "native_range": native_range,
            "scheme": schema,
        },
        "expected_output": output,
    }
