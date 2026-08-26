use serde::Serialize;
use std::net::IpAddr;

#[derive(Debug, Clone, PartialEq, Serialize)]
pub struct DefaultRoute {
    pub next_hop: IpAddr,
    pub local_interface: u32,
}
