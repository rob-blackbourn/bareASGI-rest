"""Types"""

from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    NewType
)

from .protocol.config import SerializerConfig

Annotation = Any
MediaType = bytes
MediaTypeParams = Dict[bytes, bytes]

Deserializer = Callable[
    [
        MediaType,
        MediaTypeParams,
        SerializerConfig,
        str,
        Annotation
    ],
    Any
]
DictConsumes = Dict[bytes, Deserializer]

Serializer = Callable[
    [
        MediaType,
        MediaTypeParams,
        SerializerConfig,
        Any,
        Annotation
    ],
    str
]
DictProduces = Dict[bytes, Serializer]

DictSerializerConfig = Dict[bytes, SerializerConfig]

RestCallback = Callable[..., Awaitable[Any]]

ArgDeserializer = Callable[[str, Annotation], Any]

ArgDeserializerFactory = Callable[
    [SerializerConfig],
    Callable[[str, Annotation], Any]
]

Body = NewType('Body', None)  # type: ignore
