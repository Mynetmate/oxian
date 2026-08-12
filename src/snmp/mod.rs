mod client;
mod interface;
mod neighbors;
mod oid;
mod system;

pub use client::connect;
pub use interface::get_device_interface;
pub use neighbors::discover_neighbors;
pub use system::get_device_info;

use async_snmp::{Client, Oid, Value};
use std::collections::HashMap;

async fn walk_column(client: &Client, oid: Oid) -> anyhow::Result<HashMap<u32, Value>> {
    let mut result = HashMap::new();
    let mut walk = client.walk(oid)?;

    while let Some(item) = walk.next().await {
        let vb = item?;

        let parts = vb.oid.as_ref();
        let if_index = *parts.last().unwrap();

        result.insert(if_index, vb.value);
    }

    Ok(result)
}

type LldpIndex = (u32, u32, u32);

async fn walk_lldp_column(client: &Client, oid: Oid) -> anyhow::Result<HashMap<LldpIndex, Value>> {
    let mut result = HashMap::new();
    let mut walk = client.walk(oid)?;

    while let Some(item) = walk.next().await {
        let vb = item?;

        let parts = vb.oid.as_ref();

        if parts.len() < 3 {
            continue;
        }

        let len = parts.len();

        let index = (parts[len - 3], parts[len - 2], parts[len - 1]);

        result.insert(index, vb.value);
    }

    Ok(result)
}
