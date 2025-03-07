"""
Config flow for WatchYourLAN integration.
"""
import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
from homeassistant.const import (
    CONF_HOST,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
)

from .const import DOMAIN, DEFAULT_HOST, DEFAULT_PORT, DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class WatchYourLANConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for WatchYourLAN."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    def __init__(self):
        """Initialize."""
        self._errors = {}

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        self._errors = {}

        if user_input is not None:
            await self.async_set_unique_id(f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}")
            self._abort_if_unique_id_configured()

            valid = await self._test_connection(
                user_input[CONF_HOST], user_input[CONF_PORT]
            )
            
            if valid:
                return self.async_create_entry(
                    title=f"WatchYourLAN ({user_input[CONF_HOST]})",
                    data=user_input,
                )
            
            self._errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST, default=DEFAULT_HOST): str,
                    vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
                    vol.Optional(
                        CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                    ): int,
                }
            ),
            errors=self._errors,
        )

    async def _test_connection(self, host, port):
        """Test connectivity to WatchYourLAN."""
        try:
            session = async_get_clientsession(self.hass)
            url = f"http://{host}:{port}/api/status/"
            
            async with session.get(url) as resp:
                if resp.status == 200:
                    return True
                return False
        except Exception:
            return False