use std::net::IpAddr;

use crate::{
    models::{DefaultRoute, Device, Neighbor},
    snmp, vendor,
};

pub async fn scan_one_device(
    ip: IpAddr,
) -> anyhow::Result<(Device, Vec<Neighbor>, Option<DefaultRoute>)> {
    let client = snmp::connect(ip).await?;

    let sys_info = snmp::get_device_info(&client).await?;
    let interface = snmp::get_device_interface(&client).await?;
    let chassis_id = snmp::get_local_chassis_id(&client).await?;
    let neighbors = snmp::discover_neighbors(&client).await?;
    let default_route = snmp::get_default_route(&client).await.unwrap_or(None);

    let vendor = vendor::detect_vender(sys_info.object_id.as_deref());

    let device = Device {
        ip: Some(ip),
        hostname: sys_info.hostname,
        description: sys_info.description,
        vendor,
        interface,
        chassis_id,
        is_managed: true,
    };

    Ok((device, neighbors, default_route))
}
