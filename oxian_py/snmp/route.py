from __future__ import annotations

import ipaddress

from ..models.route import DefaultRoute
from . import oid
from .client import SnmpClient


async def get_default_route(client: SnmpClient) -> DefaultRoute | None:
    """Extract default route (0.0.0.0/0) from RFC 2096 ipCidrRouteTable."""
    try:
        rows = await client.walk_raw(oid.ip_cidr_route_next_hop())
    except Exception:
        return None

    for oid_parts, val in rows:
        # Suffix format: [dest: 4, mask: 4, tos: 1, next_hop: 4]
        if len(oid_parts) < 13:
            continue

        dest = oid_parts[-13:-9]
        mask = oid_parts[-9:-5]

        if dest != (0, 0, 0, 0) and list(dest) != [0, 0, 0, 0]:
            continue
        if mask != (0, 0, 0, 0) and list(mask) != [0, 0, 0, 0]:
            continue

        # Extract next_hop
        next_hop = None
        if val is not None:
            val_str = str(val).strip()
            try:
                next_hop = str(ipaddress.ip_address(val_str))
            except ValueError:
                pass

        if next_hop is None:
            nh = oid_parts[-4:]
            next_hop = f"{nh[0]}.{nh[1]}.{nh[2]}.{nh[3]}"

        suffix = oid_parts[-13:]
        if_index_oid = "1.3.6.1.2.1.4.24.4.1.5." + ".".join(str(p) for p in suffix)

        try:
            if_val = await client.get(if_index_oid)
            local_interface = int(if_val) if if_val is not None else 0
        except Exception:
            local_interface = 0

        return DefaultRoute(
            next_hop=next_hop,
            local_interface=local_interface,
        )

    return None
