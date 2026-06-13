"""Tests for the panel IP sensor entity."""
from __future__ import annotations

import pytest

from homeassistant.const import EntityCategory

from open_ialarm_mk_local_api import AlarmStatusEnum
from open_ialarm_mk_local_api.models.alarm_status_model import AlarmStatusModel

from custom_components.open_ialarm_mk.coordinator import IAlarmMkCoordinator, IAlarmMkData
from custom_components.open_ialarm_mk.sensor import IAlarmMkPanelIpSensor
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
def ip_sensor(coordinator):
    return IAlarmMkPanelIpSensor(coordinator)


def test_ip_sensor_native_value(ip_sensor, mock_network_info):
    assert ip_sensor.native_value == mock_network_info.ip


def test_ip_sensor_unique_id(ip_sensor, mock_network_info):
    assert mock_network_info.mac in ip_sensor.unique_id
    assert "panel_ip" in ip_sensor.unique_id


def test_ip_sensor_is_diagnostic(ip_sensor):
    assert ip_sensor.entity_category == EntityCategory.DIAGNOSTIC


def test_ip_sensor_icon(ip_sensor):
    assert ip_sensor.icon == "mdi:ip-network"


def test_ip_sensor_device_info(ip_sensor, mock_network_info):
    assert (DOMAIN, mock_network_info.mac) in ip_sensor.device_info["identifiers"]
