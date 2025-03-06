from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.components.sensor import SensorEntity

from .const import DOMAIN

SENSOR_TYPES = {
    "total": {"name": "Total Hosts", "icon": "mdi:network"},
    "online": {"name": "Online Hosts", "icon": "mdi:lan-connect"},
    "offline": {"name": "Offline Hosts", "icon": "mdi:lan-disconnect"},
    "known": {"name": "Known Hosts", "icon": "mdi:account-check"},
    "unknown": {"name": "Unknown Hosts", "icon": "mdi:account-question"}
}

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [
        WatchYourLANSensor(coordinator, sensor_type)
        for sensor_type in SENSOR_TYPES
    ]
    async_add_entities(entities, True)

class WatchYourLANSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, sensor_type):
        super().__init__(coordinator)
        self._type = sensor_type
        self._attr_name = f"WatchYourLAN {SENSOR_TYPES[sensor_type]['name']}"
        self._attr_icon = SENSOR_TYPES[sensor_type]["icon"]
        self._attr_unique_id = f"watchyourlan_{sensor_type}"

    @property
    def state(self):
        hosts = self.coordinator.data or []
        total = len(hosts)
        online = sum(1 for h in hosts if h.get("online"))
        known = sum(1 for h in hosts if h.get("known"))

        if self._type == "total":
            return total
        if self._type == "online":
            return online
        if self._type == "offline":
            return total - online
        if self._type == "known":
            return known
        if self._type == "unknown":
            return total - known

    @property
    def extra_state_attributes(self):
        return {"hosts": self.coordinator.data}
