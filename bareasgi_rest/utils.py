"""Utility functions"""

from typing import (
    Any,
    Callable,
    Generic,
    TypeVar,
    cast
)

import bareasgi_rest.typing_inspect as typing_inspect
from .types import Body, Renamer, Annotation

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


def _rename_if_str(value: Any, rename: Renamer) -> Any:
    return rename(value) if isinstance(value, str) else value


def _rename_dict(dct: dict, rename: Renamer) -> dict:
    return {
        _rename_if_str(name, rename): rename_object(obj, rename)
        for name, obj in dct.items()
    }


def _rename_list(lst: list, rename: Renamer) -> list:
    return [rename_object(obj, rename) for obj in lst]


def rename_object(obj: T, rename: Renamer) -> T:
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
