"""WebSocket commands related to the Kodi playlist.

Provides the `kodi_media_sensors/subscribe_playlist` command:
- sends the full playlist when the client subscribes
- pushes the updated playlist whenever a change is detected on the
  associated Kodi media_player entity (via the core Kodi integration).

Note: the core `kodi.call_method` action does not support
`return_response=True`. Results of JSON-RPC calls are instead
delivered asynchronously via a `kodi_call_method_result` event on the
event bus. We call the action and wait for the matching event.
"""
import asyncio
import logging
import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback, Event
from homeassistant.helpers.event import async_track_state_change_event

from ..const import (
    DOMAIN,
    CONF_KODI_ENTITY,
    KODI_DOMAIN,
    SERVICE_CALL_METHOD,
    DEFAULT_PLAYLIST_ID,
)

_LOGGER = logging.getLogger(__name__)

EVENT_CALL_METHOD_RESULT = "kodi_call_method_result"
CALL_METHOD_TIMEOUT = 10


@callback
def async_register_websockets(hass: HomeAssistant) -> None:
    """Register playlist-related WebSocket commands."""
    websocket_api.async_register_command(hass, websocket_subscribe_playlist)


async def _async_fetch_playlist(hass: HomeAssistant, entity_id: str, playlist_id: int):
    """Call Playlist.GetItems on the Kodi instance via the core integration.

    The core `kodi.call_method` action does not support
    `return_response=True`. Instead, results are published on the
    `kodi_call_method_result` event bus event. We listen for that
    event before firing the call, then wait (with a timeout) for the
    matching response.
    """
    method = "Playlist.GetItems"
    params = {
        "entity_id": entity_id,
        "method": method,
        "playlistid": playlist_id,
        "properties": [
            "title",
            "artist",
            "album",
            "duration",
            "thumbnail",
            "file",
            "showtitle",
            "episode",
            "season",
        ],
    }

    result_future: asyncio.Future = asyncio.get_event_loop().create_future()

    @callback
    def _handle_result_event(event: Event) -> None:
        data = event.data
        if data.get("entity_id") != entity_id:
            return
        event_input = data.get("input", {})
        if event_input.get("method") != method:
            return
        if not result_future.done():
            result_future.set_result(data)

    unsub = hass.bus.async_listen(EVENT_CALL_METHOD_RESULT, _handle_result_event)

    try:
        await hass.services.async_call(
            KODI_DOMAIN,
            SERVICE_CALL_METHOD,
            params,
            blocking=True,
        )

        try:
            data = await asyncio.wait_for(result_future, timeout=CALL_METHOD_TIMEOUT)
        except asyncio.TimeoutError:
            _LOGGER.warning(
                "Timeout waiting for %s result for %s",
                method,
                entity_id,
            )
            return None
    except Exception as err:  # noqa: BLE001 - log anything unexpected too
        _LOGGER.error("Error calling %s for %s: %s", method, entity_id, err)
        return None
    finally:
        unsub()

    if not data.get("result_ok", False):
        _LOGGER.warning(
            "Kodi returned an error for %s on %s: %r", method, entity_id, data
        )
        return None

    result = data.get("result", {})
    items = result.get("items", [])
    _LOGGER.debug("Fetched %d playlist item(s) for %s", len(items), entity_id)
    return items


@websocket_api.websocket_command({
    vol.Required("type"): "kodi_media_sensors/subscribe_playlist",
    vol.Required("entry_id"): str,
})
@websocket_api.async_response
async def websocket_subscribe_playlist(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict,
) -> None:
    """Subscribe to playlist updates for a given Kodi instance."""

    entry_id = msg["entry_id"]
    msg_id = msg["id"]

    config_entry = hass.config_entries.async_get_entry(entry_id)

    if not config_entry or config_entry.domain != DOMAIN:
        connection.send_error(msg_id, "invalid_entry", f"Entry {entry_id} not found")
        return

    entity_id = config_entry.data.get(CONF_KODI_ENTITY)
    if not entity_id:
        connection.send_error(
            msg_id, "invalid_config", f"No Kodi entity configured for entry {entry_id}"
        )
        return

    playlist_id = config_entry.data.get("playlist_id", DEFAULT_PLAYLIST_ID)

    # Tracks the last payload sent, to avoid pushing duplicates
    last_items_sent: list | None = None

    async def _send_playlist() -> None:
        nonlocal last_items_sent
        items = await _async_fetch_playlist(hass, entity_id, playlist_id)
        if items is None:
            return
        if items == last_items_sent:
            return
        last_items_sent = items
        connection.send_message(
            websocket_api.event_message(msg_id, {
                "type": "playlist_update",
                "items": items,
            })
        )

    @callback
    def _handle_state_change(event: Event) -> None:
        """Triggered on every state change of the Kodi entity."""
        hass.async_create_task(_send_playlist())

    # Send the current playlist immediately
    await _send_playlist()

    # Subscribe to state changes of the Kodi media_player entity
    unsub = async_track_state_change_event(hass, [entity_id], _handle_state_change)

    connection.subscriptions[msg_id] = unsub

    connection.send_result(msg_id)