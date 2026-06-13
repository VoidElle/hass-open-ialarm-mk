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
    AlarmStatusEnum,
    IAlarmMkAlarmError,
    IAlarmMkClient,
    IAlarmMkConnectionError,
    IAlarmMkLoginError,
    IAlarmMkPushClient,
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
        self._push_client: IAlarmMkPushClient | None = None
        self._push_task: asyncio.Task | None = None
    @property
    def push_connected(self) -> bool:
        """True when the dedicated push TCP connection is established."""
        if self._push_client is None:
            return False
        return self._push_client.connected

    def _on_push_event(self, event: dict) -> None:
        """Called from the asyncio event loop by the dedicated push client."""
        _LOGGER.debug("Push event received on dedicated connection: %s", event)
        self.hass.async_create_task(self._async_handle_panel_event(event))

    def start_push_client(self, push_client: IAlarmMkPushClient) -> None:
        """Store the push client and start its subscription task."""
        self._push_client = push_client
        self._push_task = self.hass.async_create_background_task(
            push_client.subscribe(), "ialarm-mk-push"
        )
        _LOGGER.debug("start_push_client: push subscription task started")

    async def _async_handle_panel_event(self, event: dict) -> None:
        """Decode push event CID and update HA state.

        Push events from the dedicated connection are real-time — no batching,
        no polling needed.  Unknown CIDs fall back to a poll.
        """
        new_status = resolve_cid_status(event)
        if new_status is not None and self.data is not None:
            self.async_set_updated_data(
                IAlarmMkData(status=AlarmStatusModel(status=new_status), zones=self.data.zones)
            )
        else:
            await self.async_refresh()

    async def _async_update_data(self) -> IAlarmMkData:
        try:
            status, zones = await asyncio.gather(
                self.client.get_status(),
                self.client.get_zones(),
            )
            if status.status == AlarmStatusEnum.UNAVAILABLE:
                _LOGGER.debug("Status UNAVAILABLE (panel transitioning), retrying in 2s")
                await asyncio.sleep(2)
                status = await self.client.get_status()
                if status.status == AlarmStatusEnum.UNAVAILABLE:
                    _LOGGER.warning("Status still UNAVAILABLE after retry, raising UpdateFailed")
                    raise UpdateFailed("iAlarm-MK returned UNAVAILABLE status after retry")
            return IAlarmMkData(status=status, zones=zones)
        except (IAlarmMkConnectionError, IAlarmMkLoginError) as err:
            self._handle_poll_failure(err)
            raise UpdateFailed(f"Connection error polling iAlarm-MK: {err}") from err
        except UpdateFailed:
            raise
        except Exception as err:
            self._handle_poll_failure(err)
            raise UpdateFailed(f"Error polling iAlarm-MK: {err}") from err

    def _handle_poll_failure(self, err: Exception) -> None:
        """Detect the command pairing-lock and self-heal via reload.

        The panel accepts TCP connections but silently ignores Pair/Client
        frames when it already has an active authenticated session (the push
        client holds one).  That causes every command-client reconnect attempt
        to time out while the push keepalive keeps succeeding.

        Condition: poll failed AND push is still alive.
        Action: schedule an integration reload, which cleanly closes both
        sockets and re-authenticates from scratch - identical to a manual reload.
        """
        if self.push_connected:
            _LOGGER.warning(
                "Poll failed while push is alive — panel likely locked command pairing; "
                "scheduling reload: %s",
                err,
            )
            self.hass.async_create_task(
                self.hass.config_entries.async_reload(self.entry.entry_id)
            )

    async def async_shutdown(self) -> None:
        """Stop the push subscription and disconnect the command client."""
        if self._push_client is not None:
            self._push_client.cancel()
        if self._push_task is not None and not self._push_task.done():
            self._push_task.cancel()
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

