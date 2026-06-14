
import voluptuous as vol
from homeassistant.components import websocket_api

@websocket_api.websocket_command({
    vol.Required("type"): "kodi_media_sensors/search",
    vol.Required("entry_id"): str,
    vol.Required("query"): str,
    vol.Optional("category", default="all"): vol.In(
        ["all", "movies", "tvshows", "songs", "albums", "artists"]
    ),
})
@websocket_api.async_response
async def websocket_search(hass, connection, msg) -> None:
    ...
    results = await _async_search(hass, entity_id, msg["query"], msg["category"])
    connection.send_result(msg["id"], {"results": results})