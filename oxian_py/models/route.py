from __future__ import annotations

from ipaddress import IPv4Address, IPv6Address
from typing import Union
from pydantic import BaseModel, ConfigDict


class DefaultRoute(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, use_enum_values=True)

    next_hop: Union[str, IPv4Address, IPv6Address]
    local_interface: int
