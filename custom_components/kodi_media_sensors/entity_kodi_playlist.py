import homeassistant
import logging
from .entity_kodi_media_sensor import KodiMediaSensorEntity
from pykodi import Kodi
from homeassistant.const import (
    # EVENT_STATE_CHANGED,
    STATE_OFF,
    STATE_ON,
    STATE_IDLE,
    STATE_PAUSED,
    STATE_PLAYING,
    # STATE_PROBLEM,
)
from .const import (
    KEY_ITEMS,
    ENTITY_SENSOR_PLAYLIST,
    ENTITY_NAME_SENSOR_PLAYLIST,
    PROPS_ITEM,
)


from .types import KodiConfig


_LOGGER = logging.getLogger(__name__)

# TODO: change actions by int
ACTION_DO_NOTHING = "nothing"
ACTION_REFRESH_ALL = "refresh_all"
ACTION_REFRESH_META = "refresh_meta"
ACTION_CLEAR = "clear"

# https://raw.githubusercontent.com/custom-components/sensor.kodi_recently_added/master/custom_components/kodi_recently_added/sensor.py


class KodiPlaylistEntity(KodiMediaSensorEntity):

    _playlistid = int(-1)
    _events = {}
    _watch_start = None
    _event_context_id = None
    _initialized = False

    def __init__(
        self,
        hass,
        kodi: Kodi,
        kodi_entity_id,
        config: KodiConfig,
    ):
        super().__init__(kodi, config)
        self._hass = hass

        homeassistant.helpers.event.async_track_state_change_event(
            hass, kodi_entity_id, self.__handle_event
        )
        kodi_state = self._hass.states.get(kodi_entity_id)
        if kodi_state is None or kodi_state == STATE_OFF:
            self._state = STATE_OFF
        else:
            self._state = STATE_ON

        # TODO: populate immediately the data if kodi is running
        kodi_state = self._hass.states.get(kodi_entity_id)
        if kodi_state is None or kodi_state == STATE_OFF:
            self._state = STATE_OFF
        else:
            self._state = STATE_ON

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
        if sensor_action == ACTION_REFRESH_ALL or sensor_action == ACTION_REFRESH_META:
            await self._update_meta(evt_id)
            await self._update_data(evt_id)
        elif sensor_action == ACTION_CLEAR:
            await self._clear_all_data(evt_id)

        _LOGGER.debug("number of items in playlist : %s", str(len(self._data)))
        self.schedule_update_ha_state()

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
            await self._goto(playerid, to)
        elif method == "remove":
            item = kwargs.get("item")
            playlistid = item.get("playlistid")
            position = item.get("position")
            await self._remove(playlistid, position)

    async def _remove(self, playlistid, position):
        await self.call_method_kodi_no_result(
            "Playlist.Remove", {"playlistid": playlistid, "position": position}
        )
        # updating data is needed as there is no event fired by kodi
        await self._update_meta("remove event")
        await self._update_data("remove event")
        self.schedule_update_ha_state()

    async def _goto(self, playerid, to):
        await self.call_method_kodi_no_result(
            "Player.GoTo", {"playerid": playerid, "to": to}
        )

    async def async_update(self) -> None:
        """This update is ony used to trigger events so the frontend can be updated. But nothing will happen with this method as no polling is required, but every data change occur when kodi sends events."""
        _LOGGER.debug("> Update Playlist sensor")

        # this piece of code is used to initialize the meta and data when the sensor starts for the first time and kodi is not off (and thus the sensor neither as the state is set in the constructor based on the state of kodi)
        if self._state != STATE_OFF and len(self._meta) == 0:
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
                player, []
            )
            if props_item_playing.get("id") is not None:
                self.add_meta("currently_playing", props_item_playing["id"])
                _LOGGER.debug("Currently playing %s", str(props_item_playing["id"]))
            else:
                _LOGGER.info("No id defined for this item")
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
