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


def is_body_type(annotation: Annotation) -> bool:
    """Determine if the annotation is of type Annotation[T, Body]

    Args:
        annotation (Any): The annotation

    Returns:
        bool: True if the annotation is of type Annotation[T, Body], otherwise
            False
    """
    return (
        typing_inspect.is_annotated_type(annotation) and
        typing_inspect.get_annotated_type_metadata(annotation)[0] is Body
    )


def get_body_type(annotation: Annotation) -> Annotation:
    """Gets the type T of Annotation[T, Body]

    Args:
        annotation (Any): The annotation

    Returns:
        Any: The type of the body
    """
    return typing_inspect.get_origin(annotation)
