"""Panel push event handling for iAlarm-MK."""
from __future__ import annotations

import logging

from open_ialarm_mk_local_api import AlarmStatusEnum

_LOGGER = logging.getLogger(__name__)

# Maps panel push event CID codes to AlarmStatusEnum values.
# Source: iAlarm Contact ID protocol codes observed on MK panels.
_CID_STATUS_MAP: dict[int, AlarmStatusEnum] = {
    1100: AlarmStatusEnum.TRIGGERED,      # Emergency / panic
    1110: AlarmStatusEnum.TRIGGERED,      # Fire alarm
    1120: AlarmStatusEnum.TRIGGERED,      # Panic alarm
    1130: AlarmStatusEnum.TRIGGERED,      # Burglar alarm
    1131: AlarmStatusEnum.TRIGGERED,      # Perimeter alarm
    1132: AlarmStatusEnum.TRIGGERED,      # Interior alarm
    1133: AlarmStatusEnum.TRIGGERED,      # 24h zone alarm
    1134: AlarmStatusEnum.TRIGGERED,      # Entry/exit alarm
    1401: AlarmStatusEnum.DISARMED,       # Disarm report
    1406: AlarmStatusEnum.DISARMED,       # Alarm cancelled
    3401: AlarmStatusEnum.ARMED_AWAY,     # Arm away report
    3441: AlarmStatusEnum.ARMED_STAY,     # Arm stay report
    3456: AlarmStatusEnum.ARMED_PARTIAL,  # Arm partial report
}


def resolve_cid_status(event: dict) -> AlarmStatusEnum | None:
    """Return the AlarmStatusEnum for a push event CID, or None if unrecognised."""
    try:
        cid = int(event.get("Cid", -1))
    except (TypeError, ValueError):
        return None
    status = _CID_STATUS_MAP.get(cid)
    if status is not None:
        _LOGGER.debug("Push CID %d -> %s", cid, status.name)
    else:
        _LOGGER.debug("Push CID %d unrecognised, skipping immediate state update", cid)
    return status
