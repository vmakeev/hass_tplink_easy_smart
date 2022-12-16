"""TP-Link api."""

import logging
from typing import Final

from .classes import PortSpeed, PortState, TpLinkSystemInfo
from .coreapi import TpLinkWebApi, VariableType

_LOGGER = logging.getLogger(__name__)


_URL_DEVICE_INFO: Final = "SystemInfoRpm.htm"
_URL_PORTS_SETTINGS_GET: Final = "PortSettingRpm.htm"
_URL_PORT_SETTINGS_SET: Final = "port_setting.cgi"


# ---------------------------
#   TpLinkApi
# ---------------------------
class TpLinkApi:
    def __init__(
        self,
        host: str,
        port: int,
        use_ssl: bool,
        user: str,
        password: str,
        verify_ssl: bool,
    ) -> None:
        """Initialize."""
        self._core_api = TpLinkWebApi(host, port, use_ssl, user, password, verify_ssl)
        _LOGGER.debug("New instance of TpLinkApi created")

    async def authenticate(self) -> None:
        """Perform authentication."""
        await self._core_api.authenticate()

    async def disconnect(self) -> None:
        """Disconnect from api."""
        await self._core_api.disconnect()

    @property
    def device_url(self) -> str:
        """URL address of the device."""
        return self._core_api.device_url

    async def get_device_info(self) -> TpLinkSystemInfo:
        """Return the device information."""
        data = await self._core_api.get_variable(
            _URL_DEVICE_INFO, "info_ds", VariableType.Dict
        )

        def get_value(key: str) -> str | None:
            if data is None:
                return None
            array = data.get(key, [])
            if len(array) != 1:
                return None
            return array[0]

        return TpLinkSystemInfo(
            name=get_value("descriStr"),
            mac=get_value("macStr"),
            ip=get_value("ipStr"),
            netmask=get_value("netmaskStr"),
            gateway=get_value("gatewayStr"),
            firmware=get_value("firmwareStr"),
            hardware=get_value("hardwareStr"),
        )

    async def get_port_states(self) -> list[PortState]:
        """Return the port states."""
        data = await self._core_api.get_variables(
            _URL_PORTS_SETTINGS_GET,
            [
                ("all_info", VariableType.Dict),
                ("max_port_num", VariableType.Int),
            ],
        )

        result: list[PortState] = []

        all_info = data.get("all_info")
        if not all_info:
            return result

        max_port_num = data.get("max_port_num")
        if not max_port_num:
            return result

        enabled_flags = all_info.get("state")
        speeds_config = all_info.get("spd_cfg")
        speeds_actual = all_info.get("spd_act")
        fc_config_flags = all_info.get("fc_cfg")
        fc_actual_flags = all_info.get("fc_act")

        for number in range(1, max_port_num + 1):
            state = PortState(
                number=number,
                speed_config=PortSpeed(speeds_config[number - 1]),
                speed_actual=PortSpeed(speeds_actual[number - 1]),
                enabled=enabled_flags[number - 1] == 1,
                flow_control_config=fc_config_flags[number - 1] == 1,
                flow_control_actual=fc_actual_flags[number - 1] == 1,
            )
            result.append(state)

        return result

    async def set_port_state(
        self,
        number: int,
        enabled: bool,
        speed_config: PortSpeed,
        flow_control_config: bool,
    ) -> None:
        """Change port state."""
        query: str = (
            f"portid={number}&"
            f"state={1 if enabled else 0}&"
            f"speed={speed_config.value}&"
            f"flowcontrol={1 if flow_control_config else 0}&"
            f"apply=Apply"
        )
        await self._core_api.get(_URL_PORT_SETTINGS_SET, query=query)
