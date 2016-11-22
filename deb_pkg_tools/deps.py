# Debian packaging tools: Relationship parsing and evaluation.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: November 22, 2016
# URL: https://github.com/xolox/python-deb-pkg-tools

"""
Parsing and evaluation of Debian package relationship declarations.

The :mod:`deb_pkg_tools.deps` module provides functions to parse and evaluate
Debian package relationship declarations as defined in `chapter 7`_ of the
Debian policy manual. The most important function is :func:`parse_depends()`
which returns a :class:`RelationshipSet` object. The
:func:`RelationshipSet.matches()` function can be used to evaluate relationship
expressions. The relationship parsing is implemented in pure Python (no
external dependencies) but relationship evaluation uses the external command
``dpkg --compare-versions`` to ensure compatibility with Debian's package
version comparison algorithm.

To give you an impression of how to use this module:

>>> from deb_pkg_tools.deps import parse_depends
>>> dependencies = parse_depends('python (>= 2.6), python (<< 3) | python (>= 3.4)')
>>> dependencies.matches('python', '2.5')
False
>>> dependencies.matches('python', '3.0')
False
>>> dependencies.matches('python', '2.6')
True
>>> dependencies.matches('python', '3.4')
True
>>> print(repr(dependencies))
RelationshipSet(VersionedRelationship(name='python', operator='>=', version='2.6'),
                AlternativeRelationship(VersionedRelationship(name='python', operator='<<', version='3'),
                                        VersionedRelationship(name='python', operator='>=', version='3.4')))
>>> print(str(dependencies))
python (>= 2.6), python (<< 3) | python (>= 3.4)

As you can see the :func:`repr()` output of the relationship set shows the
object tree and the :class:`str` output is the dependency line.

.. warning:: The relationship parsing code does not understand the complete
             syntax defined in the Debian policy manual. More specifically
             architecture restrictions are not supported (because I simply
             don't use them).

.. _chapter 7: http://www.debian.org/doc/debian-policy/ch-relationships.html#s-depsyntax
"""

# Standard library modules.
import logging
import re

# External dependencies.
from humanfriendly.text import compact, split
from six import string_types, text_type

# Modules included in our package.
from deb_pkg_tools.compat import str_compatible
from deb_pkg_tools.utils import OrderedObject
from deb_pkg_tools.version import compare_versions

# Initialize a logger.
logger = logging.getLogger(__name__)


def parse_depends(relationships):
    """
    Parse a Debian package relationship declaration line.

    :param relationships: A string containing one or more comma separated
                          package relationships or a list of strings with
                          package relationships.
    :returns: A :class:`RelationshipSet` object.
    :raises: :exc:`~exceptions.ValueError` when parsing fails.

    This function parses a list of package relationships of the form ``python
    (>= 2.6), python (<< 3)``, i.e. a comma separated list of relationship
    expressions. Uses :func:`parse_alternatives()` to parse each comma
    separated expression.

    Here's an example:

    >>> from deb_pkg_tools.deps import parse_depends
    >>> dependencies = parse_depends('python (>= 2.6), python (<< 3)')
    >>> print(repr(dependencies))
    RelationshipSet(VersionedRelationship(name='python', operator='>=', version='2.6'),
                    VersionedRelationship(name='python', operator='<<', version='3'))
    >>> dependencies.matches('python', '2.5')
    False
    >>> dependencies.matches('python', '2.6')
    True
    >>> dependencies.matches('python', '2.7')
    True
    >>> dependencies.matches('python', '3.0')
    False
    """
    if isinstance(relationships, string_types):
        relationships = split(relationships, ',')
    return RelationshipSet(*map(parse_alternatives, relationships))


def parse_alternatives(expression):
    """
    Parse an expression containing one or more alternative relationships.

    :param expression: A relationship expression (a string).
    :returns: A :class:`Relationship` object.
    :raises: :exc:`~exceptions.ValueError` when parsing fails.

    This function parses an expression containing one or more alternative
    relationships of the form ``python2.6 | python2.7.``, i.e. a list of
    relationship expressions separated by ``|`` tokens. Uses
    :func:`parse_relationship()` to parse each ``|`` separated expression.

    An example:

    >>> from deb_pkg_tools.deps import parse_alternatives
    >>> parse_alternatives('python2.6')
    Relationship(name='python2.6')
    >>> parse_alternatives('python2.6 | python2.7')
    AlternativeRelationship(Relationship(name='python2.6'),
                            Relationship(name='python2.7'))

    """
    if '|' in expression:
        return AlternativeRelationship(*map(parse_relationship, expression.split('|')))
    else:
        return parse_relationship(expression)


def parse_relationship(expression):
    """
    Parse an expression containing a package name and version.

    :param expression: A relationship expression (a string).
    :returns: A :class:`Relationship` object.
    :raises: :exc:`~exceptions.ValueError` when parsing fails.

    This function parses relationship expressions containing a package name
    and (optionally) a version relation of the form ``python (>= 2.6)``.

    An example:

    >>> from deb_pkg_tools.deps import parse_relationship
    >>> parse_relationship('python')
    Relationship(name='python')
    >>> parse_relationship('python (<< 3)')
    VersionedRelationship(name='python', operator='<<', version='3')
    """
    tokens = [t.strip() for t in re.split('[()]', expression) if t and not t.isspace()]
    if len(tokens) == 1:
        # Just a package name (no version information).
        return Relationship(tokens[0])
    elif len(tokens) != 2:
        # Encountered something unexpected!
        raise ValueError(compact("""
            Corrupt package relationship expression: Splitting name from
            relationship resulted in more than two tokens!
            (expression: {e}, tokens: {t})
        """, e=expression, t=tokens))
    else:
        # Package name followed by relationship to specific version(s) of package.
        name, relationship = tokens
        tokens = [t.strip() for t in re.split('([<>=]+)', relationship) if t and not t.isspace()]
        if len(tokens) != 2:
            # Encountered something unexpected!
            raise ValueError(compact("""
                Corrupt package relationship expression: Splitting operator
                from version resulted in more than two tokens!
                (expression: {e}, tokens: {t})
            """, e=relationship, t=tokens))
        return VersionedRelationship(name, *tokens)


def cache_matches(f):
    """
    High performance memoizing decorator for overrides of :func:`Relationship.matches()`.

    Before writing this function I tried out several caching decorators from
    PyPI, unfortunately all of them were bloated. I benchmarked using
    :func:`.collect_related_packages()` and where this decorator would get a
    total runtime of 8 seconds the other caching decorators would get
    something like 40 seconds...
    """
    def decorator(self, package, version=None):
        # Get or create the cache.
        try:
            cache = self._matches_cache
        except AttributeError:
            cache = {}
            setattr(self, '_matches_cache', cache)
        # Get or create the entry.
        key = (package, version)
        try:
            return cache[key]
        except KeyError:
            value = f(self, package, version)
            cache[key] = value
            return value
    return decorator


@str_compatible
class Relationship(OrderedObject):

    """
    A simple package relationship referring only to the name of a package.

    Created by :func:`parse_relationship()`.
    """

    def __init__(self, name):
        """
        Initialize a simple relationship.

        :param name: The name of a package (a string).
        """
        self.name = name

    @property
    def names(self):
        """
        Get the name(s) of the packages in the relationship.

        :returns: A set of package names (strings).
        """
        return set([self.name])

    def matches(self, name, version=None):
        """
        Check if the relationship matches a given package and version.

        :param name: The name of a package (a string).
        :param version: The version number of a package (a string, optional).
        :returns: :data:`True` if the relationship matches, :data:`None` otherwise.
        """
        return True if self.name == name else None

    def __str__(self):
        """Serialize a :class:`Relationship` object to a Debian package relationship expression."""
        return self.name

    def __repr__(self):
        """Serialize a :class:`Relationship` object to a Python expression."""
        return "%s(%s)" % (self.__class__.__name__, ', '.join([
            'name=%r' % self.name
        ]))

    def _key(self):
        """
        Get the comparison key of this :class:`Relationship` object.

        Used to implement the equality and rich comparison operations.
        """
        return (self.name,)


@str_compatible
class VersionedRelationship(Relationship):

    """
    A conditional package relationship that refers to a package and certain versions of that package.

    Created by :func:`parse_relationship()`.
    """

    def __init__(self, name, operator, version):
        """
        Initialize a conditional relationship.

        :param name: The name of a package (a string).
        :param operator: A version comparison operator (a string).
        :param version: The version number of a package (a string).
        """
        self.name = name
        self.operator = operator
        self.version = version

    @cache_matches
    def matches(self, name, version=None):
        """
        Check if the relationship matches a given package and version.

        :param name: The name of a package (a string).
        :param version: The version number of a package (a string, optional).
        :returns: :data:`True` if the name and version match, :data:`False` if only the
                  name matches, :data:`None` otherwise.

        Uses the external command ``dpkg --compare-versions`` to ensure
        compatibility with Debian's package version comparison algorithm.
        """
        if self.name == name:
            if version:
                return compare_versions(version, self.operator, self.version)
            else:
                return False

    def __str__(self):
        """Serialize a :class:`VersionedRelationship` object to a Debian package relationship expression."""
        return u'%s (%s %s)' % (self.name, self.operator, self.version)

    def __repr__(self):
        """Serialize a :class:`VersionedRelationship` object to a Python expression."""
        return "%s(%s)" % (self.__class__.__name__, ', '.join([
            'name=%r' % self.name,
            'operator=%r' % self.operator,
            'version=%r' % self.version,
        ]))

    def _key(self):
        """
        Get the comparison key of this :class:`VersionedRelationship` object.

        Used to implement the equality and rich comparison operations.
        """
        return (self.name, self.operator, self.version)


@str_compatible
class AlternativeRelationship(Relationship):

    """
    A package relationship that refers to one of several alternative packages.

    Created by :func:`parse_alternatives()`.
    """

    def __init__(self, *relationships):
        """
        Initialize an alternatives relationship.

        :param relationships: One or more :class:`Relationship` objects.
        """
        self.relationships = tuple(relationships)

    @property
    def names(self):
        """
        Get the name(s) of the packages in the alternative relationship.

        :returns: A set of package names (strings).
        """
        names = set()
        for relationship in self.relationships:
            names |= relationship.names
        return names

    @cache_matches
    def matches(self, name, version=None):
        """
        Check if the relationship matches a given package and version.

        :param name: The name of a package (a string).
        :param version: The version number of a package (a string, optional).
        :returns: :data:`True` if the name and version of an alternative match,
                  :data:`False` if the name of an alternative was matched but the
                  version didn't match, :data:`None` otherwise.
        """
        matches = None
        for alternative in self.relationships:
            alternative_matches = alternative.matches(name, version)
            if alternative_matches is True:
                return True
            elif alternative_matches is False:
                # Keep looking for a match but return False if we don't find one.
                matches = False
        return matches

    def __str__(self):
        """Serialize an :class:`AlternativeRelationship` object to a Debian package relationship expression."""
        return u' | '.join(map(text_type, self.relationships))

    def __repr__(self):
        """Serialize an :class:`AlternativeRelationship` object to a Python expression."""
        return "%s(%s)" % (self.__class__.__name__, ', '.join(repr(r) for r in self.relationships))

    def _key(self):
        """
        Get the comparison key of this :class:`AlternativeRelationship` object.

        Used to implement the equality and rich comparison operations.
        """
        return self.relationships


@str_compatible
class RelationshipSet(OrderedObject):

    """A set of package relationships. Created by :func:`parse_depends()`."""

    def __init__(self, *relationships):
        """
        Initialize a set of relationships.

        :param relationships: One or more :class:`Relationship` objects.
        """
        self.relationships = tuple(relationships)

    @property
    def names(self):
        """
        Get the name(s) of the packages in the relationship set.

        :returns: A set of package names (strings).
        """
        names = set()
        for relationship in self.relationships:
            names |= relationship.names
        return names

    @cache_matches
    def matches(self, name, version=None):
        """
        Check if the set of relationships matches a given package and version.

        :param name: The name of a package (a string).
        :param version: The version number of a package (a string, optional).
        :returns: :data:`True` if all matched relationships evaluate to true,
                  :data:`False` if a relationship is matched and evaluates to false,
                  :data:`None` otherwise.

        .. warning:: Results are cached in the assumption that
                     :class:`RelationshipSet` objects are
                     immutable. This is not enforced.
        """
        results = [r.matches(name, version) for r in self.relationships]
        matches = [r for r in results if r is not None]
        return all(matches) if matches else None

    def __str__(self):
        """Serialize a :class:`RelationshipSet` object to a Debian package relationship expression."""
        return u', '.join(map(text_type, self.relationships))

    def __repr__(self, pretty=False, indent=0):
        """Serialize a :class:`RelationshipSet` object to a Python expression."""
        prefix = '%s(' % self.__class__.__name__
        indent += len(prefix)
        delimiter = ',\n%s' % (' ' * indent) if pretty else ', '
        return prefix + delimiter.join(repr(r) for r in self.relationships) + ')'

    def _key(self):
        """
        Get the comparison key of this :class:`RelationshipSet` object.

        Used to implement the equality and rich comparison operations.
        """
        return self.relationships

    def __iter__(self):
        """Iterate over the relationships in a relationship set."""
        return iter(self.relationships)
