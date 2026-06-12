"""Data update coordinator for iAlarm-MK."""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from open_ialarm_mk_local_api import (
    IAlarmMkAlarmError,
    IAlarmMkClient,
    IAlarmMkConnectionError,
    IAlarmMkLoginError,
)
from open_ialarm_mk_local_api.models.alarm_status_model import AlarmStatusModel
from open_ialarm_mk_local_api.models.network_info_model import NetworkInfoModel
from open_ialarm_mk_local_api.models.zone_model import ZoneModel

from .const import DOMAIN
from .panel_events import resolve_cid_status

_LOGGER = logging.getLogger(__name__)


@dataclass
class IAlarmMkData:
    status: AlarmStatusModel
    zones: list[ZoneModel]


class IAlarmMkCoordinator(DataUpdateCoordinator[IAlarmMkData]):
    """Coordinator for iAlarm-MK panel — polls status + zones together."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: IAlarmMkClient,
        network_info: NetworkInfoModel,
        scan_interval: int,
        model: str = "MK7",
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        self.client = client
        self.network_info = network_info
        self.model = model
        self.entry = entry
        self.client.on_event = self._on_panel_event

    def _on_panel_event(self, event: dict) -> None:
        """Called from a SyncWorker thread when the panel pushes an unsolicited event."""
        _LOGGER.debug("Panel push event received on command connection: %s", event)
        asyncio.run_coroutine_threadsafe(
            self._async_handle_panel_event(event), self.hass.loop
        )

    async def _async_handle_panel_event(self, event: dict) -> None:
        """Decode push event CID, immediately update HA state, then confirm with a poll."""
        new_status = resolve_cid_status(event)
        if new_status is not None and self.data is not None:
            self.async_set_updated_data(
                IAlarmMkData(status=AlarmStatusModel(status=new_status), zones=self.data.zones)
            )
        await self.async_refresh()

    async def _async_update_data(self) -> IAlarmMkData:
        try:
            status, zones = await asyncio.gather(
                self.client.get_status(),
                self.client.get_zones(),
            )
            return IAlarmMkData(status=status, zones=zones)
        except (IAlarmMkConnectionError, IAlarmMkLoginError) as err:
            raise UpdateFailed(f"Connection error polling iAlarm-MK: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Error polling iAlarm-MK: {err}") from err

    async def async_shutdown(self) -> None:
        """Disconnect the panel client."""
        try:
            await self.client.disconnect()
        except Exception as err:
            _LOGGER.debug("Error during disconnect: %s", err)

    # ------------------------------------------------------------------
    # Alarm control commands
    # ------------------------------------------------------------------

    async def async_arm_away(self) -> None:
        try:
            await self.client.arm_away()
        except IAlarmMkAlarmError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="device_rejected_command",
            ) from err
        await self.async_refresh()

    async def async_arm_stay(self) -> None:
        try:
            await self.client.arm_stay()
        except IAlarmMkAlarmError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="device_rejected_command",
            ) from err
        await self.async_refresh()

    async def async_arm_partial(self) -> None:
        try:
            await self.client.arm_partial()
        except IAlarmMkAlarmError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="device_rejected_command",
            ) from err
        await self.async_refresh()

    async def async_disarm(self) -> None:
        try:
            await self.client.disarm()
        except IAlarmMkAlarmError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="device_rejected_command",
            ) from err
        await self.async_refresh()

    async def async_cancel_alarm(self) -> None:
        try:
            await self.client.cancel_alarm()
        except IAlarmMkAlarmError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="device_rejected_command",
            ) from err
        await self.async_refresh()
