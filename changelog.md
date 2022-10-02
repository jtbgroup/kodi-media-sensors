# KODI MEDIA SENSOR - Changelog

## 3.8.0

- Added the `moveto` command in the playlist sensor . This new command is used to reorder the playlist.

## 3.7.0
- Added the file attribute in the meta data. This value can be used when item is not yet in a library and no ID can be used. (see [issue #22](https://github.com/jtbgroup/kodi-media-sensors/issues/22). Thanks to [Rudd-O](https://github.com/Rudd-O)

## 3.6.0

- Added the music videos items in the search result if wanted (see [issue #16](https://github.com/jtbgroup/kodi-search-card/issues/16)). Thanks to [Rudd-O](https://github.com/Rudd-O)
- Added the file attribute in the item object of the playlist (see [issue #21](https://github.com/jtbgroup/kodi-search-card/issues/21)). Thanks to [Rudd-O](https://github.com/Rudd-O)
- Recently added items also includes the music videos

## 3.5.0

- Search sensor can now search for recently played songs and albums. Some config options changed name. You'll need to reconfigure them if you don't use the default values.
- Deprecated code (see [issue #18](https://github.com/jtbgroup/kodi-media-sensors/issues/18)). Thanks to [mshuflin](https://github.com/mshuflin) for reporting and [Raman Gupta](https://github.com/raman325) for the solution.

## 3.4.3

- BugFix: changed from DeviceStateAttrs to ExtraStateAttrs. Thanks to [Raman Gupta](https://github.com/raman325)

## 3.4.2

- Bugfix: choose the right playlist when playing or adding an item (id of the player isn't constant in rpc methods) (see [issue#9](https://github.com/jtbgroup/kodi-search-card/issues/9))

## 3.4.1

- Bugfix: regression bug when getting position of the current playing item

## 3.4.0

- Search entity: new method add at the desired position (see [issue #6](https://github.com/jtbgroup/kodi-search-card/issues/6))
- Search entity plays now the selected item at the current position +1
- Bugfix: playlist sensor raised an error when starting HA

## 3.3.0

- Added keep alive timer option for Search Sensor

## 3.2.3

- No search limit when the configuration option **x_limit*- is 0
- Added Search PVR Channels functionnality. During the first search operation, the sensor checks if a PVR client addon is present and enabled. if not, the PVR search is desactivated.
- New properties in the configuration to (de)activate item types in the search and setlimits per item types.

## 3.1.5

- code refactoring
- search enhanced with 'recently added' items
- playlist sensor initialized directly after installation
- added art tags from kodi
- includes 'episode' in the search result (based on the title of the episode)

## 3.0.2

- name of the kodi entity was hardcoded :-S

## 3.0.0

- playlist sensor based on events from kodi
- playlist and search sensors state (on / off) depends on kodi state
- playlist and search sensors meta attributes contains the last data update timestamp

## 2.x

- A new sensor (search) is available and can be used with a new card.

***Remarks***

- Uninstall and re-install this integration is advised.
- **Attention that the name of entities also changed.**

## 1.2

This was the first version of the integration
