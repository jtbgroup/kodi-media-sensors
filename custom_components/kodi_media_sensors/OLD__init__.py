"""The Kodi Media Sensor integration."""

import asyncio
import logging
import uuid

from homeassistant import config_entries, core

from .const import (
    CONF_KODI_INSTANCE,
    CONF_SENSOR_PLAYLIST,
    CONF_SENSOR_RECENTLY_ADDED_MOVIE,
    CONF_SENSOR_RECENTLY_ADDED_TVSHOW,
    CONF_SENSOR_SEARCH,
    DEFAULT_OPTION_SEARCH_ALBUMS_LIMIT,
    DEFAULT_OPTION_SEARCH_ARTISTS_LIMIT,
    DEFAULT_OPTION_SEARCH_CHANNELS_RADIO_LIMIT,
    DEFAULT_OPTION_SEARCH_CHANNELS_TV_LIMIT,
    DEFAULT_OPTION_SEARCH_EPISODES_LIMIT,
    DEFAULT_OPTION_SEARCH_KEEP_ALIVE_TIMER,
    DEFAULT_OPTION_SEARCH_MOVIES_LIMIT,
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
    OPTION_HIDE_WATCHED,
    OPTION_SEARCH_ALBUMS_LIMIT,
    OPTION_SEARCH_ARTISTS_LIMIT,
    OPTION_SEARCH_CHANNELS_RADIO_LIMIT,
    OPTION_SEARCH_CHANNELS_TV_LIMIT,
    OPTION_SEARCH_EPISODES_LIMIT,
    OPTION_SEARCH_KEEP_ALIVE_TIMER,
    OPTION_SEARCH_MOVIES_LIMIT,
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

_LOGGER = logging.getLogger(__name__)
PLATFORMS = ["sensor"]


async def async_setup_entry(
    hass: core.HomeAssistant, entry: config_entries.ConfigEntry
) -> bool:
    """Set up platforms from a ConfigEntry."""

    # A uuid is added to allow multiple instances
    # uuid_gen = uuid.uuid1().hex
    # entry.unique_id = "kodi_media_sensors-" + uuid_gen

    kodi_config_entry_id = entry.data[CONF_KODI_INSTANCE]
    sensor_recently_added_tvshow = entry.data[CONF_SENSOR_RECENTLY_ADDED_TVSHOW]
    sensor_recently_added_movie = entry.data[CONF_SENSOR_RECENTLY_ADDED_MOVIE]
    sensor_playlist = entry.data[CONF_SENSOR_PLAYLIST]
    sensor_search = entry.data[CONF_SENSOR_SEARCH]
    unsub_options_update_listener = entry.add_update_listener(options_update_listener)
    hass.data[DOMAIN][entry.entry_id] = {
        OPTION_HIDE_WATCHED: entry.options.get(OPTION_HIDE_WATCHED, False),
        OPTION_SEARCH_SONGS_LIMIT: entry.options.get(
            OPTION_SEARCH_SONGS_LIMIT, DEFAULT_OPTION_SEARCH_SONGS_LIMIT
        ),
        OPTION_SEARCH_ARTISTS_LIMIT: entry.options.get(
            OPTION_SEARCH_ARTISTS_LIMIT, DEFAULT_OPTION_SEARCH_ARTISTS_LIMIT
        ),
        OPTION_SEARCH_ALBUMS_LIMIT: entry.options.get(
            OPTION_SEARCH_ALBUMS_LIMIT, DEFAULT_OPTION_SEARCH_ALBUMS_LIMIT
        ),
        OPTION_SEARCH_MUSICVIDEOS_LIMIT: entry.options.get(
            OPTION_SEARCH_MUSICVIDEOS_LIMIT, DEFAULT_OPTION_SEARCH_MUSICVIDEOS_LIMIT
        ),
        OPTION_SEARCH_MOVIES_LIMIT: entry.options.get(
            OPTION_SEARCH_MOVIES_LIMIT, DEFAULT_OPTION_SEARCH_MOVIES_LIMIT
        ),
        OPTION_SEARCH_TVSHOWS_LIMIT: entry.options.get(
            OPTION_SEARCH_TVSHOWS_LIMIT, DEFAULT_OPTION_SEARCH_TVSHOWS_LIMIT
        ),
        OPTION_SEARCH_CHANNELS_TV_LIMIT: entry.options.get(
            OPTION_SEARCH_CHANNELS_TV_LIMIT, DEFAULT_OPTION_SEARCH_CHANNELS_TV_LIMIT
        ),
        OPTION_SEARCH_CHANNELS_RADIO_LIMIT: entry.options.get(
            OPTION_SEARCH_CHANNELS_RADIO_LIMIT,
            DEFAULT_OPTION_SEARCH_CHANNELS_RADIO_LIMIT,
        ),
        OPTION_SEARCH_EPISODES_LIMIT: entry.options.get(
            OPTION_SEARCH_EPISODES_LIMIT, DEFAULT_OPTION_SEARCH_EPISODES_LIMIT
        ),
        OPTION_SEARCH_RECENTLY_ADDED_SONGS_LIMIT: entry.options.get(
            OPTION_SEARCH_RECENTLY_ADDED_SONGS_LIMIT,
            DEFAULT_OPTION_SEARCH_RECENTLY_ADDED_SONGS_LIMIT,
        ),
        OPTION_SEARCH_RECENTLY_ADDED_ALBUMS_LIMIT: entry.options.get(
            OPTION_SEARCH_RECENTLY_ADDED_ALBUMS_LIMIT,
            DEFAULT_OPTION_SEARCH_RECENTLY_ADDED_ALBUMS_LIMIT,
        ),
        OPTION_SEARCH_RECENTLY_ADDED_MOVIES_LIMIT: entry.options.get(
            OPTION_SEARCH_RECENTLY_ADDED_MOVIES_LIMIT,
            DEFAULT_OPTION_SEARCH_RECENTLY_ADDED_MOVIES_LIMIT,
        ),
        OPTION_SEARCH_RECENTLY_ADDED_MUSICVIDEOS_LIMIT: entry.options.get(
            OPTION_SEARCH_RECENTLY_ADDED_MUSICVIDEOS_LIMIT,
            DEFAULT_OPTION_SEARCH_RECENTLY_ADDED_MUSICVIDEOS_LIMIT,
        ),
        OPTION_SEARCH_RECENTLY_ADDED_EPISODES_LIMIT: entry.options.get(
            OPTION_SEARCH_RECENTLY_ADDED_EPISODES_LIMIT,
            DEFAULT_OPTION_SEARCH_RECENTLY_ADDED_EPISODES_LIMIT,
        ),
        OPTION_SEARCH_RECENTLY_PLAYED_SONGS_LIMIT: entry.options.get(
            OPTION_SEARCH_RECENTLY_PLAYED_SONGS_LIMIT,
            DEFAULT_OPTION_SEARCH_RECENTLY_PLAYED_SONGS_LIMIT,
        ),
        OPTION_SEARCH_RECENTLY_PLAYED_ALBUMS_LIMIT: entry.options.get(
            OPTION_SEARCH_RECENTLY_PLAYED_ALBUMS_LIMIT,
            DEFAULT_OPTION_SEARCH_RECENTLY_PLAYED_ALBUMS_LIMIT,
        ),
        OPTION_SEARCH_KEEP_ALIVE_TIMER: entry.options.get(
            OPTION_SEARCH_KEEP_ALIVE_TIMER, DEFAULT_OPTION_SEARCH_KEEP_ALIVE_TIMER
        ),
        CONF_KODI_INSTANCE: kodi_config_entry_id,
        CONF_SENSOR_RECENTLY_ADDED_TVSHOW: sensor_recently_added_tvshow,
        CONF_SENSOR_RECENTLY_ADDED_MOVIE: sensor_recently_added_movie,
        CONF_SENSOR_PLAYLIST: sensor_playlist,
        CONF_SENSOR_SEARCH: sensor_search,
        "unsub_options_update_listener": unsub_options_update_listener,
    }

    if not entry.unique_id:
        hass.config_entries.async_update_entry(
            entry, unique_id="kodi_media_sensors-" + entry.entry_id
        )

    for component in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, component)
        )

    return True


async def async_unload_entry(
    hass: core.HomeAssistant, entry: config_entries.ConfigEntry
) -> bool:
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
            ]
        )
    )
    # Remove options_update_listener.
    hass.data[DOMAIN][entry.entry_id]["unsub_options_update_listener"]()

    # Remove config entry from domain.
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def options_update_listener(
    hass: core.HomeAssistant, config_entry: config_entries.ConfigEntry
):
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)


async def async_setup(hass: core.HomeAssistant, config: dict) -> bool:
    """Set up the Kodi Media Sensor component from yaml configuration."""
    hass.data.setdefault(DOMAIN, {})
    return True
