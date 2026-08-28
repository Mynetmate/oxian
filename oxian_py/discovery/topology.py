from __future__ import annotations

from ipaddress import IPv4Address, IPv6Address

from ..models.device import Device, Vendor
from ..models.discovery import DiscoveryResult
from ..models.link import Link
from ..models.neighbor import Neighbor, UnresolvedNeighbor
from ..models.route import DefaultRoute


def _same_ip(
    ip1: str | IPv4Address | IPv6Address | None,
    ip2: str | IPv4Address | IPv6Address | None,
) -> bool:
    if ip1 is None or ip2 is None:
        return ip1 is ip2
    return str(ip1) == str(ip2)


def resolve_topology(
    devices: list[Device],
    neighbor_records: list[tuple[str | IPv4Address | IPv6Address, Neighbor]],
    default_routes: list[tuple[str | IPv4Address | IPv6Address, DefaultRoute]],
    duration_ms: int | None = None,
) -> DiscoveryResult:
    """Resolve physical links, inferred unmanaged nodes, and WAN gateways into a topology graph.

    Args:
        devices: Discovered managed network devices.
        neighbor_records: Discovered LLDP/CDP neighbor relationships.
        default_routes: Discovered default routes (0.0.0.0/0).
        duration_ms: Total discovery execution time in milliseconds.

    Returns:
        DiscoveryResult containing complete device list, resolved links, and unresolved neighbors.
    """
    devices_list = list(devices)
    links: list[Link] = []
    unresolved_neighbors: list[UnresolvedNeighbor] = []

    _resolve_lldp_neighbors(
        devices=devices_list,
        neighbor_records=neighbor_records,
        links=links,
        unresolved_neighbors=unresolved_neighbors,
    )

    _resolve_default_routes(
        devices=devices_list,
        default_routes=default_routes,
        links=links,
    )

    return DiscoveryResult(
        devices=devices_list,
        links=links,
        unresolved_neighbors=unresolved_neighbors,
        duration_ms=duration_ms,
    )


def _matches_neighbor(device: Device, neighbor: Neighbor) -> bool:
    has_chassis_match = (
        bool(neighbor.chassis_id)
        and device.chassis_id is not None
        and device.chassis_id == neighbor.chassis_id
    )
    has_ip_match = (
        neighbor.remote_ip is not None
        and _same_ip(device.ip, neighbor.remote_ip)
    )
    has_hostname_match = (
        neighbor.hostname is not None
        and device.hostname is not None
        and device.hostname == neighbor.hostname
    )
    return has_chassis_match or has_ip_match or has_hostname_match


def _find_target_device(devices: list[Device], neighbor: Neighbor) -> Device | None:
    for device in devices:
        if _matches_neighbor(device, neighbor):
            return device
    return None


def _infer_unresolved_device(neighbor: Neighbor) -> Device | None:
    has_identity = bool(neighbor.chassis_id) or (neighbor.remote_ip is not None) or (neighbor.hostname is not None)
    if not has_identity:
        return None

    chassis_id = neighbor.chassis_id if neighbor.chassis_id else None

    return Device(
        ip=neighbor.remote_ip,
        hostname=neighbor.hostname,
        description=neighbor.remote_port_description,
        vendor=Vendor.Unknown,
        interfaces=[],
        chassis_id=chassis_id,
        is_managed=False,
    )


def _is_duplicate_link(
    links: list[Link],
    source: Device,
    target: Device,
    source_interface: str | None,
    remote_port_id: str,
) -> bool:
    for link in links:
        forward = (
            _same_ip(link.source_ip, source.ip)
            and link.source_interface == source_interface
            and link.target_chassis_id == target.chassis_id
            and link.target_port_id == remote_port_id
        )

        reverse = (
            link.source_chassis_id == target.chassis_id
            and link.target_chassis_id == source.chassis_id
            and (
                (link.source_ip is not None and _same_ip(link.source_ip, target.ip))
                or (link.target_ip is not None and _same_ip(link.target_ip, source.ip))
            )
        )

        if forward or reverse:
            return True

    return False


def _resolve_lldp_neighbors(
    devices: list[Device],
    neighbor_records: list[tuple[str | IPv4Address | IPv6Address, Neighbor]],
    links: list[Link],
    unresolved_neighbors: list[UnresolvedNeighbor],
) -> None:
    # Phase 1: Infer unresolved nodes
    for _, neighbor in neighbor_records:
        if _find_target_device(devices, neighbor) is not None:
            continue

        unresolved_device = _infer_unresolved_device(neighbor)
        if unresolved_device is None:
            continue

        devices.append(unresolved_device)

    # Phase 2: Create links and collect unresolved neighbors
    for source_ip, neighbor in neighbor_records:
        source_device = next((d for d in devices if _same_ip(d.ip, source_ip)), None)
        if source_device is None:
            continue

        source_interface = None
        for inf in source_device.interfaces:
            if inf.index == neighbor.local_interface:
                source_interface = inf.description
                break

        target_device = _find_target_device(devices, neighbor)
        if target_device is None:
            unresolved_neighbors.append(
                UnresolvedNeighbor(
                    source_ip=source_ip,
                    neighbor=neighbor,
                )
            )
            continue

        if not _is_duplicate_link(
            links,
            source_device,
            target_device,
            source_interface,
            neighbor.remote_port_id,
        ):
            links.append(
                Link(
                    source_ip=source_device.ip,
                    source_chassis_id=source_device.chassis_id,
                    source_interface=source_interface,
                    target_ip=target_device.ip,
                    target_chassis_id=target_device.chassis_id,
                    target_hostname=target_device.hostname,
                    target_port_id=neighbor.remote_port_id,
                    target_port_description=neighbor.remote_port_description,
                    protocol="lldp",
                )
            )


def _resolve_default_routes(
    devices: list[Device],
    default_routes: list[tuple[str | IPv4Address | IPv6Address, DefaultRoute]],
    links: list[Link],
) -> None:
    # Phase 1: Add default gateway nodes if not already known
    for source_ip, route in default_routes:
        source_device = next((d for d in devices if _same_ip(d.ip, source_ip)), None)
        source_interface = None
        if source_device is not None:
            for inf in source_device.interfaces:
                if inf.index == route.local_interface:
                    source_interface = inf.description
                    break

        has_valid_ip = bool(route.next_hop) and str(route.next_hop) not in ("0.0.0.0", "127.0.0.1")

        if has_valid_ip:
            is_already_known = any(_same_ip(d.ip, route.next_hop) for d in devices)
            if not is_already_known:
                gateway_device = Device(
                    ip=route.next_hop,
                    hostname="Default Gateway",
                    description=f"Discovered via Default Route (0.0.0.0/0 Next-Hop {route.next_hop})",
                    vendor=Vendor.Unknown,
                    interfaces=[],
                    chassis_id=None,
                    is_managed=False,
                )
                devices.append(gateway_device)
        else:
            # Interface-only / Direct-attached default route
            gw_name = f"WAN Gateway ({source_interface})" if source_interface else "WAN Gateway"
            is_already_known = any(d.hostname == gw_name and d.ip is None for d in devices)
            if not is_already_known:
                gateway_device = Device(
                    ip=None,
                    hostname=gw_name,
                    description=f"Discovered via Interface Route (0.0.0.0/0 via {source_interface or 'interface'})",
                    vendor=Vendor.Unknown,
                    interfaces=[],
                    chassis_id=None,
                    is_managed=False,
                )
                devices.append(gateway_device)

    # Phase 2: Create default route links
    for source_ip, route in default_routes:
        source_device = next((d for d in devices if _same_ip(d.ip, source_ip)), None)
        if source_device is None:
            continue

        source_interface = None
        for inf in source_device.interfaces:
            if inf.index == route.local_interface:
                source_interface = inf.description
                break

        has_valid_ip = bool(route.next_hop) and str(route.next_hop) not in ("0.0.0.0", "127.0.0.1")
        if has_valid_ip:
            target_device = next((d for d in devices if _same_ip(d.ip, route.next_hop)), None)
            desc = f"0.0.0.0/0 Next-Hop ({route.next_hop})"
        else:
            gw_name = f"WAN Gateway ({source_interface})" if source_interface else "WAN Gateway"
            target_device = next((d for d in devices if d.hostname == gw_name and d.ip is None), None)
            desc = f"0.0.0.0/0 Direct Interface ({source_interface or 'interface'})"

        if target_device is None:
            continue

        port_id = "default-route"

        if not _is_duplicate_link(
            links,
            source_device,
            target_device,
            source_interface,
            port_id,
        ):
            links.append(
                Link(
                    source_ip=source_device.ip,
                    source_chassis_id=source_device.chassis_id,
                    source_interface=source_interface,
                    target_ip=target_device.ip,
                    target_chassis_id=target_device.chassis_id,
                    target_hostname=target_device.hostname,
                    target_port_id=port_id,
                    target_port_description=desc,
                    protocol="default_route",
                )
            )
