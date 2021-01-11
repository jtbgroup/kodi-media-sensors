from typing import Optional

from homeassistant import config_entries, core
from homeassistant.components.kodi.const import DOMAIN as KODI_DOMAIN
from homeassistant.const import CONF_HOST


def find_matching_config_entry(
    hass: core.HomeAssistant, entry_id: str
) -> Optional[config_entries.ConfigEntry]:
    """Search existing config entries for one matching the entry_id."""
    for entry in hass.config_entries.async_entries(KODI_DOMAIN):
        # Skip any entry whose source is marked as ignored.
        if entry.entry_id == entry_id and entry.source != "ignore":
            return entry
    return None


def find_matching_config_entry_for_host(
    hass: core.HomeAssistant, host: str
) -> Optional[config_entries.ConfigEntry]:
    """Search existing config entries for one matching the host."""
    for entry in hass.config_entries.async_entries(KODI_DOMAIN):
        # Skip any entry whose source is marked as ignored.
        if entry.data.get(CONF_HOST) == host and entry.source != "ignore":
            return entry
    return None
