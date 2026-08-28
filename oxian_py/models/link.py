from __future__ import annotations

from ipaddress import IPv4Address, IPv6Address
from pydantic import BaseModel, ConfigDict


class Link(BaseModel):
    """Represents a topological link between two network devices or interfaces."""

    model_config = ConfigDict(arbitrary_types_allowed=True, use_enum_values=True)

    source_ip: str | IPv4Address | IPv6Address | None = None
    source_chassis_id: str | None = None
    source_interface: str | None = None

    target_ip: str | IPv4Address | IPv6Address | None = None
    target_chassis_id: str | None = None
    target_hostname: str | None = None
    target_port_id: str = ""
    target_port_description: str | None = None
