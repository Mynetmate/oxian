use std::net::IpAddr;

#[derive(Debug, Clone, PartialEq)]
pub struct Neighbor {
    pub chassis_id: String,

    pub remote_port_id: String,
    pub remote_port_description: Option<String>,

    pub hostname: Option<String>,
    pub remote_ip: Option<IpAddr>,

    pub local_interface: u32,
}

#[derive(Debug, Clone, PartialEq)]
pub struct UnresolvedNeighbor {
    pub source_ip: IpAddr,
    pub neighbor: Neighbor,
}
