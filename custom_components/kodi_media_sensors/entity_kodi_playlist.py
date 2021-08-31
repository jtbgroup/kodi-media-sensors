import homeassistant
import logging
import json
import time as timer
import asyncio

# import datetime
from typing import Optional, Dict, List, Any
from homeassistant.helpers.entity import Entity
from homeassistant import core
from urllib import parse
from .entity_kodi_media_sensor import KodiMediaSensorEntity
from pykodi import Kodi
from homeassistant.const import (
    EVENT_STATE_CHANGED,
    STATE_OFF,
    STATE_ON,
    STATE_IDLE,
    STATE_PAUSED,
    STATE_PLAYING,
    STATE_PROBLEM,
)
from .const import (
    KEY_ALBUMS,
    KEY_SONGS,
    KEY_ARTISTS,
    KEY_MOVIES,
    KEY_ALBUM_DETAILS,
    KEY_ITEMS,
    ENTITY_SENSOR_PLAYLIST,
    ENTITY_NAME_SENSOR_PLAYLIST,
    DOMAIN,
)
from homeassistant.components.kodi.media_player import EVENT_KODI_CALL_METHOD_RESULT

from .types import DeviceStateAttrs, KodiConfig


_LOGGER = logging.getLogger(__name__)

# TODO: change actions by int
ACTION_DO_NOTHING = "nothing"
ACTION_REFRESH_ALL = "refresh_all"
ACTION_REFRESH_META = "refresh_meta"
ACTION_CLEAR = "clear"
EVENT_KODI_SENSOR_PLAYLIST_UPDATE = "kodi.sensor.playlist.update"


# https://raw.githubusercontent.com/custom-components/sensor.kodi_recently_added/master/custom_components/kodi_recently_added/sensor.py


class KodiPlaylistEntity(KodiMediaSensorEntity):

    _playlistid = int(-1)
    _events = {}
    _watch_start = None
    _event_context_id = None

    def __init__(
        self,
        hass,
        kodi: Kodi,
        kodi_entity_id,
        config: KodiConfig,
        use_auth_url: bool = False,
    ):
        super().__init__(kodi, config, use_auth_url)
        self._hass = hass
        self._state = STATE_OFF
        self._kodi_entity_id = kodi_entity_id

        homeassistant.helpers.event.async_track_state_change_event(
            hass, "media_player.kodi", self.__handle_event
        )

    @property
    def name(self) -> str:
        return ENTITY_NAME_SENSOR_PLAYLIST

    @property
    def unique_id(self) -> str:
        return ENTITY_SENSOR_PLAYLIST

    async def __handle_event(self, event):
        old_kodi_event_state = (
            str(event.data.get("old_state").state)
            if event.data.get("old_state") != None
            else STATE_OFF
        )
        old_kodi_event_media_title = str(
            event.data.get("old_state").attributes.get("media_title")
        )
        new_kodi_event_state = str(event.data.get("new_state").state)
        new_kodi_event_media_title = str(
            event.data.get("new_state").attributes.get("media_title")
        )

        old_core_state = core.State(self.entity_id, "off")
        old_core_state.attributes = self._attrs.copy()

        sensor_action = ACTION_DO_NOTHING
        new_entity_state = STATE_ON

        if old_kodi_event_state == new_kodi_event_state:
            if old_kodi_event_media_title == new_kodi_event_media_title:
                sensor_action = ACTION_DO_NOTHING
            else:
                sensor_action = ACTION_REFRESH_ALL
        elif old_kodi_event_state == STATE_OFF:
            sensor_action = ACTION_REFRESH_ALL
        elif new_kodi_event_state == STATE_OFF:
            sensor_action = ACTION_CLEAR
            new_entity_state = STATE_OFF
        elif (
            old_kodi_event_state == STATE_IDLE and new_kodi_event_state == STATE_PLAYING
        ):
            sensor_action = ACTION_REFRESH_ALL
        elif (
            old_kodi_event_state == STATE_PAUSED
            and new_kodi_event_state == STATE_PLAYING
        ) or (
            old_kodi_event_state == STATE_PLAYING
            and new_kodi_event_state == STATE_PAUSED
        ):
            sensor_action = ACTION_REFRESH_META
        elif new_kodi_event_state == STATE_IDLE:
            sensor_action = ACTION_REFRESH_META

        time = event.time_fired
        id = event.context.id + " [" + new_kodi_event_state + "]"
        _LOGGER.debug(
            "Event received:"
            + "\r\n\tState (old >>> new): "
            + old_kodi_event_state
            + " >>> "
            + new_kodi_event_state
            + "\r\n\tTitle (old >>> new): "
            + old_kodi_event_media_title
            + " >>> "
            + new_kodi_event_media_title
            + "\r\n\tExpected action : "
            + sensor_action
            + "\r\n\tTime fired : "
            + str(time)
            + "\r\n\tEvent id : "
            + id
        )

        self._state = new_entity_state
        if sensor_action == ACTION_REFRESH_ALL or sensor_action == ACTION_REFRESH_META:
            await self.__update_meta(id)
            await self.__update_data(id)
        elif sensor_action == ACTION_CLEAR:
            await self.__clear_playlist_data(id)

        self.build_attrs()

        new_core_state = core.State(self.entity_id, "on")
        new_core_state.attributes = self._attrs.copy()
        _LOGGER.debug("number of items in playlist : " + str(len(self._data)))

        event_data = {
            "entity_id": self.entity_id,
            "old_state": old_core_state,
            "new_state": new_core_state,
        }

        self._hass.bus.async_fire(EVENT_STATE_CHANGED, event_data)

    async def async_call_method(self, method, **kwargs):
        _LOGGER.debug("************************************calling method")
        args = ", ".join(f"{key}={value}" for key, value in kwargs.items())
        _LOGGER.debug("calling method " + method + " with arguments " + args)
        self._meta[0]["method"] = method
        self._meta[0]["args"] = args

        if method == "goto":
            item = kwargs.get("item")
            playerid = item.get("playerid")
            to = item.get("to")
            await self.__goto(playerid, to)
        elif method == "remove":
            item = kwargs.get("item")
            playlistid = item.get("playlistid")
            position = item.get("position")
            await self.__remove(playlistid, position)

    async def __remove(self, playlistid, position):
        await self.call_method_kodi_no_result(
            "Playlist.Remove", {"playlistid": playlistid, "position": position}
        )
        await self.__update_meta("remove event")
        await self.__update_data("remove event")

    async def __goto(self, playerid, to):
        await self.call_method_kodi_no_result(
            "Player.GoTo", {"playerid": playerid, "to": to}
        )

    async def async_update(self) -> None:
        """This update is ony used to trigger events so the frontend can be updated. But nothing will happen with this method as no polling is required, but every data change occur when kodi sends events."""
        _LOGGER.debug("> Update Playlist sensor")

    async def __clear_playlist_data(self, event_id):
        self.purge_meta(event_id)
        self.purge_data(event_id)

    async def __update_meta(self, event_id):
        self.init_meta(event_id)
        player_id = -1

        players = await self._kodi.get_players()

        if len(players) == 1:
            kodi_state = self._hass.states.get(self._kodi_entity_id).state
            self._meta[0]["kodi_state"] = kodi_state
            player = players[0]
            player_id = player["playerid"]
            props_player = await self._kodi.get_player_properties(player, ["type"])

            self.add_meta("playlist_id", player_id)
            # TODO : verify if type needed
            self.add_meta("playlist_type", props_player["type"])
            props_item_playing = await self._kodi.get_playing_item_properties(
                player, []
            )

            if props_item_playing.get("id") != None:
                self.add_meta("currently_playing", props_item_playing["id"])
            else:
                _LOGGER.info("No id defined for this item")
        self._playlistid = player_id
        _LOGGER.debug("Metadata updated (event " + event_id + ")")

    async def __update_data(self, event_id):
        result = None
        self.purge_data(event_id)
        try:
            # await self.__update_meta()
            # TODO : is this condition really necessary?
            if self._playlistid > -1:
                result = await self.kodi_get_playlist()
                for item in result:
                    card = {}
                    self.__add_attribute("type", item, "object_type", card)
                    self.__add_attribute("artist", item, "artist", card)
                    self.__add_attribute("genre", item, "genre", card)
                    self.__add_attribute("id", item, "id", card)
                    self.__add_attribute("album", item, "album", card)
                    self.__add_attribute("albumid", item, "albumid", card)
                    self.__add_attribute("artistid", item, "artistid", card)
                    self.__add_attribute("duration", item, "duration", card)
                    self.__add_attribute("label", item, "label", card)
                    self.__add_attribute("title", item, "title", card)
                    self.__add_attribute("episode", item, "episode", card)
                    self.__add_attribute("season", item, "season", card)
                    self.__add_attribute("year", item, "year", card)
                    self.__add_attribute("track", item, "track", card)

                    thumbnail = item["thumbnail"]
                    if thumbnail:
                        thumbnail = self._kodi.thumbnail_url(thumbnail)
                    card["thumbnail"] = thumbnail
                    self.add_data(card)
        except Exception:
            _LOGGER.exception("Error updating sensor, is kodi running?")
            self._state = STATE_PROBLEM

        _LOGGER.debug("Data updated (event " + event_id + ")")

    async def kodi_get_playlist(self):
        limits = {"start": 0}
        return await self.call_method_kodi(
            KEY_ITEMS,
            "Playlist.GetItems",
            {
                "properties": [
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
                ],
                "playlistid": self._playlistid,
                "limits": limits,
            },
        )

    def __add_attribute(self, attribute_name, data, target_attribute_name, target):
        if attribute_name in data:
            target[target_attribute_name] = data[attribute_name]

    async def fire_kodi_sensor_update_event(self):
        self._hass.bus.fire(
            "state_changed",
            {
                "entity_id": self.entity_id,
                "old_state": {
                    "entity_id": self.entity_id,
                    "state": self._state,
                    "attributes": {
                        "data": self._attrs,
                        "friendly_name": self.name,
                    },
                },
                "new_state": {
                    "entity_id": self.entity_id,
                    "state": self._state,
                    "attributes": {
                        "data": self._attrs,
                        "friendly_name": self.name,
                    },
                },
            },
        )
        _LOGGER.info("event event event event")
