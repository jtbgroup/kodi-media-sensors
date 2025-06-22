import asyncio
import logging

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

_LOGGER = logging.getLogger(__name__)
PLATFORMS = ["sensor"]


async def async_setup(hass: core.HomeAssistant, config: dict) -> bool:
    """Set up the Kodi Media Sensor component from yaml configuration."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass, config: config_entries.ConfigEntries):
    """Set up platforms from a ConfigEntry."""

    kodi_config_entry_id = config.data[CONF_KODI_INSTANCE]
    sensor_recently_added_tvshow = config.data[CONF_SENSOR_RECENTLY_ADDED_TVSHOW]
    sensor_recently_added_movie = config.data[CONF_SENSOR_RECENTLY_ADDED_MOVIE]
    sensor_playlist = config.data[CONF_SENSOR_PLAYLIST]
    sensor_search = config.data[CONF_SENSOR_SEARCH]
    unsub_options_update_listener = config.add_update_listener(options_update_listener)
    hass.data[DOMAIN][config.entry_id] = {
        OPTION_HIDE_WATCHED: config.options.get(OPTION_HIDE_WATCHED, False),
        OPTION_SEARCH_SONGS_LIMIT: config.options.get(
            OPTION_SEARCH_SONGS_LIMIT, DEFAULT_OPTION_SEARCH_SONGS_LIMIT
        ),
        OPTION_SEARCH_ARTISTS_LIMIT: config.options.get(
            OPTION_SEARCH_ARTISTS_LIMIT, DEFAULT_OPTION_SEARCH_ARTISTS_LIMIT
        ),
        OPTION_SEARCH_ALBUMS_LIMIT: config.options.get(
            OPTION_SEARCH_ALBUMS_LIMIT, DEFAULT_OPTION_SEARCH_ALBUMS_LIMIT
        ),
        OPTION_SEARCH_MUSICVIDEOS_LIMIT: config.options.get(
            OPTION_SEARCH_MUSICVIDEOS_LIMIT, DEFAULT_OPTION_SEARCH_MUSICVIDEOS_LIMIT
        ),
        OPTION_SEARCH_MOVIES_LIMIT: config.options.get(
            OPTION_SEARCH_MOVIES_LIMIT, DEFAULT_OPTION_SEARCH_MOVIES_LIMIT
        ),
        OPTION_SEARCH_TVSHOWS_LIMIT: config.options.get(
            OPTION_SEARCH_TVSHOWS_LIMIT, DEFAULT_OPTION_SEARCH_TVSHOWS_LIMIT
        ),
        OPTION_SEARCH_CHANNELS_TV_LIMIT: config.options.get(
            OPTION_SEARCH_CHANNELS_TV_LIMIT, DEFAULT_OPTION_SEARCH_CHANNELS_TV_LIMIT
        ),
        OPTION_SEARCH_CHANNELS_RADIO_LIMIT: config.options.get(
            OPTION_SEARCH_CHANNELS_RADIO_LIMIT,
            DEFAULT_OPTION_SEARCH_CHANNELS_RADIO_LIMIT,
        ),
        OPTION_SEARCH_EPISODES_LIMIT: config.options.get(
            OPTION_SEARCH_EPISODES_LIMIT, DEFAULT_OPTION_SEARCH_EPISODES_LIMIT
        ),
        OPTION_SEARCH_MUSIC_PLAYLISTS_LIMIT: config.options.get(
            OPTION_SEARCH_MUSIC_PLAYLISTS_LIMIT,
            DEFAULT_OPTION_SEARCH_MUSIC_PLAYLISTS_LIMIT,
        ),
        OPTION_SEARCH_RECENTLY_ADDED_SONGS_LIMIT: config.options.get(
            OPTION_SEARCH_RECENTLY_ADDED_SONGS_LIMIT,
            DEFAULT_OPTION_SEARCH_RECENTLY_ADDED_SONGS_LIMIT,
        ),
        OPTION_SEARCH_RECENTLY_ADDED_ALBUMS_LIMIT: config.options.get(
            OPTION_SEARCH_RECENTLY_ADDED_ALBUMS_LIMIT,
            DEFAULT_OPTION_SEARCH_RECENTLY_ADDED_ALBUMS_LIMIT,
        ),
        OPTION_SEARCH_RECENTLY_ADDED_MOVIES_LIMIT: config.options.get(
            OPTION_SEARCH_RECENTLY_ADDED_MOVIES_LIMIT,
            DEFAULT_OPTION_SEARCH_RECENTLY_ADDED_MOVIES_LIMIT,
        ),
        OPTION_SEARCH_RECENTLY_ADDED_MUSICVIDEOS_LIMIT: config.options.get(
            OPTION_SEARCH_RECENTLY_ADDED_MUSICVIDEOS_LIMIT,
            DEFAULT_OPTION_SEARCH_RECENTLY_ADDED_MUSICVIDEOS_LIMIT,
        ),
        OPTION_SEARCH_RECENTLY_ADDED_EPISODES_LIMIT: config.options.get(
            OPTION_SEARCH_RECENTLY_ADDED_EPISODES_LIMIT,
            DEFAULT_OPTION_SEARCH_RECENTLY_ADDED_EPISODES_LIMIT,
        ),
        OPTION_SEARCH_RECENTLY_PLAYED_SONGS_LIMIT: config.options.get(
            OPTION_SEARCH_RECENTLY_PLAYED_SONGS_LIMIT,
            DEFAULT_OPTION_SEARCH_RECENTLY_PLAYED_SONGS_LIMIT,
        ),
        OPTION_SEARCH_RECENTLY_PLAYED_ALBUMS_LIMIT: config.options.get(
            OPTION_SEARCH_RECENTLY_PLAYED_ALBUMS_LIMIT,
            DEFAULT_OPTION_SEARCH_RECENTLY_PLAYED_ALBUMS_LIMIT,
        ),
        OPTION_SEARCH_KEEP_ALIVE_TIMER: config.options.get(
            OPTION_SEARCH_KEEP_ALIVE_TIMER, DEFAULT_OPTION_SEARCH_KEEP_ALIVE_TIMER
        ),
        CONF_KODI_INSTANCE: kodi_config_entry_id,
        CONF_SENSOR_RECENTLY_ADDED_TVSHOW: sensor_recently_added_tvshow,
        CONF_SENSOR_RECENTLY_ADDED_MOVIE: sensor_recently_added_movie,
        CONF_SENSOR_PLAYLIST: sensor_playlist,
        CONF_SENSOR_SEARCH: sensor_search,
        "unsub_options_update_listener": unsub_options_update_listener,
    }

    # for component in PLATFORMS:
    #     hass.async_create_task(
    await hass.config_entries.async_forward_entry_setups(config, PLATFORMS)
    # )

    return True


async def options_update_listener(
    hass: core.HomeAssistant, config_entry: config_entries.ConfigEntry
):
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)


async def async_unload_entry(
    hass: core.HomeAssistant, entry: config_entries.ConfigEntry
) -> bool:
    """Unload a config entry."""
    _LOGGER.debug(f"async_unload_entry entry [{entry.entry_id}]")

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    # Remove options_update_listener.
    hass.data[DOMAIN][entry.entry_id]["unsub_options_update_listener"]()

    # Remove config entry from domain.
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
