"""Config flow for WatchYourLAN integration."""
import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv

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
        """Handle the initial step in the user config flow."""
        self._errors = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input[CONF_PORT]

            # Create unique ID (so we only allow one config entry per host:port)
            await self.async_set_unique_id(f"{host}:{port}")
            self._abort_if_unique_id_configured()

            valid = await self._test_connection(host, port)
            if valid:
                return self.async_create_entry(
                    title=f"WatchYourLAN ({host})",
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

    async def _test_connection(self, host, port) -> bool:
        """Test connectivity to WatchYourLAN via a quick GET to /api/status/."""
        session = async_get_clientsession(self.hass)
        url = f"http://{host}:{port}/api/status/"
        try:
            async with session.get(url) as resp:
                if resp.status == 200:
                    return True
                _LOGGER.warning(
                    "WatchYourLAN test connection returned status %s, expected 200",
                    resp.status,
                )
                return False
        except Exception as exc:
            _LOGGER.error("Error testing WatchYourLAN connection: %s", exc)
            return False
