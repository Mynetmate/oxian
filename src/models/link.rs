use std::net::IpAddr;

#[derive(Debug, Clone, PartialEq)]
pub struct Link {
    pub source_ip: Option<IpAddr>,
    pub source_chassis_id: Option<String>,
    pub source_interface: Option<String>,

    pub target_ip: Option<IpAddr>,
    pub target_chassis_id: Option<String>,
    pub target_hostname: Option<String>,
    pub target_port_id: String,
    pub target_port_description: Option<String>,
}
