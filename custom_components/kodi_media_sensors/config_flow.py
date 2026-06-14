import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import DOMAIN, CONF_LABEL, CONF_KODI_ENTITY


class KodiMediaSensorsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Kodi Media Sensors."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Initial step: select the Kodi instance to monitor."""
        errors = {}

        if user_input is not None:
            label = user_input.get(CONF_LABEL, "").strip()
            kodi_entity = user_input.get(CONF_KODI_ENTITY)

            if not label:
                errors[CONF_LABEL] = "label_required"
            elif not kodi_entity:
                errors[CONF_KODI_ENTITY] = "kodi_entity_required"
            else:
                # Prevent configuring the same Kodi entity twice
                for entry in self._async_current_entries():
                    if entry.data.get(CONF_KODI_ENTITY) == kodi_entity:
                        errors[CONF_KODI_ENTITY] = "already_configured"
                        break

                if not errors:
                    return self.async_create_entry(
                        title=label,
                        data={
                            CONF_LABEL: label,
                            CONF_KODI_ENTITY: kodi_entity,
                        },
                    )

        data_schema = vol.Schema({
            vol.Required(CONF_LABEL, default="My Kodi"): str,
            vol.Required(CONF_KODI_ENTITY): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="media_player", integration="kodi")
            ),
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )