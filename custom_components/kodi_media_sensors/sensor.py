"""Support for Kodi config sensors."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .const import DOMAIN, CONF_KODI_ENTITY
from .kodi_client import async_call_method

_LOGGER = logging.getLogger(__name__)



async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Configuration des entités sensor pour Kodi."""
    async_add_entities([KodiConfigSensor(hass, entry)], True)


class KodiConfigSensor(SensorEntity):
    """Entité qui track l'état dynamique du Kodi configuré."""

    _attr_icon = "mdi:kodi"
    _unsubscribe_state_change: callable | None = None

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialisation."""
        self._hass = hass
        self._entry = entry
        self._kodi_entity_id = entry.data.get(CONF_KODI_ENTITY)
        
        self._attr_name = f"Kodi {entry.title}"
        self._attr_unique_id = f"{entry.entry_id}_state"
        self._attr_state = "unavailable"
        self._current_track: dict[str, Any] | None = None

    async def async_added_to_hass(self) -> None:
        """Subscribe to Kodi entity state changes when sensor is added."""
        await super().async_added_to_hass()
        
        if not self._kodi_entity_id:
            _LOGGER.error("No Kodi entity configured for sensor %s", self.unique_id)
            return

        # S'abonner aux changements d'état du Kodi
        self._unsubscribe_state_change = async_track_state_change_event(
            self._hass,
            [self._kodi_entity_id],
            self._async_on_kodi_state_change,
        )

        # Récupérer l'état initial
        state = self._hass.states.get(self._kodi_entity_id)
        if state:
            self._attr_state = state.state
            await self._async_update_current_track()
        else:
            self._attr_state = "unavailable"

        self.async_write_ha_state()
        _LOGGER.debug("Kodi sensor %s subscribed to %s", self.unique_id, self._kodi_entity_id)

    async def async_will_remove_from_hass(self) -> None:
        """Unsubscribe from state changes when sensor is removed."""
        if self._unsubscribe_state_change:
            self._unsubscribe_state_change()
        await super().async_will_remove_from_hass()

    @callback
    def _async_on_kodi_state_change(self, event) -> None:
        """Handle Kodi entity state changes."""
        new_state = event.data.get("new_state")
        
        if new_state:
            self._attr_state = new_state.state
            # Mettre à jour le current_track de manière asynchrone
            self._hass.async_create_task(self._async_update_current_track())
            self.async_write_ha_state()
            _LOGGER.debug("Kodi sensor %s state updated to %s", self.unique_id, self._attr_state)

    async def _async_update_current_track(self) -> None:
        """Fetch the current playing item's ID and type only.
    
        ID is the unique identifier in Kodi (songid, movieid, episodeid, etc).
        """
        if self._attr_state in ("unavailable", "off", "idle"):
            self._current_track = None
            return

        try:
            # 1. Récupérer le player actif
            result = await async_call_method(
                self._hass,
                self._kodi_entity_id,
                "Player.GetActivePlayers",
            )
            
            if not result:
                self._current_track = None
                return

            player_id = result[0].get("playerid")
            if player_id is None:
                self._current_track = None
                return

            # 2. Récupérer l'item courant avec tous les IDs possibles
            item_result = await async_call_method(
                self._hass,
                self._kodi_entity_id,
                "Player.GetItem",
                playerid=player_id,
                properties=["artistid"],
            )

            if item_result and "item" in item_result:
                item = item_result["item"]
                item_type = item.get("type")
                item_id = item.get("id")
                raw_artist_id = item.get("artistid")
                artist_id = None
                
                # Si c'est une liste et qu'elle n'est pas vide, on prend le premier (index 0)
                if isinstance(raw_artist_id, list) and raw_artist_id:
                    artist_id = raw_artist_id[0]
                # S'il y a une valeur mais que ce n'est bizarrement pas une liste
                elif raw_artist_id is not None and not isinstance(raw_artist_id, list):
                    artist_id = raw_artist_id
                        
                if item_id is not None:
                    # 1. Base obligatoire
                    self._current_track = {
                        "id": item_id,      
                        "type": item_type,
                    }
                    
                    # 2. Ajout de l'artist_id seulement s'il a été trouvé
                    if artist_id is not None:
                        self._current_track["artist_id"] = artist_id
                    else:
                        self._current_track = None

        except Exception as err:
            _LOGGER.debug("Error updating current track: %s", err)
            self._current_track = None

    @property
    def state(self) -> str:
        """État du sensor = état du Kodi."""
        return self._attr_state

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose config entry info et current track."""
        attrs = {
            "config_entry_id": self._entry.entry_id,
            "kodi_entity_id": self._kodi_entity_id,
        }
        
        if self._current_track:
            attrs["current_track"] = self._current_track
        
        return attrs