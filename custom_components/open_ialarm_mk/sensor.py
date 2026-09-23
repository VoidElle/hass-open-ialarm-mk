"""Diagnostic sensor entities for iAlarm-MK."""
from __future__ import annotations

from datetime import datetime

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import IAlarmMkCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: IAlarmMkCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        IAlarmMkPanelIpSensor(coordinator),
        IAlarmMkLastAlarmZoneSensor(coordinator),
        IAlarmMkLastAlarmZoneNameSensor(coordinator),
        IAlarmMkLastAlarmCidSensor(coordinator),
        IAlarmMkLastAlarmTimeSensor(coordinator),
    ])


def _device_info(coordinator: IAlarmMkCoordinator) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, coordinator.network_info.mac)},
        name=coordinator.network_info.name or "iAlarm-MK",
        manufacturer="Antifurto365 / Meian Technology",
        model=f"iAlarm {coordinator.model}",
    )


class IAlarmMkPanelIpSensor(CoordinatorEntity[IAlarmMkCoordinator], SensorEntity):
    """Panel IP address."""

    _attr_has_entity_name = True
    _attr_translation_key = "panel_ip"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:ip-network"

    def __init__(self, coordinator: IAlarmMkCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.network_info.mac}_panel_ip"
        self._attr_native_value = coordinator.network_info.ip

    @property
    def device_info(self) -> DeviceInfo:
        return _device_info(self.coordinator)


class IAlarmMkLastAlarmZoneSensor(CoordinatorEntity[IAlarmMkCoordinator], SensorEntity):
    """Zone index of the last triggered alarm."""

    _attr_has_entity_name = True
    _attr_translation_key = "last_alarm_zone"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:shield-alert-outline"

    def __init__(self, coordinator: IAlarmMkCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.network_info.mac}_last_alarm_zone"

    @property
    def device_info(self) -> DeviceInfo:
        return _device_info(self.coordinator)

    @property
    def native_value(self) -> int | None:
        return self.coordinator.data.last_alarm_zone if self.coordinator.data else None


class IAlarmMkLastAlarmZoneNameSensor(CoordinatorEntity[IAlarmMkCoordinator], SensorEntity):
    """Zone name of the last triggered alarm."""

    _attr_has_entity_name = True
    _attr_translation_key = "last_alarm_zone_name"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:map-marker-alert-outline"

    def __init__(self, coordinator: IAlarmMkCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.network_info.mac}_last_alarm_zone_name"

    @property
    def device_info(self) -> DeviceInfo:
        return _device_info(self.coordinator)

    @property
    def native_value(self) -> str | None:
        return self.coordinator.data.last_alarm_zone_name if self.coordinator.data else None


class IAlarmMkLastAlarmCidSensor(CoordinatorEntity[IAlarmMkCoordinator], SensorEntity):
    """CID code of the last triggered alarm."""

    _attr_has_entity_name = True
    _attr_translation_key = "last_alarm_cid"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:identifier"

    def __init__(self, coordinator: IAlarmMkCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.network_info.mac}_last_alarm_cid"

    @property
    def device_info(self) -> DeviceInfo:
        return _device_info(self.coordinator)

    @property
    def native_value(self) -> str | None:
        return self.coordinator.data.last_alarm_cid if self.coordinator.data else None


class IAlarmMkLastAlarmTimeSensor(CoordinatorEntity[IAlarmMkCoordinator], SensorEntity):
    """Timestamp of the last triggered alarm."""

    _attr_has_entity_name = True
    _attr_translation_key = "last_alarm_time"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:clock-alert-outline"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator: IAlarmMkCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.network_info.mac}_last_alarm_time"

    @property
    def device_info(self) -> DeviceInfo:
        return _device_info(self.coordinator)

    @property
    def native_value(self) -> datetime | None:
        return self.coordinator.data.last_alarm_time_utc if self.coordinator.data else None
