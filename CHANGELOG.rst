Changelog
=========


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
