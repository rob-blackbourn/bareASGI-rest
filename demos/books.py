"""
A simple request handler.
"""

from datetime import datetime
import logging
from typing import Any, Dict, List, Optional, Tuple

from bareasgi import Application
from bareasgi_rest import RestHttpRouter
import bareasgi_jinja2
import jinja2
import pkg_resources
import uvicorn

logging.basicConfig(level=logging.DEBUG)


class BookController:

    def __init__(self):
        self.books: Dict[int, Dict[str, Any]] = {}
        self.next_id = 0

    def add_routes(self, router: RestHttpRouter):
        tags = ['Books']
        router.add_rest(
            {'GET'},
            '/books',
            self.get_books,
            tags=tags,
            responses={200: {'description': 'OK'}}
        )
        router.add_rest(
            {'GET'},
            '/books/{bookId:int}',
            self.get_book,
            tags=tags,
            responses={
                200: {'description': 'OK'},
                404: {'description': 'Book not found'}
            }
        )
        router.add_rest(
            {'POST'},
            '/books',
            self.create_book,
            tags=tags,
            responses={201: {'description': 'Created'}}
        )
        router.add_rest(
            {'PUT'},
            '/books/{bookId:int}',
            self.update_book,
            tags=tags,
            responses={
                204: {'description': 'Updated'},
                404: {'description': 'Book not found'}
            }
        )

    async def get_books(self) -> Tuple[int, List[Any]]:
        """Get all the books.

        This method gets all the books in the shop.

        Returns:
            Tuple[int, List[Any]]: All the books
        """
        return 200, list(self.books.values())

    async def get_book(
            self,
            book_id: int
    ) -> Tuple[int, Optional[Dict[str, Any]]]:
        """Get a book for a given id

        Args:
            book_id (int): The id of the book

        Returns:
            Tuple[int, Optional[Dict[str, Any]]]: The book or nothing
        """
        if book_id in self.books:
            return 200, self.books[book_id]
        else:
            return 404, None

    async def create_book(
            self,
            author: str,
            title: str,
            published: datetime
    ) -> Tuple[int, int]:
        """Add a book

        Args:
            author (str): The author
            title (str): The title
            published (datetime): The publication date

        Returns:
            Tuple[int, int]: The id of the new book
        """
        self.next_id += 1
        self.books[self.next_id] = {
            'book_id': self.next_id,
            'title': title,
            'author': author,
            'published': published
        }
        return 201, self.next_id

    async def update_book(
            self,
            book_id: int,
            author: str,
            title: str,
            published: datetime
    ) -> Tuple[int, Any]:
        """Update a book

        Args:
            book_id (int): The id of the book to update
            author (str): The new author
            title (str): The title
            published (datetime): The publication date

        Returns:
            Tuple[int, Any]: Nothing
        """
        if book_id in self.books:
            self.books[book_id]['title'] = title
            self.books[book_id]['author'] = author
            self.books[book_id]['published'] = published
            return 204, None
        else:
            return 404, None


if __name__ == "__main__":

    TEMPLATES = pkg_resources.resource_filename("bareasgi_rest", "templates")

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(TEMPLATES),
        autoescape=jinja2.select_autoescape(['html', 'xml']),
        enable_async=True
    )

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
    bareasgi_jinja2.add_jinja2(app, env)

    controller = BookController()
    controller.add_routes(rest_router)

    uvicorn.run(app, port=9009)
