use std::net::IpAddr;

use crate::model;

#[derive(Debug)]
pub struct Device {
    pub ip: IpAddr,
    pub hostname: Option<String>,
    pub description: Option<String>,
    pub vendor: Vendor,
    pub interface: Vec<model::Interface>,

    pub chassis_id: Option<String>,
}

#[derive(Debug)]
pub enum Vendor {
    Cisco,
    MikroTik,
    Juniper,
    Unknown,
}
