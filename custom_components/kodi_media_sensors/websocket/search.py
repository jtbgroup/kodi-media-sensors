"""WebSocket command to search Kodi's media libraries.

Provides the `kodi_media_sensors/search` command. This is a one-shot
request/response command (not a subscription): the client sends a
query and an optional category, and receives a single result message.
"""
import asyncio
import logging
import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback
from homeassistant.const import STATE_UNAVAILABLE

from ..const import DOMAIN, CONF_KODI_ENTITY
from ..kodi_client import async_call_method

_LOGGER = logging.getLogger(__name__)

CATEGORY_ALL = "all"
CATEGORY_MOVIES = "movies"
CATEGORY_TVSHOWS = "tvshows"
CATEGORY_SONGS = "songs"
CATEGORY_ALBUMS = "albums"
CATEGORY_ARTISTS = "artists"

VALID_CATEGORIES = [
    CATEGORY_ALL,
    CATEGORY_MOVIES,
    CATEGORY_TVSHOWS,
    CATEGORY_SONGS,
    CATEGORY_ALBUMS,
    CATEGORY_ARTISTS,
]

@callback
def async_register_websockets(hass: HomeAssistant) -> None:
    """Register search-related WebSocket commands."""
    websocket_api.async_register_command(hass, websocket_search)

async def _is_kodi_connected(hass: HomeAssistant, entity_id: str) -> bool:
    """Check if the Kodi entity is available in Home Assistant."""
    state = hass.states.get(entity_id)
    return state is not None and state.state != STATE_UNAVAILABLE

async def _search_movies(hass: HomeAssistant, entity_id: str, query: str):
    result = await async_call_method(
        hass, entity_id, "VideoLibrary.GetMovies",
        properties=["title", "year", "thumbnail", "file", "rating"],
        filter={"field": "title", "operator": "contains", "value": query},
    )
    return result.get("movies", []) if result else None

async def _search_tvshows(hass: HomeAssistant, entity_id: str, query: str):
    result = await async_call_method(
        hass, entity_id, "VideoLibrary.GetTVShows",
        properties=["title", "year", "thumbnail", "rating"],
        filter={"field": "title", "operator": "contains", "value": query},
    )
    return result.get("tvshows", []) if result else None

async def _search_songs(hass: HomeAssistant, entity_id: str, query: str):
    result = await async_call_method(
        hass, entity_id, "AudioLibrary.GetSongs",
        properties=["title", "artist", "album", "duration", "thumbnail", "file", "albumid"],
        filter={"field": "title", "operator": "contains", "value": query},
    )
    return result.get("songs", []) if result else None

async def _search_albums(hass: HomeAssistant, entity_id: str, query: str):
    result = await async_call_method(
        hass, entity_id, "AudioLibrary.GetAlbums",
        properties=["title", "artist", "year", "thumbnail"],
        filter={"field": "album", "operator": "contains", "value": query},
    )
    return result.get("albums", []) if result else None

async def _search_artists(hass: HomeAssistant, entity_id: str, query: str):
    result = await async_call_method(
        hass, entity_id, "AudioLibrary.GetArtists",
        properties=["thumbnail"],
        filter={"field": "artist", "operator": "contains", "value": query},
    )
    return result.get("artists", []) if result else None

_CATEGORY_HANDLERS = {
    CATEGORY_MOVIES: _search_movies,
    CATEGORY_TVSHOWS: _search_tvshows,
    CATEGORY_SONGS: _search_songs,
    CATEGORY_ALBUMS: _search_albums,
    CATEGORY_ARTISTS: _search_artists,
}

async def _async_search(hass: HomeAssistant, entity_id: str, query: str, category: str) -> dict:
    """Run the search and return a dict keyed by category."""
    if category == CATEGORY_ALL:
        categories = list(_CATEGORY_HANDLERS)
    else:
        categories = [category]

    coroutines = [_CATEGORY_HANDLERS[cat](hass, entity_id, query) for cat in categories]
    results = await asyncio.gather(*coroutines)

    return {
        cat: (items if items is not None else [])
        for cat, items in zip(categories, results)
    }

@websocket_api.websocket_command({
    vol.Required("type"): "kodi_media_sensors/search",
    vol.Required("entry_id"): str,
    vol.Required("kodi_entity_id"): str,
    vol.Required("query"): str,
    vol.Optional("category"): vol.In(VALID_CATEGORIES),
})
@websocket_api.async_response
async def websocket_search(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict,
) -> None:
    """Search Kodi's libraries for the given query."""
    entry_id = msg["entry_id"]
    msg_id = msg["id"]
    query = msg["query"]
    kodi_entity_id = msg["kodi_entity_id"]
    category = msg["category"]

    config_entry = hass.config_entries.async_get_entry(entry_id)
    if not config_entry or config_entry.domain != DOMAIN:
        connection.send_error(msg_id, "invalid_entry", f"Entry {entry_id} not found")
        return

    # entity_id = config_entry.data.get(CONF_KODI_ENTITY)
    # if not entity_id:
    #     connection.send_error(msg_id, "invalid_config", "No Kodi entity configured")
    #     return

    # Vérification de la connexion avant exécution
    if not await _is_kodi_connected(hass, kodi_entity_id):
        connection.send_error(msg_id, "kodi_unavailable", "Kodi is currently unreachable")
        return

    if not query.strip():
        connection.send_error(msg_id, "invalid_query", "Query cannot be empty")
        return

    results = await _async_search(hass, kodi_entity_id, query, category)
    
   # 🚀 Génération de tokens sécurisés officiels HA pour chaque miniature de recherche
    mp_component = hass.data.get("media_player")
    mp_entity = mp_component.get_entity(kodi_entity_id) if mp_component else None
    if mp_entity:
        for cat, items in results.items():
            for item in items:
                thumb = item.get("thumbnail")
                
                # 1. Extraction : si c'est une liste, on prend le premier élément non-null
                final_thumb = None
                if isinstance(thumb, list):
                    # Trouve le premier élément qui n'est pas None
                    final_thumb = next((t for t in thumb if t is not None), None)
                elif isinstance(thumb, str):
                    final_thumb = thumb
                
                # 2. Transformation : si on a une URL Kodi, on demande le proxy
                if final_thumb and final_thumb.startswith("image://"):
                    # On utilise await pour obtenir l'URL réelle
                    item["thumbnail"] = await mp_entity.async_get_browse_image("image", final_thumb)
                else:
                    item["thumbnail"] = None

    # Envoi du résultat enrichi avec les vraies URLs de confiance
    connection.send_result(msg_id, {
        "results": results,
        "kodi_entity_id": kodi_entity_id
    })
    