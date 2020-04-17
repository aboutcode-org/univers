debut: Utilities to parse Debian package, copyright and control files
=====================================================================

The Python package `debut` is a collection of utilities to parse various Debian
package manifests, machine readable copyright and control files collectively
known as the Debian 822 format (based on the RFC822 email format).

Why the name `debut`? That's a portmanteau of DEBian and UTilities!


Origin
------

This library is based on a heavily modified and remixed combo of original code
with code from several other origins:

* python-deb-pkg-tools from @xolox for its handling of Debian packages and the
  parsing of dependencies and other package-to-package relationship fields.
  See https://github.com/xolox/python-deb-pkg-tools

* dlt (Debian license tools) from @agustinhenze for its check of the
  coverage of a license file Files sections and a lot of inspiration.
  See https://github.com/agustinhenze/dlt/

* PGPy from @SecurityInnovation and @Commod0re for its ability to remove a PGP
  signature from an email. dsc (Debian Source Control) files are typically
  PGP-signed.
  See https://github.com/SecurityInnovation/PGPy

* python-dpkg by @TheClimateCorporation and @memory for its ability to process
  the syntax of Debian versions and to compare them according to the spec.
  See https://github.com/TheClimateCorporation/python-dpkg


Why?
----

Why create this seemingly redundant library? The official python-debian tools
and several other utilities already provide similar capabilities!

On the surface this is correct, but there are several differences and reasons
listed here:

* Existing tools are parsing control files rather strictly. This library tries
  to be more flexible. For instance it can recognize and fix some almost
  correct copyright files that are not fully "machine readable" but close
  enough to the spec to be worthy of recovery.

* Several of these tools have to deal with a lot of legacy compatibility. We
  do not have such need. For instance, the Python standard library email module
  and one line of code is enough to parse a Debian 822 file fields. I doubt
  thatthis feature was available in the standard library when python-debian was
  started but it is here now and this vastly simplifies the code.

* This library focus is to parse and inspect control files and much less so to
  emit and create them, so the code and tests can be much simpler. For instance,
  rather than using somewhat more complex case-insensitive dictionary keys while
  preserving case for Deb822-like objects, this library uses lower case keys
  throughout.

* The official python-debian library is GPL-licensed making it it hard to
  combine with Apache-licensed libraries. I went through efforts to
  work out a relicensing of python-debian with all its authors such that it
  could be integrated in permissive-licensed Python tools. Even though most
  current maintainers and contributors were OK with that relicensing to a
  permissive or an LGPL license, I could not get a reply and agreement from
  some important legacy authors: therefore the relicensing could not happen.


License
-------

SPDX-License-Identifier: Apache-2.0 AND BSD-3-Clause AND MIT

This software combines several origins each with their own license.
All these licenses apply as all original files have been refactored and remixed
significantly::

    Copyright nexB Inc. and others.
    Copyright (c) 2018 Peter Odding.
    Copyright 2017 The Climate Corporation (https://climate.com)
    Copyright (c) 2014-2019 Security Innovation, Inc
    Copyright 2013 Agustin Henze <tin@sluc.org.ar>

Note that the tests/ may also contain files using other FOSS licenses.
