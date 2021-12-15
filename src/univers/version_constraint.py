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

try:
    # only stanadard in Python 3.10 and up
    from itertools import pairwise  # NOQA
except ImportError:
    # back from docs at https://docs.python.org/3/library/itertools.html#itertools.pairwise
    import itertools

    def pairwise(iterable):
        a, b = itertools.tee(iterable)
        next(b, None)
        return zip(a, b)


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


# a minimalist, reduced set of comparators
MINIMALIST_COMPARATORS = {">=", "<", "*"}

COMPARATORS = {
    ">=": operator.ge,
    "<=": operator.le,
    "!=": operator.ne,
    "<": operator.lt,
    ">": operator.gt,
    "=": operator.eq,
    "*": operator_star,
}


@total_ordering
@attr.s(frozen=True, repr=True, str=False, order=False, eq=True, hash=True)
class VersionConstraint:
    """
    Represent a single constraint composed of a comparator and a version.

    VersionConstraint is:
    - comparable and orderable e.g., implements functools.total_ordering
      by version then comparator.
    - immutable and hashable.
    """

    # one of the COMPARATORS
    comparator = attr.ib(type=str, default="=")

    # a Version subclass instance or None
    version = attr.ib(type=Version, default="")

    # a function for the comparator
    comp_operator = attr.ib(default=None, repr=False)

    def __attrs_post_init__(self):
        # Notes: setattr is used because this is an immutable frozen instance.
        # See https://www.attrs.org/en/stable/init.html?#post-init
        try:
            object.__setattr__(self, "comp_operator", COMPARATORS[self.comparator])
        except KeyError as e:
            raise ValueError(f"Unknown comparator: {self.comparator}") from e

    def __str__(self):
        """
        Return a string representing this constraint.
        For example::
        >>> assert str(VersionConstraint(comparator=">=", version="2.3")) == ">=2.3"
        >>> assert str(VersionConstraint(comparator="*")) == "*"
        >>> assert str(VersionConstraint(comparator="<", version="2.3")) == "<2.3"
        >>> assert str(VersionConstraint(comparator="=", version="2.3.0")) == "2.3.0"
        >>> assert str(VersionConstraint(version="2.3.0")) == "2.3.0"
        """
        if self.comparator == "*":
            return "*"

        if self.comparator == "=":
            return str(self.version)

        version = str(self.version)
        return f"{self.comparator}{version}"

    to_string = __str__

    def to_dict(self):
        return dict(comparator=self.comparator, version=str(self.version))

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.comparator == other.comparator and self.version == other.version

    def __lt__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        # we compare tuples, version first
        return (self.version, self.comparator).__lt__((other.version, other.comparator))

    @classmethod
    def from_string(cls, string, version_class):
        """
        Return a single VersionConstraint built from a constraint ``string`` and
        a ``version_class`` Version class.
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
                # NOTE: we do not report an error if this is not valid
                version = constraint_string.lstrip(comparator)
                if comparator == "*":
                    version = ""
                return comparator, version

        # default to equality
        return "=", constraint_string

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

        if not isinstance(version, self.version.__class__):
            raise ValueError(
                f"Cannot compare {version.__class__!r} instance "
                f"with {self.version.__class__!r} instance."
            )
        return self.comp_operator(version, self.version)

    contains = __contains__

    @classmethod
    def validate(cls, constraints):
        """
        Raise an assertion error if the ``constraints`` is not a list of
        VersionConstraint objects or if two VersionConstraint contain the same
        Version (ignoring the comparator).
        Also validate that the sequence of comparators is valid.
        Return True otherwise.
        """

        if not isinstance(constraints, (list, tuple)):
            raise ValueError(f"{constraints!r} is a not list or tuple")

        if not all(isinstance(c, VersionConstraint) for c in constraints):
            raise ValueError(f"{constraints!r} can contain only VersionConstraint")

        if len(set(c.version for c in constraints)) != len(constraints):
            raise ValueError(f"{constraints!r} cannot contain duplicated Version")

        constraints.sort()
        return validate_comparators(constraints)

    @classmethod
    def dedupe(cls, constraints):
        """
        Return a new ``constraints`` list with duplicated constraints removed.
        This includes removing exact duplicates adn redundant constraints.
        """
        constraints = deduplicate_exact(constraints)
        constraints = deduplicate_comparators(constraints)
        return constraints


def deduplicate_exact(constraints):
    """
    Return a new ``constraints`` list with exact duplicated constraints removed.
    """
    seen = set()
    unique = []
    for c in constraints:
        if c not in seen:
            unique.append(c)
            seen.add(c)
    return unique


def validate_comparators(constraints):
    """
    Raise an assertion error if the ``constraints`` list contains an invalid
    sequence of constraint comparators according to ``vers`` rules.
    Return True otherwise.

    The following are the validity rules for contiguous constraints where the
    constraints are canonical e.g., sorted by version and versions are unique
    ignoring comparators:

    - "*" can only occur alone
    - "!=" can be followed by anything, i.e., one of "=", "!=", ">", ">=", "<", "<="

    And ignoring all "!=":
    - "=" can be followed only by one of "=", ">", ">="

    And ignoring all "=" and "!=", there must be an alternation of greater and lesser:
    - "<" and "<=" can only be followed by one of ">", ">="
    - ">" and ">=" can only be followed by one of "<", "<="
    """

    if any(c.comparator == "*" for c in constraints):
        if len(constraints) != 1:
            raise ValueError(f"Invalid {constraints!r}: can contain only one star '*'")
        return True

    # discard != that can occur anywhere
    constraints = [c for c in constraints if c.comparator != "!="]
    if not constraints:
        return True

    # check that equals is followed only by "=", ">", ">="
    invalid_equal = [
        (cur, nxt)
        for cur, nxt in pairwise(constraints)
        if cur.comparator == "=" and nxt.comparator not in ("=", ">", ">=")
    ]
    if invalid_equal:
        raise ValueError(
            f"Invalid {constraints!r}\n: where \n{invalid_equal!r} "
            "cannot contain an equal = followed by either < or <="
        )

    # discard = that have been validated above
    constraints = [c for c in constraints if c.comparator != "="]
    if not constraints:
        return True

    # from now on this must be an alternation of greater/lesser
    for cur_constraint, nxt_constraint in pairwise(constraints):
        cur_comp = cur_constraint.comparator
        nxt_comp = nxt_constraint.comparator

        if (cur_comp in ("<", "<=") and nxt_comp not in (">", ">=")) or (
            cur_comp in (">", ">=") and nxt_comp not in ("<", "<=")
        ):

            raise ValueError(
                f"Invalid {constraints!r}: {cur_constraint!r} "
                f"cannot be followed by {nxt_constraint!r}"
            )

    return True


def deduplicate_comparators(constraints):
    """
    Return a list of VersionConstraint given a ``constraints`` list by
    discarding redundant constraints according to ``vers`` rules.
    """
    if len(constraints) == 1 or any(c.comparator == "*" for c in constraints):
        return list(constraints)

    constraints = sorted(constraints)

    inequal_constraints = [c for c in constraints if c.comparator == "!="]
    constraints = [c for c in constraints if c.comparator != "!="]

    if not constraints:
        return sorted(inequal_constraints)

    # iterate as long as constraints length diminishes with each ieration
    cycle = 1
    while True:
        starting_length = len(constraints)
        constraints = list(dedup(constraints))
        ending_length = len(constraints)
        if ending_length == 1 or ending_length == starting_length:
            # no filtering happened in this iteration, we are done
            break
        cycle += 1

    return sorted(inequal_constraints + constraints)


def dedup(constraints):
    """
    Yield filtered constraints, discarding redundant ones according to ``vers``.
    """
    skip = False
    for cur, nxt in pairwise(constraints):
        cur_comp = cur.comparator
        nxt_comp = nxt.comparator
        if skip:
            skip = False
            continue

        if cur_comp in ("=", "<", "<=") and nxt_comp in ("<", "<="):
            # keep only next (drop current)
            skip = True
            yield nxt
            continue

        if cur_comp in (">", ">=") and nxt_comp in ("=", ">", ">="):
            # keep only current (drop next)
            skip = True
            yield cur
            continue

        # keep cur
        skip = False
        yield cur

    # yield last next
    yield nxt


def contains_version(version, constraints):
    """
    Return True an assertion error if the ``constraints`` list contains the
    ``version`` Version object according to ``vers`` rules.
    """
    # If the constraint list contains only one item and the comparator is "*",
    # then the "tested version" is IN the range. Check is finished.

    # If the constraint list contains only one item and and the "tested version"
    # satisfies the comparator then the "tested version"  is IN the range.
    # Check is finished.
    if len(constraints) == 1:
        return version in constraints[0]

    # If the "tested version" is equal to the any of the constraint version
    # where the constraint comparator is for equality (any of "=", "<=", or ">=")
    # then the "tested version" is in the range. Check is finished.
    for constraint in constraints:
        if "=" in constraint.comparator and version == constraint.version:
            return True

    # If the "tested version" is equal to the any of the constraint version where
    # the constraint comparator is "=!" then the "tested version" is NOT in the
    # range. Check is finished.
    for constraint in constraints:
        if "!=" in constraint.comparator and version == constraint.version:
            return False

    # Split the constraint list in two sub lists:
    #   a first list where the comparator is "=" or "!="
    #   a second list where the comparator is neither "=" nor "!="
    constraints = [c for c in constraints if c.comparator not in ("=", "!=")]
    if not constraints:
        return False

    # Iterate over the current and next contiguous constraints pairs (aka. pairwise)
    # in the second list.
    # For each current and next constraint:

    cur_comp = nxt_comp = cur_constraint = nxt_constraint = None
    first_iteration = True
    for cur_constraint, nxt_constraint in pairwise(constraints):
        cur_comp = cur_constraint.comparator
        nxt_comp = nxt_constraint.comparator

        # If this is the first iteration and current comparator is "<" or <="
        # and the "tested version" is less than the current version
        # then the "tested version" is IN the range. Check is finished.
        if first_iteration:
            if cur_comp in ("<", "<=") and version < cur_constraint.version:
                return True
            first_iteration = False

        # If current comparator is ">" or >=" and next comparator is "<" or <="
        # and the "tested version" is greater than the current version
        # and the "tested version" is less than the next version
        # then the "tested version" is IN the range. Check is finished.
        if (
            cur_comp in (">", ">=")
            and nxt_comp in ("<", "<=")
            and version > cur_constraint.version
            and version < nxt_constraint.version
        ):
            return True

        # If current comparator is "<" or <=" and next comparator is ">" or >="
        # then these versions are out the range. Continue to the next iteration.
        elif cur_comp in ("<", "<=") and nxt_comp in (">", ">="):
            pass

        else:
            # this should never happen as the constraints must be valid going in
            raise Exception(f"Invalid constraints sequence: {constraints }")

    # If this is the last iteration and next comparator is ">" or >="
    # and the "tested version" is greater than the next version
    # then the "tested version" is IN the range. Check is finished.
    if nxt_comp in (">", ">=") and version > nxt_constraint.version:
        return True

    # Reaching here without having finished the check before means that the
    # "tested version" is NOT in the range.
    return False
