"""Diagnostic sensor entities for iAlarm-MK."""
from __future__ import annotations

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
        IAlarmMkLastPollSensor(coordinator),
        IAlarmMkPanelIpSensor(coordinator),
    ])


def _device_info(coordinator: IAlarmMkCoordinator) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, coordinator.network_info.mac)},
        name=coordinator.network_info.name or "iAlarm-MK",
        manufacturer="Antifurto365 / Meian Technology",
        model=f"iAlarm {coordinator.model}",
    )


class IAlarmMkLastPollSensor(CoordinatorEntity[IAlarmMkCoordinator], SensorEntity):
    """Timestamp of the last successful coordinator poll."""

    _attr_has_entity_name = True
    _attr_translation_key = "last_poll"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: IAlarmMkCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.network_info.mac}_last_poll"

    @property
    def available(self) -> bool:
        return True

    @property
    def device_info(self) -> DeviceInfo:
        return _device_info(self.coordinator)

    @property
    def native_value(self):
        return self.coordinator.last_successful_poll


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
