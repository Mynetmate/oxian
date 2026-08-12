use std::net::IpAddr;

use clap::{Parser, Subcommand};

#[derive(Parser)]
#[command(name = "oxian", version, about = "Network device scanner")]
pub struct Cli {
    #[command(subcommand)]
    pub commands: Commands,
}

#[derive(Subcommand)]
pub enum Commands {
    /// Scan a subnet for network devices
    Scan {
        /// Target IP address (e.g. 192.168.1.1)
        ip: IpAddr,

        /// CIDR prefix length (e.g. 24 for /24)
        #[arg(short, long)]
        cidr: Option<u8>,
    },
    // Walk {
    //     ip_address: Ipv4Addr,
    // },
}
