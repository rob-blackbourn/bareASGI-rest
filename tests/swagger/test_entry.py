"""Tests for entry.py"""

from datetime import datetime
from typing import Dict, List, Optional
try:
    from typing import TypedDict  # type:ignore
except:  # pylint: disable=bare-except
    from typing_extensions import TypedDict
from typing_extensions import Annotated  # type: ignore

from bareasgi.basic_router.path_definition import PathDefinition
from jetblack_serialization.json import JSONValue

from bareasgi_rest.swagger.entry import make_swagger_entry

from .mocks import MOCK_SWAGGER_CONFIG


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


def test_get():
    """Tests for get calls"""

    async def get_books() -> List[Book]:
        """Get all the books.

        This method gets all the books in the shop.

        Returns:
            List[Book]: All the books
        """
        return list(BOOKS.values())

    get_books_swagger_entry = make_swagger_entry(
        'GET',
        PathDefinition('/books'),
        get_books,
        [b'application/json'],
        [b'application/json'],
        'multi',
        ['Books'],
        200,
        'OK',
        MOCK_SWAGGER_CONFIG
    )
    assert get_books_swagger_entry == {
        'parameters': [],
        'produces': ['application/json'],
        'consumes': ['application/json'],
        'responses': {
            200: {
                'description': 'OK',
                'schema': {
                    'description': 'All the books',
                    'type': 'array',
                    'collectionFormat': 'multi',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'bookId': {
                                'name': 'bookId',
                                'description': 'The book id',
                                'type': 'integer'
                            },
                            'title': {
                                'name': 'title',
                                'description': 'The title',
                                'type': 'string'
                            },
                            'author': {
                                'name': 'author',
                                'description': 'The author',
                                'type': 'string'
                            },
                            'publicationDate': {
                                'name': 'publicationDate',
                                'description': 'The publication date',
                                'type': 'string',
                                'format': 'date-time'
                            }
                        }
                    }
                }
            }
        },
        'summary': 'Get all the books.',
        'description': 'This method gets all the books in the shop.',
        'tags': ['Books']
    }

    async def find_books(
            library: str,
            title: Optional[str] = None,
            author: Optional[str] = None,
            before_date: Optional[datetime] = None,
            after_date: Optional[datetime] = None
    ) -> List[Book]:
        """Find books

        Args:
            library (str): The library
            title (Optional[str], optional): The title. Defaults to None.
            author (Optional[str], optional): The author. Defaults to None.
            before_date (Optional[datetime], optional): The oldest date. Defaults to None.
            after_date (Optional[datetime], optional): The newest date. Defaults to None.

        Returns:
            List[Book]: The matching books
        """
        return list(BOOKS.values())

    find_books_swagger_entry = make_swagger_entry(
        'GET',
        PathDefinition('/books/{library:str}'),
        find_books,
        [b'application/json'],
        [b'application/json'],
        'multi',
        ['Books'],
        200,
        'OK',
        MOCK_SWAGGER_CONFIG
    )
    assert find_books_swagger_entry == {
        'parameters': [
            {
                'name': 'library',
                'description': 'The library',
                'type': 'string',
                'in': 'path',
                'required': True
            },
            {
                'name': 'title',
                'description': 'The title. Defaults to None.',
                'default': None,
                'type': 'string',
                'in': 'query',
                'required': False
            },
            {
                'name': 'author',
                'description': 'The author. Defaults to None.',
                'default': None,
                'type': 'string',
                'in': 'query',
                'required': False
            },
            {
                'name': 'beforeDate',
                'description': 'The oldest date. Defaults to None.',
                'default': None,
                'type': 'string',
                'format': 'date-time',
                'in': 'query',
                'required': False
            },
            {
                'name': 'afterDate',
                'description': 'The newest date. Defaults to None.',
                'default': None,
                'type': 'string',
                'format': 'date-time',
                'in': 'query',
                'required': False
            }
        ],
        'produces': ['application/json'],
        'consumes': ['application/json'],
        'responses': {
            200: {
                'description': 'OK',
                'schema': {
                    'description': 'The matching books',
                    'type': 'array',
                    'collectionFormat': 'multi',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'bookId': {
                                'name': 'bookId',
                                'description': 'The book id',
                                'type': 'integer'
                            },
                            'title': {
                                'name': 'title',
                                'description': 'The title',
                                'type': 'string'
                            },
                            'author': {
                                'name': 'author',
                                'description': 'The author',
                                'type': 'string'
                            },
                            'publicationDate': {
                                'name': 'publicationDate',
                                'description': 'The publication date',
                                'type': 'string',
                                'format': 'date-time'
                            }
                        }
                    }
                }
            }
        },
        'summary': 'Find books',
        'tags': ['Books']
    }


def test_post():
    """Tests for POST"""

    async def update_if_withdrawn(
            library: str,
            is_withdrawn: bool,
            book: Annotated[Book, JSONValue()]
    ) -> None:
        """Update the book if not withdrawn

        Args:
            library (str): The library
            is_withdrawn (bool): True if the book has been withdrawn
            book (Annotated[Book, Annotated[Book, JSONValue()]]): The book details to update
        """
        return list(BOOKS.values())

    update_if_withdrawn_swagger_entry = make_swagger_entry(
        'POST',
        PathDefinition('/books/{library:str}'),
        update_if_withdrawn,
        [b'application/json'],
        [b'application/json'],
        'multi',
        ['Books'],
        200,
        'OK',
        MOCK_SWAGGER_CONFIG
    )
    assert update_if_withdrawn_swagger_entry == {
        'parameters': [
            {
                'name': 'library',
                'description': 'The library',
                'type': 'string',
                'in': 'path',
                'required': True
            },
            {
                'name': 'isWithdrawn',
                'description': 'True if the book has been withdrawn',
                'type': 'boolean',
                'in': 'query',
                'required': True
            },
            {
                'in': 'body',
                'name': 'schema',
                'description': 'The body schema',
                'schema': {
                    'name': 'book',
                    'type': 'object',
                    'properties': {
                        'bookId': {
                            'name': 'bookId',
                            'description': 'The book id',
                            'type': 'integer'
                        },
                        'title': {
                            'name': 'title',
                            'description': 'The title',
                            'type': 'string'
                        },
                        'author': {
                            'name': 'author',
                            'description': 'The author',
                            'type': 'string'
                        },
                        'publicationDate': {
                            'name': 'publicationDate',
                            'description': 'The publication date',
                            'type': 'string',
                            'format': 'date-time'
                        }
                    }
                }
            }
        ],
        'produces': ['application/json'],
        'consumes': ['application/json'],
        'responses': {
            200: {
                'description': 'OK'
            }
        },
        'summary': 'Update the book if not withdrawn',
        'tags': ['Books']
    }
