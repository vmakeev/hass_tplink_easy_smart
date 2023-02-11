"""Support for binary sensors."""

from dataclasses import dataclass, field
import logging
from typing import Final

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .client.tplink_api import PoePowerStatus, PortSpeed
from .displayed_values import (
    DISPLAYED_POE_CLASSES,
    DISPLAYED_POE_POWER_LIMITS,
    DISPLAYED_POE_POWER_STATUS,
    DISPLAYED_POE_PRIORITY,
    DISPLAYED_PORT_SPEED,
)
from .helpers import (
    generate_entity_id,
    generate_entity_name,
    generate_entity_unique_id,
    get_coordinator,
)
from .update_coordinator import TpLinkDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

_FUNCTION_DISPLAYED_NAME_PORT_STATE_FORMAT: Final = "Port {} state"
_FUNCTION_UID_PORT_STATE_FORMAT: Final = "port_{}_state"

_FUNCTION_DISPLAYED_NAME_PORT_POE_STATE_FORMAT: Final = "Port {} PoE state"
_FUNCTION_UID_PORT_POE_STATE_FORMAT: Final = "port_{}_poe_state"


ENTITY_DOMAIN: Final = "binary_sensor"


# ---------------------------
#   TpLinkBinarySensorEntityDescription
# ---------------------------
@dataclass
class TpLinkBinarySensorEntityDescription(BinarySensorEntityDescription):
    """A class that describes binary sensor entities."""

    function_name: str | None = None
    function_uid: str | None = None
    device_name: str | None = None
    name: str | None = field(init=False)

    def __post_init__(self):
        self.name = generate_entity_name(self.function_name, self.device_name)


# ---------------------------
#   TpLinkPortBinarySensorEntityDescription
# ---------------------------
@dataclass
class TpLinkPortBinarySensorEntityDescription(TpLinkBinarySensorEntityDescription):
    """A class that describes port binary sensor entities."""

    port_number: int | None = None


# ---------------------------
#   async_setup_entry
# ---------------------------
async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors for TP-Link component."""
    coordinator: TpLinkDataUpdateCoordinator = get_coordinator(hass, config_entry)

    sensors = []

    for port_number in range(1, coordinator.ports_count + 1):
        sensors.append(
            TpLinkPortStateBinarySensor(
                coordinator,
                TpLinkPortBinarySensorEntityDescription(
                    key=f"port_{port_number}_info",
                    icon="mdi:ethernet",
                    device_class=BinarySensorDeviceClass.CONNECTIVITY,
                    port_number=port_number,
                    device_name=coordinator.get_switch_info().name,
                    function_uid=_FUNCTION_UID_PORT_STATE_FORMAT.format(port_number),
                    function_name=_FUNCTION_DISPLAYED_NAME_PORT_STATE_FORMAT.format(
                        port_number
                    ),
                ),
            )
        )

    for port_number in range(1, coordinator.ports_poe_count + 1):
        sensors.append(
            TpLinkPortPoeStateBinarySensor(
                coordinator,
                TpLinkPortBinarySensorEntityDescription(
                    key=f"port_{port_number}_poe_info",
                    icon="mdi:lightning-bolt-outline",
                    device_class=BinarySensorDeviceClass.POWER,
                    port_number=port_number,
                    device_name=coordinator.get_switch_info().name,
                    function_uid=_FUNCTION_UID_PORT_POE_STATE_FORMAT.format(
                        port_number
                    ),
                    function_name=_FUNCTION_DISPLAYED_NAME_PORT_POE_STATE_FORMAT.format(
                        port_number
                    ),
                ),
            )
        )

    async_add_entities(sensors)


# ---------------------------
#   TpLinkBinarySensor
# ---------------------------
class TpLinkBinarySensor(
    CoordinatorEntity[TpLinkDataUpdateCoordinator], BinarySensorEntity
):
    entity_description: TpLinkBinarySensorEntityDescription

    def __init__(
        self,
        coordinator: TpLinkDataUpdateCoordinator,
        description: TpLinkBinarySensorEntityDescription,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_device_info = coordinator.get_device_info()
        self._attr_unique_id = generate_entity_unique_id(
            coordinator, description.function_uid
        )
        self._attr_available = True
        self._attr_is_on = None
        self.entity_id = generate_entity_id(
            coordinator, ENTITY_DOMAIN, description.function_name
        )

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._attr_available

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        await super().async_added_to_hass()
        self._handle_coordinator_update()
        _LOGGER.debug("%s added to hass", self.name)


# ---------------------------
#   TpLinkPortStateBinarySensor
# ---------------------------
class TpLinkPortStateBinarySensor(TpLinkBinarySensor):
    entity_description: TpLinkPortBinarySensorEntityDescription

    def __init__(
        self,
        coordinator: TpLinkDataUpdateCoordinator,
        description: TpLinkPortBinarySensorEntityDescription,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator, description)
        self._attr_extra_state_attributes = {}
        self._port_number = description.port_number

    @callback
    def _handle_coordinator_update(self) -> None:
        port_info = self.coordinator.get_port_state(self._port_number)

        if port_info:
            self._attr_available = port_info.enabled

            self._attr_is_on = (
                port_info.enabled and port_info.speed_actual != PortSpeed.LINK_DOWN
            )

            self._attr_extra_state_attributes["number"] = port_info.number
            self._attr_extra_state_attributes["speed"] = DISPLAYED_PORT_SPEED.get(
                port_info.speed_actual
            )
            self._attr_extra_state_attributes[
                "speed_config"
            ] = DISPLAYED_PORT_SPEED.get(port_info.speed_config)
        else:
            self._attr_available = False
            self._attr_is_on = None

        super()._handle_coordinator_update()


# ---------------------------
#   TpLinkPortPoeStateBinarySensor
# ---------------------------
class TpLinkPortPoeStateBinarySensor(TpLinkBinarySensor):
    entity_description: TpLinkPortBinarySensorEntityDescription

    def __init__(
        self,
        coordinator: TpLinkDataUpdateCoordinator,
        description: TpLinkPortBinarySensorEntityDescription,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator, description)
        self._attr_extra_state_attributes = {}
        self._port_number = description.port_number

    @callback
    def _handle_coordinator_update(self) -> None:
        port_poe_info = self.coordinator.get_port_poe_state(self._port_number)

        if port_poe_info:
            self._attr_available = port_poe_info.enabled

            self._attr_is_on = (
                port_poe_info.enabled
                and port_poe_info.power_status != PoePowerStatus.OFF
            )

            self._attr_extra_state_attributes["priority"] = DISPLAYED_POE_PRIORITY.get(
                port_poe_info.priority
            )
            self._attr_extra_state_attributes[
                "power_limit"
            ] = DISPLAYED_POE_POWER_LIMITS.get(
                port_poe_info.power_limit, port_poe_info.power_limit
            )
            self._attr_extra_state_attributes["power_w"] = port_poe_info.power
            self._attr_extra_state_attributes["current_ma"] = port_poe_info.current
            self._attr_extra_state_attributes["voltage_v"] = port_poe_info.voltage
            self._attr_extra_state_attributes["pd_class"] = DISPLAYED_POE_CLASSES.get(
                port_poe_info.pd_class
            )
            self._attr_extra_state_attributes[
                "power_status"
            ] = DISPLAYED_POE_POWER_STATUS.get(port_poe_info.power_status)
        else:
            self._attr_available = False
            self._attr_is_on = None

        super()._handle_coordinator_update()
