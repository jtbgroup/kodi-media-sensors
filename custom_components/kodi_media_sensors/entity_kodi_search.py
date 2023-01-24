import logging
import time
from typing import Any

import homeassistant
from homeassistant.const import STATE_OFF, STATE_ON
from pykodi import Kodi

from .const import (
    DEFAULT_OPTION_SEARCH_ALBUMS_LIMIT,
    DEFAULT_OPTION_SEARCH_ARTISTS_LIMIT,
    DEFAULT_OPTION_SEARCH_CHANNELS_RADIO_LIMIT,
    DEFAULT_OPTION_SEARCH_CHANNELS_TV_LIMIT,
    DEFAULT_OPTION_SEARCH_EPISODES_LIMIT,
    DEFAULT_OPTION_SEARCH_KEEP_ALIVE_TIMER,
    DEFAULT_OPTION_SEARCH_MOVIES_LIMIT,
    DEFAULT_OPTION_SEARCH_MUSICVIDEOS_LIMIT,
    DEFAULT_OPTION_SEARCH_RECENTLY_ADDED_ALBUMS_LIMIT,
    DEFAULT_OPTION_SEARCH_RECENTLY_ADDED_EPISODES_LIMIT,
    DEFAULT_OPTION_SEARCH_RECENTLY_ADDED_MOVIES_LIMIT,
    DEFAULT_OPTION_SEARCH_RECENTLY_ADDED_MUSICVIDEOS_LIMIT,
    DEFAULT_OPTION_SEARCH_RECENTLY_ADDED_SONGS_LIMIT,
    DEFAULT_OPTION_SEARCH_RECENTLY_PLAYED_ALBUMS_LIMIT,
    DEFAULT_OPTION_SEARCH_RECENTLY_PLAYED_SONGS_LIMIT,
    DEFAULT_OPTION_SEARCH_SONGS_LIMIT,
    DEFAULT_OPTION_SEARCH_TVSHOWS_LIMIT,
    ENTITY_NAME_SENSOR_SEARCH,
    ENTITY_SENSOR_SEARCH,
    MAX_KEEP_ALIVE,
    MAX_SEARCH_LIMIT,
    MEDIA_TYPE_SEASON_DETAIL,
    PLAYLIST_ID_MUSIC,
    PLAYLIST_ID_VIDEO,
    PLAYLIST_MAP,
    PROPS_ADDONS,
    PROPS_ALBUM,
    PROPS_ALBUM_DETAIL,
    PROPS_ARTIST,
    PROPS_CHANNEL,
    PROPS_EPISODE,
    PROPS_MOVIE,
    PROPS_MUSICVIDEOS,
    PROPS_RECENT_EPISODES,
    PROPS_SEASON,
    PROPS_SONG,
    PROPS_TVSHOW,
)
from .entity_kodi_media_sensor import KodiMediaSensorEntity
from .media_sensor_event_manager import MediaSensorEventManager
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
SEARCH_MEDIA_TYPE_RECENTLY_ADDED = "recently_added"
SEARCH_MEDIA_TYPE_RECENTLY_PLAYED = "recently_played"
SEARCH_MEDIA_TYPE_ARTIST = "artist"
SEARCH_MEDIA_TYPE_TVSHOW = "tvshow"
PLAY_ATTR_SONGID = "songid"
PLAY_ATTR_ALBUMID = "albumid"
PLAY_ATTR_MOVIEID = "movieid"
PLAY_ATTR_MUSICVIDEOID = "musicvideoid"
PLAY_ATTR_EPISODEID = "episodeid"
PLAY_ATTR_CHANNELID = "channelid"

ADD_ATTR_POSITION = "position"
PLAY_POSN = 0


class KodiSearchEntity(KodiMediaSensorEntity):
    """This sensor is dedicated to the search functionality of Kodi"""

    _search_start_time = 0
    addons_initialized = False
    can_search_pvr = False
    _search_songs_limit = DEFAULT_OPTION_SEARCH_SONGS_LIMIT
    _search_albums_limit = DEFAULT_OPTION_SEARCH_ALBUMS_LIMIT
    _search_artists_limit = DEFAULT_OPTION_SEARCH_ARTISTS_LIMIT
    _search_musicvideos_limit = DEFAULT_OPTION_SEARCH_MUSICVIDEOS_LIMIT
    _search_movies_limit = DEFAULT_OPTION_SEARCH_MOVIES_LIMIT
    _search_tvshows_limit = DEFAULT_OPTION_SEARCH_TVSHOWS_LIMIT
    _search_channels_tv_limit = DEFAULT_OPTION_SEARCH_CHANNELS_TV_LIMIT
    _search_channels_radio_limit = DEFAULT_OPTION_SEARCH_CHANNELS_RADIO_LIMIT
    _search_episodes_limit = DEFAULT_OPTION_SEARCH_EPISODES_LIMIT
    _search_recently_added_songs_limit = (
        DEFAULT_OPTION_SEARCH_RECENTLY_ADDED_SONGS_LIMIT
    )
    _search_recently_added_albums_limit = (
        DEFAULT_OPTION_SEARCH_RECENTLY_ADDED_ALBUMS_LIMIT
    )
    _search_recently_added_movies_limit = (
        DEFAULT_OPTION_SEARCH_RECENTLY_ADDED_MOVIES_LIMIT
    )
    _search_recently_added_episodes_limit = (
        DEFAULT_OPTION_SEARCH_RECENTLY_ADDED_EPISODES_LIMIT
    )
    _search_recently_added_musicvideos_limit = (
        DEFAULT_OPTION_SEARCH_RECENTLY_ADDED_MUSICVIDEOS_LIMIT
    )
    _search_recently_played_songs_limit = (
        DEFAULT_OPTION_SEARCH_RECENTLY_PLAYED_SONGS_LIMIT
    )
    _search_recently_played_albums_limit = (
        DEFAULT_OPTION_SEARCH_RECENTLY_PLAYED_ALBUMS_LIMIT
    )
    _search_keep_alive_timer = DEFAULT_OPTION_SEARCH_KEEP_ALIVE_TIMER

    def __init__(
        self,
        hass,
        kodi: Kodi,
        kodi_entity_id,
        config: KodiConfig,
        event_manager: MediaSensorEventManager,
    ):
        super().__init__(kodi, config, event_manager)
        self._hass = hass
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

    def set_search_songs_limit(self, limit: int):
        """Assigns the search limits for the SONGS object. Value provided is enforced between 0 and MAX_SEARCH_LIMIT"""
        value = 0 if limit < 0 else limit
        value = MAX_SEARCH_LIMIT if value > MAX_SEARCH_LIMIT else value
        self._search_songs_limit = value

    def set_search_albums_limit(self, limit: int):
        """Assigns the search limits for the ALBUMS object. Value provided is enforced between 0 and MAX_SEARCH_LIMIT"""
        value = 0 if limit < 0 else limit
        value = MAX_SEARCH_LIMIT if value > MAX_SEARCH_LIMIT else value
        self._search_albums_limit = value

    def set_search_artists_limit(self, limit: int):
        """Assigns the search limits for the ARTISTS object. Value provided is enforced between 0 and MAX_SEARCH_LIMIT"""
        value = 0 if limit < 0 else limit
        value = MAX_SEARCH_LIMIT if value > MAX_SEARCH_LIMIT else value
        self._search_artists_limit = value

    def set_search_movies_limit(self, limit: int):
        """Assigns the search limits for the MOVIES object. Value provided is enforced between 0 and MAX_SEARCH_LIMIT"""
        value = 0 if limit < 0 else limit
        value = MAX_SEARCH_LIMIT if value > MAX_SEARCH_LIMIT else value
        self._search_movies_limit = value

    def set_search_musicvideos_limit(self, limit: int):
        """Assigns the search limits for the MUSIC_VIDEOS object. Value provided is enforced between 0 and MAX_SEARCH_LIMIT"""
        value = 0 if limit < 0 else limit
        value = MAX_SEARCH_LIMIT if value > MAX_SEARCH_LIMIT else value
        self._search_musicvideos_limit = value

    def set_search_tvshows_limit(self, limit: int):
        """Assigns the search limits for the TV_SHOWS object. Value provided is enforced between 0 and MAX_SEARCH_LIMIT"""
        value = 0 if limit < 0 else limit
        value = MAX_SEARCH_LIMIT if value > MAX_SEARCH_LIMIT else value
        self._search_tvshows_limit = value

    def set_search_channels_tv_limit(self, limit: int):
        """Assigns the search limits for the CHANNEL_TV object. Value provided is enforced between 0 and MAX_SEARCH_LIMIT"""
        value = 0 if limit < 0 else limit
        value = MAX_SEARCH_LIMIT if value > MAX_SEARCH_LIMIT else value
        self._search_channels_tv_limit = value

    def set_search_channels_radio_limit(self, limit: int):
        """Assigns the search limits for the CHANNEL_RADIO object. Value provided is enforced between 0 and MAX_SEARCH_LIMIT"""
        value = 0 if limit < 0 else limit
        value = MAX_SEARCH_LIMIT if value > MAX_SEARCH_LIMIT else value
        self._search_channels_radio_limit = value

    def set_search_episodes_limit(self, limit: int):
        """Assigns the search limits for the EPISODES object. Value provided is enforced between 0 and MAX_SEARCH_LIMIT"""
        value = 0 if limit < 0 else limit
        value = MAX_SEARCH_LIMIT if value > MAX_SEARCH_LIMIT else value
        self._search_episodes_limit = value

    def set_search_recently_added_songs_limit(self, limit: int):
        """Assigns the search limits for the SONGS object in the recently added search. Value provided is enforced between 0 and MAX_SEARCH_LIMIT"""
        value = 0 if limit < 0 else limit
        value = MAX_SEARCH_LIMIT if value > MAX_SEARCH_LIMIT else value
        self._search_recently_added_songs_limit = value

    def set_search_recently_added_albums_limit(self, limit: int):
        """Assigns the search limits for the ALBUMS object in the recently added search. Value provided is enforced between 0 and MAX_SEARCH_LIMIT"""
        value = 0 if limit < 0 else limit
        value = MAX_SEARCH_LIMIT if value > MAX_SEARCH_LIMIT else value
        self._search_recently_added_albums_limit = value

    def set_search_recently_added_movies_limit(self, limit: int):
        """Assigns the search limits for the MOVIES object in the recently added search. Value provided is enforced between 0 and MAX_SEARCH_LIMIT"""
        value = 0 if limit < 0 else limit
        value = MAX_SEARCH_LIMIT if value > MAX_SEARCH_LIMIT else value
        self._search_recently_added_movies_limit = value

    def set_search_recently_added_musicvideos_limit(self, limit: int):
        """Assigns the search limits for the MUSIC_VIDEOS object in the recently added search. Value provided is enforced between 0 and MAX_SEARCH_LIMIT"""
        value = 0 if limit < 0 else limit
        value = MAX_SEARCH_LIMIT if value > MAX_SEARCH_LIMIT else value
        self._search_recently_added_musicvideos_limit = value

    def set_search_recently_added_episodes_limit(self, limit: int):
        """Assigns the search limits for the EPISODES object in the recently added search. Value provided is enforced between 0 and MAX_SEARCH_LIMIT"""
        value = 0 if limit < 0 else limit
        value = MAX_SEARCH_LIMIT if value > MAX_SEARCH_LIMIT else value
        self._search_recently_added_episodes_limit = value

    def set_search_recently_played_songs_limit(self, limit: int):
        """Assigns the search limits for the SONGS object in the recently played search. Value provided is enforced between 0 and MAX_SEARCH_LIMIT"""
        value = 0 if limit < 0 else limit
        value = MAX_SEARCH_LIMIT if value > MAX_SEARCH_LIMIT else value
        self._search_recently_played_songs_limit = value

    def set_search_recently_played_albums_limit(self, limit: int):
        """Assigns the search limits for the ALBUMS object in the recently played search. Value provided is enforced between 0 and MAX_SEARCH_LIMIT"""
        value = 0 if limit < 0 else limit
        value = MAX_SEARCH_LIMIT if value > MAX_SEARCH_LIMIT else value
        self._search_recently_played_albums_limit = value

    # def set_search_keep_alive_timer(self, value: bool):
    def set_search_keep_alive_timer(self, timer: int):
        """Assigns the search limits for the ALBUMS object in the recently played search. Value provided is enforced between 0 and MAX_SEARCH_LIMIT. timer is expressed in minutes."""
        value = 0 if timer < 0 else timer
        value = MAX_KEEP_ALIVE if value > MAX_KEEP_ALIVE else value

        self._search_keep_alive_timer = value * 60

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
            self._force_update_state()

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
            elif media_type == SEARCH_MEDIA_TYPE_RECENTLY_ADDED:
                await self.search_recently_added()
            elif media_type == SEARCH_MEDIA_TYPE_RECENTLY_PLAYED:
                await self.search_recently_played()
            elif media_type == SEARCH_MEDIA_TYPE_ARTIST:
                await self.search_artist(search_value)
            elif media_type == SEARCH_MEDIA_TYPE_TVSHOW:
                await self.search_tvshow_detail(search_value)
            else:
                raise ValueError("The given media type is unsupported: " + media_type)

            self.init_meta("search method called")
            if (
                media_type == SEARCH_MEDIA_TYPE_RECENTLY_ADDED
                or media_type == SEARCH_MEDIA_TYPE_RECENTLY_PLAYED
                or search_value is not None
            ):
                self.add_meta("search", "true")
            self._force_update_state()

        elif method == METHOD_CLEAR:
            await self._clear_result()
            self._force_update_state()
        elif method == METHOD_RESET_ADDONS:
            await self._reset_addons()
        elif method == METHOD_PLAY:
            if kwargs.get("songid") is not None:
                await self.play_song(kwargs.get(PLAY_ATTR_SONGID))
            if kwargs.get("albumid") is not None:
                await self.play_album(kwargs.get(PLAY_ATTR_ALBUMID))
            if kwargs.get("movieid") is not None:
                await self.play_movie(kwargs.get(PLAY_ATTR_MOVIEID))
            if kwargs.get("musicvideoid") is not None:
                await self.play_musicvideo(kwargs.get(PLAY_ATTR_MUSICVIDEOID))
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
            if kwargs.get("musicvideoid") is not None:
                await self.add_musicvideo(kwargs.get(PLAY_ATTR_MUSICVIDEOID), position)
            if kwargs.get("episodeid") is not None:
                await self.add_episode(kwargs.get(PLAY_ATTR_EPISODEID), position)
            if kwargs.get("channelid") is not None:
                await self.add_channel(kwargs.get(PLAY_ATTR_CHANNELID), position)
        else:
            raise ValueError("The given method is unsupported: " + method)

        self._meta[0]["method"] = method
        self._meta[0]["kwargs"] = kwargs

    def _force_update_state(self):
        self.hass.async_create_task(self.async_update_ha_state(True))

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

    async def add_item(self, dest_playlistid, item_name, item_value, position):
        _LOGGER.debug(item_value)
        if not isinstance(item_value, (list, tuple)):
            insertable = [item_value]
            item_value = insertable

        idx = position
        for item in item_value:
            await self.call_method_kodi_no_result(
                "Playlist.Insert",
                {
                    "playlistid": dest_playlistid,
                    "position": idx,
                    "item": {item_name: item},
                },
            )
            idx = idx + 1
            _LOGGER.debug("added song id %s in position %s", item, idx)

    async def add_song(self, songid, position):
        if position > -1:
            await self.add_item(PLAYLIST_ID_MUSIC, "songid", songid, position)
            await self._event_manager.notify_event(self, "item_added")
        else:
            raise Exception("Position can't be < -1")

    async def add_album(self, albumid, position):
        if position > -1:
            await self.add_item(PLAYLIST_ID_MUSIC, "albumid", albumid, position)
            await self._event_manager.notify_event(self, "item_added")
        else:
            raise Exception("Position can't be < -1")

    async def add_movie(self, movieid, position):
        if position > -1:
            await self.add_item(PLAYLIST_ID_VIDEO, "movieid", movieid, position)
            await self._event_manager.notify_event(self, "item_added")
        else:
            raise Exception("Position can't be < -1")

    async def add_musicvideo(self, musicvideoid, position):
        if position > -1:
            await self.add_item(
                PLAYLIST_ID_VIDEO, "musicvideoid", musicvideoid, position
            )
            await self._event_manager.notify_event(self, "item_added")
        else:
            raise Exception("Position can't be < -1")

    async def add_channel(self, channelid, position):
        if position > -1:
            await self.add_item(PLAYLIST_ID_VIDEO, "channelid", channelid, position)
            await self._event_manager.notify_event(self, "item_added")
        else:
            raise Exception("Position can't be < -1")

    async def add_episode(self, episodeid, position):
        if position > -1:
            await self.add_item(PLAYLIST_ID_VIDEO, "episodeid", episodeid, position)
            await self._event_manager.notify_event(self, "item_added")
        else:
            raise Exception("Position can't be < -1")

    async def play_item(self, dest_playlistid, item_name, item_value):
        _LOGGER.debug(item_value)
        if not isinstance(item_value, (list, tuple)):
            insertable = [item_value]
            item_value = insertable

        current_posn = -1

        active_players = await self._kodi.get_players()
        if len(active_players) == 1:
            active_player = active_players[0]
            active_type = active_player.get("type")
            active_playlistid = PLAYLIST_MAP.get(active_type).get("playlistid")
            dest_playlist = await self.call_method_kodi(
                "Playlist.GetItems",
                {
                    "playlistid": dest_playlistid,
                    "properties": ["file"],
                },
            )
            if active_playlistid == dest_playlistid:
                props_item_playing = await self._kodi.get_playing_item_properties(
                    active_player,
                    ["file"],
                )
                active_item_id = props_item_playing.get("id")
                active_item_file = props_item_playing.get("file")
                posn = 0
                for item in dest_playlist:
                    if item.get("id") is not None and item.get("id") == active_item_id:
                        current_posn = posn
                        break
                    if (
                        item.get("file") is not None
                        and item.get("file") == active_item_file
                    ):
                        current_posn = posn
                        break
                    else:
                        posn = posn + 1

            else:
                current_posn = len(dest_playlist)

        idx = current_posn + 1 if current_posn > -1 else PLAY_POSN
        rolling_idx = idx
        for item in item_value:
            await self.call_method_kodi_no_result(
                "Playlist.Insert",
                {
                    "playlistid": dest_playlistid,
                    "position": rolling_idx,
                    "item": {item_name: item},
                },
            )
            rolling_idx = rolling_idx + 1

        await self.call_method_kodi_no_result(
            "Player.Open",
            {"item": {"playlistid": dest_playlistid, "position": idx}},
        )

    async def play_song(self, songid):
        await self.play_item(PLAYLIST_ID_MUSIC, "songid", songid)

    async def play_album(self, albumid):
        await self.play_item(PLAYLIST_ID_MUSIC, "albumid", albumid)

    async def play_movie(self, movieid):
        await self.play_item(PLAYLIST_ID_VIDEO, "movieid", movieid)

    async def play_musicvideo(self, musicvideoid):
        await self.play_item(PLAYLIST_ID_VIDEO, "musicvideoid", musicvideoid)

    async def play_channel(self, channelid):
        await self.call_method_kodi_no_result(
            "Player.Open",
            {"item": {"channelid": channelid}},
        )

    async def play_episode(self, episodeid):
        await self.play_item(PLAYLIST_ID_VIDEO, "episodeid", episodeid)

    async def search_tvshow_detail(self, tvshowid):
        card_json = []

        if tvshowid is None or tvshowid == "":
            _LOGGER.warning("The argument 'value' passed is empty")
            return
        try:
            season_resultset = await self.kodi_search_tvshow_seasons(tvshowid)
            season_data: list[dict[str, Any]] = list()

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
            songs_resultset = await self.kodi_search_songs(value, "artistid", True)

        except Exception:
            _LOGGER.exception("Error updating sensor, is kodi running?")

        if songs_resultset is not None and len(songs_resultset) > 0:
            album_id_set = set()
            albums_data: list[dict[str, Any]] = list()
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
        self, value, filter_field: str = "title", unlimited: bool = False
    ):
        limits = {"start": 0}
        if not unlimited:
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

    async def kodi_search_albums(self, value):
        limits = {"start": 0, "end": self._search_albums_limit}
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

    async def kodi_search_recently_played_songs(self):
        limits = {"start": 0, "end": self._search_recently_played_songs_limit}
        return await self.call_method_kodi(
            "AudioLibrary.GetSongs",
            {
                "properties": PROPS_SONG,
                "limits": limits,
                "sort": {
                    "method": "lastplayed",
                    "order": "descending",
                },
            },
        )

    async def kodi_search_recently_played_albums(self):
        limits = {"start": 0, "end": self._search_recently_played_albums_limit}
        return await self.call_method_kodi(
            "AudioLibrary.GetRecentlyPlayedAlbums",
            {
                "properties": PROPS_ALBUM,
                "limits": limits,
            },
        )

    async def kodi_search_recently_added_albums(self):
        limits = {"start": 0, "end": self._search_recently_added_albums_limit}
        return await self.call_method_kodi(
            "AudioLibrary.GetRecentlyAddedAlbums",
            {
                "properties": PROPS_ALBUM,
                "limits": limits,
            },
        )

    async def kodi_search_recently_added_songs(self):
        limits = {"start": 0, "end": self._search_recently_added_songs_limit}
        return await self.call_method_kodi(
            "AudioLibrary.GetRecentlyAddedSongs",
            {
                "properties": PROPS_SONG,
                "limits": limits,
            },
        )

    async def kodi_search_recently_added_movies(self):
        limits = {"start": 0, "end": self._search_recently_added_movies_limit}
        return await self.call_method_kodi(
            "VideoLibrary.GetRecentlyAddedMovies",
            {
                "properties": PROPS_MOVIE,
                "limits": limits,
            },
        )

    async def kodi_search_recently_added_musicvideos(self):
        limits = {"start": 0, "end": self._search_recently_added_musicvideos_limit}
        return await self.call_method_kodi(
            "VideoLibrary.GetRecentlyAddedMusicVideos",
            {
                "properties": PROPS_MUSICVIDEOS,
                "limits": limits,
            },
        )

    async def kodi_search_recently_added_episodes(self):
        limits = {"start": 0, "end": self._search_recently_added_episodes_limit}
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

    async def kodi_search_artists(self, value):
        limits = {"start": 0, "end": self._search_artists_limit}
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

    async def kodi_search_musicvideos(self, value):
        limits = {"start": 0, "end": self._search_musicvideos_limit}

        return await self.call_method_kodi(
            "VideoLibrary.GetMusicVideos",
            {
                "properties": PROPS_MUSICVIDEOS,
                "limits": limits,
                "sort": {
                    "method": "artist",
                    "order": "ascending",
                    "ignorearticle": True,
                },
                "filter": {
                    "or": [
                        {"field": "title", "operator": "contains", "value": value},
                        {"field": "artist", "operator": "contains", "value": value},
                    ]
                },
            },
        )

    async def kodi_search_movies(self, value):
        limits = {"start": 0, "end": self._search_movies_limit}
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

    async def kodi_search_tvshows(self, value):
        limits = {"start": 0, "end": self._search_tvshows_limit}
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

    async def kodi_search_channels_tv(self, value):
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
        idx = 0
        for value in sub_result:
            filtered_result.append(value)
            if idx < self._search_channels_tv_limit - 1:
                idx += 1
            else:
                break

        return filtered_result

    async def kodi_search_channels_radio(self, value):
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

    async def kodi_search_episodes(self, value):
        limits = {"start": 0, "end": self._search_episodes_limit}
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

    async def search_recently_added(self):
        _LOGGER.debug("Searching recently added")
        card_json = []
        if self._search_recently_added_songs_limit > 0:
            songs = await self.kodi_search_recently_added_songs()
            self._add_result(songs, card_json)

        if self._search_recently_added_albums_limit > 0:
            albums = await self.kodi_search_recently_added_albums()
            self._add_result(albums, card_json)

        if self._search_recently_added_movies_limit > 0:
            movies = await self.kodi_search_recently_added_movies()
            self._add_result(movies, card_json)

        if self._search_recently_added_episodes_limit > 0:
            episodes = await self.kodi_search_recently_added_episodes()
            self._add_result(episodes, card_json)

        if self._search_recently_added_musicvideos_limit > 0:
            musicvideos = await self.kodi_search_recently_added_musicvideos()
            self._add_result(musicvideos, card_json)

        self._data.clear
        self._data = card_json

    async def search_recently_played(self):
        _LOGGER.debug("Searching recently played")
        card_json = []
        if self._search_recently_played_songs_limit > 0:
            songs = await self.kodi_search_recently_played_songs()
            self._add_result(songs, card_json)

        if self._search_recently_played_albums_limit > 0:
            albums = await self.kodi_search_recently_played_albums()
            self._add_result(albums, card_json)

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
        if self._search_songs_limit > 0:
            songs = await self.kodi_search_songs(value)
            self._add_result(songs, card_json)

        if self._search_albums_limit > 0:
            albums = await self.kodi_search_albums(value)
            self._add_result(albums, card_json)

        if self._search_artists_limit > 0:
            artists = await self.kodi_search_artists(value)
            self._add_result(artists, card_json)

        if self._search_movies_limit > 0:
            movies = await self.kodi_search_movies(value)
            self._add_result(movies, card_json)

        if self._search_musicvideos_limit > 0:
            musicvodeos = await self.kodi_search_musicvideos(value)
            self._add_result(musicvodeos, card_json)

        if self._search_tvshows_limit > 0:
            tvshows = await self.kodi_search_tvshows(value)
            self._add_result(tvshows, card_json)

        if self._search_episodes_limit > 0:
            episodes = await self.kodi_search_episodes(value)
            self._add_result(episodes, card_json)

        if self.can_search_pvr and self._search_channels_tv_limit > 0:
            channels = await self.kodi_search_channels_tv(value)
            self._add_result(channels, card_json)

        if self.can_search_pvr and self._search_channels_radio_limit > 0:
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
