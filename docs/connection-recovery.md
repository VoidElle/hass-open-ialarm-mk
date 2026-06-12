# Connection Recovery

## The Pairing-Lock Problem

### Symptom

After running for a while, the alarm panel entity shows "Not available" in Home Assistant.
Manually reloading the integration (Settings > Devices & Services > iAlarm-MK > Reload) fixes it immediately.

### What happens

The panel firmware silently ignores `Pair/Client` authentication frames when it already has an active authenticated session. The push client holds one such session. After the command client's TCP connection drops and it tries to reconnect, every pairing attempt times out:

```
TCP connect -> OK
Send Pair/Client -> (no reply for 10 s) -> Connection timed out
Disconnect -> retry -> repeat
```

Meanwhile the push client stays healthy, sending keepalive pings every 60 s and receiving acknowledgements.

### Why entities go unavailable

`DataUpdateCoordinator` sets `last_update_success = False` after the first `UpdateFailed`. Since all `CoordinatorEntity` subclasses return `self.coordinator.last_update_success` from their `available` property, every entity flips to unavailable.

### Log signature

```
DEBUG  meian_client  login: TCP connection established
DEBUG  meian_client  login: sending Pair/Client (token=...)
ERROR  ialarmmk_client  _run: reconnect failed: Connection timed out
DEBUG  coordinator  Finished fetching open_ialarm_mk data in 20.0 seconds (success: False)
DEBUG  meian_push_client  _keepalive: sending %%maI ping       <- push still alive
DEBUG  meian_push_client  data_received: keepalive acknowledged by panel
```

---

## Detection

The combination of two conditions precisely identifies this failure mode:

| Condition | Meaning |
|---|---|
| `UpdateFailed` raised in `_async_update_data` | Command connection failed |
| `coordinator.push_connected == True` | Push connection is alive, panel is reachable |

If the panel were genuinely offline both clients would be dead and `push_connected` would be `False`. In that case "Not available" is the correct state and no reload is attempted.

---

## Self-Healing

`coordinator._handle_poll_failure` is called whenever `_async_update_data` catches a connection or login error. When `push_connected` is `True` it schedules an integration reload:

```python
self.hass.async_create_task(
    self.hass.config_entries.async_reload(self.entry.entry_id)
)
```

The reload calls `async_unload_entry` (cleanly closes both sockets) followed by `async_setup_entry` (opens fresh connections). After a clean disconnect the panel accepts the new pairing and both clients reconnect successfully.

Recovery happens within one poll cycle of entering the broken state (default 30 s).
