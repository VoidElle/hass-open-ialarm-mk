# Coding Agent Instructions — hass-open-ialarm-mk

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
  coordinator.py       # DataUpdateCoordinator — polls status + zones, exposes arm/disarm commands
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
- Use `DataUpdateCoordinator` for all polling — do not poll in entity `async_update`.
- Raise `ConfigEntryNotReady` on connection failure during setup.
- Raise `UpdateFailed` inside `_async_update_data` on poll errors.
- Register entities via `async_forward_entry_setups` — never directly.
- Use `entry.async_on_unload` for cleanup hooks.

### Local API (`open-ialarm-mk-local-api`)
- Client: `IAlarmMkClient(host, port, username, password, keepalive_interval=None)`
- Key exceptions: `IAlarmMkConnectionError`, `IAlarmMkLoginError`
- Key models: `AlarmStatusModel`, `ZoneModel`, `NetworkInfoModel`
- Panel MAC (from `get_network_info()`) is the unique ID — never use IP/host.
- Commands: `arm_away()`, `arm_stay()`, `arm_partial()`, `disarm()`, `cancel_alarm()`
- Push events via `client.on_event` callback → trigger `async_request_refresh()`.

### Coordinator (`IAlarmMkCoordinator`)
- Polls `get_status()` + `get_zones()` in parallel with `asyncio.gather`.
- Data type: `IAlarmMkData(status, zones)`.
- All arm/disarm methods call `async_request_refresh()` after the command.
- Shutdown: `async_shutdown()` calls `client.disconnect()`.

### Config & Constants
- Config keys: `CONF_HOST`, `CONF_PORT`, `CONF_USERNAME`, `CONF_PASSWORD` (from HA), `CONF_SCAN_INTERVAL` (custom).
- Defaults: `DEFAULT_PORT = 8000`, `DEFAULT_SCAN_INTERVAL = 30`.
- Scan interval valid range: 10–300 seconds.
- `single_config_entry: true` — only one panel per HA instance.

### Entities
- **Alarm control panel** states: `armed_away`, `armed_home`, `armed_custom_bypass`, `disarmed`, `triggered`, `arming`, `unavailable`.
- **Binary sensors**: one per zone, device class auto-detected from `zone_type` + name keywords (`door`/`porta` → door, `motion`/`pir`/`intern` → motion, type 3 → motion, type 4/5 → problem, type 6 + `gas` → gas, type 6 other → smoke, fallback → opening).
- Zone attributes: `bypass`, `low_battery`, `signal_loss`, `zone_type`, `zone_index`.

## Code Style
- Python 3.12+, async/await throughout.
- `from __future__ import annotations` in every module.
- Logger: `_LOGGER = logging.getLogger(__name__)`.
- No `configuration.yaml` support — UI-only config flow.
- Keep strings in `strings.json` + `translations/`; never hardcode UI text.

## Adding a New Platform
1. Add the `Platform.*` constant to `PLATFORMS` in `__init__.py`.
2. Create `<platform>.py` following existing `alarm_control_panel.py` / `binary_sensor.py` patterns.
3. Entities read data from `coordinator.data` — never call the client directly from an entity.

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
