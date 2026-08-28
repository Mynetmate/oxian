"""Oxian - Network Device and Topology Discovery Core in Python."""

from __future__ import annotations

from ipaddress import IPv4Address, IPv6Address, ip_address
from typing import Any

from . import discovery, models, snmp, vendor
from .discovery import resolve_topology, scan, scan_one_device
from .models import (
    DefaultRoute,
    Device,
    DiscoveryResult,
    Interface,
    InterfaceStatus,
    Link,
    Neighbor,
    UnresolvedNeighbor,
    Vendor,
)
from .vendor import detect_vender, detect_vendor


async def discover(
    target: str | IPv4Address | IPv6Address,
    port: int = 161,
    community: str = "public",
    timeout: int = 2,
) -> dict[str, Any]:
    """Scan and discover network devices starting from the target seed IP address.

    Args:
        target: Seed device IP address (string or IPv4Address/IPv6Address).
        port: SNMP UDP port (default: 161).
        community: SNMP v2c community string (default: "public").
        timeout: SNMP timeout in seconds (default: 2).

    Returns:
        JSON-serializable dictionary with keys: devices, links, and unresolved_neighbors.
    """
    ip = ip_address(str(target))
    result = await scan(ip, port=port, community=community, timeout=timeout)
    return result.to_dict()


__version__ = "0.1.0"

__all__ = [
    "discovery",
    "models",
    "snmp",
    "vendor",
    "scan",
    "discover",
    "scan_one_device",
    "resolve_topology",
    "DefaultRoute",
    "Device",
    "DiscoveryResult",
    "Interface",
    "InterfaceStatus",
    "Link",
    "Neighbor",
    "UnresolvedNeighbor",
    "Vendor",
    "detect_vendor",
    "detect_vender",
]
