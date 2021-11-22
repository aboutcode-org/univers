#
# Copyright (c) nexB Inc. and others.
# SPDX-License-Identifier: Apache-2.0
#
# Visit https://aboutcode.org and https://github.com/nexB/univers for support and download.

import operator
from functools import total_ordering

import attr

from univers.utils import remove_spaces
from univers.versions import Version

"""
Universal version constraint object that stores a comparator such as "=" and
an ecosystem- or package-specific Version object.
"""


def operator_star(a, b):
    """
    Comparison operator for the star "*" constraint comparator. Since it matches
    any version, it is always True.
    """
    return True


COMPARATORS = {
    # note: the operators may look like inverted... but that's because we
    # b in a rather than a in b as a containment test
    ">=": operator.le,
    "<=": operator.ge,
    "!=": operator.ne,
    "<": operator.gt,
    ">": operator.lt,
    "=": operator.eq,
    "*": operator_star,
}


@total_ordering
@attr.s(frozen=True, repr=True, str=False, order=False, eq=True, hash=True)
class VersionConstraint:
    """
    Represent a single constraint composed of a comparator and a version.
    Version constraints are sortable by version then comparator

    """

    # one of the COMPARATORS
    comparator = attr.ib(type=str)

    # a Version subclass instance or None
    version = attr.ib(type=Version, default=None)

    def __str__(self):
        """
        Return a string representing this constraint.
        For example::
        >>> assert str(VersionConstraint(comparator=">=", version="2.3")) == ">=2.3"
        >>> assert str(VersionConstraint(comparator="*", version=None)) == "*"
        >>> assert str(VersionConstraint(comparator="<", version="2.3")) == "<2.3"
        >>> assert str(VersionConstraint(comparator="=", version="2.3.0")) == "2.3.0"
        """
        if self.comparator == "*":
            return "*"
        elif self.comparator == "=":
            return str(self.version)
        else:
            version = str(self.version)
            return f"{self.comparator}{version}"

    to_string = __str__

    def to_dict(self):
        return dict(comparator=self.comparator, version=str(self.version))

    def __lt__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.version.__lt__ == other.version

    @classmethod
    def from_string(cls, string, version_class):
        """
        Return a single VersionConstraint built from a constraint ``string`` and a
        ``version_class`` Version class.
        """
        constraint_string = remove_spaces(string)
        comparator, version = cls.split(constraint_string)

        if comparator not in COMPARATORS:
            raise ValueError(f"Unknown comparator: {comparator!r}")

        if not version and comparator != "*":
            raise ValueError("Empty version")

        version = version_class(version)
        return cls(comparator, version)

    @staticmethod
    def split(string):
        """
        Return a tuple of (comparator, version) strings given a
        constraint ``string`` such as ">=2.3".

        For example::
        >>> assert VersionConstraint.split(">=2.3") == (">=", "2.3",)
        >>> assert VersionConstraint.split("  <   =  2 . 3  ") == ("<=", "2.3",)
        >>> assert VersionConstraint.split("2.3") == ("=", "2.3",)
        >>> assert VersionConstraint.split("*2.3") == ("*", "",)
        >>> assert VersionConstraint.split("*") == ("*", "",)
        >>> assert VersionConstraint.split("<2.3") == ("<", "2.3",)
        >>> assert VersionConstraint.split(">2.3") == (">", "2.3",)
        >>> assert VersionConstraint.split("!=2.3") == ("!=", "2.3",)
        """
        constraint_string = remove_spaces(string)

        # special case for star
        if constraint_string.startswith("*"):
            return "*", ""

        for comparator in COMPARATORS:
            if constraint_string.startswith(comparator):
                # we do not report an error if this is not valid
                version = constraint_string.lstrip("><=!")
                if comparator == "*":
                    version = ""
                return comparator, version

        # default to equality
        return "=", constraint_string

    # FIXME: this may be not enough to only handle "contains"?
    def __contains__(self, version):
        """
        Return a True if the ``version`` Version is contained in this
        VersionConstraint or "satisfies" this VersionConstraint.

        For example::
        >>> from univers.versions import PypiVersion
        >>> v22 = PypiVersion("2.2")
        >>> v23 = PypiVersion("2.3")
        >>> v24 = PypiVersion("2.4")
        >>> assert v23 in VersionConstraint(comparator="=", version=v23)
        >>> assert v24 not in VersionConstraint(comparator="=", version=v23)
        >>> try:
        ...   None in VersionConstraint(comparator="=", version=v23)
        ... except ValueError:
        ...   pass

        >>> assert v22 in VersionConstraint(comparator="!=", version=v23)
        >>> assert v23 in VersionConstraint(comparator="!=", version=v24)
        >>> assert v24 not in VersionConstraint(comparator="!=", version=v24)

        >>> assert v24 in VersionConstraint(comparator=">", version=v23)
        >>> assert v23 not in VersionConstraint(comparator=">", version=v23)
        >>> assert v24 in VersionConstraint(comparator=">=", version=v23)
        >>> assert v23 in VersionConstraint(comparator=">=", version=v23)
        >>> assert v22 not in VersionConstraint(comparator=">=", version=v23)

        >>> assert v23 in VersionConstraint(comparator="<", version=v24)
        >>> assert v23 in VersionConstraint(comparator="<=", version=v24)
        >>> assert v24 in VersionConstraint(comparator="<=", version=v24)
        >>> assert v24 not in VersionConstraint(comparator="<", version=v24)
        """
        if version.__class__ != self.version.__class__:
            raise ValueError(
                f"Cannot compare {version.__class__!r} instance "
                f"with {self.version.__class__!r} instance."
            )
        try:
            comp_operator = COMPARATORS[self.comparator]
        except KeyError as e:
            raise ValueError(f"Unknown comparator: {self.comparator}") from e

        return comp_operator(self.version, version)

    contains = __contains__

    @classmethod
    def validate(cls, constraints):
        """
        Raise an assertion error if the ``constraints`` is not a two-level
        nested list of VersionConstraint objects.
        """
        assert isinstance(constraints, (list, tuple)), constraints
        for inner_constraints in constraints:
            assert isinstance(inner_constraints, (list, tuple)), inner_constraints
            for constraint in inner_constraints:
                assert isinstance(constraint, VersionConstraint), constraint

    @classmethod
    def sort(cls, constraints):
        """
        Return sorted nested list of ``constraints`` using the "vers" canonical
        order. Sorting is done in place.
        """
        for inner_constraints in constraints:
            inner_constraints.sort(key=lambda vc: str(vc))
        constraints.sort(key=lambda vc: str(vc))
        return constraints

    @classmethod
    def to_constraints_string(cls, constraints):
        """
        Return a string representing the provided ``constraints`` nested
        list of VersionConstraint objects such that the outer sequence
        VersionConstraints are joined with an "OR" e.g., a "vers" pipe "|" and
        the inner sequences of VersionConstraint are each joined with an "AND"
        e.g., a "vers" coma ",".
        For instance:
        >>> from univers.versions import PypiVersion
        >>> constraints = [
        ...    [VersionConstraint(comparator="=", version=PypiVersion("2"))],
        ...    [
        ...        VersionConstraint(comparator="=>", version=PypiVersion("3")),
        ...        VersionConstraint(comparator="<", version=PypiVersion("4")),
        ...    ],
        ...    [VersionConstraint(comparator="=", version=PypiVersion("5"))],
        ... ]
        >>> assert VersionConstraint.to_constraints_string(constraints) == "2|=>3,<4|5"
        """
        cls.validate(constraints)
        anyof_constraints = []
        for inner_constraints in constraints:
            allof_constraints = ",".join(map(str, inner_constraints))
            anyof_constraints.append(allof_constraints)
        return "|".join(anyof_constraints)
