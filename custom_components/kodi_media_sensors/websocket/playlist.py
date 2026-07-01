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


def _filter_items_by_player_type(items: list, player_type: str) -> list:
    """✅ FILTRE CRITIQUE : Rejette les items qui ne correspondent pas au type de player actif.
    
    Cela évite le mélange de songs et movies lors d'une transition rapide entre deux media types.
    
    Args:
        items: List of Kodi items (from Playlist.GetItems)
        player_type: "video", "audio", or "picture"
    
    Returns:
        Filtered list containing only items matching the player_type
    """
    if not items or not player_type:
        return items
    
    filtered = []
    for item in items:
        item_type = item.get("type")
        
        if player_type == "audio" and item_type in ("song", "musicvideo"):
            filtered.append(item)
        elif player_type == "video" and item_type in ("movie", "episode"):
            filtered.append(item)
        elif player_type == "picture" and item_type == "picture":
            filtered.append(item)
    
    if len(filtered) < len(items):
        _LOGGER.warning(
            "Filtered out %d/%d items (player_type=%s). Race condition during media type switch?",
            len(items) - len(filtered), len(items), player_type
        )
    
    return filtered


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
    """Retourne le playlist_id actif = playerid du player actif.

    Kodi utilise le playerid directement comme playlistid (comportement réel).
    """
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
    """Récupère et formate la playlist pour le frontend.

    ✅ IMPROVED: Détecte et valide le player actif, inspiré de la logique legacy.
    Note: Ne retourne PAS kodi_state — le senseur gère l'état Kodi.
    """
    if not _is_kodi_connected(hass, kodi_entity_id):
        return {"items": [], "playlist_id": None, "current_index": -1}

    # ✅ ÉTAPE 1 : Récupérer les PLAYERS ACTIFS (peut être 0, 1, ou plusieurs)
    # Logique inspirée de: if len(players) == 1: (legacy)
    try:
        active_players = await async_call_method(
            hass, kodi_entity_id, "Player.GetActivePlayers"
        )
    except Exception as err:
        _LOGGER.error("Failed to get active players: %s", err)
        return {"items": [], "playlist_id": None, "current_index": -1}
    
    # ✅ ÉTAPE 2 : Vérifier qu'il y a EXACTEMENT 1 player actif
    if not active_players or len(active_players) == 0:
        # Pas de player actif
        return {"items": [], "playlist_id": None, "current_index": -1}
    
    if len(active_players) > 1:
        # Plusieurs players actifs → logger un warning
        # (en théorie ça ne devrait pas arriver)
        _LOGGER.warning(
            "Multiple players active (%d). Using the first one.", len(active_players)
        )
    
    # ✅ ÉTAPE 3 : Extraire les infos du premier (et seul) player
    active_player = active_players[0]
    active_player_type = active_player.get("type")
    active_player_id = active_player.get("playerid")
    
    # ✅ Utiliser directement playerid comme playlistid (comportement Kodi réel).
    # L'ancien code le faisait aussi : self._playlistid = player["playerid"]
    # Le mapping "video→1 / audio→0" est faux : Kodi peut très bien lancer
    # un film avec playerid=0 (ex: Player.Open {movieid: X}).
    active_playlist_id = active_player_id

    _LOGGER.warning(
        "[PLAYLIST] player_id=%s, player_type=%s → using playlist_id=%s",
        active_player_id, active_player_type, active_playlist_id,
    )

    # ✅ ÉTAPE 4 : Récupérer les items DE CE PLAYLIST
    items = []
    if active_playlist_id is not None:
        try:
            raw_items = (
                await _async_fetch_playlist(hass, kodi_entity_id, active_playlist_id) or []
            )

            # ✅ FILTRE CRITIQUE : Valider que les items correspondent au type de player actif
            items = _filter_items_by_player_type(raw_items, active_player_type)

            _LOGGER.debug(
                "Playlist data: type=%s, playlist_id=%d, items_count=%d (raw: %d)",
                active_player_type, active_playlist_id, len(items), len(raw_items)
            )
        except Exception as err:
            _LOGGER.error("Failed to fetch playlist %d: %s", active_playlist_id, err)
            return {"items": [], "playlist_id": active_playlist_id, "current_index": -1}

    # ✅ FALLBACK : Playlist vide mais player actif
    # Kodi joue parfois un item directement (Player.Open avec movieid/songid)
    # sans l'avoir ajouté à la playlist — dans ce cas on synthétise une
    # playlist d'un seul item à partir de Player.GetItem.
    if not items and active_player_id is not None:
        _LOGGER.warning(
            "[PLAYLIST] Playlist %d is empty but player %d is active — fetching current item via Player.GetItem",
            active_playlist_id, active_player_id,
        )
        try:
            item_result = await async_call_method(
                hass,
                kodi_entity_id,
                "Player.GetItem",
                playerid=active_player_id,
                properties=[
                    "showtitle", "album", "albumid", "artist", "artistid",
                    "duration", "genre", "thumbnail", "title", "track",
                    "year", "episode", "season", "art", "file",
                ],
            )
            if item_result and "item" in item_result:
                current_item = item_result["item"]
                # Player.GetItem retourne toujours un item même si rien ne joue ;
                # on vérifie qu'il a au moins un titre ou un fichier.
                if current_item.get("title") or current_item.get("file"):
                    items = [current_item]
                    _LOGGER.warning(
                        "[PLAYLIST] Synthesized playlist from Player.GetItem: type=%s id=%s title=%s",
                        current_item.get("type"), current_item.get("id"), current_item.get("title"),
                    )
        except Exception as err:
            _LOGGER.error("Failed to get current item via Player.GetItem: %s", err)

    # 🚀 SIGNATURE DES URLS
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

    # ✅ ÉTAPE 5 : Récupérer l'index courant du player
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
    last_player_type = None  # ✅ NOUVEAU : Tracker le type de player précédent

    async def _send_playlist(*args):
        nonlocal last_items, last_player_type

        _LOGGER.warning(
            "[PLAYLIST] _send_playlist called — last_player_type=%s, last_items_count=%s",
            last_player_type,
            len(last_items) if last_items is not None else "None",
        )

        # ÉTAPE 1 : Récupérer les players actifs
        active_players = await async_call_method(
            hass, kodi_entity_id, "Player.GetActivePlayers"
        )

        _LOGGER.warning(
            "[PLAYLIST] GetActivePlayers → %s", active_players
        )

        # ÉTAPE 2 : Aucun player actif (transition en cours ou idle)
        if not active_players or len(active_players) == 0:
            # On ne reset PAS last_player_type ici : Kodi peut passer brièvement
            # par 0 player actif lors d'une transition audio→video. On attend
            # l'event suivant qui confirmera le nouveau player.
            _LOGGER.warning(
                "[PLAYLIST] No active player — skipping (last_player_type=%s stays unchanged)",
                last_player_type,
            )
            # On envoie la playlist vide SEULEMENT si on n'avait rien avant non plus
            if last_items is not None and len(last_items) > 0:
                _LOGGER.warning("[PLAYLIST] Had items before, keeping last state — waiting for next event")
            return

        # ÉTAPE 3 : Extraire le type du player actif
        current_player_type = active_players[0].get("type")

        _LOGGER.warning(
            "[PLAYLIST] Active player type=%s (last=%s)",
            current_player_type, last_player_type,
        )

        # ÉTAPE 4 : Détection de transition (audio → video ou vice-versa)
        if last_player_type is not None and last_player_type != current_player_type:
            _LOGGER.warning(
                "[PLAYLIST] Player type changed: %s → %s — forcing full refresh",
                last_player_type, current_player_type,
            )
            last_items = None  # Force l'envoi même si les items sont identiques

        last_player_type = current_player_type

        # ÉTAPE 5 : Récupérer les données de playlist
        data = await _async_get_full_playlist_data(hass, kodi_entity_id)
        items = data["items"]

        _LOGGER.warning(
            "[PLAYLIST] Got %d items (playlist_id=%s, current_index=%s)",
            len(items), data["playlist_id"], data["current_index"],
        )

        # Déduplication: envoyer seulement si les items ont changé
        if items == last_items:
            _LOGGER.warning("[PLAYLIST] Items unchanged — skipping send")
            return

        last_items = items

        payload = {
            "type": "playlist_update",
            "items": items,
            "playlist_id": data["playlist_id"],
            "current_index": data["current_index"],
        }

        _LOGGER.warning(
            "[PLAYLIST] → Sending playlist_update: %d items, playlist_id=%s, current_index=%s",
            len(items), data["playlist_id"], data["current_index"],
        )
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