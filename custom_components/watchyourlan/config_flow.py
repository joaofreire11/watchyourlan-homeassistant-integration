"""
Config flow for WatchYourLAN integration with dynamic removal of deselected devices.
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

# Import your existing constants. Adjust as needed.
from .const import (
    DOMAIN,
    DEFAULT_HOST,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


class WatchYourLANConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for WatchYourLAN."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    def __init__(self):
        """Initialize the config flow."""
        self._errors = {}

    async def async_step_user(self, user_input=None):
        """
        Step that runs when the user starts adding the integration
        (host, port, scan interval).
        """
        self._errors = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input[CONF_PORT]

            # Create a unique ID for this integration instance: host:port
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
            data_schema=vol.Schema({
                vol.Required(CONF_HOST, default=DEFAULT_HOST): str,
                vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
                vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): int,
            }),
            errors=self._errors,
        )

    async def _test_connection(self, host, port) -> bool:
        """Test connectivity by checking /api/status/ endpoint (or any quick check)."""
        session = async_get_clientsession(self.hass)
        url = f"http://{host}:{port}/api/status/"
        try:
            async with session.get(url) as resp:
                if resp.status == 200:
                    return True
                _LOGGER.warning("WatchYourLAN test connection status: %s", resp.status)
                return False
        except Exception as exc:
            _LOGGER.error("Error testing WatchYourLAN connection: %s", exc)
            return False

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return the options flow handler for this entry."""
        return WatchYourLANOptionsFlowHandler(config_entry)


class WatchYourLANOptionsFlowHandler(config_entries.OptionsFlow):
    """
    Handle the Options Flow for WatchYourLAN, including dynamic
    removal of devices from the device registry when deselected.
    """

    def __init__(self, config_entry: config_entries.ConfigEntry):
        """Initialize with the existing config entry."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """
        Main step that displays a multi-select for devices (MAC addresses).
        """
        if user_input is not None:
            old_set = set(self.config_entry.options.get("devices_to_track", []))
            new_set = set(user_input.get("devices_to_track", []))

            # Figure out which devices were removed from the selection
            removed = old_set - new_set

            if removed:
                # Dynamically remove them from HA
                await self._async_remove_devices(removed)

            # Save the updated options
            entry = self.async_create_entry(title="", data=user_input)

            # Force a reload so the integration picks up the new device set
            await self.hass.config_entries.async_reload(self.config_entry.entry_id)

            return entry

        # If user_input is None, we show the form:
        coordinator = self.hass.data[DOMAIN][self.config_entry.entry_id]["coordinator"]
        all_hosts = coordinator.data.get("hosts", [])

        # Build a dict of MAC -> "Name (MAC)" for the multi_select
        device_map = {}
        for host in all_hosts:
            mac = host.get("mac")
            name = host.get("name") or mac
            if mac:
                device_map[mac] = f"{name} ({mac})"

        current_devices = self.config_entry.options.get("devices_to_track", [])

        data_schema = vol.Schema({
            vol.Optional("devices_to_track", default=current_devices):
                cv.multi_select(device_map)
        })

        return self.async_show_form(step_id="init", data_schema=data_schema)

    async def _async_remove_devices(self, removed_macs: set):
        """
        Removes each deselected device from Home Assistant's device registry.

        This also removes all entities associated with each device, so
        they won't remain in the UI as 'unavailable'.
        """
        import homeassistant.helpers.device_registry as dr

        device_registry = dr.async_get(self.hass)

        for mac in removed_macs:
            device = device_registry.async_get_device(identifiers={(DOMAIN, mac)})
            if device:
                _LOGGER.info("Removing device with MAC %s from device registry", mac)
                device_registry.async_remove_device(device.id)
