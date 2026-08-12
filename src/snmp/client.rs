use std::{net::IpAddr, time::Duration};

use async_snmp::{Auth, Client};

pub async fn connect(ip: IpAddr) -> anyhow::Result<Client> {
    let client = Client::builder((ip.to_string(), 161), Auth::v2c("public"))
        .timeout(Duration::from_secs(5))
        .connect()
        .await?;

    Ok(client)
}
