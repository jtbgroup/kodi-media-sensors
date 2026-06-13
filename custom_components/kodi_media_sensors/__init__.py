import logging
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from .websocket import async_register_websockets

_LOGGER = logging.getLogger(__name__)
DOMAIN = "kodi_media_sensors"

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the integration (Global registration)."""
    # Register the custom realtime WebSocket endpoints once
    async_register_websockets(hass)
    _LOGGER.info("Kodi Media Sensors WebSocket API registered successfully.")
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the integration from a config flow UI entry."""
    return True