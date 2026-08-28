from __future__ import annotations

from enum import Enum
from typing import Optional, Union
from pydantic import BaseModel, ConfigDict


class InterfaceStatus(str, Enum):
    Up = "Up"
    Down = "Down"
    Testing = "Testing"
    Unknown = "Unknown"

    @classmethod
    def from_u32(cls, value: int) -> Union[InterfaceStatus, str]:
        if value == 1:
            return cls.Up
        elif value == 2:
            return cls.Down
        elif value == 3:
            return cls.Testing
        else:
            return f"Unknown({value})"

    @classmethod
    def from_int(cls, value: int) -> Union[InterfaceStatus, str]:
        return cls.from_u32(value)


class Interface(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, use_enum_values=True)

    index: int
    description: Optional[str] = None
    mac_address: Optional[str] = None
    admin_status: Optional[Union[InterfaceStatus, str]] = None
    oper_status: Optional[Union[InterfaceStatus, str]] = None
