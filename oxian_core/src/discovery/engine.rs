use std::{
    collections::{HashSet, VecDeque},
    net::IpAddr,
};

use ipnet::Ipv4Net;

use crate::{
    discovery::{scanner, topology},
    models::{DefaultRoute, DiscoveryResult, Neighbor},
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
    let mut default_route_records: Vec<(IpAddr, DefaultRoute)> = Vec::new();

    queue.push_back(ip);

    while let Some(ip) = queue.pop_front() {
        if visited.contains(&ip) {
            continue;
        }

        let (device, neighbors, default_route) = match scanner::scan_one_device(ip).await {
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

        if let Some(route) = default_route {
            default_route_records.push((ip, route));
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

    let result = topology::resolve_topology(devices, neighbor_records, default_route_records);

    Ok(result)
}

async fn scan_network(ip: IpAddr, cidr: u8) -> anyhow::Result<DiscoveryResult> {
    let net = match ip {
        IpAddr::V4(ipv4) => Ipv4Net::new(ipv4, cidr)?,
        IpAddr::V6(_) => anyhow::bail!("IPv6 is not supported yet"),
    };

    let mut devices = Vec::new();

    for host in net.hosts() {
        let ip = IpAddr::V4(host);

        match scanner::scan_one_device(ip).await {
            Ok((device, _neighbors, _route)) => {
                devices.push(device);
            }
            Err(_) => {
                continue;
            }
        }
    }

    println!("{:?}", devices);
    todo!("Concurrent devices scan")
}
