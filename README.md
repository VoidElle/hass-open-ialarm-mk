<div align="center">
  <img src="./assets/logo.png" alt="Logo" height="200">
  <br>
  <h1>🔒 Open iAlarm-MK</h1>
  <p><em>Home Assistant integration for iAlarm-MK alarm panels via local API</em></p>
  <br>
  <a href="https://github.com/VoidElle/open-ialarm-mk-local-api"><img src="https://img.shields.io/badge/open--ialarm--mk--local--api-v1.0.0-blue?style=flat-square&logo=github" alt="open-ialarm-mk-local-api"></a>
  <a href="https://github.com/VoidElle/hass-open-ialarm-mk-7/releases"><img src="https://img.shields.io/github/v/release/VoidElle/hass-open-ialarm-mk-7?style=flat-square&label=version" alt="version"></a>
  <a href="https://github.com/VoidElle/hass-open-ialarm-mk-7/blob/master/LICENSE"><img src="https://img.shields.io/github/license/VoidElle/hass-open-ialarm-mk-7?style=flat-square" alt="license"></a>
  <br>
  <a href="https://hacs.xyz"><img src="https://img.shields.io/badge/HACS-Custom-orange?style=flat-square&logo=home-assistant-community-store" alt="HACS"></a>
  <a href="https://www.home-assistant.io/"><img src="https://img.shields.io/badge/Home%20Assistant-%E2%89%A52024.1-41BDF5?style=flat-square&logo=home-assistant" alt="Home Assistant"></a>
  <a href="https://github.com/VoidElle/hass-open-ialarm-mk-7"><img src="https://img.shields.io/badge/IoT%20class-Local%20Polling-green?style=flat-square" alt="IoT class"></a>
  <a href="https://github.com/VoidElle/hass-open-ialarm-mk-7/stargazers"><img src="https://img.shields.io/github/stars/VoidElle/hass-open-ialarm-mk-7?style=flat-square" alt="stars"></a>
  <a href="https://github.com/VoidElle/hass-open-ialarm-mk-7/commits"><img src="https://img.shields.io/github/last-commit/VoidElle/hass-open-ialarm-mk-7?style=flat-square" alt="last commit"></a>
</div>


Open iAlarm-MK is a Home Assistant integration that enables local control and monitoring of **iAlarm-MK** alarm panels through Home Assistant.

Communicates **entirely over your local network** via direct TCP connection to the panel - no cloud, no P2P relay required.

> [!NOTE]
> Support has been confirmed on **MK7** panels. Other MK variants may work but have not been tested.
> For MK2, see [mistermax80/ialarm_mk2](https://github.com/mistermax80/ialarm_mk2).

## Installation 📦

### Via HACS (Recommended) ⭐

[![Open in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=VoidElle&repository=hass-open-ialarm-mk-7&category=integration)

### Via HACS (Manual)

1. Add custom repository:
    - Open HACS in your Home Assistant interface
    - Go to "Integrations" tab
    - Click on the three dots in the top right corner and select "Custom repositories"
    - Enter the repository URL: `https://github.com/VoidElle/hass-open-ialarm-mk-7`
    - Select "Integration" as the category
    - Click "Add"

2. Install the integration:
   - In HACS Integrations, click + Explore & Download Repositories
   - Search for "iAlarm-MK"
   - Click on the integration and then Download
   - Select the latest version and click Download

3. Restart Home Assistant 🔄

### Manual Installation 🔧

1. Copy `custom_components/open_ialarm_mk/` into your `config/custom_components/` directory
2. Restart Home Assistant

## Add the Integration to Home Assistant 🧩

After installing and restarting Home Assistant:

1. Go to **Settings -> Devices & Services**
2. Click **+ Add Integration**
3. Search for **"iAlarm-MK"**
4. Fill in the connection form

## Configuration ⚙️

All configuration is done through the Home Assistant UI - no `configuration.yaml` editing required.

| Field | Description | Default |
|---|---|---|
| **Host** | IP address of the panel | (required) |
| **Port** | TCP port | `8000` |
| **Username** | Panel login username | (required) |
| **Password** | Panel login password | (required) |
| **Poll interval** | How often to refresh state in seconds (10-300) | `30` |

The integration connects to the panel, retrieves the device MAC address as a unique identifier, and sets up all entities automatically.

To update credentials later, use **Reconfigure** from the integration page - no need to remove and re-add.

## Features ✨

- 🔒 **Alarm control panel** - arm away, arm home (stay), arm custom bypass (partial), disarm
- 🚪 **Zone binary sensors** - one sensor per configured zone with automatic device class detection
- 📡 **Fully local** - direct TCP connection to the panel, no internet required
- 🔄 **Configurable poll interval** - 10 to 300 seconds
- 🛠️ **Reconfigurable** - update host and credentials without removing the integration
- 🆔 **Unique ID** - panel MAC address prevents duplicate entries

## Entities 🗂️

### Alarm Control Panel

| State | Description |
|---|---|
| `armed_away` | All zones active |
| `armed_home` | Stay / perimeter mode |
| `armed_custom_bypass` | Partial mode |
| `disarmed` | Panel disarmed |
| `triggered` | Alarm triggered |
| `arming` | Panel is arming |
| `unavailable` | Panel unreachable |

### Zone Binary Sensors

One entity per zone that is in use or has a name configured.

- **State** - `on` = zone open / faulted, `off` = zone closed / normal
- **Attributes:** `bypass`, `low_battery`, `signal_loss`, `zone_type`, `zone_index`

Device class is auto-detected from zone type and name keywords:

| Zone type | Name hint | Device class |
|---|---|---|
| 1 / 2 | `door`, `porta` | Door |
| 1 / 2 | `motion`, `pir`, `intern` | Motion |
| 1 / 2 | other | Window |
| 3 | (any) | Motion |
| 4 / 5 | (any) | Problem |
| 6 | `gas` | Gas |
| 6 | other | Smoke |
| other | (any) | Opening |

## Limitations ⚠️

- Requires local network access (panel must be reachable from Home Assistant)
- Zone sensors are registered once at startup; removing a zone requires reloading the integration

## Contributing 🤝

Contributions are welcome!

### How to Help
- 🐛 **Report bugs** via [GitHub Issues](https://github.com/VoidElle/hass-open-ialarm-mk-7/issues)
- 🌍 **Translate** to more languages
- 🔧 **Submit PRs** for improvements via [GitHub Pull Requests](https://github.com/VoidElle/hass-open-ialarm-mk-7/pulls)
- 📖 **Improve documentation**

### Development

1. Fork and clone the repository
2. Create a feature branch: `git checkout -b feature/name`
3. Follow [Home Assistant dev guidelines](https://developers.home-assistant.io/)
4. Submit a PR with a clear description
