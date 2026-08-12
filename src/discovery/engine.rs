use std::{
    collections::{HashSet, VecDeque},
    net::IpAddr,
};

use crate::{
    model::{Device, DiscoveryResult, Link, Neighbor},
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

    queue.push_back(ip);

    while let Some(ip) = queue.pop_front() {
        if visited.contains(&ip) {
            continue;
        }

        let (device, neighbors) = match scan_one_device(ip).await {
            Ok(d) => d,
            Err(e) => {
                eprintln!("Failed to scan {ip}: {e}");
                visited.insert(ip);
                continue;
            }
        };

        for neighbor in &neighbors {
            if let Some(remote_ip) = neighbor.remote_ip {
                let local_interface = device
                    .interface
                    .iter()
                    .find(|interface| interface.index == neighbor.local_interface)
                    .and_then(|interface| interface.description.clone());

                links.push(Link {
                    source_ip: device.ip,
                    source_interface: local_interface,

                    target_ip: remote_ip,
                    target_interface: neighbor.remote_interface.clone(),
                });
            }
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

    Ok(DiscoveryResult { devices, links })
}

async fn scan_one_device(ip: IpAddr) -> anyhow::Result<(Device, Vec<Neighbor>)> {
    let client = snmp::connect(ip).await?;

    let sys_info = snmp::get_device_info(&client).await?;
    let interface = snmp::get_device_interface(&client).await?;
    let neighbors = snmp::discover_neighbors(&client).await?;

    let vendor = vendor::detect_vender(sys_info.object_id.as_deref());

    let device = Device {
        ip,
        hostname: sys_info.hostname,
        description: sys_info.description,
        vendor,
        interface,
    };

    Ok((device, neighbors))
}

#[allow(dead_code)]
async fn scan_network(ip: IpAddr, cidr: u8) -> anyhow::Result<DiscoveryResult> {
    // let ip_net = Ipv4Net::new(ip.is_ipv4(), cidr);

    if cidr == 0 && cidr > 30 {
        panic!("Error cannot parse ip or subnet");
    }

    todo!("scan all network {:?}", ip);
    // snmp_scan(ip, cidr).await;
}
