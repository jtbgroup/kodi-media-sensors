import json
import logging
import time
from typing import Any, Dict, List, Optional
from urllib import parse

from homeassistant.const import STATE_OFF, STATE_ON, STATE_PROBLEM, STATE_UNKNOWN
from homeassistant.helpers.entity import Entity
from pykodi import Kodi

from .types import DeviceStateAttrs, KodiConfig
from .entity_kodi_media_sensor import KodiMediaSensorEntity
from .const import (
    ENTITY_SENSOR_RECENTLY_ADDED_MOVIE,
    ENTITY_SENSOR_RECENTLY_ADDED_TVSHOW,
    ENTITY_NAME_SENSOR_RECENTLY_ADDED_TVSHOW,
    ENTITY_NAME_SENSOR_RECENTLY_ADDED_MOVIE,
)

_LOGGER = logging.getLogger(__name__)


class KodiMediaEntity(KodiMediaSensorEntity):
    result_key: str = NotImplemented
    update_method: str = NotImplemented
    call_args: tuple()

    def __init__(
        self,
        kodi: Kodi,
        config: KodiConfig,
        hide_watched: bool = False,
        use_auth_url: bool = False,
    ) -> None:
        super().__init__(kodi, config)
        self.kodi = kodi
        self.hide_watched = hide_watched
        self.use_auth_url = use_auth_url
        self.data = []
        self._state = None

    async def async_update(self) -> None:
        result = None
        try:
            # Parameters are passed using a **kwargs because the number of JSON parmeters depends on each function
            result = await self.kodi.call_method(self.update_method, **self.call_args)
        except Exception:
            _LOGGER.exception("Error updating sensor, is kodi running?")
            self._state = STATE_OFF

        if result:
            self._handle_result(result)
        else:
            self._state = STATE_OFF

    def _handle_result(self, result) -> None:
        error = result.get("error")
        if error:
            _LOGGER.error(
                "Error while fetching %s: [%d] %s"
                % (self.result_key, error.get("code"), error.get("message"))
            )
            self._state = STATE_PROBLEM
            return

        new_data: List[Dict[str, Any]] = result.get(self.result_key, [])
        if not new_data:
            _LOGGER.warning(
                "No %s found after requesting data from Kodi, assuming empty."
                % self.result_key
            )
            self._state = STATE_UNKNOWN
            return

        self.data = new_data
        self._state = STATE_ON


class KodiRecentlyAddedTVEntity(KodiMediaEntity):

    properties = [
        "art",
        "dateadded",
        "episode",
        "fanart",
        "firstaired",
        "playcount",
        "rating",
        "runtime",
        "season",
        "showtitle",
        "title",
    ]
    update_method = "VideoLibrary.GetRecentlyAddedEpisodes"
    result_key = "episodes"
    call_args = {"properties": properties}

    @property
    def unique_id(self) -> str:
        """The unique ID of the entity.

        It's important to define this, otherwise the entities created will not show up
        on the configured integration card as associated with the integration.
        """
        return ENTITY_SENSOR_RECENTLY_ADDED_TVSHOW

    @property
    def name(self) -> str:
        return ENTITY_NAME_SENSOR_RECENTLY_ADDED_TVSHOW

    @property
    def device_state_attributes(self) -> DeviceStateAttrs:
        attrs = {}
        card_json = [
            {
                "title_default": "$title",
                "line1_default": "$episode",
                "line2_default": "$release",
                "line3_default": "$rating - $runtime",
                "line4_default": "$number",
                "icon": "mdi:eye-off",
            }
        ]
        for show in self.data:
            if self.hide_watched and show["playcount"] > 0:
                continue
            try:
                card = {
                    "airdate": show["dateadded"].replace(" ", "T") + "Z",
                    "episode": show["title"],
                    "fanart": "",
                    "flag": show["playcount"] == 0,
                    "genres": "",
                    "number": "S{:0>2}E{:0>2}".format(show["season"], show["episode"]),
                    "poster": "",
                    "release": "$day, $date",
                    "runtime": show["runtime"] // 60,
                    "title": show["showtitle"],
                    "studio": "",
                }
                rating = round(show["rating"], 1)
                if rating:
                    rating = f"\N{BLACK STAR} {rating}"
                card["rating"] = rating
                fanart = show["art"].get("tvshow.fanart", "")
                poster = show["art"].get("tvshow.poster", "")
                if fanart:
                    card["fanart"] = self.get_web_url(
                        parse.unquote(fanart)[8:].strip("/")
                    )
                if poster:
                    card["poster"] = self.get_web_url(
                        parse.unquote(poster)[8:].strip("/")
                    )
            except KeyError:
                _LOGGER.warning("Error parsing key from tv blob: %s", show)
                continue
            card_json.append(card)

        attrs["data"] = json.dumps(card_json)
        return attrs


class KodiRecentlyAddedMoviesEntity(KodiMediaEntity):

    properties = [
        "art",
        "dateadded",
        "genre",
        "playcount",
        "premiered",
        "rating",
        "runtime",
        "studio",
        "title",
    ]
    update_method = "VideoLibrary.GetRecentlyAddedMovies"
    result_key = "movies"
    call_args = {"properties": properties}

    @property
    def unique_id(self) -> str:
        return ENTITY_SENSOR_RECENTLY_ADDED_MOVIE

    @property
    def name(self) -> str:
        return ENTITY_NAME_SENSOR_RECENTLY_ADDED_MOVIE

    @property
    def device_state_attributes(self) -> DeviceStateAttrs:
        attrs = {}
        card_json = [
            {
                "title_default": "$title",
                "line1_default": "$genres",
                "line2_default": "$release",
                "line3_default": "$rating - $runtime",
                "line4_default": "$studio",
                "icon": "mdi:eye-off",
            }
        ]
        for movie in self.data:
            if self.hide_watched and movie["playcount"] > 0:
                continue
            try:
                card = {
                    "aired": movie["premiered"],
                    "airdate": movie["dateadded"].replace(" ", "T") + "Z",
                    "flag": movie["playcount"] == 0,
                    "genres": ",".join(movie["genre"]),
                    "rating": round(movie["rating"], 1),
                    "release": "$date",
                    "runtime": movie["runtime"] // 60,
                    "title": movie["title"],
                    "studio": ",".join(movie["studio"]),
                }
                rating = round(movie["rating"], 1)
                if rating:
                    rating = f"\N{BLACK STAR} {rating}"
                card["rating"] = rating
                fanart = movie["art"].get("fanart", "")
                poster = movie["art"].get("poster", "")
            except KeyError:
                _LOGGER.warning("Error parsing key from movie blob: %s", movie)
                continue
            if fanart:
                fanart = self.get_web_url(parse.unquote(fanart)[8:].strip("/"))
            if poster:
                poster = self.get_web_url(parse.unquote(poster)[8:].strip("/"))
            card["fanart"] = fanart
            card["poster"] = poster
            card_json.append(card)

        attrs["data"] = json.dumps(card_json)
        return attrs
