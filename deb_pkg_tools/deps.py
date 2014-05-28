# Debian packaging tools: Relationship parsing and evaluation.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: May 28, 2014
# URL: https://github.com/xolox/python-deb-pkg-tools

"""
Relationship parsing and evaluation
===================================

This module provides functions to parse and evaluate Debian package
relationship declarations as defined in `chapter 7`_ of the `Debian policy
manual`_. The most important function is :py:func:`parse_depends()` which
returns a :py:class:`RelationshipSet` object. The
:py:func:`RelationshipSet.matches()` function can be used to evaluate
relationship expressions. The relationship parsing is implemented in pure
Python (no external dependencies) but relationship evaluation uses the external
command ``dpkg --compare-versions`` to ensure compatibility with Debian's
package version comparison algorithm.

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

As you can see the :py:func:`repr()` output of the relationship set shows the
object tree and the :py:func:`unicode()` output (:py:func:`str()` in Python
3.x) is the normalized (sorted) dependency line.

.. warning:: The relationship parsing code does not understand the complete
             syntax defined in the Debian policy manual. More specifically
             architecture restrictions are not supported (because I simply
             don't use them).

.. _Debian policy manual: http://www.debian.org/doc/debian-policy/
.. _chapter 7: http://www.debian.org/doc/debian-policy/ch-relationships.html#s-depsyntax
"""

# Standard library modules.
import logging
import re

# Modules included in our package.
from deb_pkg_tools.compat import basestring, str_compatible, unicode
from deb_pkg_tools.utils import OrderedObject
from deb_pkg_tools.version import compare_versions

# Initialize a logger.
logger = logging.getLogger(__name__)

def parse_depends(relationships):
    """
    Parse a list of package relationships of the form ``python (>= 2.6), python
    (<< 3)``, i.e. a comma separated list of relationship expressions. Uses
    :py:func:`parse_alternatives()` to parse each comma separated expression.
    Raises :py:exc:`ValueError` when parsing fails. Here's an example:

    >>> from deb_pkg_tools.deps import parse_depends
    >>> dependencies = parse_depends('python (>= 2.6), python (<< 3)')
    >>> print(repr(dependencies))
    RelationshipSet(VersionedRelationship(name='python', operator='<<', version='3'),
                    VersionedRelationship(name='python', operator='>=', version='2.6'))
    >>> dependencies.matches('python', '2.5')
    False
    >>> dependencies.matches('python', '2.6')
    True
    >>> dependencies.matches('python', '2.7')
    True
    >>> dependencies.matches('python', '3.0')
    False

    :param relationships: A string containing one or more comma separated
                          package relationships or a list of strings with
                          package relationships.
    :returns: A :py:class:`RelationshipSet` object.
    """
    if isinstance(relationships, basestring):
        relationships = [r for r in relationships.split(',') if r and not r.isspace()]
    return RelationshipSet(*map(parse_alternatives, relationships))

def parse_alternatives(expression):
    """
    Parse an expression containing one or more alternative relationships of the
    form ``python2.6 | python2.7.``, i.e. a list of relationship expressions
    separated by ``|`` tokens. Uses :py:func:`parse_relationship()` to parse
    each ``|`` separated expression. Raises :py:exc:`ValueError` when parsing
    fails. An example:

    >>> from deb_pkg_tools.deps import parse_alternatives
    >>> parse_alternatives('python2.6')
    Relationship(name='python2.6')
    >>> parse_alternatives('python2.6 | python2.7')
    AlternativeRelationship(Relationship(name='python2.6'),
                            Relationship(name='python2.7'))

    :param expression: A relationship expression (a string).
    :returns: A :py:class:`Relationship` object.
    """
    if '|' in expression:
        return AlternativeRelationship(*map(parse_relationship, expression.split('|')))
    else:
        return parse_relationship(expression)

def parse_relationship(expression):
    """
    Parse a relationship expression containing a package name and (optionally)
    a version relation of the form ``python (>= 2.6)``. Raises
    :py:exc:`ValueError` when parsing fails. An example:

    >>> from deb_pkg_tools.deps import parse_relationship
    >>> parse_relationship('python')
    Relationship(name='python')
    >>> parse_relationship('python (<< 3)')
    VersionedRelationship(name='python', operator='<<', version='3')

    :param expression: A relationship expression (a string).
    :returns: A :py:class:`Relationship` object.
    """
    tokens = [t.strip() for t in re.split('[()]', expression) if t and not t.isspace()]
    if len(tokens) == 1:
        # Just a package name (no version information).
        return Relationship(tokens[0])
    elif len(tokens) != 2:
        # Encountered something unexpected!
        msg = "Corrupt package relationship expression: Splitting name from relationship resulted in more than two tokens! (expression: %r, tokens: %r)"
        raise ValueError(msg % (expression, tokens))
    else:
        # Package name followed by relationship to specific version(s) of package.
        name, relationship = tokens
        tokens = [t.strip() for t in re.split('([<>=]+)', relationship) if t and not t.isspace()]
        if len(tokens) != 2:
            # Encountered something unexpected!
            msg = "Corrupt package relationship expression: Splitting operator from version resulted in more than two tokens! (expression: %r, tokens: %r)"
            raise ValueError(msg % (relationship, tokens))
        return VersionedRelationship(name, *tokens)

@str_compatible
class Relationship(OrderedObject):

    """
    A simple package relationship referring only to the name of a package.
    Created by :py:func:`parse_relationship()`.
    """

    def __init__(self, name):
        """
        Initialize a simple relationship.

        :param name: The name of a package (a string).
        """
        self.name = name

    def matches(self, name, version=None):
        """
        Check if the relationship matches a given package and version.

        :param name: The name of a package (a string).
        :param version: The version number of a package (a string, optional).
        :returns: ``True`` if the relationship matches, ``None`` otherwise.
        """
        if self.name == name:
            return True

    def __unicode__(self):
        """
        Serialize a :py:class:`Relationship` object to a Debian package
        relationship expression.
        """
        return self.name

    def __repr__(self):
        """
        Serialize a :py:class:`Relationship` object to a Python expression.
        """
        return "%s(%s)" % (self.__class__.__name__, ', '.join([
            'name=%r' % self.name
        ]))

    def _key(self):
        """
        Get the comparison key of this :py:class:`Relationship` object. Used to
        implement the equality and rich comparison operations.
        """
        return (self.name,)

@str_compatible
class VersionedRelationship(Relationship):

    """
    A conditional package relationship that refers to a package and certain
    versions of that package. Created by :py:func:`parse_relationship()`.
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

    def matches(self, name, version=None):
        """
        Check if the relationship matches a given package and version. Uses the
        external command ``dpkg --compare-versions`` to ensure compatibility
        with Debian's package version comparison algorithm.

        :param name: The name of a package (a string).
        :param version: The version number of a package (a string, optional).
        :returns: ``True`` if the name and version match, ``False`` if only the
                  name matches, ``None`` otherwise.
        """
        if self.name == name:
            if version:
                return compare_versions(version, self.operator, self.version)
            else:
                return False

    def __unicode__(self):
        """
        Serialize a :py:class:`VersionedRelationship` object to a Debian package
        relationship expression.
        """
        return u'%s (%s %s)' % (self.name, self.operator, self.version)

    def __repr__(self):
        """
        Serialize a :py:class:`VersionedRelationship` object to a Python expression.
        """
        return "%s(%s)" % (self.__class__.__name__, ', '.join([
            'name=%r' % self.name,
            'operator=%r' % self.operator,
            'version=%r' % self.version,
        ]))

    def _key(self):
        """
        Get the comparison key of this :py:class:`VersionedRelationship`
        object. Used to implement the equality and rich comparison
        operations.
        """
        return (self.name, self.operator, self.version)

@str_compatible
class AlternativeRelationship(Relationship):

    """
    A package relationship that refers to one of several alternative packages.
    Created by :py:func:`parse_alternatives()`.
    """

    def __init__(self, *relationships):
        """
        Initialize an alternatives relationship.

        :param relationships: One or more :py:class:`Relationship` objects.
        """
        self.relationships = tuple(sorted(relationships))

    def matches(self, name, version=None):
        """
        Check if the relationship matches a given package and version.

        :param name: The name of a package (a string).
        :param version: The version number of a package (a string, optional).
        :returns: ``True`` if the name and version of an alternative match,
                  ``False`` if the name of an alternative was matched but the
                  version didn't match, ``None`` otherwise.
        """
        matches = None
        for alternative in self.relationships:
            alternative_matches = alternative.matches(name, version)
            if alternative_matches == True:
                return True
            elif alternative_matches == False:
                # Keep looking for a match but return False if we don't find one.
                matches = False
        return matches

    def __unicode__(self):
        """
        Serialize an :py:class:`AlternativeRelationship` object to a Debian package
        relationship expression.
        """
        return u' | '.join(map(unicode, self.relationships))

    def __repr__(self):
        """
        Serialize an :py:class:`AlternativeRelationship` object to a Python expression.
        """
        return "%s(%s)" % (self.__class__.__name__, ', '.join(repr(r) for r in self.relationships))

    def _key(self):
        """
        Get the comparison key of this :py:class:`AlternativeRelationship` object. Used to
        implement the equality and rich comparison operations.
        """
        return self.relationships

@str_compatible
class RelationshipSet(OrderedObject):

    """
    A set of package relationships. Created by :py:func:`parse_depends()`.
    """

    def __init__(self, *relationships):
        """
        Initialize a set of relationships.

        :param relationships: One or more :py:class:`Relationship` objects.
        """
        self.relationships = tuple(sorted(relationships))

    def matches(self, name, version=None):
        """
        Check if the set of relationships matches a given package and version.

        :param name: The name of a package (a string).
        :param version: The version number of a package (a string, optional).
        :returns: ``True`` if all matched relationships evaluate to true,
                  ``False`` if a relationship is matched and evaluates to false,
                  ``None`` otherwise.
        """
        results = [r.matches(name, version) for r in self.relationships]
        matches = [r for r in results if r is not None]
        if matches:
            return all(matches)

    def __unicode__(self):
        """
        Serialize a :py:class:`RelationshipSet` object to a Debian package
        relationship expression.
        """
        return u', '.join(map(unicode, self.relationships))

    def __repr__(self, pretty=False, indent=0):
        """
        Serialize a :py:class:`RelationshipSet` object to a Python expression.
        """
        prefix = '%s(' % self.__class__.__name__
        indent += len(prefix)
        delimiter = ',\n%s' % (' ' * indent) if pretty else ', '
        return prefix + delimiter.join(repr(r) for r in self.relationships) + ')'

    def _key(self):
        """
        Get the comparison key of this :py:class:`RelationshipSet` object. Used
        to implement the equality and rich comparison operations.
        """
        return self.relationships

    def __iter__(self):
        """
        Iterate over the relationships in a relationship set.
        """
        return iter(self.relationships)

# vim: ts=4 sw=4 et
