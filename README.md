# WatchYourLAN Integration for Home Assistant

This integration connects to a [WatchYourLAN](https://github.com/aceberg/WatchYourLAN) instance to provide device tracking and network monitoring in Home Assistant.

**Note:** This integration requires that you already have a WatchYourLAN instance set up and running. Please visit the [official WatchYourLAN GitHub repository](https://github.com/aceberg/WatchYourLAN) for installation instructions of the WatchYourLAN service itself.

*This integration was created with the assistance of Claude, Anthropic's AI assistant.*

## Features

- **Device Presence Detection**: Track when devices connect to or disconnect from your network
- **Network Status**: Monitor total, online, offline, known, and unknown devices
- **Device Tracking**: Use WatchYourLAN data for device_tracker entities
- **Detailed Information**: View device details including MAC address, IP address, vendor, and more

## Installation

### HACS (Recommended)

1. Ensure [HACS](https://hacs.xyz/) is installed
2. Add this repository as a custom repository in HACS:
   - Go to HACS → Integrations
   - Click the three dots in the top right corner
   - Select "Custom repositories"
   - Add the URL of this repository
   - Category: Integration
3. Click "Install" on the WatchYourLAN integration

### Manual Installation

1. Download the latest release
2. Copy the `watchyourlan` folder to `custom_components` in your Home Assistant configuration directory
3. Restart Home Assistant

## Configuration

### Via UI

1. Go to Configuration → Integrations
2. Click the "+ Add Integration" button
3. Search for "WatchYourLAN"
4. Enter the host and port of your WatchYourLAN instance
5. Set your preferred scan interval

### Via Configuration.yaml

Add the following to your `configuration.yaml`:

```yaml
watchyourlan:
  host: 192.168.1.x  # IP address of your WatchYourLAN instance
  port: 8840         # Port (default is 8840)
  scan_interval: 60  # Scan interval in seconds
```

## Entities

This integration creates the following entities:

### Sensors
- `sensor.watchyourlan_total_devices`: Total number of devices
- `sensor.watchyourlan_online_devices`: Number of online devices
- `sensor.watchyourlan_offline_devices`: Number of offline devices
- `sensor.watchyourlan_known_devices`: Number of known devices
- `sensor.watchyourlan_unknown_devices`: Number of unknown devices

### Binary Sensors
- `binary_sensor.watchyourlan_DEVICE_NAME`: Connection status for each device (on = connected)

### Device Trackers
- `device_tracker.watchyourlan_tracker_DEVICE_NAME`: Device tracker entity for each device

## Automation Examples

### Notify when an unknown device connects

```yaml
automation:
  - alias: "Unknown Device Alert"
    trigger:
      - platform: state
        entity_id: sensor.watchyourlan_unknown_devices
    condition:
      - condition: numeric_state
        entity_id: sensor.watchyourlan_unknown_devices
        above: 0
    action:
      - service: notify.mobile_app
        data:
          title: "Unknown Device Alert"
          message: "An unknown device is connected to your network!"
```

### Turn on lights when a specific device connects

```yaml
automation:
  - alias: "Turn on lights when phone connects"
    trigger:
      - platform: state
        entity_id: binary_sensor.watchyourlan_my_phone
        from: "off"
        to: "on"
    action:
      - service: light.turn_on
        target:
          entity_id: light.living_room
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.