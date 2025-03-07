async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    """Set up WatchYourLAN binary sensors based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    
    # Debug the data
    _LOGGER.debug("WatchYourLAN coordinator data: %s", coordinator.data)
    
    entities = []
    
    # Add device presence sensors for each host
    if coordinator.data and "hosts" in coordinator.data:
        if isinstance(coordinator.data["hosts"], list) and coordinator.data["hosts"]:
            for host in coordinator.data["hosts"]:
                _LOGGER.debug("Adding sensor for host: %s", host)
                entities.append(WatchYourLANDevicePresenceSensor(coordinator, host))
        else:
            _LOGGER.warning("No hosts found in WatchYourLAN data or data is not a list")
            # Add a placeholder sensor if no hosts are found or data is invalid
            placeholder_host = {
                "id": "none",
                "mac": "none",
                "name": "None",
                "ip": "none",
                "known": False,
                "vendor": "Unknown",
                "online": False
            }
            entities.append(WatchYourLANDevicePresenceSensor(coordinator, placeholder_host))
    else:
        _LOGGER.warning("No hosts data in WatchYourLAN coordinator")
    
    async_add_entities(entities, True)

class WatchYourLANDevicePresenceSensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor for WatchYourLAN device presence."""

    def __init__(self, coordinator, host_data):
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._host_id = host_data.get("id", "unknown")
        self._mac = host_data.get("mac", "unknown")
        self._name = host_data.get("name") or host_data.get("mac", "Unknown Device")
        if not self._name or self._name == "null":
            self._name = self._mac or "Unknown Device"
        self._ip = host_data.get("ip", "")
        self._known = host_data.get("known", False)
        self._vendor = host_data.get("vendor", "")
        
        # Set initial state
        self._is_on = host_data.get("online", False)

    @callback
    def _handle_coordinator_update(self):
        """Handle updated data from the coordinator."""
        if (self.coordinator.data and 
            "hosts" in self.coordinator.data and 
            isinstance(self.coordinator.data["hosts"], list)):
            
            found = False
            for host in self.coordinator.data["hosts"]:
                mac = host.get("mac")
                if mac and mac == self._mac:
                    self._is_on = host.get("online", False)
                    self._ip = host.get("ip", self._ip)
                    self._known = host.get("known", self._known)
                    # Update name if changed in WatchYourLAN
                    new_name = host.get("name")
                    if new_name and new_name != "null" and new_name != self._name and new_name != self._mac:
                        self._name = new_name
                    found = True
                    break
            
            # If the device is no longer in the list, mark it as offline
            if not found and self._mac != "none":
                self._is_on = False
        
        self.async_write_ha_state()