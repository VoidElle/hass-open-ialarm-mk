# Coding Agent Instructions - hass-open-ialarm-mk

## Project Overview

Home Assistant custom integration for **iAlarm-MK** alarm panels (confirmed on MK7). Communicates via local TCP using the `open-ialarm-mk-local-api` Python library. HACS-compatible.

- **Domain:** `open_ialarm_mk`
- **Platforms:** `alarm_control_panel`, `binary_sensor`
- **IoT class:** `local_polling`
- **Min HA version:** 2024.1

## Repository Layout

```
custom_components/open_ialarm_mk/
  __init__.py          # Entry setup/unload, ConfigEntry lifecycle
  coordinator.py       # DataUpdateCoordinator - polls status + zones, exposes arm/disarm commands
  alarm_control_panel.py
  binary_sensor.py
  config_flow.py       # UI config + reconfigure flows
  const.py             # DOMAIN, defaults, config keys
  manifest.json        # Integration metadata, requirements
  strings.json         # UI strings (en)
  translations/        # Per-locale strings
```

## Key Patterns & Conventions

### Home Assistant Integration Standards
- Follow [HA developer guidelines](https://developers.home-assistant.io/).
- All I/O must be async. Never block the event loop.
- Use `DataUpdateCoordinator` for all polling - do not poll in entity `async_update`.
- Raise `ConfigEntryNotReady` on connection failure during setup.
- Raise `UpdateFailed` inside `_async_update_data` on poll errors.
- Register entities via `async_forward_entry_setups` - never directly.
- Use `entry.async_on_unload` for cleanup hooks.

### Local API (`open-ialarm-mk-local-api`)

**Public surface (all exported from package root):**

| Symbol | Type | Notes |
|---|---|---|
| `IAlarmMkClient` | async command client | wraps blocking `MeianClient` via executor |
| `IAlarmMkPushClient` | push-only subscriber | only needed without a persistent command connection |
| `AlarmStatusEnum` | `IntEnum` | see values below |
| `ZoneStatusEnum` | `IntFlag` | bitmask, see values below |
| `AlarmStatusModel` | dataclass | `status: AlarmStatusEnum` |
| `ZoneModel` | dataclass | `index`, `name`, `zone_type`, `status: ZoneStatusEnum` + properties below |
| `NetworkInfoModel` | dataclass | `mac`, `name`, `ip`; built via `from_dict(data)` |
| `IAlarmMkConnectionError` | exception | TCP/socket failure |
| `IAlarmMkLoginError` | exception | auth failure |
| `IAlarmMkAlarmError` | exception | panel-level alarm error |

**`IAlarmMkClient` constructor:**
```python
IAlarmMkClient(host, port, username, password, timeout=10.0, keepalive_interval=None)
```
- HA uses `keepalive_interval=None` (coordinator polling replaces keepalive).
- Supports async context manager (`async with`).
- Internal `asyncio.Lock` serialises all commands - concurrent callers are safe.
- Auto-reconnects once on `IAlarmMkConnectionError` before re-raising.

**`IAlarmMkClient` methods:**
| Method | Notes |
|---|---|
| `connect()` | login + start keepalive |
| `disconnect()` | stop keepalive + logout |
| `get_status() → AlarmStatusModel` | polls `GetAlarmStatus` |
| `get_network_info() → NetworkInfoModel` | polls `GetNet`; use MAC as unique ID |
| `get_zones() → list[ZoneModel]` | polls `GetZone`; skips `None` entries |
| `arm_away()` | `SetAlarmStatus` code `0` |
| `disarm()` | `SetAlarmStatus` code `1` |
| `arm_stay()` | `SetAlarmStatus` code `2` |
| `cancel_alarm()` | `SetAlarmStatus` code `3` |
| `arm_partial()` | `SetAlarmStatus` code `8` |
| `on_event` (property) | set to `Callable[[dict], None]`; called from worker thread on unsolicited panel push events |

**`AlarmStatusEnum` values:**
```python
ARMED_AWAY = 0
DISARMED = 1
ARMED_STAY = 2
CANCEL = 3
TRIGGERED = 4
ALARM_ARMING = 5
UNAVAILABLE = 6
ARMED_PARTIAL = 8
```

**`ZoneStatusEnum` (IntFlag bitmask):**
```python
NOT_USED = 0
IN_USE = 1 << 0
ALARM = 1 << 1
BYPASS = 1 << 2
FAULT = 1 << 3
LOW_BATTERY = 1 << 4
LOSS = 1 << 5
```

**`ZoneModel` computed properties:**
- `is_open` → `IN_USE & FAULT` both set
- `is_bypassed` → `BYPASS` set
- `low_battery` → `LOW_BATTERY` set
- `signal_loss` → `LOSS` set

**`IAlarmMkPushClient`:** dedicated push-only TCP connection (separate port, typically 18034). Not used in the HA integration because `IAlarmMkClient.on_event` already receives push events on the command connection.

**Protocol internals (Meian XML over TCP):**
- XPath-keyed XML frames, length-prefixed values (`STR`, `S32`, `BOL`, `PWD`, `TYP`, etc.).
- XPath constants live in `_internal/paths.py`.
- Never depend on `_internal` from the HA integration - use the public API only.

### Coordinator (`IAlarmMkCoordinator`)
- Polls `get_status()` + `get_zones()` in parallel with `asyncio.gather`.
- Data type: `IAlarmMkData(status, zones)`.
- All arm/disarm methods call `async_request_refresh()` after the command.
- Shutdown: `async_shutdown()` calls `client.disconnect()`.

### Config & Constants
- Config keys: `CONF_HOST`, `CONF_PORT`, `CONF_USERNAME`, `CONF_PASSWORD` (from HA), `CONF_SCAN_INTERVAL` (custom).
- Defaults: `DEFAULT_PORT = 8000`, `DEFAULT_SCAN_INTERVAL = 30`.
- Scan interval valid range: 10–300 seconds.
- `single_config_entry: true` - only one panel per HA instance.

### Entities
- **Alarm control panel** states: `armed_away`, `armed_home`, `armed_custom_bypass`, `disarmed`, `triggered`, `arming`, `unavailable`.
- **Binary sensors**: one per zone, device class auto-detected from `zone_type` + name keywords (`door`/`porta` → door, `motion`/`pir`/`intern` → motion, type 3 → motion, type 4/5 → problem, type 6 + `gas` → gas, type 6 other → smoke, fallback → opening).
- Zone attributes: `bypass`, `low_battery`, `signal_loss`, `zone_type`, `zone_index`.

## Code Style
- Python 3.12+, async/await throughout.
- `from __future__ import annotations` in every module.
- Logger: `_LOGGER = logging.getLogger(__name__)`.
- No `configuration.yaml` support - UI-only config flow.
- Keep strings in `strings.json` + `translations/`; never hardcode UI text.

## Adding a New Platform
1. Add the `Platform.*` constant to `PLATFORMS` in `__init__.py`.
2. Create `<platform>.py` following existing `alarm_control_panel.py` / `binary_sensor.py` patterns.
3. Entities read data from `coordinator.data` - never call the client directly from an entity.

## Testing & Validation
- Run against a real MK7 panel or a mock TCP server implementing the iAlarm-MK protocol.
- Enable debug logging for integration + library during testing:
  ```yaml
  logger:
    logs:
      custom_components.open_ialarm_mk: debug
      open_ialarm_mk_local_api: debug
  ```

## Translations
- Source of truth: `strings.json` (English).
- Each locale lives in `translations/<lang>.json` with identical key structure.
- When adding new config/option keys, update both `strings.json` and all existing translation files.

## Release Checklist
- Bump `version` in `manifest.json`.
- Update `requirements` if `open-ialarm-mk-local-api` version changes.
- Tag release on GitHub so HACS picks it up.
