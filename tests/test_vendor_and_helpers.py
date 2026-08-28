import unittest
from oxian_py.models import InterfaceStatus, Vendor, DiscoveryResult, Device, Link, Neighbor, UnresolvedNeighbor
from oxian_py.vendor import detect_vendor, detect_vender
from oxian_py.snmp.interface import parse_mac, value_to_u32
from oxian_py.snmp.neighbors import normalize_chassis_id, parse_remote_ip


class TestVendorAndHelpers(unittest.TestCase):
    def test_detect_vendor(self):
        self.assertEqual(detect_vendor("1.3.6.1.4.1.9.1.2665"), Vendor.Cisco)
        self.assertEqual(detect_vendor("1.3.6.1.4.1.14988.1"), Vendor.MikroTik)
        self.assertEqual(detect_vendor("1.3.6.1.4.1.2636.1.1.1.2.108"), Vendor.Juniper)
        self.assertEqual(detect_vendor("1.3.6.1.4.1.99999"), Vendor.Unknown)
        self.assertEqual(detect_vendor(None), Vendor.Unknown)
        self.assertEqual(detect_vender("1.3.6.1.4.1.9.1"), Vendor.Cisco)

    def test_parse_mac(self):
        self.assertEqual(parse_mac("0x001a2b3c4d01"), "00:1A:2B:3C:4D:01")
        self.assertEqual(parse_mac("001a2b3c4d01"), "00:1A:2B:3C:4D:01")
        self.assertEqual(parse_mac(b"\x00\x1a\x2b\x3c\x4d\x01"), "00:1A:2B:3C:4D:01")
        self.assertIsNone(parse_mac("0x000000000000"))
        self.assertIsNone(parse_mac("invalid"))
        self.assertIsNone(parse_mac(None))

    def test_normalize_chassis_id(self):
        self.assertEqual(normalize_chassis_id("00:11:22:33:44:AA"), "0011223344aa")
        self.assertEqual(normalize_chassis_id("00-11-22-33-44-BB"), "0011223344bb")
        self.assertEqual(normalize_chassis_id("0011.2233.44CC"), "0011223344cc")
        self.assertEqual(normalize_chassis_id("0x0011223344dd"), "0011223344dd")
        self.assertEqual(normalize_chassis_id(None), "")

    def test_parse_remote_ip(self):
        self.assertEqual(parse_remote_ip("192.168.1.1"), "192.168.1.1")
        self.assertEqual(parse_remote_ip(b"\xc0\xa8\x01\x01"), "192.168.1.1")
        self.assertEqual(parse_remote_ip("0xc0a80101"), "192.168.1.1")
        self.assertIsNone(parse_remote_ip(None))

    def test_interface_status(self):
        self.assertEqual(InterfaceStatus.from_u32(1), InterfaceStatus.Up)
        self.assertEqual(InterfaceStatus.from_u32(2), InterfaceStatus.Down)
        self.assertEqual(InterfaceStatus.from_u32(3), InterfaceStatus.Testing)
        self.assertEqual(InterfaceStatus.from_u32(99), "Unknown(99)")

    def test_discovery_result_to_dict(self):
        res = DiscoveryResult(
            devices=[
                Device(
                    ip="192.168.1.1",
                    hostname="Router",
                    description="Cisco",
                    vendor=Vendor.Cisco,
                    interfaces=[],
                    chassis_id="001122334455",
                    is_managed=True,
                )
            ],
            links=[],
            unresolved_neighbors=[],
        )
        d = res.to_dict()
        self.assertIn("devices", d)
        self.assertIn("links", d)
        self.assertIn("unresolved_neighbors", d)
        self.assertEqual(d["devices"][0]["hostname"], "Router")
        self.assertEqual(d["devices"][0]["vendor"], "Cisco")


if __name__ == "__main__":
    unittest.main()
