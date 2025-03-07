"""
Home Assistant integration for WatchYourLAN network scanner.
"""
import asyncio
import logging
from datetime import timedelta
import voluptuous as vol

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.components.binary_sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    CONF_HOST,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

DOMAIN = "watchyourlan"
SIGNAL_UPDATE_WATCHYOURLAN = f"{DOMAIN}_update"

ICON = "mdi:lan"

DEFAULT_HOST = "localhost"
DEFAULT_PORT = 8840
DEFAULT_SCAN_INTERVAL = timedelta(seconds=60)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Optional(CONF_HOST, default=DEFAULT_HOST): cv.string,
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
                vol.Optional(
                    CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                ): cv.time_period,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

PLATFORMS = ["binary_sensor", "sensor", "device_tracker"]


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the WatchYourLAN component."""
    if DOMAIN not in config:
        return True

    conf = config[DOMAIN]
    host = conf.get(CONF_HOST)
    port = conf.get(CONF_PORT)
    scan_interval = conf.get(CONF_SCAN_INTERVAL)

    coordinator = WatchYourLANDataUpdateCoordinator(
        hass, host, port, scan_interval
    )
    
    await coordinator.async_refresh()

    hass.data[DOMAIN] = {
        "coordinator": coordinator,
    }

    for platform in PLATFORMS:
        hass.async_create_task(
            hass.helpers.discovery.async_load_platform(
                platform, DOMAIN, {}, config
            )
        )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up WatchYourLAN from a config entry."""
    host = entry.data.get(CONF_HOST, DEFAULT_HOST)
    port = entry.data.get(CONF_PORT, DEFAULT_PORT)
    scan_interval = entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    coordinator = WatchYourLANDataUpdateCoordinator(
        hass, host, port, scan_interval
    )
    
    await coordinator.async_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
    }

    for platform in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, platform)
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
            ]
        )
    )
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class WatchYourLANDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching WatchYourLAN data."""

    def __init__(self, hass, host, port, scan_interval):
        """Initialize the data object."""
        self.host = host
        self.port = port
        self.url = f"http://{host}:{port}"
        self.session = async_get_clientsession(hass)

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=scan_interval,
        )

    async def _async_update_data(self):
        """Fetch data from WatchYourLAN."""
        try:
            # Fetch all hosts
            hosts_data = await self._fetch_json_data("/api/all")
            
            # Fetch network status
            status_data = await self._fetch_json_data("/api/status/")
            
            return {
                "hosts": hosts_data,
                "status": status_data,
                "last_update": self.hass.states.get("sensor.date_time_iso"),
            }
        except Exception as err:
            raise UpdateFailed(f"Error communicating with WatchYourLAN: {err}")

    async def _fetch_json_data(self, endpoint):
        """Fetch JSON data from the specified endpoint."""
        try:
            async with self.session.get(f"{self.url}{endpoint}") as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    _LOGGER.error(
                        "Error fetching data from %s%s: %s", 
                        self.url, 
                        endpoint, 
                        resp.status
                    )
                    return {}
        except aiohttp.ClientError as err:
            _LOGGER.error(
                "Error fetching data from %s%s: %s", 
                self.url, 
                endpoint, 
                err
            )
            return {}