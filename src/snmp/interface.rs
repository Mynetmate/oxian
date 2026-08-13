use async_snmp::Client;

use crate::{
    models::{Interface, InterfaceStatus},
    snmp::{oid, walk_column},
};

pub async fn get_device_interface(client: &Client) -> anyhow::Result<Vec<Interface>> {
    let descriptions = walk_column(client, oid::if_descr()).await?;
    let macs = walk_column(client, oid::if_phys_address()).await?;
    let admin_status = walk_column(client, oid::if_admin_status()).await?;
    let oper_status = walk_column(client, oid::if_oper_status()).await?;

    let mut interfaces = Vec::new();

    for (index, description) in descriptions {
        let interface = Interface {
            index,
            description: Some(description.to_string()),
            mac_address: macs.get(&index).and_then(parse_mac),
            admin_status: admin_status
                .get(&index)
                .and_then(value_to_u32)
                .map(InterfaceStatus::from),
            oper_status: oper_status
                .get(&index)
                .and_then(value_to_u32)
                .map(InterfaceStatus::from),
        };

        interfaces.push(interface);
    }

    let mut interfaces: Vec<_> = interfaces.into_iter().collect();
    interfaces.sort_by_key(|interface| interface.index);

    Ok(interfaces)
}

fn value_to_u32(value: &async_snmp::Value) -> Option<u32> {
    match value {
        async_snmp::Value::Integer(v) => u32::try_from(*v).ok(),
        async_snmp::Value::Counter32(v) => Some(*v),
        async_snmp::Value::Gauge32(v) => Some(*v),
        async_snmp::Value::UInteger32(v) => Some(*v),
        _ => None,
    }
}

fn parse_mac(value: &async_snmp::Value) -> Option<String> {
    let raw = value.to_string();

    let hex = raw.strip_prefix("0x")?;

    if hex.len() != 12 {
        return None;
    }

    if hex.chars().all(|c| c == '0') {
        return None;
    }

    Some(
        hex.as_bytes()
            .chunks(2)
            .map(|chunk| std::str::from_utf8(chunk).ok())
            .collect::<Option<Vec<_>>>()?
            .join(":")
            .to_uppercase(),
    )
}
