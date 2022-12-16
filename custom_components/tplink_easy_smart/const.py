"""TP-Link shared constants."""

from typing import Final

from homeassistant.const import Platform

DOMAIN: Final = "tplink_easy_smart"

DEFAULT_HOST: Final = "192.168.0.1"
DEFAULT_USER: Final = "admin"
DEFAULT_PORT: Final = 80
DEFAULT_SSL: Final = False
DEFAULT_PASS: Final = ""
DEFAULT_NAME: Final = "TP-Link Switch"
DEFAULT_VERIFY_SSL: Final = False
DEFAULT_SCAN_INTERVAL: Final = 30

DATA_KEY_COORDINATOR = "coordinator"

ATTR_MANUFACTURER: Final = "TP-Link"
PLATFORMS: Final = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
]
