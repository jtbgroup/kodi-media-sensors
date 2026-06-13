import voluptuous as vol
import asyncio
import logging
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from pykodi import Kodi

_LOGGER = logging.getLogger(__name__)

@callback
def async_register_websockets(hass: HomeAssistant) -> None:
    """Register WebSocket commands for the integration."""
    websocket_api.async_register_command(hass, websocket_subscribe_playlist)

# Schema expects the entity_id from the frontend card
SCHEMA_SUBSCRIBE_PLAYLIST = websocket_api.BASE_COMMAND_SCHEMA.extend(
    {
        vol.Required("type"): "kodi_media_sensors/subscribe_playlist",
        vol.Required("entity_id"): str,
    }
)

@websocket_api.websocket_command(SCHEMA_SUBSCRIBE_PLAYLIST)
@websocket_api.async_response
async def websocket_subscribe_playlist(
    hass: HomeAssistant, 
    connection: websocket_api.ActiveConnection, 
    msg: dict
) -> None:
    """Handle a long-lived WebSocket subscription mapped to a HA entity."""
    
    entity_id = msg["entity_id"]
    
    # 1. Retrieve the entity from the Home Assistant Entity Registry
    entity_reg = er.async_get(hass)
    entity_entry = entity_reg.async_get(entity_id)
    
    if not entity_entry or not entity_entry.config_entry_id:
        connection.send_error(msg["id"], "invalid_entity", f"Entity {entity_id} not found or not linked to an integration.")
        return

    # 2. Fetch the ConfigEntry to extract the network settings
    config_entry = hass.config_entries.async_get_entry(entity_entry.config_entry_id)
    
    if not config_entry:
        connection.send_error(msg["id"], "config_not_found", "Could not retrieve configuration for this entity.")
        return

    host = config_entry.data.get("host")
    port_http = config_entry.data.get("port_http", 8080)
    port_ws = config_entry.data.get("port_ws", 9090)

    kodi_client = Kodi(host, port_http=port_http, port_ws=port_ws)

    # Acknowledge the subscription request
    connection.send_result(msg["id"])

    async def send_current_playlist():
        """Fetch the active playlist from Kodi and push it to the frontend."""
        try:
            playlist_data = await kodi_client.call_method(
                "Playlist.GetItems", playlistid=0, properties=["title", "artist", "duration"]
            )
            connection.send_message(
                websocket_api.event_message(msg["id"], {
                    "event_type": "playlist_updated",
                    "playlist": playlist_data.get("items", [])
                })
            )
        except Exception as e:
            _LOGGER.error("Failed to fetch playlist data from Kodi: %s", e)

    # Initial fetch
    await send_current_playlist()

    async def kodi_listener():
        """Listen for WebSocket notification events from Kodi."""
        try:
            await kodi_client.ws_connect()
            while kodi_client.ws_connected:
                kodi_msg = await kodi_client.ws_receive()
                if kodi_msg is None:
                    break
                
                method = kodi_msg.get("method", "")
                if method in ["Playlist.OnAdd", "Playlist.OnRemove", "Playlist.OnClear", "Player.OnPlay"]:
                    await send_current_playlist()
                    
        except asyncio.CancelledError:
            await kodi_client.ws_close()
        except Exception as e:
            _LOGGER.error("Error inside the Kodi WebSocket event listener loop: %s", e)

    listener_task = hass.async_create_task(kodi_listener())
    # Cleanup task when the frontend disconnects
    connection.on_close(listener_task.cancel)