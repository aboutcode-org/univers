#
# Copyright (c) 2019 JFrog LTD
# SPDX-License-Identifier: MIT
#
# Visit https://aboutcode.org and https://github.com/aboutcode-org/univers for support and download.

from functools import total_ordering
from typing import TYPE_CHECKING

from univers.conan.errors import ConanException

if TYPE_CHECKING:
    try:
        from typing import Self
    except ImportError:
        from typing_extensions import Self


@total_ordering
class _VersionItem:
    """a single "digit" in a version, like X.Y.Z all X and Y and Z are VersionItems
    They can be int or strings
    """

    def __init__(self, item: str | int | Self):
        try:
            self._v = int(item)
        except ValueError:
            self._v = item

    @property
    def value(self) -> int:
        return self._v

    def __str__(self) -> str:
        return str(self._v)

    def __add__(self, other: Self) -> int:
        # necessary for the "bump()" functionality. Other aritmetic operations are missing
        return self._v + other

    def __eq__(self, other: str | int | Self) -> bool:
        if not isinstance(other, _VersionItem):
            other = _VersionItem(other)
        return self._v == other._v

    def __hash__(self) -> int:
        return hash(self._v)

    def __lt__(self, other: str | int | Self) -> bool:
        """
        @type other: _VersionItem
        """
        if not isinstance(other, _VersionItem):
            other = _VersionItem(other)
        try:
            return self._v < other._v
        except TypeError:
            return str(self._v) < str(other._v)


@total_ordering
class Version:
    """
    This is NOT an implementation of semver, as users may use any pattern in their versions.
    It is just a helper to parse "." or "-" and compare taking into account integers when possible
    """

    def __init__(self, value: int | str | Self):
        value = str(value)
        self._value = value

        items = value.rsplit("+", 1)  # split for build
        if len(items) == 2:
            value, build = items
            self._build = Version(build)  # This is a nested version by itself
        else:
            value = items[0]
            self._build = None

        items = value.rsplit("-", 1)  # split for pre-release
        if len(items) == 2:
            value, pre = items
            self._pre = Version(pre)  # This is a nested version by itself
        else:
            value = items[0]
            self._pre = None
        items = value.split(".")
        items = [_VersionItem(item) for item in items]
        self._items = tuple(items)
        while items and items[-1].value == 0:
            del items[-1]
        self._nonzero_items = tuple(items)

    def bump(self, index: int) -> Self:
        """
        :meta private:
            Bump the version
            Increments by 1 the version field at the specified index, setting to 0 the fields
            on the right.
            2.5 => bump(1) => 2.6
            1.5.7 => bump(0) => 2.0.0

        :param index:
        """
        # this method is used to compute version ranges from tilde ~1.2 and caret ^1.2.1 ranges
        # TODO: at this moment it only works for digits, cannot increment pre-release or builds
        # better not make it public yet, keep it internal
        items = list(self._items[:index])
        try:
            items.append(self._items[index] + 1)
        except TypeError:
            raise ConanException(f"Cannot bump '{self._value} version index {index}, not an int")
        items.extend([0] * (len(items) - index - 1))
        v = ".".join(str(i) for i in items)
        # prerelease and build are dropped while bumping digits
        result = Version(v)
        return result

    def upper_bound(self, index: int) -> Self:
        items = list(self._items[:index])
        try:
            items.append(self._items[index] + 1)
        except TypeError:
            raise ConanException(f"Cannot bump '{self._value} version index {index}, not an int")
        items.extend([0] * (len(items) - index - 1))
        v = ".".join(str(i) for i in items)
        v += "-"  # Exclude prereleases
        result = Version(v)
        return result

    @property
    def pre(self) -> Self | None:
        return self._pre

    @property
    def build(self) -> Self | None:
        return self._build

    @property
    def main(self) -> tuple[_VersionItem, ...]:
        return self._items

    @property
    def major(self) -> _VersionItem | None:
        try:
            return self.main[0]
        except IndexError:
            return None

    @property
    def minor(self) -> _VersionItem | None:
        try:
            return self.main[1]
        except IndexError:
            return None

    @property
    def patch(self) -> _VersionItem | None:
        try:
            return self.main[2]
        except IndexError:
            return None

    @property
    def micro(self) -> _VersionItem | None:
        try:
            return self.main[3]
        except IndexError:
            return None

    def __str__(self) -> str:
        return self._value

    def __repr__(self) -> str:
        return self._value

    def __eq__(self, other: int | str | Self | None) -> bool:
        if other is None:
            return False
        if not isinstance(other, Version):
            other = Version(other)

        return (self._nonzero_items, self._pre, self._build) == (
            other._nonzero_items,
            other._pre,
            other._build,
        )

    def __hash__(self) -> int:
        return hash((self._nonzero_items, self._pre, self._build))

    def __lt__(self, other: int | str | Self | None) -> bool:
        if other is None:
            return False
        if not isinstance(other, Version):
            other = Version(other)

        if self._pre:
            if other._pre:  # both are pre-releases
                return (self._nonzero_items, self._pre, self._build) < (
                    other._nonzero_items,
                    other._pre,
                    other._build,
                )
            else:  # Left hand is pre-release, right side is regular
                if (
                    self._nonzero_items == other._nonzero_items
                ):  # Problem only happens if both equal
                    return True
                else:
                    return self._nonzero_items < other._nonzero_items
        else:
            if other._pre:  # Left hand is regular, right side is pre-release
                if (
                    self._nonzero_items == other._nonzero_items
                ):  # Problem only happens if both equal
                    return False
                else:
                    return self._nonzero_items < other._nonzero_items
            else:  # None of them is pre-release
                return (self._nonzero_items, self._build) < (other._nonzero_items, other._build)
