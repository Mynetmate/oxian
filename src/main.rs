use std::time::Duration;

use async_snmp::{Auth, Client, oid};
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

            snmp_walk(&client).await;
        }
        Commands::Scan { ip_cidr } => snmp_scan(ip_cidr).await,
    }
}

async fn snmp_scan(ip_cidr: Ipv4Net) {
    todo!("scan all network {}", ip_cidr);
}

async fn snmp_walk(snmp_client: &Client) {
    // get a system OBJECT-CLASS
    // oid!(1, 3, 6, 1, 2, 1, 1)
    let mut walk = snmp_client
        .walk(oid!(1, 3, 6, 1, 2, 1, 1))
        .expect("cannot walk");

    while let Some(result) = walk.next().await {
        let vb = result.expect("cannot get vb");
        println!("{}: {:?}", vb.oid, vb.value)
    }
}
