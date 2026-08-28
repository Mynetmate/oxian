from __future__ import annotations

from ipaddress import IPv4Address, IPv6Address
from typing import Optional, Union
from pydantic import BaseModel, ConfigDict


class Link(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, use_enum_values=True)

    source_ip: Optional[Union[str, IPv4Address, IPv6Address]] = None
    source_chassis_id: Optional[str] = None
    source_interface: Optional[str] = None

    target_ip: Optional[Union[str, IPv4Address, IPv6Address]] = None
    target_chassis_id: Optional[str] = None
    target_hostname: Optional[str] = None
    target_port_id: str = ""
    target_port_description: Optional[str] = None
