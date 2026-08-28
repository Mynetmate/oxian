from __future__ import annotations

import ipaddress
from typing import Any, Optional

try:
    from ..models.neighbor import Neighbor
except (ImportError, ValueError):
    from models.neighbor import Neighbor

from . import oid
from .client import SnmpClient


def normalize_chassis_id(value: Any) -> str:
    if value is None:
        return ""

    if isinstance(value, (bytes, bytearray)):
        return value.hex().lower()

    try:
        raw_bytes = bytes(value)
        # If binary MAC (6 bytes, non-ascii)
        if len(raw_bytes) == 6 and not all(32 <= b <= 126 for b in raw_bytes):
            return raw_bytes.hex().lower()
    except Exception:
        pass

    s = str(value).strip()
    if s.startswith("0x") or s.startswith("0X"):
        s = s[2:]

    for ch in (":", ".", "-"):
        s = s.replace(ch, "")

    return s.lower()


def parse_remote_ip(value: Any) -> Optional[str]:
    if value is None:
        return None

    val_str = str(value).strip()
    try:
        return str(ipaddress.ip_address(val_str))
    except ValueError:
        pass

    if isinstance(value, (bytes, bytearray)) and len(value) == 4:
        return f"{value[0]}.{value[1]}.{value[2]}.{value[3]}"

    clean = val_str.lower().removeprefix("0x")
    if len(clean) == 8:
        try:
            b = bytes.fromhex(clean)
            return f"{b[0]}.{b[1]}.{b[2]}.{b[3]}"
        except ValueError:
            pass

    return None


async def get_local_chassis_id(client: SnmpClient) -> Optional[str]:
    try:
        val = await client.get(oid.lldp_loc_chassis_id())
        if val is not None:
            norm = normalize_chassis_id(val)
            return norm if norm else None
    except Exception:
        pass
    return None


async def discover_neighbors(client: SnmpClient) -> list[Neighbor]:
    hostnames = await client.walk_lldp_column(oid.lldp_rem_sys_name())
    ports = await client.walk_lldp_column(oid.lldp_rem_port_id())
    port_descriptions = await client.walk_lldp_column(oid.lldp_rem_port_description())
    addresses = await client.walk_lldp_column(oid.lldp_rem_man_addr())
    chassis_ids = await client.walk_lldp_column(oid.lldp_rem_chassis_id())

    neighbors: list[Neighbor] = []

    for index, chassis_id in chassis_ids.items():
        hostname = hostnames.get(index)
        port = ports.get(index)
        port_description = port_descriptions.get(index)
        address = addresses.get(index)

        remote_ip = parse_remote_ip(address)

        neighbors.append(
            Neighbor(
                chassis_id=normalize_chassis_id(chassis_id),
                remote_port_id=str(port) if port is not None else "",
                remote_port_description=str(port_description) if port_description is not None else None,
                hostname=str(hostname) if hostname is not None else None,
                remote_ip=remote_ip,
                local_interface=index[1],
            )
        )

    return neighbors
