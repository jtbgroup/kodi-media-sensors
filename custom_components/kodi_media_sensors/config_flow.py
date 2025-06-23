from __future__ import annotations

from typing import Optional

from homeassistant import config_entries
from homeassistant.components.kodi.const import DOMAIN as KODI_DOMAIN
from homeassistant.core import callback
import voluptuous as vol

from .const import (
    CONF_KODI_INSTANCE,
    CONF_SENSOR_PLAYLIST,
    CONF_SENSOR_RECENTLY_ADDED_MOVIE,
    CONF_SENSOR_RECENTLY_ADDED_TVSHOW,
    CONF_SENSOR_SEARCH,
    DEFAULT_OPTION_HIDE_WATCHED,
    DEFAULT_OPTION_SEARCH_ALBUMS_LIMIT,
    DEFAULT_OPTION_SEARCH_ARTISTS_LIMIT,
    DEFAULT_OPTION_SEARCH_CHANNELS_RADIO_LIMIT,
    DEFAULT_OPTION_SEARCH_CHANNELS_TV_LIMIT,
    DEFAULT_OPTION_SEARCH_EPISODES_LIMIT,
    DEFAULT_OPTION_SEARCH_KEEP_ALIVE_TIMER,
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
    DOMAIN,
    MAX_KEEP_ALIVE,
    MAX_SEARCH_LIMIT,
    OPTION_HIDE_WATCHED,
    OPTION_SEARCH_ALBUMS_LIMIT,
    OPTION_SEARCH_ARTISTS_LIMIT,
    OPTION_SEARCH_CHANNELS_RADIO_LIMIT,
    OPTION_SEARCH_CHANNELS_TV_LIMIT,
    OPTION_SEARCH_EPISODES_LIMIT,
    OPTION_SEARCH_KEEP_ALIVE_TIMER,
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
    async def async_step_user(self, user_input):
        # Find all configured kodi instances to allow the user to select one.

        _in_use = list()
        _kms = self.hass.config_entries.async_entries(DOMAIN)
        for kms in _kms:
            _in_use.append(kms.data[CONF_KODI_INSTANCE])

        _kodi_instances: dict[str, str] = {
            entry.entry_id: entry.title
            for entry in self.hass.config_entries.async_entries(KODI_DOMAIN)
            if entry.source != "ignore" and entry.entry_id not in _in_use
        }

        _data_schema = vol.Schema(
            {
                vol.Required(CONF_KODI_INSTANCE): vol.In(
                    list(_kodi_instances.values())
                ),
                vol.Optional(CONF_SENSOR_RECENTLY_ADDED_TVSHOW, default=False): bool,
                vol.Optional(CONF_SENSOR_RECENTLY_ADDED_MOVIE, default=False): bool,
                vol.Optional(CONF_SENSOR_PLAYLIST, default=False): bool,
                vol.Optional(CONF_SENSOR_SEARCH, default=False): bool,
            }
        )

        errors = {}

        if not _kodi_instances:
            errors["base"] = "kodi_not_configured"

        selected_kodi_title = ""
        if user_input is not None:
            config_entry_id: str | None = None
            for entry_id, title in _kodi_instances.items():
                if title == user_input[CONF_KODI_INSTANCE]:
                    config_entry_id = entry_id
                    selected_kodi_title = title
                    break
            if config_entry_id is None:
                errors["base"] = "kodi_not_configured"

            if not errors:
                return self.async_create_entry(
                    title="Kodi Media Sensors (" + selected_kodi_title + ")",
                    data={
                        CONF_KODI_INSTANCE: config_entry_id,
                        CONF_SENSOR_RECENTLY_ADDED_TVSHOW: user_input[
                            CONF_SENSOR_RECENTLY_ADDED_TVSHOW
                        ],
                        CONF_SENSOR_RECENTLY_ADDED_MOVIE: user_input[
                            CONF_SENSOR_RECENTLY_ADDED_MOVIE
                        ],
                        CONF_SENSOR_PLAYLIST: user_input[CONF_SENSOR_PLAYLIST],
                        CONF_SENSOR_SEARCH: user_input[CONF_SENSOR_SEARCH],
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_data_schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        # return OptionsFlowHandler(config_entry)
        return OptionsFlowHandler()


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handles options flow for the component."""

    # def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
    #     self.config_entry = config_entry
    @property
    def config_entry(self):
        return self.hass.config_entries.async_get_entry(self.handler)

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        schema_base = {}

        sensor_recent_movie_active = self.config_entry.data.get(
            CONF_SENSOR_RECENTLY_ADDED_MOVIE
        )
        sensor_recent_tvshow_active = self.config_entry.data.get(
            CONF_SENSOR_RECENTLY_ADDED_TVSHOW
        )
        sensor_search_active = self.config_entry.data.get(CONF_SENSOR_SEARCH)

        if (
            sensor_recent_movie_active is not None
            and str(sensor_recent_movie_active) == "True"
        ) or (
            sensor_recent_tvshow_active is not None
            and str(sensor_recent_tvshow_active) == "True"
        ):
            schema_base = self.add_to_schema(
                OPTION_HIDE_WATCHED,
                DEFAULT_OPTION_HIDE_WATCHED,
                bool,
                schema_base,
            )

        if sensor_search_active is not None and str(sensor_search_active) == "True":
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

            # SEARCH CHANNELS TV
            schema_base = self.add_int_to_schema(
                OPTION_SEARCH_CHANNELS_TV_LIMIT,
                DEFAULT_OPTION_SEARCH_CHANNELS_TV_LIMIT,
                0,
                MAX_SEARCH_LIMIT,
                schema_base,
            )

            # SEARCH CHANNELS RADIO
            schema_base = self.add_int_to_schema(
                OPTION_SEARCH_CHANNELS_RADIO_LIMIT,
                DEFAULT_OPTION_SEARCH_CHANNELS_RADIO_LIMIT,
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
                0,
                MAX_SEARCH_LIMIT,
                schema_base,
            )
            schema_base = self.add_int_to_schema(
                OPTION_SEARCH_RECENTLY_PLAYED_ALBUMS_LIMIT,
                DEFAULT_OPTION_SEARCH_RECENTLY_PLAYED_ALBUMS_LIMIT,
                0,
                MAX_SEARCH_LIMIT,
                schema_base,
            )

            # SEARCH KEEP ALIVE TIMER
            schema_base = self.add_int_to_schema(
                OPTION_SEARCH_KEEP_ALIVE_TIMER,
                DEFAULT_OPTION_SEARCH_KEEP_ALIVE_TIMER,
                0,
                MAX_KEEP_ALIVE,
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
