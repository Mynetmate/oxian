use std::net::IpAddr;

#[derive(Debug)]
pub struct Link {
    pub source_ip: IpAddr,
    pub source_interface: Option<String>,
    pub target_ip: IpAddr,
    pub target_interface: Option<String>,
}
