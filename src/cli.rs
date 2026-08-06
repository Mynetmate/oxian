use std::net::Ipv4Addr;

use clap::{Parser, Subcommand};
use ipnet::Ipv4Net;

#[derive(Parser)]
pub struct Cli {
    #[command(subcommand)]
    pub commands: Commands,
}

#[derive(Subcommand)]
pub enum Commands {
    Walk { ip_address: Ipv4Addr },
    Scan { ip_cidr: Ipv4Net },
}
