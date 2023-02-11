"""TP-Link web api core functions."""

import asyncio
from enum import Enum
import logging
import re
from typing import Callable, Dict, Final, Iterable, Tuple, TypeAlias

import aiohttp
from aiohttp import ClientResponse
import json5

TIMEOUT: Final = 5.0

APICALL_ERRCODE_UNAUTHORIZED: Final = -2
APICALL_ERRCODE_REQUEST: Final = -3

APICALL_ERRCAT_CREDENTIALS: Final = "user_pass_err"
APICALL_ERRCAT_REQUEST: Final = "request_error"
APICALL_ERRCAT_UNAUTHORIZED: Final = "unauthorized"

AUTH_FAILURE_GENERAL: Final = "auth_general"
AUTH_FAILURE_CREDENTIALS: Final = "auth_invalid_credentials"
AUTH_USER_BLOCKED: Final = "auth_user_blocked"
AUTH_TOO_MANY_USERS: Final = "auth_too_many_users"
AUTH_SESSION_TIMEOUT: Final = "auth_session_timeout"

_SCRIPT_REGEX = r".*<script>(.*)<\/script>\s*<html>"
_VARIABLES_REGEX = r".*var\s+(?P<variable>[a-zA-Z0-9_]+)\s*=\s*(?P<value>[^;]+);\s*"
_ARRAY_VALUES_REGEX = r"\s*new\s*Array\s*\((?P<items>[^\)]+)\)"

_LOGGER = logging.getLogger(__name__)

VariableValue: TypeAlias = str | int | list[str] | dict[str, any]

_VAR_LOGON_INFO: str = "logonInfo"


# ---------------------------
#   VariableType
# ---------------------------
class VariableType(Enum):
    Str = 0
    Int = 1
    List = 2
    Dict = 3


# ---------------------------
#   AuthenticationError
# ---------------------------
class AuthenticationError(Exception):
    def __init__(self, message: str, reason_code: str) -> None:
        """Initialize."""
        super().__init__(message)
        self._message = message
        self._reason_code = reason_code

    @property
    def reason_code(self) -> str | None:
        """Error reason code."""
        return self._reason_code

    def __str__(self, *args, **kwargs) -> str:
        """Return str(self)."""
        return f"{self._message}; reason: {self._reason_code}"

    def __repr__(self) -> str:
        """Return repr(self)."""
        return self.__str__()


# ---------------------------
#   ApiCallError
# ---------------------------
class ApiCallError(Exception):
    def __init__(
        self, message: str, error_code: int | None, error_category: str | None
    ):
        """Initialize."""
        super().__init__(message)
        self._message = message
        self._error_code = error_code
        self._error_category = error_category

    @property
    def code(self) -> int | None:
        """Error code."""
        return self._error_code

    @property
    def category(self) -> int | None:
        """Error category."""
        return self._error_category

    def __str__(self, *args, **kwargs) -> str:
        """Return str(self)."""
        return f"{self._message}; code: {self._error_code}, category: {self._error_category}"

    def __repr__(self) -> str:
        """Return repr(self)."""
        return self.__str__()


# ---------------------------
#   _get_response_text
# ---------------------------
async def _get_response_text(response: ClientResponse) -> str:
    content_bytes = await response.content.read()
    text = content_bytes.decode("utf-8")
    return text


# ---------------------------
#   _get_variables
# ---------------------------
def _get_variables(page: str) -> dict[str, str]:
    result = {}

    script_match = re.match(_SCRIPT_REGEX, page, re.RegexFlag.DOTALL)
    if not script_match:
        return result

    script_content = script_match.group(1)

    for variable_match in re.finditer(_VARIABLES_REGEX, script_content):
        variable = variable_match.group("variable")
        value = variable_match.group("value")
        result[variable] = value

    return result


# ---------------------------
#   _to_array
# ---------------------------
def _to_list(array_data: str) -> Iterable[str]:
    match = re.match(_ARRAY_VALUES_REGEX, array_data)
    array_items = match.group("items")
    if array_items:
        for item in array_items.split(","):
            yield item.strip(' ,\r\n\t"')


# ---------------------------
#   _to_dict
# ---------------------------
def _to_dict(json_data: str) -> dict[str, any] | None:
    return json5.loads(json_data) if json_data else None


# ---------------------------
#   _convert_value
# ---------------------------
def _convert_value(value: str, variable_type: VariableType) -> VariableValue | None:
    if value is None:
        return None
    elif variable_type == VariableType.Str:
        return value.strip("'\"")
    elif variable_type == VariableType.Int:
        return int(value)
    elif variable_type == VariableType.List:
        return list(_to_list(value))
    elif variable_type == VariableType.Dict:
        return _to_dict(value)


# ---------------------------
#   _get_variable
# ---------------------------
def _get_variable(
    page: str, name: str, variable_type: VariableType
) -> VariableValue | None:
    variables = _get_variables(page)
    if not variables:
        return None

    variable_str = variables.get(name)
    if not variable_str:
        return None

    return _convert_value(variable_str, variable_type)


# ---------------------------
#   _check_authorized
# ---------------------------
def _check_authorized(response: ClientResponse, result: str) -> bool:
    if response.status != 200:
        return False
    if not result:
        return False
    logon_info = _get_variable(result, _VAR_LOGON_INFO, VariableType.Str)
    if logon_info:
        return False
    return True


# ---------------------------
#   TpLinkWebApi
# ---------------------------
class TpLinkWebApi:
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
        _LOGGER.debug("New instance of TpLinkWebApi created")
        self._user: str = user
        self._password: str = password
        self._verify_ssl: bool = verify_ssl
        self._session: aiohttp.ClientSession | None = None
        self._active_csrf: Dict | None = None
        self._is_initialized: bool = False
        self._call_locker = asyncio.Lock()

        schema = "https" if use_ssl else "http"
        self._base_url: str = f"{schema}://{host}:{port}"

    @property
    def device_url(self) -> str:
        """Return switch's configuration url."""
        return self._base_url

    def _get_url(self, path) -> str:
        """Return full address to the endpoint."""
        return self._base_url + "/" + path

    async def _ensure_initialized(self) -> None:
        """Ensure that initial authorization was completed successfully."""
        if not self._is_initialized:
            await self.authenticate()
            self._is_initialized = True

    async def _get_raw(self, path: str) -> ClientResponse:
        """Perform GET request to the specified relative URL and return raw ClientResponse."""
        try:
            _LOGGER.debug("Performing GET to %s", path)
            response = await self._session.get(
                url=self._get_url(path),
                allow_redirects=True,
                verify_ssl=self._verify_ssl,
                timeout=TIMEOUT,
            )
            _LOGGER.debug("GET %s performed, status: %s", path, response.status)
            return response
        except Exception as ex:
            _LOGGER.error("GET %s failed: %s", path, str(ex))
            raise ApiCallError(
                f"Can not perform GET request at {path} cause of {repr(ex)}",
                APICALL_ERRCODE_REQUEST,
                APICALL_ERRCAT_REQUEST,
            )

    async def _post_raw(self, path: str, data: Dict) -> ClientResponse:
        """Perform POST request to the specified relative URL with specified body and return raw ClientResponse."""
        try:
            _LOGGER.debug("Performing POST to %s", path)
            response = await self._session.post(
                url=self._get_url(path),
                data=data,
                verify_ssl=self._verify_ssl,
                timeout=TIMEOUT,
            )
            _LOGGER.debug("POST to %s performed, status: %s", path, response.status)
            return response
        except Exception as ex:
            _LOGGER.error("POST %s failed: %s", path, str(ex))
            raise ApiCallError(
                f"Can not perform POST request at {path} cause of {repr(ex)}",
                APICALL_ERRCODE_REQUEST,
                APICALL_ERRCAT_REQUEST,
            )

    def _refresh_session(self) -> None:
        """Initialize the client session (if not exists) and clear cookies."""
        _LOGGER.debug("Refresh session called")
        if self._session is None:
            """Unsafe cookies for IP addresses instead of domain names"""
            jar = aiohttp.CookieJar(unsafe=True)
            self._session = aiohttp.ClientSession(cookie_jar=jar)
            _LOGGER.debug("Session created")
        self._session.cookie_jar.clear()
        self._active_csrf = None

    async def authenticate(self) -> None:
        """Perform authentication and return true when authentication success"""
        try:
            _LOGGER.debug("Authentication started")
            self._refresh_session()
            _LOGGER.debug("Performing logon")
            response = await self._post_raw(
                "logon.cgi",
                {"username": self._user, "password": self._password, "logon": "Login"},
            )

            if response.status != 200:
                _LOGGER.error(
                    "Authentication failed: can not perform POST, status is %s",
                    response.status,
                )
                raise AuthenticationError("Failed to get index", AUTH_FAILURE_GENERAL)

            result = await _get_response_text(response)
            if not result:
                raise AuthenticationError(
                    "Failed to get Logon response body", AUTH_FAILURE_GENERAL
                )

            array_items: list[str] = _get_variable(
                result, _VAR_LOGON_INFO, VariableType.List
            )

            if array_items[0] == "0":
                _LOGGER.debug("Authentication success")
                return
            elif array_items[0] == "1":
                raise AuthenticationError(
                    "The user name or the password is wrong", AUTH_FAILURE_CREDENTIALS
                )
            elif array_items[0] == "2":
                raise AuthenticationError(
                    "The user is not allowed to login", AUTH_USER_BLOCKED
                )
            elif array_items[0] == "3":
                raise AuthenticationError(
                    "The number of the user that allowed to login has been full",
                    AUTH_TOO_MANY_USERS,
                )
            elif array_items[0] == "4":
                raise AuthenticationError(
                    "The number of the login user has been full, it is allowed 16 people to login at the same time",
                    AUTH_TOO_MANY_USERS,
                )
            elif array_items[0] == "5":
                raise AuthenticationError(
                    "The session is timeout.",
                    AUTH_SESSION_TIMEOUT,
                )
            else:
                raise AuthenticationError(
                    f"Unknonwn error {array_items[0]}", AUTH_FAILURE_GENERAL
                )

        except AuthenticationError as ex:
            _LOGGER.warning("Authentication failed: %s", {repr(ex)})
            raise
        except ApiCallError as ex:
            _LOGGER.warning("Authentication failed: %s", {repr(ex)})
            raise AuthenticationError(
                "Authentication failed due to api call error", AUTH_FAILURE_GENERAL
            )
        except Exception as ex:
            _LOGGER.warning("Authentication failed: %s", {repr(ex)})
            raise AuthenticationError(
                "Authentication failed due to unknown error", AUTH_FAILURE_GENERAL
            )

    async def get(
        self, path: str, query: str | None = None, **kwargs: any
    ) -> str | None:
        """Perform GET request to the relative address."""
        async with self._call_locker:
            await self._ensure_initialized()

            relative_url = path if not query else f"{path}?{query}"

            check_authorized: Callable[[ClientResponse, str], bool] = (
                kwargs.get("check_authorized") or _check_authorized
            )

            response = await self._get_raw(relative_url)
            response_text = await _get_response_text(response)
            _LOGGER.debug("Response: %s", response_text)

            if not check_authorized(response, response_text):
                _LOGGER.debug("GET seems unauthorized, trying to re-authenticate")
                await self.authenticate()

                response = await self._get_raw(relative_url)
                response_text = await _get_response_text(response)

                if not check_authorized(response, response_text):
                    raise ApiCallError(
                        f"Api call error, status:{response.status}",
                        APICALL_ERRCODE_UNAUTHORIZED,
                        APICALL_ERRCAT_UNAUTHORIZED,
                    )

            return response_text

    async def post(
        self, path: str, data: dict | None = None, **kwargs: any
    ) -> str | None:
        """Perform POST request to the relative address."""
        async with self._call_locker:
            await self._ensure_initialized()

            check_authorized: Callable[[ClientResponse, str], bool] = (
                kwargs.get("check_authorized") or _check_authorized
            )

            response = await self._post_raw(path, data)
            response_text = await _get_response_text(response)
            _LOGGER.debug("Response: %s", response_text)

            if not check_authorized(response, response_text):
                _LOGGER.debug("POST seems unauthorized, trying to re-authenticate")
                await self.authenticate()

                response = await self._post_raw(path, data)
                response_text = await _get_response_text(response)

                if not check_authorized(response, response_text):
                    raise ApiCallError(
                        f"Api call error, status:{response.status}",
                        APICALL_ERRCODE_UNAUTHORIZED,
                        APICALL_ERRCAT_UNAUTHORIZED,
                    )

            return response_text

    async def get_variables(
        self, path: str, variables: Iterable[Tuple[str, VariableType]], **kwargs: any
    ) -> dict[str, VariableValue | None] | None:
        """Perform GET request to the relative address and get dict with the specified variables."""
        response_text = await self.get(path)
        result = {}
        response_variables = _get_variables(response_text)

        for variable, variable_type in variables:
            result[variable] = _convert_value(
                response_variables.get(variable), variable_type
            )

        _LOGGER.debug("Result is %s", result)

        return result

    async def get_variable(
        self, path: str, variable: str, variable_type: VariableType, **kwargs: any
    ) -> VariableValue | None:
        """Perform GET request to the relative address and get the value of the specified variable."""
        result = await self.get_variables(path, [(variable, variable_type)], **kwargs)
        return result.get(variable) if result else None

    async def disconnect(self) -> None:
        """Close session."""
        _LOGGER.debug("Disconnecting")
        if self._session is not None:
            await self._session.close()
            self._session = None
