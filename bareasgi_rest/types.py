"""Types"""

from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    NewType
)

Renamer = Callable[[str], str]
Annotation = Any
MediaType = bytes
MediaTypeParams = Dict[bytes, bytes]

Deserializer = Callable[
    [
        MediaType,
        MediaTypeParams,
        Renamer,
        Renamer,
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
        Renamer,
        Renamer,
        Any,
        Annotation
    ],
    str
]
DictProduces = Dict[bytes, Serializer]

RestCallback = Callable[..., Awaitable[Any]]

ArgDeserializer = Callable[[str, Annotation], Any]

ArgDeserializerFactory = Callable[
    [Renamer, Renamer],
    Callable[[str, Annotation], Any]
]

Body = NewType('Body', None)  # type: ignore
