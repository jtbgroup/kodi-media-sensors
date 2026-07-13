import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector
from homeassistant.core import callback


from .const import (
    DOMAIN,
    CONF_LABEL,
    CONF_KODI_ENTITY,
    DEFAULT_OPTION_SEARCH_ALBUMS_LIMIT,
    DEFAULT_OPTION_SEARCH_ARTISTS_LIMIT,
    DEFAULT_OPTION_SEARCH_CHANNELS_LIMIT,
    DEFAULT_OPTION_SEARCH_EPISODES_LIMIT,
    DEFAULT_OPTION_SEARCH_MOVIES_LIMIT,
    DEFAULT_OPTION_SEARCH_MUSIC_PLAYLISTS_LIMIT,
    DEFAULT_OPTION_SEARCH_MUSICVIDEOS_LIMIT,
    DEFAULT_OPTION_SEARCH_RECENTLY_ADDED_ALBUMS_LIMIT,
    DEFAULT_OPTION_SEARCH_RECENTLY_ADDED_EPISODES_LIMIT,
    DEFAULT_OPTION_SEARCH_RECENTLY_ADDED_MOVIES_LIMIT,
    DEFAULT_OPTION_SEARCH_RECENTLY_ADDED_MUSICVIDEOS_LIMIT,
    DEFAULT_OPTION_SEARCH_RECENTLY_ADDED_SONGS_LIMIT,
    DEFAULT_OPTION_SEARCH_RECENTLY_PLAYED_ALBUMS_LIMIT,
    DEFAULT_OPTION_SEARCH_RECENTLY_PLAYED_SONGS_LIMIT,
    DEFAULT_OPTION_SEARCH_SONGS_LIMIT,
    DEFAULT_OPTION_SEARCH_TVSHOWS_LIMIT,
    MAX_SEARCH_LIMIT,
    MIN_SEARCH_RECENTLY_PLAYED,
    OPTION_SEARCH_ALBUMS_LIMIT,
    OPTION_SEARCH_ARTISTS_LIMIT,
    OPTION_SEARCH_CHANNELS_LIMIT,
    OPTION_SEARCH_EPISODES_LIMIT,
    OPTION_SEARCH_MOVIES_LIMIT,
    OPTION_SEARCH_MUSIC_PLAYLISTS_LIMIT,
    OPTION_SEARCH_MUSICVIDEOS_LIMIT,
    OPTION_SEARCH_RECENTLY_ADDED_ALBUMS_LIMIT,
    OPTION_SEARCH_RECENTLY_ADDED_EPISODES_LIMIT,
    OPTION_SEARCH_RECENTLY_ADDED_MOVIES_LIMIT,
    OPTION_SEARCH_RECENTLY_ADDED_MUSICVIDEOS_LIMIT,
    OPTION_SEARCH_RECENTLY_ADDED_SONGS_LIMIT,
    OPTION_SEARCH_RECENTLY_PLAYED_ALBUMS_LIMIT,
    OPTION_SEARCH_RECENTLY_PLAYED_SONGS_LIMIT,
    OPTION_SEARCH_SONGS_LIMIT,
    OPTION_SEARCH_TVSHOWS_LIMIT,
)


class KodiMediaSensorsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Kodi Media Sensors."""

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

        data_schema = vol.Schema(
            {
                vol.Required(CONF_LABEL, default="My Kodi"): str,
                vol.Required(CONF_KODI_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="media_player", integration="kodi"
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler()


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handles options flow for the component."""

    @property
    def config_entry(self):
        return self.hass.config_entries.async_get_entry(self.handler)

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        schema_base = {}

        # SEARCH SONGS
        schema_base = self.add_int_to_schema(
            OPTION_SEARCH_SONGS_LIMIT,
            int(DEFAULT_OPTION_SEARCH_SONGS_LIMIT),
            0,
            MAX_SEARCH_LIMIT,
            schema_base,
        )

        # SEARCH ALBUMS
        schema_base = self.add_int_to_schema(
            OPTION_SEARCH_ALBUMS_LIMIT,
            DEFAULT_OPTION_SEARCH_ALBUMS_LIMIT,
            0,
            MAX_SEARCH_LIMIT,
            schema_base,
        )

        # SEARCH ARTISTS
        schema_base = self.add_int_to_schema(
            OPTION_SEARCH_ARTISTS_LIMIT,
            DEFAULT_OPTION_SEARCH_ARTISTS_LIMIT,
            0,
            MAX_SEARCH_LIMIT,
            schema_base,
        )

        # SEARCH MUSIC_VIDEOS
        schema_base = self.add_int_to_schema(
            OPTION_SEARCH_MUSICVIDEOS_LIMIT,
            DEFAULT_OPTION_SEARCH_MUSICVIDEOS_LIMIT,
            0,
            MAX_SEARCH_LIMIT,
            schema_base,
        )

        # SEARCH MOVIES
        schema_base = self.add_int_to_schema(
            OPTION_SEARCH_MOVIES_LIMIT,
            DEFAULT_OPTION_SEARCH_MOVIES_LIMIT,
            0,
            MAX_SEARCH_LIMIT,
            schema_base,
        )

        # SEARCH TVSHOWS
        schema_base = self.add_int_to_schema(
            OPTION_SEARCH_TVSHOWS_LIMIT,
            DEFAULT_OPTION_SEARCH_TVSHOWS_LIMIT,
            0,
            MAX_SEARCH_LIMIT,
            schema_base,
        )

        # SEARCH EPISODES
        schema_base = self.add_int_to_schema(
            OPTION_SEARCH_EPISODES_LIMIT,
            DEFAULT_OPTION_SEARCH_EPISODES_LIMIT,
            0,
            MAX_SEARCH_LIMIT,
            schema_base,
        )

        # SEARCH CHANNELS
        schema_base = self.add_int_to_schema(
            OPTION_SEARCH_CHANNELS_LIMIT,
            DEFAULT_OPTION_SEARCH_CHANNELS_LIMIT,
            0,
            MAX_SEARCH_LIMIT,
            schema_base,
        )

        # SEARCH PLAYLIST
        schema_base = self.add_int_to_schema(
            OPTION_SEARCH_MUSIC_PLAYLISTS_LIMIT,
            DEFAULT_OPTION_SEARCH_MUSIC_PLAYLISTS_LIMIT,
            0,
            MAX_SEARCH_LIMIT,
            schema_base,
        )

        # SEARCH RECENTLY ADDED
        schema_base = self.add_int_to_schema(
            OPTION_SEARCH_RECENTLY_ADDED_SONGS_LIMIT,
            DEFAULT_OPTION_SEARCH_RECENTLY_ADDED_SONGS_LIMIT,
            0,
            MAX_SEARCH_LIMIT,
            schema_base,
        )
        schema_base = self.add_int_to_schema(
            OPTION_SEARCH_RECENTLY_ADDED_ALBUMS_LIMIT,
            DEFAULT_OPTION_SEARCH_RECENTLY_ADDED_ALBUMS_LIMIT,
            0,
            MAX_SEARCH_LIMIT,
            schema_base,
        )
        schema_base = self.add_int_to_schema(
            OPTION_SEARCH_RECENTLY_ADDED_MOVIES_LIMIT,
            DEFAULT_OPTION_SEARCH_RECENTLY_ADDED_MOVIES_LIMIT,
            0,
            MAX_SEARCH_LIMIT,
            schema_base,
        )
        schema_base = self.add_int_to_schema(
            OPTION_SEARCH_RECENTLY_ADDED_MUSICVIDEOS_LIMIT,
            DEFAULT_OPTION_SEARCH_RECENTLY_ADDED_MUSICVIDEOS_LIMIT,
            0,
            MAX_SEARCH_LIMIT,
            schema_base,
        )
        schema_base = self.add_int_to_schema(
            OPTION_SEARCH_RECENTLY_ADDED_EPISODES_LIMIT,
            DEFAULT_OPTION_SEARCH_RECENTLY_ADDED_EPISODES_LIMIT,
            0,
            MAX_SEARCH_LIMIT,
            schema_base,
        )

        # SEARCH RECENTLT PLAYED
        schema_base = self.add_int_to_schema(
            OPTION_SEARCH_RECENTLY_PLAYED_SONGS_LIMIT,
            DEFAULT_OPTION_SEARCH_RECENTLY_PLAYED_SONGS_LIMIT,
            MIN_SEARCH_RECENTLY_PLAYED,
            MAX_SEARCH_LIMIT,
            schema_base,
        )
        schema_base = self.add_int_to_schema(
            OPTION_SEARCH_RECENTLY_PLAYED_ALBUMS_LIMIT,
            DEFAULT_OPTION_SEARCH_RECENTLY_PLAYED_ALBUMS_LIMIT,
            MIN_SEARCH_RECENTLY_PLAYED,
            MAX_SEARCH_LIMIT,
            schema_base,
        )

        schema_full = vol.Schema(schema_base)
        return self.async_show_form(
            step_id="init",
            data_schema=schema_full,
        )

    def add_to_schema(self, option, default, value_type, schema):
        option_value = self.config_entry.options.get(option, default)
        if value_type == bool:
            schema[vol.Optional(option, default=option_value)] = bool

        elif value_type == int:
            schema[vol.Optional(option, default=option_value)] = int

        return schema

    def add_int_to_schema(self, option, default, option_min, option_max, schema):
        option_value = self.config_entry.options.get(option, default)
        schema[vol.Required(option, default=option_value)] = vol.All(
            int, vol.Range(min=option_min, max=option_max)
        )

        return schema
