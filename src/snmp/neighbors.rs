use std::net::IpAddr;

use async_snmp::Client;

use crate::{
    model::Neighbor,
    snmp::{oid, walk_lldp_column},
};

pub async fn get_local_chassis_id(client: &Client) -> anyhow::Result<Option<String>> {
    let result = client.get(&oid::lldp_loc_chassis_id()).await;

    match result {
        Ok(v) => Ok(Some(normalize_chassis_id(&v.value.to_string()))),
        Err(_) => Ok(None),
    }
}

pub async fn discover_neighbors(client: &Client) -> anyhow::Result<Vec<Neighbor>> {
    let hostnames = walk_lldp_column(client, oid::lldp_rem_sys_name()).await?;
    let ports = walk_lldp_column(client, oid::lldp_rem_port_id()).await?;
    let port_descriptions = walk_lldp_column(client, oid::lldp_rem_port_description()).await?;

    let addresses = walk_lldp_column(client, oid::lldp_rem_man_addr()).await?;
    let chassis_ids = walk_lldp_column(client, oid::lldp_rem_chassis_id()).await?;

    let mut neighbors: Vec<Neighbor> = Vec::new();

    for (index, chassis_id) in chassis_ids {
        let hostname = hostnames.get(&index);
        let port = ports.get(&index);
        let port_description = port_descriptions.get(&index);
        let address = addresses.get(&index);

        neighbors.push(Neighbor {
            chassis_id: normalize_chassis_id(&chassis_id.to_string()),
            remote_port_id: port.map(|v| v.to_string()).unwrap_or_default(),
            remote_port_description: port_description.map(|v| v.to_string()),
            hostname: hostname.map(|v| v.to_string()),
            remote_ip: address.and_then(|v| v.to_string().parse::<IpAddr>().ok()),
            local_interface: index.1,
        });
    }

    Ok(neighbors)
}

fn normalize_chassis_id(value: &str) -> String {
    value
        .trim()
        .trim_start_matches("0x")
        .replace(':', "")
        .replace('.', "")
        .replace('-', "")
        .to_ascii_lowercase()
}
