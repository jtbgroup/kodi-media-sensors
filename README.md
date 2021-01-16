# Kodi Recently Added Media for Home Assistant

[![](https://img.shields.io/github/release/boralyl/kodi-recently-added/all.svg?style=for-the-badge)](https://github.com/boralyl/kodi-recently-added/releases)
[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge)](https://github.com/hacs/integration)
[![](https://img.shields.io/github/license/boralyl/kodi-recently-added?style=for-the-badge)](LICENSE)
[![](https://img.shields.io/github/workflow/status/boralyl/kodi-recently-added/Python%20package?style=for-the-badge)](https://github.com/boralyl/kodi-recently-added/actions)

Home Assistant component to feed custom cards like [Upcoming Media Card](https://github.com/custom-cards/upcoming-media-card) and [Playlist Media Card](https://github.com/jtbgroup/playlist-media-card) with data coming from Kodi.

This component is based on the project of Aaron Godfrey (https://github.com/boralyl/kodi-recently-added). Check the [credits section](#credits).

![Kodi Recently Added Media](https://github.com/jtbgroup/kodi-media-sensors/tree/master/assets/example.png)

# Table of Contents

- [Installation](#installation)
  - [Pre-Installation](#pre-installation)
  - [HACS Install](#hacs-install)
  - [Manual Install](#manual-install)
- [Configuration](#configuration)
  - [Configuring via Integrations](#configuring-via-integrations)
  - [Card Configuration](#card-configuration)
- [Upgrading from configuration.yaml to UI integration](#upgrading-from-configurationyaml-to-ui-integration)
- [Known Issues](#known-issues)
- [Credits](#credits)

## Installation

### Pre-Installation

**NOTE: This component has been tested with Home Assistant 2021.1.3 only. Additionally Kodi must be setup via the UI in the integrations section of the Home Assistant configuration.**

### HACS Install

1. Search for `Kodi Media Sensors` under `Integrations` in the HACS Store tab.
2. Install the card: [Playlist Media Card](https://github.com/jtbgroup) or [Upcoming Media Card](https://github.com/custom-cards/upcoming-media-card) 
3. Add the code for the card to your `ui-lovelace.yaml`, or via the lovelace dashboard.
5. **You will need to restart after installation for the component to start working.**
6. [Configure](#configuration) your sensor using the options.

### Manual Install

1. In your `/config` directory, create a `custom_components` folder if one does not exist.
2. Copy the [kodi_media_sensors](https://github.com/jtbgroup/kodi-media-sensors/tree/master/custom_components) folder and all of it's contents from to your `custom_components` directory.
3. Restart Home Assistant.
4. [Configure](#configuration) your sensor using the options.

## Configuration

### Configuring via Integrations

1. Navigate to the Integrations page under the Configuration section.
2. Click the button to add a new integration and search for `Kodi Media Sensors`.
3. Select which instance of Kodi you would like to use and click Submit.
4. Choose the entities you want to be created depending on the card you want to use: 
    * `sensor.kodi_recently_added_tv` tracks your recently added tv shows 
    * `sensor.kodi_recently_added_movies` tracks your recently added movies
    * `sensor.kodi_playlist`tracks your playlist in Kodi (audio and video)

An `Options` button will appear on the integration. Clicking this will allow you to
toggle additional options. Currently the only option is whether or not the "recently added" should
ignore watched media or not. By default it does not.

### Card Configuration

#### Sample for ui-lovelace.yaml:

```yaml
- type: custom:upcoming-media-card
  entity: sensor.kodi_recently_added_tv
  title: Recently Added Episodes
  image_style: fanart

- type: custom:upcoming-media-card
  entity: sensor.kodi_recently_added_movies
  title: Recently Added Movies
  image_style: fanart
```

## Upgrading from configuration.yaml to UI Integration

1. Remove any sensors in your `configuration.yaml` that reference the `kodi_media_sensors`
   platform.
2. Restart Home Assistant.
3. Follow the steps from the begining in the section [Configuring via Integrations](#configuring-via-integrations)

## Known Issues

Below is a list of known issues that either can't be fixed by changes to the component
itself due to external factors.

### Artwork does not load when using the upcoming-media-card

One reason this could occur is if you setup you Home Assistance instance to use SSL and
your Kodi instance does not use SSL. When the upcoming-media-card tries to load the
artwork it will fail to do so since modern browsers do not allow loading insecure requests.
See [#6](https://github.com/boralyl/kodi-recently-added/issues/6) for more details and
possible workarounds.

### Genres, ratings and studios don't show up for TV Shows

Currently genres, rating, and studio are only populated for Movies. This is a limitation
of the data Kodi stores for TV shows.

## Credits

[Aaron Godfrey](https://github.com/boralyl) is the original developer of this project and did an excellent job. As I needed 
something similar to display my running playlist in Kodi, I started to enhance the component. 
Thanks a lot Aaron for letting me enhance your project! Let's hope other people might find it useful.
Do not hesitate to support Aaron and his many projects.