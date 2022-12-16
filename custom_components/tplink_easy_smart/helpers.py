"""Helpful common functions."""

from homeassistant.helpers.entity import generate_entity_id as hass_generate_id

from .update_coordinator import TpLinkDataUpdateCoordinator


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
