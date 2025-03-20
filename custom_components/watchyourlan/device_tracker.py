"""Device tracker for WatchYourLAN."""
import logging

from homeassistant.components.device_tracker.config_entry import ScannerEntity
from homeassistant.components.device_tracker.const import SourceType
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up WatchYourLAN device trackers from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    chosen_macs = entry.options.get("devices_to_track", [])

    entities = []
    data = coordinator.data
    if data and "hosts" in data:
        for host in data["hosts"]:
            mac = host.get("mac")
            if mac and mac in chosen_macs:
                entities.append(WatchYourLANDeviceTracker(coordinator, host))

    async_add_entities(entities, True)


class WatchYourLANDeviceTracker(CoordinatorEntity, ScannerEntity):
    """WatchYourLAN device tracker entity."""

    def __init__(self, coordinator, host_data):
        super().__init__(coordinator)
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
        return f"watchyourlan_tracker_{self._mac}"

    @property
    def source_type(self):
        return SourceType.ROUTER

    @property
    def is_connected(self):
        return self._is_connected

    @property
    def ip_address(self):
        return self._ip

    @property
    def mac_address(self):
        return self._mac

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._mac)},
            "name": self._name,
            "manufacturer": self._vendor or "Unknown",
            "model": "Network Device",
        }

    @property
    def extra_state_attributes(self):
        return {
            "known": self._known,
            "vendor": self._vendor,
            "id": self._host_id,
        }

    @callback
    def _handle_coordinator_update(self):
        """Handle updated data from the coordinator."""
        data = self.coordinator.data
        if data and "hosts" in data:
            for host in data["hosts"]:
                if host.get("mac") == self._mac:
                    self._is_connected = host.get("online", False)
                    self._ip = host.get("ip")
                    self._known = host.get("known", False)
                    new_name = host.get("name")
                    if new_name and new_name not in (self._mac, self._name):
                        self._name = new_name
                    break

        self.async_write_ha_state()
