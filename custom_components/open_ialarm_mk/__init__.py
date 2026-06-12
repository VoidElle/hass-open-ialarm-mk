"""iAlarm-MK Home Assistant integration."""
from __future__ import annotations

import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from open_ialarm_mk_local_api import IAlarmMkClient, IAlarmMkConnectionError, IAlarmMkLoginError, IAlarmMkPushClient

from .const import CONF_SCAN_INTERVAL, CONF_MODEL, DEFAULT_MODEL, DEFAULT_SCAN_INTERVAL, DOMAIN
from .coordinator import IAlarmMkCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.ALARM_CONTROL_PANEL, Platform.BINARY_SENSOR, Platform.BUTTON, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]
    scan_interval = entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    model = entry.data.get(CONF_MODEL, DEFAULT_MODEL)

    client = IAlarmMkClient(host, port, username, password, keepalive_interval=None)

    try:
        async with asyncio.timeout(15):
            await client.connect()
            network_info = await client.get_network_info()
    except (IAlarmMkConnectionError, IAlarmMkLoginError, TimeoutError) as err:
        await _safe_disconnect(client)
        raise ConfigEntryNotReady(
            f"Cannot connect to iAlarm-MK at {host}:{port}"
        ) from err
    except Exception as err:
        await _safe_disconnect(client)
        raise ConfigEntryNotReady(f"Unexpected error connecting to {host}:{port}") from err

    coordinator = IAlarmMkCoordinator(hass, entry, client, network_info, scan_interval, model)

    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception:
        await coordinator.async_shutdown()
        raise

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    push_client = IAlarmMkPushClient(host, port, username, coordinator._on_push_event)
    coordinator.start_push_client(push_client)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator: IAlarmMkCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.async_shutdown()
    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def _safe_disconnect(client: IAlarmMkClient) -> None:
    try:
        await client.disconnect()
    except Exception:
        pass
