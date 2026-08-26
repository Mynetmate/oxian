use crate::models::{Device, Link, UnresolvedNeighbor};

#[derive(Debug, Clone, PartialEq)]
pub struct DiscoveryResult {
    pub devices: Vec<Device>,
    pub links: Vec<Link>,
    pub unresolved_neighbors: Vec<UnresolvedNeighbor>,
}
