"""Types"""

from typing import (
    Any,
    Awaitable,
    Callable,
    Dict
)

Deserializer = Callable[[str, bytes, Dict[bytes, bytes]], Any]
DictConsumes = Dict[bytes, Deserializer]

Serializer = Callable[[Any], str]
DictProduces = Dict[bytes, Serializer]

RestCallback = Callable[..., Awaitable[Any]]
