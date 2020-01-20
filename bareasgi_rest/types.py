"""Types"""

from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    Generic,
    TypeVar
)

Deserializer = Callable[
    [
        bytes,
        Dict[bytes, bytes],
        Callable[[str], str],
        Callable[[str], str],
        str,
        Any,
    ],
    Any
]
DictConsumes = Dict[bytes, Deserializer]

Serializer = Callable[
    [
        bytes,
        Dict[bytes, bytes],
        Callable[[str], str],
        Callable[[str], str],
        Any,
        Any
    ],
    str
]
DictProduces = Dict[bytes, Serializer]

RestCallback = Callable[..., Awaitable[Any]]

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
