"""Config flow for iAlarm-MK integration."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.helpers.device_registry import format_mac

from open_ialarm_mk_local_api import IAlarmMkClient, IAlarmMkConnectionError, IAlarmMkLoginError

from .const import CONF_SCAN_INTERVAL, CONF_MODEL, DEFAULT_PORT, DEFAULT_SCAN_INTERVAL, DEFAULT_MODEL, DOMAIN, SUPPORTED_MODELS

_LOGGER = logging.getLogger(__name__)

_STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): vol.Coerce(int),
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Required(CONF_MODEL, default=DEFAULT_MODEL): vol.In(SUPPORTED_MODELS),
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
            vol.Coerce(int), vol.Range(min=10, max=300)
        ),
    }
)


async def _validate_and_get_info(
    host: str, port: int, username: str, password: str
) -> tuple[str, str]:
    """Connect to the panel, retrieve MAC and name, then disconnect. Raises on failure."""
    client = IAlarmMkClient(host, port, username, password, keepalive_interval=None)
    try:
        async with asyncio.timeout(15):
            await client.connect()
            info = await client.get_network_info()
            return format_mac(info.mac), info.name or "iAlarm-MK"
    finally:
        try:
            await client.disconnect()
        except Exception:
            pass


class IAlarmMk7ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow for iAlarm-MK."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input[CONF_PORT]
            username = user_input[CONF_USERNAME]
            password = user_input[CONF_PASSWORD]

            try:
                mac, name = await _validate_and_get_info(host, port, username, password)
            except IAlarmMkLoginError:
                errors["base"] = "invalid_auth"
            except (IAlarmMkConnectionError, TimeoutError, OSError):
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error during setup")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(mac)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=name,
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_STEP_USER_SCHEMA,
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        entry: ConfigEntry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input[CONF_PORT]
            username = user_input[CONF_USERNAME]
            password = user_input[CONF_PASSWORD]

            try:
                mac, name = await _validate_and_get_info(host, port, username, password)
            except IAlarmMkLoginError:
                errors["base"] = "invalid_auth"
            except (IAlarmMkConnectionError, TimeoutError, OSError):
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error during reconfigure")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(mac)
                self._abort_if_unique_id_mismatch()
                return self.async_update_reload_and_abort(
                    entry, data=user_input, reason="reconfigure_successful"
                )

        schema = self.add_suggested_values_to_schema(
            _STEP_USER_SCHEMA, entry.data
        )
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=schema,
            errors=errors,
        )
