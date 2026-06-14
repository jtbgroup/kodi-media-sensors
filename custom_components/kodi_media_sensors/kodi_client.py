"""Shared helper to call Kodi JSON-RPC methods via the core integration.

Instead of using the `kodi.call_method` action (which delivers results
asynchronously via a `kodi_call_method_result` event on the global
event bus -- a poor fit for large payloads, as it gets broadcast to
every listener and the Recorder logs warnings once it exceeds 32KB),
this module calls the underlying `pykodi.Kodi` client directly.

That client is exposed by the core Kodi integration as
`config_entry.runtime_data.kodi`, and its `call_method` coroutine
returns the JSON-RPC result directly -- no event bus involved.

This is an internal implementation detail of the core Kodi
integration and is not part of its public API. If a future Home
Assistant release changes this structure, `_async_get_kodi_client`
is the single place that needs updating.
"""
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

_LOGGER = logging.getLogger(__name__)


def _async_get_kodi_client(hass: HomeAssistant, entity_id: str):
    """Return the pykodi.Kodi client backing the given media_player entity.

    Returns None if the entity, its config entry, or the runtime data
    is not found (e.g. the core Kodi integration is not loaded, or its
    internal structure has changed).
    """
    entity_registry = er.async_get(hass)
    entity_entry = entity_registry.async_get(entity_id)
    if entity_entry is None or entity_entry.config_entry_id is None:
        _LOGGER.error("No config entry found for entity %s", entity_id)
        return None

    config_entry = hass.config_entries.async_get_entry(entity_entry.config_entry_id)
    if config_entry is None:
        _LOGGER.error(
            "Config entry %s not found for entity %s",
            entity_entry.config_entry_id,
            entity_id,
        )
        return None

    runtime_data = getattr(config_entry, "runtime_data", None)
    kodi_client = getattr(runtime_data, "kodi", None)
    if kodi_client is None:
        _LOGGER.error(
            "Could not access the Kodi client for entity %s "
            "(core Kodi integration internals may have changed)",
            entity_id,
        )
        return None

    return kodi_client


async def async_call_method(
    hass: HomeAssistant,
    entity_id: str,
    method: str,
    **params,
) -> dict | None:
    """Call a Kodi JSON-RPC method and return its result directly.

    Returns the JSON-RPC `result` dict from Kodi, or None on error
    (entity/client not found, or the JSON-RPC call itself failed).
    """
    kodi_client = _async_get_kodi_client(hass, entity_id)
    if kodi_client is None:
        return None

    try:
        result = await kodi_client.call_method(method, **params)
    except Exception as err:  # noqa: BLE001 - any JSON-RPC/connection error
        _LOGGER.error("Error calling %s for %s: %s", method, entity_id, err)
        return None

    _LOGGER.debug("Result of %s for %s: %r", method, entity_id, result)
    return result