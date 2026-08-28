from __future__ import annotations

from ipaddress import IPv4Address, IPv6Address
from typing import Any

from pysnmp.hlapi.v1arch.asyncio import ObjectIdentity, ObjectType, Slim


class SnmpClient:
    """Async SNMP v2c client using PySNMP v1arch / Slim."""

    def __init__(
        self,
        host: str,
        port: int = 161,
        community: str = "public",
        timeout: int = 2,
        retries: int = 0,
    ) -> None:
        self.host = host
        self.port = port
        self.community = community
        self.timeout = timeout
        self.retries = retries
        self._slim: Slim | None = None

    def _get_slim(self) -> Slim:
        if self._slim is None:
            self._slim = Slim(2)
        return self._slim

    async def get(self, oid_str: str) -> Any | None:
        """Perform SNMP GET query for a specific OID."""
        slim = self._get_slim()
        try:
            err_ind, err_status, _, var_binds = await slim.get(
                self.community,
                self.host,
                self.port,
                ObjectType(ObjectIdentity(oid_str)),
                timeout=self.timeout,
                retries=self.retries,
            )
            if err_ind or err_status or not var_binds:
                return None
            return var_binds[0][1]
        except Exception:
            return None

    async def walk(self, oid_str: str) -> list[tuple[tuple[int, ...], Any]]:
        """Perform SNMP NEXT walk starting from an OID prefix."""
        target_prefix = tuple(int(x) for x in oid_str.strip(".").split(".") if x)
        slim = self._get_slim()
        current_oid = oid_str
        results: list[tuple[tuple[int, ...], Any]] = []

        while True:
            try:
                err_ind, err_status, _, var_binds = await slim.next(
                    self.community,
                    self.host,
                    self.port,
                    ObjectType(ObjectIdentity(current_oid)),
                    timeout=self.timeout,
                    retries=self.retries,
                )
            except Exception:
                break

            if err_ind or err_status or not var_binds:
                break

            found_any = False
            for var_bind in var_binds:
                oid_obj = var_bind[0]
                val = var_bind[1]

                oid_parts = tuple(int(x) for x in str(oid_obj).strip(".").split(".") if x)
                if len(oid_parts) < len(target_prefix) or oid_parts[: len(target_prefix)] != target_prefix:
                    return results

                results.append((oid_parts, val))
                current_oid = ".".join(str(x) for x in oid_parts)
                found_any = True

            if not found_any:
                break

        return results

    async def walk_column(self, oid_str: str) -> dict[int, Any]:
        """Walk a table column indexed by a single integer index."""
        raw = await self.walk(oid_str)
        column: dict[int, Any] = {}
        for parts, val in raw:
            if parts:
                column[parts[-1]] = val
        return column

    async def walk_lldp_column(self, oid_str: str) -> dict[tuple[int, int, int], Any]:
        """Walk an LLDP table column indexed by (time_mark, local_port_num, rem_index)."""
        raw = await self.walk(oid_str)
        column: dict[tuple[int, int, int], Any] = {}
        for parts, val in raw:
            if len(parts) >= 3:
                column[(parts[-3], parts[-2], parts[-1])] = val
        return column

    async def walk_raw(self, oid_str: str) -> list[tuple[tuple[int, ...], Any]]:
        """Alias for raw walk."""
        return await self.walk(oid_str)

    def close(self) -> None:
        """Close client connection."""
        if self._slim is not None:
            self._slim.close()
            self._slim = None

    async def __aenter__(self) -> SnmpClient:
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()


async def connect(
    ip: str | IPv4Address | IPv6Address,
    port: int = 161,
    community: str = "public",
    timeout: int = 2,
    retries: int = 0,
) -> SnmpClient:
    """Create and return an SNMP client for the specified target host."""
    host_str = str(ip)
    return SnmpClient(host=host_str, port=port, community=community, timeout=timeout, retries=retries)
