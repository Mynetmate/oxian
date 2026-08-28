from __future__ import annotations

from ipaddress import IPv4Address, IPv6Address
from typing import Optional, Union
from pydantic import BaseModel, ConfigDict


class Neighbor(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, use_enum_values=True)

    chassis_id: str = ""
    remote_port_id: str = ""
    remote_port_description: Optional[str] = None
    hostname: Optional[str] = None
    remote_ip: Optional[Union[str, IPv4Address, IPv6Address]] = None
    local_interface: int = 0


class UnresolvedNeighbor(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, use_enum_values=True)

    source_ip: Union[str, IPv4Address, IPv6Address]
    neighbor: Neighbor
