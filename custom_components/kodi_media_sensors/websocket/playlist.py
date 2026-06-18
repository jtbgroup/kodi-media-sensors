"""WebSocket commands related to the Kodi playlist.

Provides the `kodi_media_sensors/playlist_subscribe` command:
- sends the full playlist when the client subscribes
- pushes the updated playlist whenever a change is detected on the
  associated Kodi media_player entity (via the core Kodi integration)
- notifies the client with a `kodi_unavailable` status instead of a
  playlist when the Kodi entity is unavailable (Kodi/host unreachable),
  so the client can distinguish "no playlist data yet" from "Kodi is
  simply not reachable right now".
- sends an empty playlist when Kodi is idle (no active player).

Provides the `kodi_media_sensors/playlist_play_item` command:
- plays the item at the specified index in the current playlist.

Provides the `kodi_media_sensors/playlist_remove_item` command:
- removes the item at the specified index from the current playlist.
- fires a refresh event to ensure the client receives the updated playlist.
"""

import asyncio
import logging
import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback, Event
from homeassistant.helpers.event import async_track_state_change_event

from ..const import DOMAIN, CONF_KODI_ENTITY, DEFAULT_PLAYLIST_ID
from ..kodi_client import async_call_method

_LOGGER = logging.getLogger(__name__)

STATE_UNAVAILABLE = "unavailable"


@callback
def async_register_websockets(hass: HomeAssistant) -> None:
    """Register playlist-related WebSocket commands."""
    websocket_api.async_register_command(hass, websocket_playlist_subscribe)
    websocket_api.async_register_command(hass, websocket_playlist_play_item)
    websocket_api.async_register_command(hass, websocket_playlist_remove_item)
    websocket_api.async_register_command(hass, websocket_playlist_reorder)


async def _async_get_active_playlist_id(hass: HomeAssistant, entity_id: str) -> int | None:
    """Determine the active playlist ID based on what's currently playing."""
    result = await async_call_method(hass, entity_id, "Player.GetActivePlayers")
    if result is None or not result:
        return None
    for player in result:
        if player.get("type") == "video":
            return 1
        elif player.get("type") == "audio":
            return 0
    return None


async def _async_get_active_player_id(hass: HomeAssistant, entity_id: str) -> int | None:
    """Get the currently active player ID (playerid)."""
    result = await async_call_method(hass, entity_id, "Player.GetActivePlayers")
    if result is None or not result:
        return None
    for player in result:
        playerid = player.get("playerid")
        if playerid is not None:
            return playerid
    return None

async def _async_get_active_item_index(hass: HomeAssistant, entity_id: str, player_id: int) -> int:
    """Get the current index (position) of the item being played.
    
    Returns:
        The 0-based index of the current item, or -1 if no item is playing.
    """
    result = await async_call_method(hass, entity_id, "Player.GetProperties", playerid=player_id, properties=["position"])
    return result.get("position", -1) if result else -1


async def _async_fetch_playlist(hass: HomeAssistant, entity_id: str, playlist_id: int):
    """Fetch the current playlist items via Playlist.GetItems."""
    result = await async_call_method(
        hass, entity_id, "Playlist.GetItems", playlistid=playlist_id,
        properties=["showtitle", "album", "albumid", "artist", "artistid", "duration", "genre", "thumbnail", "title", "track", "year", "episode", "season", "art", "file"],
    )
    return result.get("items", []) if result else None


@websocket_api.websocket_command({
    vol.Required("type"): "kodi_media_sensors/playlist_subscribe",
    vol.Required("entry_id"): str,
})
@websocket_api.async_response
async def websocket_playlist_subscribe(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    """Subscribe to playlist updates for a given Kodi instance."""
    entry_id = msg["entry_id"]
    msg_id = msg["id"]
    config_entry = hass.config_entries.async_get_entry(entry_id)
    entity_id = config_entry.data.get(CONF_KODI_ENTITY)

    last_items_sent: list | None = None
    last_kodi_state_sent: str | None = None
    last_playlist_id_sent: int | None = None
    last_current_index_sent: int = -1
    last_status_sent: str | None = None

    fetch_lock = asyncio.Lock()
    pending_tasks: set[asyncio.Task] = set()

    async def _send_playlist(*args) -> None:
        nonlocal last_items_sent, last_kodi_state_sent, last_playlist_id_sent, last_current_index_sent, last_status_sent
        
        state = hass.states.get(entity_id)
        if state is None or state.state == STATE_UNAVAILABLE:
            if last_status_sent != "kodi_unavailable":
                last_status_sent = "kodi_unavailable"
                connection.send_message(websocket_api.event_message(msg_id, {"type": "kodi_unavailable"}))
            return

        active_playlist_id = await _async_get_active_playlist_id(hass, entity_id)
        active_player_id = await _async_get_active_player_id(hass, entity_id)
        
        async with fetch_lock:
            items = [] if active_playlist_id is None else await _async_fetch_playlist(hass, entity_id, active_playlist_id)

        if items is None: 
            return

        # Récupérer l'index actuel de l'item en lecture
        current_index = -1
        if active_player_id is not None:
            current_index = await _async_get_active_item_index(hass, entity_id, active_player_id)

        # Déduplication : ne pas renvoyer si rien n'a changé
        if items == last_items_sent and state.state == last_kodi_state_sent and active_playlist_id == last_playlist_id_sent and current_index == last_current_index_sent:
            return

        last_items_sent, last_kodi_state_sent, last_playlist_id_sent, last_status_sent = items, state.state, active_playlist_id, "playlist_update"
        last_current_index_sent = current_index
        
        connection.send_message(websocket_api.event_message(msg_id, {
            "type": "playlist_update",
            "items": items,
            "kodi_state": state.state,
            "playlist_id": active_playlist_id,
            "current_index": current_index
        }))

    # Listen for state changes AND manual refresh events
    unsub_state = async_track_state_change_event(hass, [entity_id], _send_playlist)
    # unsub_refresh = hass.bus.async_listen(f"{DOMAIN}_refresh_{entry_id}", _send_playlist)

    @callback
    def _handle_global_refresh(event: Event) -> None:
        if event.data.get("entry_id") == entry_id:
            hass.async_create_task(_send_playlist())

    unsub_refresh = hass.bus.async_listen(f"{DOMAIN}_playlist_updated", _handle_global_refresh)

    await _send_playlist()

    @callback
    def _unsubscribe() -> None:
        unsub_state()
        unsub_refresh()

    connection.subscriptions[msg_id] = _unsubscribe
    connection.send_result(msg_id)


@websocket_api.websocket_command({
    vol.Required("type"): "kodi_media_sensors/playlist_play_item",
    vol.Required("entry_id"): str,
    vol.Required("index"): vol.All(vol.Coerce(int), vol.Range(min=0)),
})
@websocket_api.async_response
async def websocket_playlist_play_item(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    entity_id = hass.config_entries.async_get_entry(msg["entry_id"]).data.get(CONF_KODI_ENTITY)
    player_id = await _async_get_active_player_id(hass, entity_id)
    
    if player_id is not None and await async_call_method(hass, entity_id, "Player.GoTo", playerid=player_id, to=msg["index"]):
        connection.send_result(msg["id"])
    else:
        connection.send_error(msg["id"], "playback_failed", "Failed to play item")


@websocket_api.websocket_command({
    vol.Required("type"): "kodi_media_sensors/playlist_remove_item",
    vol.Required("entry_id"): str,
    vol.Required("index"): vol.All(vol.Coerce(int), vol.Range(min=0)),
})
@websocket_api.async_response
async def websocket_playlist_remove_item(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    entry_id = msg["entry_id"]
    entity_id = hass.config_entries.async_get_entry(entry_id).data.get(CONF_KODI_ENTITY)
    playlist_id = await _async_get_active_playlist_id(hass, entity_id)

    if playlist_id is not None and await async_call_method(hass, entity_id, "Playlist.Remove", playlistid=playlist_id, position=msg["index"]):
        # Trigger the manual refresh so the client gets the updated list immediately
        hass.bus.async_fire(f"{DOMAIN}_refresh_{entry_id}")
        connection.send_result(msg["id"])
    else:
        connection.send_error(msg["id"], "removal_failed", "Failed to remove item")


@websocket_api.websocket_command({
    vol.Required("type"): "kodi_media_sensors/playlist_reorder",
    vol.Required("entry_id"): str,
    vol.Required("from_index"): vol.All(vol.Coerce(int), vol.Range(min=0)),
    vol.Required("to_index"): vol.All(vol.Coerce(int), vol.Range(min=0)),
})
@websocket_api.async_response
async def websocket_playlist_reorder(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    """Réordonne les items de la playlist via une suppression et une réinsertion."""
    entry_id = msg["entry_id"]
    from_index = msg["from_index"]
    to_index = msg["to_index"]
    
    _LOGGER.debug("Reorder requested: entry_id=%s, from=%d, to=%d", entry_id, from_index, to_index)

    if from_index == to_index:
        connection.send_result(msg["id"])
        return

    entity_id = hass.config_entries.async_get_entry(entry_id).data.get(CONF_KODI_ENTITY)
    playlist_id = await _async_get_active_playlist_id(hass, entity_id)

    if playlist_id is None:
        _LOGGER.error("Reorder failed: No active playlist found for %s", entity_id)
        connection.send_error(msg["id"], "reorder_failed", "No active playlist")
        return

    # 1. Récupération des items pour identifier celui à déplacer
    items = await _async_fetch_playlist(hass, entity_id, playlist_id)
    if not items or from_index >= len(items):
        _LOGGER.error("Reorder failed: index %d out of bounds", from_index)
        connection.send_error(msg["id"], "reorder_failed", "Invalid index")
        return
    
    item_to_move = items[from_index]
    # On isole uniquement le champ 'file' pour éviter l'erreur "Invalid params" de Kodi
    simplified_item = {"file": item_to_move.get("file")}

    # 2. Suppression de l'ancienne position
    removed = await async_call_method(hass, entity_id, "Playlist.Remove", playlistid=playlist_id, position=from_index)
    if not removed:
        _LOGGER.error("Reorder failed: Kodi failed to remove item at %d", from_index)
        connection.send_error(msg["id"], "removal_failed", "Failed to remove item")
        return

    # 3. Insertion à la nouvelle position
    inserted = await async_call_method(
        hass, entity_id, "Playlist.Insert", 
        playlistid=playlist_id, 
        position=to_index, 
        item=simplified_item
    )

    if inserted:
        _LOGGER.info("Reorder successful: Item moved from %d to %d.", from_index, to_index)
        # 4. Trigger du rafraîchissement
        hass.bus.async_fire(
            f"{DOMAIN}_playlist_updated", 
            {"entry_id": entry_id}
        )
        connection.send_result(msg["id"])

    else:
        _LOGGER.error("Reorder failed: Kodi failed to insert item at %d", to_index)
        connection.send_error(msg["id"], "reorder_failed", "Failed to insert item at new position")