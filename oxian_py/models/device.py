from __future__ import annotations

from enum import Enum
from ipaddress import IPv4Address, IPv6Address
from pydantic import BaseModel, ConfigDict, Field

from .interface import Interface


class Vendor(str, Enum):
    """Network device hardware vendor."""

    Cisco = "Cisco"
    MikroTik = "MikroTik"
    Juniper = "Juniper"
    Unknown = "Unknown"


class Device(BaseModel):
    """Represents a discovered network device."""

    model_config = ConfigDict(arbitrary_types_allowed=True, use_enum_values=True)

    ip: str | IPv4Address | IPv6Address | None = None
    hostname: str | None = None
    description: str | None = None
    vendor: Vendor = Vendor.Unknown
    interfaces: list[Interface] = Field(default_factory=list)
    chassis_id: str | None = None
    is_managed: bool = True
