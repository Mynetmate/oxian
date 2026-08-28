import unittest
from ipaddress import IPv4Address

from oxian_py.discovery.topology import resolve_topology
from oxian_py.models import (
    Device,
    Interface,
    InterfaceStatus,
    Neighbor,
    Vendor,
)


def create_test_interface(index: int, desc: str) -> Interface:
    return Interface(
        index=index,
        description=desc,
        mac_address=None,
        admin_status=InterfaceStatus.Up,
        oper_status=InterfaceStatus.Up,
    )


class TestTopology(unittest.TestCase):
    def test_resolve_topology_with_managed_devices(self):
        ip_a = IPv4Address("192.168.1.1")
        ip_b = IPv4Address("192.168.1.2")

        device_a = Device(
            ip=ip_a,
            hostname="Switch-A",
            description="Cisco 2960",
            vendor=Vendor.Cisco,
            interfaces=[create_test_interface(1, "GigabitEthernet0/1")],
            chassis_id="0011223344aa",
            is_managed=True,
        )

        device_b = Device(
            ip=ip_b,
            hostname="Switch-B",
            description="Cisco 2960",
            vendor=Vendor.Cisco,
            interfaces=[create_test_interface(2, "GigabitEthernet0/2")],
            chassis_id="0011223344bb",
            is_managed=True,
        )

        neighbor_records = [
            (
                ip_a,
                Neighbor(
                    chassis_id="0011223344bb",
                    remote_port_id="Gi0/2",
                    remote_port_description="GigabitEthernet0/2",
                    hostname="Switch-B",
                    remote_ip=ip_b,
                    local_interface=1,
                ),
            ),
            (
                ip_b,
                Neighbor(
                    chassis_id="0011223344aa",
                    remote_port_id="Gi0/1",
                    remote_port_description="GigabitEthernet0/1",
                    hostname="Switch-A",
                    remote_ip=ip_a,
                    local_interface=2,
                ),
            ),
        ]

        result = resolve_topology([device_a, device_b], neighbor_records, [])

        self.assertEqual(len(result.devices), 2)
        self.assertTrue(all(d.is_managed for d in result.devices))
        self.assertEqual(len(result.links), 1)
        self.assertEqual(str(result.links[0].source_ip), str(ip_a))
        self.assertEqual(str(result.links[0].target_ip), str(ip_b))
        self.assertEqual(len(result.unresolved_neighbors), 0)

    def test_resolve_topology_with_unresolved_neighbor(self):
        ip_a = IPv4Address("192.168.1.1")
        ip_unresolved = IPv4Address("192.168.1.50")

        device_a = Device(
            ip=ip_a,
            hostname="Switch-A",
            description="Managed Switch",
            vendor=Vendor.Cisco,
            interfaces=[create_test_interface(5, "GigabitEthernet0/5")],
            chassis_id="0011223344aa",
            is_managed=True,
        )

        neighbor_records = [
            (
                ip_a,
                Neighbor(
                    chassis_id="aabbccddeeff",
                    remote_port_id="eth0",
                    remote_port_description="AP Port",
                    hostname="Unresolved-AP",
                    remote_ip=ip_unresolved,
                    local_interface=5,
                ),
            )
        ]

        result = resolve_topology([device_a], neighbor_records, [])

        self.assertEqual(len(result.devices), 2)

        managed = next(d for d in result.devices if d.is_managed)
        self.assertEqual(managed.hostname, "Switch-A")

        unresolved = next(d for d in result.devices if not d.is_managed)
        self.assertEqual(unresolved.hostname, "Unresolved-AP")
        self.assertEqual(unresolved.chassis_id, "aabbccddeeff")
        self.assertEqual(str(unresolved.ip), str(ip_unresolved))
        self.assertFalse(unresolved.is_managed)

        self.assertEqual(len(result.links), 1)
        self.assertEqual(str(result.links[0].source_ip), str(ip_a))
        self.assertEqual(result.links[0].source_interface, "GigabitEthernet0/5")
        self.assertEqual(str(result.links[0].target_ip), str(ip_unresolved))
        self.assertEqual(result.links[0].target_chassis_id, "aabbccddeeff")
        self.assertEqual(result.links[0].target_port_id, "eth0")
        self.assertEqual(len(result.unresolved_neighbors), 0)

    def test_resolve_topology_unresolved_node_deduplication(self):
        ip_a = IPv4Address("192.168.1.1")
        ip_b = IPv4Address("192.168.1.2")

        device_a = Device(
            ip=ip_a,
            hostname="Switch-A",
            description=None,
            vendor=Vendor.Cisco,
            interfaces=[create_test_interface(1, "Gi0/1")],
            chassis_id="0011223344aa",
            is_managed=True,
        )

        device_b = Device(
            ip=ip_b,
            hostname="Switch-B",
            description=None,
            vendor=Vendor.Cisco,
            interfaces=[create_test_interface(1, "Gi0/1")],
            chassis_id="0011223344bb",
            is_managed=True,
        )

        neighbor_records = [
            (
                ip_a,
                Neighbor(
                    chassis_id="deadbeef0001",
                    remote_port_id="port1",
                    remote_port_description=None,
                    hostname="Unresolved-Switch",
                    remote_ip=None,
                    local_interface=1,
                ),
            ),
            (
                ip_b,
                Neighbor(
                    chassis_id="deadbeef0001",
                    remote_port_id="port2",
                    remote_port_description=None,
                    hostname="Unresolved-Switch",
                    remote_ip=None,
                    local_interface=1,
                ),
            ),
        ]

        result = resolve_topology([device_a, device_b], neighbor_records, [])

        # 2 managed + 1 deduplicated unresolved switch = 3 devices
        self.assertEqual(len(result.devices), 3)
        unresolved_count = sum(1 for d in result.devices if not d.is_managed)
        self.assertEqual(unresolved_count, 1)

        # 2 separate links: A -> Unresolved-Switch and B -> Unresolved-Switch
        self.assertEqual(len(result.links), 2)

    def test_resolve_topology_anonymous_unresolved_neighbor(self):
        ip_a = IPv4Address("192.168.1.1")

        device_a = Device(
            ip=ip_a,
            hostname="Switch-A",
            description=None,
            vendor=Vendor.Cisco,
            interfaces=[create_test_interface(1, "Gi0/1")],
            chassis_id="0011223344aa",
            is_managed=True,
        )

        neighbor_records = [
            (
                ip_a,
                Neighbor(
                    chassis_id="",
                    remote_port_id="",
                    remote_port_description=None,
                    hostname=None,
                    remote_ip=None,
                    local_interface=1,
                ),
            )
        ]

        result = resolve_topology([device_a], neighbor_records, [])

        # Only 1 device (cannot infer node with zero identifiers)
        self.assertEqual(len(result.devices), 1)
        self.assertEqual(len(result.links), 0)
        self.assertEqual(len(result.unresolved_neighbors), 1)


if __name__ == "__main__":
    unittest.main()
