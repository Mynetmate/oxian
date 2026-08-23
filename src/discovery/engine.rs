use std::{
    collections::{HashSet, VecDeque},
    net::IpAddr,
};

use ipnet::Ipv4Net;

use crate::{
    models::{Device, DiscoveryResult, Link, Neighbor, UnresolvedNeighbor, Vendor},
    snmp, vendor,
};

pub async fn scan(ip: IpAddr, cidr: Option<u8>) -> anyhow::Result<DiscoveryResult> {
    match cidr {
        Some(subnet) => scan_network(ip, subnet).await,
        None => scan_device(ip).await,
    }
}

async fn scan_device(ip: IpAddr) -> anyhow::Result<DiscoveryResult> {
    let mut queue: VecDeque<IpAddr> = VecDeque::new();
    let mut visited = HashSet::new();
    let mut devices = Vec::new();

    let mut neighbor_records: Vec<(IpAddr, Neighbor)> = Vec::new();

    queue.push_back(ip);

    while let Some(ip) = queue.pop_front() {
        if visited.contains(&ip) {
            continue;
        }

        let (device, neighbors) = match scan_one_device(ip).await {
            Ok(result) => result,
            Err(e) => {
                eprintln!("Failed to scan {ip}: {e}");
                visited.insert(ip);
                continue;
            }
        };

        for neighbor in neighbors.iter().cloned() {
            neighbor_records.push((ip, neighbor));
        }

        for neighbor in &neighbors {
            let Some(remote_ip) = neighbor.remote_ip else {
                continue;
            };

            if !visited.contains(&remote_ip) {
                queue.push_back(remote_ip);
            }
        }

        visited.insert(ip);
        devices.push(device);
    }

    Ok(resolve_topology(devices, neighbor_records))
}

pub fn resolve_topology(
    mut devices: Vec<Device>,
    neighbor_records: Vec<(IpAddr, Neighbor)>,
) -> DiscoveryResult {
    let mut links = Vec::new();
    let mut unresolved_neighbors = Vec::new();

    for (_, neighbor) in &neighbor_records {
        let is_already_known = find_target_device(&devices, neighbor).is_some();

        if is_already_known {
            continue;
        }

        let Some(unresolved_device) = infer_unresolved_device(neighbor) else {
            continue;
        };

        devices.push(unresolved_device);
    }

    for (source_ip, neighbor) in &neighbor_records {
        let Some(source_device) = devices.iter().find(|d| d.ip == Some(*source_ip)) else {
            continue;
        };

        let source_interface = source_device
            .interface
            .iter()
            .find(|inf| inf.index == neighbor.local_interface)
            .and_then(|inf| inf.description.clone());

        let Some(target_device) = find_target_device(&devices, neighbor) else {
            unresolved_neighbors.push(UnresolvedNeighbor {
                source_ip: *source_ip,
                neighbor: neighbor.clone(),
            });
            continue;
        };

        if !is_duplicate_link(
            &links,
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

    DiscoveryResult {
        devices,
        links,
        unresolved_neighbors,
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

async fn scan_one_device(ip: IpAddr) -> anyhow::Result<(Device, Vec<Neighbor>)> {
    let client = snmp::connect(ip).await?;

    let sys_info = snmp::get_device_info(&client).await?;
    let interface = snmp::get_device_interface(&client).await?;
    let chassis_id = snmp::get_local_chassis_id(&client).await?;
    let neighbors = snmp::discover_neighbors(&client).await?;

    let vendor = vendor::detect_vender(sys_info.object_id.as_deref());

    let device = Device {
        ip: Some(ip),
        hostname: sys_info.hostname,
        description: sys_info.description,
        vendor,
        interface,
        chassis_id,
        is_managed: true,
    };

    Ok((device, neighbors))
}

async fn scan_network(ip: IpAddr, cidr: u8) -> anyhow::Result<DiscoveryResult> {
    let net = match ip {
        IpAddr::V4(ipv4) => Ipv4Net::new(ipv4, cidr)?,
        IpAddr::V6(_) => anyhow::bail!("IPv6 is not supported yet"),
    };

    let mut devices = Vec::new();
    // let links = Vec::new();
    // let unresolved_neighbors = Vec::new();

    for host in net.hosts() {
        let ip = IpAddr::V4(host);

        match scan_one_device(ip).await {
            Ok((device, _neighbors)) => {
                devices.push(device);
            }
            Err(_) => {
                continue;
            }
        }
    }

    println!("{:?}", devices);
    todo!("Concurrent devices scan")

    // Ok(DiscoveryResult {
    //     devices,
    //     links,
    //     unresolved_neighbors,
    // });
}
