use std::{
    collections::{HashSet, VecDeque},
    net::IpAddr,
};

use ipnet::Ipv4Net;

use crate::{
    models::{Device, DiscoveryResult, Link, Neighbor, UnresolvedNeighbor},
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
    let mut links = Vec::new();

    let mut neighbor_records: Vec<(IpAddr, Neighbor)> = Vec::new();
    let mut unresolved_neighbors = Vec::new();

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
            neighbor_records.push((device.ip, neighbor));
        }

        for neighbor in &neighbors {
            if let Some(remote_ip) = neighbor.remote_ip {
                if !visited.contains(&remote_ip) {
                    queue.push_back(remote_ip);
                }
            }
        }

        visited.insert(ip);
        devices.push(device);
    }

    for (source_ip, neighbor) in &neighbor_records {
        let source_device = devices.iter().find(|d| d.ip == *source_ip);

        let Some(source_device) = source_device else {
            continue;
        };

        let source_interface = source_device
            .interface
            .iter()
            .find(|inf| inf.index == neighbor.local_interface)
            .and_then(|inf| inf.description.clone());

        let target_device = devices
            .iter()
            .find(|d| d.chassis_id.as_deref() == Some(neighbor.chassis_id.as_str()))
            .or_else(|| {
                neighbor
                    .remote_ip
                    .and_then(|ip| devices.iter().find(|d| d.ip == ip))
            })
            .or_else(|| {
                devices
                    .iter()
                    .find(|d| d.hostname.as_deref() == neighbor.hostname.as_deref())
            });

        let Some(target_device) = target_device else {
            unresolved_neighbors.push(UnresolvedNeighbor {
                source_ip: *source_ip,
                neighbor: neighbor.clone(),
            });
            continue;
        };

        let exists = links.iter().any(|l: &Link| {
            (l.source_ip == source_device.ip) && (l.target_ip == target_device.ip)
                || (l.source_ip == target_device.ip) && (l.target_ip == source_device.ip)
        });

        if !exists {
            links.push(Link {
                source_ip: source_device.ip,
                source_interface,
                target_ip: target_device.ip,
                target_port_id: neighbor.remote_port_id.clone(),
                target_port_description: neighbor.remote_port_description.clone(),
            });
        }
    }

    Ok(DiscoveryResult {
        devices,
        links,
        unresolved_neighbors,
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
        ip,
        hostname: sys_info.hostname,
        description: sys_info.description,
        vendor,
        interface,
        chassis_id,
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
