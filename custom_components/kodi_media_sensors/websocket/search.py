"""WebSocket command to search Kodi's media libraries.

Provides the `kodi_media_sensors/search` command. This is a one-shot
request/response command (not a subscription): the client sends a
query and an optional category, and receives a single result message.
"""

import asyncio
import logging
import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.const import STATE_UNAVAILABLE

from ..const import (
    DOMAIN,
    OPTION_SEARCH_SONGS_LIMIT,
    DEFAULT_OPTION_SEARCH_SONGS_LIMIT,
    OPTION_SEARCH_ALBUMS_LIMIT,
    DEFAULT_OPTION_SEARCH_ALBUMS_LIMIT,
)
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
    websocket_api.async_register_command(hass, websocket_search_recently_played)
    websocket_api.async_register_command(hass, websocket_search_artist)
    websocket_api.async_register_command(hass, websocket_search_recently_added)


async def _is_kodi_connected(hass: HomeAssistant, entity_id: str) -> bool:
    """Check if the Kodi entity is available in Home Assistant."""
    state = hass.states.get(entity_id)
    return state is not None and state.state != STATE_UNAVAILABLE


def _getSearchLimit(config_entry: ConfigEntry, option_key: str, default: int):
    search_limit = config_entry.options.get(option_key, default)
    return {"start": 0, "end": search_limit}


async def _search_movies(hass: HomeAssistant, config_entry: ConfigEntry,entity_id: str, query: str):
    result = await async_call_method(
        hass,
        entity_id,
        "VideoLibrary.GetMovies",
        properties=["title", "year", "thumbnail", "file", "rating"],
        filter={"field": "title", "operator": "contains", "value": query},
    )
    return result.get("movies", []) if result else None


async def _search_tvshows(hass: HomeAssistant, config_entry: ConfigEntry,entity_id: str, query: str):
    result = await async_call_method(
        hass,
        entity_id,
        "VideoLibrary.GetTVShows",
        properties=["title", "year", "thumbnail", "rating"],
        filter={"field": "title", "operator": "contains", "value": query},
    )
    return result.get("tvshows", []) if result else None


async def _search_songs(
    hass: HomeAssistant, config_entry: ConfigEntry, entity_id: str, query: str
):
    result = await async_call_method(
        hass,
        entity_id,
        "AudioLibrary.GetSongs",
        properties=[
            "title",
            "artist",
            "album",
            "duration",
            "thumbnail",
            "file",
            "albumid",
        ],
        filter={"field": "title", "operator": "contains", "value": query},
        limits=_getSearchLimit(config_entry, OPTION_SEARCH_SONGS_LIMIT, DEFAULT_OPTION_SEARCH_SONGS_LIMIT)
    )
    return result.get("songs", []) if result else None


async def _search_albums(hass: HomeAssistant, config_entry: ConfigEntry,entity_id: str, query: str):
    result = await async_call_method(
        hass,
        entity_id,
        "AudioLibrary.GetAlbums",
        properties=["title", "artist", "year", "thumbnail"],
        filter={"field": "album", "operator": "contains", "value": query},
    )
    return result.get("albums", []) if result else None


async def _search_artists(hass: HomeAssistant, config_entry: ConfigEntry,entity_id: str, query: str):
    result = await async_call_method(
        hass,
        entity_id,
        "AudioLibrary.GetArtists",
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


async def _async_search(
    hass: HomeAssistant, kodi_entity_id: str, entry_id: str, query: str, category: str
) -> dict:
    """Run the search and return a dict keyed by category."""
    if category == CATEGORY_ALL:
        categories = list(_CATEGORY_HANDLERS)
    else:
        categories = [category]

    config_entry = hass.config_entries.async_get_entry(entry_id)
    # if not config_entry or config_entry.domain != DOMAIN:
    #     connection.send_error(msg_id, "invalid_entry", f"Entry {entry_id} not found")
    #     return

    # search_limit = config_entry.options.get(
    #     OPTION_SEARCH_SONGS_LIMIT, DEFAULT_OPTION_SEARCH_SONGS_LIMIT
    # )

    coroutines = [
        _CATEGORY_HANDLERS[cat](hass,config_entry, kodi_entity_id, query)
        for cat in categories
    ]
    results = await asyncio.gather(*coroutines)

    return {
        cat: (items if items is not None else [])
        for cat, items in zip(categories, results)
    }


@websocket_api.websocket_command(
    {
        vol.Required("type"): "kodi_media_sensors/search_artist",
        vol.Required("kodi_entity_id"): str,
        vol.Required("artistid"): vol.Any(
            int, str
        ),  # 🚀 L'ID transmis par le clic frontend
    }
)
@websocket_api.async_response
async def websocket_search_artist(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict,
) -> None:
    """Get detailed view of an artist (Albums containing their Songs)."""
    msg_id = msg["id"]
    kodi_entity_id = msg["kodi_entity_id"]
    artist_id = int(msg["artistid"])

    # Vérification de la connexion
    if not await _is_kodi_connected(hass, kodi_entity_id):
        connection.send_error(
            msg_id, "kodi_unavailable", "Kodi is currently unreachable"
        )
        return

    try:
        # 1. Récupération des albums de l'artiste en parallèle avec ses morceaux
        albums_task = async_call_method(
            hass,
            kodi_entity_id,
            "AudioLibrary.GetAlbums",
            properties=["title", "artist", "year", "thumbnail"],
            filter={"artistid": artist_id},  # 🚀 La bonne syntaxe raccourcie !
        )

        songs_task = async_call_method(
            hass,
            kodi_entity_id,
            "AudioLibrary.GetSongs",
            properties=[
                "title",
                "artist",
                "album",
                "duration",
                "thumbnail",
                "file",
                "albumid",
            ],
            filter={"artistid": artist_id},  # 🚀 La bonne syntaxe raccourcie !
        )

        raw_albums, raw_songs = await asyncio.gather(albums_task, songs_task)

        albums = raw_albums.get("albums", []) if raw_albums else []
        songs = raw_songs.get("songs", []) if raw_songs else []

        # 2. Imbrication idéale : On distribue les morceaux dans leurs albums respectifs
        albums_dict = {album["albumid"]: {**album, "songs": []} for album in albums}

        # S'il y a des chansons orphelines (ex: single sans album), on crée un conteneur fictif si nécessaire,
        # mais Kodi lie généralement les morceaux à un album (ou "Unknown Album")
        for song in songs:
            album_id = song.get("albumid")
            if album_id in albums_dict:
                albums_dict[album_id]["songs"].append(song)

        structured_albums = list(albums_dict.values())

        # 3. Traitement des images via le Media Player Proxy de Home Assistant (Authentification)
        mp_component = hass.data.get("media_player")
        mp_entity = mp_component.get_entity(kodi_entity_id) if mp_component else None

        if mp_entity:
            for album in structured_albums:
                # Signer la miniature de l'album
                thumb = album.get("thumbnail")
                final_thumb = (
                    next((t for t in thumb if t is not None), None)
                    if isinstance(thumb, list)
                    else thumb
                )
                if final_thumb and final_thumb.startswith("image://"):
                    album["thumbnail"] = await mp_entity.async_get_browse_image(
                        "image", final_thumb
                    )
                else:
                    album["thumbnail"] = None

                # Signer la miniature de chaque chanson à l'intérieur
                for song in album["songs"]:
                    s_thumb = song.get("thumbnail")
                    final_s_thumb = (
                        next((t for t in s_thumb if t is not None), None)
                        if isinstance(s_thumb, list)
                        else s_thumb
                    )
                    if final_s_thumb and final_s_thumb.startswith("image://"):
                        song["thumbnail"] = await mp_entity.async_get_browse_image(
                            "image", final_s_thumb
                        )
                    else:
                        song["thumbnail"] = None

        # 4. Envoi de la structure propre au frontend sous la clé "albums"
        connection.send_result(msg_id, {"albums": structured_albums})

    except Exception as e:
        _LOGGER.error("Erreur lors du drill-down de l'artiste %s: %s", artist_id, e)
        connection.send_error(
            msg_id,
            websocket_api.const.ERR_UNKNOWN_ERROR,
            f"Erreur lors de la requête Kodi : {str(e)}",
        )


@websocket_api.websocket_command(
    {
        vol.Required("type"): "kodi_media_sensors/search_recently_added",
        vol.Required("entry_id"): str,
        vol.Required("kodi_entity_id"): str,
    }
)
@websocket_api.async_response
async def websocket_search_recently_added(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict,
) -> None:
    """Fetch all recently added media from Kodi (Songs, Albums, Movies, Episodes, Music Videos)."""
    msg_id = msg["id"]
    kodi_entity_id = msg["kodi_entity_id"]

    try:
        # 1. Préparation de toutes les requêtes en parallèle (50 éléments max)
        # ⚠️ NOTE : On ne passe PLUS 'songid', 'albumid', etc. dans 'properties' car Kodi les renvoie déjà par défaut !
        limit = {"end": 50}

        songs_task = async_call_method(
            hass,
            kodi_entity_id,
            "AudioLibrary.GetRecentlyAddedSongs",
            properties=["title", "artist", "album", "duration", "thumbnail", "file"],
            limits=limit,
        )

        albums_task = async_call_method(
            hass,
            kodi_entity_id,
            "AudioLibrary.GetRecentlyAddedAlbums",
            properties=["title", "artist", "year", "thumbnail"],
            limits=limit,
        )

        movies_task = async_call_method(
            hass,
            kodi_entity_id,
            "VideoLibrary.GetRecentlyAddedMovies",
            properties=["title", "year", "thumbnail", "file", "rating"],
            limits=limit,
        )

        episodes_task = async_call_method(
            hass,
            kodi_entity_id,
            "VideoLibrary.GetRecentlyAddedEpisodes",
            properties=[
                "title",
                "showtitle",
                "season",
                "episode",
                "thumbnail",
                "file",
                "rating",
            ],
            limits=limit,
        )

        musicvideos_task = async_call_method(
            hass,
            kodi_entity_id,
            "VideoLibrary.GetRecentlyAddedMusicVideos",
            properties=["title", "artist", "album", "thumbnail", "file"],
            limits=limit,
        )

        # 2. Exécution simultanée des 5 requêtes pour des performances maximales
        (
            raw_songs,
            raw_albums,
            raw_movies,
            raw_episodes,
            raw_musicvideos,
        ) = await asyncio.gather(
            songs_task, albums_task, movies_task, episodes_task, musicvideos_task
        )

        # 3. Structuration propre des résultats par catégories
        results = {
            "songs": raw_songs.get("songs", []) if raw_songs else [],
            "albums": raw_albums.get("albums", []) if raw_albums else [],
            "movies": raw_movies.get("movies", []) if raw_movies else [],
            "musicvideos": raw_musicvideos.get("musicvideos", [])
            if raw_musicvideos
            else [],
            "episodes": [
                {
                    **ep,
                    "artist": ep.get("showtitle"),
                    "label": f"S{ep.get('season', 0):02d}E{ep.get('episode', 0):02d} - {ep.get('title')}",
                }
                for ep in (raw_episodes.get("episodes", []) if raw_episodes else [])
            ],
        }

        # 4. Sécurisation des miniatures via le proxy de Home Assistant
        mp_component = hass.data.get("media_player")
        mp_entity = mp_component.get_entity(kodi_entity_id) if mp_component else None

        if mp_entity:
            for category, items in results.items():
                for item in items:
                    thumb = item.get("thumbnail")
                    final_thumb = (
                        next((t for t in thumb if t is not None), None)
                        if isinstance(thumb, list)
                        else thumb
                    )
                    if final_thumb and final_thumb.startswith("image://"):
                        item["thumbnail"] = await mp_entity.async_get_browse_image(
                            "image", final_thumb
                        )
                    else:
                        item["thumbnail"] = None

        # 5. Envoi du résultat nettoyé au frontend
        connection.send_result(
            msg_id,
            {"results": results},
        )

    except Exception as e:
        connection.send_error(
            msg_id,
            websocket_api.const.ERR_UNKNOWN_ERROR,
            f"Erreur lors de la requête Kodi : {str(e)}",
        )


@websocket_api.websocket_command(
    {
        vol.Required("type"): "kodi_media_sensors/search_recently_played",
        vol.Required("entry_id"): str,
        vol.Required("kodi_entity_id"): str,
    }
)
@websocket_api.async_response
async def websocket_search_recently_played(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict,
) -> None:
    try:
        # On passe les 3 arguments requis, puis les paramètres nommés par analogie avec le reste du fichier
        raw_result = await async_call_method(
            hass,
            msg["kodi_entity_id"],
            "AudioLibrary.GetSongs",
            properties=[
                "title",
                "album",
                "albumid",
                "artist",
                "artistid",
                "track",
                "year",
                "duration",
                "genre",
                "thumbnail",
            ],
            sort={
                "method": "lastplayed",
                "order": "descending",
            },
            limits={"end": 50},
        )

        # 2. On extrait les morceaux
        items = raw_result.get("songs", []) if raw_result else []

        connection.send_result(
            msg["id"],
            {"items": items},
        )

    except Exception as e:
        connection.send_error(
            msg["id"],
            websocket_api.const.ERR_UNKNOWN_ERROR,
            f"Erreur lors de la requête Kodi : {str(e)}",
        )


@websocket_api.websocket_command(
    {
        vol.Required("type"): "kodi_media_sensors/search",
        vol.Required("entry_id"): str,
        vol.Required("kodi_entity_id"): str,
        vol.Required("query"): str,
        vol.Optional("category"): vol.In(VALID_CATEGORIES),
    }
)
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

    # config_entry = hass.config_entries.async_get_entry(entry_id)
    # if not config_entry or config_entry.domain != DOMAIN:
    #     connection.send_error(msg_id, "invalid_entry", f"Entry {entry_id} not found")
    #     return

    # search_limit = config_entry.options.get(
    #     OPTION_SEARCH_SONGS_LIMIT, DEFAULT_OPTION_SEARCH_SONGS_LIMIT
    # )

    # Vous pouvez maintenant utiliser 'search_limit' dans votre logique de recherche

    # entity_id = config_entry.data.get(CONF_KODI_ENTITY)
    # if not entity_id:
    #     connection.send_error(msg_id, "invalid_config", "No Kodi entity configured")
    #     return

    # Vérification de la connexion avant exécution
    if not await _is_kodi_connected(hass, kodi_entity_id):
        connection.send_error(
            msg_id, "kodi_unavailable", "Kodi is currently unreachable"
        )
        return

    if not query.strip():
        connection.send_error(msg_id, "invalid_query", "Query cannot be empty")
        return

    results = await _async_search(hass, kodi_entity_id, entry_id, query, category)

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
                    item["thumbnail"] = await mp_entity.async_get_browse_image(
                        "image", final_thumb
                    )
                else:
                    item["thumbnail"] = None

    # Envoi du résultat enrichi avec les vraies URLs de confiance
    connection.send_result(
        msg_id, {"results": results, "kodi_entity_id": kodi_entity_id}
    )
