# KODI MEDIA SENSOR - Changelog

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