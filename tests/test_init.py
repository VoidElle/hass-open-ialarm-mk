"""Integration-level tests for async_setup_entry / async_unload_entry."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.exceptions import ConfigEntryNotReady

from open_ialarm_mk_local_api import IAlarmMkConnectionError, IAlarmMkLoginError

from custom_components.open_ialarm_mk.const import CONF_MODEL, CONF_SCAN_INTERVAL, DOMAIN
from tests.conftest import MOCK_HOST, MOCK_MAC, MOCK_PORT, MOCK_PASSWORD, MOCK_USERNAME


def _make_mock_client(network_info, status, zones):
    client = MagicMock()
    client.connect = AsyncMock()
    client.disconnect = AsyncMock()
    client.get_network_info = AsyncMock(return_value=network_info)
    client.get_status = AsyncMock(return_value=status)
    client.get_zones = AsyncMock(return_value=zones)
    return client


async def test_setup_entry_success(hass, mock_entry, mock_network_info, mock_alarm_status_disarmed, mock_zone_in_use):
    mock_entry.add_to_hass(hass)
    client = _make_mock_client(mock_network_info, mock_alarm_status_disarmed, [mock_zone_in_use])
    push_client = MagicMock()
    push_client.connected = True
    push_client.subscribe = AsyncMock()
    push_client.cancel = MagicMock()

    with (
        patch("custom_components.open_ialarm_mk.IAlarmMkClient", return_value=client),
        patch("custom_components.open_ialarm_mk.IAlarmMkPushClient", return_value=push_client),
    ):
        result = await hass.config_entries.async_setup(mock_entry.entry_id)

    assert result is True
    assert mock_entry.entry_id in hass.data[DOMAIN]


async def test_setup_entry_connection_error_raises_not_ready(hass, mock_entry):
    mock_entry.add_to_hass(hass)
    client = MagicMock()
    client.connect = AsyncMock(side_effect=IAlarmMkConnectionError("no host"))
    client.disconnect = AsyncMock()

    with patch("custom_components.open_ialarm_mk.IAlarmMkClient", return_value=client):
        with pytest.raises(ConfigEntryNotReady):
            from custom_components.open_ialarm_mk import async_setup_entry
            await async_setup_entry(hass, mock_entry)


async def test_setup_entry_login_error_raises_not_ready(hass, mock_entry):
    mock_entry.add_to_hass(hass)
    client = MagicMock()
    client.connect = AsyncMock(side_effect=IAlarmMkLoginError("bad auth"))
    client.disconnect = AsyncMock()

    with patch("custom_components.open_ialarm_mk.IAlarmMkClient", return_value=client):
        with pytest.raises(ConfigEntryNotReady):
            from custom_components.open_ialarm_mk import async_setup_entry
            await async_setup_entry(hass, mock_entry)


async def test_unload_entry_success(hass, mock_entry, mock_network_info, mock_alarm_status_disarmed, mock_zone_in_use):
    mock_entry.add_to_hass(hass)
    client = _make_mock_client(mock_network_info, mock_alarm_status_disarmed, [mock_zone_in_use])
    push_client = MagicMock()
    push_client.connected = True
    push_client.subscribe = AsyncMock()
    push_client.cancel = MagicMock()

    with (
        patch("custom_components.open_ialarm_mk.IAlarmMkClient", return_value=client),
        patch("custom_components.open_ialarm_mk.IAlarmMkPushClient", return_value=push_client),
    ):
        await hass.config_entries.async_setup(mock_entry.entry_id)
        result = await hass.config_entries.async_unload(mock_entry.entry_id)

    assert result is True
    assert mock_entry.entry_id not in hass.data.get(DOMAIN, {})
