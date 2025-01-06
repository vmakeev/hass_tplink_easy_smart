"""TP-Link api."""

import logging
from typing import Tuple

from .classes import (
    PoeClass,
    PoePowerLimit,
    PoePowerStatus,
    PoePriority,
    PoeState,
    PortPoeState,
    PortSpeed,
    PortState,
    TpLinkSystemInfo,
    PortStatistics,
)
from .const import (
    FEATURE_POE,
    FEATURE_STATS,
    URL_DEVICE_INFO,
    URL_POE_PORT_SETTINGS_SET,
    URL_POE_SETTINGS_GET,
    URL_POE_SETTINGS_SET,
    URL_PORT_SETTINGS_SET,
    URL_PORTS_SETTINGS_GET,
    URL_PORT_STATISTICS_GET,
)
from .coreapi import TpLinkWebApi, VariableType
from .utils import TpLinkFeaturesDetector

_LOGGER = logging.getLogger(__name__)

_POE_PRIORITIES_SET_MAP: dict[PoePriority, int] = {
    PoePriority.HIGH: 1,
    PoePriority.MIDDLE: 2,
    PoePriority.LOW: 3,
}

_POE_POWER_LIMITS_SET_MAP: dict[PoePowerLimit, Tuple[int, str | None]] = {
    PoePowerLimit.AUTO: (1, None),
    PoePowerLimit.CLASS_1: (2, "(4w)"),
    PoePowerLimit.CLASS_2: (3, "(7w)"),
    PoePowerLimit.CLASS_3: (4, "(15.4w)"),
    PoePowerLimit.CLASS_4: (5, "(30w)"),
}


# ---------------------------
#   ActionError
# ---------------------------
class ActionError(Exception):
    def __init__(self, message: str):
        """Initialize."""
        super().__init__(message)
        self._message = message

    def __str__(self, *args, **kwargs) -> str:
        """Return str(self)."""
        return f"{self._message}"

    def __repr__(self) -> str:
        """Return repr(self)."""
        return self.__str__()


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
        self._is_features_updated = False
        self._features = TpLinkFeaturesDetector(self._core_api)
        _LOGGER.debug("New instance of TpLinkApi created")

    async def _ensure_features_updated(self):
        if not self._is_features_updated:
            _LOGGER.debug("Updating available features")
            await self._features.update()
            self._is_features_updated = True
            _LOGGER.debug("Available features updated")

    async def is_feature_available(self, feature: str) -> bool:
        """Return true if specified feature is known and available."""
        await self._ensure_features_updated()
        return self._features.is_available(feature)

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
            URL_DEVICE_INFO, "info_ds", VariableType.Dict
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
            URL_PORTS_SETTINGS_GET,
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

    async def get_port_statistics(self) -> list[PortStatistics]:
        """Return the port states."""
        if not await self.is_feature_available(FEATURE_STATS):
            return []
        data = await self._core_api.get_variables(
            URL_PORT_STATISTICS_GET,
            [
                ("all_info", VariableType.Dict),
                ("max_port_num", VariableType.Int),
            ],
        )

        result: list[PortStatistics] = []

        all_info = data.get("all_info")
        if not all_info:
            return result

        max_port_num = data.get("max_port_num")
        if not max_port_num:
            return result

        pkts = all_info.get("pkts")
        enabled_flags = all_info.get("state")
        k = 0
        for number in range(1, max_port_num + 1):
            if k + 3 > len(pkts):
                break
            state = PortStatistics(
                number=number,
                enabled=enabled_flags[number - 1] == 1,
                tx_good_pkts=pkts[k + 0],
                tx_bad_pkts=pkts[k + 1],
                rx_good_pkts=pkts[k + 2],
                rx_bad_pkts=pkts[k + 3],
            )
            k += 4
            result.append(state)

        return result

    async def get_port_poe_states(self) -> list[PortPoeState]:
        """Return the port states."""
        if not await self.is_feature_available(FEATURE_POE):
            return []

        data = await self._core_api.get_variables(
            URL_POE_SETTINGS_GET,
            [
                ("portConfig", VariableType.Dict),
                ("poe_port_num", VariableType.Int),
            ],
        )

        result: list[PortPoeState] = []

        port_config = data.get("portConfig")
        if not port_config:
            _LOGGER.debug("No portConfig found, returning")
            return result

        max_port_num = data.get("poe_port_num")
        if not max_port_num:
            _LOGGER.debug("No poe_port_num found, returning")
            return result

        state_flags = port_config.get("state")
        priority_flags = port_config.get("priority")
        powerlimit_flags = port_config.get("powerlimit")
        powers = port_config.get("power")
        currents = port_config.get("current")
        voltages = port_config.get("voltage")
        pdclass_flags = port_config.get("pdclass")
        powerstatus_flags = port_config.get("powerstatus")

        for number in range(1, max_port_num + 1):
            state = PortPoeState(
                number=number,
                enabled=state_flags[number - 1] == 1,
                priority=PoePriority(priority_flags[number - 1]),
                current=currents[number - 1],
                voltage=voltages[number - 1] / 10,
                power_limit=PoePowerLimit.try_parse(powerlimit_flags[number - 1])
                or powerlimit_flags[number - 1] / 10,
                power_status=PoePowerStatus(powerstatus_flags[number - 1]),
                pd_class=PoeClass.try_parse(pdclass_flags[number - 1]),
                power=powers[number - 1] / 10,
            )
            result.append(state)

        return result

    async def get_poe_state(self) -> PoeState | None:
        """Return the port states."""
        if not await self.is_feature_available(FEATURE_POE):
            return None

        _LOGGER.debug("Begin fetching POE states")

        poe_config = await self._core_api.get_variable(
            URL_POE_SETTINGS_GET, "globalConfig", VariableType.Dict
        )
        if not poe_config:
            _LOGGER.debug("No globalConfig found, returning")
            return None

        return PoeState(
            power_limit=poe_config.get("system_power_limit", 0) / 10,
            power_remain=poe_config.get("system_power_remain", 0) / 10,
            power_limit_min=poe_config.get("system_power_limit_min", 0) / 10,
            power_limit_max=poe_config.get("system_power_limit_max", 0) / 10,
            power_consumption=poe_config.get("system_power_consumption", 0) / 10,
        )

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
        await self._core_api.get(URL_PORT_SETTINGS_SET, query=query)

    async def set_poe_limit(self, limit: float) -> None:
        """Change poe limit."""
        if not await self.is_feature_available(FEATURE_POE):
            raise ActionError("POE feature is not supported by device")

        current_state = await self.get_poe_state()
        if not current_state:
            raise ActionError("Can not get actual PoE state")

        if limit < current_state.power_limit_min:
            raise ActionError(
                f"PoE limit should be greater than or equal to {current_state.power_limit_min}"
            )
        if limit > current_state.power_limit_max:
            raise ActionError(
                f"PoE limit should be less than or equal to {current_state.power_limit_max}"
            )

        data = {
            "name_powerlimit": limit,
            "name_powerconsumption": current_state.power_consumption,
            "name_powerremain": current_state.power_remain,
            "applay": "Apply",
        }
        result = await self._core_api.post(URL_POE_SETTINGS_SET, data)
        _LOGGER.debug("POE_SET_RESULT: %s", result)

    async def set_port_poe_settings(
        self,
        port_number: int,
        enabled: bool,
        priority: PoePriority,
        power_limit: PoePowerLimit | float,
    ) -> None:
        if not await self.is_feature_available(FEATURE_POE):
            raise ActionError("POE feature is not supported by device")
        """Change port poe settings."""
        if port_number < 1:
            raise ActionError("Port number should be greater than or equals to 1")

        poe_ports_count = await self._core_api.get_variable(
            URL_POE_SETTINGS_GET, "poe_port_num", VariableType.Int
        )
        if not poe_ports_count:
            raise ActionError("Can not get PoE ports count")

        if port_number > poe_ports_count:
            raise ActionError(
                f"Port number should be less than or equals to {poe_ports_count}"
            )

        pstate = 2 if enabled else 1

        ppriority = _POE_PRIORITIES_SET_MAP.get(priority)
        if not ppriority:
            raise ActionError("Invalid PoePriority specified")

        if isinstance(power_limit, PoePowerLimit):
            ppowerlimit, ppowerlimit2 = _POE_POWER_LIMITS_SET_MAP.get(power_limit)
            if not ppowerlimit:
                raise ActionError("Invalid PoePowerLimit specified")
        elif isinstance(power_limit, float):
            if 0.1 <= power_limit <= 30.0:  # hardcoded in Tp-Link javascript
                ppowerlimit = 6
                ppowerlimit2 = power_limit
            else:
                raise ActionError("Power limit must be in range of 0.1-30.0")
        else:
            raise ActionError("Invalid power_limit specified")

        data = {
            "name_pstate": pstate,
            "name_ppriority": ppriority,
            "name_ppowerlimit": ppowerlimit,
            "name_ppowerlimit2": ppowerlimit2,
            f"sel_{port_number}": 1,
            "applay": "Apply",
        }
        result = await self._core_api.post(URL_POE_PORT_SETTINGS_SET, data)
        _LOGGER.debug("POE_PORT_SETTINGS_SET_RESULT: %s", result)
