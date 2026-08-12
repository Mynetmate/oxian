use crate::model::{Device, Link};

#[derive(Debug)]
pub struct DiscoveryResult {
    pub devices: Vec<Device>,
    pub links: Vec<Link>,
}
