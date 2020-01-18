from datetime import datetime
import logging
from typing import Dict, List, Optional
try:
    from typing import TypedDict  # type:ignore
except:  # pylint: disable=bare-except
    from typing_extensions import TypedDict
from urllib.error import HTTPError

from bareasgi.basic_router.path_definition import PathDefinition

from bareasgi_rest.types import Body
from bareasgi_rest.swagger.entry import make_swagger_entry


class Book(TypedDict):
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


BOOKS: Dict[int, Book] = {}


async def update_if_withdrawn(
        library: str,
        is_withdrawn: bool,
        book: Body[Book]
) -> None:
    """Update the book if not withdrawn

    Args:
        library (str): The library
        is_withdrawn (bool): True if the book has been withdrawn
        book (Body[Book]): The book details to update
    """
    return list(BOOKS.values())

update_if_withdrawn_swagger_entry = make_swagger_entry(
    'POST',
    PathDefinition('/books/{library:str}'),
    update_if_withdrawn,
    b'application/json',
    b'application/json',
    'multi',
    ['Books'],
    200,
    'OK'
)
print(update_if_withdrawn_swagger_entry)
