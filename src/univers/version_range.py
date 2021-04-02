# Copyright (c) nexB Inc. and others.
# SPDX-License-Identifier: Apache-2.0
#
# Visit https://aboutcode.org and https://github.com/nexB/ for support and download.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import operator as operator_module

from univers.utils import remove_spaces
from univers.versions import version_class_by_scheme
from univers.versions import validate_scheme


class VersionRange:
    # one of <> >= =< or != or =
    operator = ""
    version = None

    def __init__(self, version_range_string, scheme):
        version_range_string = remove_spaces(version_range_string)
        self.operator, self.version = self.split(version_range_string)

        try:
            validate_scheme(scheme)
            self.validate()
        except:
            raise ValueError(f"Version range{version_range_string} has no bounds")

        version_class = version_class_by_scheme[scheme]

        self.version = version_class(self.version)

    def validate(self):
        # self.operator will always have a valid value
        if not self.version:
            raise ValueError()

    @staticmethod
    def split(version_range):
        """
        Return a tuple of (operator, range value) given a version ``range``
        string such as ">=2.3".
        """
        operators = ">=", "<=", "!=", "<", ">", "="
        for operator in operators:
            if version_range.startswith(operator):
                return operator, version_range.lstrip("><=!")

        # Contains no operator, so assume equality
        return "=", version_range

    def __contains__(self, version):

        if version.__class__ != self.version.__class__:
            raise ValueError(
                f"Can't compare {version.__class__} instance with {self.version.__class__} instance"
            )

        operators = {
            "<=": operator_module.le,
            ">=": operator_module.ge,
            "!=": operator_module.ne,
            "<": operator_module.lt,
            ">": operator_module.gt,
            "=": operator_module.eq,
        }
        operator = operators[self.operator]
        return operator(version, self.version)

    def __eq__(self, other):
        return (self.version, self.operator) == (other.version, other.operator)

    def __str__(self):
        return f"{self.operator}{self.version}"
