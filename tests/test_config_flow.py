"""Config flow tests."""
from unittest import mock

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.kodi_media_sensors.const import (
    OPTION_HIDE_WATCHED,
    CONF_KODI_INSTANCE,
    CONF_SENSOR_RECENTLY_ADDED_TVSHOW,
    DOMAIN,
)
from custom_components.kodi_media_sensors.utils import KODI_DOMAIN


async def test_flow_init_kodi_not_configured(hass):
    """Test the initial flow when kodi is not configured."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    assert {
        "data_schema": mock.ANY,
        "description_placeholders": None,
        "errors": {"base": "kodi_not_configured"},
        "flow_id": mock.ANY,
        "handler": "kodi_media_sensors",
        "step_id": "user",
        "type": "form",
    } == result


async def test_flow_init_kodi_is_configured(hass):
    """Test the initial flow when kodi IS configured."""
    config_entries = [
        MockConfigEntry(
            entry_id="foo",
            title="Android",
            data={
                "host": "127.0.0.1",
                "port": 8081,
                "ws_port": 1234,
                "username": None,
                "password": None,
                "ssl": False,
            },
            domain=KODI_DOMAIN,
        ),
        MockConfigEntry(
            entry_id="bar",
            title="HTPC",
            data={
                "host": "127.0.0.2",
                "port": 8080,
                "ws_port": 5678,
                "username": None,
                "password": None,
                "ssl": False,
            },
            domain=KODI_DOMAIN,
        ),
    ]
    hass.config_entries.async_entries = mock.Mock(return_value=config_entries)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )

    assert {
        "data_schema": mock.ANY,
        "description_placeholders": None,
        "errors": {},
        "flow_id": mock.ANY,
        "handler": "kodi_media_sensors",
        "step_id": "user",
        "type": "form",
    } == result

    # Verify the schema populated with config entry titles.
    assert ["Android", "HTPC"] == result["data_schema"].schema[
        CONF_KODI_INSTANCE
    ].container


async def test_flow_user_setp_success(hass):
    """Test the user flow when successfully completed by the user."""
    config_entries = [
        MockConfigEntry(
            entry_id="foo",
            title="Android",
            data={
                "host": "127.0.0.1",
                "port": 8081,
                "ws_port": 1234,
                "username": None,
                "password": None,
                "ssl": False,
            },
            domain=KODI_DOMAIN,
        ),
        MockConfigEntry(
            entry_id="bar",
            title="HTPC",
            data={
                "host": "127.0.0.2",
                "port": 8080,
                "ws_port": 5678,
                "username": None,
                "password": None,
                "ssl": False,
            },
            domain=KODI_DOMAIN,
        ),
    ]
    hass.config_entries.async_entries = mock.Mock(return_value=config_entries)
    _result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    result = await hass.config_entries.flow.async_configure(
        _result["flow_id"], user_input={CONF_KODI_INSTANCE: "HTPC"}
    )
    expected = {
        "version": 1,
        "type": "create_entry",
        "flow_id": mock.ANY,
        "handler": "kodi_media_sensors",
        "title": "Kodi Media Sensors",
        "data": {"kodi_config_entry_id": "bar","sensor_recently_added_tvshow": False, "sensor_recently_added_movie": False, "sensor_playlist": False, "sensor_search": False},
        "description": None,
        "description_placeholders": None,
        "result": mock.ANY,
    }
    assert expected == result


async def test_options_flow(hass):
    """Test config flow options."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="kodi_media_sensors",
        data={"kodi_entry_id": "abc", CONF_SENSOR_RECENTLY_ADDED_TVSHOW: True},
    )
    config_entry.add_to_hass(hass)
    #assert await hass.config_entries.async_setup(config_entry.entry_id)
    #await hass.async_block_till_done()

    # show initial form
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert "form" == result["type"]
    assert "init" == result["step_id"]

    # submit form with options
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={OPTION_HIDE_WATCHED: True}
    )
    expected = {
        "data": {OPTION_HIDE_WATCHED: True},
        "description": None,
        "description_placeholders": None,
        "flow_id": mock.ANY,
        "handler": mock.ANY,
        "result": True,
        "title": "",
        "type": "create_entry",
        "version": 1,
    }
    assert expected == result
