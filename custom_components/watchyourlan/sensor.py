"""sensor.py - Aggregator sensors for the main 'hub' device."""
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
    entry_id = entry.entry_id

    # Aggregator sensors that always appear under the "hub" device
    sensors = [
        WatchYourLANTotalDevicesSensor(coordinator, entry_id),
        WatchYourLANOnlineDevicesSensor(coordinator, entry_id),
        WatchYourLANOfflineDevicesSensor(coordinator, entry_id),
    ]

    # Example: mark these two as DIAGNOSTIC so they show under "Diagnostics"
    diag_known = WatchYourLANKnownDevicesSensor(coordinator, entry_id)
    diag_known._attr_entity_category = EntityCategory.DIAGNOSTIC
    diag_unknown = WatchYourLANUnknownDevicesSensor(coordinator, entry_id)
    diag_unknown._attr_entity_category = EntityCategory.DIAGNOSTIC

    sensors.append(diag_known)
    sensors.append(diag_unknown)

    async_add_entities(sensors, True)


class WatchYourLANBaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for aggregator sensors on the 'hub' device."""

    def __init__(self, coordinator, entry_id, name_suffix, entity_id_suffix):
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
        """
        Identify this sensor as belonging to exactly one device: the 'hub'
        using (DOMAIN, entry_id) so it shows up as 1 device with multiple entities.
        """
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": "WatchYourLAN Server",
            "manufacturer": "WatchYourLAN",
            "model": "Network Gateway",
        }


class WatchYourLANTotalDevicesSensor(WatchYourLANBaseSensor):
    """Example aggregator sensor: total devices."""

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
    """Example aggregator sensor: online devices."""

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
    """Example aggregator sensor: offline devices."""

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
    """Example aggregator sensor: known devices."""

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
    """Example aggregator sensor: unknown devices."""

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
