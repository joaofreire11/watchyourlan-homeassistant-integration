"""device_tracker.py - One child device per tracked host in WatchYourLAN."""
import logging

from homeassistant.components.device_tracker.config_entry import ScannerEntity
from homeassistant.components.device_tracker.const import SourceType
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up WatchYourLAN device trackers (child devices) from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    entry_id = entry.entry_id

    # The user-chosen MACs (the devices they want to see in HA)
    chosen_macs = entry.options.get("devices_to_track", [])

    entities = []
    data = coordinator.data
    if data and "hosts" in data:
        for host in data["hosts"]:
            mac = host.get("mac")
            if mac and mac in chosen_macs:
                # Create a child device for this host
                entities.append(WatchYourLANHostDeviceTracker(coordinator, entry_id, host))

    async_add_entities(entities, True)


class WatchYourLANHostDeviceTracker(CoordinatorEntity, ScannerEntity):
    """Device tracker for each selected host, represented as a separate device."""

    def __init__(self, coordinator, entry_id, host_data):
        super().__init__(coordinator)
        self._entry_id = entry_id
        self._host_id = host_data.get("id")
        self._mac = host_data.get("mac")
        self._ip = host_data.get("ip")
        self._known = host_data.get("known", False)
        self._vendor = host_data.get("vendor", "")
        self._name = host_data.get("name") or host_data.get("mac")
        self._is_connected = host_data.get("online", False)

    @property
    def name(self):
        return f"WatchYourLAN Tracker {self._name}"

    @property
    def unique_id(self):
        """Unique ID for the device tracker entity."""
        return f"watchyourlan_tracker_{self._mac}"

    @property
    def source_type(self):
        """This is typically SourceType.ROUTER for a router-based tracker."""
        return SourceType.ROUTER

    @property
    def is_connected(self):
        """Return true if the device is connected."""
        return self._is_connected

    @property
    def ip_address(self):
        """The IP address of the host."""
        return self._ip

    @property
    def mac_address(self):
        """The MAC address of the host."""
        return self._mac

    @property
    def device_info(self):
        """
        Make each tracked host a child device of the main 'hub'.
        Use (DOMAIN, self._mac) as the unique identifier for the child device.
        'via_device': tie it back to the aggregator/hub device (DOMAIN, entry_id).
        """
        return {
            "identifiers": {(DOMAIN, self._mac)},
            "name": self._name,
            "manufacturer": self._vendor or "Unknown",
            "model": "Tracked Host",
            "via_device": (DOMAIN, self._entry_id),
        }

    @property
    def extra_state_attributes(self):
        """Provide any additional attributes."""
        return {
            "host_id": self._host_id,
            "known": self._known,
            "vendor": self._vendor,
        }

    @callback
    def _handle_coordinator_update(self):
        """Update from coordinator data."""
        for host in self.coordinator.data.get("hosts", []):
            if host.get("mac") == self._mac:
                self._is_connected = host.get("online", False)
                self._ip = host.get("ip")
                self._known = host.get("known", False)
                new_name = host.get("name")
                if new_name and new_name != self._mac and new_name != self._name:
                    self._name = new_name
                break

        self.async_write_ha_state()
