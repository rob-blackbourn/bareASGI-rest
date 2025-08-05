"""
A simple request handler.
"""

from datetime import datetime
from enum import Enum, auto
import logging
from typing import Annotated, TypedDict

import uvicorn

from jetblack_serialization.json import JSONValue
from jetblack_serialization.xml import XMLEntity

from bareasgi_rest import (
    RestApplication,
    RestHttpRouter,
    RestError,
)
from bareasgi_rest.swagger import add_swagger_ui

logging.basicConfig(level=logging.DEBUG)


class Genre(Enum):
    FICTION = auto()
    NON_FICTION = auto()


class Book(TypedDict):
    """A Book

    Args:
        book_id (int): The book id
        title (str): The title
        author (str): The author
        publication_date (datetime): The publication date
        genre (Genre): The genre
    """
    title: str
    author: str
    publication_date: datetime
    genre: Genre


class BookWithId(Book):
    """A Book

    Args:
        book_id (int): The book id
        title (str): The title
        author (str): The author
        publication_date (datetime): The publication date
    """
    book_id: int


class State(TypedDict):
    """The state of the application"""
    books: dict[int, BookWithId]
    next_id: int


TAGS = ['Books']

rest_router = RestHttpRouter(
    title="Books",
    version="1",
    description="A book api",
    base_path='/api/1',
    tags=[
        {
            'name': 'Books',
            'description': 'The book store API'
        }
    ]
)
app = RestApplication(
    rest_router=rest_router,
    info={'state': State(books={}, next_id=0)},
)
add_swagger_ui(app)


@app.on_rest_request(
    {'GET'},
    '/books',
    tags=TAGS,
    status_code=200,
    produces=[b'application/json', b'application/xml']
)
async def get_books() -> Annotated[list[BookWithId], JSONValue(), XMLEntity('Book')]:
    """Get all the books.

    This method gets all the books in the shop.

    Returns:
        list[Book]: All the books
    """
    state = app.info['state']
    return list(state['books'].values())


@app.on_rest_request(
    {'GET'},
    '/books/{book_id:int}',
    tags=TAGS,
    status_code=200,
    produces=[b'application/json', b'application/xml']
)
async def get_book(book_id: int) -> Annotated[BookWithId, JSONValue(), XMLEntity('Book')]:
    """Get a book for a given id

    Args:
        book_id (int): The id of the book

    Raises:
        RestError: 404, when a book is not found

    Returns:
        Book: The book
    """
    state = app.info['state']

    if book_id not in state.books:
        raise RestError(404, 'Book not found')

    return state.books[book_id]


@app.on_rest_request(
    {'POST'},
    '/books',
    tags=TAGS,
    status_code=201,
    consumes=[b'application/json', b'application/xml'],
)
async def create_book(
        book: Annotated[Book, JSONValue(), XMLEntity('Book')]
) -> int:
    """Add a book

    Args:
        book (Book): The book

    Returns:
        int: The id of the new book
    """
    state = app.info['state']

    state.next_id += 1

    state.books[state.next_id] = BookWithId(
        book_id=state.next_id,
        title=book['title'],
        author=book['author'],
        publication_date=book['publication_date'],
        genre=book['genre']
    )

    return state.next_id


@app.on_rest_request(
    {'PUT'},
    '/books/{book_id:int}',
    tags=TAGS,
    status_code=204,
    consumes=[b'application/json', b'application/xml'],
)
async def update_book(
        book_id: int,
        book: Annotated[Book, JSONValue(), XMLEntity('Book')]
) -> None:
    """Update a book

    Args:
        book_id (int): The id of the book to update
        book (Annotated[Book, T]): The book as the body

    Raises:
        RestError: 404, when a book is not found
    """
    state = app.info['state']

    if book_id not in state.books:
        raise RestError(404, 'Book not found')
    found_book = state.books[book_id]
    found_book.update(book)


uvicorn.run(app, port=9009)
