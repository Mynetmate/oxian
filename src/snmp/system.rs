use async_snmp::Client;

use crate::snmp::oid;

#[derive(Debug)]
pub struct SystemInfo {
    pub hostname: Option<String>,
    pub description: Option<String>,
    pub object_id: Option<String>,
}

pub async fn get_device_info(client: &Client) -> anyhow::Result<SystemInfo> {
    let sys_name = client.get(&oid::sys_name()).await?;
    let sys_descr = client.get(&oid::sys_descr()).await?;
    let sys_object_id = client.get(&oid::sys_object_id()).await?;

    Ok(SystemInfo {
        hostname: Some(sys_name.value.to_string()),
        description: Some(sys_descr.value.to_string()),
        object_id: Some(sys_object_id.value.to_string()),
    })
}
