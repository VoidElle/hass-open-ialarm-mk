"""Tests for the cancel-alarm button entity."""
from __future__ import annotations

import pytest

from open_ialarm_mk_local_api import AlarmStatusEnum, IAlarmMkAlarmError
from open_ialarm_mk_local_api.models.alarm_status_model import AlarmStatusModel

from homeassistant.exceptions import HomeAssistantError

from custom_components.open_ialarm_mk.button import IAlarmMkCancelAlarmButton
from custom_components.open_ialarm_mk.coordinator import IAlarmMkCoordinator, IAlarmMkData
from custom_components.open_ialarm_mk.const import DOMAIN


@pytest.fixture
def coordinator(hass, mock_entry, mock_client, mock_network_info):
    mock_entry.add_to_hass(hass)
    coord = IAlarmMkCoordinator(hass, mock_entry, mock_client, mock_network_info, 30, "MK7")
    coord.async_set_updated_data(
        IAlarmMkData(status=AlarmStatusModel(status=AlarmStatusEnum.DISARMED), zones=[])
    )
    return coord


@pytest.fixture
def cancel_button(coordinator):
    return IAlarmMkCancelAlarmButton(coordinator)


def test_cancel_button_unique_id(cancel_button, mock_network_info):
    assert mock_network_info.mac in cancel_button.unique_id
    assert "cancel_alarm" in cancel_button.unique_id


def test_cancel_button_device_info(cancel_button, mock_network_info):
    assert (DOMAIN, mock_network_info.mac) in cancel_button.device_info["identifiers"]


async def test_cancel_button_press_calls_coordinator(cancel_button, mock_client):
    mock_client.get_status.return_value = AlarmStatusModel(status=AlarmStatusEnum.DISARMED)
    mock_client.get_zones.return_value = []
    await cancel_button.async_press()
    mock_client.cancel_alarm.assert_called_once()


async def test_cancel_button_press_raises_ha_error_on_alarm_error(cancel_button, mock_client):
    mock_client.cancel_alarm.side_effect = IAlarmMkAlarmError("rejected")
    with pytest.raises(HomeAssistantError):
        await cancel_button.async_press()
