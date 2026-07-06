# Kodi Media Sensors for Home Assistant

[![](https://img.shields.io/github/release/jtbgroup/kodi-media-sensors/all.svg?style=for-the-badge)](https://github.com/jtbgroup/kodi-media-sensors)
[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge)](https://github.com/hacs/integration)
[![](https://img.shields.io/github/license/jtbgroup/kodi-media-sensors?style=for-the-badge)](LICENSE)

<!-- [![](https://img.shields.io/github/workflow/status/jtbgroup/kodi-media-sensors/Python%20package?style=for-the-badge)](https://github.com/jtbgroup/kodi-media-sensors/actions) -->

This Home Assistant component is used to feed custom cards like [Kodi Playlist Card](https://github.com/jtbgroup/kodi-playlist-card) or [Kodi Search Card](https://github.com/jtbgroup/kodi-search-card) with data coming from Kodi. 

 Kodi playlist Card                                            | Kodi search Card                                       |
| ------------------------------------------------------------- | ------------------------------------------------------ |
| ![Kodi Playlist Card](./assets/kodi_playlist_card.png) | ![Kodi Search Card](./assets/kodi_search_card.png) |

## Table of Contents

- [Installation](#installation)
- [Sensors](#sensors)
- [Configuration](#configuration)
- [Services](#services)
- [Issues](#issues)
- [Credits](#credits)

## Installation

### Pre-Installation

**NOTE: This component has been tested with the (almost) last versions of Home Assistant. No backward compatibility is tested.Additionally Kodi must be setup via the UI in the integrations section of the Home Assistant configuration.**

### HACS Install

1. Search for `Kodi Media Sensors` under `Integrations` in the HACS Store tab.
2. **You will need to restart after installation for the component to start working.**

### Manual Install

**This method is not recommended**

1. In your `/config` directory, create a `custom_components` folder if one does not exist.
2. Copy the [kodi_media_sensors](https://github.com/jtbgroup/kodi-media-sensors/tree/master/custom_components) folder and all of it's contents from to your `custom_components` directory.
3. Restart Home Assistant.

### Integration Installation

1. After automatic or manual install, go to the Integration panel (under Configuration section) and search for the ne component by clicking on the button 'Add Integration'.
2. Enter the name for the integration on your system and choose the Kodi entity previously installed. A sensor connected to the kodi integration will become available.
3. Click Submit
4. You should now see the sensor in Home Assistant with a status linked to your Kodi integration.


## Sensors

| Sensor name                                      | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| ------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `sensor.<<name of your previously configured sensor>>` | The sensor tha will make the link between your integration and the kodi player. It has several attributes available such as the status, information about the current playing track (id, type, artist).

## Configuration

### Configuring the Integrations

A `Configure` button will appear on the integration. Clicking this will allow you to
toggle additional options. To access the option, the right sensor must be present.

| Option                                  | Sensor                                           | Value                                 | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| --------------------------------------- | ------------------------------------------------ | ------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| hide_watched                            | recently added movie, <br/>recently added tvshow | boolean<br/>(default = false)         | Excludes recently added video media that is marked as watched (movie sensors) when option is schecked                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| search_songs_limit                      | search                                           | int<br/>[0 - 100]<br/>(default = 15)  | Limits the number of SONGS in the search result. <br/>0 means the search won't be performed for this ite type. Values < 0 are considered = 0; values > 100 are considered = 100.                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| search_albums_limit                     | search                                           | int<br/>[0 - 100]<br/> (default = 10) | Limits the number of ALBUMS in the search result. <br/>0 means the search won't be performed for this ite type. Values < 0 are considered = 0; values > 100 are considered = 100.                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| search_artists_limit                    | search                                           | int<br/>[0 - 100]<br/> (default = 10) | Limits the number of ARTISTS in the search result. <br/>0 means the search won't be performed for this ite type. Values < 0 are considered = 0; values > 100 are considered = 100.                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| search_movies_limit                     | search                                           | int<br/>[0 - 100]<br/> (default = 5)  | Limits the number of MOVIES in the search result. <br/>0 means the search won't be performed for this ite type. Values < 0 are considered = 0; values > 100 are considered = 100.                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| search_musicvideos_limit                | search                                           | int<br/>[0 - 100]<br/> (default = 5)  | Limits the number of MUSIC VIDEOS in the search result. <br/>0 means the search won't be performed for this ite type. Values < 0 are considered = 0; values > 100 are considered = 100.                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| search_tvshows_limit                    | search                                           | int<br/>[0 - 100]<br/> (default = 5)  | Limits the number of TVSHOWS in the search result. <br/>0 means the search won't be performed for this ite type. Values < 0 are considered = 0; values > 100 are considered = 100.                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| search_episodes_limit                   | search                                           | int<br/>[0 - 100]<br/> (default = 5)  | Limits the number of EPISODES in the search result. <br/>0 means the search won't be performed for this ite type. Values < 0 are considered = 0; values > 100 are considered = 100.                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| search_channels_tv_limit                | search                                           | int<br/>[0 - 100]<br/> (default = 10) | Limits the number of TV CHANNELS in the search result. <br/>0 means the search won't be performed for this ite type. Values < 0 are considered = 0; values > 100 are considered = 100.                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| search_channels_radio_limit             | search                                           | int<br/>[0 - 100]<br/> (default = 5)  | Limits the number of RADIO CHANNELS in the search result. <br/>0 means the search won't be performed for this ite type. Values < 0 are considered = 0; values > 100 are considered = 100.                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| search_music_playlists_limit            | search                                           | int<br/>[0 - 100]<br/> (default = 10) | Limits the number of [music playlists](https://kodi.wiki/view/Basic_playlists) retrieved by the search engine. The search method is applied on the label and the filename returned by kodi in the json answer. Only the supported format are treated. The search method only searches in the [special://musicplaylists](https://kodi.wiki/view/Special_protocol) folder.<br/>Values < 0 are considered = 0; values > 100 are considered = 100.                                                                                                                                                                                                        |
| search_recently_added_songs_limit       | search                                           | int<br/>[0 - 100]<br/> (default = 20) | Limits the number of SONGS in the RECENTLY ADDED search result. <br/>0 means the search won't be performed for this ite type. Values < 0 are considered = 0; values > 100 are considered = 100.                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| search_recently_added_albums_limit      | search                                           | int<br/>[0 - 100]<br/> (default = 20) | Limits the number of ALBUMS in the RECENTLY ADDED search result. <br/>0 means the search won't be performed for this ite type. Values < 0 are considered = 0; values > 100 are considered = 100.                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| search_recently_added_movies_limit      | search                                           | int<br/>[0 - 100]<br/> (default = 20) | Limits the number of MOVIES in the RECENTLY ADDED search result. <br/>0 means the search won't be performed for this ite type. Values < 0 are considered = 0; values > 100 are considered = 100.                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| search_recently_added_musicvideos_limit | search                                           | int<br/>[0 - 100]<br/> (default = 20) | Limits the number of MUSIC VIDEOS in the RECENTLY ADDED search result. <br/>0 means the search won't be performed for this ite type. Values < 0 are considered = 0; values > 100 are considered = 100.                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| search_recently_added_episodes_limit    | search                                           | int<br/>[0 - 100]<br/> (default = 20) | Include EPISODES search result in RECENTLY ADDED items                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| search_recently_played_songs_limit      | search                                           | int<br/>[0 - 100]<br/> (default = 10) | Limits the number of SONGS in the RECENTLY PLAYED search result. <br/>0 means the search won't be performed for this ite type. Values < 0 are considered = 0; values > 100 are considered = 100.                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| search_recently_played_albums_limit     | search                                           | int<br/>[0 - 100]<br/> (default = 10) | Limits the number of ALBUMS in the RECENTLY PLAYED search result. <br/>0 means the search won't be performed for this ite type. Values < 0 are considered = 0; values > 100 are considered = 100.                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| search_keep_alive_timer                 | search                                           | 300                                   | Lifetime (in sec) of the result. <br/>When using value **0**, the query will automatically be reprocessed with the same parameters. This is only true for search methods (_normal search_ and _recently added_), not the other methods (like _clear_ or _reset addons_). <br/> **Remark**: the timer also depends on the polling of the sensor which is set to 300 sec. The evaluation of purging data is only evaluated during the polling. This means the real lifetime of the data is between the specified value and this value added by the polling eriod. <br/> Ex: if value = 20 sec, the purge occurs after a period between 20sec and 320sec |

## Services

in order to interact withe the integration, some api calls can be used.

### **Playlist**

1. **kodi_media_sensors/playlist_subscribe**

   This method allows a client to subscribe to the playlist and being notified in case of changes in the playlist.

   Parameter:

   - entry_id = the entry id of the integration you want to subscribe to.


2. **kodi_media_sensors/playlist_goto_index**

   This function plays the object at the given position for the given player

   Parameters:

   - entry_id = the entry id of the integration you want to subscribe to.
   - index = the index to be played in the playlist
  
3. **kodi_media_sensors/playlist_remove_item**

   This function removes an object from the given playlist

   Parameters:

   - entry_id = the entry id of the integration you want to subscribe to.
   - from_index = the index of the item to be moved
   - to_index = the index where the selected item should be moved

4. **kodi_media_sensors/playlist_reorder"**

   This function moves an item from position `from`to position `to` in the given playlist. Basically, the function does a `remove` followed by an `insert`. It means the indexes passed as position must take into account that in some cases, -1 must be calculated for the `position_to`0. If you use a framework such as SortableJS, this calculation is already taken into account.

   Parameters:
   
   - entry_id = the entry id of the integration you want to subscribe to.
   - index = the index to be removed from the playlist
  
5. **kodi_media_sensors/playlist_play_item"**

   This function plays the desired object with the good player. The argument depends on what object has to be played. 

   Parameters:
   
   - entry_id = the entry id of the integration you want to subscribe to.
   - item_id = the id of the item to be played.
   - item_name = a keyword lnked to the type of item to be played. Must be of the following: songid", "movieid", "albumid", "musicvideoid", episodeid", "channelid", "filemusicplaylist".
  
6. **kodi_media_sensors/playlist_add_item"**

   This method adds an item to the right playlist depending on the item passed. The `position`argument indicates where the item must be added in the playlist. The playlist index is 0-based, so 0 is the first position. To add an item at the end of the playlist, just use a index > the length of the playlist (ex: use 1000 when you have a playlist of 50 items, even in party mode).
  
   Parameters:
   
   - entry_id = the entry id of the integration you want to subscribe to.
   - item_id = the id of the item to be added.
   - item_name = a keyword lnked to the type of item to be played. Must be of the following: songid", "movieid", "albumid", "musicvideoid", episodeid", "channelid", "filemusicplaylist".
   - position = the index where to add the item

### **Search**

1. **kodi_media_sensors/search**

   Searches in the specified media type for the referenced value. The media type 'all' will return result for songs, albums, artists, movies and tv shows.

   Parameters:
   
   - entry_id = the entry id of the integration you want to subscribe to.
   - item_id = the id of the item to be added.
   - query = the text to search in the diferent categories
   - category (optional) = the category you want to search on.


2. **kodi_media_sensors/search_artist**

3. **kodi_media_sensors/search_tvshow**

4. **kodi_media_sensors/search_recently_played**

5. **kodi_media_sensors/search_recently_added**

### Cards to use with sensors

The goal is to group all the sensors and have separate Cards to display the sensors data. The cards that where tested are:

- [Kodi Playlist Card](https://github.com/jtbgroup/kodi-playlist-card) (kodi_media_sensor_playlist)
- [Kodi Search Card](https://github.com/jtbgroup/kodi-search-card) (kodi_media_sensor_search)

**Samples** for ui-lovelace.yaml


Here two examples with [Kodi Search Card](https://github.com/jtbgroup/kodi-search-card) and [Kodi Playlist Card](https://github.com/jtbgroup/kodi-playlist-card)

```yaml
- type: custom:kodi-search-card
  entity: sensor.kodi_media_sensor_KODI-1
```

```yaml
- type: custom:kodi-playlist-card
  entity: sensor.kodi_media_sensor_KODI-2
```


## Issues

Don't hesitate to create tickets in the Github repo for questions.


## Credits

Thanks to all the people for testing, reporting dysfunctions and propose improvements.
