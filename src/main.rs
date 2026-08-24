mod cli;

use clap::Parser;
use cli::{Cli, Commands};

use oxian::{discovery, models::DiscoveryResult};

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    let cli = Cli::parse();

    match cli.commands {
        Commands::Scan { ip, cidr } => {
            let result = discovery::scan(ip, cidr).await?;
            print_discovery_result(&result)
        }
    }

    Ok(())
}

fn print_discovery_result(result: &DiscoveryResult) {
    println!("Devices: {}", result.devices.len());
    println!("Links: {}", result.links.len());
    println!(
        "Unresolved neighbors: {}",
        result.unresolved_neighbors.len()
    );
    println!();

    for device in &result.devices {
        let name = device.hostname.as_deref().unwrap_or("-");
        let ip = device
            .ip
            .map(|ip| ip.to_string())
            .unwrap_or_else(|| "-".to_string());
        let vendor = match device.vendor {
            oxian::models::Vendor::Cisco => "Cisco",
            oxian::models::Vendor::MikroTik => "MikroTik",
            oxian::models::Vendor::Juniper => "Juniper",
            oxian::models::Vendor::Unknown => "Unknown",
        };

        println!("{} ({}) [{}]", name, ip, vendor);

        let device_links = result.links.iter().filter(|l| {
            (device.ip.is_some() && l.source_ip == device.ip)
                || (device.chassis_id.is_some() && l.source_chassis_id == device.chassis_id)
        });

        for link in device_links {
            let local_if = link.source_interface.as_deref().unwrap_or("-");
            let target_name = link.target_hostname.as_deref().or_else(|| {
                result
                    .devices
                    .iter()
                    .find(|d| d.ip.is_some() && d.ip == link.target_ip)
                    .and_then(|d| d.hostname.as_deref())
            });

            let target_display = match target_name {
                Some(name) => name.to_string(),
                None => link
                    .target_ip
                    .map(|ip| ip.to_string())
                    .unwrap_or_else(|| "-".to_string()),
            };

            let target_port = if link.target_port_id.is_empty() {
                "-"
            } else {
                &link.target_port_id
            };

            println!("  {} -> {}:{}", local_if, target_display, target_port);
        }

        println!();
    }
}
