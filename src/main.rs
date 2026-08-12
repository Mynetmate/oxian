mod cli;

use clap::Parser;
use cli::{Cli, Commands};

use oxian::discovery;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    let cli = Cli::parse();

    match cli.commands {
        Commands::Scan { ip, cidr } => {
            let result = discovery::scan(ip, cidr).await?;

            println!("{:?}", result)
        }
    }

    Ok(())
}
