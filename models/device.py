from __future__ import annotations

from enum import Enum
from ipaddress import IPv4Address, IPv6Address
from typing import Optional, Union
from pydantic import BaseModel, ConfigDict, Field

from .interface import Interface


class Vendor(str, Enum):
    Cisco = "Cisco"
    MikroTik = "MikroTik"
    Juniper = "Juniper"
    Unknown = "Unknown"


class Device(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, use_enum_values=True)

    ip: Optional[Union[str, IPv4Address, IPv6Address]] = None
    hostname: Optional[str] = None
    description: Optional[str] = None
    vendor: Vendor = Vendor.Unknown
    interfaces: list[Interface] = Field(default_factory=list)
    chassis_id: Optional[str] = None
    is_managed: bool = True
