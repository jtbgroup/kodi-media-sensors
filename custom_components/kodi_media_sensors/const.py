DOMAIN = "kodi_media_sensors"
CONF_LABEL = "label"
CONF_KODI_ENTITY = "kodi_entity_id"

# Kodi service (core integration) used to call JSON-RPC methods
KODI_DOMAIN = "kodi"
SERVICE_CALL_METHOD = "call_method"

# Default Kodi playlist (0 = audio playlist, see Playlist.GetPlaylists)
DEFAULT_PLAYLIST_ID = 0

KODI_STATE_IDLE = "idle"
KODI_STATE_ON = "on"
KODI_STATE_OFF = "off"
KODI_STATE_PAUSE = "pause"
KODI_STATE_UNAVAILABLE = "unavailable"
KODI_STATES = {
    KODI_STATE_IDLE,
    KODI_STATE_OFF,
    KODI_STATE_ON,
    KODI_STATE_PAUSE,
    KODI_STATE_UNAVAILABLE,
}
KODI_PLAYLIST_ID_VIDEO = 1
KODI_PLAYLIST_ID_AUDIO = 0
