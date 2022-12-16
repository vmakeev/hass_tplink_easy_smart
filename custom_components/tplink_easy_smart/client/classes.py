"""TP-Link core classes."""

from dataclasses import dataclass
from enum import IntEnum
from typing import TypeAlias

MAC_ADDR: TypeAlias = str


# ---------------------------
#   TpLinkSystemInfo
# ---------------------------
@dataclass()
class TpLinkSystemInfo:
    name: str | None = (None,)
    mac: str | None = (None,)
    ip: str | None = (None,)
    netmask: str | None = (None,)
    gateway: str | None = (None,)
    firmware: str | None = (None,)
    hardware: str | None = None


# ---------------------------
#   PortSpeed
# ---------------------------
class PortSpeed(IntEnum):
    LINK_DOWN = 0
    AUTO = 1
    HALF_10M = 2
    FULL_10M = 3
    HALF_100M = 4
    FULL_100M = 5
    FULL_1000M = 6
    UNKNOWN = 7


# ---------------------------
#   PortState
# ---------------------------
@dataclass
class PortState:
    number: int
    enabled: bool
    flow_control_config: bool
    flow_control_actual: bool
    speed_config: PortSpeed
    speed_actual: PortSpeed
