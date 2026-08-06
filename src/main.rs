use std::{net::Ipv4Addr, time::Duration};

use async_snmp::{Auth, Client, Value, oid};
use clap::Parser;
use ipnet::Ipv4Net;
use oxian::cli::{Cli, Commands};

#[tokio::main]
async fn main() {
    let cli = Cli::parse();

    match cli.commands {
        Commands::Walk { ip_address } => {
            let client = Client::builder((format!("{}", &ip_address), 1611), Auth::v2c("public"))
                .timeout(Duration::from_secs(5))
                .connect()
                .await
                .expect("error cannnot connect to client");

            let result = client.get(&oid!(1, 3, 6, 1, 2, 1, 1, 1, 0)).await;

            match result {
                Ok(data) => println!("First node: {}", data.value),
                Err(error) => panic!("{}", error),
            }

            let neighbor_ip = snmp_walk(&client).await;

            snmp_neighbor_scan(&neighbor_ip).await;
        }
        Commands::Scan { ip_cidr } => snmp_scan(ip_cidr).await,
    }
}

async fn snmp_scan(ip_cidr: Ipv4Net) {
    todo!("scan all network {}", ip_cidr);
}

async fn snmp_walk(snmp_client: &Client) -> Vec<Ipv4Addr> {
    // get a system OBJECT-CLASS
    // oid!(1, 3, 6, 1, 2, 1, 1)
    let mut walk = snmp_client
        .walk(oid!(1, 3, 6, 1, 2, 1, 2, 2, 1))
        .expect("cannot walk");

    while let Some(result) = walk.next().await {
        match result {
            Ok(vb) => println!("{}: {:?}", vb.oid, vb.value),
            Err(e) => {
                eprintln!("walk error: {}", e);
                break;
            }
        }
    }

    let mut neighbor_ip: Vec<Ipv4Addr> = Vec::new();

    let mut walk = snmp_client
        .walk(oid!(1, 3, 6, 1, 4, 1, 9, 9, 23, 1, 2, 1, 1))
        .expect("cannot walk");

    while let Some(result) = walk.next().await {
        match result {
            Ok(vb) => {
                if let Value::OctetString(bytes) = &vb.value {
                    if let Some(ip) = bytes_to_ipv4(&bytes) {
                        println!("Neighbor IP: {}", ip);
                        neighbor_ip.push(ip);
                    }
                };
            }
            Err(e) => {
                eprintln!("walk error: {}", e);
                break;
            }
        }
    }

    neighbor_ip
}

fn bytes_to_ipv4(bytes: &[u8]) -> Option<Ipv4Addr> {
    if bytes.len() == 4 {
        Some(Ipv4Addr::new(bytes[0], bytes[1], bytes[2], bytes[3]))
    } else {
        None
    }
}

async fn snmp_neighbor_scan(neighbor_ip: &Vec<Ipv4Addr>) {
    let mut sim_port = 1612;

    // ip use in production (without snmp sim)
    for _ip in neighbor_ip {
        let neighbor_client = Client::builder(
            format!("{}:{}", "127.0.0.1", &sim_port),
            Auth::v2c("public"),
        )
        .timeout(Duration::from_secs(5))
        .connect()
        .await
        .expect("error cannnot connect to client");
        let result = neighbor_client.get(&oid!(1, 3, 6, 1, 2, 1, 1, 1, 0)).await;

        match result {
            Ok(data) => println!("First node: {}", data.value),
            Err(error) => panic!("{}", error),
        }

        snmp_walk(&neighbor_client).await;

        sim_port += 1;
    }
}
