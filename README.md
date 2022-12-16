# TP-Link Easy Smart switches component for Home Assistant

Home Assistant custom component for control TP-Link Easy Smart switches over LAN.

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![License](https://img.shields.io/github/license/vmakeev/hass_tplink_easy_smart)](https://github.com/vmakeev/hass_tplink_easy_smart/blob/master/LICENSE.md)

[![Release](https://img.shields.io/github/v/release/vmakeev/hass_tplink_easy_smart)](https://github.com/vmakeev/hass_tplink_easy_smart/releases/latest)
[![ReleaseDate](https://img.shields.io/github/release-date/vmakeev/hass_tplink_easy_smart)](https://github.com/vmakeev/hass_tplink_easy_smart/releases/latest)
![Maintained](https://img.shields.io/maintenance/yes/2022)

## Key features

- obtaining information about all ports:
  - connection status
  - actual connection speed
  - configured connection speed
- ports management:
  - enable or disable specific ports
- hardware and firmware version of the switch

## Supported models

|                                         Name                                          |  Revision | Confirmed |           Notes                         |
|---------------------------------------------------------------------------------------|-----------|-----------|-----------------------------------------|
| [TL-SG1016PE](https://www.tp-link.com/en/business-networking/poe-switch/tl-sg1016pe/) |     V1    |    Yes    | All features are available              |
| Other Easy Smart switches with web-based user interface                               | --------- |    No     | Will most likely work                   

## Installation

### Manual

Copy `tplink_easy_smart` folder from [latest release](https://github.com/vmakeev/hass_tplink_easy_smart/releases/latest) to `custom_components` folder in your Home Assistant config folder and restart Home Assistant. The final path to folder should look like this: `<home-assistant-config-folder>/custom_components/tplink_easy_smart`.

### HACS

[Add a custom repository](https://hacs.xyz/docs/faq/custom_repositories/) `https://github.com/vmakeev/hass_tplink_easy_smart` with `Integration` category to [HACS](https://hacs.xyz/) and restart Home Assistant.

## Configuration

Configuration > [Integrations](https://my.home-assistant.io/redirect/integrations/) > Add Integration > [TP-Link Easy Smart](https://my.home-assistant.io/redirect/config_flow_start/?domain=tplink_easy_smart)


## Sensors

### Network information

The component allows you to get the network information of the switch. 
The sensor value is the IP address of the switch.

There is one sensor that is always present:
* `sensor.<integration_name>_network_info`

The sensor exposes the following attributes:

|     Attribute     |          Description          |
|-------------------|-------------------------------|
| `mac`             | The MAC address or the switch |
| `gateway`         | Default gateway               |
| `netmask`         | Subnet mask                   |


## Binary sensors

### Port status

The component allows you to get the status of each port.

There are several sensors that are always present:
* `binary_sensor.<integration_name>_port_<port_number>_state`

Each sensor exposes the following attributes:

|     Attribute        |          Description         |
|----------------------|------------------------------|
| `number`             | The number of the port       |
| `speed`              | Actual connection speed*     |
| `speed_config`       | Configured connection speed* |

\* the connection speed is represented by the following values:

|    Value    |        Description        |
|-------------|---------------------------|
| `Link Down` | The link is down          |
| `Auto`      | Automatic speed selection |
| `10MH`      | 10 Mbps, half-duplex      |
| `10MF`      | 10 Mbps, full duplex      |
| `100MH`     | 100 Mbps, half-duplex     |
| `100MF`     | 100 Mbps, full duplex     |
| `1000MF`    | 1000 Mbps, full duplex    |

_Note: The sensor will be unavailable if the port is not enabled (see [port state switch](#port-state))._

## Switches

### Port state

The component allows you to enable and disable each port.

There are several switches that are always present:
* `switch.<integration_name>_port_<port_number>_enabled`

_Note: these switches are not enabled by default. If you need to use this feature, please enable it manually. Don't use this feature if you don't know what you are doing._
