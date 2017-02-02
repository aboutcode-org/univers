# Debian packaging tools: Relationship parsing and evaluation.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: February 2, 2017
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
RelationshipSet(VersionedRelationship(name='python', operator='>=', version='2.6', architectures=()),
                AlternativeRelationship(VersionedRelationship(name='python', operator='<<', version='3', architectures=()),
                                        VersionedRelationship(name='python', operator='>=', version='3.4', architectures=())))
>>> print(str(dependencies))
python (>= 2.6), python (<< 3) | python (>= 3.4)

As you can see the :func:`repr()` output of the relationship set shows the
object tree and the :class:`str` output is the dependency line.

.. _chapter 7: http://www.debian.org/doc/debian-policy/ch-relationships.html#s-depsyntax
"""

# Standard library modules.
import logging
import re

# External dependencies.
from humanfriendly.text import compact, split
from property_manager import PropertyManager, key_property
from six import string_types, text_type

# Modules included in our package.
from deb_pkg_tools.compat import str_compatible
from deb_pkg_tools.version import compare_versions

# Initialize a logger.
logger = logging.getLogger(__name__)

# Define a compiled regular expression pattern that we will use to match
# package relationship expressions consisting of a package name followed by
# optional version and architecture restrictions.
EXPRESSION_PATTERN = re.compile(r'''
    # Capture all leading characters up to (but not including)
    # the first parenthesis, bracket or space.
    (?P<name> [^\(\[ ]+ )
    # Ignore any whitespace.
    \s*
    # Optionally capture version restriction inside parentheses.
    ( \( (?P<version> [^)]+ ) \) )?
    # Ignore any whitespace.
    \s*
    # Optionally capture architecture restriction inside brackets.
    ( \[ (?P<architectures> [^\]]+ ) \] )?
''', re.VERBOSE)

ARCHITECTURE_RESTRICTIONS_MESSAGE = """
Evaluation of architecture restrictions hasn't been implemented yet. If you
think this would be useful to you then please submit a feature request at
https://github.com/xolox/python-deb-pkg-tools/issues/9
"""


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
    logger.debug("Parsing relationships: %r", relationships)
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
        logger.debug("Parsing relationship with alternatives: %r", expression)
        return AlternativeRelationship(*map(parse_relationship, split(expression, '|')))
    else:
        return parse_relationship(expression)


def parse_relationship(expression):
    """
    Parse an expression containing a package name and optional version/architecture restrictions.

    :param expression: A relationship expression (a string).
    :returns: A :class:`Relationship` object.
    :raises: :exc:`~exceptions.ValueError` when parsing fails.

    This function parses relationship expressions containing a package name and
    (optionally) a version relation of the form ``python (>= 2.6)`` and/or an
    architecture restriction (refer to the Debian policy manual's documentation
    on the `syntax of relationship fields`_ for details). Here's an example:

    >>> from deb_pkg_tools.deps import parse_relationship
    >>> parse_relationship('python')
    Relationship(name='python')
    >>> parse_relationship('python (<< 3)')
    VersionedRelationship(name='python', operator='<<', version='3')

    .. _syntax of relationship fields: https://www.debian.org/doc/debian-policy/ch-relationships.html
    """
    logger.debug("Parsing relationship: %r", expression)
    match = EXPRESSION_PATTERN.match(expression)
    name = match.group('name')
    version = match.group('version')
    # Split the architecture restrictions into a tuple of strings.
    architectures = tuple((match.group('architectures') or '').split())
    if name and not version:
        # A package name (and optional architecture restrictions) without version relation.
        return Relationship(name=name, architectures=architectures)
    else:
        # A package name (and optional architecture restrictions) followed by a
        # relationship to specific version(s) of the package.
        tokens = [t.strip() for t in re.split('([<>=]+)', version) if t and not t.isspace()]
        if len(tokens) != 2:
            # Encountered something unexpected!
            raise ValueError(compact("""
                Corrupt package relationship expression: Splitting operator
                from version resulted in more than two tokens!
                (expression: {e}, tokens: {t})
            """, e=expression, t=tokens))
        return VersionedRelationship(name=name, architectures=architectures, operator=tokens[0], version=tokens[1])


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


class AbstractRelationship(PropertyManager):

    """Abstract base class for the various types of relationship objects defined in :mod:`deb_pkg_tools.deps`."""

    @property
    def names(self):
        """
        The name(s) of the packages in the relationship.

        :returns: A set of package names (strings).

        .. note:: This property needs to be implemented by subclasses.
        """
        raise NotImplementedError

    def matches(self, name, version=None):
        """
        Check if the relationship matches a given package and version.

        :param name: The name of a package (a string).
        :param version: The version number of a package (a string, optional).
        :returns: One of the values :data:`True`, :data:`False` or :data:`None`
                  meaning the following:

                  - :data:`True` if the name matches and the version
                    doesn't invalidate the match,

                  - :data:`False` if the name matches but the version
                    invalidates the match,

                  - :data:`None` if the name doesn't match at all.

        .. note:: This method needs to be implemented by subclasses.
        """
        raise NotImplementedError


@str_compatible
class Relationship(AbstractRelationship):

    """
    A simple package relationship referring only to the name of a package.

    Created by :func:`parse_relationship()`.
    """

    # Explicitly define the sort order of the key properties.
    key_properties = 'name', 'architectures'

    @key_property
    def name(self):
        """The name of a package (a string)."""

    @key_property
    def architectures(self):
        """The architecture restriction(s) on the relationship (a tuple of strings)."""
        return ()

    @property
    def names(self):
        """The name(s) of the packages in the relationship."""
        return set([self.name])

    def matches(self, name, version=None):
        """
        Check if the relationship matches a given package name.

        :param name: The name of a package (a string).
        :param version: The version number of a package (this parameter is ignored).
        :returns: :data:`True` if the name matches, :data:`None` otherwise.
        :raises: :exc:`~exceptions.NotImplementedError` when :attr:`architectures`
                 is not empty (because evaluation of architecture restrictions
                 hasn't been implemented).
        """
        if self.name == name:
            if self.architectures:
                raise NotImplementedError(compact(ARCHITECTURE_RESTRICTIONS_MESSAGE))
            return True

    def __str__(self):
        """Serialize a :class:`Relationship` object to a Debian package relationship expression."""
        expression = self.name
        if self.architectures:
            expression += u" [%s]" % " ".join(self.architectures)
        return expression

    def __repr__(self):
        """Serialize a :class:`Relationship` object to a Python expression."""
        return "%s(%s)" % (self.__class__.__name__, ', '.join([
            'name=%r' % self.name,
            'architectures=%s' % repr(self.architectures),
        ]))


@str_compatible
class VersionedRelationship(Relationship):

    """
    A conditional package relationship that refers to a package and certain versions of that package.

    Created by :func:`parse_relationship()`.
    """

    # Explicitly define the sort order of the key properties.
    key_properties = 'name', 'operator', 'version', 'architectures'

    @key_property
    def operator(self):
        """An operator that compares Debian package version numbers (a string)."""

    @key_property
    def version(self):
        """The version number of a package (a string)."""

    @cache_matches
    def matches(self, name, version=None):
        """
        Check if the relationship matches a given package name and version.

        :param name: The name of a package (a string).
        :param version: The version number of a package (a string, optional).
        :returns: One of the values :data:`True`, :data:`False` or :data:`None`
                  meaning the following:

                  - :data:`True` if the name matches and the version
                    doesn't invalidate the match,

                  - :data:`False` if the name matches but the version
                    invalidates the match,

                  - :data:`None` if the name doesn't match at all.
        :raises: :exc:`~exceptions.NotImplementedError` when :attr:`architectures`
                 is not empty (because evaluation of architecture restrictions
                 hasn't been implemented).

        Uses the external command ``dpkg --compare-versions`` to ensure
        compatibility with Debian's package version comparison algorithm.
        """
        if self.name == name:
            if version:
                if self.architectures:
                    raise NotImplementedError(compact(ARCHITECTURE_RESTRICTIONS_MESSAGE))
                return compare_versions(version, self.operator, self.version)
            else:
                return False

    def __str__(self):
        """Serialize a :class:`VersionedRelationship` object to a Debian package relationship expression."""
        expression = u'%s (%s %s)' % (self.name, self.operator, self.version)
        if self.architectures:
            expression += u" [%s]" % " ".join(self.architectures)
        return expression

    def __repr__(self):
        """Serialize a :class:`VersionedRelationship` object to a Python expression."""
        return "%s(%s)" % (self.__class__.__name__, ', '.join([
            'name=%r' % self.name,
            'operator=%r' % self.operator,
            'version=%r' % self.version,
            'architectures=%s' % repr(self.architectures),
        ]))


@str_compatible
class AlternativeRelationship(AbstractRelationship):

    """
    A package relationship that refers to one of several alternative packages.

    Created by :func:`parse_alternatives()`.
    """

    def __init__(self, *relationships):
        """
        Initialize an :class:`AlternativeRelationship` object.

        :param relationships: One or more :class:`Relationship` objects.
        """
        self.relationships = tuple(relationships)

    @key_property
    def relationships(self):
        """A tuple of :class:`Relationship` objects."""

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


@str_compatible
class RelationshipSet(PropertyManager):

    """A set of package relationships. Created by :func:`parse_depends()`."""

    def __init__(self, *relationships):
        """
        Initialize a :class `RelationshipSet` object.

        :param relationships: One or more :class:`Relationship` objects.
        """
        self.relationships = tuple(relationships)

    @key_property
    def relationships(self):
        """A tuple of :class:`Relationship` objects."""

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

    def __iter__(self):
        """Iterate over the relationships in a relationship set."""
        return iter(self.relationships)
