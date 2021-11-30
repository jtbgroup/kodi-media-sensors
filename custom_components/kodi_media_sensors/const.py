DOMAIN = "kodi_media_sensors"
KODI_DOMAIN_PLATFORM = "media_player"

# Configuration of the integration
CONF_SENSOR_RECENTLY_ADDED_TVSHOW = "sensor_recently_added_tvshow"
CONF_SENSOR_RECENTLY_ADDED_MOVIE = "sensor_recently_added_movie"
CONF_SENSOR_PLAYLIST = "sensor_playlist"
CONF_SENSOR_SEARCH = "sensor_search"
CONF_KODI_INSTANCE = "kodi_config_entry_id"

OPTION_HIDE_WATCHED = "hide_watched"
OPTION_SEARCH_LIMIT = "search_limit"
OPTION_SEARCH_LIMIT_DEFAULT_VALUE = 15

# Entities name and ID
ENTITY_SENSOR_RECENTLY_ADDED_TVSHOW = "kodi_media_sensor_recently_added_tvshow"
ENTITY_SENSOR_RECENTLY_ADDED_MOVIE = "kodi_media_sensor_recently_added_movie"
ENTITY_SENSOR_PLAYLIST = "kodi_media_sensor_playlist"
ENTITY_SENSOR_SEARCH = "kodi_media_sensor_search"
ENTITY_NAME_SENSOR_RECENTLY_ADDED_TVSHOW = (
    "Kodi Media Sensor Recently Added TV Episodes"
)
ENTITY_NAME_SENSOR_RECENTLY_ADDED_MOVIE = "Kodi Media Sensor Recently Added Movies"
ENTITY_NAME_SENSOR_PLAYLIST = "Kodi Media Sensor Playlist"
ENTITY_NAME_SENSOR_SEARCH = "Kodi Media Sensor Search"

# Service method
ATTR_METHOD = "method"

# Kodi keys returned in the aswer
KEY_ADDONS = "addons"
KEY_ALBUMS = "albums"
KEY_ALBUM_DETAILS = "albumdetails"
KEY_ARTISTS = "artists"
KEY_CHANNELS = "channels"
KEY_EPISODES = "episodes"
KEY_MOVIES = "movies"
KEY_SEASONS = "seasons"
KEY_SEASON_DETAILS = "seasondetails"
KEY_SONGS = "songs"
KEY_TVSHOWS = "tvshows"
KEY_TVSHOW_DETAILS = "tvshowdetails"
KEY_ITEMS = "items"
KEYS = {
    KEY_ADDONS,
    KEY_ALBUMS,
    KEY_ALBUM_DETAILS,
    KEY_ARTISTS,
    KEY_CHANNELS,
    KEY_EPISODES,
    KEY_MOVIES,
    KEY_SEASONS,
    KEY_SEASON_DETAILS,
    KEY_SONGS,
    KEY_TVSHOWS,
    KEY_TVSHOW_DETAILS,
    KEY_ITEMS,
}

# Kodi types of items
# https://github.com/xbmc/xbmc/blob/master/xbmc/media/MediaType.h
MEDIA_TYPE_ADDON = "addon"
MEDIA_TYPE_ALBUM = "album"
MEDIA_TYPE_ALBUM_DETAIL = "albumdetail"
MEDIA_TYPE_ARTIST = "artist"
MEDIA_TYPE_CHANNEL = "channel"
MEDIA_TYPE_EPISODE = "episode"
MEDIA_TYPE_MOVIE = "movie"
MEDIA_TYPE_SEASON = "season"
MEDIA_TYPE_SEASON_DETAIL = "seasondetail"
MEDIA_TYPE_SONG = "song"
MEDIA_TYPE_TVSHOW = "tvshow"
MEDIA_TYPE_TVSHOW_DETAIL = "tvshowdetail"
# MEDIA_TYPE_ITEM = "item"

MAP_KEY_MEDIA_TYPE = {
    KEY_ADDONS: MEDIA_TYPE_ADDON,
    KEY_ALBUMS: MEDIA_TYPE_ALBUM,
    KEY_ALBUM_DETAILS: MEDIA_TYPE_ALBUM_DETAIL,
    KEY_ARTISTS: MEDIA_TYPE_ARTIST,
    KEY_CHANNELS: MEDIA_TYPE_CHANNEL,
    KEY_EPISODES: MEDIA_TYPE_EPISODE,
    KEY_MOVIES: MEDIA_TYPE_MOVIE,
    KEY_SEASONS: MEDIA_TYPE_SEASON,
    KEY_SEASON_DETAILS: MEDIA_TYPE_SEASON_DETAIL,
    KEY_SONGS: MEDIA_TYPE_SONG,
    KEY_TVSHOWS: MEDIA_TYPE_TVSHOW,
    KEY_TVSHOW_DETAILS: MEDIA_TYPE_TVSHOW_DETAIL,
}


# Properties of the KODI items
PROPS_TVSHOW = [
    "title",
    "thumbnail",
    "playcount",
    "dateadded",
    "episode",
    "rating",
    "year",
    "season",
    "genre",
    "art",
]

PROPS_EPISODE = [
    "title",
    "rating",
    "episode",
    "season",
    "seasonid",
    "tvshowid",
    "thumbnail",
    "art",
]

PROPS_SONG = [
    "title",
    "album",
    "albumid",
    "artist",
    "artistid",
    "track",
    "year",
    "duration",
    "genre",
    "thumbnail",
]

PROPS_SEASON = ["season", "showtitle", "thumbnail", "title", "art"]

PROPS_MOVIE = ["thumbnail", "title", "year", "art", "genre"]
PROPS_RECENT_EPISODES = [
    "title",
    "rating",
    "episode",
    "season",
    "seasonid",
    "tvshowid",
    "thumbnail",
    "art",
]

PROPS_ALBUM = ["thumbnail", "title", "year", "art", "genre", "artist", "artistid"]
PROPS_ARTIST = ["thumbnail", "mood", "genre", "style"]
PROPS_ALBUM_DETAIL = [
    "albumlabel",
    "artist",
    "year",
    "artistid",
    "thumbnail",
    "style",
    "genre",
    "title",
]

PROPS_ITEM = [
    "album",
    "albumid",
    "artist",
    "artistid",
    "duration",
    "genre",
    "thumbnail",
    "title",
    "track",
    "year",
    "episode",
    "season",
    "art",
]

PROPS_ADDONS = ["enabled"]

PROPS_CHANNEL = [
    "uniqueid",
    "thumbnail",
    "channeltype",
    "channel",
    "channelnumber",
]
