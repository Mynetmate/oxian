from __future__ import annotations

from typing import Any, Optional

try:
    from ..models.interface import Interface, InterfaceStatus
except (ImportError, ValueError):
    from models.interface import Interface, InterfaceStatus

from . import oid
from .client import SnmpClient


def parse_mac(value: Any) -> Optional[str]:
    if value is None:
        return None

    # If bytes:
    if isinstance(value, (bytes, bytearray)):
        if len(value) == 6:
            if all(b == 0 for b in value):
                return None
            return ":".join(f"{b:02X}" for b in value)
        return None

    # If OctetString / pyasn1
    try:
        raw_bytes = bytes(value)
        if len(raw_bytes) == 6:
            if all(b == 0 for b in raw_bytes):
                return None
            return ":".join(f"{b:02X}" for b in raw_bytes)
    except Exception:
        pass

    raw = str(value).strip()
    if raw.startswith("0x") or raw.startswith("0X"):
        hex_str = raw[2:]
    else:
        hex_str = raw

    clean_hex = hex_str.replace(":", "").replace("-", "").replace(".", "")
    if len(clean_hex) != 12:
        return None

    if all(c == "0" for c in clean_hex):
        return None

    try:
        int(clean_hex, 16)
    except ValueError:
        return None

    return ":".join(clean_hex[i : i + 2].upper() for i in range(0, 12, 2))


def value_to_u32(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        val = int(value)
        if val >= 0:
            return val
        return None
    except (ValueError, TypeError):
        return None


async def get_device_interface(client: SnmpClient) -> list[Interface]:
    descriptions = await client.walk_column(oid.if_descr())
    macs = await client.walk_column(oid.if_phys_address())
    admin_status = await client.walk_column(oid.if_admin_status())
    oper_status = await client.walk_column(oid.if_oper_status())

    interfaces: list[Interface] = []

    for index, description in descriptions.items():
        mac_raw = macs.get(index)
        admin_raw = admin_status.get(index)
        oper_raw = oper_status.get(index)

        admin_val = None
        if admin_raw is not None:
            u32_val = value_to_u32(admin_raw)
            if u32_val is not None:
                admin_val = InterfaceStatus.from_u32(u32_val)

        oper_val = None
        if oper_raw is not None:
            u32_val = value_to_u32(oper_raw)
            if u32_val is not None:
                oper_val = InterfaceStatus.from_u32(u32_val)

        interface = Interface(
            index=index,
            description=str(description) if description is not None else None,
            mac_address=parse_mac(mac_raw),
            admin_status=admin_val,
            oper_status=oper_val,
        )
        interfaces.append(interface)

    interfaces.sort(key=lambda inf: inf.index)
    return interfaces
