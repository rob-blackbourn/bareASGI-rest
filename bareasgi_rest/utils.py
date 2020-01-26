"""Utility functions"""

from typing import (
    Generic,
    TypeVar
)

import bareasgi_rest.typing_inspect as typing_inspect
from .types import Body, Annotation

T = TypeVar('T')


class NullIter(Generic[T]):
    """An iterator containing no items"""

    def __aiter__(self):
        return self

    async def __anext__(self) -> T:
        raise StopAsyncIteration
