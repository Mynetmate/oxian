from __future__ import annotations

import collections
from ipaddress import IPv4Address, IPv4Network, IPv6Address, ip_address
import sys
from typing import Optional, Union

try:
    from ..models.discovery import DiscoveryResult
    from ..models.neighbor import Neighbor
    from ..models.route import DefaultRoute
except (ImportError, ValueError):
    from models.discovery import DiscoveryResult
    from models.neighbor import Neighbor
    from models.route import DefaultRoute

from . import scanner, topology


async def scan(
    ip: Union[str, IPv4Address, IPv6Address],
    cidr: Optional[int] = None,
    port: int = 161,
    community: str = "public",
    timeout: int = 2,
) -> DiscoveryResult:
    if cidr is not None:
        return await scan_network(ip, cidr, port=port, community=community, timeout=timeout)
    else:
        return await scan_device(ip, port=port, community=community, timeout=timeout)


async def scan_device(
    ip: Union[str, IPv4Address, IPv6Address],
    port: int = 161,
    community: str = "public",
    timeout: int = 2,
) -> DiscoveryResult:
    ip_obj = ip_address(str(ip))
    queue: collections.deque[Union[IPv4Address, IPv6Address]] = collections.deque([ip_obj])
    visited: set[str] = set()
    devices = []

    neighbor_records: list[tuple[Union[str, IPv4Address, IPv6Address], Neighbor]] = []
    default_route_records: list[tuple[Union[str, IPv4Address, IPv6Address], DefaultRoute]] = []

    while queue:
        current_ip = queue.popleft()
        if str(current_ip) in visited:
            continue

        try:
            device, neighbors, default_route = await scanner.scan_one_device(
                current_ip, port=port, community=community, timeout=timeout
            )
        except Exception as e:
            print(f"Failed to scan {current_ip}: {e}", file=sys.stderr)
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
    ip: Union[str, IPv4Address, IPv6Address],
    cidr: int,
    port: int = 161,
    community: str = "public",
    timeout: int = 2,
) -> DiscoveryResult:
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
        except Exception:
            continue

    return topology.resolve_topology(devices, [], [])
