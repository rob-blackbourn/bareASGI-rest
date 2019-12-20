"""
A simple request handler.
"""

from datetime import datetime
import logging
from typing import Any, Dict, List, Optional, Tuple

from bareasgi import (
    Application,
    Scope,
    Info,
    RouteMatches,
    Content,
    HttpResponse,
    text_writer
)
from bareasgi_rest import RestHttpRouter

logging.basicConfig(level=logging.DEBUG)


class BookController:

    def __init__(self):
        self.books: Dict[int, Dict[str, Any]] = {}
        self.next_id = 0

    def add_routes(self, router: RestHttpRouter):
        router.add_rest({'GET'}, '/api/1/books', self.get_books)
        router.add_rest({'GET'}, '/api/1/books/{id:int}', self.get_book)
        router.add_rest({'POST'}, '/api/1/books', self.create_book)
        router.add_rest({'PUT'}, '/api/1/books/{id:int}', self.update_book)

    async def get_books(self) -> Tuple[int, List[Any]]:
        """A request handler which returns some text"""
        return 200, list(self.books.values())

    async def get_book(
            self,
            id: int
    ) -> Tuple[int, Optional[Dict[str, Any]]]:
        """A request handler which returns some text"""
        if id in self.books:
            return 200, self.books[id]
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
            'id': self.next_id,
            'title': title,
            'author': author,
            'published': published
        }
        return 201, self.next_id

    async def update_book(
            self,
            id: int,
            author: str,
            title: str,
            published: datetime
    ) -> Tuple[int, Any]:
        if id in self.books:
            self.books[id]['title'] = title
            self.books[id]['author'] = author
            self.books[id]['published'] = published
            return 204, None
        else:
            return 404, None


if __name__ == "__main__":
    import uvicorn

    rest_router = RestHttpRouter(None)
    app = Application(http_router=rest_router)
    controller = BookController()
    controller.add_routes(rest_router)

    uvicorn.run(app, port=9009)
