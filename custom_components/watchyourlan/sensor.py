"""Support for WatchYourLAN sensors."""
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, ICON

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up WatchYourLAN sensors from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    options = entry.options

    # Possibly some sensors are always added (like network-level stats):
    entities = []
    entities.append(WatchYourLANTotalDevicesSensor(coordinator))
    entities.append(WatchYourLANOnlineDevicesSensor(coordinator))
    entities.append(WatchYourLANOfflineDevicesSensor(coordinator))
    # Mark these two as "diagnostic" just as an example
    diag_known = WatchYourLANKnownDevicesSensor(coordinator)
    diag_known._attr_entity_category = EntityCategory.DIAGNOSTIC
    diag_unknown = WatchYourLANUnknownDevicesSensor(coordinator)
    diag_unknown._attr_entity_category = EntityCategory.DIAGNOSTIC
    entities.append(diag_known)
    entities.append(diag_unknown)

    # If you create a sensor per host, limit it to only "devices_to_track"
    devices_to_track = options.get("devices_to_track", [])
    for host in coordinator.data.get("hosts", []):
        mac = host.get("mac")
        if mac and mac in devices_to_track:
            # Example: a custom sensor per device
            entities.append(WatchYourLANHostSignalSensor(coordinator, host))
            # etc. (Any other per-host sensors you want)

    async_add_entities(entities, True)


class WatchYourLANBaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for WatchYourLAN sensors."""

    def __init__(self, coordinator, name_suffix, entity_id_suffix):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._name = f"WatchYourLAN {name_suffix}"
        self._unique_id = f"watchyourlan_{entity_id_suffix}"
        self._state = None
        self._attr_icon = ICON

    @property
    def name(self):
        """Return the sensor name."""
        return self._name

    @property
    def unique_id(self):
        """Return a unique ID for this entity."""
        return self._unique_id

    @property
    def native_value(self):
        """Return the sensor's state."""
        return self._state


class WatchYourLANTotalDevicesSensor(WatchYourLANBaseSensor):
    """Sensor for total number of devices."""

    def __init__(self, coordinator):
        super().__init__(coordinator, "Total Devices", "total_devices")
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

    def __init__(self, coordinator):
        super().__init__(coordinator, "Online Devices", "online_devices")
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

    def __init__(self, coordinator):
        super().__init__(coordinator, "Offline Devices", "offline_devices")
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

    def __init__(self, coordinator):
        super().__init__(coordinator, "Known Devices", "known_devices")
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

    def __init__(self, coordinator):
        super().__init__(coordinator, "Unknown Devices", "unknown_devices")
        self._update_state()

    @callback
    def _handle_coordinator_update(self):
        self._update_state()
        self.async_write_ha_state()

    def _update_state(self):
        hosts = self.coordinator.data.get("hosts", [])
        self._state = sum(1 for h in hosts if not h.get("known"))


#
# Example custom sensor for each host (if desired):
#
class WatchYourLANHostSignalSensor(CoordinatorEntity, SensorEntity):
    """Example per-host sensor, only added if user chooses the host in Options."""

    def __init__(self, coordinator, host_data):
        super().__init__(coordinator)
        self._mac = host_data.get("mac")
        self._name = host_data.get("name") or self._mac
        self._attr_icon = "mdi:wifi"  # or whatever
        self._attr_unique_id = f"watchyourlan_signal_{self._mac}"
        self._state = None  # set by update
        # If you want this sensor under Diagnostics:
        # self._attr_entity_category = EntityCategory.DIAGNOSTIC

        # Example attribute for the IP
        self._ip = host_data.get("ip")

    @property
    def name(self):
        """Return the entity name."""
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

    @callback
    def _handle_coordinator_update(self):
        """Handle updated data from the coordinator."""
        # Re-find our host in coordinator data
        for host in self.coordinator.data.get("hosts", []):
            if host.get("mac") == self._mac:
                # Suppose we have some custom signal data in host
                self._state = host.get("signal", 100)  # or None if not provided
                self._ip = host.get("ip", self._ip)
                break

        self.async_write_ha_state()
