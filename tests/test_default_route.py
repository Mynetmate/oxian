import unittest
from ipaddress import IPv4Address

from oxian_py.discovery.topology import resolve_topology
from oxian_py.models import (
    DefaultRoute,
    Device,
    Interface,
    InterfaceStatus,
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


class TestDefaultRoute(unittest.TestCase):
    def test_resolve_topology_with_default_gateway(self):
        ip_router = IPv4Address("192.168.1.1")
        ip_gateway = IPv4Address("203.0.113.1")

        router = Device(
            ip=ip_router,
            hostname="Edge-Router",
            description="Cisco ISR 4331",
            vendor=Vendor.Cisco,
            interfaces=[
                create_test_interface(1, "GigabitEthernet0/0/0 (WAN)"),
                create_test_interface(2, "GigabitEthernet0/0/1 (LAN)"),
            ],
            chassis_id="0011223344aa",
            is_managed=True,
        )

        default_routes = [
            (
                ip_router,
                DefaultRoute(
                    next_hop=ip_gateway,
                    local_interface=1,
                ),
            )
        ]

        result = resolve_topology([router], [], default_routes)

        self.assertEqual(len(result.devices), 2)

        managed = next(d for d in result.devices if d.is_managed)
        self.assertEqual(managed.hostname, "Edge-Router")

        gateway = next(d for d in result.devices if not d.is_managed)
        self.assertEqual(gateway.hostname, "Default Gateway")
        self.assertEqual(str(gateway.ip), str(ip_gateway))
        self.assertFalse(gateway.is_managed)

        self.assertEqual(len(result.links), 1)
        self.assertEqual(str(result.links[0].source_ip), str(ip_router))
        self.assertEqual(result.links[0].source_interface, "GigabitEthernet0/0/0 (WAN)")
        self.assertEqual(str(result.links[0].target_ip), str(ip_gateway))
        self.assertEqual(result.links[0].target_port_id, "default-route")

    def test_resolve_topology_default_gateway_already_known(self):
        ip_router_a = IPv4Address("192.168.1.1")
        ip_core_switch = IPv4Address("192.168.1.254")

        router_a = Device(
            ip=ip_router_a,
            hostname="Branch-Router",
            description=None,
            vendor=Vendor.Cisco,
            interfaces=[create_test_interface(1, "Gi0/0")],
            chassis_id="0011223344aa",
            is_managed=True,
        )

        core_switch = Device(
            ip=ip_core_switch,
            hostname="Core-Switch",
            description=None,
            vendor=Vendor.Cisco,
            interfaces=[create_test_interface(24, "Gi1/0/24")],
            chassis_id="0011223344bb",
            is_managed=True,
        )

        # Default route points to Core-Switch which is already a known managed device
        default_routes = [
            (
                ip_router_a,
                DefaultRoute(
                    next_hop=ip_core_switch,
                    local_interface=1,
                ),
            )
        ]

        result = resolve_topology([router_a, core_switch], [], default_routes)

        # Should NOT create duplicate node, exactly 2 devices
        self.assertEqual(len(result.devices), 2)
        self.assertTrue(all(d.is_managed for d in result.devices))

        # Link connects Router A to Core-Switch
        self.assertEqual(len(result.links), 1)
        self.assertEqual(str(result.links[0].source_ip), str(ip_router_a))
        self.assertEqual(str(result.links[0].target_ip), str(ip_core_switch))

    def test_resolve_topology_default_gateway_deduplication(self):
        ip_router_a = IPv4Address("192.168.1.1")
        ip_router_b = IPv4Address("192.168.1.2")
        ip_shared_gateway = IPv4Address("203.0.113.1")

        router_a = Device(
            ip=ip_router_a,
            hostname="Router-A",
            description=None,
            vendor=Vendor.Cisco,
            interfaces=[create_test_interface(1, "WAN1")],
            chassis_id="0011223344aa",
            is_managed=True,
        )

        router_b = Device(
            ip=ip_router_b,
            hostname="Router-B",
            description=None,
            vendor=Vendor.Cisco,
            interfaces=[create_test_interface(1, "WAN1")],
            chassis_id="0011223344bb",
            is_managed=True,
        )

        default_routes = [
            (
                ip_router_a,
                DefaultRoute(
                    next_hop=ip_shared_gateway,
                    local_interface=1,
                ),
            ),
            (
                ip_router_b,
                DefaultRoute(
                    next_hop=ip_shared_gateway,
                    local_interface=1,
                ),
            ),
        ]

        result = resolve_topology([router_a, router_b], [], default_routes)

        self.assertEqual(len(result.devices), 3)
        unmanaged_count = sum(1 for d in result.devices if not d.is_managed)
        self.assertEqual(unmanaged_count, 1)

        self.assertEqual(len(result.links), 2)

    def test_resolve_topology_with_interface_only_default_gateway(self):
        ip_router = IPv4Address("192.168.1.1")
        router = Device(
            ip=ip_router,
            hostname="Mikrotik-Edge",
            description="RouterOS",
            vendor=Vendor.MikroTik,
            interfaces=[create_test_interface(2, "ether2")],
            chassis_id="0011223344cc",
            is_managed=True,
        )

        # Direct-attached / Interface-only route (gateway=ether2)
        default_routes = [
            (
                ip_router,
                DefaultRoute(
                    next_hop=None,
                    local_interface=2,
                ),
            )
        ]

        result = resolve_topology([router], [], default_routes, duration_ms=42)

        self.assertEqual(len(result.devices), 2)
        gateway = next(d for d in result.devices if not d.is_managed)
        self.assertEqual(gateway.hostname, "WAN Gateway (ether2)")
        self.assertIsNone(gateway.ip)
        self.assertEqual(len(result.links), 1)
        self.assertEqual(result.links[0].protocol, "default_route")
        self.assertEqual(result.links[0].source_interface, "ether2")
        self.assertEqual(result.duration_ms, 42)


if __name__ == "__main__":
    unittest.main()
