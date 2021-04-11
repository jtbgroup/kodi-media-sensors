import logging
import json
import time
from typing import Optional, Dict, List, Any
from homeassistant.helpers.entity import Entity
from urllib import parse
from .entity_kodi_media_sensor import KodiMediaSensorEntity
from homeassistant.const import STATE_OFF, STATE_ON, STATE_PROBLEM, STATE_UNKNOWN
from pykodi import Kodi
from .const import (
    KEY_ALBUMS,
    KEY_SONGS,
    KEY_ARTISTS,
    KEY_MOVIES,
    KEY_ALBUM_DETAILS,
    KEY_ITEMS,
    ENTITY_SENSOR_PLAYLIST,
    ENTITY_NAME_SENSOR_PLAYLIST,
)
from .types import DeviceStateAttrs, KodiConfig

_LOGGER = logging.getLogger(__name__)


class KodiPlaylistEntity(KodiMediaSensorEntity):

    _playlistid = int(-1)

    def __init__(
        self,
        kodi: Kodi,
        config: KodiConfig,
        kodi_entity_id: str,
        use_auth_url: bool = False,
    ):
        super().__init__(kodi, config, use_auth_url)
        self._state = STATE_ON
        self._kodi_entity_id = kodi_entity_id

    @property
    def name(self) -> str:
        return ENTITY_NAME_SENSOR_PLAYLIST

    @property
    def unique_id(self) -> str:
        return ENTITY_SENSOR_PLAYLIST

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
            await self.goto(playerid, to)
        elif method == "remove":
            item = kwargs.get("item")
            playlistid = item.get("playlistid")
            position = item.get("position")
            await self.remove(playlistid, position)

    async def remove(self, playlistid, position):
        await self.call_method_kodi_no_result(
            "Playlist.Remove", {"playlistid": playlistid, "position": position}
        )
        await self.async_update()

    async def goto(self, playerid, to):
        await self.call_method_kodi_no_result(
            "Player.GoTo", {"playerid": playerid, "to": to}
        )
        await self.async_update()

    async def async_update(self) -> None:
        _LOGGER.debug("> Update Playlist sensor")

        self.init_attrs()
        result = None
        try:
            await self.update_meta()
            if self._playlistid > -1:
                result = await self.kodi_get_playlist()
        except Exception:
            _LOGGER.exception("Error updating sensor, is kodi running?")
            self._state = STATE_OFF

        card_json = []
        if result is not None and len(result) > 0:
            card_json = self.format_items(result)

        self._data.clear
        self._data = card_json
        self._state = STATE_ON

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

    async def update_meta(self):
        result2 = {}
        # this is necessary because the player is not instantly ready when a json rpc GoTo function is called
        # time.sleep(1)
        player_type = "unknown"
        player_id = -1
        current = -1
        try:
            result2 = await self._kodi.call_method("Player.GetActivePlayers")
            if len(result2) == 0:
                _LOGGER.debug("No player currently running")
            else:
                player_id = result2[0]["playerid"]
                player_type = result2[0]["type"]

                playing = await self.call_method_kodi(
                    "item",
                    "Player.GetItem",
                    {
                        "playerid": player_id,
                    },
                )
                if playing is not None:
                    current = playing["id"]

        except Exception:
            _LOGGER.exception("Error updating sensor, is kodi running?")

        self._meta[0]["playlist_id"] = player_id
        self._meta[0]["playlist_type"] = player_type
        self._meta[0]["currently_playing"] = current
        self._playlistid = player_id

    def format_items(self, values):
        result = []
        card = {}
        if self._playlistid >= 0:
            for item in values:
                card = {
                    "object_type": item["type"],
                    "id": item["id"],
                    "artist": ",".join(item["artist"]),
                    "genre": ",".join(item["genre"]),
                    "thumbnail": "",
                }
                self.add_attribute("album", item, "album", card)
                self.add_attribute("albumid", item, "albumid", card)
                self.add_attribute("artistid", item, "artistid", card)
                self.add_attribute("duration", item, "duration", card)
                self.add_attribute("label", item, "label", card)
                self.add_attribute("title", item, "title", card)
                self.add_attribute("episode", item, "episode", card)
                self.add_attribute("season", item, "season", card)
                self.add_attribute("year", item, "year", card)
                self.add_attribute("track", item, "track", card)

                thumbnail = item["thumbnail"]
                if thumbnail:
                    thumbnail = self.get_web_url(
                        parse.unquote(thumbnail)[8:].strip("/")
                    )
                card["thumbnail"] = thumbnail

                result.append(card)
        return result

    def add_attribute(self, attribute_name, data, target_attribute_name, target):
        if attribute_name in data:
            target[target_attribute_name] = data[attribute_name]
