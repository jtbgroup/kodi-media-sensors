"""The Kodi Media Sensor integration."""

import asyncio
import logging

from homeassistant import config_entries, core

from .const import (
    OPTION_HIDE_WATCHED,
    OPTION_USE_AUTH_URL,
    DOMAIN,
    CONF_SENSOR_RECENTLY_ADDED_TVSHOW,
    CONF_SENSOR_RECENTLY_ADDED_MOVIE,
    CONF_SENSOR_PLAYLIST,
    CONF_KODI_INSTANCE,
)

_LOGGER = logging.getLogger(__name__)
PLATFORMS = ["sensor"]


async def async_setup_entry(
    hass: core.HomeAssistant, entry: config_entries.ConfigEntry
) -> bool:
    """Set up platforms from a ConfigEntry."""
    kodi_config_entry_id = entry.data[CONF_KODI_INSTANCE]
    sensor_recently_added_tvshow = entry.data[CONF_SENSOR_RECENTLY_ADDED_TVSHOW]
    sensor_recently_added_movie = entry.data[CONF_SENSOR_RECENTLY_ADDED_MOVIE]
    sensor_playlist = entry.data[CONF_SENSOR_PLAYLIST]
    unsub_options_update_listener = entry.add_update_listener(options_update_listener)
    hass.data[DOMAIN][entry.entry_id] = {
        OPTION_HIDE_WATCHED: entry.options.get(OPTION_HIDE_WATCHED, False),
        OPTION_USE_AUTH_URL: entry.options.get(OPTION_USE_AUTH_URL, False),
        CONF_KODI_INSTANCE: kodi_config_entry_id,
        CONF_SENSOR_RECENTLY_ADDED_TVSHOW: sensor_recently_added_tvshow,
        CONF_SENSOR_RECENTLY_ADDED_MOVIE: sensor_recently_added_movie,
        CONF_SENSOR_PLAYLIST: sensor_playlist,
        "unsub_options_update_listener": unsub_options_update_listener,
    }

    if not entry.unique_id:
        hass.config_entries.async_update_entry(entry, unique_id="kodi_media_sensors")

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
