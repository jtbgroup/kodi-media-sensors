from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from .const import DOMAIN
from .websocket import async_register_websockets
import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Ancienne méthode : maintenant juste une sécurité."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Chargement via UI : C'est ici que tout se passe maintenant !"""
    
    # 1. Register the WebSocket
    async_register_websockets(hass)
    
    # 2. Store config data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data
    
    _LOGGER.info("Kodi Media Sensors initialisé via l'UI avec succès.")
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Requis pour permettre de supprimer l'intégration proprement."""
    return True