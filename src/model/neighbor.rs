use std::net::IpAddr;

#[derive(Debug)]
pub struct Neighbor {
    pub hostname: Option<String>,
    pub remote_ip: Option<IpAddr>,
    pub local_interface: u32,
    pub remote_interface: Option<String>,
}
