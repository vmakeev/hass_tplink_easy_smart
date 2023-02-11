"""Helpful common functions."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import generate_entity_id as hass_generate_id

from .const import DATA_KEY_COORDINATOR, DOMAIN
from .update_coordinator import TpLinkDataUpdateCoordinator


class ConfigurationError(Exception):
    def __init__(self, message: str) -> None:
        """Initialize."""
        super().__init__(message)
        self._message = message

    def __str__(self, *args, **kwargs) -> str:
        """Return str(self)."""
        return self._message


# ---------------------------
#   generate_entity_name
# ---------------------------
def generate_entity_name(function_displayed_name: str, device_name: str) -> str:
    return f"{device_name} {function_displayed_name}"


# ---------------------------
#   generate_entity_id
# ---------------------------
def generate_entity_id(
    coordinator: TpLinkDataUpdateCoordinator,
    entity_domain: str,
    function_displayed_name: str,
) -> str:
    preferred_id = f"{coordinator.name} {function_displayed_name}"
    return hass_generate_id(entity_domain + ".{}", preferred_id, hass=coordinator.hass)


# ---------------------------
#   generate_entity_unique_id
# ---------------------------
def generate_entity_unique_id(
    coordinator: TpLinkDataUpdateCoordinator, function_uid: str
) -> str:
    prefix = coordinator.unique_id
    suffix = coordinator.get_switch_info().mac
    return f"{prefix}_{function_uid}_{suffix.lower()}"


# ---------------------------
#   get_coordinator
# ---------------------------
def get_coordinator(
    hass: HomeAssistant, config_entry: ConfigEntry
) -> TpLinkDataUpdateCoordinator:
    result = (
        hass.data.get(DOMAIN, {})
        .get(config_entry.entry_id, {})
        .get(DATA_KEY_COORDINATOR)
    )
    if not result:
        raise ConfigurationError(f"Coordinator not found at {config_entry.entry_id}")
    return result


# ---------------------------
#   pop_coordinator
# ---------------------------
def pop_coordinator(
    hass: HomeAssistant, config_entry: ConfigEntry
) -> TpLinkDataUpdateCoordinator | None:
    data = hass.data.get(DOMAIN, {}).get(config_entry.entry_id, {})
    if DATA_KEY_COORDINATOR in data:
        return data.pop(DATA_KEY_COORDINATOR)
    return None


# ---------------------------
#   set_coordinator
# ---------------------------
def set_coordinator(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    coordinator: TpLinkDataUpdateCoordinator,
) -> None:
    hass.data.setdefault(DOMAIN, {}).setdefault(config_entry.entry_id, {})[
        DATA_KEY_COORDINATOR
    ] = coordinator
