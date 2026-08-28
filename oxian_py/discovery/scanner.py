from __future__ import annotations

from ipaddress import IPv4Address, IPv6Address

from ..models.device import Device
from ..models.neighbor import Neighbor
from ..models.route import DefaultRoute
from ..snmp import (
    SnmpClient,
    connect,
    discover_neighbors,
    get_default_route,
    get_device_info,
    get_device_interface,
    get_device_ip_addresses,
    get_local_chassis_id,
)
from ..vendor import detect_vendor


async def scan_one_device(
    ip: str | IPv4Address | IPv6Address,
    port: int = 161,
    community: str = "public",
    timeout: int = 2,
) -> tuple[Device, list[Neighbor], DefaultRoute | None]:
    """Scan a single network device via SNMP.

    Queries system info, interfaces, chassis ID, LLDP neighbors, and default route.

    Args:
        ip: Target device IP address.
        port: SNMP UDP port (default: 161).
        community: SNMP v2c community string (default: "public").
        timeout: Timeout in seconds (default: 2).

    Returns:
        Tuple containing (Device, list of Neighbor, DefaultRoute or None).

    Raises:
        TimeoutError: If the target device does not respond to SNMP queries.
    """
    client: SnmpClient = await connect(ip, port=port, community=community, timeout=timeout)
    try:
        sys_info = await get_device_info(client)
        # If the device didn't respond to basic system info, consider it unreachable
        if (
            sys_info.hostname is None
            and sys_info.description is None
            and sys_info.object_id is None
        ):
            raise TimeoutError(f"No SNMP response from {ip}")

        interfaces = await get_device_interface(client)
        all_ips = await get_device_ip_addresses(client)
        if str(ip) not in all_ips:
            all_ips.insert(0, str(ip))
        chassis_id = await get_local_chassis_id(client)
        neighbors = await discover_neighbors(client)
        default_route = await get_default_route(client)

        vendor = detect_vendor(sys_info.object_id)

        device = Device(
            ip=ip,
            hostname=sys_info.hostname,
            description=sys_info.description,
            vendor=vendor,
            interfaces=interfaces,
            all_ips=all_ips,
            chassis_id=chassis_id,
            is_managed=True,
        )

        return device, neighbors, default_route

    finally:
        client.close()
