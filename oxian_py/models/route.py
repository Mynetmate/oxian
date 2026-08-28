from __future__ import annotations

from ipaddress import IPv4Address, IPv6Address
from pydantic import BaseModel, ConfigDict


class DefaultRoute(BaseModel):
    """Default route (0.0.0.0/0) information extracted from route tables."""

    model_config = ConfigDict(arbitrary_types_allowed=True, use_enum_values=True)

    next_hop: str | IPv4Address | IPv6Address
    local_interface: int
