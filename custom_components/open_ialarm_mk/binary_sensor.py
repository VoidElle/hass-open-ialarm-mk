"""Binary sensor entities for iAlarm-MK zones."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from open_ialarm_mk_local_api import ZoneStatusEnum
from open_ialarm_mk_local_api.models.zone_model import ZoneModel

from .const import DOMAIN
from .coordinator import IAlarmMkCoordinator


def _device_class_for_zone(zone: ZoneModel) -> BinarySensorDeviceClass:
    """Map zone type + name hint to a HA binary sensor device class."""
    name = zone.name.lower()
    zt = zone.zone_type

    if zt in (1, 2):
        if any(k in name for k in ("door", "port", "porta")):
            return BinarySensorDeviceClass.DOOR
        if any(k in name for k in ("motion", "pir", "intern", "movimento")):
            return BinarySensorDeviceClass.MOTION
        return BinarySensorDeviceClass.WINDOW
    if zt == 3:
        return BinarySensorDeviceClass.MOTION
    if zt in (4, 5):
        return BinarySensorDeviceClass.PROBLEM
    if zt == 6:
        if "gas" in name:
            return BinarySensorDeviceClass.GAS
        return BinarySensorDeviceClass.SMOKE
    return BinarySensorDeviceClass.OPENING


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: IAlarmMkCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[BinarySensorEntity] = [
        IAlarmMkCommandConnectionSensor(coordinator),
        IAlarmMkPushConnectionSensor(coordinator),
    ]

    if coordinator.data is not None:
        entities += [
            IAlarmMkZoneSensor(coordinator, zone)
            for zone in coordinator.data.zones
            if (zone.status & ZoneStatusEnum.IN_USE) or zone.name
        ]

    async_add_entities(entities)


def _device_info(coordinator: IAlarmMkCoordinator) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, coordinator.network_info.mac)},
        name=coordinator.network_info.name or "iAlarm-MK",
        manufacturer="Antifurto365 / Meian Technology",
        model=f"iAlarm {coordinator.model}",
    )


class IAlarmMkCommandConnectionSensor(CoordinatorEntity[IAlarmMkCoordinator], BinarySensorEntity):
    """Diagnostic sensor: command TCP connection status."""

    _attr_has_entity_name = True
    _attr_name = "Command Connection"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: IAlarmMkCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.network_info.mac}_command_connection"

    @property
    def device_info(self) -> DeviceInfo:
        return _device_info(self.coordinator)

    @property
    def is_on(self) -> bool:
        return self.coordinator.last_update_success


class IAlarmMkPushConnectionSensor(CoordinatorEntity[IAlarmMkCoordinator], BinarySensorEntity):
    """Diagnostic sensor: push TCP connection status."""

    _attr_has_entity_name = True
    _attr_name = "Push Connection"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: IAlarmMkCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.network_info.mac}_push_connection"

    @property
    def device_info(self) -> DeviceInfo:
        return _device_info(self.coordinator)

    @property
    def is_on(self) -> bool:
        return self.coordinator.push_connected


class IAlarmMkZoneSensor(CoordinatorEntity[IAlarmMkCoordinator], BinarySensorEntity):
    """Binary sensor representing a single iAlarm-MK zone."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: IAlarmMkCoordinator, zone: ZoneModel) -> None:
        super().__init__(coordinator)
        self._zone_index = zone.index
        self._attr_unique_id = f"{coordinator.network_info.mac}_zone_{zone.index}"
        self._attr_name = zone.name or f"Zone {zone.index}"
        self._attr_device_class = _device_class_for_zone(zone)

    @property
    def device_info(self) -> DeviceInfo:
        return _device_info(self.coordinator)

    @property
    def _zone(self) -> ZoneModel | None:
        if self.coordinator.data is None:
            return None
        for zone in self.coordinator.data.zones:
            if zone.index == self._zone_index:
                return zone
        return None

    @property
    def available(self) -> bool:
        zone = self._zone
        if zone is None:
            return False
        return self.coordinator.last_update_success and bool(
            zone.status & ZoneStatusEnum.IN_USE
        )

    @property
    def is_on(self) -> bool | None:
        zone = self._zone
        if zone is None:
            return None
        return zone.is_open

    @property
    def extra_state_attributes(self) -> dict:
        zone = self._zone
        if zone is None:
            return {}
        return {
            "bypass": zone.is_bypassed,
            "low_battery": zone.low_battery,
            "signal_loss": zone.signal_loss,
            "zone_type": zone.zone_type,
            "zone_index": zone.index,
        }
