from __future__ import annotations

from ipaddress import IPv4Address, IPv6Address
from pydantic import BaseModel, ConfigDict


class Neighbor(BaseModel):
    """Raw neighbor adjacency discovered from LLDP or CDP tables."""

    model_config = ConfigDict(arbitrary_types_allowed=True, use_enum_values=True)

    chassis_id: str = ""
    remote_port_id: str = ""
    remote_port_description: str | None = None
    hostname: str | None = None
    remote_ip: str | IPv4Address | IPv6Address | None = None
    local_interface: int = 0
    protocol: str = "lldp"



class UnresolvedNeighbor(BaseModel):
    """An unresolved LLDP/CDP neighbor whose full device identity could not be queried."""

    model_config = ConfigDict(arbitrary_types_allowed=True, use_enum_values=True)

    source_ip: str | IPv4Address | IPv6Address
    neighbor: Neighbor
