"""Binary sensors for WatchYourLAN."""
import logging

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up WatchYourLAN binary sensors from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    chosen_macs = entry.options.get("devices_to_track", [])

    _LOGGER.debug("WatchYourLAN coordinator data: %s", coordinator.data)

    entities = []
    data = coordinator.data
    if data and "hosts" in data:
        hosts = data["hosts"]
        if isinstance(hosts, list) and hosts:
            for host in hosts:
                mac = host.get("mac")
                if mac and mac in chosen_macs:
                    entities.append(WatchYourLANDevicePresenceSensor(coordinator, host))
        else:
            _LOGGER.warning("No hosts found in WatchYourLAN data or data is not a list")
    else:
        _LOGGER.warning("No hosts data in WatchYourLAN coordinator")

    async_add_entities(entities, True)


class WatchYourLANDevicePresenceSensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor representing whether a device is online (presence)."""

    def __init__(self, coordinator, host_data):
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._host_id = host_data.get("id", "unknown")
        self._mac = host_data.get("mac", "unknown")
        self._ip = host_data.get("ip", "")
        self._known = host_data.get("known", False)
        self._vendor = host_data.get("vendor", "")
        self._name = host_data.get("name") or self._mac or "Unknown Device"
        self._is_on = host_data.get("online", False)

    @property
    def name(self):
        """Return the entity’s name."""
        return f"{self._name} Presence"

    @property
    def is_on(self):
        """Return True if device is online."""
        return self._is_on

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"watchyourlan_binary_sensor_{self._mac}"

    @callback
    def _handle_coordinator_update(self):
        """Handle updated data from the coordinator."""
        found = False
        data = self.coordinator.data
        if data and "hosts" in data and isinstance(data["hosts"], list):
            for host in data["hosts"]:
                mac = host.get("mac")
                if mac and mac == self._mac:
                    # Update presence info
                    self._is_on = host.get("online", False)
                    self._ip = host.get("ip", self._ip)
                    self._known = host.get("known", self._known)
                    new_name = host.get("name")
                    if new_name and new_name not in ("null", self._name, self._mac):
                        self._name = new_name
                    found = True
                    break
            if not found and self._mac != "none":
                # Host is missing from the updated list, mark offline
                self._is_on = False

        self.async_write_ha_state()
