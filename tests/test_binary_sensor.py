"""Tests for binary sensor entities."""
from __future__ import annotations

import pytest

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.const import EntityCategory

from open_ialarm_mk_local_api import ZoneStatusEnum
from open_ialarm_mk_local_api.models.alarm_status_model import AlarmStatusModel
from open_ialarm_mk_local_api.models.zone_model import ZoneModel
from open_ialarm_mk_local_api import AlarmStatusEnum

from custom_components.open_ialarm_mk.binary_sensor import (
    IAlarmMkCommandConnectionSensor,
    IAlarmMkPushConnectionSensor,
    IAlarmMkZoneSensor,
    _device_class_for_zone,
)
from custom_components.open_ialarm_mk.coordinator import IAlarmMkCoordinator, IAlarmMkData
from custom_components.open_ialarm_mk.const import DOMAIN


@pytest.fixture
def coordinator(hass, mock_entry, mock_client, mock_network_info):
    mock_entry.add_to_hass(hass)
    coord = IAlarmMkCoordinator(hass, mock_entry, mock_client, mock_network_info, 30, "MK7")
    coord.async_set_updated_data(
        IAlarmMkData(
            status=AlarmStatusModel(status=AlarmStatusEnum.DISARMED),
            zones=[],
        )
    )
    return coord


# ── _device_class_for_zone ──────────────────────────────────────────────────

@pytest.mark.parametrize(
    "name,zone_type,expected",
    [
        ("Front Door", 1, BinarySensorDeviceClass.DOOR),
        ("porta cucina", 2, BinarySensorDeviceClass.DOOR),
        ("PIR motion", 1, BinarySensorDeviceClass.MOTION),
        ("intern hall", 1, BinarySensorDeviceClass.MOTION),
        ("movimento soggiorno", 2, BinarySensorDeviceClass.MOTION),
        ("window living", 1, BinarySensorDeviceClass.WINDOW),
        ("zone a", 3, BinarySensorDeviceClass.MOTION),
        ("tamper", 4, BinarySensorDeviceClass.PROBLEM),
        ("sabotage", 5, BinarySensorDeviceClass.PROBLEM),
        ("gas sensor", 6, BinarySensorDeviceClass.GAS),
        ("smoke detector", 6, BinarySensorDeviceClass.SMOKE),
        ("unknown type", 99, BinarySensorDeviceClass.OPENING),
    ],
)
def test_device_class_mapping(name, zone_type, expected):
    zone = ZoneModel(1, name, zone_type, ZoneStatusEnum.IN_USE)
    assert _device_class_for_zone(zone) == expected


# ── IAlarmMkCommandConnectionSensor ────────────────────────────────────────

def test_command_sensor_is_on_when_last_update_success(coordinator):
    sensor = IAlarmMkCommandConnectionSensor(coordinator)
    coordinator.last_update_success = True
    assert sensor.is_on is True


def test_command_sensor_is_off_when_last_update_failed(coordinator):
    sensor = IAlarmMkCommandConnectionSensor(coordinator)
    coordinator.last_update_success = False
    assert sensor.is_on is False


def test_command_sensor_unique_id(coordinator, mock_network_info):
    sensor = IAlarmMkCommandConnectionSensor(coordinator)
    assert mock_network_info.mac in sensor.unique_id
    assert "command_connection" in sensor.unique_id


def test_command_sensor_device_class(coordinator):
    sensor = IAlarmMkCommandConnectionSensor(coordinator)
    assert sensor.device_class == BinarySensorDeviceClass.CONNECTIVITY


def test_command_sensor_is_diagnostic(coordinator):
    sensor = IAlarmMkCommandConnectionSensor(coordinator)
    assert sensor.entity_category == EntityCategory.DIAGNOSTIC


# ── IAlarmMkPushConnectionSensor ───────────────────────────────────────────

def test_push_sensor_is_on_when_push_connected(coordinator, mock_push_client):
    coordinator._push_client = mock_push_client
    mock_push_client.connected = True
    sensor = IAlarmMkPushConnectionSensor(coordinator)
    assert sensor.is_on is True


def test_push_sensor_is_off_when_push_disconnected(coordinator, mock_push_client):
    coordinator._push_client = mock_push_client
    mock_push_client.connected = False
    sensor = IAlarmMkPushConnectionSensor(coordinator)
    assert sensor.is_on is False


def test_push_sensor_is_off_when_no_push_client(coordinator):
    sensor = IAlarmMkPushConnectionSensor(coordinator)
    assert sensor.is_on is False


def test_push_sensor_unique_id(coordinator, mock_network_info):
    sensor = IAlarmMkPushConnectionSensor(coordinator)
    assert mock_network_info.mac in sensor.unique_id
    assert "push_connection" in sensor.unique_id


# ── IAlarmMkZoneSensor ──────────────────────────────────────────────────────

@pytest.fixture
def zone_open():
    z = ZoneModel(1, "Front Door", 1, ZoneStatusEnum.IN_USE | ZoneStatusEnum.ALARM)
    return z


@pytest.fixture
def zone_sensor(coordinator, zone_open):
    coordinator.async_set_updated_data(
        IAlarmMkData(
            status=AlarmStatusModel(status=AlarmStatusEnum.DISARMED),
            zones=[zone_open],
        )
    )
    return IAlarmMkZoneSensor(coordinator, zone_open)


def test_zone_sensor_unique_id(zone_sensor, mock_network_info):
    assert mock_network_info.mac in zone_sensor.unique_id
    assert "zone_1" in zone_sensor.unique_id


def test_zone_sensor_name(zone_sensor):
    assert zone_sensor.name == "Front Door"


def test_zone_sensor_name_fallback():
    from unittest.mock import MagicMock
    coordinator = MagicMock()
    coordinator.network_info.mac = "aa:bb:cc:dd:ee:ff"
    zone = ZoneModel(5, "", 1, ZoneStatusEnum.IN_USE)
    sensor = IAlarmMkZoneSensor(coordinator, zone)
    assert sensor.name == "Zone 5"


def test_zone_sensor_is_on_when_open(zone_sensor, zone_open):
    assert zone_sensor.is_on == zone_open.is_open


def test_zone_sensor_is_none_when_no_data(zone_sensor):
    zone_sensor.coordinator.async_set_updated_data(None)
    assert zone_sensor.is_on is None


def test_zone_sensor_available_when_in_use(zone_sensor):
    assert zone_sensor.available is True


def test_zone_sensor_unavailable_when_not_in_use(coordinator, mock_network_info):
    zone = ZoneModel(3, "Unused", 1, ZoneStatusEnum(0))
    coordinator.async_set_updated_data(
        IAlarmMkData(
            status=AlarmStatusModel(status=AlarmStatusEnum.DISARMED),
            zones=[zone],
        )
    )
    sensor = IAlarmMkZoneSensor(coordinator, zone)
    assert sensor.available is False


def test_zone_sensor_extra_state_attributes(zone_sensor):
    attrs = zone_sensor.extra_state_attributes
    assert "bypass" in attrs
    assert "low_battery" in attrs
    assert "signal_loss" in attrs
    assert "zone_type" in attrs
    assert "zone_index" in attrs


def test_zone_sensor_extra_state_attributes_empty_when_no_data(zone_sensor):
    zone_sensor.coordinator.async_set_updated_data(None)
    assert zone_sensor.extra_state_attributes == {}
