use clap::{Parser, Subcommand};
use ipnet::Ipv4Net;

#[derive(Parser)]
pub struct Cli {
    #[command(subcommand)]
    pub command: Commands,
}

#[derive(Subcommand)]
pub enum Commands {
    Scan { ip_cidr: Ipv4Net },
}
