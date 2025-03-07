"""Support for WatchYourLAN sensors."""
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, ICON

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up WatchYourLAN sensors from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities = []
    entities.append(WatchYourLANTotalDevicesSensor(coordinator))
    entities.append(WatchYourLANOnlineDevicesSensor(coordinator))
    entities.append(WatchYourLANOfflineDevicesSensor(coordinator))
    entities.append(WatchYourLANKnownDevicesSensor(coordinator))
    entities.append(WatchYourLANUnknownDevicesSensor(coordinator))

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
        """Return the name of the sensor."""
        return self._name

    @property
    def unique_id(self):
        """Return a unique ID for this sensor."""
        return self._unique_id

    @property
    def native_value(self):
        """Return the sensor's state."""
        return self._state


class WatchYourLANTotalDevicesSensor(WatchYourLANBaseSensor):
    """Sensor showing the total number of devices."""

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
    """Sensor showing the number of online devices."""

    def __init__(self, coordinator):
        super().__init__(coordinator, "Online Devices", "online_devices")
        self._update_state()

    @callback
    def _handle_coordinator_update(self):
        self._update_state()
        self.async_write_ha_state()

    def _update_state(self):
        hosts = self.coordinator.data.get("hosts", [])
        self._state = sum(1 for host in hosts if host.get("online"))


class WatchYourLANOfflineDevicesSensor(WatchYourLANBaseSensor):
    """Sensor showing the number of offline devices."""

    def __init__(self, coordinator):
        super().__init__(coordinator, "Offline Devices", "offline_devices")
        self._update_state()

    @callback
    def _handle_coordinator_update(self):
        self._update_state()
        self.async_write_ha_state()

    def _update_state(self):
        hosts = self.coordinator.data.get("hosts", [])
        self._state = sum(1 for host in hosts if not host.get("online"))


class WatchYourLANKnownDevicesSensor(WatchYourLANBaseSensor):
    """Sensor showing the number of known devices."""

    def __init__(self, coordinator):
        super().__init__(coordinator, "Known Devices", "known_devices")
        self._update_state()

    @callback
    def _handle_coordinator_update(self):
        self._update_state()
        self.async_write_ha_state()

    def _update_state(self):
        hosts = self.coordinator.data.get("hosts", [])
        self._state = sum(1 for host in hosts if host.get("known"))


class WatchYourLANUnknownDevicesSensor(WatchYourLANBaseSensor):
    """Sensor showing the number of unknown devices."""

    def __init__(self, coordinator):
        super().__init__(coordinator, "Unknown Devices", "unknown_devices")
        self._update_state()

    @callback
    def _handle_coordinator_update(self):
        self._update_state()
        self.async_write_ha_state()

    def _update_state(self):
        hosts = self.coordinator.data.get("hosts", [])
        self._state = sum(1 for host in hosts if not host.get("known"))
