from __future__ import annotations

from typing import Optional

try:
    from ..models.device import Vendor
except (ImportError, ValueError):
    from models.device import Vendor


def detect_vendor(sys_object_id: Optional[str]) -> Vendor:
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
