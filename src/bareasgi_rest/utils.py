"""Utility functions"""


class NullIter[T]:
    """An iterator containing no items"""

    def __aiter__(self):
        return self

    async def __anext__(self) -> T:
        raise StopAsyncIteration
