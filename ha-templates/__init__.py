"""Central registry for Kodi Media Sensors WebSocket commands.

Each functional domain (playlist, player, library, ...) has its own
module exposing an `async_register_websockets` function. This file
aggregates them for a single registration entry point.
"""
import logging
from homeassistant.core import HomeAssistant, callback

from ...websocket import playlist

_LOGGER = logging.getLogger(__name__)


@callback
def async_register_websockets(hass: HomeAssistant) -> None:
    """Register all WebSocket commands for this integration."""
    playlist.async_register_websockets(hass)
    _LOGGER.debug("All Kodi Media Sensors WebSocket commands registered")