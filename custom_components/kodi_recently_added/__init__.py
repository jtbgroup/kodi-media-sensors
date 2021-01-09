"""The Kodi Recently Added integration."""

import asyncio
import logging

from homeassistant import config_entries, core

from .const import CONF_HIDE_WATCHED, DOMAIN

_LOGGER = logging.getLogger(__name__)
PLATFORMS = ["sensor"]


async def async_setup_entry(
    hass: core.HomeAssistant, entry: config_entries.ConfigEntry
) -> bool:
    """Set up platforms from a ConfigEntry."""
    kodi_entry_id = entry.data["kodi_entry_id"]
    unsub_options_update_listener = entry.add_update_listener(options_update_listener)
    hass.data[DOMAIN][entry.entry_id] = {
        "hide_watched": entry.options.get(CONF_HIDE_WATCHED, False),
        "kodi_config_entry_id": kodi_entry_id,
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
    """Set up the Kodi Recently Added Media component from yaml configuration."""
    hass.data.setdefault(DOMAIN, {})
    return True
