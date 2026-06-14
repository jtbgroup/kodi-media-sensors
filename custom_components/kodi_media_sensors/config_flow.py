import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import DOMAIN, CONF_LABEL


class KodiMediaSensorsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow pour Kodi Media Sensors."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Étape initiale : affiche le formulaire de config."""
        errors = {}

        if user_input is not None:
            # Minimal validation: label can't be empty
            if not user_input.get(CONF_LABEL, "").strip():
                errors[CONF_LABEL] = "label_required"
            else:
                return self.async_create_entry(
                    title=user_input[CONF_LABEL],
                    data=user_input,
                )

        data_schema = vol.Schema({
            vol.Required(CONF_LABEL, default="Mon Kodi"): str,
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )