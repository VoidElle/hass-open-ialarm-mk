"""Tests for the config flow."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.data_entry_flow import FlowResultType

from open_ialarm_mk_local_api import IAlarmMkConnectionError, IAlarmMkLoginError

from custom_components.open_ialarm_mk.const import (
    CONF_MODEL,
    CONF_SCAN_INTERVAL,
    DEFAULT_MODEL,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

VALID_INPUT = {
    CONF_HOST: "192.168.1.100",
    CONF_PORT: DEFAULT_PORT,
    CONF_USERNAME: "admin",
    CONF_PASSWORD: "password",
    CONF_MODEL: DEFAULT_MODEL,
    CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
}

MOCK_MAC = "aa:bb:cc:dd:ee:ff"
MOCK_NAME = "iAlarm Test"


# ── async_step_user ─────────────────────────────────────────────────────────

async def test_user_step_shows_form(hass):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}


async def test_user_step_success(hass):
    with (
        patch(
            "custom_components.open_ialarm_mk.config_flow._validate_and_get_info",
            AsyncMock(return_value=(MOCK_MAC, MOCK_NAME)),
        ),
        patch("custom_components.open_ialarm_mk.async_setup_entry", AsyncMock(return_value=True)),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=VALID_INPUT,
        )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == MOCK_NAME
    assert result["data"] == VALID_INPUT


async def test_user_step_invalid_auth(hass):
    with patch(
        "custom_components.open_ialarm_mk.config_flow._validate_and_get_info",
        AsyncMock(side_effect=IAlarmMkLoginError("bad creds")),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=VALID_INPUT,
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"]["base"] == "invalid_auth"


async def test_user_step_cannot_connect(hass):
    with patch(
        "custom_components.open_ialarm_mk.config_flow._validate_and_get_info",
        AsyncMock(side_effect=IAlarmMkConnectionError("no host")),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=VALID_INPUT,
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"]["base"] == "cannot_connect"


async def test_user_step_timeout(hass):
    with patch(
        "custom_components.open_ialarm_mk.config_flow._validate_and_get_info",
        AsyncMock(side_effect=TimeoutError()),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=VALID_INPUT,
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"]["base"] == "cannot_connect"


async def test_user_step_unknown_error(hass):
    with patch(
        "custom_components.open_ialarm_mk.config_flow._validate_and_get_info",
        AsyncMock(side_effect=RuntimeError("boom")),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=VALID_INPUT,
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"]["base"] == "unknown"


async def test_user_step_aborts_on_duplicate(hass):
    """Second setup with same MAC aborts with already_configured."""
    with (
        patch(
            "custom_components.open_ialarm_mk.config_flow._validate_and_get_info",
            AsyncMock(return_value=(MOCK_MAC, MOCK_NAME)),
        ),
        patch("custom_components.open_ialarm_mk.async_setup_entry", AsyncMock(return_value=True)),
    ):
        result1 = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=VALID_INPUT,
        )
    assert result1["type"] == FlowResultType.CREATE_ENTRY

    with patch(
        "custom_components.open_ialarm_mk.config_flow._validate_and_get_info",
        AsyncMock(return_value=(MOCK_MAC, MOCK_NAME)),
    ):
        result2 = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=VALID_INPUT,
        )
    assert result2["type"] == FlowResultType.ABORT
    assert result2["reason"] == "already_configured"


# ── async_step_reconfigure ──────────────────────────────────────────────────

async def test_reconfigure_step_success(hass):
    """Reconfigure with new credentials updates the entry."""
    with (
        patch(
            "custom_components.open_ialarm_mk.config_flow._validate_and_get_info",
            AsyncMock(return_value=(MOCK_MAC, MOCK_NAME)),
        ),
        patch("custom_components.open_ialarm_mk.async_setup_entry", AsyncMock(return_value=True)),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=VALID_INPUT,
        )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    entry = result["result"]

    with (
        patch(
            "custom_components.open_ialarm_mk.config_flow._validate_and_get_info",
            AsyncMock(return_value=(MOCK_MAC, MOCK_NAME)),
        ),
        patch("custom_components.open_ialarm_mk.async_setup_entry", AsyncMock(return_value=True)),
    ):
        reconfigure_result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_RECONFIGURE, "entry_id": entry.entry_id},
            data={**VALID_INPUT, CONF_HOST: "192.168.1.200"},
        )

    assert reconfigure_result["type"] == FlowResultType.ABORT
    assert reconfigure_result["reason"] == "reconfigure_successful"


async def test_reconfigure_step_shows_form(hass):
    with (
        patch(
            "custom_components.open_ialarm_mk.config_flow._validate_and_get_info",
            AsyncMock(return_value=(MOCK_MAC, MOCK_NAME)),
        ),
        patch("custom_components.open_ialarm_mk.async_setup_entry", AsyncMock(return_value=True)),
    ):
        create_result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=VALID_INPUT,
        )
    entry = create_result["result"]

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_RECONFIGURE, "entry_id": entry.entry_id},
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "reconfigure"


async def test_reconfigure_step_invalid_auth(hass):
    with (
        patch(
            "custom_components.open_ialarm_mk.config_flow._validate_and_get_info",
            AsyncMock(return_value=(MOCK_MAC, MOCK_NAME)),
        ),
        patch("custom_components.open_ialarm_mk.async_setup_entry", AsyncMock(return_value=True)),
    ):
        create_result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=VALID_INPUT,
        )
    entry = create_result["result"]

    with patch(
        "custom_components.open_ialarm_mk.config_flow._validate_and_get_info",
        AsyncMock(side_effect=IAlarmMkLoginError("bad")),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_RECONFIGURE, "entry_id": entry.entry_id},
            data=VALID_INPUT,
        )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"]["base"] == "invalid_auth"
