DOMAIN = "kodi_media_sensors"
KODI_DOMAIN_PLATFORM = "media_player"

# Configuration of the integration
CONF_SENSOR_RECENTLY_ADDED_TVSHOW = "sensor_recently_added_tvshow"
CONF_SENSOR_RECENTLY_ADDED_MOVIE = "sensor_recently_added_movie"
CONF_SENSOR_PLAYLIST = "sensor_playlist"
CONF_SENSOR_SEARCH = "sensor_search"
CONF_KODI_INSTANCE = "kodi_config_entry_id"

OPTION_HIDE_WATCHED = "hide_watched"
OPTION_SEARCH_SONGS = "search_songs"
OPTION_SEARCH_SONGS_LIMIT = "search_songs_limit"
OPTION_SEARCH_ARTISTS = "search_artists"
OPTION_SEARCH_ARTISTS_LIMIT = "search_artists_limit"
OPTION_SEARCH_ALBUMS = "search_albums"
OPTION_SEARCH_ALBUMS_LIMIT = "search_albums_limit"
OPTION_SEARCH_MOVIES = "search_movies"
OPTION_SEARCH_MOVIES_LIMIT = "search_movies_limit"
OPTION_SEARCH_TVSHOWS = "search_tvshows"
OPTION_SEARCH_TVSHOWS_LIMIT = "search_tvshows_limit"
OPTION_SEARCH_CHANNELS_TV = "search_channels_tv"
OPTION_SEARCH_CHANNELS_TV_LIMIT = "search_channels_tv_limit"
OPTION_SEARCH_CHANNELS_RADIO = "search_channels_radio"
OPTION_SEARCH_CHANNELS_RADIO_LIMIT = "search_channels_radio_limit"
OPTION_SEARCH_EPISODES = "search_episodes"
OPTION_SEARCH_EPISODES_LIMIT = "search_episodes_limit"
OPTION_SEARCH_RECENT_LIMIT = "search_recent_limit"

OPTION_SEARCH_RECENT_SONGS = "search_recent_songs"
OPTION_SEARCH_RECENT_ALBUMS = "search_recent_albums"
OPTION_SEARCH_RECENT_MOVIES = "search_recent_movies"
OPTION_SEARCH_RECENT_EPISODES = "search_recent_episodes"
OPTION_SEARCH_KEEP_ALIVE_TIMER = "search_keep_alive_timer"

DEFAULT_OPTION_HIDE_WATCHED = False
DEFAULT_OPTION_SEARCH_SONGS = True
DEFAULT_OPTION_SEARCH_SONGS_LIMIT = 15
DEFAULT_OPTION_SEARCH_ARTISTS = True
DEFAULT_OPTION_SEARCH_ARTISTS_LIMIT = 10
DEFAULT_OPTION_SEARCH_ALBUMS = True
DEFAULT_OPTION_SEARCH_ALBUMS_LIMIT = 10
DEFAULT_OPTION_SEARCH_MOVIES = True
DEFAULT_OPTION_SEARCH_MOVIES_LIMIT = 5
DEFAULT_OPTION_SEARCH_TVSHOWS = True
DEFAULT_OPTION_SEARCH_TVSHOWS_LIMIT = 5
DEFAULT_OPTION_SEARCH_EPISODES = True
DEFAULT_OPTION_SEARCH_EPISODES_LIMIT = 5
DEFAULT_OPTION_SEARCH_CHANNELS_TV = True
DEFAULT_OPTION_SEARCH_CHANNELS_TV_LIMIT = 10
DEFAULT_OPTION_SEARCH_CHANNELS_RADIO = True
DEFAULT_OPTION_SEARCH_CHANNELS_RADIO_LIMIT = 5
DEFAULT_OPTION_SEARCH_RECENT_LIMIT = 20
# Expressed in seconds
DEFAULT_OPTION_SEARCH_KEEP_ALIVE_TIMER = 300

DEFAULT_OPTION_SEARCH_RECENT_SONGS = True
DEFAULT_OPTION_SEARCH_RECENT_ALBUMS = True
DEFAULT_OPTION_SEARCH_RECENT_MOVIES = True
DEFAULT_OPTION_SEARCH_RECENT_EPISODES = True

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

# KODI Constants
PLAYLIST_ID_MUSIC = 0
PLAYLIST_ID_VIDEO = 1
PLAYLIST_TYPE_MUSIC = "music"
PLAYLIST_TYPE_VIDEO = "video"
PLAYLIST_TYPE_AUDIO = "audio"
PLAYLIST_MAP = {
    PLAYLIST_TYPE_MUSIC: {"playlistid": PLAYLIST_ID_MUSIC},
    PLAYLIST_TYPE_AUDIO: {"playlistid": PLAYLIST_ID_MUSIC},
    PLAYLIST_TYPE_VIDEO: {"playlistid": PLAYLIST_ID_VIDEO},
}

# KODI keys returned in the aswer
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

# KODI types of items
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
