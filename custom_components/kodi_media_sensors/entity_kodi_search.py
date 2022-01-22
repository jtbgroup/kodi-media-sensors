import logging
from config.custom_components.kodi_media_sensors.media_sensor_event_manager import (
    MediaSensorEventManager,
)
import homeassistant
import time
from typing import Dict, List, Any
from .entity_kodi_media_sensor import KodiMediaSensorEntity
from homeassistant.const import STATE_OFF, STATE_ON
from pykodi import Kodi
from .const import (
    DEFAULT_OPTION_SEARCH_ALBUMS,
    DEFAULT_OPTION_SEARCH_ALBUMS_LIMIT,
    DEFAULT_OPTION_SEARCH_ARTISTS,
    DEFAULT_OPTION_SEARCH_ARTISTS_LIMIT,
    DEFAULT_OPTION_SEARCH_CHANNELS_RADIO,
    DEFAULT_OPTION_SEARCH_CHANNELS_RADIO_LIMIT,
    DEFAULT_OPTION_SEARCH_CHANNELS_TV,
    DEFAULT_OPTION_SEARCH_CHANNELS_TV_LIMIT,
    DEFAULT_OPTION_SEARCH_MOVIES,
    DEFAULT_OPTION_SEARCH_MOVIES_LIMIT,
    DEFAULT_OPTION_SEARCH_RECENT_LIMIT,
    DEFAULT_OPTION_SEARCH_SONGS,
    DEFAULT_OPTION_SEARCH_SONGS_LIMIT,
    DEFAULT_OPTION_SEARCH_TVSHOWS,
    DEFAULT_OPTION_SEARCH_TVSHOWS_LIMIT,
    DEFAULT_OPTION_SEARCH_EPISODES,
    DEFAULT_OPTION_SEARCH_EPISODES_LIMIT,
    DEFAULT_OPTION_SEARCH_RECENT_SONGS,
    DEFAULT_OPTION_SEARCH_RECENT_ALBUMS,
    DEFAULT_OPTION_SEARCH_RECENT_MOVIES,
    DEFAULT_OPTION_SEARCH_RECENT_EPISODES,
    DEFAULT_OPTION_SEARCH_KEEP_ALIVE_TIMER,
    DOMAIN,
    ENTITY_SENSOR_SEARCH,
    ENTITY_NAME_SENSOR_SEARCH,
    MEDIA_TYPE_SEASON_DETAIL,
    PROPS_SEASON,
    PROPS_RECENT_EPISODES,
    PROPS_ALBUM,
    PROPS_ALBUM_DETAIL,
    PROPS_ARTIST,
    PROPS_EPISODE,
    PROPS_MOVIE,
    PROPS_SONG,
    PROPS_TVSHOW,
    PROPS_ADDONS,
    PROPS_CHANNEL,
    PLAYLIST_MOVIE,
    PLAYLIST_MUSIC,
)
from .types import KodiConfig

_LOGGER = logging.getLogger(__name__)
ACTION_DO_NOTHING = "nothing"
ACTION_CLEAR = "clear"
ACTION_REFRESH_META = "refresh_meta"

METHOD_SEARCH = "search"
METHOD_CLEAR = "clear"
METHOD_PLAY = "play"
METHOD_ADD = "add"
METHOD_RESET_ADDONS = "reset_addons"
SEARCH_MEDIA_TYPE_ALL = "all"
SEARCH_MEDIA_TYPE_RECENT = "recent"
SEARCH_MEDIA_TYPE_ARTIST = "artist"
SEARCH_MEDIA_TYPE_TVSHOW = "tvshow"
PLAY_ATTR_SONGID = "songid"
PLAY_ATTR_ALBUMID = "albumid"
PLAY_ATTR_MOVIEID = "movieid"
PLAY_ATTR_EPISODEID = "episodeid"
PLAY_ATTR_CHANNELID = "channelid"
ADD_ATTR_POSITION = "position"

PLAY_POSN = 0


class KodiSearchEntity(KodiMediaSensorEntity):
    """This sensor is dedicated to the search functionality of Kodi"""

    _search_start_time = 0
    addons_initialized = False
    can_search_pvr = False
    _search_songs = DEFAULT_OPTION_SEARCH_SONGS
    _search_songs_limit = DEFAULT_OPTION_SEARCH_SONGS_LIMIT
    _search_albums = DEFAULT_OPTION_SEARCH_ALBUMS
    _search_albums_limit = DEFAULT_OPTION_SEARCH_ALBUMS_LIMIT
    _search_artists = DEFAULT_OPTION_SEARCH_ARTISTS
    _search_artists_limit = DEFAULT_OPTION_SEARCH_ARTISTS_LIMIT
    _search_movies = DEFAULT_OPTION_SEARCH_MOVIES
    _search_movies_limit = DEFAULT_OPTION_SEARCH_MOVIES_LIMIT
    _search_tvshows = DEFAULT_OPTION_SEARCH_TVSHOWS
    _search_tvshows_limit = DEFAULT_OPTION_SEARCH_TVSHOWS_LIMIT
    _search_channels_tv = DEFAULT_OPTION_SEARCH_CHANNELS_TV
    _search_channels_tv_limit = DEFAULT_OPTION_SEARCH_CHANNELS_TV_LIMIT
    _search_channels_radio = DEFAULT_OPTION_SEARCH_CHANNELS_RADIO
    _search_channels_radio_limit = DEFAULT_OPTION_SEARCH_CHANNELS_RADIO_LIMIT
    _search_episodes = DEFAULT_OPTION_SEARCH_EPISODES
    _search_episodes_limit = DEFAULT_OPTION_SEARCH_EPISODES_LIMIT
    _search_recent_limit = DEFAULT_OPTION_SEARCH_RECENT_LIMIT
    _search_recent_songs = DEFAULT_OPTION_SEARCH_RECENT_SONGS
    _search_recent_albums = DEFAULT_OPTION_SEARCH_RECENT_ALBUMS
    _search_recent_movies = DEFAULT_OPTION_SEARCH_RECENT_MOVIES
    _search_recent_episodes = DEFAULT_OPTION_SEARCH_RECENT_EPISODES
    _search_keep_alive_timer = DEFAULT_OPTION_SEARCH_KEEP_ALIVE_TIMER

    def __init__(
        self,
        hass,
        kodi: Kodi,
        kodi_entity_id,
        config: KodiConfig,
        event_manager: MediaSensorEventManager,
    ):
        super().__init__(hass, kodi, config, event_manager)

        homeassistant.helpers.event.async_track_state_change_event(
            self._hass, kodi_entity_id, self.__handle_kodi_state_event
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

    def set_search_songs(self, search_songs: bool):
        self._search_songs = search_songs

    def set_search_songs_limit(self, search_songs_limits: int):
        self._search_songs_limit = search_songs_limits

    def set_search_albums(self, value: bool):
        self._search_albums = value

    def set_search_albums_limit(self, limit: int):
        self._search_albums_limit = limit

    def set_search_artists(self, value: bool):
        self._search_artists = value

    def set_search_artists_limit(self, limit: int):
        self._search_artists_limit = limit

    def set_search_movies(self, value: bool):
        self._search_movies = value

    def set_search_movies_limit(self, limit: int):
        self._search_movies_limit = limit

    def set_search_tvshows(self, value: bool):
        self._search_tvshows = value

    def set_search_tvshows_limit(self, limit: int):
        self._search_tvshows_limit = limit

    def set_search_channels_tv(self, value: bool):
        self._search_channels_tv = value

    def set_search_channels_tv_limit(self, limit: int):
        self._search_channels_tv_limit = limit

    def set_search_channels_radio(self, value: bool):
        self._search_channels_radio = value

    def set_search_channels_radio_limit(self, limit: int):
        self._search_channels_radio_limit = limit

    def set_search_episodes(self, value: bool):
        self._search_episodes = value

    def set_search_episodes_limit(self, limit: int):
        self._search_episodes_limit = limit

    def set_search_recent_limit(self, limit: int):
        self._search_recent_limit = limit

    def set_search_recent_songs(self, value: bool):
        self._search_recent_songs = value

    def set_search_recent_albums(self, value: bool):
        self._search_recent_albums = value

    def set_search_recent_movies(self, value: bool):
        self._search_recent_movies = value

    def set_search_recent_episodes(self, value: bool):
        self._search_recent_episodes = value

    def set_search_keep_alive_timer(self, value: bool):
        self._search_keep_alive_timer = value

    async def __handle_kodi_state_event(self, event):
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
            self._search_keep_alive_timer == 0
            and "method" in self._meta[0]
            and self._meta[0]["method"] == METHOD_SEARCH
        ):
            method = self._meta[0]["method"]
            kwargs = self._meta[0]["kwargs"]
            _LOGGER.debug(
                "Search result must be reprocessed. The query is reprocessed."
            )
            await self.async_call_method(method, **kwargs)
        elif (
            self._search_start_time > 0
            and (time.perf_counter() - self._search_start_time)
            > self._search_keep_alive_timer
        ):
            await self._clear_result()

    async def async_call_method(self, method, **kwargs):
        self._search_start_time = time.perf_counter()
        args = ", ".join(f"{key}={value}" for key, value in kwargs.items())
        _LOGGER.debug("calling method %s with arguments %s", method, args)

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
        elif method == METHOD_RESET_ADDONS:
            await self._reset_addons()
        elif method == METHOD_PLAY:
            if kwargs.get("songid") is not None:
                await self.play_song(kwargs.get(PLAY_ATTR_SONGID))
            if kwargs.get("albumid") is not None:
                await self.play_album(kwargs.get(PLAY_ATTR_ALBUMID))
            if kwargs.get("movieid") is not None:
                await self.play_movie(kwargs.get(PLAY_ATTR_MOVIEID))
            if kwargs.get("episodeid") is not None:
                await self.play_episode(kwargs.get(PLAY_ATTR_EPISODEID))
            if kwargs.get("channelid") is not None:
                await self.play_channel(kwargs.get(PLAY_ATTR_CHANNELID))
        elif method == METHOD_ADD:
            position = 1
            if kwargs.get(ADD_ATTR_POSITION) is not None:
                position = int(kwargs.get(ADD_ATTR_POSITION))
            if kwargs.get("songid") is not None:
                await self.add_song(kwargs.get(PLAY_ATTR_SONGID), position)
            if kwargs.get("albumid") is not None:
                await self.add_album(kwargs.get(PLAY_ATTR_ALBUMID), position)
            if kwargs.get("movieid") is not None:
                await self.add_movie(kwargs.get(PLAY_ATTR_MOVIEID), position)
            if kwargs.get("episodeid") is not None:
                await self.add_episode(kwargs.get(PLAY_ATTR_EPISODEID), position)
            if kwargs.get("channelid") is not None:
                await self.add_channel(kwargs.get(PLAY_ATTR_CHANNELID), position)
        else:
            raise ValueError("The given method is unsupported: " + method)

        self._meta[0]["method"] = method
        self._meta[0]["kwargs"] = kwargs

    async def _reset_addons(self):
        self.addons_initialized = False
        await self.init_addons()

    async def _clear_result(self):
        self._search_start_time = 0
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

        players = await self._kodi.get_players()
        current_posn = -1
        if len(players) == 1:
            player = players[0]
            props_item_playing = await self._kodi.get_playing_item_properties(
                player, []
            )
            current_item_id = props_item_playing.get("id")

            playlistid = player.get("playerid")
            playlist = await self.call_method_kodi(
                "Playlist.GetItems",
                {
                    "playlistid": playlistid,
                },
            )

            posn = 0
            for item in playlist:
                if item.get("id") == current_item_id:
                    current_posn = posn
                    break
                else:
                    posn = posn + 1

        idx = current_posn + 1 if current_posn > -1 else PLAY_POSN
        rolling_idx = idx
        for item in item_value:
            await self.call_method_kodi_no_result(
                "Playlist.Insert",
                {
                    "playlistid": playlistid,
                    "position": rolling_idx,
                    "item": {item_name: item},
                },
            )
            rolling_idx = rolling_idx + 1

        await self.call_method_kodi_no_result(
            "Player.Open",
            {"item": {"playlistid": playlistid, "position": idx}},
        )

    async def play_song(self, songid):
        await self.play_item(PLAYLIST_MUSIC, "songid", songid)

    async def play_album(self, albumid):
        await self.play_item(PLAYLIST_MUSIC, "albumid", albumid)

    async def play_movie(self, movieid):
        await self.play_item(PLAYLIST_MOVIE, "movieid", movieid)

    async def play_channel(self, channelid):
        await self.call_method_kodi_no_result(
            "Player.Open",
            {"item": {"channelid": channelid}},
        )

    async def play_episode(self, episodeid):
        await self.play_item(PLAYLIST_MOVIE, "episodeid", episodeid)

    async def add_item(self, playlistid, item_name, item_value, position):
        _LOGGER.debug(item_value)
        if not isinstance(item_value, (list, tuple)):
            insertable = [item_value]
            item_value = insertable

        idx = position
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
            _LOGGER.debug("added song id %s in position %s", item, idx)
            event_data = {
                "type": "playlist_item_added",
            }
            self._hass.bus.async_fire(DOMAIN, event_data)

    async def add_song(self, songid, position):
        if position > -1:
            await self.add_item(PLAYLIST_MUSIC, "songid", songid, position)
            await self._event_manager.notify_event(self, "item_added")
        else:
            raise Exception("Position can't be < -1")

    async def add_album(self, albumid, position):
        if position > -1:
            await self.add_item(PLAYLIST_MUSIC, "albumid", albumid, position)
            await self._event_manager.notify_event(self, "item_added")
        else:
            raise Exception("Position can't be < -1")

    async def add_movie(self, movieid, position):
        if position > -1:
            await self.add_item(PLAYLIST_MOVIE, "movieid", movieid, position)
            await self._event_manager.notify_event(self, "item_added")
        else:
            raise Exception("Position can't be < -1")

    async def add_channel(self, channelid, position):
        if position > -1:
            await self.add_item(PLAYLIST_MOVIE, "channelid", channelid, position)
            await self._event_manager.notify_event(self, "item_added")
        else:
            raise Exception("Position can't be < -1")

    async def add_episode(self, episodeid, position):
        if position > -1:
            await self.add_item(PLAYLIST_MOVIE, "episodeid", episodeid, position)
            await self._event_manager.notify_event(self, "item_added")
        else:
            raise Exception("Position can't be < -1")

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
        limits = {"start": 0}
        if not unlimited or self._search_songs_limit == 0:
            limits["end"] = self._search_songs_limit

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
                "limits": limits,
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
        if not unlimited or self._search_albums_limit == 0:
            limits["end"] = self._search_albums_limit
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
        if not unlimited or self._search_recent_limit == 0:
            limits["end"] = self._search_recent_limit
        return await self.call_method_kodi(
            "AudioLibrary.GetRecentlyAddedAlbums",
            {
                "properties": PROPS_ALBUM,
                "limits": limits,
            },
        )

    async def kodi_search_recent_songs(self, unlimited: bool = False):
        limits = {"start": 0}
        if not unlimited or self._search_recent_limit == 0:
            limits["end"] = self._search_recent_limit
        return await self.call_method_kodi(
            "AudioLibrary.GetRecentlyAddedSongs",
            {
                "properties": PROPS_SONG,
                "limits": limits,
            },
        )

    async def kodi_search_recent_movies(self, unlimited: bool = False):
        limits = {"start": 0}
        if not unlimited or self._search_recent_limit == 0:
            limits["end"] = self._search_recent_limit
        return await self.call_method_kodi(
            "VideoLibrary.GetRecentlyAddedMovies",
            {
                "properties": PROPS_MOVIE,
                "limits": limits,
            },
        )

    async def kodi_search_recent_episodes(self, unlimited: bool = False):
        limits = {"start": 0}
        if not unlimited or self._search_recent_limit == 0:
            limits["end"] = self._search_recent_limit
        result = await self.call_method_kodi(
            "VideoLibrary.GetRecentlyAddedEpisodes",
            {
                "properties": PROPS_RECENT_EPISODES,
                "limits": limits,
            },
        )
        if result is not None:
            for episode in result:
                tvshow = await self.kodi_search_tvshow_details(episode["tvshowid"])
                episode["tvshowtitle"] = tvshow["title"]
                episode["genre"] = tvshow["genre"]
        return result

    async def kodi_search_artists(self, value, unlimited: bool = False):
        limits = {"start": 0}
        if not unlimited or self._search_artists_limit == 0:
            limits["end"] = self._search_artists_limit
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
        if not unlimited or self._search_movies_limit == 0:
            limits["end"] = self._search_movies_limit
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
        if not unlimited or self._search_tvshows_limit == 0:
            limits["end"] = self._search_tvshows_limit
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

    async def kodi_search_channels_tv(self, value, unlimited: bool = False):
        result_tv = await self.call_method_kodi(
            "PVR.GetChannels",
            {
                "properties": PROPS_CHANNEL,
                "channelgroupid": "alltv",
            },
        )

        filtered_result = []

        if not result_tv is None:
            sub_result = list(
                filter(
                    lambda d: value.lower() in d["label"].lower(),
                    result_tv,
                )
            )
            if not unlimited or self._search_channels_tv_limit == 0:
                idx = 0
                for value in sub_result:
                    filtered_result.append(value)
                    if idx < self._search_channels_tv_limit - 1:
                        idx += 1
                    else:
                        break
            else:
                filtered_result.extend(sub_result)

        return filtered_result

    async def kodi_search_channels_radio(self, value, unlimited: bool = False):
        result_radio = await self.call_method_kodi(
            "PVR.GetChannels",
            {
                "properties": PROPS_CHANNEL,
                "channelgroupid": "allradio",
            },
        )

        filtered_result = []

        if not result_radio is None:
            sub_result = list(
                filter(
                    lambda d: value.lower() in d["label"].lower(),
                    result_radio,
                )
            )
            idx = 0
            for value in sub_result:
                filtered_result.append(value)
                if idx < self._search_channels_radio_limit - 1:
                    idx += 1
                else:
                    break

        return filtered_result

    async def kodi_search_episodes(self, value, unlimited: bool = False):
        limits = {"start": 0}
        if not unlimited or self._search_episodes_limit == 0:
            limits["end"] = self._search_episodes_limit
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
        if result is not None:
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
        card_json = []
        if self._search_recent_songs is True:
            songs = await self.kodi_search_recent_songs()
            self._add_result(songs, card_json)

        if self._search_recent_albums is True:
            albums = await self.kodi_search_recent_albums()
            self._add_result(albums, card_json)

        if self._search_recent_movies is True:
            movies = await self.kodi_search_recent_movies()
            self._add_result(movies, card_json)

        if self._search_recent_episodes is True:
            episodes = await self.kodi_search_recent_episodes()
            self._add_result(episodes, card_json)

        self._data.clear
        self._data = card_json

    async def search(self, value):
        # Initialize the addons during the first search
        if not self.addons_initialized:
            await self.init_addons()

        if value is None or value == "":
            _LOGGER.warning("The argument 'value' passed is empty")
            return

        _LOGGER.debug("Searching for '%s'", value)

        card_json = []
        if self._search_songs is True:
            songs = await self.kodi_search_songs(value)
            self._add_result(songs, card_json)

        if self._search_albums is True:
            albums = await self.kodi_search_albums(value)
            self._add_result(albums, card_json)

        if self._search_artists is True:
            artists = await self.kodi_search_artists(value)
            self._add_result(artists, card_json)

        if self._search_movies is True:
            movies = await self.kodi_search_movies(value)
            self._add_result(movies, card_json)

        if self._search_tvshows is True:
            tvshows = await self.kodi_search_tvshows(value)
            self._add_result(tvshows, card_json)

        if self._search_episodes is True:
            episodes = await self.kodi_search_episodes(value)
            self._add_result(episodes, card_json)

        if self.can_search_pvr and self._search_channels_tv is True:
            channels = await self.kodi_search_channels_tv(value)
            self._add_result(channels, card_json)

        if self.can_search_pvr and self._search_channels_radio is True:
            channels = await self.kodi_search_channels_radio(value)
            self._add_result(channels, card_json)

        self._data.clear
        self._data = card_json

    async def init_addons(self):
        addons = await self.call_method_kodi(
            "Addons.GetAddons", {"type": "kodi.pvrclient", "properties": PROPS_ADDONS}
        )

        self.addons_initialized = True

        pvr_addons = list(
            filter(
                lambda d: d["enabled"] is True,
                addons,
            )
        )

        if len(pvr_addons) > 0:
            _LOGGER.info(
                "PVR Addons found. The search will be done on PVR channels too"
            )
            self.can_search_pvr = True
        else:
            self.can_search_pvr = False
            _LOGGER.info(
                "No PVR Addon found. The search sensor will not search results in the PVR channels"
            )

    def _add_result(self, data, target):
        if data is not None and len(data) > 0:
            for row in data:
                target.append(row)

    async def handle_media_sensor_event(self, event):
        return
