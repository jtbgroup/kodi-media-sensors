import logging
import homeassistant
import time
from typing import Dict, List, Any
from .entity_kodi_media_sensor import KodiMediaSensorEntity
from homeassistant.const import STATE_OFF, STATE_ON
from pykodi import Kodi
from .const import (
    ENTITY_SENSOR_SEARCH,
    ENTITY_NAME_SENSOR_SEARCH,
    MEDIA_TYPE_SEASON_DETAIL,
    OPTION_SEARCH_LIMIT_DEFAULT_VALUE,
    PROPS_SEASON,
    PROPS_RECENT_EPISODES,
    PROPS_ALBUM,
    PROPS_ALBUM_DETAIL,
    PROPS_ARTIST,
    PROPS_EPISODE,
    PROPS_MOVIE,
    PROPS_SONG,
    PROPS_TVSHOW,
)
from .types import KodiConfig

_LOGGER = logging.getLogger(__name__)
ACTION_DO_NOTHING = "nothing"
ACTION_CLEAR = "clear"
ACTION_REFRESH_META = "refresh_meta"

METHOD_SEARCH = "search"
METHOD_CLEAR = "clear"
METHOD_PLAY = "play"
SEARCH_MEDIA_TYPE_ALL = "all"
SEARCH_MEDIA_TYPE_RECENT = "recent"
SEARCH_MEDIA_TYPE_ARTIST = "artist"
SEARCH_MEDIA_TYPE_TVSHOW = "tvshow"
PLAY_ATTR_SONGID = "songid"
PLAY_ATTR_ALBUMID = "albumid"
PLAY_ATTR_MOVIEID = "movieid"
PLAY_ATTR_EPISODEID = "episodeid"


class KodiSearchEntity(KodiMediaSensorEntity):
    """This sensor is dedicated to the search functionality of Kodi"""

    _search_limit = OPTION_SEARCH_LIMIT_DEFAULT_VALUE
    _search_moment = 0
    _clear_timer = 300

    def __init__(
        self,
        hass,
        kodi: Kodi,
        kodi_entity_id,
        config: KodiConfig,
        search_limit: int,
    ):
        super().__init__(kodi, config)
        self._hass = hass
        self._search_limit = search_limit
        homeassistant.helpers.event.async_track_state_change_event(
            hass, kodi_entity_id, self.__handle_event
        )

        kodi_state = self._hass.states.get(kodi_entity_id)
        if kodi_state is None or kodi_state == STATE_OFF:
            self._state = STATE_OFF
        else:
            self._state = STATE_ON

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return ENTITY_NAME_SENSOR_SEARCH

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return ENTITY_SENSOR_SEARCH

    async def __handle_event(self, event):
        new_kodi_event_state = str(event.data.get("new_state").state)

        action = ACTION_DO_NOTHING
        new_entity_state = STATE_ON

        if new_kodi_event_state == STATE_OFF and self._state != STATE_OFF:
            action = ACTION_CLEAR
            new_entity_state = STATE_OFF
        elif new_kodi_event_state != STATE_OFF and self._state != STATE_ON:
            action = ACTION_REFRESH_META

        self._state = new_entity_state

        ctxt_id = event.context.id + " [" + new_kodi_event_state + "]"
        if action == ACTION_CLEAR:
            self._clear_all_data(ctxt_id)
        if action == ACTION_REFRESH_META:
            self.purge_data(ctxt_id)
            self.init_meta(ctxt_id)

        if action != ACTION_DO_NOTHING:
            self.schedule_update_ha_state()

    async def async_update(self):
        """Update is only used to purge the search result"""
        _LOGGER.debug("> Update Search sensor")

        if self._state != STATE_OFF and len(self._meta) == 0:
            self.init_meta("Kodi Search update event")

        if (
            self._search_moment > 0
            and (time.perf_counter() - self._search_moment) > self._clear_timer
        ):
            await self._clear_result()

    async def async_call_method(self, method, **kwargs):
        self._search_moment = time.perf_counter()
        args = ", ".join(f"{key}={value}" for key, value in kwargs.items())
        _LOGGER.debug("calling method %s with arguments %s", method, args)
        self._meta[0]["method"] = method
        self._meta[0]["args"] = args

        if method == METHOD_SEARCH:
            item = kwargs.get("item")
            media_type = item.get("media_type")
            search_value = item.get("value")
            if media_type == SEARCH_MEDIA_TYPE_ALL:
                await self.search(search_value)
            elif media_type == SEARCH_MEDIA_TYPE_RECENT:
                await self.search_recent()
            elif media_type == SEARCH_MEDIA_TYPE_ARTIST:
                await self.search_artist(search_value)
            elif media_type == SEARCH_MEDIA_TYPE_TVSHOW:
                await self.search_tvshow_detail(search_value)
            else:
                raise ValueError("The given media type is unsupported: " + media_type)

            self.init_meta("search method called")
            if media_type == SEARCH_MEDIA_TYPE_RECENT or search_value is not None:
                self.add_meta("search", "true")
            self.schedule_update_ha_state()

        elif method == METHOD_CLEAR:
            await self._clear_result()
            self.schedule_update_ha_state()
        elif method == METHOD_PLAY:
            if kwargs.get("songid") is not None:
                await self.play_song(kwargs.get(PLAY_ATTR_SONGID))
            if kwargs.get("albumid") is not None:
                await self.play_album(kwargs.get(PLAY_ATTR_ALBUMID))
            if kwargs.get("movieid") is not None:
                await self.play_movie(kwargs.get(PLAY_ATTR_MOVIEID))
            if kwargs.get("episodeid") is not None:
                await self.play_episode(kwargs.get(PLAY_ATTR_EPISODEID))

        else:
            raise ValueError("The given method is unsupported: " + method)

    async def _clear_result(self):
        self._search_moment = 0
        self.init_meta("clear results event")
        self.purge_data("clear results event")
        _LOGGER.debug("Kodi search result clearded")

    def _clear_all_data(self, event_id):
        self.purge_meta(event_id)
        self.purge_data(event_id)
        _LOGGER.debug("Kodi search result clearded")

    async def play_item(self, playlistid, item_name, item_value):
        _LOGGER.debug(item_value)
        if not isinstance(item_value, (list, tuple)):
            insertable = [item_value]
            item_value = insertable

        idx = 1
        for item in item_value:
            await self.call_method_kodi_no_result(
                "Playlist.Insert",
                {
                    "playlistid": playlistid,
                    "position": idx,
                    "item": {item_name: item},
                },
            )
            idx = idx + 1

        await self.call_method_kodi_no_result(
            "Player.Open",
            {"item": {"playlistid": playlistid, "position": 1}},
        )

    async def play_song(self, songid):
        await self.play_item(0, "songid", songid)

    async def play_album(self, albumid):
        await self.play_item(0, "albumid", albumid)

    async def play_movie(self, movieid):
        await self.play_item(1, "movieid", movieid)

    async def play_episode(self, episodeid):
        await self.play_item(1, "episodeid", episodeid)

    async def search_tvshow_detail(self, tvshowid):
        card_json = []
        self._data.clear

        if tvshowid is None or tvshowid == "":
            _LOGGER.warning("The argument 'value' passed is empty")
            return
        try:
            season_resultset = await self.kodi_search_tvshow_seasons(tvshowid)
            season_data: List[Dict[str, Any]] = list()

            if season_resultset is not None and len(season_resultset) > 0:
                for tvshow_season in season_resultset:
                    season_number = tvshow_season["season"]

                    episodes_resultset = await self.kodi_search_episodes_by_season(
                        tvshowid, season_number
                    )

                    tvshow_season["type"] = MEDIA_TYPE_SEASON_DETAIL
                    tvshow_season["episodes"] = episodes_resultset

                    season_data.append(tvshow_season)
            self._add_result(season_data, card_json)

            self._state = STATE_ON
        except Exception:
            _LOGGER.exception("Error updating sensor, is kodi running?")
            self._state = STATE_OFF

        self._data = card_json

    async def search_artist(self, value):
        if value is None or value == "":
            _LOGGER.warning("The argument 'value' passed is empty")
            return
        try:
            songs_resultset = await self.kodi_search_songs(value, True, "artistid")

        except Exception:
            _LOGGER.exception("Error updating sensor, is kodi running?")

        if songs_resultset is not None and len(songs_resultset) > 0:
            album_id_set = set()
            albums_data: List[Dict[str, Any]] = list()
            songs_data = list(
                filter(
                    lambda d: d["albumid"] is None or d["albumid"] == "",
                    songs_resultset,
                )
            )

            for song in songs_resultset:
                if song["albumid"] is not None and song["albumid"] != "":
                    album_id_set.add(song["albumid"])

            for album_id in album_id_set:
                _LOGGER.debug("start album id %s", album_id)
                album_resultset = await self.kodi_search_albumdetails(album_id)

                album_songs = list(
                    filter(lambda d: d["albumid"] == album_id, songs_resultset)
                )

                if album_resultset["label"] is None:
                    _LOGGER.exception("????????????? %s", album_id)

                album_resultset["albumid"] = album_id
                album_resultset["songs"] = album_songs

                albums_data.append(album_resultset)
                _LOGGER.debug("ok for album id %s", album_id)

            card_json = []
            self._add_result(songs_data, card_json)
            self._add_result(albums_data, card_json)

            self._data.clear
            self._data = card_json

    async def kodi_search_albumdetails(self, value):
        return await self.call_method_kodi(
            "AudioLibrary.GetAlbumDetails",
            {
                "properties": PROPS_ALBUM_DETAIL,
                "albumid": value,
            },
        )

    async def kodi_search_songs(
        self, value, unlimited: bool = False, filter_field: str = "title"
    ):
        _limits = {"start": 0}
        if not unlimited:
            _limits["end"] = self._search_limit

        _filter = {}
        if filter_field == "title":
            _filter["field"] = "title"
            _filter["operator"] = "contains"
            _filter["value"] = value
        elif filter_field == "artistid":
            _filter["artistid"] = value

        return await self.call_method_kodi(
            "AudioLibrary.GetSongs",
            {
                "properties": PROPS_SONG,
                "limits": _limits,
                "sort": {
                    "method": "track",
                    "order": "ascending",
                    "ignorearticle": True,
                },
                "filter": _filter,
            },
        )

    async def kodi_search_episodes_by_season(self, tvshowid, season_number):
        _limits = {"start": 0}

        return await self.call_method_kodi(
            "VideoLibrary.GetEpisodes",
            {
                "properties": PROPS_EPISODE,
                "limits": _limits,
                "sort": {
                    "method": "episode",
                    "order": "ascending",
                    "ignorearticle": True,
                },
                "tvshowid": tvshowid,
                "season": season_number,
            },
        )

    async def kodi_search_tvshow_seasons(self, value):
        _limits = {"start": 0}

        return await self.call_method_kodi(
            "VideoLibrary.GetSeasons",
            {
                "properties": PROPS_SEASON,
                "limits": _limits,
                "sort": {
                    "method": "season",
                    "order": "ascending",
                    "ignorearticle": True,
                },
                "tvshowid": value,
            },
        )

    async def kodi_search_albums(self, value, unlimited: bool = False):
        limits = {"start": 0}
        if not unlimited:
            limits["end"] = self._search_limit
        return await self.call_method_kodi(
            "AudioLibrary.GetAlbums",
            {
                "properties": PROPS_ALBUM,
                "limits": limits,
                "sort": {
                    "method": "title",
                    "order": "ascending",
                    "ignorearticle": True,
                },
                "filter": {
                    "field": "album",
                    "operator": "contains",
                    "value": value,
                },
            },
        )

    async def kodi_search_recent_albums(self, unlimited: bool = False):
        limits = {"start": 0}
        if not unlimited:
            limits["end"] = self._search_limit
        return await self.call_method_kodi(
            "AudioLibrary.GetRecentlyAddedAlbums",
            {
                "properties": PROPS_ALBUM,
                "limits": limits,
            },
        )

    async def kodi_search_recent_songs(self, unlimited: bool = False):
        limits = {"start": 0}
        if not unlimited:
            limits["end"] = self._search_limit
        return await self.call_method_kodi(
            "AudioLibrary.GetRecentlyAddedSongs",
            {
                "properties": PROPS_SONG,
                "limits": limits,
            },
        )

    async def kodi_search_recent_movies(self, unlimited: bool = False):
        limits = {"start": 0}
        if not unlimited:
            limits["end"] = self._search_limit
        return await self.call_method_kodi(
            "VideoLibrary.GetRecentlyAddedMovies",
            {
                "properties": PROPS_MOVIE,
                "limits": limits,
            },
        )

    async def kodi_search_recent_episodes(self, unlimited: bool = False):
        limits = {"start": 0}
        if not unlimited:
            limits["end"] = self._search_limit
        result = await self.call_method_kodi(
            "VideoLibrary.GetRecentlyAddedEpisodes",
            {
                "properties": PROPS_RECENT_EPISODES,
                "limits": limits,
            },
        )
        for episode in result:
            tvshow = await self.kodi_search_tvshow_details(episode["tvshowid"])
            episode["tvshowtitle"] = tvshow["title"]
            episode["genre"] = tvshow["genre"]
        return result

    async def kodi_search_artists(self, value, unlimited: bool = False):
        limits = {"start": 0}
        if not unlimited:
            limits["end"] = self._search_limit
        return await self.call_method_kodi(
            "AudioLibrary.GetArtists",
            {
                "properties": PROPS_ARTIST,
                "limits": limits,
                "sort": {
                    "method": "title",
                    "order": "ascending",
                    "ignorearticle": True,
                },
                "filter": {
                    "field": "artist",
                    "operator": "contains",
                    "value": value,
                },
            },
        )

    async def kodi_search_movies(self, value, unlimited: bool = False):
        limits = {"start": 0}
        if not unlimited:
            limits["end"] = self._search_limit
        return await self.call_method_kodi(
            "VideoLibrary.GetMovies",
            {
                "properties": PROPS_MOVIE,
                "limits": limits,
                "sort": {
                    "method": "title",
                    "order": "ascending",
                    "ignorearticle": True,
                },
                "filter": {
                    "field": "title",
                    "operator": "contains",
                    "value": value,
                },
            },
        )

    async def kodi_search_tvshows(self, value, unlimited: bool = False):
        limits = {"start": 0}
        if not unlimited:
            limits["end"] = self._search_limit
        return await self.call_method_kodi(
            "VideoLibrary.GetTVShows",
            {
                "properties": PROPS_TVSHOW,
                "limits": limits,
                "sort": {
                    "method": "title",
                    "order": "ascending",
                },
                "filter": {
                    "field": "title",
                    "operator": "contains",
                    "value": value,
                },
            },
        )

    async def kodi_search_episodes(self, value, unlimited: bool = False):
        limits = {"start": 0}
        if not unlimited:
            limits["end"] = self._search_limit
        result = await self.call_method_kodi(
            "VideoLibrary.GetEpisodes",
            {
                "properties": PROPS_EPISODE,
                "limits": limits,
                "sort": {
                    "method": "title",
                    "order": "ascending",
                },
                "filter": {
                    "field": "title",
                    "operator": "contains",
                    "value": value,
                },
            },
        )
        for episode in result:
            tvshow = await self.kodi_search_tvshow_details(episode["tvshowid"])
            episode["tvshowtitle"] = tvshow["title"]
            episode["genre"] = tvshow["genre"]
        return result

    async def kodi_search_tvshow_details(self, tvshowid):
        return await self.call_method_kodi(
            "VideoLibrary.GetTVShowDetails",
            {"properties": PROPS_TVSHOW, "tvshowid": tvshowid},
        )

    async def search_recent(self):
        _LOGGER.debug("Searching recents")
        try:
            songs = await self.kodi_search_recent_songs()
            albums = await self.kodi_search_recent_albums()
            movies = await self.kodi_search_recent_movies()
            episodes = await self.kodi_search_recent_episodes()
        except Exception:
            _LOGGER.exception("Error updating sensor, is kodi running?")

        card_json = []
        self._add_result(songs, card_json)
        self._add_result(albums, card_json)
        self._add_result(movies, card_json)
        self._add_result(episodes, card_json)

        self._data.clear
        self._data = card_json

    async def search(self, value):
        if value is None or value == "":
            _LOGGER.warning("The argument 'value' passed is empty")
            return

        _LOGGER.debug("Searching for '%s'", value)

        try:
            songs = await self.kodi_search_songs(value)
            albums = await self.kodi_search_albums(value)
            artists = await self.kodi_search_artists(value)
            movies = await self.kodi_search_movies(value)
            tvshows = await self.kodi_search_tvshows(value)
            episodes = await self.kodi_search_episodes(value)

        except Exception:
            _LOGGER.exception("Error updating sensor, is kodi running?")
            # self._state = STATE_OFF

        card_json = []
        self._add_result(songs, card_json)
        self._add_result(albums, card_json)
        self._add_result(artists, card_json)
        self._add_result(movies, card_json)
        self._add_result(tvshows, card_json)
        self._add_result(episodes, card_json)

        self._data.clear
        self._data = card_json
        # self._state = STATE_ON

    def _add_result(self, data, target):
        if data is not None and len(data) > 0:
            for row in data:
                target.append(row)
