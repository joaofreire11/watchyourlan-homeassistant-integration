"""
Support for tracking devices using WatchYourLAN.
"""
import logging

from homeassistant.components.device_tracker.config_entry import ScannerEntity
from homeassistant.components.device_tracker.const import SourceType
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(
    hass: HomeAssistant, config, async_add_entities, discovery_info=None
):
    """Set up the WatchYourLAN device trackers."""
    coordinator = hass.data[DOMAIN]["coordinator"]
    
    await coordinator.async_refresh()
    
    if not coordinator.last_update_success:
        return
    
    entities = []
    
    if coordinator.data and "hosts" in coordinator.data:
        for host in coordinator.data["hosts"]:
            entities.append(WatchYourLANDeviceTracker(coordinator, host))
    
    async_add_entities(entities, True)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    """Set up WatchYourLAN device trackers based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    
    entities = []
    
    if coordinator.data and "hosts" in coordinator.data:
        for host in coordinator.data["hosts"]:
            entities.append(WatchYourLANDeviceTracker(coordinator, host))
    
    async_add_entities(entities, True)


class WatchYourLANDeviceTracker(CoordinatorEntity, ScannerEntity):
    """WatchYourLAN device tracker."""

    def __init__(self, coordinator, host_data):
        """Initialize the device tracker."""
        super().__init__(coordinator)
        self._host_id = host_data.get("id")
        self._mac = host_data.get("mac")
        self._name = host_data.get("name") or host_data.get("mac")
        self._ip = host_data.get("ip")
        self._known = host_data.get("known", False)
        self._vendor = host_data.get("vendor", "")
        
        # Set initial state
        self._is_connected = host_data.get("online", False)

    @property
    def name(self):
        """Return the name of the device."""
        return f"WatchYourLAN Tracker {self._name}"

    @property
    def unique_id(self):
        """Return a unique, Home Assistant friendly identifier for this entity."""
        return f"watchyourlan_tracker_{self._mac}"

    @property
    def source_type(self):
        """Return the source type of the device."""
        return SourceType.ROUTER

    @property
    def is_connected(self):
        """Return true if the device is connected to the network."""
        return self._is_connected

    @property
    def ip_address(self):
        """Return the IP address of the device."""
        return self._ip

    @property
    def mac_address(self):
        """Return the MAC address of the device."""
        return self._mac

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self._mac)},
            "name": self._name,
            "manufacturer": self._vendor or "Unknown",
            "model": "Network Device",
        }

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return {
            "known": self._known,
            "vendor": self._vendor,
            "id": self._host_id,
        }

    @callback
    def _handle_coordinator_update(self):
        """Handle updated data from the coordinator."""
        if self.coordinator.data and "hosts" in self.coordinator.data:
            for host in self.coordinator.data["hosts"]:
                if host.get("mac") == self._mac:
                    self._is_connected = host.get("online", False)
                    self._ip = host.get("ip")
                    self._known = host.get("known", False)
                    # Update name if changed in WatchYourLAN
                    new_name = host.get("name")
                    if new_name and new_name != self._name and new_name != self._mac:
                        self._name = new_name
                    break
        
        self.async_write_ha_state()