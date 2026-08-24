use std::net::IpAddr;

use crate::models;

#[derive(Debug, Clone, PartialEq)]
pub struct Device {
    pub ip: Option<IpAddr>,
    pub hostname: Option<String>,
    pub description: Option<String>,
    pub vendor: Vendor,
    pub interfaces: Vec<models::Interface>,

    pub chassis_id: Option<String>,
    pub is_managed: bool,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Vendor {
    Cisco,
    MikroTik,
    Juniper,
    Unknown,
}
