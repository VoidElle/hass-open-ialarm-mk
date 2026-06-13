"""Tests for const.py."""
from __future__ import annotations

from custom_components.open_ialarm_mk.const import (
    CONF_MODEL,
    CONF_SCAN_INTERVAL,
    DEFAULT_MODEL,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    SUPPORTED_MODELS,
)


def test_domain():
    assert DOMAIN == "open_ialarm_mk"


def test_default_port():
    assert DEFAULT_PORT == 8000


def test_default_scan_interval():
    assert isinstance(DEFAULT_SCAN_INTERVAL, int)
    assert DEFAULT_SCAN_INTERVAL > 0


def test_default_model_in_supported():
    assert DEFAULT_MODEL in SUPPORTED_MODELS


def test_supported_models_non_empty():
    assert len(SUPPORTED_MODELS) > 0


def test_conf_keys_are_strings():
    assert isinstance(CONF_SCAN_INTERVAL, str)
    assert isinstance(CONF_MODEL, str)
