use clap::Parser;
use ipnet::Ipv4Net;
use oxian::cli::{Cli, Commands};

fn main() {
    let cli = Cli::parse();

    match cli.command {
        Commands::Scan { ip_cidr } => snmp_scan(ip_cidr),
    }
}

fn snmp_scan(ip_cidr: Ipv4Net) {
    let ip = ip_cidr.addr();
    let ip_network = ip_cidr.network();

    if ip != ip_network {
        // scan only router or switch
    } else {
        // scan all network
    }
}
