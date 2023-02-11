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
#   PoePriority
# ---------------------------
class PoePriority(IntEnum):
    HIGH = 0
    MIDDLE = 1
    LOW = 2

    @classmethod
    def try_parse(cls, value):
        if value in cls._value2member_map_:
            return PoePriority(value)
        return None


# ---------------------------
#   PoePowerLimit
# ---------------------------
class PoePowerLimit(IntEnum):
    AUTO = 330
    CLASS_1 = 40
    CLASS_2 = 70
    CLASS_3 = 154
    CLASS_4 = 300

    @classmethod
    def try_parse(cls, value):
        if value in cls._value2member_map_:
            return PoePowerLimit(value)
        return None


# ---------------------------
#   PoeClass
# ---------------------------
class PoeClass(IntEnum):
    CLASS_1 = 40
    CLASS_2 = 70
    CLASS_3 = 154
    CLASS_4 = 300
    CLASS_0 = 330

    @classmethod
    def try_parse(cls, value):
        if value in cls._value2member_map_:
            return PoeClass(value)
        return None


# ---------------------------
#   PoePowerStatus
# ---------------------------
class PoePowerStatus(IntEnum):
    OFF = 0
    TURNING_ON = 1
    ON = 2
    OVELOAD = 3
    SHORT = 4
    NOSTANDARD_PD = 5
    VOLTAGE_HIGH = 6
    VOLTAGE_LOW = 7
    HARDWARE_FAULT = 8
    OVERTEMPERATURE = 9

    @classmethod
    def try_parse(cls, value):
        if value in cls._value2member_map_:
            return PoePowerStatus(value)
        return None


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


# ---------------------------
#   PortPoeState
# ---------------------------
@dataclass
class PortPoeState:
    number: int
    enabled: bool
    priority: PoePriority
    power_limit: PoePowerLimit | float
    power: float
    current: float
    voltage: float
    pd_class: PoeClass | None
    power_status: PoePowerStatus


# ---------------------------
#   PoeState
# ---------------------------
@dataclass
class PoeState:
    power_limit: float
    power_limit_min: float
    power_limit_max: float
    power_consumption: float
    power_remain: float
