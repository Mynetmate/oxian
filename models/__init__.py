from __future__ import annotations

from .device import Device, Vendor
from .discovery import DiscoveryResult
from .interface import Interface, InterfaceStatus
from .link import Link
from .neighbor import Neighbor, UnresolvedNeighbor
from .route import DefaultRoute

__all__ = [
    "Device",
    "Vendor",
    "DiscoveryResult",
    "Interface",
    "InterfaceStatus",
    "Link",
    "Neighbor",
    "UnresolvedNeighbor",
    "DefaultRoute",
]
