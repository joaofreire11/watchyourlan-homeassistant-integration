"""
Support for WatchYourLAN binary sensors.
"""
import logging
from typing import Callable, Dict, List, Optional

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DOMAIN, SIGNAL_UPDATE_WATCHYOURLAN

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(
    hass: HomeAssistant, config, async_add_entities, discovery_info=None
):
    """Set up the WatchYourLAN binary sensors."""
    coordinator = hass.data[DOMAIN]["coordinator"]
    
    await coordinator.async_refresh()
    
    if not coordinator.last_update_success:
        return
    
    entities = []
    
    # Add device presence sensors for each host
    if coordinator.data and "hosts" in coordinator.data:
        for host in coordinator.data["hosts"]:
            entities.append(WatchYourLANDevicePresenceSensor(coordinator, host))
    
    async_add_entities(entities, True)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    """Set up WatchYourLAN binary sensors based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    
    entities = []
    
    # Add device presence sensors for each host
    if coordinator.data and "hosts" in coordinator.data:
        for host in coordinator.data["hosts"]:
            entities.append(WatchYourLANDevicePresenceSensor(coordinator, host))
    
    async_add_entities(entities, True)


class WatchYourLANDevicePresenceSensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor for WatchYourLAN device presence."""

    def __init__(self, coordinator, host_data):
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._host_id = host_data.get("id")
        self._mac = host_data.get("mac")
        self._name = host_data.get("name") or host_data.get("mac")
        self._ip = host_data.get("ip")
        self._known = host_data.get("known", False)
        self._vendor = host_data.get("vendor", "")
        
        # Set initial state
        self._is_on = host_data.get("online", False)

    @property
    def name(self):
        """Return the name of the binary sensor."""
        return f"WatchYourLAN {self._name}"

    @property
    def unique_id(self):
        """Return a unique, Home Assistant friendly identifier for this entity."""
        return f"watchyourlan_device_{self._mac}"

    @property
    def device_class(self):
        """Return the class of this device."""
        return BinarySensorDeviceClass.CONNECTIVITY

    @property
    def is_on(self):
        """Return true if the binary sensor is on."""
        return self._is_on

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
            "mac": self._mac,
            "ip": self._ip,
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
                    self._is_on = host.get("online", False)
                    self._ip = host.get("ip")
                    self._known = host.get("known", False)
                    # Update name if changed in WatchYourLAN
                    new_name = host.get("name")
                    if new_name and new_name != self._name and new_name != self._mac:
                        self._name = new_name
                    break
        
        self.async_write_ha_state()