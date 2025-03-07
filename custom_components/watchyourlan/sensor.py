"""
Support for WatchYourLAN sensors.
"""
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DOMAIN, ICON

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(
    hass: HomeAssistant, config, async_add_entities, discovery_info=None
):
    """Set up the WatchYourLAN sensors."""
    coordinator = hass.data[DOMAIN]["coordinator"]
    
    await coordinator.async_refresh()
    
    if not coordinator.last_update_success:
        return
    
    entities = []
    
    # Add network status sensors
    entities.append(WatchYourLANTotalDevicesSensor(coordinator))
    entities.append(WatchYourLANOnlineDevicesSensor(coordinator))
    entities.append(WatchYourLANOfflineDevicesSensor(coordinator))
    entities.append(WatchYourLANKnownDevicesSensor(coordinator))
    entities.append(WatchYourLANUnknownDevicesSensor(coordinator))
    
    async_add_entities(entities, True)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    """Set up WatchYourLAN sensors based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    
    entities = []
    
    # Add network status sensors
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
        self._icon = ICON

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def unique_id(self):
        """Return a unique, Home Assistant friendly identifier for this entity."""
        return self._unique_id

    @property
    def icon(self):
        """Return the icon to use in the frontend."""
        return self._icon

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._state


class WatchYourLANTotalDevicesSensor(WatchYourLANBaseSensor):
    """Sensor for total devices in WatchYourLAN."""

    def __init__(self, coordinator):
        """Initialize the sensor."""
        super().__init__(coordinator, "Total Devices", "total_devices")
        self._update_state()

    @callback
    def _handle_coordinator_update(self):
        """Handle updated data from the coordinator."""
        self._update_state()
        self.async_write_ha_state()

    def _update_state(self):
        """Update the state from the coordinator data."""
        if self.coordinator.data and "hosts" in self.coordinator.data:
            self._state = len(self.coordinator.data["hosts"])
        else:
            self._state = 0


class WatchYourLANOnlineDevicesSensor(WatchYourLANBaseSensor):
    """Sensor for online devices in WatchYourLAN."""

    def __init__(self, coordinator):
        """Initialize the sensor."""
        super().__init__(coordinator, "Online Devices", "online_devices")
        self._update_state()

    @callback
    def _handle_coordinator_update(self):
        """Handle updated data from the coordinator."""
        self._update_state()
        self.async_write_ha_state()

    def _update_state(self):
        """Update the state from the coordinator data."""
        if self.coordinator.data and "hosts" in self.coordinator.data:
            self._state = sum(
                1 for host in self.coordinator.data["hosts"] if host.get("online", False)
            )
        else:
            self._state = 0


class WatchYourLANOfflineDevicesSensor(WatchYourLANBaseSensor):
    """Sensor for offline devices in WatchYourLAN."""

    def __init__(self, coordinator):
        """Initialize the sensor."""
        super().__init__(coordinator, "Offline Devices", "offline_devices")
        self._update_state()

    @callback
    def _handle_coordinator_update(self):
        """Handle updated data from the coordinator."""
        self._update_state()
        self.async_write_ha_state()

    def _update_state(self):
        """Update the state from the coordinator data."""
        if self.coordinator.data and "hosts" in self.coordinator.data:
            self._state = sum(
                1 for host in self.coordinator.data["hosts"] if not host.get("online", False)
            )
        else:
            self._state = 0


class WatchYourLANKnownDevicesSensor(WatchYourLANBaseSensor):
    """Sensor for known devices in WatchYourLAN."""

    def __init__(self, coordinator):
        """Initialize the sensor."""
        super().__init__(coordinator, "Known Devices", "known_devices")
        self._update_state()

    @callback
    def _handle_coordinator_update(self):
        """Handle updated data from the coordinator."""
        self._update_state()
        self.async_write_ha_state()

    def _update_state(self):
        """Update the state from the coordinator data."""
        if self.coordinator.data and "hosts" in self.coordinator.data:
            self._state = sum(
                1 for host in self.coordinator.data["hosts"] if host.get("known", False)
            )
        else:
            self._state = 0


class WatchYourLANUnknownDevicesSensor(WatchYourLANBaseSensor):
    """Sensor for unknown devices in WatchYourLAN."""

    def __init__(self, coordinator):
        """Initialize the sensor."""
        super().__init__(coordinator, "Unknown Devices", "unknown_devices")
        self._update_state()

    @callback
    def _handle_coordinator_update(self):
        """Handle updated data from the coordinator."""
        self._update_state()
        self.async_write_ha_state()

    def _update_state(self):
        """Update the state from the coordinator data."""
        if self.coordinator.data and "hosts" in self.coordinator.data:
            self._state = sum(
                1 for host in self.coordinator.data["hosts"] if not host.get("known", False)
            )
        else:
            self._state = 0