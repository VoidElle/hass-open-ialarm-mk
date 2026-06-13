"""Tests for panel_events.py — pure logic, no HA mocking needed."""
from __future__ import annotations

import pytest

from open_ialarm_mk_local_api import AlarmStatusEnum

from custom_components.open_ialarm_mk.panel_events import resolve_cid_status


# ── known CID mappings ──────────────────────────────────────────────────────

TRIGGER_CIDS = [1100, 1110, 1120, 1130, 1131, 1132, 1133, 1134]
DISARM_CIDS = [1401, 1406]


@pytest.mark.parametrize("cid", TRIGGER_CIDS)
def test_trigger_cids_map_to_triggered(cid):
    event = {"Cid": cid}
    assert resolve_cid_status(event) == AlarmStatusEnum.TRIGGERED


@pytest.mark.parametrize("cid", DISARM_CIDS)
def test_disarm_cids_map_to_disarmed(cid):
    event = {"Cid": cid}
    assert resolve_cid_status(event) == AlarmStatusEnum.DISARMED


def test_arm_away_cid():
    assert resolve_cid_status({"Cid": 3401}) == AlarmStatusEnum.ARMED_AWAY


def test_arm_stay_cid():
    assert resolve_cid_status({"Cid": 3441}) == AlarmStatusEnum.ARMED_STAY


def test_arm_partial_cid():
    assert resolve_cid_status({"Cid": 3456}) == AlarmStatusEnum.ARMED_PARTIAL


# ── unknown / edge cases ────────────────────────────────────────────────────

def test_unknown_cid_returns_none():
    assert resolve_cid_status({"Cid": 9999}) is None


def test_missing_cid_key_returns_none():
    assert resolve_cid_status({}) is None


def test_none_cid_returns_none():
    assert resolve_cid_status({"Cid": None}) is None


def test_string_numeric_cid_is_parsed():
    """String representation of a known CID must still resolve."""
    assert resolve_cid_status({"Cid": "3401"}) == AlarmStatusEnum.ARMED_AWAY


def test_invalid_string_cid_returns_none():
    assert resolve_cid_status({"Cid": "not_a_number"}) is None


def test_zero_cid_returns_none():
    assert resolve_cid_status({"Cid": 0}) is None


def test_negative_cid_returns_none():
    assert resolve_cid_status({"Cid": -1}) is None
