"""TP-Link Easy Smart integration."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation

from .const import DATA_KEY_COORDINATOR, DOMAIN, PLATFORMS
from .update_coordinator import TpLinkDataUpdateCoordinator

CONFIG_SCHEMA = config_validation.removed(DOMAIN, raise_if_present=False)


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

    hass.config_entries.async_setup_platforms(config_entry, PLATFORMS)
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
        coordinator = (
            hass.data[DOMAIN].get(config_entry.entry_id, {}).pop(DATA_KEY_COORDINATOR)
        )
        if coordinator and isinstance(coordinator, TpLinkDataUpdateCoordinator):
            coordinator.unload()
    return unload_ok
