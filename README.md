# Oxian — Network Device and Topology Discovery

Oxian discovers network devices and topology through SNMP, LLDP, CDP, and
route information. The repository contains two native implementations that
share the same domain:

- `oxian_core` and `oxian_cli`: the Rust library and command-line scanner.
- `oxian_py`: the asynchronous Python package for FastAPI services, workers,
  and other Python applications.

The Python package replaces the former PyO3 binding. It does not require a
Rust extension at runtime.

## Rust CLI

Build and run the CLI from the repository root:

```sh
cargo run -p oxian_cli -- scan 192.168.1.1
```

Optionally supply a subnet prefix for scanning:

```sh
cargo run -p oxian_cli -- scan 192.168.1.1 --cidr 24
```

## Python API

Install the Python package in editable mode:

```sh
pip install -e .
```

Discover a topology asynchronously:

```python
import asyncio

from oxian_py import discover


async def main() -> None:
    topology = await discover("192.168.1.1", community="public", timeout=2)
    print(topology["devices"])
    print(topology["links"])


asyncio.run(main())
```

For streaming discovery events, use `oxian_py.discover_stream`.

## Testing

Run the Rust workspace tests:

```sh
cargo test --workspace
```

Run the Python test suite:

```sh
uv run --extra dev pytest
```

## Test environments

- [snmpsim](https://github.com/lextudio/snmpsim)
- [containerlab](https://github.com/srl-labs/containerlab)
