# Architecture

## Overview

The integration uses two separate persistent TCP connections to the panel on port 8000.

```
Home Assistant
    |
    +-- IAlarmMkClient (command connection)
    |       Polling: get_status, get_zones
    |       Commands: arm_away, arm_stay, arm_partial, disarm, cancel_alarm
    |
    +-- IAlarmMkPushClient (push connection)
            Real-time events: CID push frames from panel
            Keepalive: %%maI ping every 60 s
```

Both clients are created in `async_setup_entry` (`__init__.py`) and live for the lifetime of the config entry.

---

## Entry Setup Flow

```
async_setup_entry
    1. Create IAlarmMkClient
    2. Connect + get_network_info (MAC, IP, name) -- used as unique ID and device info
    3. Create IAlarmMkCoordinator
    4. First refresh (populates coordinator.data before entities register)
    5. Forward entry setup to all platforms
    6. Create IAlarmMkPushClient, start subscription task
```

On unload (`async_unload_entry`) the coordinator `async_shutdown` cancels the push task and disconnects both clients.

---

## Coordinator

`IAlarmMkCoordinator` extends `DataUpdateCoordinator[IAlarmMkData]`.

**Poll** (`_async_update_data`): fetches `get_status` and `get_zones` in parallel via `asyncio.gather`.  
**Push** (`_on_push_event`): called by the push client on the event loop; decodes the CID code and calls `async_set_updated_data` directly, bypassing the poll timer.

`IAlarmMkData` holds:
- `status: AlarmStatusModel` -- current armed/disarmed/triggered state
- `zones: list[ZoneModel]` -- all zone states

---

## Data Flow

```
Panel push event (CID frame)
    -> IAlarmMkPushClient.data_received
    -> coordinator._on_push_event
    -> resolve_cid_status (panel_events.py)
        known CID -> async_set_updated_data (instant HA state update)
        unknown CID -> async_refresh (full poll as fallback)

Poll timer fires
    -> coordinator._async_update_data
    -> get_status + get_zones in parallel
    -> async_set_updated_data via DataUpdateCoordinator
```

---

## Platforms

| Platform | File | Entities |
|---|---|---|
| `alarm_control_panel` | `alarm_control_panel.py` | `IAlarmMkPanel` |
| `binary_sensor` | `binary_sensor.py` | `IAlarmMkCommandConnectionSensor`, `IAlarmMkPushConnectionSensor`, `IAlarmMkZoneSensor` (one per active zone) |
| `sensor` | `sensor.py` | `IAlarmMkLastPollSensor`, `IAlarmMkPanelIpSensor` |
| `button` | `button.py` | `IAlarmMkCancelAlarmButton` |

All entities inherit `CoordinatorEntity` and are updated whenever the coordinator publishes new data.

---

## Config Flow

`IAlarmMk7ConfigFlow` supports two steps:

- `async_step_user`: initial setup. Connects to panel, retrieves MAC as unique ID, aborts if already configured.
- `async_step_reconfigure`: update credentials/host. Reconnects to verify, aborts if MAC changed (different panel).

Unique ID is the formatted MAC address from `get_network_info`.
