use clap::Parser;
use ipnet::Ipv4Net;
use oxian::cli::{Cli, Commands};

#[tokio::main]
async fn main() {
    let cli = Cli::parse();

    match cli.command {
        Commands::Scan { ip_cidr } => snmp_scan(ip_cidr),
    }
}

fn snmp_scan(ip_cidr: Ipv4Net) {
    let ip = ip_cidr.addr();
    let ip_network = ip_cidr.network();

    if ip != ip_network {
        snmp_walk();
        todo!("scan only router or switch");
    } else {
        snmp_walk();
        todo!("scan all network");
    }
}

fn snmp_scan_agent() {
    todo!("scan snmp agent");
}

fn snmp_walk() {
    todo!("scan snmp agent in other networks");
}
