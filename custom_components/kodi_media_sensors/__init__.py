import logging
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from .const import DOMAIN, CONF_LABEL

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Setup via configuration.yaml — not used, but required."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the integration from the UI."""

    label = entry.data.get(CONF_LABEL, "unknown")
    _LOGGER.info("Kodi Media Sensors started — label: '%s'", label)

    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "label": label,
    }

    # IMPORTANT: register WebSocket commands without awaiting.
    # They must be registered at the domain level, not per entry.
    _async_setup_websocket(hass)
    _LOGGER.info("WebSocket kodi_media_sensors commands registered.")

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Clean up when the integration is removed."""
    hass.data[DOMAIN].pop(entry.entry_id, None)
    _LOGGER.info("Kodi Media Sensors unloaded.")
    return True


def _async_setup_websocket(hass: HomeAssistant) -> None:
    """Register WebSocket commands.

    Called from async_setup_entry to ensure registration happens
    before any client connects.
    """
    # Local import to avoid circular dependencies
    from .websocket import async_register_websockets

    # This is a @callback and must be called synchronously
    async_register_websockets(hass)