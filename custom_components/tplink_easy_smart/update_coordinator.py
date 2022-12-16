"""Update coordinator for TP-Link."""
from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_SSL,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .client.classes import TpLinkSystemInfo
from .client.tplink_api import PortSpeed, PortState, TpLinkApi
from .const import ATTR_MANUFACTURER, DOMAIN

_LOGGER = logging.getLogger(__name__)


# ---------------------------
#   TpLinkDataUpdateCoordinator
# ---------------------------
class TpLinkDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize."""
        self._config: ConfigEntry = config_entry

        self._api: TpLinkApi = TpLinkApi(
            host=config_entry.data[CONF_HOST],
            port=config_entry.data[CONF_PORT],
            use_ssl=config_entry.data[CONF_SSL],
            user=config_entry.data[CONF_USERNAME],
            password=config_entry.data[CONF_PASSWORD],
            verify_ssl=config_entry.data[CONF_VERIFY_SSL],
        )
        self._switch_info: TpLinkSystemInfo | None = None
        self._port_states: list[PortState] = []

        super().__init__(
            hass,
            _LOGGER,
            name=config_entry.data[CONF_NAME],
            update_method=self.async_update,
            update_interval=timedelta(seconds=config_entry.data[CONF_SCAN_INTERVAL]),
        )

    @property
    def unique_id(self) -> str:
        """Return the system descriptor."""
        entry = self.config_entry

        if entry.unique_id:
            return entry.unique_id

        return entry.entry_id

    @property
    def cfg_host(self) -> str:
        """Return the host of the device."""
        return self.config_entry.data[CONF_HOST]

    @property
    def ports_count(self) -> int:
        """Return ports count of the device."""
        return len(self._port_states)

    def get_port_state(self, number: int) -> PortState | None:
        """Return the specified port state."""
        if number > self.ports_count or number < 1:
            return None
        return self._port_states[number - 1]

    def get_switch_info(self) -> TpLinkSystemInfo | None:
        """Return the information of the switch."""
        return self._switch_info

    def get_device_info(self) -> DeviceInfo | None:
        """Return the DeviceInfo."""
        switch_info = self.get_switch_info()
        if not switch_info:
            _LOGGER.debug("Device info not found")
            return None

        result = DeviceInfo(
            configuration_url=self._api.device_url,
            identifiers={(DOMAIN, switch_info.mac)},
            manufacturer=ATTR_MANUFACTURER,
            name=switch_info.name,
            hw_version=switch_info.hardware,
            sw_version=switch_info.firmware,
        )
        return result

    def _safe_disconnect(self, api: TpLinkApi) -> None:
        """Disconnect from API."""
        try:
            self.hass.async_add_job(api.disconnect)
        except Exception as ex:
            _LOGGER.warning("Can not schedule disconnect: %s", str(ex))

    async def async_update(self) -> None:
        """Asynchronous update of all data."""
        _LOGGER.debug("Update started")
        await self._update_switch_info()
        await self._update_port_states()
        _LOGGER.debug("Update completed")

    def unload(self) -> None:
        """Unload the coordinator and disconnect from API."""
        self._safe_disconnect(self._api)

    async def _update_switch_info(self):
        self._switch_info = await self._api.get_device_info()

    async def _update_port_states(self):
        try:
            self._port_states = await self._api.get_port_states()
        except Exception as ex:
            _LOGGER.warning("Can not get port states: %s", repr(ex))
            self._port_states = []

    async def set_port_state(
        self,
        number: int,
        enabled: bool,
        speed_config: PortSpeed,
        flow_control_config: bool,
    ) -> None:
        await self._api.set_port_state(
            number, enabled, speed_config, flow_control_config
        )

        index = number - 1
        if len(self._port_states) >= index:
            self._port_states[index].enabled = enabled
            self.async_update_listeners()
