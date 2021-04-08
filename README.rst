Univers: Ecosystem specific version comparision and conversion
==============================================================

|Build Status| |License| |Python 3.6+|

.. |Build Status| image:: https://api.travis-ci.com/sbs2001/univers.svg?branch=main&status=passed
   :target: https://github.com/nexB/vulnerablecode/actions?query=workflow%3ACI
.. |License| image:: https://img.shields.io/badge/License-Apache%202.0-blue.svg
   :target: https://opensource.org/licenses/Apache-2.0
.. |Python 3.6+| image:: https://img.shields.io/badge/python-3.6+-blue.svg
   :target: https://www.python.org/downloads/release/python-380/



Why ecosystem specific ?
========================

Univers was born out of the need for version comparision at VulnerableCode. Existing
tools follow a particular algorithm to evaluate and compare versions. This is not 
accurate across different ecosystems, since they follow different versioning rules. For 
example there's no concept of 'epoch' in  semver based ecosystem like npm or ruby gems, but
epochs do exist in  debian ecosystem. The tools solely based on semver or dpkg version spec therefore
give different and wrong results in both cases.

Univers is different, it considers the ecosystem of version.

How Univers works ?
===================

Univers, can be considered as a wrapper around many version comparision libraries, each of which
solving the problem for the respective ecosystem. It delegates the actual comparision to these libraries
depending upon the ecosystem.


The supported ecosystems and underlying libraries are: 

- npm, golang, php-composer, ruby-gems and others which follow the semver spec. These use `semantic_version <https://github.com/rbarrois/python-semanticversion>`_ library.
- debian, this is handled by `debian-inspector <https://github.com/sbs2001/univers/blob/main/src/univers/debian.py.ABOUT>`_ library.
- pypi, this is handled by Python's ``packaging.version`` module.
- maven, this is handled by   `rpm_vercmp <https://github.com/sbs2001/univers/blob/main/src/univers/rpm.py.ABOUT>`_ library.

Installation
============

        $ pip install univers

Examples
========

Comparing discrete versions

.. code:: python

    from univers.version import PYPIVersion
    v1 = PYPIVersion("1.2.3")
    v2 = PYPIVersion("1.2.4")
    assert v1 < v2 == True


Evaluating version ranges

.. code:: python

    from univers.version import PYPIVersion
    from univers.version_specifier import VersionSpecifier

    vs = VersionSpecifier.from_scheme_version_spec_string("pypi", ">=1.2.4")
    v1 = PYPIVersion("1.2.4")
    v2 = PYPIVersion("1.2.3")

    assert (v1 in vs ) == True
    assert (v2 in vs ) == False
