"""WebSocket commands related to the Kodi playlist.

Provides the `kodi_media_sensors/playlist_subscribe` command:
- sends the full playlist when the client subscribes
- pushes the updated playlist whenever items change in the
  associated Kodi media_player entity (via the core Kodi integration)
- does NOT send state updates (the sensor tracks Kodi state separately)
- sends an empty playlist when Kodi is idle (no active player)

Provides the `kodi_media_sensors/playlist_play_item` command:
- plays the item at the specified index in the current playlist.

Provides the `kodi_media_sensors/playlist_remove_item` command:
- removes the item at the specified index from the current playlist.
- fires a refresh event to ensure the client receives the updated playlist.

Provides the `kodi_media_sensors/playlist_get` command:
- returns the current playlist immediately (one-shot request/response).

Provides the `kodi_media_sensors/playlist_reorder` command:
- reorders items in the playlist via remove-and-insert.
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
    KODI_PLAYER_ID_VIDEO,
    KODI_PLAYER_ID_AUDIO,
    KODI_STATE_UNAVAILABLE,
    KODI_STATE_OFF,
)
from ..kodi_client import async_call_method

_LOGGER = logging.getLogger(__name__)


@callback
def _is_kodi_connected(hass: HomeAssistant, entity_id: str) -> bool:
    """Vérifie si l'entité Kodi est disponible."""
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
    # websocket_api.async_register_command(hass, websocket_playlist_get)
    websocket_api.async_register_command(hass, websocket_playlist_goto_index)
    websocket_api.async_register_command(hass, websocket_playlist_remove_item)
    websocket_api.async_register_command(hass, websocket_playlist_reorder)
    websocket_api.async_register_command(hass, websocket_playlist_play_item)
    websocket_api.async_register_command(hass, websocket_playlist_add_item)


def _get_kodi_entity_id_from_entry(hass, entry_id):
    """Récupère kodi_entity_id à partir de entry_id"""
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
        # if player.get("type") == "video":
        #     return KODI_PLAYER_ID_VIDEO
        # elif player.get("type") == "audio":
        #     return KODI_PLAYER_ID_AUDIO
        return player.get("playerid")
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
    """Récupère et formate la playlist pour le frontend.

    Note: Ne retourne PAS kodi_state — le senseur gère l'état Kodi.
    """
    if not _is_kodi_connected(hass, kodi_entity_id):
        return {"items": [], "playlist_id": None, "current_index": -1}

    active_playlist_id = await _async_get_active_playlist_id(hass, kodi_entity_id)
    active_player_id = await _async_get_active_player_id(hass, kodi_entity_id)

    items = []
    if active_playlist_id is not None:
        items = (
            await _async_fetch_playlist(hass, kodi_entity_id, active_playlist_id) or []
        )

    # 🚀 SIGNATURE DES URLS
    mp_component = hass.data.get("media_player")
    mp_entity = mp_component.get_entity(kodi_entity_id) if mp_component else None

    if mp_entity and items:
        for item in items:
            thumb = item.get("thumbnail")
            if thumb and isinstance(thumb, str) and thumb.startswith("image://"):
                item["thumbnail"] = await mp_entity.async_get_browse_image(
                    "image", thumb
                )

    current_index = -1
    if active_player_id is not None:
        current_index = await _async_get_active_item_index(
            hass, kodi_entity_id, active_player_id
        )

    return {
        "items": items,
        "playlist_id": active_playlist_id,
        "current_index": current_index,
    }


@websocket_api.websocket_command(
    {
        vol.Required("type"): "kodi_media_sensors/playlist_subscribe",
        vol.Required("entry_id"): str,
        # vol.Required(CONF_KODI_ENTITY): str,
    }
)
@websocket_api.async_response
async def websocket_playlist_subscribe(hass, connection, msg):
    kodi_entity_id = _get_kodi_entity_id_from_entry(hass, msg["entry_id"])
    msg_id = msg["id"]
    entry_id = msg["entry_id"]

    # Suivi des derniers items (pour la déduplication)
    last_items = None

    async def _send_playlist(*args):
        nonlocal last_items
        data = await _async_get_full_playlist_data(hass, kodi_entity_id)
        items = data["items"]

        # Déduplication: envoyer seulement si les items ont changé
        if items == last_items:
            return

        last_items = items

        # Envoyer l'event avec les nouvelles données
        payload = {
            "type": "playlist_update",
            "items": items,
            "playlist_id": data["playlist_id"],
            "current_index": data["current_index"],
        }

        connection.send_message(websocket_api.event_message(msg_id, payload))

    # ✅ CORRECTION ICI : Remplacement de la lambda par une fonction async dédiée
    async def _handle_playlist_updated(event: Event) -> None:
        if event.data.get("entry_id") == entry_id:
            await _send_playlist()

    # Enregistrement des listeners
    unsub_state = async_track_state_change_event(hass, [kodi_entity_id], _send_playlist)

    # ✅ CORRECTION ICI : On passe la fonction async directement. HA gère la sécurité !
    unsub_refresh = hass.bus.async_listen(
        f"{DOMAIN}_playlist_updated", _handle_playlist_updated
    )

    connection.subscriptions[msg_id] = lambda: (unsub_state(), unsub_refresh())
    await _send_playlist()
    connection.send_result(msg_id)


# @websocket_api.websocket_command(
#     {
#         vol.Required("type"): "kodi_media_sensors/playlist_get",
#         vol.Required("entry_id"): str,
#         # vol.Required(CONF_KODI_ENTITY): str,
#     }
# )
# @websocket_api.async_response
# async def websocket_playlist_get(hass, connection, msg):
#     kodi_entity_id = _get_kodi_entity_id_from_entry(hass, msg["entry_id"])
#     data = await _async_get_full_playlist_data(hass, kodi_entity_id)
#     connection.send_result(msg["id"], data)


@websocket_api.websocket_command(
    {
        vol.Required("type"): "kodi_media_sensors/playlist_goto_index",
        vol.Required("entry_id"): str,
        vol.Required("index"): vol.All(vol.Coerce(int), vol.Range(min=0)),
        # vol.Required(CONF_KODI_ENTITY): str,
    }
)
@websocket_api.async_response
async def websocket_playlist_goto_index(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict
) -> None:
    kodi_entity_id = _get_kodi_entity_id_from_entry(
        hass, msg["entry_id"]
    )
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
        # Trigger the manual refresh so the client gets the updated list immediately
        hass.bus.async_fire(f"{DOMAIN}_playlist_updated", {"entry_id": entry_id})
        connection.send_result(msg["id"])
    else:
        connection.send_error(msg["id"], "removal_failed", "Failed to remove item")


@websocket_api.websocket_command(
    {
        vol.Required("type"): "kodi_media_sensors/playlist_reorder",
        # vol.Required(CONF_KODI_ENTITY): str,
        vol.Required("entry_id"): str,
        vol.Required("from_index"): vol.All(vol.Coerce(int), vol.Range(min=0)),
        vol.Required("to_index"): vol.All(vol.Coerce(int), vol.Range(min=0)),
    }
)
@websocket_api.async_response
async def websocket_playlist_reorder(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict
) -> None:
    """Réordonne les items de la playlist via une suppression et une réinsertion."""
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

    # 1. Récupération des items pour identifier celui à déplacer
    items = await _async_fetch_playlist(hass, kodi_entity_id, playlist_id)
    if not items or from_index >= len(items):
        _LOGGER.error("Reorder failed: index %d out of bounds", from_index)
        connection.send_error(msg["id"], "reorder_failed", "Invalid index")
        return

    item_to_move = items[from_index]
    # On isole uniquement le champ 'file' pour éviter l'erreur "Invalid params" de Kodi
    simplified_item = {"file": item_to_move.get("file")}

    # 2. Suppression de l'ancienne position
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

    # 3. Insertion à la nouvelle position
    inserted = await async_call_method(
        hass,
        kodi_entity_id,
        "Playlist.Insert",
        playlistid=playlist_id,
        position=to_index,
        item=simplified_item,
    )

    if inserted:
        _LOGGER.info(
            "Reorder successful: Item moved from %d to %d.", from_index, to_index
        )
        # 4. Trigger du rafraîchissement
        hass.bus.async_fire(f"{DOMAIN}_playlist_updated", {"entry_id": entry_id})
        connection.send_result(msg["id"])

    else:
        _LOGGER.error("Reorder failed: Kodi failed to insert item at %d", to_index)
        connection.send_error(
            msg["id"], "reorder_failed", "Failed to insert item at new position"
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
        # vol.Required(CONF_KODI_ENTITY): str,
    }
)
@websocket_api.async_response
async def websocket_playlist_play_item(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict
) -> None:
    entry_id = msg["entry_id"]
    # kodi_entity_id = msg[CONF_KODI_ENTITY]
    item_id = msg["item_id"]
    item_name = msg["item_name"]
    kodi_entity_id = _get_kodi_entity_id_from_entry(hass, entry_id)

    # 1. Récupérer la playlist active ou déterminer s'il faut en cibler une par défaut
    playlist_id = await _async_get_active_playlist_id(hass, kodi_entity_id)
    active_player_id = await _async_get_active_player_id(hass, kodi_entity_id)

    # Si aucune playlist n'est active, on se base sur le type d'item demandé
    # En règle générale : playlist 0 pour l'audio, playlist 1 pour la vidéo
    if playlist_id is None:
        playlist_id = 0 if item_name == "songid" else 1

    # 2. Récupérer les items de la playlist pour connaître sa longueur et trouver l'index actuel
    playlist_items = (
        await _async_fetch_playlist(hass, kodi_entity_id, playlist_id) or []
    )

    current_index = -1
    if active_player_id is not None:
        current_index = await _async_get_active_item_index(
            hass, kodi_entity_id, active_player_id
        )

    # 3. Déterminer la position d'insertion (juste après l'item courant, ou à la fin)
    if current_index != -1:
        insert_index = current_index + 1
    else:
        insert_index = len(playlist_items)

    # 4. Construction de l'objet item dynamique (ex: {"songid": 123})
    kodi_item = {f"{item_name}id": item_id}

    # 5. Insérer le nouvel élément dans la playlist de Kodi
    inserted = await async_call_method(
        hass,
        kodi_entity_id,
        "Playlist.Insert",
        playlistid=playlist_id,
        position=insert_index,
        item={
            item_name: item_id
        },  # <-- CORRECTION : On envoie un dictionnaire {"songid": 40716}
    )

    if not inserted:
        _LOGGER.error(
            "Failed to insert item %s %d into playlist %d",
            item_name,
            item_id,
            playlist_id,
        )
        connection.send_error(
            msg["id"], "insert_failed", f"Failed to insert {item_name} into playlist"
        )
        return

    # 6. Ouvrir le player à la position de l'élément inséré pour lancer la lecture immédiate
    opened = await async_call_method(
        hass,
        kodi_entity_id,
        "Player.Open",
        item={"playlistid": playlist_id, "position": insert_index},
    )

    if opened:
        # Notification au bus d'événement pour rafraîchir instantanément l'UI Home Assistant
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
        vol.Required("position"): vol.All(vol.Coerce(int), vol.Range(min=0)),
        # vol.Required(CONF_KODI_ENTITY): str,
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
    insert_position = msg["position"]

    # 1. Récupérer la playlist active ou déterminer s'il faut en cibler une par défaut
    playlist_id = await _async_get_active_playlist_id(hass, kodi_entity_id)

    # Si aucune playlist n'est active, on se base sur le type d'item demandé (0 pour l'audio, 1 pour la vidéo)
    if playlist_id is None:
        playlist_id = 0 if item_name in ["songid", "albumid"] else 1

    # 2. Insérer le nouvel élément directement à la position indiquée
    # Kodi gère nativement le fait de l'ajouter à la fin si l'index dépasse la taille maximale de la liste
    inserted = await async_call_method(
        hass,
        kodi_entity_id,
        "Playlist.Insert",
        playlistid=playlist_id,
        position=insert_position,
        item={item_name: item_id},
    )

    if inserted:
        # Notification au bus d'événement pour rafraîchir instantanément l'UI de la playlist
        hass.bus.async_fire(f"{DOMAIN}_playlist_updated", {"entry_id": entry_id})
        connection.send_result(msg["id"])
    else:
        _LOGGER.error(
            "Failed to add item %s %d into playlist %d at position %d",
            item_name,
            item_id,
            playlist_id,
            insert_position,
        )
        connection.send_error(
            msg["id"], "add_failed", f"Failed to insert {item_name} into playlist"
        )
