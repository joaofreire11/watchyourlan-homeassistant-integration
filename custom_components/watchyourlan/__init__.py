"""Initialize the WatchYourLAN integration."""
import asyncio
import logging
from datetime import timedelta

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up WatchYourLAN from a config entry."""
    # Pull config values
    host = entry.data["host"]
    port = entry.data["port"]
    scan_interval = entry.data["scan_interval"]

    # Create an aiohttp session
    # (We’ll store this so we can close it on unload.)
    session = aiohttp.ClientSession()

    coordinator = WatchYourLANCoordinator(
        hass,
        session,
        host,
        port,
        scan_interval,
    )

    try:
        # Attempt initial refresh to verify we can connect
        await coordinator.async_config_entry_first_refresh()

    except (ConfigEntryNotReady, UpdateFailed) as err:
        # If you prefer, you can raise ConfigEntryNotReady to have HA retry setup
        _LOGGER.warning("Failed initial WatchYourLAN update: %s", err)
        await session.close()
        raise ConfigEntryNotReady from err
    except Exception as exc:
        # Catch-all for unexpected errors
        _LOGGER.error("Unexpected error setting up WatchYourLAN: %s", exc)
        await session.close()
        raise

    # Store references so platforms can look up the coordinator
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "coordinator": coordinator,
        "session": session,
    }

    # Forward the setup to your platforms
    # (sensor, binary_sensor, device_tracker are all used by your code)
    await hass.config_entries.async_forward_entry_setups(
        entry, ["sensor", "binary_sensor", "device_tracker"]
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a WatchYourLAN config entry."""
    # Unload entities in each platform
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, ["sensor", "binary_sensor", "device_tracker"]
    )
    if unload_ok:
        # Close our stored aiohttp session
        session = hass.data[DOMAIN][entry.entry_id]["session"]
        await session.close()

        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class WatchYourLANCoordinator(DataUpdateCoordinator):
    """DataUpdateCoordinator to fetch data from WatchYourLAN's API."""

    def __init__(
        self,
        hass: HomeAssistant,
        session: aiohttp.ClientSession,
        host: str,
        port: int,
        interval: int,
    ):
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="WatchYourLAN",
            update_interval=timedelta(seconds=interval),
        )
        self._session = session
        self._api_url = f"http://{host}:{port}/api/all"

    async def _async_update_data(self) -> dict:
        """Fetch the latest data from the WatchYourLAN API."""
        try:
            async with self._session.get(self._api_url) as resp:
                if resp.status != 200:
                    raise UpdateFailed(
                        f"Unexpected status from WatchYourLAN API: {resp.status}"
                    )
                data = await resp.json()
                if not isinstance(data, dict):
                    # If the API returns something unexpected, handle gracefully
                    raise UpdateFailed(
                        f"Invalid JSON response from WatchYourLAN: {data}"
                    )
                return data
        except asyncio.CancelledError:
            # Let Home Assistant handle canceled tasks properly
            raise
        except Exception as err:
            raise UpdateFailed(f"Error communicating with WatchYourLAN: {err}") from err
