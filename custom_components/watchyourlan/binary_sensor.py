"""Binary sensors for WatchYourLAN, creating separate child devices for each tracked host."""
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
    entry_id = entry.entry_id

    # The user-chosen MACs from your Options Flow
    chosen_macs = entry.options.get("devices_to_track", [])

    entities = []
    data = coordinator.data
    if data and "hosts" in data:
        hosts = data["hosts"]
        if isinstance(hosts, list) and hosts:
            for host in hosts:
                mac = host.get("mac")
                if mac and mac in chosen_macs:
                    # Create a separate child device for this host
                    entities.append(WatchYourLANHostPresenceSensor(coordinator, entry_id, host))
        else:
            _LOGGER.warning("No hosts found in WatchYourLAN data or data is not a list")
    else:
        _LOGGER.warning("No hosts data in WatchYourLAN coordinator")

    async_add_entities(entities, True)


class WatchYourLANHostPresenceSensor(CoordinatorEntity, BinarySensorEntity):
    """
    A binary sensor for each tracked host, represented as a separate device in HA.
    """

    def __init__(self, coordinator, entry_id, host_data):
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._entry_id = entry_id
        self._host_id = host_data.get("id", "unknown")
        self._mac = host_data.get("mac", "unknown")
        self._ip = host_data.get("ip", "")
        self._known = host_data.get("known", False)
        self._vendor = host_data.get("vendor", "")
        self._name = host_data.get("name") or self._mac or "Unknown Device"
        self._is_on = host_data.get("online", False)

    @property
    def name(self):
        """Return the entity's name."""
        return f"{self._name} Presence"

    @property
    def is_on(self):
        """Return True if device is online (presence)."""
        return self._is_on

    @property
    def unique_id(self):
        """Return a unique ID for this sensor."""
        return f"watchyourlan_binary_sensor_{self._mac}"

    @property
    def device_info(self):
        """
        Make this sensor appear as a *separate device* (the tracked host),
        with 'via_device' pointing to our 'hub' device (the server).
        """
        return {
            # Unique identifier for this device, based on MAC
            "identifiers": {(DOMAIN, self._mac)},
            "name": self._name,
            "manufacturer": self._vendor or "WatchYourLAN",
            "model": "Tracked Host",
            # 'via_device': tie this child device to the main hub device
            "via_device": (DOMAIN, self._entry_id),
        }

    @property
    def extra_state_attributes(self):
        """Return extra attributes about the host."""
        return {
            "mac": self._mac,
            "ip": self._ip,
            "known": self._known,
            "vendor": self._vendor,
            "host_id": self._host_id,
        }

    @callback
    def _handle_coordinator_update(self):
        """Handle updated data from the coordinator."""
        found = False
        data = self.coordinator.data
        if data and "hosts" in data and isinstance(data["hosts"], list):
            for host in data["hosts"]:
                if host.get("mac") == self._mac:
                    self._is_on = host.get("online", False)
                    self._ip = host.get("ip", self._ip)
                    self._known = host.get("known", self._known)
                    new_name = host.get("name")
                    if new_name and new_name not in ("null", self._name, self._mac):
                        self._name = new_name
                    found = True
                    break

            if not found and self._mac != "none":
                # If the host is missing from updated data, mark offline
                self._is_on = False

        self.async_write_ha_state()
