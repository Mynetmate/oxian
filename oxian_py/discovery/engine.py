from __future__ import annotations

import collections
from ipaddress import IPv4Address, IPv4Network, IPv6Address, ip_address
import logging

from ..models.discovery import DiscoveryResult
from ..models.neighbor import Neighbor
from ..models.route import DefaultRoute
from . import scanner, topology

logger = logging.getLogger("oxian.discovery")


async def scan(
    ip: str | IPv4Address | IPv6Address,
    cidr: int | None = None,
    port: int = 161,
    community: str = "public",
    timeout: int = 2,
) -> DiscoveryResult:
    """Scan and discover network devices and topology.

    Args:
        ip: Seed device IP or network address.
        cidr: Optional CIDR subnet mask length for subnet scans (e.g. 24).
        port: SNMP UDP port.
        community: SNMP community string.
        timeout: SNMP timeout in seconds.

    Returns:
        DiscoveryResult containing devices, links, and unresolved neighbors.
    """
    if cidr is not None:
        return await scan_network(ip, cidr, port=port, community=community, timeout=timeout)
    else:
        return await scan_device(ip, port=port, community=community, timeout=timeout)


async def scan_device(
    ip: str | IPv4Address | IPv6Address,
    port: int = 161,
    community: str = "public",
    timeout: int = 2,
) -> DiscoveryResult:
    """Traverse network topology iteratively starting from a seed device IP.

    Args:
        ip: Seed device IP address.
        port: SNMP UDP port.
        community: SNMP community string.
        timeout: SNMP timeout in seconds.

    Returns:
        DiscoveryResult representing the discovered network topology.

    Raises:
        TimeoutError: If the seed target device cannot be reached via SNMP.
    """
    ip_obj = ip_address(str(ip))
    queue: collections.deque[IPv4Address | IPv6Address] = collections.deque([ip_obj])
    visited: set[str] = set()
    devices = []

    neighbor_records: list[tuple[str | IPv4Address | IPv6Address, Neighbor]] = []
    default_route_records: list[tuple[str | IPv4Address | IPv6Address, DefaultRoute]] = []

    while queue:
        current_ip = queue.popleft()
        if str(current_ip) in visited:
            continue

        try:
            device, neighbors, default_route = await scanner.scan_one_device(
                current_ip, port=port, community=community, timeout=timeout
            )
        except Exception as e:
            logger.warning("Failed to scan %s: %s", current_ip, e)
            visited.add(str(current_ip))
            if current_ip == ip_obj and not devices:
                raise
            continue

        for neighbor in neighbors:
            neighbor_records.append((current_ip, neighbor))

        if default_route is not None:
            default_route_records.append((current_ip, default_route))

        for neighbor in neighbors:
            if neighbor.remote_ip is not None:
                try:
                    remote_ip_obj = ip_address(str(neighbor.remote_ip))
                    if str(remote_ip_obj) not in visited:
                        queue.append(remote_ip_obj)
                except ValueError:
                    pass

        visited.add(str(current_ip))
        devices.append(device)

    return topology.resolve_topology(devices, neighbor_records, default_route_records)


async def scan_network(
    ip: str | IPv4Address | IPv6Address,
    cidr: int,
    port: int = 161,
    community: str = "public",
    timeout: int = 2,
) -> DiscoveryResult:
    """Scan all reachable IP addresses within a CIDR subnet.

    Args:
        ip: Subnet network address.
        cidr: Subnet mask bit length.
        port: SNMP UDP port.
        community: SNMP community string.
        timeout: SNMP timeout in seconds.

    Returns:
        DiscoveryResult containing all responsive devices.
    """
    ip_obj = ip_address(str(ip))
    if isinstance(ip_obj, IPv4Address):
        net = IPv4Network(f"{ip_obj}/{cidr}", strict=False)
    else:
        raise ValueError("IPv6 is not supported yet")

    devices = []
    for host in net.hosts():
        try:
            device, _, _ = await scanner.scan_one_device(
                host, port=port, community=community, timeout=timeout
            )
            devices.append(device)
        except Exception as exc:
            logger.debug("Host %s not responding: %s", host, exc)
            continue

    return topology.resolve_topology(devices, [], [])
