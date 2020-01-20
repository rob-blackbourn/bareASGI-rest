"""Utility functions"""

from typing import (
    Any,
    Generic,
    TypeVar
)

from inflection import camelize

import bareasgi_rest.typing_inspect as typing_inspect
from .types import Body

T = TypeVar('T')


class NullIter(Generic[T]):
    """An iterator containing no items"""

    def __aiter__(self):
        return self

    async def __anext__(self) -> T:
        raise StopAsyncIteration


def is_body_type(annotation: Any) -> bool:
    """Determine if the annotation is of type Body[T]

    Args:
        annotation (Any): The annotation

    Returns:
        bool: True if the annotation is of type Body[T], otherwise False
    """
    return typing_inspect.get_origin(annotation) is Body


def get_body_type(annotation: Any) -> Any:
    """Gets the type T of Body[T]

    Args:
        annotation (Any): The annotation

    Returns:
        Any: The type of the body
    """
    body_type, *_rest = typing_inspect.get_args(annotation)
    return body_type


def camelcase(text: str) -> str:
    """Apply camelcase

    Args:
        text (str): The text to transform

    Returns:
        str: The camelcase version of the text
    """
    return camelize(text, uppercase_first_letter=False)
