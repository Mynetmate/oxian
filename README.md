# Oxian (oxian_py) - Network Device & Topology Discovery

Asynchronous network device and topology discovery engine in Python via SNMP and LLDP. Designed as a standalone Python library that can be integrated directly into FastAPI, background workers, or CLI applications.

## Installation

```sh
pip install -e .
```
or as a git submodule in your backend project:
```sh
git submodule add <repo-url> libs/oxian_py
```

## Quick Start

### 1. Python Async API

```python
import asyncio
from oxian_py import scan, discover

async def main():
    # Scan network topology starting from a seed IP
    result = await scan("192.168.1.1", community="public", timeout=2)
    
    print(f"Discovered {len(result.devices)} devices, {len(result.links)} links")
    for device in result.devices:
        print(f"Device: {device.hostname} ({device.ip}) - {device.vendor}")
    
    for link in result.links:
        print(f"Link: {link.source_ip}:{link.source_interface} -> {link.target_ip}:{link.target_port_id}")

    # Or get dictionary directly:
    data = await discover("192.168.1.1")

asyncio.run(main())
```

### 2. Integration in FastAPI Backend

In your FastAPI backend project:

```python
from fastapi import FastAPI
from oxian_py import scan, DiscoveryResult

app = FastAPI(title="Network Automation API")

@app.get("/api/v1/topology/{target_ip}", response_model=DiscoveryResult)
async def get_network_topology(target_ip: str, community: str = "public"):
    # All models are Pydantic v2 compatible
    result = await scan(ip=target_ip, community=community, timeout=2)
    return result
```

## Running Tests

```sh
pytest -v
```