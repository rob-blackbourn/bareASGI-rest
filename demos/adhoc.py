from datetime import datetime, timedelta
import inspect
import types
from typing import (
    Any,
    Dict,
    Generic,
    List,
    NewType,
    Optional,
    TypeVar,
    Union
)
from typing_extensions import TypedDict, Annotated

import bareasgi_rest.typing_inspect as typing_inspect


class Book(TypedDict, total=False):
    """A Book

    Args:
        book_id (int): The book id
        title (str): The title
        author (str): The author
        publication_date (datetime): The publication date
    """
    book_id: int
    title: str
    author: str
    publication_date: datetime


# T = TypeVar('T')
# Body = NewType('Body', TypedDict)  # type: ignore
# Body = Union[TypedDict]
Body = NewType('Body', None)  # type: ignore


def func() -> Annotated[Book, Body]:
    pass


sig = inspect.signature(func)


def is_body(annotation):
    return (
        typing_inspect.is_annotated_type(annotation) and
        typing_inspect.get_annotated_type_metadata(annotation)[0] is Body
    )


def get_body_type(annotation):
    return typing_inspect.get_origin(annotation)


print(sig)
