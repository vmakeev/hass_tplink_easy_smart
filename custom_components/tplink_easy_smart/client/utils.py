import logging
from functools import wraps

from .const import FEATURE_POE, URL_POE_SETTINGS_GET, FEATURE_STATS, URL_PORT_STATISTICS_GET
from .coreapi import (
    ApiCallError,
    TpLinkWebApi,
    VariableType,
    APICALL_ERRCAT_DISCONNECTED,
)

_LOGGER = logging.getLogger(__name__)


# ---------------------------
#   TpLinkFeaturesDetector
# ---------------------------
class TpLinkFeaturesDetector:
    def __init__(self, core_api: TpLinkWebApi):
        """Initialize."""
        self._core_api = core_api
        self._available_features = set()
        self._is_initialized = False

    @staticmethod
    def disconnected_as_false(func):
        @wraps(func)
        async def wrapper(*args, **kwargs) -> bool:
            try:
                return await func(*args, **kwargs)
            except ApiCallError as ace:
                if ace.category == APICALL_ERRCAT_DISCONNECTED:
                    return False
                raise

        return wrapper

    @staticmethod
    def log_feature(feature_name: str):
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                try:
                    _LOGGER.debug("Check feature '%s' availability", feature_name)
                    result = await func(*args, **kwargs)
                    if result:
                        _LOGGER.debug("Feature '%s' is available", feature_name)
                    else:
                        _LOGGER.debug("Feature '%s' is not available", feature_name)
                    return result
                except Exception:
                    _LOGGER.debug(
                        "Feature availability check failed on %s", feature_name
                    )
                    raise

            return wrapper

        return decorator

    @log_feature(FEATURE_POE)
    @disconnected_as_false
    async def _is_poe_available(self) -> bool:
        data = await self._core_api.get_variables(
            URL_POE_SETTINGS_GET,
            [
                ("portConfig", VariableType.Dict),
                ("poe_port_num", VariableType.Int),
            ],
        )
        return data.get("portConfig") is not None and data.get("poe_port_num") > 0

    @log_feature(FEATURE_STATS)
    @disconnected_as_false
    async def _is_stats_available(self) -> bool:
        data = await self._core_api.get_variables(
            URL_PORT_STATISTICS_GET,
            [
                ("all_info", VariableType.Dict),
                ("max_port_num", VariableType.Int),
            ],
        )
        return data.get("all_info") is not None and data.get("max_port_num") > 0

    async def update(self) -> None:
        """Update the available features list."""
        if await self._is_poe_available():
            self._available_features.add(FEATURE_POE)
        if await self._is_stats_available():
            self._available_features.add(FEATURE_STATS)

    def is_available(self, feature: str) -> bool:
        """Return true if feature is available."""
        return feature in self._available_features
