use std::net::IpAddr;

#[derive(Debug, Clone)]
pub struct Link {
    pub source_ip: IpAddr,
    pub source_interface: Option<String>,

    pub target_ip: IpAddr,
    pub target_port_id: String,
    pub target_port_description: Option<String>,
}
