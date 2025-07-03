"""Support for services."""

from dataclasses import dataclass
import logging
from typing import Final

import voluptuous as vol

from enum import StrEnum
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError, ServiceNotFound
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.service import verify_domain_control

from .client.classes import PoePowerLimit, PoePriority
from .const import DATA_KEY_COORDINATOR, DATA_KEY_SERVICES, DOMAIN
from .update_coordinator import TpLinkDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

_FIELD_MAC_ADDRESS: Final = "mac_address"
_FIELD_POWER_LIMIT: Final = "power_limit"
_FIELD_PORT_NUMBER: Final = "port_number"
_FIELD_ENABLED: Final = "enabled"
_FIELD_PRIORITY: Final = "priority"
_FIELD_MANUAL_POWER_LIMIT: Final = "manual_power_limit"

_CV_MAC_ADDR: Final = cv.matches_regex("^([A-Fa-f0-9]{2}\\:){5}[A-Fa-f0-9]{2}$")

_POE_PRIORITY_MAP: dict[str, PoePriority] = {
    "High": PoePriority.HIGH,
    "Middle": PoePriority.MIDDLE,
    "Low": PoePriority.LOW,
}

_POE_POWER_LIMIT_MAP: dict[str, PoePowerLimit | None] = {
    "Auto": PoePowerLimit.AUTO,
    "Class 1": PoePowerLimit.CLASS_1,
    "Class 2": PoePowerLimit.CLASS_2,
    "Class 3": PoePowerLimit.CLASS_3,
    "Class 4": PoePowerLimit.CLASS_4,
    "Manual": None,
}


# ---------------------------
#   ServiceNames
# ---------------------------
class ServiceNames(StrEnum):
    SET_GENERAL_POE_LIMIT = "set_general_poe_limit"
    SET_PORT_POE_SETTINGS = "set_port_poe_settings"


@dataclass
class ServiceDescription:
    name: str
    schema: vol.Schema


SERVICES = [
    ServiceDescription(
        name=ServiceNames.SET_GENERAL_POE_LIMIT,
        schema=vol.Schema(
            {
                vol.Required(_FIELD_MAC_ADDRESS): _CV_MAC_ADDR,
                vol.Required(_FIELD_POWER_LIMIT): vol.All(
                    vol.Any(vol.Coerce(float), vol.Coerce(int)),
                    vol.Range(min=1, max=1000),
                ),
            }
        ),
    ),
    ServiceDescription(
        name=ServiceNames.SET_PORT_POE_SETTINGS,
        schema=vol.Schema(
            {
                vol.Required(_FIELD_MAC_ADDRESS): _CV_MAC_ADDR,
                vol.Required(_FIELD_PORT_NUMBER): vol.All(
                    vol.Coerce(int), vol.Range(min=1)
                ),
                vol.Required(_FIELD_ENABLED): vol.Coerce(bool),
                vol.Required(_FIELD_PRIORITY): vol.In(list(_POE_PRIORITY_MAP.keys())),
                vol.Required(_FIELD_POWER_LIMIT): vol.In(
                    list(_POE_POWER_LIMIT_MAP.keys())
                ),
                vol.Optional(_FIELD_MANUAL_POWER_LIMIT): vol.Any(
                    vol.Coerce(float), vol.Coerce(int)
                ),
            }
        ),
    ),
]


# ---------------------------
#   _find_coordinator
# ---------------------------
def _find_coordinator(
    hass: HomeAssistant, device_mac: str
) -> TpLinkDataUpdateCoordinator | None:
    _LOGGER.debug("Looking for coordinator with address '%s'", device_mac)
    for key, item in hass.data[DOMAIN].items():
        if key == DATA_KEY_SERVICES:
            continue
        coordinator = item.get(DATA_KEY_COORDINATOR)
        if not coordinator or not isinstance(coordinator, TpLinkDataUpdateCoordinator):
            continue
        if coordinator.get_switch_info().mac == device_mac:
            return coordinator
    return None


# ---------------------------
#   _async_set_general_poe_limit
# ---------------------------
async def _async_set_general_poe_limit(hass: HomeAssistant, service: ServiceCall):
    """Service to set general poe limit."""
    device_mac = service.data[_FIELD_MAC_ADDRESS].upper()
    coordinator = _find_coordinator(hass, device_mac)
    if not coordinator:
        raise HomeAssistantError(
            f"Can not find coordinator with mac address '{device_mac}'"
        )
    _LOGGER.debug(
        "Service '%s' called for mac '%s' with name %s",
        service.service,
        device_mac,
        coordinator.name,
    )
    try:
        limit = float(service.data[_FIELD_POWER_LIMIT])
        await coordinator.async_set_poe_limit(limit)
    except Exception as ex:
        raise HomeAssistantError(str(ex))


# ---------------------------
#   _async_set_port_poe_settings
# ---------------------------
async def _async_set_port_poe_settings(hass: HomeAssistant, service: ServiceCall):
    """Service to set port poe settings."""
    device_mac = service.data[_FIELD_MAC_ADDRESS].upper()

    coordinator = _find_coordinator(hass, device_mac)
    if not coordinator:
        raise HomeAssistantError(
            f"Can not find coordinator with mac address '{device_mac}'"
        )

    _LOGGER.debug(
        "Service '%s' called for mac '%s' with name %s",
        service.service,
        device_mac,
        coordinator.name,
    )

    try:
        port_number: int = service.data[_FIELD_PORT_NUMBER]
        enabled: bool = service.data[_FIELD_ENABLED]
        priority: PoePriority = _POE_PRIORITY_MAP[service.data[_FIELD_PRIORITY]]
        power_limit: PoePowerLimit | float = _POE_POWER_LIMIT_MAP[
            service.data[_FIELD_POWER_LIMIT]
        ] or float(service.data[_FIELD_MANUAL_POWER_LIMIT])

        await coordinator.async_set_port_poe_settings(
            port_number, enabled, priority, power_limit
        )
    except Exception as ex:
        raise HomeAssistantError(str(ex))


# ---------------------------
#   _change_instances_count
# ---------------------------
def _change_instances_count(hass: HomeAssistant, delta: int) -> int:
    current_count = hass.data.setdefault(DOMAIN, {}).setdefault(DATA_KEY_SERVICES, 0)
    result = current_count + delta
    hass.data[DOMAIN][DATA_KEY_SERVICES] = result
    return result


async def async_setup_services(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Set up the Huawei Router services."""
    active_instances = _change_instances_count(hass, 1)
    if active_instances > 1:
        _LOGGER.debug(
            "%s active instances has already been registered, skipping",
            active_instances - 1,
        )
        return

    @verify_domain_control(hass, DOMAIN)
    async def async_call_service(service: ServiceCall) -> None:
        service_name = service.service

        if service_name == ServiceNames.SET_GENERAL_POE_LIMIT:
            await _async_set_general_poe_limit(hass, service)

        if service_name == ServiceNames.SET_PORT_POE_SETTINGS:
            await _async_set_port_poe_settings(hass, service)

        else:
            raise ServiceNotFound(DOMAIN, service_name)

    for item in SERVICES:
        hass.services.async_register(
            domain=DOMAIN,
            service=item.name,
            service_func=async_call_service,
            schema=item.schema,
        )


async def async_unload_services(hass: HomeAssistant, config_entry: ConfigEntry):
    """Unload services."""
    active_instances = _change_instances_count(hass, -1)
    if active_instances > 0:
        _LOGGER.debug("%s active instances remaining, skipping", active_instances)
        return

    hass.data[DOMAIN].pop(DATA_KEY_SERVICES)
    for service in SERVICES:
        hass.services.async_remove(domain=DOMAIN, service=service.name)
