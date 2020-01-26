"""
A simple request handler.
"""

from datetime import datetime
import logging
from typing import Dict, List
try:
    from typing import TypedDict  # type:ignore
except:  # pylint: disable=bare-except
    from typing_extensions import TypedDict
from typing_extensions import Annotated  # type: ignore
from urllib.error import HTTPError

from bareasgi import Application
import uvicorn

from bareasgi_rest import RestHttpRouter, add_swagger_ui, Body
from bareasgi_rest.protocol.json import JSONValue
from bareasgi_rest.protocol.xml import XMLEntity

logging.basicConfig(level=logging.DEBUG)


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


class BookController:
    """The book controller"""

    def __init__(self):
        self.books: Dict[int, Book] = {}
        self.next_id = 0

    def add_routes(self, router: RestHttpRouter):
        tags = ['Books']
        router.add_rest(
            {'GET'},
            '/books',
            self.get_books,
            tags=tags,
            status_code=200,
            produces=[b'application/json', b'application/xml']
        )
        router.add_rest(
            {'GET'},
            '/books/{book_id:int}',
            self.get_book,
            tags=tags,
            status_code=200,
            produces=[b'application/json', b'application/xml']
        )
        router.add_rest(
            {'POST'},
            '/books',
            self.create_book,
            tags=tags,
            status_code=201
        )
        router.add_rest(
            {'PUT'},
            '/books/{book_id:int}',
            self.update_book,
            tags=tags,
            status_code=204,
            consumes=[b'application/json', b'application/xml']
        )

    async def get_books(
            self
    ) -> Annotated[List[Book], JSONValue(), XMLEntity('Book')]:
        """Get all the books.

        This method gets all the books in the shop.

        Returns:
            List[Book]: All the books
        """
        return list(self.books.values())

    async def get_book(
            self,
            book_id: int
    ) -> Annotated[Book, JSONValue(), XMLEntity('Book')]:
        """Get a book for a given id

        Args:
            book_id (int): The id of the book

        Raises:
            HTTPError: 404, when a book is not found

        Returns:
            Book: The book
        """

        if book_id not in self.books:
            raise HTTPError(None, 404, 'Book not found', None, None)

        return self.books[book_id]

    async def create_book(
            self,
            author: str,
            title: str,
            publication_date: datetime
    ) -> int:
        """Add a book

        Args:
            author (str): The author
            title (str): The title
            publication_date (datetime): The publication date

        Returns:
            int: The id of the new book
        """
        self.next_id += 1

        self.books[self.next_id] = Book(
            book_id=self.next_id,
            title=title,
            author=author,
            publication_date=publication_date
        )

        return self.next_id

    async def update_book(
            self,
            book_id: int,
            book: Annotated[Book, JSONValue(), XMLEntity('Book')]
    ) -> None:
        """Update a book

        Args:
            book_id (int): The id of the book to update
            book (Body[Book]): The book as the body

        Raises:
            HTTPError: 404, when a book is not found
        """
        if book_id not in self.books:
            raise HTTPError(None, 404, None, None, None)
        self.books[book_id] = book


if __name__ == "__main__":

    rest_router = RestHttpRouter(
        None,
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
    app = Application(http_router=rest_router)
    add_swagger_ui(app)

    controller = BookController()
    controller.add_routes(rest_router)

    uvicorn.run(app, port=9009)
