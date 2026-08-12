# Oxian - Auto network devices discovery

A cli tool for scaning snmp agent in any network.

### Usage

```sh
oxian scan [IP_CIDR] # 192.168.1.1 or 192.168.1.0/24
```

# Library
- [Async runtime](https://crates.io/crates/tokio)
- [SNMP client](https://crates.io/crates/async-snmp)
- [Command Line Argument Parser](https://crates.io/crates/clap)
- [IPv4 and IPv6 methods](https://crates.io/crates/ipnet)

# Testing Environtment
- https://github.com/lextudio/snmpsim
- https://github.com/srl-labs/containerlab