"""WebSocket commands related to the Kodi playlist.

Provides the `kodi_media_sensors/subscribe_playlist` command:
- sends the full playlist when the client subscribes
- pushes the updated playlist whenever a change is detected on the
  associated Kodi media_player entity (via the core Kodi integration)
- notifies the client with a `kodi_unavailable` status instead of a
  playlist when the Kodi entity is unavailable (Kodi/host unreachable),
  so the client can distinguish "no playlist data yet" from "Kodi is
  simply not reachable right now".
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
    websocket_api.async_register_command(hass, websocket_subscribe_playlist)


async def _async_fetch_playlist(hass: HomeAssistant, entity_id: str, playlist_id: int):
    """Fetch the current playlist items via Playlist.GetItems."""
    result = await async_call_method(
        hass,
        entity_id,
        "Playlist.GetItems",
        playlistid=playlist_id,
        properties=[
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
    )
    if result is None:
        return None

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

    # Tracks the last payload sent, to avoid pushing duplicates.
    # Also used to track whether the last message sent was an
    # "unavailable" status, so we don't spam it on every state change
    # while Kodi stays off.
    last_items_sent: list | None = None
    last_kodi_state_sent: str | None = None
    last_status_sent: str | None = None

    # Prevents overlapping fetches: state_changed can fire rapidly
    # (e.g. every second while Kodi is playing), but we only care
    # about the latest playlist snapshot.
    fetch_lock = asyncio.Lock()
    pending_tasks: set[asyncio.Task] = set()

    def _get_kodi_state() -> str | None:
        state = hass.states.get(entity_id)
        return state.state if state is not None else None

    def _is_kodi_available() -> bool:
        kodi_state = _get_kodi_state()
        return kodi_state is not None and kodi_state != STATE_UNAVAILABLE

    async def _send_playlist() -> None:
        nonlocal last_items_sent, last_kodi_state_sent, last_status_sent

        if not _is_kodi_available():
            if last_status_sent != "kodi_unavailable":
                last_status_sent = "kodi_unavailable"
                last_items_sent = None
                last_kodi_state_sent = None
                connection.send_message(
                    websocket_api.event_message(msg_id, {
                        "type": "kodi_unavailable",
                    })
                )
            return

        async with fetch_lock:
            items = await _async_fetch_playlist(hass, entity_id, playlist_id)

        if items is None:
            # Kodi entity is available but the JSON-RPC call failed or
            # timed out. Don't overwrite the last known good state with
            # nothing; just skip this update.
            return

        kodi_state = _get_kodi_state()

        if (
            items == last_items_sent
            and kodi_state == last_kodi_state_sent
            and last_status_sent == "playlist_update"
        ):
            return

        last_items_sent = items
        last_kodi_state_sent = kodi_state
        last_status_sent = "playlist_update"
        connection.send_message(
            websocket_api.event_message(msg_id, {
                "type": "playlist_update",
                "items": items,
                "kodi_state": kodi_state,
            })
        )

    @callback
    def _handle_state_change(event: Event) -> None:
        """Triggered on every state change of the Kodi entity."""
        task = hass.async_create_task(_send_playlist())
        pending_tasks.add(task)
        task.add_done_callback(pending_tasks.discard)

    # Send the current playlist (or unavailable status) immediately
    await _send_playlist()

    # Subscribe to state changes of the Kodi media_player entity
    unsub_state_change = async_track_state_change_event(
        hass, [entity_id], _handle_state_change
    )

    @callback
    def _unsubscribe() -> None:
        """Clean up listeners and cancel any in-flight fetch on unsubscribe."""
        unsub_state_change()
        for task in list(pending_tasks):
            task.cancel()

    connection.subscriptions[msg_id] = _unsubscribe

    connection.send_result(msg_id)