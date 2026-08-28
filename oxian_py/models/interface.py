from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, ConfigDict


class InterfaceStatus(str, Enum):
    """Operational / administrative status of a network interface."""

    Up = "Up"
    Down = "Down"
    Testing = "Testing"
    Unknown = "Unknown"

    @classmethod
    def from_u32(cls, value: int) -> InterfaceStatus | str:
        if value == 1:
            return cls.Up
        elif value == 2:
            return cls.Down
        elif value == 3:
            return cls.Testing
        else:
            return f"Unknown({value})"

    @classmethod
    def from_int(cls, value: int) -> InterfaceStatus | str:
        return cls.from_u32(value)


class Interface(BaseModel):
    """Network device physical/logical interface information."""

    model_config = ConfigDict(arbitrary_types_allowed=True, use_enum_values=True)

    index: int
    description: str | None = None
    mac_address: str | None = None
    admin_status: InterfaceStatus | str | None = None
    oper_status: InterfaceStatus | str | None = None
