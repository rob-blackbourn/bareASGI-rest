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
from urllib.error import HTTPError

from bareasgi import Application
import uvicorn

from bareasgi_rest import RestHttpRouter, add_swagger_ui

logging.basicConfig(level=logging.DEBUG)


class BookType(TypedDict):
    """A Book

    Args:
        book_id (int): The book id
        title (str): The title
        author (str): The author
        published (datetime): The publication date
    """
    book_id: int
    title: str
    author: str
    published: datetime


class BookController:

    def __init__(self):
        self.books: Dict[int, BookType] = {}
        self.next_id = 0

    def add_routes(self, router: RestHttpRouter):
        tags = ['Books']
        router.add_rest(
            {'GET'},
            '/books',
            self.get_books,
            tags=tags,
            status_code=200
        )
        router.add_rest(
            {'GET'},
            '/books/{bookId:int}',
            self.get_book,
            tags=tags,
            status_code=200
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
            '/books/{bookId:int}',
            self.update_book,
            tags=tags,
            status_code=204
        )

    async def get_books(self) -> List[BookType]:
        """Get all the books.

        This method gets all the books in the shop.

        Returns:
            List[Any]: All the books
        """
        return list(self.books.values())

    async def get_book(
            self,
            book_id: int
    ) -> BookType:
        """Get a book for a given id

        Args:
            book_id (int): The id of the book

        Raises:
            HTTPError: 404, when a book is not found

        Returns:
            Tuple[int, Optional[Dict[str, Any]]]: The book or nothing
        """

        if book_id not in self.books:
            raise HTTPError(None, 404, None, None, None)

        return self.books[book_id]

    async def create_book(
            self,
            author: str,
            title: str,
            published: datetime
    ) -> int:
        """Add a book

        Args:
            author (str): The author
            title (str): The title
            published (datetime): The publication date

        Returns:
            Tuple[int, int]: The id of the new book
        """
        self.next_id += 1
        book: BookType = BookType(
            book_id=self.next_id,
            title=title,
            author=author,
            published=published
        )
        self.books[self.next_id] = book
        return self.next_id

    async def update_book(
            self,
            book_id: int,
            author: str,
            title: str,
            published: datetime
    ) -> None:
        """Update a book

        Args:
            book_id (int): The id of the book to update
            author (str): The new author
            title (str): The title
            published (datetime): The publication date

        Raises:
            HTTPError: 404, when a book is not found

        Returns:
            Tuple[int, Any]: Nothing
        """
        if book_id not in self.books:
            raise HTTPError(None, 404, None, None, None)
        self.books[book_id]['title'] = title
        self.books[book_id]['author'] = author
        self.books[book_id]['published'] = published


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
