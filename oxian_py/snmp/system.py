from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from . import oid
from .client import SnmpClient


@dataclass
class SystemInfo:
    hostname: Optional[str] = None
    description: Optional[str] = None
    object_id: Optional[str] = None


async def get_device_info(client: SnmpClient) -> SystemInfo:
    sys_name = await client.get(oid.sys_name())
    sys_descr = await client.get(oid.sys_descr())
    sys_object_id = await client.get(oid.sys_object_id())

    hostname = str(sys_name).strip() if sys_name is not None else None
    description = str(sys_descr).strip() if sys_descr is not None else None
    object_id = str(sys_object_id).strip() if sys_object_id is not None else None

    return SystemInfo(
        hostname=hostname,
        description=description,
        object_id=object_id,
    )
