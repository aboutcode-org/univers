Pure Python implementation of rpmvercmp

Installation
============
        $ pip install rpm_vercmp

Usage
=====

        import rpm_vercmp
        assert rpm_vercmp.vercmp("1.0", "1.0") == 0
        assert rpm_vercmp.vercmp("1.0", "1.1") == -1

Testing
=======
The testsuite includes rpm's test file in m4 format.
The file cat be fetched from:
https://raw.githubusercontent.com/rpm-software-management/rpm/master/tests/rpmvercmp.at
