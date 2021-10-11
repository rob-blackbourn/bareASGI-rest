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
try:
    from typing import Annotated  # type: ignore
except:  # pylint: disable=bare-except
    from typing_extensions import Annotated  # type: ignore

from bareasgi import Application
import uvicorn

from jetblack_serialization.json import JSONValue
from jetblack_serialization.xml import XMLEntity

from bareasgi_rest import RestHttpRouter, RestError, add_swagger_ui

logging.basicConfig(level=logging.DEBUG)


class Book(TypedDict):
    """A Book

    Args:
        book_id (int): The book id
        title (str): The title
        author (str): The author
        publication_date (datetime): The publication date
    """
    title: str
    author: str
    publication_date: datetime

class BookWithId(Book):
    """A Book

    Args:
        book_id (int): The book id
        title (str): The title
        author (str): The author
        publication_date (datetime): The publication date
    """
    book_id: int


class BookController:
    """The book controller"""

    def __init__(self):
        self.books: Dict[int, BookWithId] = {}
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
            status_code=201,
            consumes=[b'application/json', b'application/xml']
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
    ) -> Annotated[List[BookWithId], JSONValue(), XMLEntity('Book')]:
        """Get all the books.

        This method gets all the books in the shop.

        Returns:
            List[Book]: All the books
        """
        return list(self.books.values())

    async def get_book(
            self,
            book_id: int
    ) -> Annotated[BookWithId, JSONValue(), XMLEntity('Book')]:
        """Get a book for a given id

        Args:
            book_id (int): The id of the book

        Raises:
            RestError: 404, when a book is not found

        Returns:
            Book: The book
        """

        if book_id not in self.books:
            raise RestError(404, 'Book not found')

        return self.books[book_id]

    async def create_book(
            self,
            book: Annotated[Book, JSONValue(), XMLEntity('Book')]
    ) -> int:
        """Add a book

        Args:
            book (Book): The book

        Returns:
            int: The id of the new book
        """
        self.next_id += 1

        self.books[self.next_id] = BookWithId(
            book_id=self.next_id,
            title=book['title'],
            author=book['author'],
            publication_date=book['publication_date']
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
            book (Annotated[Book, T]): The book as the body

        Raises:
            RestError: 404, when a book is not found
        """
        if book_id not in self.books:
            raise RestError(404, 'Book not found')
        found_book = self.books[book_id]
        found_book.update(book)


if __name__ == "__main__":

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
    app = Application(http_router=rest_router)
    add_swagger_ui(app)

    controller = BookController()
    controller.add_routes(rest_router)

    uvicorn.run(app, port=9009)
