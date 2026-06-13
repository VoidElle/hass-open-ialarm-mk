# Entities

## Alarm Control Panel

**Entity:** `alarm_control_panel.<device_name>`  
**Class:** `IAlarmMkPanel`  
**Unique ID:** `<mac>_alarm_panel`

### States

| HA state | `AlarmStatusEnum` | Description |
|---|---|---|
| `armed_away` | `ARMED_AWAY` | All zones active |
| `armed_home` | `ARMED_STAY` | Stay / perimeter mode |
| `armed_custom_bypass` | `ARMED_PARTIAL` | Partial arming mode |
| `disarmed` | `DISARMED` | Panel disarmed |
| `disarmed` | `CANCEL` | Alarm cancelled (maps to disarmed) |
| `triggered` | `TRIGGERED` | Alarm sounding |
| `arming` | `ALARM_ARMING` | Panel is arming |
| `unavailable` | `UNAVAILABLE` or no data | Transitioning or unreachable |

### Supported features

`ARM_HOME`, `ARM_AWAY`, `ARM_CUSTOM_BYPASS`. No code required (`code_arm_required = False`).

---

## Zone Binary Sensors

**Class:** `IAlarmMkZoneSensor`  
**Unique ID:** `<mac>_zone_<index>`  
**Created:** one per zone where `IN_USE` flag is set or a name is configured.

### State

- `on`: zone open or faulted
- `off`: zone closed or normal
- `unavailable`: zone no longer in use, or `IN_USE` flag cleared (e.g. "Check magnets" disabled in iAlarm app)

### Attributes

| Attribute | Type | Description |
|---|---|---|
| `bypass` | bool | Zone is bypassed |
| `low_battery` | bool | Zone sensor has low battery |
| `signal_loss` | bool | Wireless zone signal lost |
| `zone_type` | int | Raw zone type from panel |
| `zone_index` | int | Zone number (1-based) |

### Device class detection

| Zone type | Name contains | Device class |
|---|---|---|
| 1, 2 | `door`, `porta` | `door` |
| 1, 2 | `motion`, `pir`, `intern`, `movimento` | `motion` |
| 1, 2 | (other) | `window` |
| 3 | (any) | `motion` |
| 4, 5 | (any) | `problem` |
| 6 | `gas` | `gas` |
| 6 | (other) | `smoke` |
| (other) | (any) | `opening` |

New zones are discovered automatically on each poll without reloading the integration.

---

## Diagnostic Binary Sensors

### Command Connection

**Class:** `IAlarmMkCommandConnectionSensor`  
**Unique ID:** `<mac>_command_connection`  
`is_on` reflects `coordinator.last_update_success`.

### Push Connection

**Class:** `IAlarmMkPushConnectionSensor`  
**Unique ID:** `<mac>_push_connection`  
`is_on` reflects `coordinator.push_connected` (whether the dedicated push TCP connection is established and alive).

---

## Diagnostic Sensors

### Panel IP

**Class:** `IAlarmMkPanelIpSensor`  
**Unique ID:** `<mac>_panel_ip`  
IP address reported by the panel via `get_network_info` at setup. Static; does not update after setup.

---

## Button

### Cancel Alarm

**Class:** `IAlarmMkCancelAlarmButton`  
**Unique ID:** `<mac>_cancel_alarm`  
Sends `cancel_alarm` to the panel. Silences the siren and cancels the triggered state without fully disarming. If the panel rejects the command a `HomeAssistantError` is raised and shown in the UI.
