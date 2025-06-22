import logging

import homeassistant
from homeassistant.const import (  # EVENT_STATE_CHANGED,
    STATE_IDLE,
    STATE_OFF,
    STATE_ON,
    STATE_PAUSED,
    STATE_PLAYING,
)
from pykodi import Kodi

from .const import PROPS_ITEM, PROPS_ITEM_LIGHT
from .entity_kodi_media_sensor import KodiMediaSensorEntity
from .media_sensor_event_manager import MediaSensorEventManager
from homeassistant.helpers import entity_registry as er
from .types import KodiConfig
from urllib.parse import urlparse
from homeassistant.helpers import entity_registry as entity_registry

_UNIQUE_ID_PREFIX = "kms_p_"
_LOGGER = logging.getLogger(__name__)

# TODO: change actions by int
ACTION_DO_NOTHING = "nothing"
ACTION_REFRESH_ALL = "refresh_all"
ACTION_REFRESH_META = "refresh_meta"
ACTION_CLEAR = "clear"


class KodiMediaSensorsPlaylistEntity(KodiMediaSensorEntity):
    _unique_id: str
    _playlistid = int(-1)
    _events = {}
    _watch_start = None
    _event_context_id = None
    _initialized = False

    def __init__(
        self,
        config_unique_id,
        hass,
        kodi: Kodi,
        kodi_entity_id,
        config: KodiConfig,
        event_manager: MediaSensorEventManager,
    ):
        super().__init__(
            _UNIQUE_ID_PREFIX + config_unique_id,
            kodi,
            kodi_entity_id,
            config,
            event_manager,
        )

        self._hass = hass

        homeassistant.helpers.event.async_track_state_change_event(
            hass, kodi_entity_id, self.__handle_event
        )

        # TODO: populate immediately the data if kodi is running
        kodi_state = self._hass.states.get(kodi_entity_id).state
        if kodi_state is None or kodi_state == STATE_OFF:
            self._state = STATE_OFF
        else:
            self._state = STATE_ON

    async def handle_media_sensor_event(self, event):
        event_id = event
        await self._update_meta(event_id)
        await self._update_data(event_id)
        _LOGGER.debug("number of items in playlist : %s", str(len(self._data)))
        self._force_update_state()

    async def __handle_event(self, event):
        old_kodi_event_state = (
            str(event.data.get("old_state").state)
            if event.data.get("old_state") != None
            else STATE_OFF
        )
        old_kodi_event_media_title = str(
            str(event.data.get("old_state").attributes.get("media_title"))
            if event.data.get("old_state") is not None
            else ""
        )
        new_kodi_event_state = str(event.data.get("new_state").state)
        new_kodi_event_media_title = str(
            event.data.get("new_state").attributes.get("media_title")
        )

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
        evt_id = (
            event.context.id
            + " "
            + str(event.time_fired)
            + " ["
            + new_kodi_event_state
            + "]"
        )
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
            + evt_id
        )

        self._state = new_entity_state
        # if sensor_action == ACTION_REFRESH_ALL or sensor_action == ACTION_REFRESH_META:
        if sensor_action == ACTION_CLEAR:
            await self._clear_all_data(evt_id)
        else:
            await self._update_meta(evt_id)
            await self._update_data(evt_id)

        _LOGGER.debug("number of items in playlist : %s", str(len(self._data)))
        self._force_update_state()

    def _force_update_state(self):
        # self.schedule_update_ha_state()
        # await self.async_schedule_update_ha_state()
        self._hass.async_create_task(self.async_update_ha_state(True))

    async def async_call_method(self, method, **kwargs):
        _LOGGER.debug("************************************calling method")
        args = ", ".join(f"{key}={value}" for key, value in kwargs.items())
        _LOGGER.debug("calling method %s with arguments %s", method, args)
        self._meta[0]["method"] = method
        self._meta[0]["args"] = args

        if method == "goto":
            item = kwargs.get("item")
            playerid = item.get("playerid")
            position = item.get("position")
            await self._goto(playerid, position)
        elif method == "remove":
            item = kwargs.get("item")
            playlistid = item.get("playlistid")
            position = item.get("position")
            await self._remove(playlistid, position)
        elif method == "moveto":
            item = kwargs.get("item")
            playlistid = item.get("playlistid")
            position_from = item.get("position_from")
            position_to = item.get("position_to")
            await self._moveto(playlistid, position_from, position_to)

    async def _moveto(self, playlistid, position_from, position_to):
        items = await self.kodi_get_playlist_light(playlistid)
        origin = items[int(position_from)]
        # if position_from < position_to:
        #     position_to = position_to - 1

        await self.call_method_kodi_no_result(
            "Playlist.Remove", {"playlistid": playlistid, "position": position_from}
        )

        await self.call_method_kodi_no_result(
            "Playlist.Insert",
            {
                "playlistid": playlistid,
                "position": position_to,
                "item": {self._get_id_tag(origin.get("type")): origin.get("id")},
            },
        )

        # updating data is needed as there is no event fired by kodi
        await self._update_meta("move event")
        await self._update_data("move event")
        self._force_update_state()

    def _get_id_tag(self, type):
        if type == "song":
            return "songid"
        elif type == "movie":
            return "movieid"

        return "itemid"

    async def _remove(self, playlistid, position):
        await self.call_method_kodi_no_result(
            "Playlist.Remove", {"playlistid": playlistid, "position": position}
        )
        # updating data is needed as there is no event fired by kodi
        await self._update_meta("remove event")
        await self._update_data("remove event")
        self._force_update_state()

    async def _goto(self, playerid, to):
        await self.call_method_kodi_no_result(
            "Player.GoTo", {"playerid": playerid, "to": to}
        )

    async def async_update(self) -> None:
        """This update is only used to trigger events so the frontend can be updated. But nothing will happen with this method as no polling is required, but every data change occur when kodi sends events."""
        _LOGGER.debug("> Update Playlist sensor")

        # this piece of code is used to initialize the meta and data when the sensor starts for the first time and kodi is not off (and thus the sensor neither as the state is set in the constructor based on the state of kodi)
        if self._state == STATE_ON and len(self._meta) == 0:
            self.init_meta("Kodi Playlist update event")
            await self._update_meta("Kodi Playlist update event")
            await self._update_data("Kodi Playlist update event")
            self._initialized = True

    async def _clear_all_data(self, event_id):
        self.purge_meta(event_id)
        self.purge_data(event_id)

    async def _update_meta(self, event_id):
        self.init_meta(event_id)
        players = await self._kodi.get_players()
        if len(players) == 1:
            player = players[0]
            player_id = player["playerid"]
            self.add_meta("playlist_id", player_id)
            self.add_meta("playlist_type", player["type"])

            props_item_playing = await self._kodi.get_playing_item_properties(
                player, ["file"]
            )
            if props_item_playing.get("id") is not None:
                self.add_meta("currently_playing", props_item_playing["id"])
                _LOGGER.debug("Currently playing %s", str(props_item_playing["id"]))
            else:
                _LOGGER.info("No id defined for this item")
            if props_item_playing.get("file") is not None:
                self.add_meta("currently_playing_file", props_item_playing["file"])
                _LOGGER.debug(
                    "Currently playing file %s", str(props_item_playing["file"])
                )
            else:
                _LOGGER.info("No file path known for this item")
            self._playlistid = player_id
        else:
            self._playlistid = -1

        _LOGGER.debug("Metadata updated (event %s)", event_id)

    async def _update_data(self, event_id):
        items = None
        try:
            # TODO : is this condition really necessary?
            if self._playlistid > -1:
                items = await self.kodi_get_playlist()

        except Exception:
            _LOGGER.exception("Error updating sensor, is kodi running?")

        self._kodi.get_album_details
        card_json = []
        self.add_result(items, card_json)
        self._data.clear
        self._data = card_json

        _LOGGER.debug("Data updated (event %s)", event_id)

    def add_result(self, data, target):
        if data is not None and len(data) > 0:
            for row in data:
                target.append(row)

    async def kodi_get_playlist(self):
        limits = {"start": 0}
        return await self.call_method_kodi(
            "Playlist.GetItems",
            {
                "properties": PROPS_ITEM,
                "playlistid": self._playlistid,
                "limits": limits,
            },
        )

        # result = await self.call_method_kodi(
        #     "Playlist.GetItems",
        #     {
        #         "properties": PROPS_ITEM,
        #         "playlistid": self._playlistid,
        #         "limits": limits,
        #     },
        # )

        # attrs = self._hass.states.get(self._kodi_entity_id).attributes
        # if attrs["entity_picture"]:
        #     parsed_url = urlparse(attrs["entity_picture"]).query
        #     params = parsed_url.split("&")
        #     d = dict(s.split("=") for s in params)
        #     for value in result:
        #         url = (
        #             "/api/media_player_proxy/"
        #             + self._kodi_entity_id
        #             + "/browse_media/album/"
        #             + str(value["albumid"])
        #             # + "?token="
        #             # + d["token"]
        #         )
        #         value["api_image"] = url

        # return result

    async def kodi_get_playlist_light(self, playlistid):
        limits = {"start": 0}
        return await self.call_method_kodi(
            "Playlist.GetItems",
            {
                "properties": PROPS_ITEM_LIGHT,
                "playlistid": playlistid,
                "limits": limits,
            },
        )
