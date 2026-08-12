use std::net::IpAddr;

use async_snmp::Client;

use crate::{
    model::Neighbor,
    snmp::{oid, walk_lldp_column},
};

pub async fn discover_neighbors(client: &Client) -> anyhow::Result<Vec<Neighbor>> {
    let hostnames = walk_lldp_column(client, oid::lldp_rem_sys_name()).await?;
    let ports = walk_lldp_column(client, oid::lldp_rem_port_id()).await?;
    let addresses = walk_lldp_column(client, oid::lldp_rem_man_addr()).await?;

    let mut neighbors: Vec<Neighbor> = Vec::new();

    for (index, hostname) in hostnames {
        let port = ports.get(&index);
        let address = addresses.get(&index);

        neighbors.push(Neighbor {
            hostname: Some(hostname.to_string()),
            remote_interface: port.map(|v| v.to_string()),
            local_interface: index.1,
            remote_ip: address.and_then(|v| v.to_string().parse::<IpAddr>().ok()),
        });
    }

    Ok(neighbors)
}
