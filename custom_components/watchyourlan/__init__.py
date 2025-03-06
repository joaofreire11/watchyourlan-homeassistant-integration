import logging
from datetime import timedelta
import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    session = aiohttp.ClientSession()
    coordinator = WatchYourLANCoordinator(
        hass,
        session,
        entry.data["host"],
        entry.data.get("scan_interval", DEFAULT_SCAN_INTERVAL),
    )

    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor"])
    if unload_ok:
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.session.close()
    return unload_ok

class WatchYourLANCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, session, host, scan_interval):
        self.host = host.rstrip('/')
        self.session = session
        super().__init__(
            hass,
            _LOGGER,
            name="WatchYourLAN Coordinator",
            update_interval=timedelta(seconds=scan_interval),
        )

    async def _async_update_data(self):
        url = f"{self.host}/api/all"
        try:
            async with self.session.get(url, timeout=10) as response:
                response.raise_for_status()
                return await response.json()
        except Exception as err:
            raise UpdateFailed(f"Failed fetching data: {err}") from err
