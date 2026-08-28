from __future__ import annotations

import ipaddress
from typing import Any

from ..models.neighbor import Neighbor
from . import oid
from .client import SnmpClient


def normalize_chassis_id(value: Any) -> str:
    """Normalize chassis ID string / binary into a clean lowercase hex string."""
    if value is None:
        return ""

    try:
        raw_bytes = bytes(value)
        # If binary MAC or chassis ID
        if len(raw_bytes) in (6, 8) and not all(32 <= b <= 126 for b in raw_bytes):
            return raw_bytes.hex().lower()
    except Exception:
        pass

    if isinstance(value, (bytes, bytearray)):
        return value.hex().lower()

    s = str(value).strip()
    if s.startswith(("0x", "0X")):
        s = s[2:]

    for ch in (":", ".", "-"):
        s = s.replace(ch, "")

    return s.lower()


def parse_port_id(value: Any) -> str:
    """Parse port ID from SNMP octets into printable ASCII string or MAC address."""
    if value is None:
        return ""

    try:
        raw_b = bytes(value)
        if len(raw_b) == 6 and not all(32 <= b <= 126 for b in raw_b):
            return ":".join(f"{b:02X}" for b in raw_b)
    except Exception:
        pass

    s = str(value).strip()
    if all(32 <= ord(c) <= 126 for c in s):
        return s

    try:
        raw_b = bytes(value)
        if len(raw_b) == 6:
            return ":".join(f"{b:02X}" for b in raw_b)
        return raw_b.hex().lower()
    except Exception:
        return s


def parse_remote_ip(value: Any) -> str | None:

    """Parse remote management IP from LLDP/CDP management address octets."""
    if value is None:
        return None

    # Handle binary bytes or PySNMP OctetString
    try:
        raw_b = bytes(value)
        if len(raw_b) == 4:
            return f"{raw_b[0]}.{raw_b[1]}.{raw_b[2]}.{raw_b[3]}"
        if len(raw_b) == 16:
            return str(ipaddress.IPv6Address(raw_b))
    except Exception:
        pass

    val_str = str(value).strip()
    try:
        return str(ipaddress.ip_address(val_str))
    except ValueError:
        pass

    clean = val_str.lower().removeprefix("0x")
    if len(clean) == 8:
        try:
            b = bytes.fromhex(clean)
            return f"{b[0]}.{b[1]}.{b[2]}.{b[3]}"
        except ValueError:
            pass

    return None


async def get_local_chassis_id(client: SnmpClient) -> str | None:
    """Query local device chassis ID via LLDP MIB."""
    try:
        val = await client.get(oid.lldp_loc_chassis_id())
        if val is not None:
            norm = normalize_chassis_id(val)
            return norm if norm else None
    except Exception:
        pass
    return None


async def discover_neighbors(client: SnmpClient) -> list[Neighbor]:
    """Discover LLDP and CDP neighbor adjacencies from target device."""
    neighbors: list[Neighbor] = []

    # 1. LLDP Discovery
    hostnames = await client.walk_lldp_column(oid.lldp_rem_sys_name())
    ports = await client.walk_lldp_column(oid.lldp_rem_port_id())
    port_descriptions = await client.walk_lldp_column(oid.lldp_rem_port_description())
    addresses = await client.walk_lldp_man_addr()
    chassis_ids = await client.walk_lldp_column(oid.lldp_rem_chassis_id())

    for index, chassis_id in chassis_ids.items():
        hostname = hostnames.get(index)
        port = ports.get(index)
        port_description = port_descriptions.get(index)
        address = addresses.get(index)

        remote_ip = parse_remote_ip(address) if address else None


        neighbors.append(
            Neighbor(
                chassis_id=normalize_chassis_id(chassis_id),
                remote_port_id=parse_port_id(port),
                remote_port_description=str(port_description) if port_description is not None else None,
                hostname=str(hostname) if hostname is not None else None,
                remote_ip=remote_ip,
                local_interface=index[1],
                protocol="lldp",
            )
        )

    # 2. CDP Discovery (Cisco Discovery Protocol)
    cdp_device_ids = await client.walk_cdp_column(oid.cdp_cache_device_id())
    if cdp_device_ids:
        cdp_ports = await client.walk_cdp_column(oid.cdp_cache_device_port())
        cdp_addresses = await client.walk_cdp_column(oid.cdp_cache_address())
        cdp_platforms = await client.walk_cdp_column(oid.cdp_cache_platform())

        for index, device_id in cdp_device_ids.items():
            if_index, _ = index
            port = cdp_ports.get(index)
            address = cdp_addresses.get(index)
            platform = cdp_platforms.get(index)

            remote_ip = parse_remote_ip(address)
            dev_name = str(device_id).strip() if device_id is not None else None

            # Deduplicate if already discovered by LLDP on same local interface
            already_exists = any(
                n.local_interface == if_index
                and (
                    (dev_name and n.hostname == dev_name)
                    or (remote_ip and n.remote_ip == remote_ip)
                )
                for n in neighbors
            )
            if not already_exists:
                neighbors.append(
                    Neighbor(
                        chassis_id="",
                        remote_port_id=parse_port_id(port),
                        remote_port_description=str(platform) if platform is not None else None,
                        hostname=dev_name,
                        remote_ip=remote_ip,
                        local_interface=if_index,
                        protocol="cdp",
                    )
                )

    return neighbors


