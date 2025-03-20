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
    host = entry.data["host"]
    port = entry.data["port"]
    scan_interval = entry.data["scan_interval"]

    session = aiohttp.ClientSession()

    coordinator = WatchYourLANCoordinator(
        hass,
        session,
        host,
        port,
        scan_interval,
    )

    try:
        await coordinator.async_config_entry_first_refresh()

    except (ConfigEntryNotReady, UpdateFailed) as err:
        _LOGGER.warning("Failed initial WatchYourLAN update: %s", err)
        await session.close()
        raise ConfigEntryNotReady from err
    except Exception as exc:
        _LOGGER.error("Unexpected error setting up WatchYourLAN: %s", exc)
        await session.close()
        raise

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "coordinator": coordinator,
        "session": session,
    }

    await hass.config_entries.async_forward_entry_setups(
        entry, ["sensor", "binary_sensor", "device_tracker"]
    )

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a WatchYourLAN config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, ["sensor", "binary_sensor", "device_tracker"]
    )
    if unload_ok:
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

                if isinstance(data, list):
                    # Wrap the list in {"hosts": []} 
                    wrapped_hosts = []
                    for item in data:
                        wrapped_hosts.append(
                            {
                                "id": item.get("ID"),
                                "mac": item.get("Mac"),
                                "name": item.get("Name") or "",
                                "online": bool(item.get("Now")),
                                "known": bool(item.get("Known")),
                                "ip": item.get("IP"),
                                "vendor": item.get("Hw"),
                                "iface": item.get("Iface"),
                                "dns": item.get("DNS"),
                                "date": item.get("Date"),
                            }
                        )
                    return {"hosts": wrapped_hosts}
                elif isinstance(data, dict):
                    return data
                else:
                    raise UpdateFailed(f"Invalid JSON structure: {data}")

        except Exception as err:
            raise UpdateFailed(f"Error communicating with WatchYourLAN: {err}") from err
