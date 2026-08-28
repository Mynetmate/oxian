import unittest
from unittest.mock import AsyncMock, patch
from ipaddress import IPv4Address

import oxian_py
from oxian_py.discovery.engine import scan, scan_device, scan_network
from oxian_py.discovery.scanner import scan_one_device
from oxian_py.models import (
    DefaultRoute,
    Device,
    Interface,
    InterfaceStatus,
    Neighbor,
    Vendor,
)


class TestEngineAsync(unittest.IsolatedAsyncioTestCase):
    @patch("oxian_py.discovery.scanner.scan_one_device")
    async def test_scan_single_device_with_neighbors(self, mock_scan):
        ip_core = IPv4Address("192.168.1.1")
        ip_branch = IPv4Address("192.168.1.2")

        dev_core = Device(
            ip=ip_core,
            hostname="RT-CORE",
            description="Cisco ISR",
            vendor=Vendor.Cisco,
            interfaces=[
                Interface(
                    index=1,
                    description="Gi0/0/1",
                    admin_status=InterfaceStatus.Up,
                    oper_status=InterfaceStatus.Up,
                )
            ],
            chassis_id="0011223344aa",
            is_managed=True,
        )

        dev_branch = Device(
            ip=ip_branch,
            hostname="RT-BRANCH",
            description="Juniper SRX",
            vendor=Vendor.Juniper,
            interfaces=[
                Interface(
                    index=2,
                    description="ge-0/0/0",
                    admin_status=InterfaceStatus.Up,
                    oper_status=InterfaceStatus.Up,
                )
            ],
            chassis_id="0011223344bb",
            is_managed=True,
        )

        async def side_effect(ip, *args, **kwargs):
            if str(ip) == "192.168.1.1":
                return (
                    dev_core,
                    [
                        Neighbor(
                            chassis_id="0011223344bb",
                            remote_port_id="ge-0/0/0",
                            remote_port_description="Uplink to Branch",
                            hostname="RT-BRANCH",
                            remote_ip=ip_branch,
                            local_interface=1,
                        )
                    ],
                    DefaultRoute(next_hop=IPv4Address("203.0.113.1"), local_interface=1),
                )
            elif str(ip) == "192.168.1.2":
                return (
                    dev_branch,
                    [
                        Neighbor(
                            chassis_id="0011223344aa",
                            remote_port_id="Gi0/0/1",
                            remote_port_description="Uplink to Core",
                            hostname="RT-CORE",
                            remote_ip=ip_core,
                            local_interface=2,
                        )
                    ],
                    None,
                )
            raise ConnectionError(f"Could not connect to {ip}")

        mock_scan.side_effect = side_effect

        result = await scan(ip_core)

        # 2 managed devices + 1 default gateway = 3 devices
        self.assertEqual(len(result.devices), 3)
        self.assertEqual(len(result.links), 2)  # LLDP link + default route link
        self.assertEqual(len(result.unresolved_neighbors), 0)

        # Test discover() helper returning dict
        dict_result = await oxian_py.discover("192.168.1.1")
        self.assertIsInstance(dict_result, dict)
        self.assertEqual(len(dict_result["devices"]), 3)
        self.assertEqual(len(dict_result["links"]), 2)

    @patch("oxian_py.discovery.scanner.scan_one_device")
    async def test_scan_seed_device_failure(self, mock_scan):
        mock_scan.side_effect = TimeoutError("No SNMP response from 192.168.1.1")
        with self.assertRaises(TimeoutError):
            await scan("192.168.1.1")


if __name__ == "__main__":
    unittest.main()
