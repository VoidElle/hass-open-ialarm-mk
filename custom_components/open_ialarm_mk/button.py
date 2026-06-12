"""Button entities for iAlarm-MK."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
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
    async_add_entities([IAlarmMkCancelAlarmButton(coordinator)])


class IAlarmMkCancelAlarmButton(CoordinatorEntity[IAlarmMkCoordinator], ButtonEntity):
    """Button that sends a cancel-alarm command to the panel."""

    _attr_has_entity_name = True
    _attr_translation_key = "cancel_alarm"

    def __init__(self, coordinator: IAlarmMkCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.network_info.mac}_cancel_alarm"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.network_info.mac)},
        )

    async def async_press(self) -> None:
        await self.coordinator.async_cancel_alarm()
