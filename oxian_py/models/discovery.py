from __future__ import annotations

from typing import Any
from pydantic import BaseModel, ConfigDict, Field

from .device import Device
from .link import Link
from .neighbor import UnresolvedNeighbor


class DiscoveryResult(BaseModel):
    """Aggregate result of a network topology and device discovery scan."""

    model_config = ConfigDict(arbitrary_types_allowed=True, use_enum_values=True)

    devices: list[Device] = Field(default_factory=list, description="All discovered network devices (managed & inferred)")
    links: list[Link] = Field(default_factory=list, description="All resolved physical/logical links between nodes")
    unresolved_neighbors: list[UnresolvedNeighbor] = Field(default_factory=list, description="Discovered neighbors that could not be fully resolved")
    duration_ms: int | None = Field(default=None, description="Total discovery duration in milliseconds")

    def to_dict(self) -> dict[str, Any]:
        """Convert discovery results into a JSON-serializable dictionary."""
        return self.model_dump(mode="json")
