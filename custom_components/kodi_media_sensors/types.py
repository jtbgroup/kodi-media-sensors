from typing import Optional

from typing_extensions import TypedDict


class ExtraStateAttrs(TypedDict):
    data: str


class MediaSensorStateAttrs(TypedDict):
    meta: str
    data: str


class KodiConfig(TypedDict):
    host: str
    name: Optional[str]
    password: str
    port: int
    ssl: bool
    timeout: int
    username: str
    ws_port: int
