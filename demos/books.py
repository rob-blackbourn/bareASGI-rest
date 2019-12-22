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
        router.add_rest({'GET'}, '/books', self.get_books)
        router.add_rest({'GET'}, '/books/{bookId:int}', self.get_book)
        router.add_rest({'POST'}, '/books', self.create_book)
        router.add_rest({'PUT'}, '/books/{bookId:int}', self.update_book)

    async def get_books(self) -> Tuple[int, List[Any]]:
        """A request handler which returns some text"""
        return 200, list(self.books.values())

    async def get_book(
            self,
            book_id: int
    ) -> Tuple[int, Optional[Dict[str, Any]]]:
        """A request handler which returns some text"""
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
        if id in self.books:
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
        base_path='/api/1'
    )
    app = Application(http_router=rest_router)
    bareasgi_jinja2.add_jinja2(app, env)

    controller = BookController()
    controller.add_routes(rest_router)

    uvicorn.run(app, port=9009)
