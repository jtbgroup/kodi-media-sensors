from homeassistant import config_entries
import voluptuous as vol
from .const import DOMAIN

class KodiMediaSensorsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Kodi Media Sensors."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="Kodi Media Sensors", data=user_input)

        data_schema = vol.Schema({
            vol.Required("host", default="127.0.0.1"): str,
            vol.Required("port_http", default=8080): int,
            vol.Required("port_ws", default=9090): int,
        })

        return self.async_show_form(step_id="user", data_schema=data_schema)

config_entries.HANDLERS.register(DOMAIN, KodiMediaSensorsConfigFlow)