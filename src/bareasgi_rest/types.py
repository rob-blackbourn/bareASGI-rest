"""Types"""

from typing import Any, Awaitable, Callable

from jetblack_serialization import SerializerConfig, Annotation

type MediaType = bytes
type MediaTypeParams = dict[bytes, bytes]

type Deserializer = Callable[
    [
        MediaType,
        MediaTypeParams,
        SerializerConfig,
        str,
        Annotation
    ],
    Any
]
type DictConsumes = dict[bytes, Deserializer]

type Serializer = Callable[
    [
        MediaType,
        MediaTypeParams,
        SerializerConfig,
        Any,
        Annotation
    ],
    str
]
type DictProduces = dict[bytes, Serializer]

type DictSerializerConfig = dict[bytes, SerializerConfig]

type RestCallback = Callable[..., Awaitable[Any]]

type ArgDeserializer = Callable[[str, Annotation], Any]

type ArgDeserializerFactory = Callable[
    [SerializerConfig],
    Callable[[str, Annotation], Any]
]


class RestError(Exception):

    def __init__(self, status: int, message: str, *args) -> None:
        super().__init__(*args)
        self.status = status
        self.message = message
