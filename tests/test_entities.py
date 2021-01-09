"""Tests for entities.py."""
from unittest import mock

from custom_components.kodi_recently_added.entities import KodiMediaEntity


def test_kodi_media_entity_init_base_web_url_https():
    """Test base web url property with ssl enabled."""
    config = {
        "host": "127.0.0.1",
        "password": "password",
        "port": 8080,
        "ssl": True,
        "username": "username",
    }
    entity = KodiMediaEntity(mock.Mock(), config)
    expected = "https://username:password@127.0.0.1:8080/image/image%3A%2F%2F"
    assert expected == entity.base_web_url


def test_kodi_media_entity_init_base_web_url_http():
    """Test base web url property with ssl disabled."""
    config = {
        "host": "127.0.0.1",
        "password": "password",
        "port": 8080,
        "ssl": False,
        "username": "username",
    }
    entity = KodiMediaEntity(mock.Mock(), config)
    expected = "http://username:password@127.0.0.1:8080/image/image%3A%2F%2F"
    assert expected == entity.base_web_url


def test_kodi_media_entity_init_base_web_url_no_auth():
    """Test base web url property when there is no authentication configured."""
    config = {
        "host": "127.0.0.1",
        "password": None,
        "port": 8080,
        "ssl": False,
        "username": None,
    }
    entity = KodiMediaEntity(mock.Mock(), config)
    expected = "http://127.0.0.1:8080/image/image%3A%2F%2F"
    assert expected == entity.base_web_url


def test_get_web_url_http_already():
    """Test get_web_url when path is an http url."""
    config = {
        "host": "127.0.0.1",
        "password": "password",
        "port": 8080,
        "ssl": False,
        "username": "username",
    }
    entity = KodiMediaEntity(mock.Mock(), config)
    path = "http://localhost/path/to/image.jpg"
    expected = path
    assert expected == entity.get_web_url(path)


def test_get_web_url_non_http():
    """Test get_web_url when path is not a http url."""
    config = {
        "host": "127.0.0.1",
        "password": "password",
        "port": 8080,
        "ssl": False,
        "username": "username",
    }
    entity = KodiMediaEntity(mock.Mock(), config)
    path = "nfs://127.0.0.2/volume1/image.png"
    expected = "http://username:password@127.0.0.1:8080/image/image%3A%2F%2Fnfs%253A%252F%252F127.0.0.2%252Fvolume1%252Fimage.png"
    assert expected == entity.get_web_url(path)
