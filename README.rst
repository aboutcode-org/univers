univers: mostly universal version and version ranges comparison and conversion
===============================================================================

|Build Status| |License| |Python 3.6+|

.. |Build Status| image:: https://api.travis-ci.com/sbs2001/univers.svg?branch=main&status=passed
.. |License| image:: https://img.shields.io/badge/License-Apache%202.0-blue.svg
   :target: https://scancode-licensedb.aboutcode.org/apache-2.0.html
.. |Python 3.6+| image:: https://img.shields.io/badge/python-3.6+-blue.svg
   :target: https://www.python.org/downloads/release/python-380/


**univers** was born out of the need for a mostly universal way to store version
ranges and to compare two software package versions in VulnerableCode.

Package version ranges and version constraints are useful and essential:

- When relating a known vulnerability or bug to a range of affected package
  versions. For instance a statement such as "vulnerability 123 affects
  package bar, version 3.1 and version 4.2 but not version 5" defines a
  range of bar versions affected by a vulnerability.

- When resolving the dependencies of a package to express which subset of the
  versions are supported. For instance a dependency requirement statement such
  as "I require package foo, version 2.0 and later versions" defines a range of
  acceptable foo versions.

Version syntaxes and range notations are quite different across ecosystems,
making it is difficult to process versions and version ranges across ecosystems
in a consistent way.

Existing tools and libraries typically support a single algorithms to parse and
compare versions with a single version range notation for a single package
ecosystem.


**univers** is different:

- It tracks each ecosystem versioning scheme and how two versions are compared.

- It support a growing number of package ecosystems versioning in a single
  library.

- It can parse version range strings using their native notation (such as an npm
  range) into the common "vers" notation and internal object model and can
  return back a native version range string rebuilt from a "vers" range.

- It is designed to work with `Package URLs (purl) <https://github.com/package-url>`_.


How does **univers** work ?
============================

**univers** wraps, embeds and implements multiple version comparison libraries,
each focused on a specific ecosystem versioning scheme.

For each scheme, **univers** provides an implementation for:

- the version comparison procedure e.g, how to compare two versions,
- parsing and converting from a native version range notation to the
  **univers** normalized and unified internal model,
- converting a range back to its scheme-native range syntax and to the
  ``vers`` syntax.

**univers** implements ``vers``, an experimental unified and mostly universal
version range syntax. It can parse and convert an existing native version range
strings to this unified syntax. For example, this means:

- converting ">=1.2.3" as used in a Python package into ``vers:pypi/>=1.2.3``,

- or converting "^1.0.2" as used in an npm package dependency declaration into
  ``vers:npm/>=1.0.2|<2.0.0``

The supported package ecosystems versioning schemes and underlying libraries
include:

- npm that use the "node-semver" ranges notation and the semver versions syntax
  This is supported in part by the `semantic_version
  <https://github.com/rbarrois/python-semanticversion>`_ library.

- pypi: handled by Python's packaging library and the standard
  ``packaging.version`` module.

- Rubygems which use a semver-like but not-quite-semver scheme and there can be
  commonly more than three version segments.
  Gems also use a slightly different range notation from node-semver with
  different operators and slightly different semantics: for instance it uses "~>"
  as a pessimistic operator and supports exclusion with != and does not support
  "OR" between constraints (that it call requirements).
  Gem are handled by Python port of the Rubygems requirements and version
  handling code from the `puppeteer tool
  <https://github.com/aboutcode-org/univers/blob/main/src/univers/debian.py.ABOUT>`_

- debian: handled by the  `debian-inspector library
  <https://github.com/aboutcode-org/univers/blob/main/src/univers/debian.py.ABOUT>`_.

- maven: handled by the embedded `pymaven library
  <https://github.com/aboutcode-org/univers/blob/main/src/univers/pymaven.py.ABOUT>`_.

- rpm: handled by the embedded `rpm_vercmp library
  <https://github.com/aboutcode-org/univers/blob/main/src/univers/rpm.py.ABOUT>`_.

- golang (using semver)

- PHP composer

- ebuild/gentoo: handled by the embedded `gentoo_vercmp module
  <https://github.com/aboutcode-org/univers/blob/main/src/univers/gentoo.py.ABOUT>`_.

- arch linux: handled by the embedded `arch utility module borrowed from msys2
  <https://github.com/aboutcode-org/univers/blob/main/src/univers/arch.py.ABOUT>`_.

- Alpine linux: handled using the base Gentoo version support and extras
  specific to Alpine.


The level of support for each ecosystem may not be even for now and new schemes
and support for more package types are implemented on a continuous basis.


Alternative
============

Rather than using ecosystem-specific version schemes and code, another approach
is to use a single procedure for all the versions as implemented in `libversion
<https://github.com/repology/libversion>`_. ``libversion`` works in the most
common case but may not work correctly when a task that demand precise version
comparisons such as for dependency resolution and vulnerability lookup where
a "good enough" comparison accuracy is not acceptable. ``libversion`` does not
handle version range notations.


Installation
============

    $ pip install univers


Examples
========

Compare two native Python versions:

.. code:: python

    from univers.versions import PypiVersion
    assert PypiVersion("1.2.3") < PypiVersion("1.2.4")


Normalize a version range from an npm:

.. code:: python

    from univers.version_range import NpmVersionRange
    range = NpmVersionRange.from_native("^1.0.2")
    assert str(range) == "vers:npm/>=1.0.2|<2.0.0"


Test if a version is within or outside a version range:

.. code:: python

    from univers.versions import PypiVersion
    from univers.version_range import VersionRange

    range = VersionRange.from_string("vers:pypi/>=1.2.4")

    assert PypiVersion("1.2.4") in range
    assert PypiVersion("1.2.3") not in range


Development
============

Run these commands, starting from a git clone of https://github.com/aboutcode-org/univers ::

    $ ./configure --dev
    $ source venv/bin/active
    $ pytest -vvs


We use the same development process as other AboutCode projects.

Visit https://github.com/aboutcode-org/univers and
https://gitter.im/aboutcode-org/vulnerablecode and
https://gitter.im/aboutcode-org/aboutcode for support and chat.


Primary license: Apache-2.0
SPDX-License-Identifier: Apache-2.0 AND BSD-3-Clause AND MIT


Acknowledgements, Funding, Support and Sponsoring
--------------------------------------------------------

This project is funded, supported and sponsored by:

- Generous support and contributions from users like you!
- the European Commission NGI programme
- the NLnet Foundation 
- the Swiss State Secretariat for Education, Research and Innovation (SERI)
- Google, including the Google Summer of Code and the Google Seasons of Doc programmes
- Mercedes-Benz Group
- Microsoft and Microsoft Azure
- AboutCode ASBL
- nexB Inc. 



|europa|   |dgconnect| 

|ngi|   |nlnet|   

|aboutcode|  |nexb|



This project was funded through the NGI0 PET Fund, a fund established by NLnet with financial
support from the European Commission's Next Generation Internet programme, under the aegis of DG
Communications Networks, Content and Technology under grant agreement No 825310.

|ngizeropet|  https://nlnet.nl/project/VulnerableCode/


This project was funded through the NGI0 Discovery Fund, a fund established by NLnet with financial
support from the European Commission's Next Generation Internet programme, under the aegis of DG
Communications Networks, Content and Technology under grant agreement No 825322.

|ngidiscovery| https://nlnet.nl/project/vulnerabilitydatabase/


This project was funded through the NGI0 Core Fund, a fund established by NLnet with financial
support from the European Commission's Next Generation Internet programme, under the aegis of DG
Communications Networks, Content and Technology under grant agreement No 101092990.

|ngizerocore| https://nlnet.nl/project/VulnerableCode-enhancements/


This project is funded through the NGI0 Entrust Fund, a fund established by NLnet with financial
support from the European Commission's Next Generation Internet programme, under the aegis of DG
Communications Networks, Content and Technology under grant agreement No 101069594.

|ngizeroentrust| https://nlnet.nl/project/FederatedSoftwareMetadata/


This project was funded through the NGI0 Commons Fund, a fund established by NLnet with financial
support from the European Commission's Next Generation Internet programme, under the aegis of DG
Communications Networks, Content and Technology under grant agreement No 101135429. Additional
funding is made available by the Swiss State Secretariat for Education, Research and Innovation
(SERI). 

|ngizerocommons| |swiss| https://nlnet.nl/project/FederatedCodeNext/


This project was funded through the NGI0 Entrust Fund, a fund established by NLnet with financial
support from the European Commission's Next Generation Internet programme, under the aegis of DG
Communications Networks, Content and Technology under grant agreement No 101069594. 

|ngizeroentrust| https://nlnet.nl/project/CRAVEX/



.. |nlnet| image:: https://nlnet.nl/logo/banner.png
    :target: https://nlnet.nl
    :height: 50
    :alt: NLnet foundation logo

.. |ngi| image:: https://ngi.eu/wp-content/uploads/thegem-logos/logo_8269bc6efcf731d34b6385775d76511d_1x.png
    :target: https://ngi.eu35
    :height: 50
    :alt: NGI logo

.. |nexb| image:: https://nexb.com/wp-content/uploads/2022/04/nexB.svg
    :target: https://nexb.com
    :height: 30
    :alt: nexB logo

.. |europa| image:: https://ngi.eu/wp-content/uploads/sites/77/2017/10/bandiera_stelle.png
    :target: http://ec.europa.eu/index_en.htm
    :height: 40
    :alt: Europa logo

.. |aboutcode| image:: https://aboutcode.org/wp-content/uploads/2023/10/AboutCode.svg
    :target: https://aboutcode.org/
    :height: 30
    :alt: AboutCode logo

.. |swiss| image:: https://www.sbfi.admin.ch/sbfi/en/_jcr_content/logo/image.imagespooler.png/1493119032540/logo.png
    :target: https://www.sbfi.admin.ch/sbfi/en/home/seri/seri.html
    :height: 40
    :alt: Swiss logo

.. |dgconnect| image:: https://commission.europa.eu/themes/contrib/oe_theme/dist/ec/images/logo/positive/logo-ec--en.svg
    :target: https://commission.europa.eu/about-european-commission/departments-and-executive-agencies/communications-networks-content-and-technology_en
    :height: 40
    :alt: EC DG Connect logo

.. |ngizerocore| image:: https://nlnet.nl/image/logos/NGI0_tag.svg
    :target: https://nlnet.nl/core
    :height: 40
    :alt: NGI Zero Core Logo

.. |ngizerocommons| image:: https://nlnet.nl/image/logos/NGI0_tag.svg
    :target: https://nlnet.nl/commonsfund/
    :height: 40
    :alt: NGI Zero Commons Logo

.. |ngizeropet| image:: https://nlnet.nl/image/logos/NGI0PET_tag.svg
    :target: https://nlnet.nl/PET
    :height: 40
    :alt: NGI Zero PET logo

.. |ngizeroentrust| image:: https://nlnet.nl/image/logos/NGI0Entrust_tag.svg
    :target: https://nlnet.nl/entrust
    :height: 38
    :alt: NGI Zero Entrust logo

.. |ngiassure| image:: https://nlnet.nl/image/logos/NGIAssure_tag.svg
    :target: https://nlnet.nl/image/logos/NGIAssure_tag.svg
    :height: 32
    :alt: NGI Assure logo

.. |ngidiscovery| image:: https://nlnet.nl/image/logos/NGI0Discovery_tag.svg
    :target: https://nlnet.nl/discovery/
    :height: 40
    :alt: NGI Discovery logo






