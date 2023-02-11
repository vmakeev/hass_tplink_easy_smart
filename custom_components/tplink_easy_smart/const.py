"""TP-Link shared constants."""

from typing import Final

from homeassistant.const import Platform

DOMAIN: Final = "tplink_easy_smart"

DATA_KEY_COORDINATOR: Final = "coordinator"
DATA_KEY_SERVICES: Final = "services_count"

DEFAULT_HOST: Final = "192.168.0.1"
DEFAULT_USER: Final = "admin"
DEFAULT_PORT: Final = 80
DEFAULT_SSL: Final = False
DEFAULT_PASS: Final = ""
DEFAULT_NAME: Final = "TP-Link Switch"
DEFAULT_VERIFY_SSL: Final = False
DEFAULT_SCAN_INTERVAL: Final = 30
DEFAULT_PORT_STATE_SWITCHES: Final = False
DEFAULT_POE_STATE_SWITCHES: Final = False

OPT_PORT_STATE_SWITCHES: Final = "port_state_switches"
OPT_POE_STATE_SWITCHES: Final = "poe_state_switches"

ATTR_MANUFACTURER: Final = "TP-Link"
PLATFORMS: Final = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
]
