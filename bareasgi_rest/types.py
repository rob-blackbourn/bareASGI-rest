"""Types"""

from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    Generic,
    TypeVar
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

T = TypeVar('T')


class Body(Generic[T]):
    """A wrapper for the body"""

    def __init__(self, value: T) -> None:
        """A wrapper for the body

        Args:
            value (T): The body value
        """
        self.value = value

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, type(self)) and self.value == other.value
