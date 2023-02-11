"""TP-Link Easy Smart integration."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation

from .const import (
    DATA_KEY_COORDINATOR,
    DEFAULT_POE_STATE_SWITCHES,
    DOMAIN,
    OPT_POE_STATE_SWITCHES,
    PLATFORMS,
)
from .helpers import pop_coordinator, set_coordinator
from .services import async_setup_services, async_unload_services
from .update_coordinator import TpLinkDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = config_validation.removed(DOMAIN, raise_if_present=False)


# ---------------------------
#   async_setup
# ---------------------------
async def async_setup(hass, _config):
    """Set up configured TP-Link Controller."""
    hass.data[DOMAIN] = {}
    return True


# ---------------------------
#   async_setup_entry
# ---------------------------
async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up TP-Link as config entry."""
    coordinator = TpLinkDataUpdateCoordinator(hass, config_entry)
    hass.data.setdefault(DOMAIN, {}).setdefault(config_entry.entry_id, {})[
        DATA_KEY_COORDINATOR
    ] = coordinator

    await coordinator.async_config_entry_first_refresh()

    config_entry.async_on_unload(config_entry.add_update_listener(update_listener))
    config_entry.async_on_unload(coordinator.unload)

    set_coordinator(hass, config_entry, coordinator)

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    await async_setup_services(hass, config_entry)
    return True


# ---------------------------
#   update_listener
# ---------------------------
async def update_listener(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Update listener."""
    await hass.config_entries.async_reload(config_entry.entry_id)


# ---------------------------
#   async_update_entry
# ---------------------------
async def async_update_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options."""
    await hass.config_entries.async_reload(entry.entry_id)


# ---------------------------
#   async_unload_entry
# ---------------------------
async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        config_entry, PLATFORMS
    )
    if unload_ok:
        coordinator = pop_coordinator(hass, config_entry)
        if coordinator and isinstance(coordinator, TpLinkDataUpdateCoordinator):
            coordinator.unload()
    await async_unload_services(hass, config_entry)
    return unload_ok


async def async_migrate_entry(hass, config_entry: ConfigEntry):
    """Migrate old entry."""
    _LOGGER.debug("Migrating from version %s", config_entry.version)

    updated_data = {**config_entry.data}
    updated_options = {**config_entry.options}

    if config_entry.version == 1:
        _LOGGER.debug("Migrating to version 2")
        updated_options[OPT_POE_STATE_SWITCHES] = DEFAULT_POE_STATE_SWITCHES
        config_entry.version = 2

    hass.config_entries.async_update_entry(
        config_entry, data=updated_data, options=updated_options
    )

    _LOGGER.info("Migration to version %s successful", config_entry.version)

    return True
