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
    OPTION_SEARCH_LIMIT,
    OPTION_SEARCH_LIMIT_DEFAULT_VALUE,
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
)
from .entity_kodi_search import KodiSearchEntity
from .entity_kodi_playlist import KodiPlaylistEntity
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
            vol.Optional(
                OPTION_SEARCH_LIMIT, default=OPTION_SEARCH_LIMIT_DEFAULT_VALUE
            ): int,
        }
    ),
)

KODI_MEDIA_SENSOR_CALL_METHOD_SCHEMA = cv.make_entity_service_schema(
    {vol.Required(ATTR_METHOD): cv.string}, extra=vol.ALLOW_EXTRA
)


SCAN_INTERVAL = timedelta(minutes=3)
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
        )
        sensorsList.append(tv_entity)

    if conf.get(CONF_SENSOR_RECENTLY_ADDED_MOVIE):
        movies_entity = KodiRecentlyAddedMoviesEntity(
            kodi,
            kodi_config_entry.data,
            hide_watched=conf.get(OPTION_HIDE_WATCHED, False),
        )
        sensorsList.append(movies_entity)

    if conf.get(CONF_SENSOR_PLAYLIST):
        playlist_entity = KodiPlaylistEntity(
            hass,
            kodi,
            kodi_entity_id,
            kodi_config_entry.data,
            use_auth_url=conf.get(OPTION_USE_AUTH_URL, False),
        )
        sensorsList.append(playlist_entity)

    if conf.get(CONF_SENSOR_SEARCH):
        search_entity = KodiSearchEntity(
            hass,
            kodi,
            kodi_config_entry.data,
            search_limit=conf.get(
                OPTION_SEARCH_LIMIT, OPTION_SEARCH_LIMIT_DEFAULT_VALUE
            ),
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
