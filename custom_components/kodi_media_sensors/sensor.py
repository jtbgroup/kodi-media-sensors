from datetime import timedelta
import logging

from homeassistant import config_entries, core
from homeassistant.components.kodi.const import DOMAIN as KODI_DOMAIN
from homeassistant.helpers import entity_platform
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_registry import async_get
import voluptuous as vol

from .const import (
    ATTR_METHOD,
    CONF_KODI_INSTANCE,
    CONF_SENSOR_PLAYLIST,
    CONF_SENSOR_RECENTLY_ADDED_MOVIE,
    CONF_SENSOR_RECENTLY_ADDED_TVSHOW,
    CONF_SENSOR_SEARCH,
    DEFAULT_OPTION_SEARCH_ALBUMS_LIMIT,
    DEFAULT_OPTION_SEARCH_ARTISTS_LIMIT,
    DEFAULT_OPTION_SEARCH_CHANNELS_RADIO_LIMIT,
    DEFAULT_OPTION_SEARCH_CHANNELS_TV_LIMIT,
    DEFAULT_OPTION_SEARCH_EPISODES_LIMIT,
    DEFAULT_OPTION_SEARCH_KEEP_ALIVE_TIMER,
    DEFAULT_OPTION_SEARCH_MOVIES_LIMIT,
    DEFAULT_OPTION_SEARCH_MUSIC_PLAYLISTS_LIMIT,
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
    DOMAIN,
    KODI_DOMAIN_PLATFORM,
    OPTION_HIDE_WATCHED,
    OPTION_SEARCH_ALBUMS_LIMIT,
    OPTION_SEARCH_ARTISTS_LIMIT,
    OPTION_SEARCH_CHANNELS_RADIO_LIMIT,
    OPTION_SEARCH_CHANNELS_TV_LIMIT,
    OPTION_SEARCH_EPISODES_LIMIT,
    OPTION_SEARCH_KEEP_ALIVE_TIMER,
    OPTION_SEARCH_MOVIES_LIMIT,
    OPTION_SEARCH_MUSIC_PLAYLISTS_LIMIT,
    OPTION_SEARCH_MUSICVIDEOS_LIMIT,
    OPTION_SEARCH_RECENTLY_ADDED_ALBUMS_LIMIT,
    OPTION_SEARCH_RECENTLY_ADDED_EPISODES_LIMIT,
    OPTION_SEARCH_RECENTLY_ADDED_MOVIES_LIMIT,
    OPTION_SEARCH_RECENTLY_ADDED_MUSICVIDEOS_LIMIT,
    OPTION_SEARCH_RECENTLY_ADDED_SONGS_LIMIT,
    OPTION_SEARCH_RECENTLY_PLAYED_ALBUMS_LIMIT,
    OPTION_SEARCH_RECENTLY_PLAYED_SONGS_LIMIT,
    OPTION_SEARCH_SONGS_LIMIT,
    OPTION_SEARCH_TVSHOWS_LIMIT,
)
from .entities import KodiRecentlyAddedMoviesEntity, KodiRecentlyAddedTVEntity
from .entity_kodi_media_sensor_playlist import KodiMediaSensorsPlaylistEntity
from .entity_kodi_media_sensor_search import KodiMediaSensorsSearchEntity
from .media_sensor_event_manager import MediaSensorEventManager
from .utils import find_matching_config_entry

KODI_MEDIA_SENSOR_CALL_METHOD_SCHEMA = cv.make_entity_service_schema(
    {vol.Required(ATTR_METHOD): cv.string}, extra=vol.ALLOW_EXTRA
)


SCAN_INTERVAL = timedelta(seconds=300)
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities,
):
    conf = hass.data[DOMAIN][config_entry.entry_id]
    kodi_config_entry = find_matching_config_entry(hass, conf[CONF_KODI_INSTANCE])
    reg = async_get(hass)

    key = kodi_config_entry.unique_id
    if key is None:
        key = kodi_config_entry.entry_id

    kodi_entity_id = reg.async_get_entity_id(KODI_DOMAIN_PLATFORM, KODI_DOMAIN, key)

    media_player_component = hass.data.get("media_player")
    if media_player_component:
        entities = media_player_component.entities  # set of Entity
        for entity in entities:
            _LOGGER.info("Entity id: %s, state: %s", entity.entity_id, entity.state)
            kodi = None
            if kodi_entity_id == entity.entity_id:
                kodi = entity._kodi
                break

    # try:
    #     data = hass.data[KODI_DOMAIN][conf[CONF_KODI_INSTANCE]]
    # except KeyError:
    #     config_entries = [
    #         entry.as_dict() for entry in hass.config_entries.async_entries(KODI_DOMAIN)
    #     ]
    #     _LOGGER.error(
    #         "Failed to setup sensor. Could not find kodi data from existing config entries: %s",
    #         config_entries,
    #     )
    #     return

    # kodi = mp[kodi_entity_id]

    sensorsList = list()
    event_manager = MediaSensorEventManager()

    if conf.get(CONF_SENSOR_RECENTLY_ADDED_TVSHOW):
        tv_entity = KodiRecentlyAddedTVEntity(
            config_entry.entry_id,
            hass,
            kodi,
            kodi_entity_id,
            kodi_config_entry.data,
            hide_watched=conf.get(OPTION_HIDE_WATCHED, False),
        )
        sensorsList.append(tv_entity)

    if conf.get(CONF_SENSOR_RECENTLY_ADDED_MOVIE):
        movies_entity = KodiRecentlyAddedMoviesEntity(
            config_entry.entry_id,
            hass,
            kodi,
            kodi_entity_id,
            kodi_config_entry.data,
            hide_watched=conf.get(OPTION_HIDE_WATCHED, False),
        )
        sensorsList.append(movies_entity)

    if conf.get(CONF_SENSOR_PLAYLIST):
        playlist_entity = KodiMediaSensorsPlaylistEntity(
            config_entry.entry_id,
            hass,
            kodi,
            kodi_entity_id,
            kodi_config_entry.data,
            event_manager,
        )
        sensorsList.append(playlist_entity)

    if conf.get(CONF_SENSOR_SEARCH):
        search_entity = KodiMediaSensorsSearchEntity(
            config_entry.entry_id,
            hass,
            kodi,
            kodi_entity_id,
            kodi_config_entry.data,
            event_manager,
        )
        search_entity.set_search_songs_limit(
            conf.get(OPTION_SEARCH_SONGS_LIMIT, DEFAULT_OPTION_SEARCH_SONGS_LIMIT)
        )
        search_entity.set_search_albums_limit(
            conf.get(OPTION_SEARCH_ALBUMS_LIMIT, DEFAULT_OPTION_SEARCH_ALBUMS_LIMIT)
        )
        search_entity.set_search_artists_limit(
            conf.get(OPTION_SEARCH_ARTISTS_LIMIT, DEFAULT_OPTION_SEARCH_ARTISTS_LIMIT)
        )
        search_entity.set_search_musicvideos_limit(
            conf.get(
                OPTION_SEARCH_MUSICVIDEOS_LIMIT, DEFAULT_OPTION_SEARCH_MUSICVIDEOS_LIMIT
            )
        )
        search_entity.set_search_movies_limit(
            conf.get(OPTION_SEARCH_MOVIES_LIMIT, DEFAULT_OPTION_SEARCH_MOVIES_LIMIT)
        )
        search_entity.set_search_tvshows_limit(
            conf.get(OPTION_SEARCH_TVSHOWS_LIMIT, DEFAULT_OPTION_SEARCH_TVSHOWS_LIMIT)
        )
        search_entity.set_search_episodes_limit(
            conf.get(OPTION_SEARCH_EPISODES_LIMIT, DEFAULT_OPTION_SEARCH_EPISODES_LIMIT)
        )
        search_entity.set_search_channels_tv_limit(
            conf.get(
                OPTION_SEARCH_CHANNELS_TV_LIMIT, DEFAULT_OPTION_SEARCH_CHANNELS_TV_LIMIT
            )
        )
        search_entity.set_search_channels_radio_limit(
            conf.get(
                OPTION_SEARCH_CHANNELS_RADIO_LIMIT,
                DEFAULT_OPTION_SEARCH_CHANNELS_RADIO_LIMIT,
            )
        )

        search_entity.set_search_music_playlists_limit(
            conf.get(
                OPTION_SEARCH_MUSIC_PLAYLISTS_LIMIT,
                DEFAULT_OPTION_SEARCH_MUSIC_PLAYLISTS_LIMIT,
            )
        )

        search_entity.set_search_recently_played_songs_limit(
            conf.get(
                OPTION_SEARCH_RECENTLY_PLAYED_SONGS_LIMIT,
                DEFAULT_OPTION_SEARCH_RECENTLY_PLAYED_SONGS_LIMIT,
            )
        )
        search_entity.set_search_recently_played_albums_limit(
            conf.get(
                OPTION_SEARCH_RECENTLY_PLAYED_ALBUMS_LIMIT,
                DEFAULT_OPTION_SEARCH_RECENTLY_PLAYED_ALBUMS_LIMIT,
            )
        )
        search_entity.set_search_recently_added_songs_limit(
            conf.get(
                OPTION_SEARCH_RECENTLY_ADDED_SONGS_LIMIT,
                DEFAULT_OPTION_SEARCH_RECENTLY_ADDED_SONGS_LIMIT,
            )
        )
        search_entity.set_search_recently_added_albums_limit(
            conf.get(
                OPTION_SEARCH_RECENTLY_ADDED_ALBUMS_LIMIT,
                DEFAULT_OPTION_SEARCH_RECENTLY_ADDED_ALBUMS_LIMIT,
            )
        )
        search_entity.set_search_recently_added_movies_limit(
            conf.get(
                OPTION_SEARCH_RECENTLY_ADDED_MOVIES_LIMIT,
                DEFAULT_OPTION_SEARCH_RECENTLY_ADDED_MOVIES_LIMIT,
            )
        )

        search_entity.set_search_recently_added_musicvideos_limit(
            conf.get(
                OPTION_SEARCH_RECENTLY_ADDED_MUSICVIDEOS_LIMIT,
                DEFAULT_OPTION_SEARCH_RECENTLY_ADDED_MUSICVIDEOS_LIMIT,
            )
        )
        search_entity.set_search_recently_added_episodes_limit(
            conf.get(
                OPTION_SEARCH_RECENTLY_ADDED_EPISODES_LIMIT,
                DEFAULT_OPTION_SEARCH_RECENTLY_ADDED_EPISODES_LIMIT,
            )
        )
        search_entity.set_search_keep_alive_timer(
            conf.get(
                OPTION_SEARCH_KEEP_ALIVE_TIMER, DEFAULT_OPTION_SEARCH_KEEP_ALIVE_TIMER
            )
        )
        sensorsList.append(search_entity)

    async_add_entities(sensorsList, update_before_add=True)

    # Register the services
    platform = entity_platform.current_platform.get()
    platform.async_register_entity_service(
        "call_method", KODI_MEDIA_SENSOR_CALL_METHOD_SCHEMA, "async_call_method"
    )


async def async_setup_platform(
    hass: core.HomeAssistant, config: dict, async_add_entities, discovery_info=None
) -> None:
    """Setup sensors from yaml configuration."""

    _LOGGER.warning("Configuration using yaml files is not supported")
