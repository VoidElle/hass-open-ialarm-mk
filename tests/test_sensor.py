"""Tests for the panel IP sensor entity."""
from __future__ import annotations

from datetime import datetime

import pytest

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import EntityCategory
from homeassistant.util import dt as dt_util

from open_ialarm_mk_local_api import AlarmStatusEnum
from open_ialarm_mk_local_api.models.alarm_status_model import AlarmStatusModel

from custom_components.open_ialarm_mk.coordinator import IAlarmMkCoordinator, IAlarmMkData
from custom_components.open_ialarm_mk.sensor import (
    IAlarmMkLastAlarmCidSensor,
    IAlarmMkLastAlarmTimeSensor,
    IAlarmMkLastAlarmZoneNameSensor,
    IAlarmMkLastAlarmZoneSensor,
    IAlarmMkPanelIpSensor,
)
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


# ── last_alarm_* sensors ─────────────────────────────────────────────────────


@pytest.fixture
def triggered_coordinator(hass, mock_entry, mock_client, mock_network_info):
    mock_entry.add_to_hass(hass)
    coord = IAlarmMkCoordinator(hass, mock_entry, mock_client, mock_network_info, 30, "MK7")
    coord.async_set_updated_data(
        IAlarmMkData(
            status=AlarmStatusModel(status=AlarmStatusEnum.TRIGGERED),
            zones=[],
            last_alarm_zone=3,
            last_alarm_zone_name="Ingresso",
            last_alarm_cid="1132",
            last_alarm_time="2026-09-22 00:47:44",
            last_alarm_time_utc=dt_util.as_utc(datetime(2026, 9, 22, 0, 47, 44)),
        )
    )
    return coord


def test_last_alarm_zone_sensor_unique_id(triggered_coordinator, mock_network_info):
    sensor = IAlarmMkLastAlarmZoneSensor(triggered_coordinator)
    assert sensor.unique_id == f"{mock_network_info.mac}_last_alarm_zone"


def test_last_alarm_zone_sensor_device_info(triggered_coordinator, mock_network_info):
    sensor = IAlarmMkLastAlarmZoneSensor(triggered_coordinator)
    assert (DOMAIN, mock_network_info.mac) in sensor.device_info["identifiers"]


def test_last_alarm_zone_sensor_native_value(triggered_coordinator):
    sensor = IAlarmMkLastAlarmZoneSensor(triggered_coordinator)
    assert sensor.native_value == 3


def test_last_alarm_zone_sensor_native_value_none_when_no_data(coordinator):
    coordinator.async_set_updated_data(None)
    sensor = IAlarmMkLastAlarmZoneSensor(coordinator)
    assert sensor.native_value is None


def test_last_alarm_zone_name_sensor_unique_id(triggered_coordinator, mock_network_info):
    sensor = IAlarmMkLastAlarmZoneNameSensor(triggered_coordinator)
    assert sensor.unique_id == f"{mock_network_info.mac}_last_alarm_zone_name"


def test_last_alarm_zone_name_sensor_device_info(triggered_coordinator, mock_network_info):
    sensor = IAlarmMkLastAlarmZoneNameSensor(triggered_coordinator)
    assert (DOMAIN, mock_network_info.mac) in sensor.device_info["identifiers"]


def test_last_alarm_zone_name_sensor_native_value(triggered_coordinator):
    sensor = IAlarmMkLastAlarmZoneNameSensor(triggered_coordinator)
    assert sensor.native_value == "Ingresso"


def test_last_alarm_zone_name_sensor_native_value_none_when_no_data(coordinator):
    coordinator.async_set_updated_data(None)
    sensor = IAlarmMkLastAlarmZoneNameSensor(coordinator)
    assert sensor.native_value is None


def test_last_alarm_cid_sensor_unique_id(triggered_coordinator, mock_network_info):
    sensor = IAlarmMkLastAlarmCidSensor(triggered_coordinator)
    assert sensor.unique_id == f"{mock_network_info.mac}_last_alarm_cid"


def test_last_alarm_cid_sensor_device_info(triggered_coordinator, mock_network_info):
    sensor = IAlarmMkLastAlarmCidSensor(triggered_coordinator)
    assert (DOMAIN, mock_network_info.mac) in sensor.device_info["identifiers"]


def test_last_alarm_cid_sensor_native_value(triggered_coordinator):
    sensor = IAlarmMkLastAlarmCidSensor(triggered_coordinator)
    assert sensor.native_value == "1132"


def test_last_alarm_cid_sensor_native_value_none_when_no_data(coordinator):
    coordinator.async_set_updated_data(None)
    sensor = IAlarmMkLastAlarmCidSensor(coordinator)
    assert sensor.native_value is None


def test_last_alarm_time_sensor_unique_id(triggered_coordinator, mock_network_info):
    sensor = IAlarmMkLastAlarmTimeSensor(triggered_coordinator)
    assert sensor.unique_id == f"{mock_network_info.mac}_last_alarm_time"


def test_last_alarm_time_sensor_device_info(triggered_coordinator, mock_network_info):
    sensor = IAlarmMkLastAlarmTimeSensor(triggered_coordinator)
    assert (DOMAIN, mock_network_info.mac) in sensor.device_info["identifiers"]


def test_last_alarm_time_sensor_native_value(triggered_coordinator):
    sensor = IAlarmMkLastAlarmTimeSensor(triggered_coordinator)
    assert sensor.native_value == dt_util.as_utc(datetime(2026, 9, 22, 0, 47, 44))


def test_last_alarm_time_sensor_device_class(triggered_coordinator):
    sensor = IAlarmMkLastAlarmTimeSensor(triggered_coordinator)
    assert sensor.device_class == SensorDeviceClass.TIMESTAMP


def test_last_alarm_time_sensor_native_value_none_when_no_data(coordinator):
    coordinator.async_set_updated_data(None)
    sensor = IAlarmMkLastAlarmTimeSensor(coordinator)
    assert sensor.native_value is None


def test_last_alarm_sensors_are_diagnostic(triggered_coordinator):
    for cls in (
        IAlarmMkLastAlarmZoneSensor,
        IAlarmMkLastAlarmZoneNameSensor,
        IAlarmMkLastAlarmCidSensor,
        IAlarmMkLastAlarmTimeSensor,
    ):
        assert cls(triggered_coordinator).entity_category == EntityCategory.DIAGNOSTIC
