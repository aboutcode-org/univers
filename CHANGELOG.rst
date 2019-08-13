==========
Change Log
==========

All notable changes to this project will be documented in this file.

The format is based on `Keep a Changelog`_
and this project adheres to `Semantic Versioning`_.

`Unreleased`_
=============

Changed
-------

* Use pbr for release management
* Add support for python 3.4, 3.5, and 3.6.
* Pom objects can now be loaded from a file or string and do not require
  a maven client.

Fixed
-----

* Add license_file entry to setup.cfg
* Create cache dir securely and usable on non-POSIX filesystems.

Deprecated
----------

* Drop support for python 2.6

`0.2.0`_ - 2017-06-07

Changed
-------

* Unpin dependency versions. Allow major version compatibility.

`0.1.0`_ - 2015-10-10

Added
-----

* A simple maven repository client that can fetch and search for artifacts and
  metadata.
* Support for local and http maven repositories.
* A simple cache for http maven repositories
* A python binding to POM data that dynamically loads information from POM
  inheritance and dependency management.
* Python implementation of Maven version comparision and Maven version ranges.

.. _Keep a Changelog: http://keepachangelog.com/
.. _Semantic Versioning: http://semver.org/
.. _0.1.0: https://github.com/sassoftware/pymaven/compare/114b10e...3a844cd
.. _0.2.0: https://github.com/sassoftware/pymaven/compare/3a844cd...f99a287
.. _Unreleased: https://github.com/sassoftware/pymaven/compare/f99a287...HEAD
