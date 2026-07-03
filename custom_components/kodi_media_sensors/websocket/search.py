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

from ..const import (
    CONF_KODI_ENTITY,
    DOMAIN,
    OPTION_SEARCH_SONGS_LIMIT,
    DEFAULT_OPTION_SEARCH_SONGS_LIMIT,
    OPTION_SEARCH_ALBUMS_LIMIT,
    DEFAULT_OPTION_SEARCH_ALBUMS_LIMIT,
    OPTION_SEARCH_ARTISTS_LIMIT,
    DEFAULT_OPTION_SEARCH_ARTISTS_LIMIT,
    OPTION_SEARCH_MOVIES_LIMIT,
    DEFAULT_OPTION_SEARCH_MOVIES_LIMIT,
    OPTION_SEARCH_TVSHOWS_LIMIT,
    DEFAULT_OPTION_SEARCH_TVSHOWS_LIMIT,
    OPTION_SEARCH_MUSICVIDEOS_LIMIT,
    DEFAULT_OPTION_SEARCH_MUSICVIDEOS_LIMIT,
    OPTION_SEARCH_EPISODES_LIMIT,
    DEFAULT_OPTION_SEARCH_EPISODES_LIMIT,
    OPTION_SEARCH_CHANNELS_TV_LIMIT,
    DEFAULT_OPTION_SEARCH_CHANNELS_TV_LIMIT,
    OPTION_SEARCH_CHANNELS_RADIO_LIMIT,
    DEFAULT_OPTION_SEARCH_CHANNELS_RADIO_LIMIT,
    OPTION_SEARCH_MUSIC_PLAYLISTS_LIMIT,
    DEFAULT_OPTION_SEARCH_MUSIC_PLAYLISTS_LIMIT,
    OPTION_SEARCH_RECENTLY_ADDED_SONGS_LIMIT,
    DEFAULT_OPTION_SEARCH_RECENTLY_ADDED_SONGS_LIMIT,
    OPTION_SEARCH_RECENTLY_ADDED_ALBUMS_LIMIT,
    DEFAULT_OPTION_SEARCH_RECENTLY_ADDED_ALBUMS_LIMIT,
    OPTION_SEARCH_RECENTLY_ADDED_MOVIES_LIMIT,
    DEFAULT_OPTION_SEARCH_RECENTLY_ADDED_MOVIES_LIMIT,
    OPTION_SEARCH_RECENTLY_ADDED_EPISODES_LIMIT,
    DEFAULT_OPTION_SEARCH_RECENTLY_ADDED_EPISODES_LIMIT,
    OPTION_SEARCH_RECENTLY_ADDED_MUSICVIDEOS_LIMIT,
    DEFAULT_OPTION_SEARCH_RECENTLY_ADDED_MUSICVIDEOS_LIMIT,
    OPTION_SEARCH_RECENTLY_PLAYED_SONGS_LIMIT,
    DEFAULT_OPTION_SEARCH_RECENTLY_PLAYED_SONGS_LIMIT,
    OPTION_SEARCH_RECENTLY_PLAYED_ALBUMS_LIMIT,
    DEFAULT_OPTION_SEARCH_RECENTLY_PLAYED_ALBUMS_LIMIT,
)

from ..kodi_client import async_call_method

_LOGGER = logging.getLogger(__name__)

CATEGORY_ALL = "all"
CATEGORY_MOVIES = "movies"
CATEGORY_TVSHOWS = "tvshows"
CATEGORY_SONGS = "songs"
CATEGORY_ALBUMS = "albums"
CATEGORY_ARTISTS = "artists"
CATEGORY_MUSIC_VIDEOS = "musicvideo"
CATEGORY_EPISODES = "episodes"

VALID_CATEGORIES = [
    CATEGORY_ALL,
    CATEGORY_MOVIES,
    CATEGORY_TVSHOWS,
    CATEGORY_SONGS,
    CATEGORY_ALBUMS,
    CATEGORY_ARTISTS,
    CATEGORY_MUSIC_VIDEOS,
    CATEGORY_EPISODES,
]


@callback
def async_register_websockets(hass: HomeAssistant) -> None:
    """Register search-related WebSocket commands."""
    websocket_api.async_register_command(hass, websocket_search)
    websocket_api.async_register_command(hass, websocket_search_recently_played)
    websocket_api.async_register_command(hass, websocket_search_artist)
    websocket_api.async_register_command(hass, websocket_search_recently_added)
    websocket_api.async_register_command(hass, websocket_search_tvshow)


def _get_kodi_entity_id_from_entry(hass, entry_id):
    """Récupère kodi_entity_id à partir de entry_id"""
    config_entry = hass.config_entries.async_get_entry(entry_id)
    return config_entry.data.get(CONF_KODI_ENTITY)


async def _is_kodi_connected(hass: HomeAssistant, entity_id: str) -> bool:
    """Check if the Kodi entity is available in Home Assistant."""
    state = hass.states.get(entity_id)
    return state is not None and state.state != STATE_UNAVAILABLE


async def _search_movies(
    hass: HomeAssistant, entity_id: str, query: str, search_limits: dict
):
    """Recherche de morceaux avec limite configurable."""
    limit_value = int(
        search_limits.get(CATEGORY_MOVIES, DEFAULT_OPTION_SEARCH_MOVIES_LIMIT)
    )

    result = await async_call_method(
        hass,
        entity_id,
        "VideoLibrary.GetMovies",
        properties=["title", "year", "thumbnail", "genre"],
        filter={"field": "title", "operator": "contains", "value": query},
        limits={"start": 0, "end": limit_value},
        sort={
            "method": "title",
            "order": "ascending",
            "ignorearticle": False,
        },
    )
    return result.get("movies", []) if result else None


async def _search_episodes(
    hass: HomeAssistant, entity_id: str, query: str, search_limits: dict
):
    """Recherche de morceaux avec limite configurable."""
    limit_value = int(
        search_limits.get(CATEGORY_EPISODES, DEFAULT_OPTION_SEARCH_EPISODES_LIMIT)
    )

    result = await async_call_method(
        hass,
        entity_id,
        "VideoLibrary.GetEpisodes",
        properties=[
            "title",
            "episode",
            "season",
            "seasonid",
            "tvshowid",
            "thumbnail",
            "showtitle",
            "art",
        ],
        filter={
            "field": "title",
            "operator": "contains",
            "value": query,
        },
        limits={"start": 0, "end": limit_value},
        sort={
            "method": "title",
            "order": "ascending",
        },
    )

    _LOGGER.warning(result)
    return result.get("episodes", []) if result else None


async def _search_musicvideos(
    hass: HomeAssistant, entity_id: str, query: str, search_limits: dict
):
    """Recherche de morceaux avec limite configurable."""
    limit_value = int(
        search_limits.get(
            CATEGORY_MUSIC_VIDEOS, DEFAULT_OPTION_SEARCH_MUSICVIDEOS_LIMIT
        )
    )

    result = await async_call_method(
        hass,
        entity_id,
        "VideoLibrary.GetMusicVideos",
        properties=["thumbnail", "title", "year", "artist", "album", "art", "genre"],
        filter={
            "or": [
                {"field": "title", "operator": "contains", "value": query},
                {"field": "artist", "operator": "contains", "value": query},
            ]
        },
        limits={"start": 0, "end": limit_value},
        sort={
            "method": "artist",
            "order": "ascending",
            "ignorearticle": False,
        },
    )
    return result.get("movies", []) if result else None


async def _search_tvshows(
    hass: HomeAssistant, entity_id: str, query: str, search_limits: dict
):
    """Recherche de morceaux avec limite configurable."""
    limit_value = int(
        search_limits.get(CATEGORY_TVSHOWS, DEFAULT_OPTION_SEARCH_TVSHOWS_LIMIT)
    )

    result = await async_call_method(
        hass,
        entity_id,
        "VideoLibrary.GetTVShows",
        properties=["title", "year", "thumbnail", "art"],
        filter={"field": "title", "operator": "contains", "value": query},
        limits={"start": 0, "end": limit_value},
        sort={
            "method": "title",
            "order": "ascending",
            "ignorearticle": False,
        },
    )
    return result.get("tvshows", []) if result else None


async def _search_songs(
    hass: HomeAssistant, entity_id: str, query: str, search_limits: dict
):
    """Recherche de morceaux avec limite configurable."""
    limit_value = int(
        search_limits.get(CATEGORY_SONGS, DEFAULT_OPTION_SEARCH_SONGS_LIMIT)
    )

    _LOGGER.debug(f"Search limit for songs: {limit_value}")

    result = await async_call_method(
        hass,
        entity_id,
        "AudioLibrary.GetSongs",
        properties=[
            "title",
            "artist",
            "year",
            "genre",
            "album",
            "albumid",
            "duration",
            "thumbnail",
        ],
        sort={
            "method": "title",
            "order": "ascending",
            "ignorearticle": False,
        },
        limits={"start": 0, "end": limit_value},
        filter={"field": "title", "operator": "contains", "value": query},
    )
    return result.get("songs", []) if result else None


async def _search_albums(
    hass: HomeAssistant, entity_id: str, query: str, search_limits: dict
):
    """Recherche de morceaux avec limite configurable."""
    limit_value = int(
        search_limits.get(CATEGORY_ALBUMS, DEFAULT_OPTION_SEARCH_ALBUMS_LIMIT)
    )

    result = await async_call_method(
        hass,
        entity_id,
        "AudioLibrary.GetAlbums",
        properties=["title", "artist", "year", "thumbnail"],
        filter={"field": "album", "operator": "contains", "value": query},
        limits={"start": 0, "end": limit_value},
        sort={
            "method": "label",
            "order": "ascending",
            "ignorearticle": False,
        },
    )
    return result.get("albums", []) if result else None


async def _search_artists(
    hass: HomeAssistant, entity_id: str, query: str, search_limits: dict
):
    """Recherche de morceaux avec limite configurable."""
    limit_value = int(
        search_limits.get(CATEGORY_ARTISTS, DEFAULT_OPTION_SEARCH_ARTISTS_LIMIT)
    )

    result = await async_call_method(
        hass,
        entity_id,
        "AudioLibrary.GetArtists",
        properties=["thumbnail"],
        filter={"field": "artist", "operator": "contains", "value": query},
        limits={"start": 0, "end": limit_value},
        sort={
            "method": "label",
            "order": "ascending",
            "ignorearticle": False,
        },
    )
    return result.get("artists", []) if result else None


_CATEGORY_HANDLERS = {
    CATEGORY_MOVIES: _search_movies,
    CATEGORY_TVSHOWS: _search_tvshows,
    CATEGORY_SONGS: _search_songs,
    CATEGORY_ALBUMS: _search_albums,
    CATEGORY_ARTISTS: _search_artists,
    CATEGORY_MUSIC_VIDEOS: _search_musicvideos,
    CATEGORY_EPISODES: _search_episodes,
}


async def _async_search(
    hass: HomeAssistant, entity_id: str, query: str, category: str, search_limits: dict
) -> dict:
    """Run the search sequentially to prevent overloading Kodi's webserver."""
    if category == CATEGORY_ALL:
        categories = list(_CATEGORY_HANDLERS)
    else:
        categories = [category]

    results = []
    for cat in categories:
        # On attend que chaque requête se termine avant de lancer la suivante
        res = await _CATEGORY_HANDLERS[cat](hass, entity_id, query, search_limits)
        results.append(res)

    return {
        cat: (items if items is not None else [])
        for cat, items in zip(categories, results)
    }


@websocket_api.websocket_command(
    {
        vol.Required("type"): "kodi_media_sensors/search_artist",
        vol.Required("entry_id"): str,
        vol.Required("artist_id"): vol.Any(int, str),
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
    kodi_entity_id = _get_kodi_entity_id_from_entry(hass, msg["entry_id"])
    artist_id = int(msg["artist_id"])

    if not await _is_kodi_connected(hass, kodi_entity_id):
        connection.send_error(
            msg_id, "kodi_unavailable", "Kodi is currently unreachable"
        )
        return

    try:
        albums_task = async_call_method(
            hass,
            kodi_entity_id,
            "AudioLibrary.GetAlbums",
            properties=["title", "artist", "year", "thumbnail","year"],
            filter={"artistid": artist_id},
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
            filter={"artistid": artist_id},
        )

        raw_albums, raw_songs = await asyncio.gather(albums_task, songs_task)

        albums = raw_albums.get("albums", []) if raw_albums else []
        songs = raw_songs.get("songs", []) if raw_songs else []

        albums_dict = {album["albumid"]: {**album, "songs": []} for album in albums}

        for song in songs:
            album_id = song.get("albumid")
            if album_id in albums_dict:
                albums_dict[album_id]["songs"].append(song)

        structured_albums = list(albums_dict.values())

        mp_component = hass.data.get("media_player")
        mp_entity = mp_component.get_entity(kodi_entity_id) if mp_component else None

        if mp_entity:
            for album in structured_albums:
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

        structured_albums.sort(key=lambda x: x.get("year", 0), reverse=True)
        results = {"albums": structured_albums}
        connection.send_result(msg_id, {"results": results})

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
        # vol.Required("kodi_entity_id"): str,
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
    entry_id = msg["entry_id"]
    kodi_entity_id = _get_kodi_entity_id_from_entry(hass, msg["entry_id"])

    config_entry = hass.config_entries.async_get_entry(entry_id)
    if not config_entry or config_entry.domain != DOMAIN:
        connection.send_error(msg_id, "invalid_entry", f"Entry {entry_id} not found")
        return
    songsLimits = int(
        config_entry.options.get(
            OPTION_SEARCH_RECENTLY_ADDED_SONGS_LIMIT,
            DEFAULT_OPTION_SEARCH_RECENTLY_ADDED_SONGS_LIMIT,
        )
    )
    albumsLimits = int(
        config_entry.options.get(
            OPTION_SEARCH_RECENTLY_ADDED_ALBUMS_LIMIT,
            DEFAULT_OPTION_SEARCH_RECENTLY_ADDED_ALBUMS_LIMIT,
        )
    )
    moviesLimits = int(
        config_entry.options.get(
            OPTION_SEARCH_RECENTLY_ADDED_MOVIES_LIMIT,
            DEFAULT_OPTION_SEARCH_RECENTLY_ADDED_MOVIES_LIMIT,
        )
    )
    episodesLimits = int(
        config_entry.options.get(
            OPTION_SEARCH_RECENTLY_ADDED_EPISODES_LIMIT,
            DEFAULT_OPTION_SEARCH_RECENTLY_ADDED_EPISODES_LIMIT,
        )
    )
    musicvideosLimits = int(
        config_entry.options.get(
            OPTION_SEARCH_RECENTLY_ADDED_MUSICVIDEOS_LIMIT,
            DEFAULT_OPTION_SEARCH_RECENTLY_ADDED_MUSICVIDEOS_LIMIT,
        )
    )
    try:
        songs_task = async_call_method(
            hass,
            kodi_entity_id,
            "AudioLibrary.GetRecentlyAddedSongs",
            properties=[
                "title",
                "artist",
                "album",
                "duration",
                "thumbnail",
                "file",
                "albumid",
            ],
            limits={"start": 0, "end": songsLimits},
        )

        albums_task = async_call_method(
            hass,
            kodi_entity_id,
            "AudioLibrary.GetRecentlyAddedAlbums",
            properties=[
                "thumbnail",
                "title",
                "year",
                "art",
                "genre",
                "artist",
                "artistid",
            ],
            limits={"start": 0, "end": albumsLimits},
        )

        movies_task = async_call_method(
            hass,
            kodi_entity_id,
            "VideoLibrary.GetRecentlyAddedMovies",
            properties=["title", "year", "thumbnail", "file", "rating"],
            limits={"start": 0, "end": moviesLimits},
        )

        episodes_task = async_call_method(
            hass,
            kodi_entity_id,
            "VideoLibrary.GetRecentlyAddedEpisodes",
            properties=[
                "title",
                "episode",
                "season",
                "seasonid",
                "tvshowid",
                "thumbnail",
                "showtitle",
                "art",
            ],
            limits={"start": 0, "end": episodesLimits},
        )

        musicvideos_task = async_call_method(
            hass,
            kodi_entity_id,
            "VideoLibrary.GetRecentlyAddedMusicVideos",
            properties=[
                "thumbnail",
                "title",
                "year",
                "artist",
                "album",
                "art",
                "genre",
            ],
            limits={"start": 0, "end": musicvideosLimits},
        )

        (
            raw_songs,
            raw_albums,
            raw_movies,
            raw_episodes,
            raw_musicvideos,
        ) = await asyncio.gather(
            songs_task, albums_task, movies_task, episodes_task, musicvideos_task
        )

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

        connection.send_result(msg_id, {"results": results})

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
        # vol.Required("kodi_entity_id"): str,
    }
)
@websocket_api.async_response
async def websocket_search_recently_played(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict,
) -> None:
    """Fetch recently played songs."""
    msg_id = msg["id"]
    entry_id = msg["entry_id"]
    msg_id = msg["id"]
    kodi_entity_id = _get_kodi_entity_id_from_entry(hass, entry_id)
    config_entry = hass.config_entries.async_get_entry(entry_id)
    if not config_entry or config_entry.domain != DOMAIN:
        connection.send_error(msg_id, "invalid_entry", f"Entry {entry_id} not found")
        return
    songsLimits = int(
        config_entry.options.get(
            OPTION_SEARCH_RECENTLY_PLAYED_SONGS_LIMIT,
            DEFAULT_OPTION_SEARCH_RECENTLY_PLAYED_SONGS_LIMIT,
        )
    )
    albumsLimits = int(
        config_entry.options.get(
            OPTION_SEARCH_RECENTLY_PLAYED_ALBUMS_LIMIT,
            DEFAULT_OPTION_SEARCH_RECENTLY_PLAYED_ALBUMS_LIMIT,
        )
    )
    try:
        songs_task = async_call_method(
            hass,
            kodi_entity_id,
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
            limits={"end": songsLimits},
        )
        albums_task = async_call_method(
            hass,
            kodi_entity_id,
            "AudioLibrary.GetRecentlyPlayedAlbums",
            properties=[
                "thumbnail",
                "title",
                "year",
                "art",
                "genre",
                "artist",
                "artistid",
            ],
            limits={"start": 0, "end": albumsLimits},
        )

        (
            raw_songs,
            raw_albums,
        ) = await asyncio.gather(songs_task, albums_task)

        results = {
            "songs": raw_songs.get("songs", []) if raw_songs else [],
            "albums": raw_albums.get("albums", []) if raw_albums else [],
        }

        connection.send_result(msg_id, {"results": results})

    except Exception as e:
        connection.send_error(
            msg_id,
            websocket_api.const.ERR_UNKNOWN_ERROR,
            f"Erreur lors de la requête Kodi : {str(e)}",
        )


@websocket_api.websocket_command(
    {
        vol.Required("type"): "kodi_media_sensors/search",
        vol.Required("entry_id"): str,
        # vol.Required("kodi_entity_id"): str,
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
    kodi_entity_id = _get_kodi_entity_id_from_entry(hass, msg["entry_id"])
    category = msg["category"]

    config_entry = hass.config_entries.async_get_entry(entry_id)
    if not config_entry or config_entry.domain != DOMAIN:
        connection.send_error(msg_id, "invalid_entry", f"Entry {entry_id} not found")
        return

    search_limits = {
        CATEGORY_SONGS: config_entry.options.get(
            OPTION_SEARCH_SONGS_LIMIT, DEFAULT_OPTION_SEARCH_SONGS_LIMIT
        ),
        CATEGORY_ALBUMS: config_entry.options.get(
            OPTION_SEARCH_ALBUMS_LIMIT, DEFAULT_OPTION_SEARCH_ALBUMS_LIMIT
        ),
        CATEGORY_MOVIES: config_entry.options.get(
            OPTION_SEARCH_MOVIES_LIMIT, DEFAULT_OPTION_SEARCH_MOVIES_LIMIT
        ),
        CATEGORY_TVSHOWS: config_entry.options.get(
            OPTION_SEARCH_TVSHOWS_LIMIT, DEFAULT_OPTION_SEARCH_TVSHOWS_LIMIT
        ),
        CATEGORY_ARTISTS: config_entry.options.get(
            OPTION_SEARCH_ARTISTS_LIMIT, DEFAULT_OPTION_SEARCH_ARTISTS_LIMIT
        ),
        CATEGORY_MUSIC_VIDEOS: config_entry.options.get(
            OPTION_SEARCH_MUSICVIDEOS_LIMIT, DEFAULT_OPTION_SEARCH_MUSICVIDEOS_LIMIT
        ),
        CATEGORY_EPISODES: config_entry.options.get(
            OPTION_SEARCH_EPISODES_LIMIT, DEFAULT_OPTION_SEARCH_EPISODES_LIMIT
        ),
    }

    if not await _is_kodi_connected(hass, kodi_entity_id):
        connection.send_error(
            msg_id, "kodi_unavailable", "Kodi is currently unreachable"
        )
        return

    if not query.strip():
        connection.send_error(msg_id, "invalid_query", "Query cannot be empty")
        return

    results = await _async_search(hass, kodi_entity_id, query, category, search_limits)

    mp_component = hass.data.get("media_player")
    mp_entity = mp_component.get_entity(kodi_entity_id) if mp_component else None
    if mp_entity:
        for cat, items in results.items():
            for item in items:
                thumb = item.get("thumbnail")

                final_thumb = None
                if isinstance(thumb, list):
                    final_thumb = next((t for t in thumb if t is not None), None)
                elif isinstance(thumb, str):
                    final_thumb = thumb

                if final_thumb and final_thumb.startswith("image://"):
                    item["thumbnail"] = await mp_entity.async_get_browse_image(
                        "image", final_thumb
                    )
                else:
                    item["thumbnail"] = None

    connection.send_result(msg_id, {"results": results})


@websocket_api.websocket_command(
    {
        vol.Required("type"): "kodi_media_sensors/search_tvshow",
        vol.Optional("entry_id"): str,
        vol.Optional("kodi_entity_id"): str,
        vol.Required("tvshow_id"): vol.Any(int, str),
    }
)
@callback
def websocket_search_tvshow(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict
) -> None:
    """Handle search tvshow websocket command."""
    hass.async_create_task(_async_handle_search_tvshow(hass, connection, msg))


async def _async_handle_search_tvshow(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict
) -> None:
    """Fetch seasons and episodes for a given TV Show."""
    msg_id = msg["id"]
    entry_id = msg.get("entry_id")
    kodi_entity_id = msg.get("kodi_entity_id")

    # Résolution de l'entité Kodi si on n'a que l'entry_id
    if not kodi_entity_id and entry_id:
        _get_kodi_entity_id_from_entry = globals().get("_get_kodi_entity_id_from_entry")
        if _get_kodi_entity_id_from_entry:
            kodi_entity_id = _get_kodi_entity_id_from_entry(hass, entry_id)

    if not kodi_entity_id:
        connection.send_error(msg_id, "invalid_entity", "No Kodi entity configured")
        return

    tvshow_id = int(msg["tvshow_id"])

    try:
        # 1. Récupérer les saisons de la série
        seasons_response = await async_call_method(
            hass,
            kodi_entity_id,
            "VideoLibrary.GetSeasons",
            tvshowid=tvshow_id,
            properties=["title", "season", "thumbnail", "tvshowid","art"],
        )
        seasons = seasons_response.get("seasons", []) if seasons_response else []

        # 2. Récupérer tous les épisodes (Correction ici : "runtime" au lieu de "duration")
        episodes_response = await async_call_method(
            hass,
            kodi_entity_id,
            "VideoLibrary.GetEpisodes",
            tvshowid=tvshow_id,
            properties=[
                "title",
                "season",
                "episode",
                "runtime",
                "thumbnail",
                "tvshowid",
                "file",
                "art",
            ],
        )
        all_episodes = (
            episodes_response.get("episodes", []) if episodes_response else []
        )

        # 3. Imbriquer les épisodes dans la saison correspondante
        for season in seasons:
            season["type"] = "season"
            season_num = season.get("season")

            # Filtrer et trier les épisodes de cette saison spécifique
            season_episodes = [
                ep for ep in all_episodes if ep.get("season") == season_num
            ]
            season_episodes.sort(key=lambda x: x.get("episode", 0))

            # Optionnel : Si tu veux convertir le "runtime" de Kodi (en secondes) en format "duration" pour le front
            for ep in season_episodes:
                if "runtime" in ep:
                    ep["duration"] = ep[
                        "runtime"
                    ]  # Permet la compatibilité avec vos types front si besoin

            season["episodes"] = season_episodes

        # 4. Traitement des images (thumbnails) via le media_player de HA
        mp_component = hass.data.get("media_player")
        mp_entity = mp_component.get_entity(kodi_entity_id) if mp_component else None

        if mp_entity:
            for season in seasons:
                thumb = season.get("thumbnail")
                if isinstance(thumb, str) and thumb.startswith("image://"):
                    season["thumbnail"] = await mp_entity.async_get_browse_image(
                        "image", thumb
                    )

                for episode in season.get("episodes", []):
                    ep_thumb = episode.get("thumbnail")
                    if isinstance(ep_thumb, str) and ep_thumb.startswith("image://"):
                        episode["thumbnail"] = await mp_entity.async_get_browse_image(
                            "image", ep_thumb
                        )

        results = {"seasons": seasons}
        connection.send_result(msg_id, {"results": results})

    except Exception as e:
        _LOGGER.error("Error searching TV show details: %s", e)
        connection.send_error(msg_id, "search_error", str(e))
