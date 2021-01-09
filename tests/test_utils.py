"""Tests for utils.py."""
from unittest.mock import Mock

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.kodi_recently_added.utils import (
    KODI_DOMAIN,
    find_matching_config_entry,
    find_matching_config_entry_for_host,
)


def test_find_matching_config_entry():
    """Test that we find a matching entry."""
    config_entries = [
        MockConfigEntry(entry_id="foo", domain=KODI_DOMAIN),
        MockConfigEntry(entry_id="bar", domain=KODI_DOMAIN),
    ]
    mock_hass = Mock()
    mock_hass.config_entries.async_entries.return_value = config_entries

    assert config_entries[1] == find_matching_config_entry(mock_hass, "bar")


def test_find_matching_config_entry_does_not_exist():
    """Test that we do not find a matching entry."""
    config_entries = [
        MockConfigEntry(entry_id="foo", domain=KODI_DOMAIN),
        MockConfigEntry(entry_id="bar", domain=KODI_DOMAIN),
    ]
    mock_hass = Mock()
    mock_hass.config_entries.async_entries.return_value = config_entries

    assert find_matching_config_entry(mock_hass, "foobar") is None


def test_find_matching_config_entry_skip_source_ignore():
    """Test we skip matches whose source is ignore."""
    config_entries = [
        MockConfigEntry(entry_id="foo", domain=KODI_DOMAIN, source="ignore"),
        MockConfigEntry(entry_id="bar", domain=KODI_DOMAIN),
    ]
    mock_hass = Mock()
    mock_hass.config_entries.async_entries.return_value = config_entries


def test_find_matching_config_entry_for_host():
    """Test we find a matching config entry."""
    config_entries = [MockConfigEntry(domain=KODI_DOMAIN, data={"host": "127.0.0.1"})]
    mock_hass = Mock()
    mock_hass.config_entries.async_entries.return_value = config_entries

    assert config_entries[0] == find_matching_config_entry_for_host(
        mock_hass, "127.0.0.1"
    )


def test_find_matching_config_entry_for_host_does_not_exist():
    """Test we find no matching config entry."""
    config_entries = [MockConfigEntry(domain=KODI_DOMAIN, data={"host": "127.0.0.1"})]
    mock_hass = Mock()
    mock_hass.config_entries.async_entries.return_value = config_entries

    assert find_matching_config_entry_for_host(mock_hass, "192.168.1.1") is None


def test_find_matching_config_entry_for_host_skip_source_ignore():
    """Test we skip matches whose source is ignore."""
    config_entries = [
        MockConfigEntry(
            domain=KODI_DOMAIN, data={"host": "127.0.0.1"}, source="ignore"
        ),
        MockConfigEntry(domain=KODI_DOMAIN, data={"host": "127.0.0.1"}, source="user"),
    ]
    mock_hass = Mock()
    mock_hass.config_entries.async_entries.return_value = config_entries

    assert config_entries[1] == find_matching_config_entry_for_host(
        mock_hass, "127.0.0.1"
    )


def test_find_matching_config_entry_for_host_no_host_key():
    """Test we do not find a matching config entry.

    Also ensure we don't raise an error if the config entry's data has no host key.
    """
    config_entries = [MockConfigEntry(domain=KODI_DOMAIN, data={})]
    mock_hass = Mock()
    mock_hass.config_entries.async_entries.return_value = config_entries

    assert find_matching_config_entry_for_host(mock_hass, "127.0.0.1") is None
