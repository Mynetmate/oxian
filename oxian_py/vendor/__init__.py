from __future__ import annotations

from ..models.device import Vendor


def detect_vendor(sys_object_id: str | None) -> Vendor:
    """Detect network device vendor based on SNMP sysObjectID.

    Args:
        sys_object_id: The SNMP sysObjectID string (e.g., '1.3.6.1.4.1.9.1.1').

    Returns:
        Vendor enum matching the sysObjectID enterprise prefix.
    """
    if not sys_object_id:
        return Vendor.Unknown
    oid = str(sys_object_id).strip()
    if oid == "1.3.6.1.4.1.9" or oid.startswith("1.3.6.1.4.1.9."):
        return Vendor.Cisco
    if oid == "1.3.6.1.4.1.14988" or oid.startswith("1.3.6.1.4.1.14988."):
        return Vendor.MikroTik
    if oid == "1.3.6.1.4.1.2636" or oid.startswith("1.3.6.1.4.1.2636."):
        return Vendor.Juniper
    return Vendor.Unknown


# Alias for backward compatibility with Rust typo
detect_vender = detect_vendor

__all__ = ["detect_vendor", "detect_vender"]
