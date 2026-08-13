# Oxian - Automatic Network Device Discovery

A CLI tool for scanning SNMP agents across any network.

### Usage

```sh
oxian scan <IP> # e.g., 192.168.1.1
```

# Dependencies
- [Async runtime](https://crates.io/crates/tokio)
- [SNMP client](https://crates.io/crates/async-snmp)
- [Command Line Argument Parser](https://crates.io/crates/clap)
- [IPv4 and IPv6 methods](https://crates.io/crates/ipnet)

# Testing Environment
- https://github.com/lextudio/snmpsim
- https://github.com/srl-labs/containerlab