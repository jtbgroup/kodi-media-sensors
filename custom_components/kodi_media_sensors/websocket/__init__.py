"""Central registry for Kodi Media Sensors WebSocket commands.

Each functional domain (playlist, search, ...) has its own module
exposing an `async_register_websockets` function. This file aggregates
them for a single registration entry point.
"""
import logging
import homeassistant.helpers.config_validation as cv
from homeassistant.core import HomeAssistant, callback

from . import playlist
from . import search

CONFIG_SCHEMA = cv.config_entry_only_config_schema

_LOGGER = logging.getLogger(__name__)


@callback
def async_register_websockets(hass: HomeAssistant) -> None:
    """Register all WebSocket commands for this integration."""
    playlist.async_register_websockets(hass)
    search.async_register_websockets(hass)
    _LOGGER.debug("All Kodi Media Sensors WebSocket commands registered")