use async_snmp::Client;

use crate::snmp::oid;

#[derive(Debug)]
pub struct SystemInfo {
    pub hostname: Option<String>,
    pub description: Option<String>,
    pub object_id: Option<String>,
}

pub async fn get_device_info(client: &Client) -> anyhow::Result<SystemInfo> {
    let mut sys_name = client.get(&oid::sys_name()).await?;
    let mut sys_descr = client.get(&oid::sys_descr()).await?;
    let mut sys_object_id = client.get(&oid::sys_object_id()).await?;

    let hostname = sys_name.varbinds.pop().map(|vb| vb.value.to_string());
    let description = sys_descr.varbinds.pop().map(|vb| vb.value.to_string());
    let object_id = sys_object_id.varbinds.pop().map(|vb| vb.value.to_string());

    Ok(SystemInfo {
        hostname,
        description,
        object_id,
    })
}
