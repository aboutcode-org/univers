univers: mostly universal version and version ranges comparison and conversion
===============================================================================

|Build Status| |License| |Python 3.6+|

.. |Build Status| image:: https://api.travis-ci.com/sbs2001/univers.svg?branch=main&status=passed
.. |License| image:: https://img.shields.io/badge/License-Apache%202.0-blue.svg
   :target: https://scancode-licensedb.aboutcode.org/apache-2.0.html
.. |Python 3.6+| image:: https://img.shields.io/badge/python-3.6+-blue.svg
   :target: https://www.python.org/downloads/release/python-380/



**univers** was born out of the need for a mostly univeral way to store version
ranges and to compare software package versions in VulnerableCode.

Package version ranges and version constraints are useful and essential:

- When resolving the dependencies of a package to express which subset of the
  versions are supported. For instance a dependency requirement statement such
  as "I require package foo, version 2.0 and later versions" defines a range of
  acceptable foo versions.

- When relating a known vulnerability or bug to a range of affected package
  versions. For instance a statement such as "vulnerability 123 affects 
  package bar, version 3.1 and version 4.2 but not version 5" also defines a
  range of affected bar versions.

Existing tools support typically a single algorithm to parse and compare
versions and a single range syntax and this quite different across ecosystems,
each following different versioning rules. For example there's no concept of
'epoch' in semver versioning such used in npm which uses the "node-semver" range
syntax, which is simialr but subtly different from the Rubygems conventions; but
epochs do exist in debian and RPM versions. A tool designed for semver or
dpkg versions processing would not be able to understand the version other
schemes and ranges correctly.

**univers** is different:

- It tracks each ecosystem version scheme and how two versions are compared

- It can parse native version ranges notation into the common "vers" notation
  and can return back native version ranges from a "vers".

- It is designed for use with Package URLs (purl) 


How does **univers** work ?
============================

**univers** wraps, embeds or implements multiple version comparison libraries, each
focused on a specific ecosystem versionning scheme.

It also implements an experimental unified syntax for version ranges specifier
and can parse and convert existing version range strings to this unified syntax.


The supported package ecosystems versioning schemes and underlying libraries is
a wrok in progress and there are some elements of support for:

- semver (for versions since there is no range notation)
  This is supported in part by the `semantic_version <https://github.com/rbarrois/python-semanticversion>`_ library.
- npm that use node-semver ranges and semver versions
- golang (using semver)
- PHP composer
- Rubygems which use a semver-like but not-quite-semver scheme and a slightly different range notation from node-semver

- debian: handled by the 
  `debian-inspector <https://github.com/sbs2001/univers/blob/main/src/univers/debian.py.ABOUT>`_
  library.

- pypi: handled by Python's packaging library and the standard ``packaging.version`` module.
- maven: handled by the embedded `pymaven <https://github.com/nexB/univers/blob/main/src/univers/pymaven.py.ABOUT>`_ library.
- rpm: handled by the embedded `rpm_vercmp <https://github.com/nexB/univers/blob/main/src/univers/rpm.py.ABOUT>`_ library.
- ebuild/gentoo: handled by the embedded `gentoo_vercmp <https://github.com/nexB/univers/blob/main/src/univers/gentoo.py.ABOUT>`_ module.
- arch linux : handled by the embedded `arch utility borrowed from msys2 <https://github.com/nexB/univers/blob/main/src/univers/arch.py.ABOUT>`_ module.

As we grow, new schemes and support for more package types will be implemented accordingly.


Alternative
============

Rather than using ecosystem-specific version schemes and code, another approach
is to use a single procedure for all the versions as implemented in `libversion
<https://github.com/repology/libversion>`_. This works in the most common case
but may not work correctly for specific tasks that demand accurate version
comparison such as for dependency resolution and vulnerabilities checks.
It does not handle version range notations.


Installation
============

    $ pip install univers


Examples
========

Compare two versions using the Python comparison operators:

.. code:: python

    from univers.version import PYPIVersion
    v1 = PYPIVersion("1.2.3")
    v2 = PYPIVersion("1.2.4")
    assert v1 < v2 == True


Test if a version is within or outside of a version range:

.. code:: python

    from univers.version import PYPIVersion
    from univers.version_range import VersionRange

    range = VersionRange.from_vers("vers:pypi/>=1.2.4")

    assert PypiVersion("1.2.4") in range
    assert PypiVersion("1.2.4") not in range


Development
============

Starting from a git clone of https://github.com/nexB/univers run these::

    $ configure --dev
    $ source venv/bin/active
    $ pytest -vvs


We use the same development process as other AboutCode projects.

Visit https://github.com/nexB/univers and
https://gitter.im/aboutcode-org/vulnerablecode and
https://gitter.im/aboutcode-org/aboutcode for support and chat.


Primary license: Apache-2.0
SPDX-License-Identifier: Apache-2.0 AND BSD-3-Clause AND MIT
