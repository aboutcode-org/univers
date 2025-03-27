import unittest
from univers.swift_version_range import SwiftVersionRange
from univers.versions import SwiftVersion

class TestSwiftVersionRange(unittest.TestCase):
    def test_exact_version(self):
        vr = SwiftVersionRange('exact: "1.2.3"')
        v = SwiftVersion("1.2.3")
        self.assertTrue(v in vr)

    def test_from_version(self):
        vr = SwiftVersionRange('from: "1.2.3"')
        v1 = SwiftVersion("1.2.3")
        v2 = SwiftVersion("2.0.0")
        self.assertTrue(v1 in vr)
        self.assertFalse(v2 in vr)

    def test_range_with_upper_bound(self):
        vr = SwiftVersionRange('"1.2.3"..<"1.2.6"')
        v1 = SwiftVersion("1.2.3")
        v2 = SwiftVersion("1.2.6")
        self.assertTrue(v1 in vr)
        self.assertFalse(v2 in vr)

    def test_range_with_both_bounds(self):
        vr = SwiftVersionRange('"1.2.3"..."1.2.6"')
        v1 = SwiftVersion("1.2.3")
        v2 = SwiftVersion("1.2.6")
        v3 = SwiftVersion("1.2.7")
        self.assertTrue(v1 in vr)
        self.assertTrue(v2 in vr)
        self.assertFalse(v3 in vr)

if __name__ == '__main__':
    unittest.main()
