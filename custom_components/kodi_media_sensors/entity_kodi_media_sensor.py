from abc import ABC, abstractmethod
from datetime import datetime
import json
import logging
from typing import Any, Optional
from urllib import parse

from homeassistant.const import STATE_OFF, STATE_ON, STATE_PROBLEM
from homeassistant.helpers.entity import Entity
from pykodi import Kodi

from .const import (
    DOMAIN,
    KEYS,
    MAP_KEY_MEDIA_TYPE,
    MEDIA_TYPE_ALBUM_DETAIL,
    MEDIA_TYPE_SEASON_DETAIL,
    MEDIA_TYPE_TVSHOW_DETAIL,
)
from .media_sensor_event_manager import MediaSensorEventManager
from .types import ExtraStateAttrs, KodiConfig

_LOGGER = logging.getLogger(__name__)
UPDATE_FORMAT = "%Y%m%d%H%M%S%f"


class KodiMediaSensorEntity(Entity, ABC):
    """This super class should never be instantiated. It's the parent class of all the kodi media sensors"""

    _attrs = {}
    _data = []
    _meta = []
    _unique_id: str

    def __init__(
        self,
        unique_id,
        kodi: Kodi,
        kodi_entity_id,
        config: KodiConfig,
        event_manager: MediaSensorEventManager,
    ) -> None:
        super().__init__()
        self._unique_id = unique_id
        self._kodi = kodi
        self._kodi_entity_id = kodi_entity_id
        self._event_manager = event_manager
        self._define_base_url(config)
        self._state = STATE_OFF
        self._event_manager.register_sensor(self)

    @property
    def unique_id(self):
        """Return the unique id of the device."""
        return self._unique_id

    @property
    def name(self):
        return self._unique_id

    def _define_base_url(self, config):
        protocol = "https" if config["ssl"] else "http"
        auth = ""
        if config["username"] is not None and config["password"] is not None:
            auth = f"{config['username']}:{config['password']}@"
        self._base_web_url = (
            f"{protocol}://{auth}{config['host']}:{config['port']}/image/image%3A%2F%2F"
        )

    @abstractmethod
    async def async_call_method(self, method, **kwargs):
        _LOGGER.warning("This method is not implemented for the entity")

    async def call_method_kodi(self, method, args) -> list:
        result = None
        data = None
        try:
            # Parameters are passed using a **kwargs because the number of JSON parameters depends on each function
            result = await self._kodi.call_method(method, **args)
            data = self._handle_result(result)
            self._state = STATE_ON
        except Exception as exception:
            _LOGGER.exception(
                "Error updating sensor, is kodi running? : %s", str(exception)
            )
            self._state = STATE_PROBLEM

        return data

    async def call_method_kodi_no_result(self, method, args):
        try:
            # Parameters are passed using a **kwargs because the number of JSON parameters depends on each function
            await self._kodi.call_method(method, **args)
            self._state = STATE_ON
        except Exception as exception:
            _LOGGER.exception(
                "Error updating sensor, is kodi running? : %s", str(exception)
            )
            self._state = STATE_PROBLEM

    def _handle_result(self, result) -> list:
        new_data = []
        error = result.get("error")
        if error:
            _LOGGER.error(
                "Error while fetching data: %s",
                [error.get("code"), error.get("message")],
            )
            self._state = STATE_PROBLEM
            return

        for entry in result:
            if entry in KEYS:
                new_data: list[dict[str, Any]] = result.get(entry, [])
                default_type = MAP_KEY_MEDIA_TYPE.get(entry)

                if self._hasLeaf(default_type):
                    for item in new_data:
                        self._format_item(item, default_type)
                else:
                    self._format_item(new_data, default_type)

        return new_data

    def _hasLeaf(self, default_type):
        if (
            default_type == MEDIA_TYPE_ALBUM_DETAIL
            or default_type == MEDIA_TYPE_TVSHOW_DETAIL
        ):
            return False
        return True

    def _format_item(self, item, default_type):
        if not "type" in item:
            item["type"] = default_type

        if "genre" in item:
            item["genre"] = ", ".join(item["genre"])

        if "thumbnail" in item:
            th = item["thumbnail"]
            if th is None or th == "":
                del item["thumbnail"]
            else:
                thumbnail = self._kodi.thumbnail_url(item["thumbnail"])
                item["thumbnail"] = thumbnail

        if "art" in item:
            fanart_ref = "fanart"
            poster_ref = "poster"

            try:
                if default_type == MEDIA_TYPE_SEASON_DETAIL:
                    fanart_ref = "tvshow.fanart"

                fanart = item["art"].get(fanart_ref, "")
                poster = item["art"].get(poster_ref, "")
                if fanart:
                    fanart = self.get_web_url(parse.unquote(fanart)[8:].strip("/"))
                if poster:
                    poster = self.get_web_url(parse.unquote(poster)[8:].strip("/"))
                if fanart != "":
                    item["fanart"] = fanart
                if poster != "":
                    item["poster"] = poster
            except KeyError:
                _LOGGER.warning("Error parsing key from movie blob: %s", item)

            del item["art"]

        if "rating" in item:
            rating = round(item["rating"], 1)
            if rating:
                rating = f"\N{BLACK STAR} {rating}"
            item["rating"] = rating

    @property
    def state(self) -> Optional[str]:
        return self._state

    def get_web_url(self, path: str) -> str:
        """Get the web URL for the provided path.

        This is used for fanart/poster images that are not a http url.  For
        example the path is local to the kodi installation or a path to
        an NFS share.

        :param path: The local/nfs/samba/etc. path.
        :returns: The web url to access the image over http.
        """
        if path.lower().startswith("http"):
            return path
        # This looks strange, but the path needs to be quoted twice in order
        # to work.
        # added Gautier : character @ causes encoding problems for thumbnails retrieved from http://...music@smb... Therefore, it is escaped in the first quote
        quoted_path2 = parse.quote(parse.quote(path, safe="@"))
        encoded = self._base_web_url + quoted_path2
        return encoded

    @property
    def domain_unique_id(self) -> str:
        return "sensor." + self.unique_id

    @property
    def extra_state_attributes(self) -> ExtraStateAttrs:
        self.build_attrs()
        return self._attrs

    def add_attribute(self, attribute_name, data, target_attribute_name, target):
        if attribute_name in data:
            target[target_attribute_name] = data[attribute_name]

    def build_attrs(self):
        # self._attrs.clear
        self._attrs["meta"] = json.dumps(self._meta)
        self._attrs["data"] = json.dumps(self._data)

    def init_meta(self, event_id):
        ds = datetime.now().strftime(UPDATE_FORMAT)
        self.purge_meta(event_id)
        self._meta[0]["update_time"] = ds
        self._meta[0]["sensor_entity_id"] = self.domain_unique_id
        self._meta[0]["kodi_entity_id"] = self._kodi_entity_id
        self._meta[0]["service_domain"] = DOMAIN
        self.build_attrs()
        _LOGGER.debug("Init metadata (event %s)", event_id)

    def purge_meta(self, event_id):
        self._meta = [{}]
        _LOGGER.debug("Purged metadata (event %s)", event_id)

    def add_meta(self, key, value):
        if len(self._meta[0]) == 0:
            self.init_meta("Init because no meta during add")
        self._meta[0][key] = value

    def purge_data(self, event_id):
        self._data = []
        _LOGGER.debug("Purged data (event %s)", event_id)
