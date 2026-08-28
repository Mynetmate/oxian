from __future__ import annotations

import ipaddress
from ipaddress import IPv4Address, IPv6Address
from typing import Any

from pysnmp.hlapi.v1arch.asyncio import ObjectIdentity, ObjectType, Slim

from . import oid



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
            val = var_binds[0][1]
            if type(val).__name__ in ("EndOfMibView", "NoSuchObject", "NoSuchInstance"):
                return None
            return val
        except Exception:
            return None

    async def walk(self, oid_str: str) -> list[tuple[tuple[int, ...], Any]]:
        """Perform SNMP NEXT walk starting from an OID prefix with infinite loop prevention."""
        target_prefix = tuple(int(x) for x in oid_str.strip(".").split(".") if x)
        slim = self._get_slim()
        current_oid = oid_str
        last_parts: tuple[int, ...] = ()
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

                # Check for PySNMP sentinel types indicating end of data
                if type(val).__name__ in ("EndOfMibView", "NoSuchObject", "NoSuchInstance"):
                    return results

                oid_parts = tuple(int(x) for x in str(oid_obj).strip(".").split(".") if x)

                # Prevent infinite loops: must strictly advance in MIB tree
                if last_parts and oid_parts <= last_parts:
                    return results

                # Check if still within prefix
                if len(oid_parts) < len(target_prefix) or oid_parts[: len(target_prefix)] != target_prefix:
                    return results

                results.append((oid_parts, val))
                last_parts = oid_parts
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

    async def walk_lldp_man_addr(self) -> dict[tuple[int, int, int], str]:
        """Walk lldpRemManAddrTable and extract remote management IP."""
        raw = await self.walk(oid.lldp_rem_man_addr_table())
        result: dict[tuple[int, int, int], str] = {}

        for parts, val in raw:
            # Format A: Cisco / Standard OID encoded suffix (length >= 16)
            if len(parts) >= 16:
                time_mark = parts[11]
                local_port = parts[12]
                rem_index = parts[13]
                subtype = parts[14]
                length = parts[15]
                addr_parts = parts[16 : 16 + length]
                if subtype == 1 and len(addr_parts) == 4:
                    result[(time_mark, local_port, rem_index)] = f"{addr_parts[0]}.{addr_parts[1]}.{addr_parts[2]}.{addr_parts[3]}"
                elif subtype == 2 and len(addr_parts) == 16:
                    try:
                        result[(time_mark, local_port, rem_index)] = str(ipaddress.IPv6Address(bytes(addr_parts)))
                    except Exception:
                        pass
            # Format B: MikroTik / Direct value format (column .2 with 3-part suffix)
            elif len(parts) >= 14 and val is not None:
                time_mark = parts[11]
                local_port = parts[12]
                rem_index = parts[13]
                val_str = str(val).strip()
                try:
                    ip_obj = ipaddress.ip_address(val_str)
                    result[(time_mark, local_port, rem_index)] = str(ip_obj)
                except ValueError:
                    pass
        return result


    async def walk_cdp_column(self, oid_str: str) -> dict[tuple[int, int], Any]:

        """Walk a CDP table column indexed by (ifIndex, entryIndex)."""
        raw = await self.walk(oid_str)
        column: dict[tuple[int, int], Any] = {}
        for parts, val in raw:
            if len(parts) >= 2:
                column[(parts[-2], parts[-1])] = val
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
