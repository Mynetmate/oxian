from __future__ import annotations

from typing import Any

from ..models.interface import Interface, InterfaceStatus
from . import oid
from .client import SnmpClient


def parse_mac(value: Any) -> str | None:
    """Parse MAC address from bytes, hex string, or OctetString."""
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
    if raw.startswith(("0x", "0X")):
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


def value_to_u32(value: Any) -> int | None:
    """Convert SNMP integer/counter value to unsigned 32-bit integer."""
    if value is None:
        return None
    try:
        val = int(value)
        if val >= 0:
            return val
        return None
    except (ValueError, TypeError):
        return None


def parse_ip_str(value: Any) -> str | None:
    """Parse IPv4 address / mask string from bytes, IpAddress, or str."""
    if value is None:
        return None

    if hasattr(value, "prettyPrint"):
        try:
            pp = str(value.prettyPrint()).strip()
            parts = pp.split(".")
            if len(parts) == 4 and all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
                return pp
        except Exception:
            pass

    try:
        raw_b = bytes(value)
        if len(raw_b) == 4:
            return ".".join(str(b) for b in raw_b)
        val_str = raw_b.decode("utf-8", errors="ignore").strip()
        parts = val_str.split(".")
        if len(parts) == 4 and all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
            return val_str
    except Exception:
        pass

    s = str(value).strip()
    parts = s.split(".")
    if len(parts) == 4 and all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
        return s
    return None



async def get_device_ip_table(client: SnmpClient) -> tuple[dict[int, str], dict[int, str], list[str]]:
    """Retrieve mapping of ifIndex -> IP, ifIndex -> subnet mask, and list of all valid IPs."""
    ip_by_ifindex: dict[int, str] = {}
    mask_by_ifindex: dict[int, str] = {}
    all_ips: list[str] = []

    try:
        if_rows = await client.walk_raw(oid.ip_ad_ent_if_index())
        mask_rows = await client.walk_raw(oid.ip_ad_ent_net_mask())

        mask_by_ip: dict[str, str] = {}
        for oid_parts, mask_raw in mask_rows:
            if len(oid_parts) >= 4:
                ip_str = ".".join(str(p) for p in oid_parts[-4:])
                mask_str = parse_ip_str(mask_raw)
                if mask_str:
                    mask_by_ip[ip_str] = mask_str

        for oid_parts, if_val in if_rows:
            if len(oid_parts) >= 4:
                ip_str = ".".join(str(p) for p in oid_parts[-4:])
                if ip_str not in ("0.0.0.0", "127.0.0.1") and not ip_str.startswith("127."):
                    if ip_str not in all_ips:
                        all_ips.append(ip_str)

                    if_idx = value_to_u32(if_val)
                    if if_idx is not None and if_idx not in ip_by_ifindex:
                        ip_by_ifindex[if_idx] = ip_str
                        if ip_str in mask_by_ip:
                            mask_by_ifindex[if_idx] = mask_by_ip[ip_str]
    except Exception:
        pass

    return ip_by_ifindex, mask_by_ifindex, all_ips


async def get_device_interface(client: SnmpClient) -> list[Interface]:
    """Retrieve and build Interface models for all network ports via ifTable and IP-MIB."""
    descriptions = await client.walk_column(oid.if_descr())
    names = await client.walk_column(oid.if_name())
    macs = await client.walk_column(oid.if_phys_address())
    admin_status = await client.walk_column(oid.if_admin_status())
    oper_status = await client.walk_column(oid.if_oper_status())
    ip_by_ifindex, mask_by_ifindex, _ = await get_device_ip_table(client)

    interfaces: list[Interface] = []

    all_indices = sorted(
        set(descriptions.keys())
        | set(names.keys())
        | set(macs.keys())
        | set(ip_by_ifindex.keys())
    )

    for index in all_indices:
        description = names.get(index) or descriptions.get(index)
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
            ip_address=ip_by_ifindex.get(index),
            subnet_mask=mask_by_ifindex.get(index),
        )
        interfaces.append(interface)

    interfaces.sort(key=lambda inf: inf.index)
    return interfaces


async def get_device_ip_addresses(client: SnmpClient) -> list[str]:
    """Retrieve all IPv4 addresses configured on the device from IP-MIB ipAddrTable."""
    _, _, all_ips = await get_device_ip_table(client)
    return all_ips


