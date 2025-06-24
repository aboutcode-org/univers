Changelog
=========

Version v31.0.0
----------------

- Raise instead of returning ``NotImplementedError`` in ``version_range.VersionRange`` methods. https://github.com/aboutcode-org/univers/pull/158

Version v30.12.1
----------------

- Update link references of ownership from nexB to aboutcode-org. https://github.com/aboutcode-org/univers/issues/140


Version v30.12.0
----------------

- Support VersionRange normalization using known versions. https://github.com/nexB/univers/pull/108
- Fix the edge case resulting in incorrect ``contains`` resolution in VersionRange. https://github.com/nexB/univers/issues/137 https://github.com/nexB/univers/pull/108
- Use native impl to parse Maven and NuGet range expression in ``from_gitlab_native``. https://github.com/nexB/univers/issues/136 https://github.com/nexB/univers/pull/108
- Fix incorrect parsing of composer range in  ``from_gitlab_native``. https://github.com/nexB/univers/issues/136 https://github.com/nexB/univers/pull/108


Version v30.11.0
----------------

- Use proper exception subclass for invalid constraints error.


Version v30.10.1
----------------

- Add Nix flake as a build system.
- Refactor gem and make nuget hashable.
- Update skeleton.
- Handle NoneType in VersionRange.from_string.
- Handle npm prerelease caret range expression.


Version v30.10.0
----------------

- Add support for conan version and version range.
- Fix version comparison for all the versions.


Version v30.9.2
----------------

- Fix unhashable error in GemVersion.


Version v30.9.1
----------------

- Add invert function to VersionRange.


Version v30.9.0
----------------

- Change type of archlinux version ranges to alpm.


Version v30.8.0
----------------

- Fix npm version ranges


Version v30.7.0
----------------

- Add composer and golang versions and also support gitlab native ranges for them


Version v30.6.0
----------------

- Add support for gitlab in pypi, npm, gem version ranges
- Subclass semver for nginx


Version v30.5.1
----------------

- Fix Nuget string representation
- Test sorting of all the OpenSSL versions ever released


Version v30.5.0
----------------

- Add version range support for maven
- Remove unsupported characters in Pypi from_native implementation
- Add Nuget Version support in Univers


Version v30.4.0
----------------

- Add support for forming VersionRange from a list of versions.Thank you
  to Keshav Priyadarshi @keshav-space for this.


Version v30.3.1
----------------

- Change equal comparator for github native ranges


Version v30.3.0
----------------

- New support for native GitHub version ranges. GitHub native version range is different from
  other native ranges. For example:
  Maven native version range looks like:
  `[1.0.0,1.0.1)`
  Github native version range looks like:
  `>= 1.0.0, < 1.0.1`


Version v30.2.0
----------------

- New support for OpenSSL version(s). These are peculiar because there are two
  epochs in the versioning: the versioning scheme is custom before version 3
  and is based on semver from version 3 onwards. Thank you to Keshav Priyadarshi
  @keshav-space for this.


Version v30.1.0
-----------------

- New support for Alpine package versions. These are based loosely on Gentoo
  versions with some variations. We do not support all the version styles yet.
  The unit tests are based on the upstream apk-tools tests and this brings in
  700 new unit tests.
- Fix handling of caret and tilde version in npm version ranges.
- Enable automated build of wheels on release
- Adopt latest skeleton, droping support for tests on macOS 10.14


Version v30.0.0
-----------------

- Implement the new "vers" spec. This is a major incomplatible change.
- Add support for nginx version scheme
- Switching back to semver
- Improve origin and license documentation
- Add tests for carets in RPMs
- Format, streamline and refactor code
- Improve testing


Version v21.4.9
-----------------

- Add support Gentoo style versions.


Version v21.4.8
-----------------

- Add support for more package types.
- Version classes are now hashable and frozen


Version v21.4.6
-----------------

- Initial Release
