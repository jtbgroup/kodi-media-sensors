import logging
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from .const import DOMAIN, CONF_LABEL

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Setup via configuration.yaml — non utilisé, mais requis."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Chargement de l'intégration via l'UI."""

    label = entry.data.get(CONF_LABEL, "inconnu")
    _LOGGER.info("Kodi Media Sensors démarré — label: '%s'", label)

    # Stockage des données de config pour usage ultérieur
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "label": label,
    }

    # ⚠️ IMPORTANT: Enregistrer le WebSocket SANS attendre
    # Il doit être enregistré au niveau du domaine, pas de l'entry
    _async_setup_websocket(hass)
    _LOGGER.info("WebSocket kodi_media_sensors/subscribe enregistré.")

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Nettoyage lors de la suppression de l'intégration."""
    hass.data[DOMAIN].pop(entry.entry_id, None)
    _LOGGER.info("Kodi Media Sensors déchargé.")
    return True


def _async_setup_websocket(hass: HomeAssistant) -> None:
    """Enregistrer les WebSocket commands.
    
    Appelé depuis async_setup_entry pour s'assurer que c'est fait
    avant que le client ne se connecte.
    """
    # Import local pour éviter les dépendances circulaires
    from .websocket import async_register_websockets
    
    # Cette fonction utilise @callback et doit être appelée synchrone
    async_register_websockets(hass)