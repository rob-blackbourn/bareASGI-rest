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
        str,
        bytes,
        Dict[bytes, bytes],
        Any,
        Callable[[str], str],
        Callable[[str], str]
    ],
    Any
]
DictConsumes = Dict[bytes, Deserializer]

Serializer = Callable[
    [
        Any,
        Callable[[str], str],
        Callable[[str], str]
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
