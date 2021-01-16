import logging
from typing import Any, Dict, Optional

from homeassistant import config_entries
from homeassistant.components.kodi.const import DOMAIN as KODI_DOMAIN
from homeassistant.core import callback
import voluptuous as vol

from .const import (
    OPTION_HIDE_WATCHED,
    CONF_KODI_INSTANCE,
    DOMAIN,
    CONF_SENSOR_RECENTLY_ADDED_TVSHOW,
    CONF_SENSOR_RECENTLY_ADDED_MOVIE,
    CONF_SENSOR_PLAYLIST,
)

_LOGGER = logging.getLogger(__name__)


class KodiMediaSensorsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Kodi Media Sensors config flow."""

    async def async_step_user(self, user_input: Optional[Dict[str, Any]]):
        """Handle a flow initialized via the user interface."""
        # Find all configured kodi instances to allow the user to select one.
        kodi_instances: Dict[str, str] = {
            entry.entry_id: entry.title
            for entry in self.hass.config_entries.async_entries(KODI_DOMAIN)
            if entry.source != "ignore"
        }
        data_schema = vol.Schema(
            {
                vol.Required(CONF_KODI_INSTANCE): vol.In(list(kodi_instances.values())),
                vol.Optional(CONF_SENSOR_RECENTLY_ADDED_TVSHOW, default=False): bool,
                vol.Optional(CONF_SENSOR_RECENTLY_ADDED_MOVIE, default=False): bool,
                vol.Optional(CONF_SENSOR_PLAYLIST, default=False): bool,
            }
        )

        errors = {}
        if not kodi_instances:
            errors["base"] = "kodi_not_configured"

        if user_input is not None:
            config_entry_id: Optional[str] = None
            for entry_id, title in kodi_instances.items():
                if title == user_input[CONF_KODI_INSTANCE]:
                    config_entry_id = entry_id
                    break
            if config_entry_id is None:
                errors["base"] = "kodi_not_configured"

            if not errors:
                return self.async_create_entry(
                    title="Kodi Media Sensors",
                    data={
                        CONF_KODI_INSTANCE: config_entry_id,
                        CONF_SENSOR_RECENTLY_ADDED_TVSHOW: user_input[
                            CONF_SENSOR_RECENTLY_ADDED_TVSHOW
                        ],
                        CONF_SENSOR_RECENTLY_ADDED_MOVIE: user_input[
                            CONF_SENSOR_RECENTLY_ADDED_MOVIE
                        ],
                        CONF_SENSOR_PLAYLIST: user_input[CONF_SENSOR_PLAYLIST],
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handles options flow for the component."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        hide_watched = self.config_entry.options.get(OPTION_HIDE_WATCHED, False)

        options_schema = vol.Schema(
            {vol.Optional(OPTION_HIDE_WATCHED, default=hide_watched): bool}
        )
        return self.async_show_form(
            step_id="init",
            data_schema=options_schema,
        )
