async def _async_update_data(self):
    """Fetch data from WatchYourLAN."""
    try:
        # Fetch all hosts
        async with self.session.get(f"{self.url}/api/all") as resp:
            if resp.status == 200:
                hosts_data = await resp.json()
                _LOGGER.debug("WatchYourLAN hosts data: %s", hosts_data)
            else:
                _LOGGER.error(
                    "Error fetching hosts from %s: %s", 
                    self.url, 
                    resp.status
                )
                hosts_data = []
        
        # Fetch network status
        async with self.session.get(f"{self.url}/api/status/") as resp:
            if resp.status == 200:
                status_data = await resp.json()
                _LOGGER.debug("WatchYourLAN status data: %s", status_data)
            else:
                _LOGGER.error(
                    "Error fetching status from %s: %s", 
                    self.url, 
                    resp.status
                )
                status_data = {}
        
        # Make sure we have a list for hosts even if the API returns something else
        if not isinstance(hosts_data, list):
            _LOGGER.warning("API returned non-list for hosts, converting to empty list")
            hosts_data = []
            
        return {
            "hosts": hosts_data,
            "status": status_data,
            "last_update": self.hass.states.get("sensor.date_time_iso"),
        }
    except Exception as err:
        _LOGGER.exception(f"Error communicating with WatchYourLAN: {err}")
        raise UpdateFailed(f"Error communicating with WatchYourLAN: {err}")