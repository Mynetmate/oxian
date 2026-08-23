use std::net::{IpAddr, Ipv4Addr};

use async_snmp::{Client, Oid, Value};

use crate::{models::DefaultRoute, snmp::oid};

pub async fn get_default_route(client: &Client) -> anyhow::Result<Option<DefaultRoute>> {
    let mut walk = match client.walk(oid::ip_cidr_route_next_hop()) {
        Ok(w) => w,
        Err(_) => return Ok(None),
    };

    while let Some(item) = walk.next().await {
        let vb = item?;
        let parts = vb.oid.as_ref();

        // OID suffix format: [dest: 4, mask: 4, tos: 1, next_hop: 4]
        if parts.len() < 13 {
            continue;
        }

        let len = parts.len();
        let dest = &parts[len - 13..len - 9];
        let mask = &parts[len - 9..len - 5];

        if dest != [0, 0, 0, 0] || mask != [0, 0, 0, 0] {
            continue;
        }

        let next_hop = match &vb.value {
            Value::IpAddress(octets) => IpAddr::V4(Ipv4Addr::from(*octets)),
            _ => {
                let nh = &parts[len - 4..len];
                IpAddr::V4(Ipv4Addr::new(
                    nh[0] as u8,
                    nh[1] as u8,
                    nh[2] as u8,
                    nh[3] as u8,
                ))
            }
        };

        let suffix = &parts[len - 13..len];
        let mut if_index_parts = vec![1, 3, 6, 1, 2, 1, 4, 24, 4, 1, 5];
        if_index_parts.extend_from_slice(suffix);

        let local_interface = match client.get(&Oid::from(if_index_parts)).await {
            Ok(vb) => match vb.value {
                Value::Integer(v) => u32::try_from(v).unwrap_or(0),
                Value::Gauge32(v) | Value::UInteger32(v) => v,
                _ => 0,
            },
            Err(_) => 0,
        };

        return Ok(Some(DefaultRoute {
            next_hop,
            local_interface,
        }));
    }

    Ok(None)
}
