======================================================
vers: a mostly universal version range specifier
======================================================

This specification is a new syntax for dependency and vulnerable version ranges.


Context
--------

Software package version ranges and version constraints are essential:

- When resolving the dependencies of a package to express which subset of the
  versions are supported. For instance a dependency or requirement statement
  such as "I require package foo, version 2.0 or later versions" defines a
  range of acceptable foo versions.

- When stating that a known vulnerability or bug affects a range of package
  versions. For instance a security advisory such as "vulnerability 123 affects
  package bar, version 3.1 and version 4.2 but not version 5" defines a range of
  vulnerable "bar" package versions.

Version ranges can be replaced by a list enumerating all the versions of
interest. But in practice, all the versions may not yet exist when defining an
open version range such as "v2.0 or later".

Therefore, a version range is a necessary, compact and practical way to
reference multiple versions rather than listing all the versions.


Problem
--------

Several version range notations exist and have evolved separately to serve the
specific needs of each package ecosystem, vulnerability databases and tools.

There is no (mostly) universal notation for version ranges and there is no
universal way to compare two versions, even though the concepts that exist in
most version range notations are similar.

Each package type or ecosystem may define their own ranges notation and version
comparison semantics for dependencies. And for security advisories, the lack of
a portable and compact notation for vulnerable package version ranges means that
these ranges may be either ambiguous or hard to compute and may be best replaced
by complete enumerations of all impacted versions, such as in the `NVD CPE Match
feed <https://nvd.nist.gov/vuln/data-feeds#cpeMatch>`_.

Because of this, expressing and resolving a version range is often a complex, or
error prone task.

In particular the need for common notation for version has emerged based on the
usage of Package URLs referencing vulnerable package version ranges such as in
vulnerability databases like `VulnerableCode
<https://github.com/nexB/vulnerablecode/>`_.

To better understand the problem, here are some of the notations and conventions
in use:

- Rubygems strongly suggest using semver but does not enforce it
  https://guides.rubygems.org/patterns/#semantic-versioning

- node-semver ranges are used in npms https://github.com/npm/node-semver#ranges
  with semantics specific to semver and node and npm.

- Dart pub versioning scheme is similar to node-semver and the documentation at
  https://dart.dev/tools/pub/versioning provides a comprehensive coverage of the
  topic of versioning. But version resolution is using its own algorithm.

- Python uses its own version ranges notation https://www.python.org/dev/peps/pep-0440/

- Debian and Ubuntu use their own notation
  https://www.debian.org/doc/debian-policy/ch-relationships.html

- RPM distros use their own range notation
  https://rpm-software-management.github.io/rpm/manual/dependencies.html

- Perl CPAN define its own version range notation similar to this specification:
  https://metacpan.org/pod/CPAN::Meta::Spec#Version-Ranges

- Apache Maven and NuGet use math intervals notation
  https://en.wikipedia.org/wiki/Interval_(mathematics)
  - Apache Maven http://maven.apache.org/enforcer/enforcer-rules/versionRanges.html
  - NuGet https://docs.microsoft.com/en-us/nuget/concepts/package-versioning#version-ranges

- Gentoo and Alpine Linux use comparison operators similar to this specification:
  - Gentoo https://wiki.gentoo.org/wiki/Version_specifier
  - Alpine linux https://gitlab.alpinelinux.org/alpine/apk-tools/-/blob/master/src/version.c

- Arch Linux https://wiki.archlinux.org/title/PKGBUILD#Dependencies use a
  simplified notation for its PKGBUILD depends array with comparison operators
  similar to this specification.

- Go modules https://golang.org/ref/mod#versions use semver versions with
  specific version resolution algorithms.

- Haskell Package Versioning Policy https://pvp.haskell.org/ provides a notation
  similar to this specification based on a modified semver with extra notations
  such as star and caret.

- The NVD https://nvd.nist.gov/vuln/data-feeds#cpeMatch defines CPE ranges as
  lists of version start and end either including or excluding the start or end
  version. And also provides a concrete enumeration of the available ranges as
  a daily feed.

Note that there is a closely related problem as the way two versions are compared
as equal, lesser or greater is often complex.

Each package ecosystem may have evolved its own peculiar version comparison
procedure. 

For instance, semver is a prominent specification in this domain but this is
just one of the many ways to structure a version string.

Debian, RPM, PyPI,  Rubygems, and Composer have their own subtly different
approach on how to determine which version is greater or lesser.


Solution
---------

A solution to the many version range syntaxes is to design a new notation to
unify them all with:

- a mostly universal and minimalist notation to express the version range
  notations from many different package types and ecosystems.

- the package type-specific definitions to normalize existing range expressions
  to this common notation .

- the designation of which algorithm or procedure to use when comparing two
  versions such that it is possible to resolve if a version is within or
  outside of a version range.

We call this solution "version range specifier" or "vers" and it is described
in this document.


Version range specifier
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A version range specifier (aka. "vers") is a URI string using the ``vers``
URI-scheme with this syntax::

   vers:<versioning-scheme>/<version-constraint>,<version-constraint&version-constraint>,...

For example to define a set of versions that contains either version ``1.2.3``,
or any versions greater than or equal to ``2.0.0`` but less than ``5.0.0`` using
the `semver` versioning scheme, the version range specifier will be::

    vers:semver/1.2.3,>=2.0.0&<5.0.0

Each ``<version-constraint>`` in the comma-separated list is either a simple
constraint such as::

    <comparator:version>

Or a composite constraint grouping multiple ``<version-constraint>`` joined by
an ampersand such as::

    <comparator:version>&<comparator:version>...

The comma is a logical `OR` and the ampersand is a logical `AND`.

A version range specifier is therefore an "OR of ANDs". This is also called a
"disjunctive normal form" in boolean logic.
See https://en.wikipedia.org/wiki/Disjunctive_normal_form for details.

``vers`` is the URI-scheme and is an acronym for "VErsion Range Specifier". It
has been selected because it is short, obviously about version and available
for a future formal registration for this URI-scheme at the IANA registry.


``<versioning-scheme>``
------------------------

The ``<versioning-scheme>`` (such as ``semver``,
``debian``, etc.) determines:

- the specific notation and conventions used for a version string encoded in
  this scheme. Versioning schemes often specify a version segments separator and
  the meaning of each version segments, such as [major.minor.patch] in semver.

- how two versions compare as greater or lesser to determine if a version is
  within or outside a range.

- how a versioning scheme-specific range notation can be transformed in the
  ``vers`` notation defined here.

Note: the ``<versioning-scheme>`` does not define which symbols to use to
compare versions, and how to compose these as this is the substance of this
specification.

The ``<versioning-scheme>`` is followed by a slash "/".

Then there are one or more ``<version-constraint>`` separated by a comma ","
meaning that **any** of these constraints must be satisfied for a version to be
resolved as within this range specifier.


``<version-constraint>``
----------------------------

Each  ``<version-constraint>`` of this comma-separated list can be either a
single constraint or a list of constraints separated by an ampersand "&" as in
``1.2.3,>=2.0.0&<5.0.0``.

Multiple ``<version-constraint>`` combined with an ampersand means that **all**
these constraints must be satisfied for a version to be resolved as within this
range.

Each simple version constraint has this syntax::

    <comparator><version>

The ``<comparator>`` is one of these comparison operators:

- "=": Version equality comparator. It is the default and implied if not
  present and means that a version must be equal to the provided version.
  For example: "=1.2.3". It must be omitted in the canonical representation.
  Equality is based on the equality of two lower-cased and normalized version
  strings and is not versioning scheme-specific.

- "!=": Version exclusion or inequality comparator. This means a version must
  not be equal to the provided version and this version must be excluded from
  the range. For example: "!=1.2.3" means that version "1.2.3" is excluded.

- "<", "<=": Less than or less-or-equal version comparators points to all
  versions less than or equal to the provided version. For example "<=1.2.3"
  means less than or equal to "1.2.3". 

- ">", ">=": Greater than or greater-or-equal version comparators points to
  all versions greater than or equal to the provided version. For example
  ">=1.2.3" means greater than or equal to "1.2.3".

- The way two version strings are compared using these comparators is defined
  by the ``<versioning-scheme>``.

- The structure and meaning of a version string such as "1.2.3" is defined by
  the ``<versioning-scheme>``. For instance, ``semver`` defines three
  dot-separated segments name major, minor and patch.

- The special star "*" ``<version-constraint>`` matches any version. This star
  constraint must be used **alone** in a version range specifier, exclusive of
  any other constraint. For example "vers:debian/\*" resolves to any version.


Examples
~~~~~~~~~

TODO.


Normalized or canonical representation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- A version range specifier contains only printable ASCII letters, digits and
  punctuation.

- Spaces are not significant and are removed in the canonical form. For example
  "!=1.2.3" and " ! = 1.2. 3" are equivalent. And so are "1.2.3 & < = 2.0.0" and
  "1.2.3&<=2.0.0"

- A version range specifier is case-insensitive and lowercase in canonical form.

- The ordering of multiple ``<version-constraint>`` in a range specifier is not
  significant. The canonical ordering is by sorting these by lexicographical
  order applied with this approach:

  - first to each sub-list of ampersand-separated ``<version-constraint>``.
  - then to the list of comma-separated ``<version-constraint>``.

- A version in a ``<version-constraint>`` can only contain printable ASCII
  characters excluding the special characters used as separators and comparators
  ``><=!,&*``. If it contains special characters (which should be rare in
  practice) the version string in a constraint must be quoted using the URL
  quoting rules.


Using version range specifiers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``vers`` primary usage is to test if a version is within or outside a range.

An input version is within a range specifier if it matches or satisfies **any**
of the ranges in this spec. To match a range, an input version must match
**all** the version constraints of a range. Otherwise, the input version is
outside of the range specifier.

Some important usages derived from this primary usage include:

- **Resolving a version range specifier to a list of concrete versions.**
  In this case, the input is the set of known versions of a package (typically
  obtained from some package repository or registry). Each version is then
  tested individually to check if it is within or outside the ranges. For
  example, this can be used to determine which existing package versions are
  affected by a known vulnerability if they match the vulnerability version
  range specifier.

- **Selecting one of several versions that are within a range.**
  For example, package management tools need to determine what are the dependent
  package versions of a package instance based the acceptable version ranges
  provided with each dependency. This usually requires deploying heuristics and
  algorithms (possibly complex such as sat solvers) that are versioning-scheme-
  and tool-specific and outside of the scope for this specification; ``vers``
  scope is limited to provide an input to the resolution process.


Parsing version range specifiers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To parse a version range specifier string:

- Remove all spaces and tabs.
- Start from left, and split once on colon ":".
- The left hand side is the URI-scheme that must be lowercase.
  - Verify that the URI-scheme value is ``vers``.
- The right hand side is the specifier.

- Split the specifier from left once on a slash "/".
- The left hand side is the <versioning-scheme> that must be lowercase.
- The right hand side is the constraints.

- If the constraint contains a star "*", validate that it is equal to "*".
  <version-constraint> is "*". Parsing is done and no further processing is
  needed for this ``vers``. A tool may be strict and report an error
  if there are extra characters beyond "*" or be lenient.

- Split the ranges on comma ",". The result is a list of <version-constraint>
  strings.
- Remove any empty strings from the list of <version-constraint>.

- For each <version-constraint> in this list:

  - Split on ampersand "&". The result is a sub-list of <version-constraint>.
  - Remove any empty strings from this sub-list.

  - For each <version-constraint> in this sub-list:

    - Split the <version-constraint> comparator and version starting from left
      based on the start of the <version-constraint>:

       - If it starts with "=", split it once on "=".
       - If it starts with "!=", split it once on "!=".
       - If it starts with "<=", split it once on "<=".
       - If it starts with ">=", split it once on ">=".
       - If it starts with "<", split it once on "<".
       - If it starts with ">", split it once on ">".
       - Otherwise if there is no split, the comparator is "=" (default) and the
         version is the <version-constraint> string.

    - After the split, the left hand side is the comparator, and the right hand
      is the version.

    - Validate that the version is not empty.

    - If the version contains a percent "%" character, apply URL quoting rules
      to unquote this string.

    - Yield the comparator and version for this constraint

  - Yield the accumulated list of (comparator and version) that must apply for
    this constraint

- Finally return the <versioning-scheme> and the list of <version-constraint>


Notes and caveats
~~~~~~~~~~~~~~~~~~~

- Comparing versions from two different versioning schemes is unspecified. Even
  though there may be some similarities between the `semver` version of an npm
  and the `debian` version of its Debian packaging, these similarities are
  specific to each versioning scheme. Tools may report an error in these
  cases.

- Schemes are related to Package URL types (aka. ecosystems) in the sense that
  each Package URL type has one versioning scheme, but multiple types can reuse
  the same versioning scheme (such as semver).

- Some package types may use the same versioning scheme such as semver to
  compare two versions, but may not use the same notation for version ranges.


Some of the known versioning schemes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

TODO: add details on how to convert to and from ``vers`` for a given versioning
scheme and package type.

- ``debian``: Debian and Ubuntu https://www.debian.org/doc/debian-policy/ch-relationships.html
   The comparators are <<, <=, =, >= and >>.

- ``rpm``: RPM distros https://rpm-software-management.github.io/rpm/manual/dependencies.html
  The version comparison routine of rmpvercmp is also used by archlinux Pacman.

- ``rubygems``: Rubygems https://guides.rubygems.org/patterns/#semantic-versioning
  which is almost but not exactly semver.

- ``semver``: node-semver as used for npm https://github.com/npm/node-semver#ranges
  It is also used by Rust: https://doc.rust-lang.org/cargo/reference/specifying-dependencies.html
  and several other package types. `composer` may need its own scheme as this is
  not strictly semver.

- ``python``: Python https://www.python.org/dev/peps/pep-0440/

- ``perl``: Perl https://perlmaven.com/how-to-compare-version-numbers-in-perl-and-for-cpan-modules

- ``go``: Go modules https://golang.org/ref/mod#versions use semver versions
  with a specific minimum version resolution algorithm.

- ``maven``: Apache Maven http://maven.apache.org/enforcer/enforcer-rules/versionRanges.html

- ``nuget``: NuGet https://docs.microsoft.com/en-us/nuget/concepts/package-versioning#version-ranges
  Note that Apache Maven and NuGet are following a similar approach with a
  math-derived intervals syntax as in https://en.wikipedia.org/wiki/Interval_(mathematics)

- ``gentoo``: Gentoo https://wiki.gentoo.org/wiki/Version_specifier

- ``alpine``: Alpine linux https://gitlab.alpinelinux.org/alpine/apk-tools/-/blob/master/src/version.c
  (which might be using Gentoo conventions)

- ``generic``: a generic version comparison algorithm (which is TBD, likely a
  split on punctuation and dealing with digit vs. strings comparisons, like is
  done in libversion)



Implementations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Python: https://github.com/nexB/univers
- Yours!


Why not reuse existing version range notations?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Most existing version range notations are tied to a specific version string
syntax and are therefore not readily applicable to other contexts. For example,
the use of elements such as tilde and caret ranges in Ruby or Dart notations
implies that a certain structure exists in the version string (semver or semver-
like). The inclusion of these additional comparators is a result of the history
and evolution in a given package ecosystem to address specific needs.

In practice, the unified and reduced set of comparators and syntax defined for
``vers`` has been designed such that all these notations can be converted to a
``vers`` and back from a ``vers`` to the original notation. 

In contrast, this would not be possible with existing notations. For instance,
the Python notation may not work with npm versions and reciprocally.

There are likely to be a few rare cases where round tripping from and to
``vers`` may not be possible, and in anycase round tripping to and from ``vers``
may only produce equivalent results and not strictly the same original strings.

Another issue with existing version range notations is that, they are primarily
meant to be used for dependency constraints and may not readily be reused for
vulnerable ranges. In particular, a vulnerability may exist for multiple
"branches" of a given package (such as Django 2, 3 and 4) which may not be
possible to express with a notation designed exclusively for dependent versions
resolution.


Why not use the NVD CPE Ranges?
###############################

- https://nvd.nist.gov/vuln/vulnerability-detail-pages#divRange
- https://nvd.nist.gov/developers/vulnerabilities#divResponse
- https://csrc.nist.gov/schema/nvd/feed/1.1/nvd_cve_feed_json_1.1.schema

The version ranges notation defined in the JSON schema of the CVE API payload
uses these four fields: ``versionStartIncluding``, ``versionStartExcluding``,
``versionEndIncluding`` and ``versionEndExcluding``. For example::

    "versionStartIncluding": "7.3.0",
    "versionEndExcluding": "7.3.31",
    "versionStartExcluding" : "9.0.0",
    "versionEndIncluding" : "9.0.46",

In addition to these ranges, the NVD publishes a list of concrete CPE with
versions resolved for a range with daily updates at
https://nvd.nist.gov/vuln/data-feeds#cpeMatch 

Note that the NVD CVE configuration is a complex specification that goes well
beyond version ranges and is used to match comprehensive configurations across
multiple products and version ranges. ``vers`` focus is exclusively versions.

The NVD JSON notation is verbose in contrast with ``vers`` that attempts to
provide a compact notation. It provides the same =, <=, < and > comparators
specified in ``vers`` and found in other notations.


Why not use node-semver ranges?
###############################

https://github.com/npm/node-semver#ranges

The node semver is very similar to this spec (this is also an OR of ANDs) but it
has a few practical issues:

- The space means "AND" and significant whitespace in a single string makes
  normalization more complicated and may be a source of confusion or errors. The
  explicit ampersand used as "AND" operator specified here improves clarity.

- There is no negation "!=" operator meaning that some version constraints are
  difficult to express and require combining < and > comparators. For instance
  stating that a vulnerability affects babel 6.2 or later but not babel 7.0 is
  possible but difficult.

- The advanced range syntax has grown to be rather complex using hyphen, stars,
  carets and tilde constructs are all tied to the JavaScript and npm ways of
  handling versions in their specific ecosystem and furthermore are bound to the
  semver semantics. These are not readily reusable elsewhere. And these multiple
  comparators and modifiers make the grammar and parsing more complex.


Why not use Python pep-0440 ranges?
#####################################

https://www.python.org/dev/peps/pep-0440/#version-specifiers

The Python pep-0440 "Version Identification and Dependency Specification"
provides a comprehensive specification for Python package versioning and a
notation for "version specifiers" to express dependencies version constraints.

This specification is mostly compatible with and is similar to this ``vers``
spec, but has a richer notation with some aspects specific to the version used
only in the Python ecosystem.

- In particular pep-0440 uses tilde, triple equal and wildcard star operators
  that are specific to how two Python versions are compared.

- The comma separator between constraints is a logical "AND" rather than an
  "OR". The "OR" does not exist in the syntax making some version ranges
  harder to express, in particular for vulnerabilities that may affect several
  exact versions or version ranges such as when there are multiple release
  branches that exist in parallel. For instance a statement such as: Django 1.2
  or later, or Django 2.2 or later or Django 3.2 or later is difficult to
  express without an "OR" logic.


Why not use Rubygems requirements notation?
##############################################################

https://guides.rubygems.org/patterns/#declaring-dependencies

The rubygems specification suggests but does not enforce using semver. It is
similar to this spec's operators with the addition of the "~>" aka. pessimistic
operator or tilde-wakka which is similar to the "tilde" used in node-semver and
implies semver versioning. This makes the notation impractical to reuse
in places that do not use the same semver-like semantics.


References
~~~~~~~~~~~~~~~~~~~~

Here are some of the discussions that led to the creation of this specification:

- https://github.com/package-url/purl-spec/issues/66
- https://github.com/package-url/purl-spec/issues/84
- https://github.com/package-url/purl-spec/pull/93
- https://github.com/nexB/vulnerablecode/issues/119
- https://github.com/nexB/vulnerablecode/issues/140