from typing import Final

from .client.classes import (
    PoeClass,
    PoePowerLimit,
    PoePowerStatus,
    PoePriority,
    PortSpeed,
)

DISPLAYED_PORT_SPEED: Final = {
    PortSpeed.AUTO: "Auto",
    PortSpeed.LINK_DOWN: "Link Down",
    PortSpeed.FULL_10M: "10MF",
    PortSpeed.FULL_100M: "100MF",
    PortSpeed.FULL_1000M: "1000MF",
    PortSpeed.HALF_10M: "10MH",
    PortSpeed.HALF_100M: "100MH",
}

DISPLAYED_POE_PRIORITY: Final = {
    PoePriority.HIGH: "High",
    PoePriority.MIDDLE: "Middle",
    PoePriority.LOW: "Low",
}

DISPLAYED_POE_POWER_LIMITS: Final = {
    PoePowerLimit.AUTO: "Auto",
    PoePowerLimit.CLASS_1: "Class 1",
    PoePowerLimit.CLASS_2: "Class 2",
    PoePowerLimit.CLASS_3: "Class 3",
    PoePowerLimit.CLASS_4: "Class 4",
}

DISPLAYED_POE_CLASSES: Final = {
    PoeClass.CLASS_0: "Class 0",
    PoeClass.CLASS_1: "Class 2",
    PoeClass.CLASS_2: "Class 3",
    PoeClass.CLASS_3: "Class 3",
    PoeClass.CLASS_4: "Class 4",
}

DISPLAYED_POE_POWER_STATUS: Final = {
    PoePowerStatus.OFF: "Off",
    PoePowerStatus.TURNING_ON: "Turning on",
    PoePowerStatus.ON: "On",
    PoePowerStatus.OVELOAD: "Overload",
    PoePowerStatus.SHORT: "Short",
    PoePowerStatus.NOSTANDARD_PD: "Non-standard PD",
    PoePowerStatus.VOLTAGE_HIGH: "Voltage high",
    PoePowerStatus.VOLTAGE_LOW: "Voltage low",
    PoePowerStatus.HARDWARE_FAULT: "Hardware fault",
    PoePowerStatus.OVERTEMPERATURE: "Overtemperature",
}
