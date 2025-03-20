"""Support for WatchYourLAN sensors."""
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import EntityCategory

from .const import DOMAIN, ICON

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up WatchYourLAN sensors from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    options = entry.options
    entry_id = entry.entry_id  # We'll pass this to each sensor

    entities = []

    # Some integration-wide sensors
    entities.append(WatchYourLANTotalDevicesSensor(coordinator, entry_id))
    entities.append(WatchYourLANOnlineDevicesSensor(coordinator, entry_id))
    entities.append(WatchYourLANOfflineDevicesSensor(coordinator, entry_id))

    # Mark these two as DIAGNOSTIC, just as an example
    diag_known = WatchYourLANKnownDevicesSensor(coordinator, entry_id)
    diag_known._attr_entity_category = EntityCategory.DIAGNOSTIC
    diag_unknown = WatchYourLANUnknownDevicesSensor(coordinator, entry_id)
    diag_unknown._attr_entity_category = EntityCategory.DIAGNOSTIC

    entities.append(diag_known)
    entities.append(diag_unknown)

    # Only create per-host sensors for devices user selected in Options
    devices_to_track = options.get("devices_to_track", [])
    for host in coordinator.data.get("hosts", []):
        mac = host.get("mac")
        if mac and mac in devices_to_track:
            # Example of a per-host sensor
            entities.append(WatchYourLANHostSignalSensor(coordinator, entry_id, host))

    async_add_entities(entities, True)


class WatchYourLANBaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for WatchYourLAN sensors that belong to one device: the 'server'."""

    def __init__(self, coordinator, entry_id, name_suffix, entity_id_suffix):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry_id = entry_id
        self._name = f"WatchYourLAN {name_suffix}"
        self._unique_id = f"watchyourlan_{entry_id}_{entity_id_suffix}"
        self._state = None
        self._attr_icon = ICON

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def native_value(self):
        return self._state

    @property
    def device_info(self):
        """Group all these sensors under one device: the 'WatchYourLAN Server'."""
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": "WatchYourLAN Server",
            "manufacturer": "WatchYourLAN",
            "model": "Network Gateway",
        }


class WatchYourLANTotalDevicesSensor(WatchYourLANBaseSensor):
    """Sensor for total number of devices."""

    def __init__(self, coordinator, entry_id):
        super().__init__(coordinator, entry_id, "Total Devices", "total_devices")
        self._update_state()

    @callback
    def _handle_coordinator_update(self):
        self._update_state()
        self.async_write_ha_state()

    def _update_state(self):
        hosts = self.coordinator.data.get("hosts", [])
        self._state = len(hosts)


class WatchYourLANOnlineDevicesSensor(WatchYourLANBaseSensor):
    """Sensor for number of online devices."""

    def __init__(self, coordinator, entry_id):
        super().__init__(coordinator, entry_id, "Online Devices", "online_devices")
        self._update_state()

    @callback
    def _handle_coordinator_update(self):
        self._update_state()
        self.async_write_ha_state()

    def _update_state(self):
        hosts = self.coordinator.data.get("hosts", [])
        self._state = sum(1 for h in hosts if h.get("online"))


class WatchYourLANOfflineDevicesSensor(WatchYourLANBaseSensor):
    """Sensor for number of offline devices."""

    def __init__(self, coordinator, entry_id):
        super().__init__(coordinator, entry_id, "Offline Devices", "offline_devices")
        self._update_state()

    @callback
    def _handle_coordinator_update(self):
        self._update_state()
        self.async_write_ha_state()

    def _update_state(self):
        hosts = self.coordinator.data.get("hosts", [])
        self._state = sum(1 for h in hosts if not h.get("online"))


class WatchYourLANKnownDevicesSensor(WatchYourLANBaseSensor):
    """Sensor for number of known devices."""

    def __init__(self, coordinator, entry_id):
        super().__init__(coordinator, entry_id, "Known Devices", "known_devices")
        self._update_state()

    @callback
    def _handle_coordinator_update(self):
        self._update_state()
        self.async_write_ha_state()

    def _update_state(self):
        hosts = self.coordinator.data.get("hosts", [])
        self._state = sum(1 for h in hosts if h.get("known"))


class WatchYourLANUnknownDevicesSensor(WatchYourLANBaseSensor):
    """Sensor for number of unknown devices."""

    def __init__(self, coordinator, entry_id):
        super().__init__(coordinator, entry_id, "Unknown Devices", "unknown_devices")
        self._update_state()

    @callback
    def _handle_coordinator_update(self):
        self._update_state()
        self.async_write_ha_state()

    def _update_state(self):
        hosts = self.coordinator.data.get("hosts", [])
        self._state = sum(1 for h in hosts if not h.get("known"))


class WatchYourLANHostSignalSensor(CoordinatorEntity, SensorEntity):
    """Example: A sensor for each tracked host, also under the single 'server' device."""

    def __init__(self, coordinator, entry_id, host_data):
        super().__init__(coordinator)
        self._entry_id = entry_id
        self._mac = host_data.get("mac")
        self._name = host_data.get("name") or self._mac
        self._attr_icon = "mdi:wifi"
        # Unique ID includes the host's mac, to avoid collisions
        self._attr_unique_id = f"watchyourlan_signal_{self._entry_id}_{self._mac}"
        self._state = None
        self._ip = host_data.get("ip")

    @property
    def name(self):
        return f"Signal for {self._name}"

    @property
    def native_value(self):
        return self._state

    @property
    def extra_state_attributes(self):
        return {
            "mac": self._mac,
            "ip": self._ip,
        }

    @property
    def device_info(self):
        """Also belongs to the single 'server' device."""
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": "WatchYourLAN Server",
            "manufacturer": "WatchYourLAN",
            "model": "Network Gateway",
        }

    @callback
    def _handle_coordinator_update(self):
        """Update from coordinator data."""
        for host in self.coordinator.data.get("hosts", []):
            if host.get("mac") == self._mac:
                # Suppose signal is in host["signal"]; if not, pick something else
                self._state = host.get("signal", 100)
                self._ip = host.get("ip", self._ip)
                break
        self.async_write_ha_state()
