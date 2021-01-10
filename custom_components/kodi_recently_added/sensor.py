import logging

from homeassistant import config_entries, core
from homeassistant.helpers import entity_registry
from homeassistant.components.kodi.const import DATA_KODI, DOMAIN as KODI_DOMAIN
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import CONF_HOST
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

from .const import CONF_HIDE_WATCHED, DOMAIN, KODI_DOMAIN_PLATFORM
from .entities import (
    KodiRecentlyAddedMoviesEntity,
    KodiRecentlyAddedTVEntity,
    KodiPlaylistEntity,
)
from .utils import (
    find_matching_config_entry,
    find_matching_config_entry_for_host,
)

PLATFORM_SCHEMA = vol.Any(
    PLATFORM_SCHEMA.extend(
        {
            vol.Required(CONF_HOST): cv.string,
            vol.Optional(CONF_HIDE_WATCHED, default=False): bool,
        }
    ),
)
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities,
):
    """Setup sensors from a config entry created in the integrations UI."""
    conf = hass.data[DOMAIN][config_entry.entry_id]
    kodi_config_entry = find_matching_config_entry(hass, conf["kodi_config_entry_id"])
    reg = await hass.helpers.entity_registry.async_get_registry()
    kodi_entity_id = reg.async_get_entity_id(
        KODI_DOMAIN_PLATFORM, KODI_DOMAIN, kodi_config_entry.entry_id
    )

    try:
        data = hass.data[KODI_DOMAIN][conf["kodi_config_entry_id"]]
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
        kodi, kodi_config_entry.data, hide_watched=conf.get(CONF_HIDE_WATCHED, False)
    )
    movies_entity = KodiRecentlyAddedMoviesEntity(
        kodi, kodi_config_entry.data, hide_watched=conf.get(CONF_HIDE_WATCHED, False)
    )
    playlist_entity = KodiPlaylistEntity(
        kodi,
        kodi_config_entry.data,
        kodi_entity_id,
        hide_watched=conf.get(CONF_HIDE_WATCHED, False),
    )
    async_add_entities(
        [tv_entity, movies_entity, playlist_entity], update_before_add=True
    )


async def async_setup_platform(
    hass: core.HomeAssistant, config: dict, async_add_entities, discovery_info=None
) -> None:
    """Setup sensors from yaml configuration."""
    host = config[CONF_HOST]
    hide_watched = config[CONF_HIDE_WATCHED]
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

    tv_entity = KodiRecentlyAddedTVEntity(kodi, config_entry.data, hide_watched)
    movies_entity = KodiRecentlyAddedMoviesEntity(kodi, config_entry.data, hide_watched)
    playlist_entity = KodiPlaylistEntity(kodi, config_entry.data, hide_watched)
    # Added the auto scan before adding he sensors
    async_add_entities(
        [tv_entity, movies_entity, playlist_entity], update_before_add=True
    )
