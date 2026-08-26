use serde::Serialize;

use crate::models::{Device, Link, UnresolvedNeighbor};

#[derive(Debug, Clone, PartialEq, Serialize)]
pub struct DiscoveryResult {
    pub devices: Vec<Device>,
    pub links: Vec<Link>,
    pub unresolved_neighbors: Vec<UnresolvedNeighbor>,
}
