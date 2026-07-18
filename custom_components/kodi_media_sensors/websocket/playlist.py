"""WebSocket commands related to the Kodi playlist.

Provides the `kodi_media_sensors/playlist_subscribe` command:
- sends the full playlist when the client subscribes
- pushes the updated playlist whenever items change in the
  associated Kodi media_player entity (via the core Kodi integration)
- does NOT send state updates (the sensor tracks Kodi state separately)
- sends an empty playlist when Kodi is idle (no active player)

Provides the `kodi_media_sensors/playlist_goto_index` command:
- navigates to the item at the specified index in the current playlist.

Provides the `kodi_media_sensors/playlist_remove_item` command:
- removes the item at the specified index from the current playlist.
- fires a refresh event to ensure the client receives the updated playlist.

Provides the `kodi_media_sensors/playlist_reorder` command:
- reorders items in the playlist via remove-and-insert.

Provides the `kodi_media_sensors/playlist_play_item` command:
- plays the item at the specified index in the current playlist.

Provides the `kodi_media_sensors/playlist_add_item` command:
- adds the item at the specified index in the current playlist.

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
    KODI_STATE_UNAVAILABLE,
    KODI_STATE_OFF,
    PLAYER_ID_AUDIO,
    PLAYER_ID_VIDEO,
)
from ..kodi_client import async_call_method

_LOGGER = logging.getLogger(__name__)


@callback
def _is_kodi_connected(hass: HomeAssistant, entity_id: str) -> bool:
    """Check whether the Kodi entity is available."""
    state = hass.states.get(entity_id)
    return (
        state is not None
        and state.state != KODI_STATE_OFF
        and state.state != KODI_STATE_UNAVAILABLE
    )


@callback
def async_register_websockets(hass: HomeAssistant) -> None:
    """Register playlist-related WebSocket commands."""
    websocket_api.async_register_command(hass, websocket_playlist_subscribe)
    websocket_api.async_register_command(hass, websocket_playlist_goto_index)
    websocket_api.async_register_command(hass, websocket_playlist_remove_item)
    websocket_api.async_register_command(hass, websocket_playlist_reorder)
    websocket_api.async_register_command(hass, websocket_playlist_play_item)
    websocket_api.async_register_command(hass, websocket_playlist_add_item)
    websocket_api.async_register_command(hass, websocket_playlist_play_playlist)
    websocket_api.async_register_command(hass, websocket_playlist_add_playlist)


def _get_default_player_id(item_name):
    if item_name == "songid":
        return PLAYER_ID_AUDIO

    return PLAYER_ID_VIDEO


def _get_kodi_entity_id_from_entry(hass, entry_id):
    """Get kodi_entity_id from entry_id"""
    config_entry = hass.config_entries.async_get_entry(entry_id)
    return config_entry.data.get(CONF_KODI_ENTITY)


async def _async_get_active_playlist_id(
    hass: HomeAssistant, entity_id: str
) -> int | None:
    if not _is_kodi_connected(hass, entity_id):
        return None
    result = await async_call_method(hass, entity_id, "Player.GetActivePlayers")
    if result is None or not result:
        return None
    for player in result:
        playerid = player.get("playerid")
        if playerid is not None:
            return playerid
    return None


async def _async_get_active_player_id(
    hass: HomeAssistant, entity_id: str
) -> int | None:
    if not _is_kodi_connected(hass, entity_id):
        return None
    result = await async_call_method(hass, entity_id, "Player.GetActivePlayers")
    if result is None or not result:
        return None
    for player in result:
        playerid = player.get("playerid")
        if playerid is not None:
            return playerid
    return None


async def _async_get_active_item_index(
    hass: HomeAssistant, entity_id: str, player_id: int
) -> int:
    """Get the current index (position) of the item being played.

    Returns:
        The 0-based index of the current item, or -1 if no item is playing.
    """
    result = await async_call_method(
        hass,
        entity_id,
        "Player.GetProperties",
        playerid=player_id,
        properties=["position"],
    )
    return result.get("position", -1) if result else -1


async def _async_fetch_playlist(hass: HomeAssistant, entity_id: str, playlist_id: int):
    """Fetch the current playlist items via Playlist.GetItems."""
    result = await async_call_method(
        hass,
        entity_id,
        "Playlist.GetItems",
        playlistid=playlist_id,
        properties=[
            "showtitle",
            "album",
            "albumid",
            "artist",
            "artistid",
            "duration",
            "genre",
            "thumbnail",
            "title",
            "track",
            "year",
            "episode",
            "season",
            "art",
            "file",
        ],
    )
    return result.get("items", []) if result else None


async def _async_get_full_playlist_data(hass: HomeAssistant, kodi_entity_id: str):
    """fetch and format the playlist for the frontend."""
    if not _is_kodi_connected(hass, kodi_entity_id):
        return {"items": [], "playlist_id": None, "current_index": -1}

    try:
        active_players = await async_call_method(
            hass, kodi_entity_id, "Player.GetActivePlayers"
        )
    except Exception as err:
        _LOGGER.error("Failed to get active players: %s", err)
        return {"items": [], "playlist_id": None, "current_index": -1}

    if not active_players or len(active_players) == 0:
        return {"items": [], "playlist_id": None, "current_index": -1}

    if len(active_players) > 1:
        _LOGGER.info(
            "Multiple players active (%d). Using the first one.", len(active_players)
        )

    active_player = active_players[0]
    active_player_type = active_player.get("type")
    active_player_id = active_player.get("playerid")

    active_playlist_id = active_player_id

    _LOGGER.debug(
        "[PLAYLIST] player_id=%s, player_type=%s → using playlist_id=%s",
        active_player_id,
        active_player_type,
        active_playlist_id,
    )

    items = []
    if active_playlist_id is not None:
        try:
            raw_items = (
                await _async_fetch_playlist(hass, kodi_entity_id, active_playlist_id)
                or []
            )

            items = raw_items

            _LOGGER.debug(
                "Playlist data: playlist_id=%d, items_count=%d",
                active_playlist_id,
                len(items),
            )
        except Exception as err:
            _LOGGER.error("Failed to fetch playlist %d: %s", active_playlist_id, err)
            return {"items": [], "playlist_id": active_playlist_id, "current_index": -1}

    if not items and active_player_id is not None:
        _LOGGER.info(
            "[PLAYLIST] Playlist %d is empty but player %d is active — fetching current item via Player.GetItem",
            active_playlist_id,
            active_player_id,
        )
        try:
            item_result = await async_call_method(
                hass,
                kodi_entity_id,
                "Player.GetItem",
                playerid=active_player_id,
                properties=[
                    "showtitle",
                    "album",
                    "albumid",
                    "artist",
                    "artistid",
                    "duration",
                    "genre",
                    "thumbnail",
                    "title",
                    "track",
                    "year",
                    "episode",
                    "season",
                    "art",
                    "file",
                ],
            )
            if item_result and "item" in item_result:
                current_item = item_result["item"]
                if current_item.get("title") or current_item.get("file"):
                    items = [current_item]
                    _LOGGER.debug(
                        "[PLAYLIST] Synthesized playlist from Player.GetItem: type=%s id=%s title=%s",
                        current_item.get("type"),
                        current_item.get("id"),
                        current_item.get("title"),
                    )
        except Exception as err:
            _LOGGER.error("Failed to get current item via Player.GetItem: %s", err)

    mp_component = hass.data.get("media_player")
    mp_entity = mp_component.get_entity(kodi_entity_id) if mp_component else None

    if mp_entity and items:
        for item in items:
            thumb = item.get("thumbnail")
            if thumb and isinstance(thumb, str) and thumb.startswith("image://"):
                try:
                    item["thumbnail"] = await mp_entity.async_get_browse_image(
                        "image", thumb
                    )
                except Exception as err:
                    _LOGGER.debug("Failed to get browse image: %s", err)
                    item["thumbnail"] = None

    current_index = -1
    if active_player_id is not None:
        try:
            current_index = await _async_get_active_item_index(
                hass, kodi_entity_id, active_player_id
            )
        except Exception as err:
            _LOGGER.debug("Failed to get current item index: %s", err)

    return {
        "items": items,
        "playlist_id": active_playlist_id,
        "current_index": current_index,
    }


@websocket_api.websocket_command(
    {
        vol.Required("type"): "kodi_media_sensors/playlist_subscribe",
        vol.Required("entry_id"): str,
    }
)
@websocket_api.async_response
async def websocket_playlist_subscribe(hass, connection, msg):
    kodi_entity_id = _get_kodi_entity_id_from_entry(hass, msg["entry_id"])
    msg_id = msg["id"]
    entry_id = msg["entry_id"]

    last_items = None
    last_player_type = None

    async def _send_playlist(*args):
        nonlocal last_items, last_player_type

        _LOGGER.debug(
            "[PLAYLIST] _send_playlist called — last_player_type=%s, last_items_count=%s",
            last_player_type,
            len(last_items) if last_items is not None else "None",
        )

        active_players = await async_call_method(
            hass, kodi_entity_id, "Player.GetActivePlayers"
        )

        _LOGGER.debug("[PLAYLIST] GetActivePlayers → %s", active_players)

        if not active_players or len(active_players) == 0:
            _LOGGER.info(
                "[PLAYLIST] No active player — skipping (last_player_type=%s stays unchanged)",
                last_player_type,
            )
            if last_items is not None and len(last_items) > 0:
                _LOGGER.info(
                    "[PLAYLIST] Had items before, keeping last state — waiting for next event"
                )
            return

        current_player_type = active_players[0].get("type")

        _LOGGER.debug(
            "[PLAYLIST] Active player type=%s (last=%s)",
            current_player_type,
            last_player_type,
        )

        if last_player_type is not None and last_player_type != current_player_type:
            _LOGGER.debug(
                "[PLAYLIST] Player type changed: %s → %s — forcing full refresh",
                last_player_type,
                current_player_type,
            )
            last_items = None  # Force sending even if the items are identical

        last_player_type = current_player_type

       

        data = await _async_get_full_playlist_data(hass, kodi_entity_id)
        items = data["items"]

        _LOGGER.debug(
            "[PLAYLIST] Got %d items (playlist_id=%s, current_index=%s)",
            len(items),
            data["playlist_id"],
            data["current_index"],
        )

        if items == last_items:
            _LOGGER.debug("[PLAYLIST] Items unchanged — skipping send")
            return

        last_items = items

        payload = {
            "type": "playlist_update",
            "items": items,
            "playlist_id": data["playlist_id"],
            "current_index": data["current_index"],
        }

        _LOGGER.debug(
            "[PLAYLIST] → Sending playlist_update: %d items, playlist_id=%s, current_index=%s",
            len(items),
            data["playlist_id"],
            data["current_index"],
        )
        connection.send_message(websocket_api.event_message(msg_id, payload))

    async def _handle_playlist_updated(event: Event) -> None:
        if event.data.get("entry_id") == entry_id:
            await _send_playlist()

    unsub_state = async_track_state_change_event(hass, [kodi_entity_id], _send_playlist)

    unsub_refresh = hass.bus.async_listen(
        f"{DOMAIN}_playlist_updated", _handle_playlist_updated
    )

    connection.subscriptions[msg_id] = lambda: (unsub_state(), unsub_refresh())
    await _send_playlist()
    connection.send_result(msg_id)


@websocket_api.websocket_command(
    {
        vol.Required("type"): "kodi_media_sensors/playlist_goto_index",
        vol.Required("entry_id"): str,
        vol.Required("index"): vol.All(vol.Coerce(int), vol.Range(min=0)),
    }
)
@websocket_api.async_response
async def websocket_playlist_goto_index(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict
) -> None:
    kodi_entity_id = _get_kodi_entity_id_from_entry(hass, msg["entry_id"])
    player_id = await _async_get_active_player_id(hass, kodi_entity_id)

    if player_id is not None and await async_call_method(
        hass, kodi_entity_id, "Player.GoTo", playerid=player_id, to=msg["index"]
    ):
        connection.send_result(msg["id"])
    else:
        connection.send_error(msg["id"], "playback_failed", "Failed to play item")


@websocket_api.websocket_command(
    {
        vol.Required("type"): "kodi_media_sensors/playlist_remove_item",
        vol.Required("entry_id"): str,
        vol.Required("index"): vol.All(vol.Coerce(int), vol.Range(min=0)),
        # vol.Required(CONF_KODI_ENTITY): str,
    }
)
@websocket_api.async_response
async def websocket_playlist_remove_item(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict
) -> None:
    entry_id = msg["entry_id"]
    kodi_entity_id = _get_kodi_entity_id_from_entry(hass, entry_id)
    playlist_id = await _async_get_active_playlist_id(hass, kodi_entity_id)

    if playlist_id is not None and await async_call_method(
        hass,
        kodi_entity_id,
        "Playlist.Remove",
        playlistid=playlist_id,
        position=msg["index"],
    ):
        hass.bus.async_fire(f"{DOMAIN}_playlist_updated", {"entry_id": entry_id})
        connection.send_result(msg["id"])
    else:
        connection.send_error(msg["id"], "removal_failed", "Failed to remove item")


@websocket_api.websocket_command(
    {
        vol.Required("type"): "kodi_media_sensors/playlist_reorder",
        vol.Required("entry_id"): str,
        vol.Required("from_index"): vol.All(vol.Coerce(int), vol.Range(min=0)),
        vol.Required("to_index"): vol.All(vol.Coerce(int), vol.Range(min=0)),
    }
)
@websocket_api.async_response
async def websocket_playlist_reorder(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict
) -> None:
    """Reorders playlist items by removing and reinserting them."""
    entry_id = msg["entry_id"]
    kodi_entity_id = _get_kodi_entity_id_from_entry(hass, entry_id)
    from_index = msg["from_index"]
    to_index = msg["to_index"]

    _LOGGER.debug(
        "Reorder requested: entry_id=%s, from=%d, to=%d", entry_id, from_index, to_index
    )

    if from_index == to_index:
        connection.send_result(msg["id"])
        return

    playlist_id = await _async_get_active_playlist_id(hass, kodi_entity_id)

    if playlist_id is None:
        _LOGGER.error("Reorder failed: No active playlist found for %s", kodi_entity_id)
        connection.send_error(msg["id"], "reorder_failed", "No active playlist")
        return

    items = await _async_fetch_playlist(hass, kodi_entity_id, playlist_id)
    if not items or from_index >= len(items):
        _LOGGER.error("Reorder failed: index %d out of bounds", from_index)
        connection.send_error(msg["id"], "reorder_failed", "Invalid index")
        return

    item_to_move = items[from_index]

    item_type = item_to_move.get("type")
    item_id = item_to_move.get("id")

    insert_payload = {}
    if item_type and item_id and item_id != -1:
        insert_payload = {f"{item_type}id": item_id}
    else:
        insert_payload = {"file": item_to_move.get("file")}

    removed = await async_call_method(
        hass,
        kodi_entity_id,
        "Playlist.Remove",
        playlistid=playlist_id,
        position=from_index,
    )
    if not removed:
        _LOGGER.error("Reorder failed: Kodi failed to remove item at %d", from_index)
        connection.send_error(msg["id"], "removal_failed", "Failed to remove item")
        return

    if from_index < to_index:
        to_index -= 1

    inserted = await async_call_method(
        hass,
        kodi_entity_id,
        "Playlist.Insert",
        playlistid=playlist_id,
        position=to_index,
        item=insert_payload,
    )

    if inserted:
        _LOGGER.debug(
            "Reorder successful: Item moved from %d to %d.", from_index, to_index
        )
        hass.bus.async_fire(f"{DOMAIN}_playlist_updated", {"entry_id": entry_id})
        connection.send_result(msg["id"])

    else:
        _LOGGER.error("Reorder failed: Kodi failed to insert item at %d", to_index)
        connection.send_error(
            msg["id"], "reorder_failed", "Failed to insert item at new position"
        )


@websocket_api.websocket_command(
    {
        vol.Required("type"): "kodi_media_sensors/playlist_play",
        vol.Required("entry_id"): str,
        vol.Required("path"): str,
        vol.Optional("playlistid"): int,
    }
)
@websocket_api.async_response
async def websocket_playlist_play_playlist(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict
) -> None:
    entry_id = msg["entry_id"]
    playlist_path = msg["path"]
    kodi_entity_id = _get_kodi_entity_id_from_entry(hass, entry_id)
    playlist_id = msg["playlistid"] | PLAYER_ID_AUDIO

    await async_call_method(
        hass,
        kodi_entity_id,
        "Playlist.Clear",
        playlistid=playlist_id,
    )

    await async_call_method(
        hass,
        kodi_entity_id,
        "Playlist.Insert",
        playlistid=playlist_id,
        position=0,
        item={"directory": playlist_path},
    )

    opened = await async_call_method(
        hass,
        kodi_entity_id,
        "Player.Open",
        item={
            "playlistid": playlist_id,
            "position": 0,
        },
    )

    # Delay introduced to avoid race conditions in events and having errors in the log
    await asyncio.sleep(0.5)

    if opened:
        hass.bus.async_fire(f"{DOMAIN}_playlist_updated", {"entry_id": entry_id})
        connection.send_result(msg["id"])
    else:
        _LOGGER.error("Failed to open playlist file: %s", playlist_path)
        connection.send_error(
            msg["id"], "play_failed", f"Failed to open playlist {playlist_path}"
        )


@websocket_api.websocket_command(
    {
        vol.Required("type"): "kodi_media_sensors/playlist_add",
        vol.Required("entry_id"): str,
        vol.Required("path"): str,
        vol.Optional("playlistid"): int,
        vol.Optional("position"): vol.In(["next", "last"]),
    }
)
@websocket_api.async_response
async def websocket_playlist_add_playlist(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict
) -> None:
    entry_id = msg["entry_id"]
    playlist_path = msg["path"]
    kodi_entity_id = _get_kodi_entity_id_from_entry(hass, entry_id)
    playlist_id = msg["playlistid"] or PLAYER_ID_AUDIO
    position = msg["position"] or "last"
    index = 1;

    if position == "last":
        items = await async_call_method(
            hass,
            kodi_entity_id,
            "Playlist.GetItems",
            playlistid=playlist_id,
        )
        items_list = items.get("items", []) if items else []
        playlist_length = len(items_list)
        index = playlist_length

    added = await async_call_method(
        hass,
        kodi_entity_id,
        "Playlist.Insert",
        playlistid=playlist_id,
        position=index,
        item={"directory": playlist_path},
    )

    # Delay introduced to avoid race conditions in events and having errors in the log
    await asyncio.sleep(0.5)

    if added:
        hass.bus.async_fire(f"{DOMAIN}_playlist_updated", {"entry_id": entry_id})
        connection.send_result(msg["id"])
    else:
        _LOGGER.error("Failed to open playlist file: %s", playlist_path)
        connection.send_error(
            msg["id"], "play_failed", f"Failed to open playlist {playlist_path}"
        )


@websocket_api.websocket_command(
    {
        vol.Required("type"): "kodi_media_sensors/playlist_play_item",
        vol.Required("entry_id"): str,
        vol.Required("item_id"): vol.Any(int, str),
        vol.Required("item_name"): vol.In(
            [
                "songid",
                "movieid",
                "albumid",
                "musicvideoid",
                "episodeid",
                "channelid",
                "filemusicplaylist",
            ]
        ),
    }
)
@websocket_api.async_response
async def websocket_playlist_play_item(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict
) -> None:
    entry_id = msg["entry_id"]
    item_id = msg["item_id"]
    item_name = msg["item_name"]
    kodi_entity_id = _get_kodi_entity_id_from_entry(hass, entry_id)

    if item_name == "channelid":
        opened = await async_call_method(
            hass, kodi_entity_id, "Player.Open", item={"channelid": item_id}
        )
    else:
        playlist_id = await _async_get_active_playlist_id(hass, kodi_entity_id)
        active_player_id = await _async_get_active_player_id(hass, kodi_entity_id)

        if playlist_id is None:
            playlist_id = 0 if item_name == "songid" else 1

        playlist_items = (
            await _async_fetch_playlist(hass, kodi_entity_id, playlist_id) or []
        )

        current_index = -1
        if active_player_id is not None:
            current_index = await _async_get_active_item_index(
                hass, kodi_entity_id, active_player_id
            )
        else:
            active_player_id = _get_default_player_id(item_name)

        if current_index != -1:
            insert_index = current_index + 1
        else:
            insert_index = len(playlist_items)

        inserted = await async_call_method(
            hass,
            kodi_entity_id,
            "Playlist.Insert",
            playlistid=playlist_id,
            position=insert_index,
            item={item_name: item_id},
        )

        if not inserted:
            _LOGGER.error(
                "Failed to insert item %s %d into playlist %d",
                item_name,
                item_id,
                playlist_id,
            )
            connection.send_error(
                msg["id"],
                "insert_failed",
                f"Failed to insert {item_name} into playlist",
            )
            return

        opened = await async_call_method(
            hass,
            kodi_entity_id,
            "Player.Open",
            item={"playlistid": playlist_id, "position": insert_index},
        )

    if opened:
        hass.bus.async_fire(f"{DOMAIN}_playlist_updated", {"entry_id": entry_id})
        connection.send_result(msg["id"])
    else:
        _LOGGER.error(
            "Failed to open player for playlist %d at position %d",
            playlist_id,
            insert_index,
        )
        connection.send_error(
            msg["id"], "play_failed", "Failed to start playback of the inserted item"
        )


@websocket_api.websocket_command(
    {
        vol.Required("type"): "kodi_media_sensors/playlist_add_item",
        vol.Required("entry_id"): str,
        vol.Required("item_id"): vol.Any(int, str),
        vol.Required("item_name"): vol.In(
            [
                "songid",
                "movieid",
                "albumid",
                "musicvideoid",
                "episodeid",
                "channelid",
                "filemusicplaylist",
            ]
        ),
        # vol.Required("position"): vol.All(vol.Coerce(int), vol.Range(min=0)),
        vol.Optional("position"): vol.In(["next", "last"]),
    }
)
@websocket_api.async_response
async def websocket_playlist_add_item(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict
) -> None:
    entry_id = msg["entry_id"]
    kodi_entity_id = _get_kodi_entity_id_from_entry(hass, entry_id)
    item_id = msg["item_id"]
    item_name = msg["item_name"]
    position = msg["position"] or "last"

    playlist_id = await _async_get_active_playlist_id(hass, kodi_entity_id)

    index = 1;
    if position == "last":
        items = await async_call_method(
            hass,
            kodi_entity_id,
            "Playlist.GetItems",
            playlistid=playlist_id,
        )
        items_list = items.get("items", []) if items else []
        playlist_length = len(items_list)
        index = playlist_length


    if playlist_id is None:
        playlist_id = 0 if item_name in ["songid", "albumid"] else 1

    inserted = await async_call_method(
        hass,
        kodi_entity_id,
        "Playlist.Insert",
        playlistid=playlist_id,
        position=index,
        item={item_name: item_id},
    )


    if inserted:
        hass.bus.async_fire(f"{DOMAIN}_playlist_updated", {"entry_id": entry_id})
        connection.send_result(msg["id"])
    else:
        _LOGGER.error(
            "Failed to add item %s %d into playlist %d at position %d",
            item_name,
            item_id,
            playlist_id,
            index,
        )
        connection.send_error(
            msg["id"], "add_failed", f"Failed to insert {item_name} into playlist"
        )
