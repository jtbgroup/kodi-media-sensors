import logging
import voluptuous as vol
import asyncio
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


@callback
def async_register_websockets(hass: HomeAssistant) -> None:
    """Enregistre les commandes WebSocket de l'intégration."""
    _LOGGER.debug("Enregistrement de la commande WebSocket subscribe")
    websocket_api.async_register_command(hass, websocket_subscribe)


@websocket_api.websocket_command({
    vol.Required("type"): "kodi_media_sensors/subscribe",
    vol.Required("entry_id"): str,
})
@websocket_api.async_response
async def websocket_subscribe(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict,
) -> None:
    """Subscribe to playlist updates for a specific Kodi instance."""
    
    entry_id = msg["entry_id"]
    _LOGGER.debug("WebSocket subscribe demandé pour entry_id=%s", entry_id)
    
    # Récupérer l'intégration correspondante
    config_entry = hass.config_entries.async_get_entry(entry_id)
    
    if not config_entry or config_entry.domain != DOMAIN:
        _LOGGER.error("Entry %s not found or invalid domain", entry_id)
        connection.send_error(msg["id"], "invalid_entry", f"Entry {entry_id} not found")
        return
    
    _LOGGER.info("Subscription confirmée pour %s", entry_id)
    
    # Envoyer immédiatement une confirmation
    connection.send_result(msg["id"])
    
    # Envoyer un message de test
    connection.send_message(websocket_api.event_message(msg["id"], {
        "type": "playlist_update",
        "items": [
            {"title": "Test Song 1", "artist": "Test Artist", "duration": 180},
            {"title": "Test Song 2", "artist": "Test Artist", "duration": 200},
        ]
    }))
    
    _LOGGER.debug("Message de test envoyé au client")