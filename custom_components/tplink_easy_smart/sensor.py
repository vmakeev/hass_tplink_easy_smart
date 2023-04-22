"""Support for additional sensors."""

from dataclasses import dataclass, field
import logging
from typing import Final

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import POWER_WATT
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .client.const import FEATURE_POE

from .helpers import (
    generate_entity_id,
    generate_entity_name,
    generate_entity_unique_id,
    get_coordinator,
)
from .update_coordinator import TpLinkDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

_FUNCTION_DISPLAYED_NAME_NETWORK_INFO: Final = "Network info"
_FUNCTION_UID_NETWORK_INFO: Final = "network_info"

_FUNCTION_DISPLAYED_NAME_POE_INFO: Final = "PoE consumption"
_FUNCTION_UID_POE_INFO: Final = "poe_consumption"

ENTITY_DOMAIN: Final = "sensor"


# ---------------------------
#   TpLinkSensorEntityDescription
# ---------------------------
@dataclass
class TpLinkSensorEntityDescription(SensorEntityDescription):
    """A class that describes sensor entities."""

    function_name: str | None = None
    function_uid: str | None = None
    device_name: str | None = None
    name: str | None = field(init=False)

    def __post_init__(self):
        self.name = generate_entity_name(self.function_name, self.device_name)


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

    sensors = [
        TpLinkNetworkInfoSensor(
            coordinator,
            TpLinkSensorEntityDescription(
                key="network_info",
                icon="mdi:network-pos",
                device_name=coordinator.get_switch_info().name,
                function_uid=_FUNCTION_UID_NETWORK_INFO,
                function_name=_FUNCTION_DISPLAYED_NAME_NETWORK_INFO,
            ),
        ),
    ]

    if await coordinator.is_feature_available(FEATURE_POE):
        sensors.append(
            TpLinkPoeInfoSensor(
                coordinator,
                TpLinkSensorEntityDescription(
                    key="poe_consumption",
                    icon="mdi:lightning-bolt",
                    device_class=SensorDeviceClass.POWER,
                    native_unit_of_measurement=POWER_WATT,
                    state_class=SensorStateClass.MEASUREMENT,
                    device_name=coordinator.get_switch_info().name,
                    function_uid=_FUNCTION_UID_POE_INFO,
                    function_name=_FUNCTION_DISPLAYED_NAME_POE_INFO,
                ),
            )
        )

    async_add_entities(sensors)


# ---------------------------
#   TpLinkSensor
# ---------------------------
class TpLinkSensor(CoordinatorEntity[TpLinkDataUpdateCoordinator], SensorEntity):
    entity_description: TpLinkSensorEntityDescription

    def __init__(
        self,
        coordinator: TpLinkDataUpdateCoordinator,
        description: TpLinkSensorEntityDescription,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_device_info = coordinator.get_device_info()
        self._attr_unique_id = generate_entity_unique_id(
            coordinator, description.function_uid
        )
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
#   TpLinkNetworkInfoSensor
# ---------------------------
class TpLinkNetworkInfoSensor(TpLinkSensor):
    entity_description: TpLinkDataUpdateCoordinator
    _attr_native_value: str | None = None

    def __init__(
        self,
        coordinator: TpLinkDataUpdateCoordinator,
        description: TpLinkSensorEntityDescription,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator, description)
        self._attr_native_value = None
        self._attr_extra_state_attributes = {}

    @callback
    def _handle_coordinator_update(self) -> None:
        system_info = self.coordinator.get_switch_info()
        if system_info:
            self._attr_native_value = system_info.ip
            self._attr_extra_state_attributes["mac"] = system_info.mac
            self._attr_extra_state_attributes["gateway"] = system_info.gateway
            self._attr_extra_state_attributes["netmask"] = system_info.netmask
            self._attr_available = True
        else:
            self._attr_available = False
        super()._handle_coordinator_update()


# ---------------------------
#   TpLinkPoeInfoSensor
# ---------------------------
class TpLinkPoeInfoSensor(TpLinkSensor):
    entity_description: TpLinkDataUpdateCoordinator
    _attr_native_value: float | None = None

    def __init__(
        self,
        coordinator: TpLinkDataUpdateCoordinator,
        description: TpLinkSensorEntityDescription,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator, description)
        self._attr_native_value = None
        self._attr_extra_state_attributes = {}

    @callback
    def _handle_coordinator_update(self) -> None:
        poe_state = self.coordinator.get_poe_state()
        if poe_state:
            self._attr_native_value = poe_state.power_consumption
            self._attr_extra_state_attributes["power_limit_w"] = poe_state.power_limit
            self._attr_extra_state_attributes["power_remain_w"] = poe_state.power_remain
            self._attr_available = True
        else:
            self._attr_available = False
        super()._handle_coordinator_update()
