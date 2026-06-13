"""Shared fixtures for the iAlarm-MK test suite."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from homeassistant import loader
from homeassistant.core import HomeAssistant

from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME

from open_ialarm_mk_local_api import (
    AlarmStatusEnum,
    ZoneStatusEnum,
)
from open_ialarm_mk_local_api.models.alarm_status_model import AlarmStatusModel
from open_ialarm_mk_local_api.models.network_info_model import NetworkInfoModel
from open_ialarm_mk_local_api.models.zone_model import ZoneModel

from custom_components.open_ialarm_mk.const import (
    CONF_MODEL,
    CONF_SCAN_INTERVAL,
    DEFAULT_MODEL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)


@pytest.fixture(autouse=True)
def enable_custom_integrations(hass: HomeAssistant) -> None:
    """Allow HA to load custom_components/ from the project root."""
    hass.data.pop(loader.DATA_CUSTOM_COMPONENTS, None)


MOCK_MAC = "aa:bb:cc:dd:ee:ff"
MOCK_HOST = "192.168.1.100"
MOCK_PORT = 8000
MOCK_USERNAME = "admin"
MOCK_PASSWORD = "password"


@pytest.fixture
def mock_entry():
    """Return a mock config entry with default test values."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_HOST: MOCK_HOST,
            CONF_PORT: MOCK_PORT,
            CONF_USERNAME: MOCK_USERNAME,
            CONF_PASSWORD: MOCK_PASSWORD,
            CONF_MODEL: DEFAULT_MODEL,
            CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
        },
        unique_id=MOCK_MAC,
    )


@pytest.fixture
def mock_network_info():
    """Return a mock NetworkInfoModel."""
    return NetworkInfoModel(mac=MOCK_MAC, name="iAlarm Test", ip=MOCK_HOST)


@pytest.fixture
def mock_alarm_status_disarmed():
    return AlarmStatusModel(status=AlarmStatusEnum.DISARMED)


@pytest.fixture
def mock_alarm_status_armed_away():
    return AlarmStatusModel(status=AlarmStatusEnum.ARMED_AWAY)


@pytest.fixture
def mock_zone_in_use():
    """Return a simple in-use open zone."""
    return ZoneModel(
        index=1,
        name="Front Door",
        zone_type=1,
        status=ZoneStatusEnum.IN_USE,
    )


@pytest.fixture
def mock_zone_closed():
    """Return a closed in-use zone (bit mask: IN_USE only, is_open=False)."""
    return ZoneModel(
        index=2,
        name="Window",
        zone_type=2,
        status=ZoneStatusEnum.IN_USE,
    )


@pytest.fixture
def mock_client(mock_network_info, mock_alarm_status_disarmed, mock_zone_in_use):
    """Return a fully mocked IAlarmMkClient."""
    client = MagicMock()
    client.connect = AsyncMock()
    client.disconnect = AsyncMock()
    client.get_network_info = AsyncMock(return_value=mock_network_info)
    client.get_status = AsyncMock(return_value=mock_alarm_status_disarmed)
    client.get_zones = AsyncMock(return_value=[mock_zone_in_use])
    client.arm_away = AsyncMock()
    client.arm_stay = AsyncMock()
    client.arm_partial = AsyncMock()
    client.disarm = AsyncMock()
    client.cancel_alarm = AsyncMock()
    return client


@pytest.fixture
def mock_push_client():
    """Return a mocked IAlarmMkPushClient."""
    push_client = MagicMock()
    push_client.connected = True
    push_client.subscribe = AsyncMock()
    push_client.cancel = MagicMock()
    return push_client
