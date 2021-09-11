import logging
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from pykodi import Kodi
from urllib import parse
from homeassistant.helpers.entity import Entity
from homeassistant.const import (
    STATE_OFF,
    STATE_ON,
    STATE_UNKNOWN,
    STATE_PROBLEM,
)
from .types import DeviceStateAttrs, KodiConfig
from .const import DOMAIN
from abc import ABC, abstractmethod

_LOGGER = logging.getLogger(__name__)
UPDATE_FORMAT = "%Y%m%d%H%M%S%f"


class KodiMediaSensorEntity(Entity, ABC):
    """This super class should never be instanciated. It's ba parent class of all the kodi media sensors"""

    _attrs = {}
    _data = []
    _meta = []

    def __init__(
        self,
        kodi: Kodi,
        config: KodiConfig,
        hide_watched: bool = False,
        use_auth_url: bool = False,
    ) -> None:
        super().__init__()
        self._kodi = kodi
        self.__define_base_url(config, use_auth_url)

    def __define_base_url(self, config, use_auth_url):
        protocol = "https" if config["ssl"] else "http"
        auth = ""
        if (
            use_auth_url
            and config["username"] is not None
            and config["password"] is not None
        ):
            auth = f"{config['username']}:{config['password']}@"
        self._base_web_url = (
            f"{protocol}://{auth}{config['host']}:{config['port']}/image/image%3A%2F%2F"
        )

    @abstractmethod
    async def async_call_method(self, method, **kwargs):
        _LOGGER.warning("This method is not implemented for the entity")

    async def call_method_kodi(self, result_key, method, args) -> List:
        result = None
        data = None
        try:
            # Parameters are passed using a **kwargs because the number of JSON parmeters depends on each function
            result = await self._kodi.call_method(method, **args)
        except Exception:
            _LOGGER.exception("Error updating sensor, is kodi running?")
            self._state = STATE_PROBLEM

        if result:
            data = self._handle_result(result, result_key)
            self._state = STATE_ON
        else:
            self._state = STATE_OFF

        return data

    async def call_method_kodi_no_result(self, method, args):
        try:
            # Parameters are passed using a **kwargs because the number of JSON parmeters depends on each function
            await self._kodi.call_method(method, **args)
            self._state = STATE_ON
        except Exception:
            _LOGGER.exception("Error updating sensor, is kodi running?")
            self._state = STATE_PROBLEM

    def _handle_result(self, result, result_key) -> List:
        error = result.get("error")
        if error:
            _LOGGER.error(
                "Error while fetching %s: [%d] %s"
                % (result_key, error.get("code"), error.get("message"))
            )
            self._state = STATE_PROBLEM
            return

        new_data: List[Dict[str, Any]] = result.get(result_key, [])
        if not new_data:
            _LOGGER.info(
                "No %s found after requesting data from Kodi, assuming empty."
                % result_key
            )
            self._state = STATE_UNKNOWN
            return

        self._state = STATE_ON
        return new_data

    @property
    def state(self) -> Optional[str]:
        return self._state

    # def get_web_url(self, path: str) -> str:
    #     """Get the web URL for the provided path.

    #     This is used for fanart/poster images that are not a http url.  For
    #     example the path is local to the kodi installation or a path to
    #     an NFS share.

    #     :param path: The local/nfs/samba/etc. path.
    #     :returns: The web url to access the image over http.
    #     """
    #     if path.lower().startswith("http"):
    #         return path
    #     # This looks strange, but the path needs to be quoted twice in order
    #     # to work.
    #     # added Gautier : character @ causes encoding problems for thumbnails revrieved from http://...music@smb... Therefore, it is escaped in the first quote
    #     quoted_path2 = parse.quote(parse.quote(path, safe="@"))
    #     encoded = self._base_web_url + quoted_path2
    #     return encoded

    @property
    def domain_unique_id(self) -> str:
        return "sensor." + self.unique_id

    @property
    def device_state_attributes(self) -> DeviceStateAttrs:
        self.build_attrs()
        return self._attrs

    def format_songs(self, values):
        if values is None:
            return None

        result = []
        for item in values:
            card = {
                "object_type": "song",
            }
            self.add_attribute("artist", item, "artist", card)
            self.add_attribute("artistid", item, "artistid", card)
            self.add_attribute("title", item, "title", card)
            self.add_attribute("album", item, "album", card)
            self.add_attribute("year", item, "year", card)
            self.add_attribute("songid", item, "songid", card)
            self.add_attribute("track", item, "track", card)
            self.add_attribute("genre", item, "genre", card)
            self.add_attribute("duration", item, "duration", card)
            self.add_attribute("id", item, "id", card)
            self.add_attribute("type", item, "object_type", card)
            self.add_attribute("albumid", item, "albumid", card)
            self.add_attribute("label", item, "label", card)
            self.add_attribute("episode", item, "episode", card)
            self.add_attribute("season", item, "season", card)

            thumbnail = item["thumbnail"]
            if thumbnail:
                # thumbnail = self.get_web_url(parse.unquote(thumbnail)[8:].strip("/"))
                thumbnail = self._kodi.thumbnail_url(thumbnail)
                card["thumbnail"] = thumbnail

            result.append(card)
        return result

    def add_attribute(self, attribute_name, data, target_attribute_name, target):
        if attribute_name in data:
            target[target_attribute_name] = data[attribute_name]

    def build_attrs(self):
        self._attrs.clear
        self._attrs["meta"] = json.dumps(self._meta)
        self._attrs["data"] = json.dumps(self._data)

    def init_meta(self, event_id):
        ds = datetime.now().strftime(UPDATE_FORMAT)
        self.purge_meta(event_id)
        self._meta[0]["update_time"] = ds
        self._meta[0]["sensor_entity_id"] = self.domain_unique_id
        self._meta[0]["service_domain"] = DOMAIN
        self.build_attrs()
        _LOGGER.debug("Init metadata (event " + event_id + ")")

    def purge_meta(self, event_id):
        self._meta = [{}]
        _LOGGER.debug("Purged metadata (event " + event_id + ")")

    def add_meta(self, key, value):
        if len(self._meta[0]) == 0:
            self.init_meta
        self._meta[0][key] = value

    def purge_data(self, event_id):
        self._data = []
        _LOGGER.debug("Purged data (event " + event_id + ")")
