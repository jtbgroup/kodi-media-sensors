"""Support for Kodi config sensors."""
from __future__ import annotations

import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import DiscoveryInfoType

from .const import DOMAIN, CONF_KODI_ENTITY

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Configuration des entités sensor pour Kodi."""
    async_add_entities([KodiConfigSensor(entry)], True)

class KodiConfigSensor(SensorEntity):
    """Entité utilisée pour exposer la configuration Kodi au Frontend."""

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialisation."""
        self._entry = entry
        self._attr_name = f"Kodi Config {entry.title}"
        self._attr_unique_id = f"{entry.entry_id}_config"
        self._attr_icon = "mdi:kodi"
        
    @property
    def state(self) -> str:
        """État du sensor (indique que la config est active)."""
        return "ready"

    @property
    def extra_state_attributes(self) -> dict:
        """Expose l'entry_id et l'entité Kodi cible aux attributs."""
        kodi_entity = self._entry.data.get(CONF_KODI_ENTITY)
        
        return {
            "config_entry_id": self._entry.entry_id,
            "kodi_entity_id": kodi_entity,
        }