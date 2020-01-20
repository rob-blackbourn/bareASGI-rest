"""Utility functions"""

from typing import (
    Any,
    Callable,
    Generic,
    TypeVar,
    cast
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


def _rename_if_str(value: Any, rename: Callable[[str], str]) -> Any:
    return rename(value) if isinstance(value, str) else value


def _rename_dict(dct: dict, rename: Callable[[str], str]) -> dict:
    return {
        _rename_if_str(name, rename): rename_object(obj, rename)
        for name, obj in dct.items()
    }


def _rename_list(lst: list, rename: Callable[[str], str]) -> list:
    return [rename_object(obj, rename) for obj in lst]


def rename_object(obj: T, rename: Callable[[str], str]) -> T:
    """Recursively rename the keys of an object

    Args:
        obj (T): The object
        rename (Callable[[str], str]): The function to rename the keys.

    Returns:
        T: The object with it's keys renamed.
    """
    if isinstance(obj, dict):
        return cast(T, _rename_dict(obj, rename))
    elif isinstance(obj, list):
        return cast(T, _rename_list(obj, rename))
    else:
        return obj
