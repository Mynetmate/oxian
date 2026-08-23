use std::net::IpAddr;

use crate::models::{
    DefaultRoute, Device, DiscoveryResult, Link, Neighbor, UnresolvedNeighbor, Vendor,
};

pub fn resolve_topology(
    mut devices: Vec<Device>,
    neighbor_records: Vec<(IpAddr, Neighbor)>,
    default_routes: Vec<(IpAddr, DefaultRoute)>,
) -> DiscoveryResult {
    let mut links = Vec::new();
    let mut unresolved_neighbors = Vec::new();

    resolve_lldp_neighbors(
        &mut devices,
        &neighbor_records,
        &mut links,
        &mut unresolved_neighbors,
    );

    resolve_default_routes(&mut devices, &default_routes, &mut links);

    DiscoveryResult {
        devices,
        links,
        unresolved_neighbors,
    }
}

fn resolve_lldp_neighbors(
    devices: &mut Vec<Device>,
    neighbor_records: &[(IpAddr, Neighbor)],
    links: &mut Vec<Link>,
    unresolved_neighbors: &mut Vec<UnresolvedNeighbor>,
) {
    for (_, neighbor) in neighbor_records {
        let is_already_known = find_target_device(devices, neighbor).is_some();
        if is_already_known {
            continue;
        }

        let Some(unresolved_device) = infer_unresolved_device(neighbor) else {
            continue;
        };

        devices.push(unresolved_device);
    }

    for (source_ip, neighbor) in neighbor_records {
        let Some(source_device) = devices.iter().find(|d| d.ip == Some(*source_ip)) else {
            continue;
        };

        let source_interface = source_device
            .interface
            .iter()
            .find(|inf| inf.index == neighbor.local_interface)
            .and_then(|inf| inf.description.clone());

        let Some(target_device) = find_target_device(devices, neighbor) else {
            unresolved_neighbors.push(UnresolvedNeighbor {
                source_ip: *source_ip,
                neighbor: neighbor.clone(),
            });
            continue;
        };

        if !is_duplicate_link(
            links,
            source_device,
            target_device,
            source_interface.as_deref(),
            &neighbor.remote_port_id,
        ) {
            links.push(Link {
                source_ip: source_device.ip,
                source_chassis_id: source_device.chassis_id.clone(),
                source_interface,
                target_ip: target_device.ip,
                target_chassis_id: target_device.chassis_id.clone(),
                target_hostname: target_device.hostname.clone(),
                target_port_id: neighbor.remote_port_id.clone(),
                target_port_description: neighbor.remote_port_description.clone(),
            });
        }
    }
}

fn resolve_default_routes(
    devices: &mut Vec<Device>,
    default_routes: &[(IpAddr, DefaultRoute)],
    links: &mut Vec<Link>,
) {
    for (_, route) in default_routes {
        let is_already_known = devices.iter().any(|d| d.ip == Some(route.next_hop));

        if is_already_known {
            continue;
        }

        let gateway_device = Device {
            ip: Some(route.next_hop),
            hostname: Some("Default Gateway".to_string()),
            description: Some("Discovered via Default Route (0.0.0.0/0)".to_string()),
            vendor: Vendor::Unknown,
            interface: vec![],
            chassis_id: None,
            is_managed: false,
        };

        devices.push(gateway_device);
    }

    for (source_ip, route) in default_routes {
        let Some(source_device) = devices.iter().find(|d| d.ip == Some(*source_ip)) else {
            continue;
        };

        let source_interface = source_device
            .interface
            .iter()
            .find(|inf| inf.index == route.local_interface)
            .and_then(|inf| inf.description.clone());

        let Some(target_device) = devices.iter().find(|d| d.ip == Some(route.next_hop)) else {
            continue;
        };

        let port_id = "default-route";

        if !is_duplicate_link(
            links,
            source_device,
            target_device,
            source_interface.as_deref(),
            port_id,
        ) {
            links.push(Link {
                source_ip: source_device.ip,
                source_chassis_id: source_device.chassis_id.clone(),
                source_interface,
                target_ip: target_device.ip,
                target_chassis_id: target_device.chassis_id.clone(),
                target_hostname: target_device.hostname.clone(),
                target_port_id: port_id.to_string(),
                target_port_description: Some("0.0.0.0/0 Next-Hop".to_string()),
            });
        }
    }
}

fn matches_neighbor(device: &Device, neighbor: &Neighbor) -> bool {
    (!neighbor.chassis_id.is_empty()
        && device.chassis_id.as_deref() == Some(neighbor.chassis_id.as_str()))
        || (neighbor.remote_ip.is_some() && device.ip == neighbor.remote_ip)
        || (neighbor.hostname.is_some()
            && device.hostname.as_deref() == neighbor.hostname.as_deref())
}

fn find_target_device<'a>(devices: &'a [Device], neighbor: &Neighbor) -> Option<&'a Device> {
    devices
        .iter()
        .find(|device| matches_neighbor(device, neighbor))
}

fn infer_unresolved_device(neighbor: &Neighbor) -> Option<Device> {
    let has_identity = !neighbor.chassis_id.is_empty()
        || neighbor.remote_ip.is_some()
        || neighbor.hostname.is_some();

    if !has_identity {
        return None;
    }

    let chassis_id = if neighbor.chassis_id.is_empty() {
        None
    } else {
        Some(neighbor.chassis_id.clone())
    };

    Some(Device {
        ip: neighbor.remote_ip,
        hostname: neighbor.hostname.clone(),
        description: neighbor.remote_port_description.clone(),
        vendor: Vendor::Unknown,
        interface: vec![],
        chassis_id,
        is_managed: false,
    })
}

fn is_duplicate_link(
    links: &[Link],
    source: &Device,
    target: &Device,
    source_interface: Option<&str>,
    remote_port_id: &str,
) -> bool {
    links.iter().any(|link| {
        let forward = link.source_ip == source.ip
            && link.source_interface.as_deref() == source_interface
            && link.target_chassis_id == target.chassis_id
            && link.target_port_id == remote_port_id;

        let reverse = link.source_chassis_id == target.chassis_id
            && link.target_chassis_id == source.chassis_id
            && ((link.source_ip.is_some() && link.source_ip == target.ip)
                || (link.target_ip.is_some() && link.target_ip == source.ip));

        forward || reverse
    })
}
