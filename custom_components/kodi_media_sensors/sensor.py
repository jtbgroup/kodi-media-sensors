import logging
import time
from datetime import timedelta

from homeassistant import config_entries, core
from homeassistant.core import callback
from homeassistant.helpers import entity_registry, entity_platform
from homeassistant.components.kodi.const import DATA_KODI, DOMAIN as KODI_DOMAIN
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import CONF_HOST
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

from .const import (
    OPTION_HIDE_WATCHED,
    OPTION_USE_AUTH_URL,
    DOMAIN,
    KODI_DOMAIN_PLATFORM,
    CONF_SENSOR_RECENTLY_ADDED_TVSHOW,
    CONF_SENSOR_RECENTLY_ADDED_MOVIE,
    CONF_SENSOR_PLAYLIST,
    CONF_SENSOR_SEARCH,
    CONF_KODI_INSTANCE,
    ATTR_METHOD,
)
from .entities import (
    KodiRecentlyAddedMoviesEntity,
    KodiRecentlyAddedTVEntity,
    KodiPlaylistEntity,
)
from .entity_kodi_search import KodiSearchEntity
from .utils import (
    find_matching_config_entry,
    find_matching_config_entry_for_host,
)

PLATFORM_SCHEMA = vol.Any(
    PLATFORM_SCHEMA.extend(
        {
            vol.Required(CONF_HOST): cv.string,
            vol.Optional(OPTION_HIDE_WATCHED, default=False): bool,
            vol.Optional(OPTION_USE_AUTH_URL, default=False): bool,
        }
    ),
)

KODI_MEDIA_SENSOR_CALL_METHOD_SCHEMA = cv.make_entity_service_schema(
    {vol.Required(ATTR_METHOD): cv.string}, extra=vol.ALLOW_EXTRA
)


SCAN_INTERVAL = timedelta(minutes=10)
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities,
):
    """Setup sensors from a config entry created in the integrations UI."""
    _hass = hass
    conf = hass.data[DOMAIN][config_entry.entry_id]
    kodi_config_entry = find_matching_config_entry(hass, conf[CONF_KODI_INSTANCE])
    reg = await hass.helpers.entity_registry.async_get_registry()

    key = kodi_config_entry.unique_id
    if key == None:
        key = kodi_config_entry.entry_id

    kodi_entity_id = reg.async_get_entity_id(KODI_DOMAIN_PLATFORM, KODI_DOMAIN, key)

    try:
        data = hass.data[KODI_DOMAIN][conf[CONF_KODI_INSTANCE]]
    except KeyError:
        config_entries = [
            entry.as_dict() for entry in hass.config_entries.async_entries(KODI_DOMAIN)
        ]
        _LOGGER.error(
            "Failed to setup sensor. Could not find kodi data from existing config entries: %s",
            config_entries,
        )
        return

    kodi = data[DATA_KODI]
    sensorsList = list()

    if conf.get(CONF_SENSOR_RECENTLY_ADDED_TVSHOW):
        tv_entity = KodiRecentlyAddedTVEntity(
            kodi,
            kodi_config_entry.data,
            hide_watched=conf.get(OPTION_HIDE_WATCHED, False),
            use_auth_url=conf.get(OPTION_USE_AUTH_URL, False),
        )
        sensorsList.append(tv_entity)

    if conf.get(CONF_SENSOR_RECENTLY_ADDED_MOVIE):
        movies_entity = KodiRecentlyAddedMoviesEntity(
            kodi,
            kodi_config_entry.data,
            hide_watched=conf.get(OPTION_HIDE_WATCHED, False),
            use_auth_url=conf.get(OPTION_USE_AUTH_URL, False),
        )
        sensorsList.append(movies_entity)

    if conf.get(CONF_SENSOR_PLAYLIST):
        playlist_entity = KodiPlaylistEntity(
            kodi,
            kodi_config_entry.data,
            kodi_entity_id,
            hide_watched=conf.get(OPTION_HIDE_WATCHED, False),
            use_auth_url=conf.get(OPTION_USE_AUTH_URL, False),
        )
        sensorsList.append(playlist_entity)

    if conf.get(CONF_SENSOR_SEARCH):
        search_entity = KodiSearchEntity(kodi, kodi_config_entry.data, kodi_entity_id)
        sensorsList.append(search_entity)

    async_add_entities(sensorsList, update_before_add=True)

    # @callback
    # async def template_bsensor_state_listener(event):
    #     """Called when the target device changes state."""

    #     sensor_name = "sensor." + playlist_entity.name
    #     old_datas = str(playlist_entity.device_state_attributes.get("data"))
    #     old_state = playlist_entity.state

    #     await playlist_entity.async_update()
    #     time.sleep(2)

    #     new_datas = str(playlist_entity.device_state_attributes.get("data"))
    #     new_state = playlist_entity.state

    #     # if event.data.get("old_state"):
    #     #     old_state = str(event.data.get("old_state").state)
    #     #     new_state = str(event.data.get("new_state").state)
    #     #     if old_state == "playing" and new_state == "playing":
    #     #         await playlist_entity.async_update()
    #     # datas = str(playlist_entity.device_state_attributes.get("data"))

    #     hass.bus.fire(
    #         "state_changed",
    #         {
    #             "entity_id": sensor_name,
    #             "old_state": {
    #                 "entity_id": sensor_name,
    #                 "state": old_state,
    #                 "attributes": {
    #                     "data": old_datas,
    #                     "friendly_name": playlist_entity.name,
    #                 },
    #             },
    #             "new_state": {
    #                 "entity_id": sensor_name,
    #                 "state": new_state,
    #                 "attributes": {
    #                     "data": new_datas,
    #                     "friendly_name": playlist_entity.name,
    #                 },
    #             },
    #         },
    #     )

    # hass.helpers.event.async_track_state_change_event(
    #     kodi_entity_id, template_bsensor_state_listener
    # )

    platform = entity_platform.current_platform.get()
    # async_add_entities(sensorsList, update_before_add=True)
    # # register services
    #     (
    #     "call_method",
    #     {
    #         {vol.Required(ATTR_METHOD): cv.string}, extra=vol.ALLOW_EXTRA
    #     },
    #     "asyn_call_method",
    # )
    platform.async_register_entity_service(
        "call_method", KODI_MEDIA_SENSOR_CALL_METHOD_SCHEMA, "async_call_method"
    )


async def async_setup_platform(
    hass: core.HomeAssistant, config: dict, async_add_entities, discovery_info=None
) -> None:
    """Setup sensors from yaml configuration."""
    host = config[CONF_HOST]
    hide_watched = config[OPTION_HIDE_WATCHED]
    use_auth_url = config[OPTION_USE_AUTH_URL]
    config_entry = find_matching_config_entry_for_host(hass, host)
    if config_entry is None:
        hosts = [
            entry.data["host"]
            for entry in hass.config_entries.async_entries(KODI_DOMAIN)
        ]
        _LOGGER.error(
            "Failed to setup sensor. Could not find config entry for kodi host `%s` from configured hosts: %s",
            host,
            hosts,
        )
        return

    try:
        data = hass.data[KODI_DOMAIN][config_entry.entry_id]
    except KeyError:
        config_entries = [
            entry.as_dict() for entry in hass.config_entries.async_entries(KODI_DOMAIN)
        ]
        _LOGGER.error(
            "Failed to setup sensor. Could not find kodi data from existing config entries: %s",
            config_entries,
        )
        return
    kodi = data[DATA_KODI]

    tv_entity = KodiRecentlyAddedTVEntity(
        kodi, config_entry.data, hide_watched, use_auth_url
    )
    movies_entity = KodiRecentlyAddedMoviesEntity(
        kodi, config_entry.data, hide_watched, use_auth_url
    )
    playlist_entity = KodiPlaylistEntity(
        kodi, config_entry.data, hide_watched, use_auth_url
    )

    search_entity = KodiSearchEntity(kodi, kodi_entity_id)
    # Added the auto scan before adding he sensors
    async_add_entities(
        [tv_entity, movies_entity, playlist_entity],
        search_entity,
        update_before_add=True,
    )
